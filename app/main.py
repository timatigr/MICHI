# -*- coding: utf-8 -*-
"""MICHI — прототип core loop: API уроков, SRS и статистики.

Упрощённый аналог контракта из SRS.md раздела 13.2 (без auth — один
пользователь, локальный запуск).
"""
import asyncio
import logging
import os
import sqlite3
import tempfile
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from . import ai_tutor, db, gamification, identity, ratelimit, srs_engine, tts
from .content.registry import (
    COURSES, GATE_PASS, GRAMMAR_BY_ID, GRAMMAR_UNITS, KANA_BY_CHAR, KANJI_BY_CHAR,
    KANJI_UNITS, LESSON_BY_ID, LESSON_ORDER, LESSONS, VOCAB_BY_ID, VOCAB_UNITS,
    srs_items_for_lesson,
)
from .exercises import _mnemonics_for, item_info, make_lesson_steps, review_exercise

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


log = logging.getLogger("michi")

# Авточистка заброшенных пустых баз (см. db.cleanup_stale_users). На auto-stop
# машинах (Fly) суточный цикл может не наступить — поэтому первый прогон сразу
# после старта (фактически на каждом «пробуждении»), затем раз в сутки для
# долгоживущих инстансов. MICHI_CLEANUP_ENABLED=0 выключает, MICHI_CLEANUP_DAYS
# задаёт порог «заброшенности» (по умолчанию 30 дней).
_CLEANUP_ENABLED = os.environ.get("MICHI_CLEANUP_ENABLED", "1") != "0"
_CLEANUP_INTERVAL_SEC = 24 * 60 * 60


def _cleanup_max_age_days() -> int:
    try:
        return max(1, int(os.environ.get("MICHI_CLEANUP_DAYS", 30)))
    except ValueError:
        return 30


async def _cleanup_loop():
    while True:
        try:
            removed = await asyncio.to_thread(
                db.cleanup_stale_users, _cleanup_max_age_days())
            if removed:
                log.info("Чистка: удалено заброшенных пустых баз: %d", removed)
        except Exception:
            log.exception("Чистка заброшенных баз не удалась")
        await asyncio.sleep(_CLEANUP_INTERVAL_SEC)


def _secret_key_warning():
    """Текст предупреждения, если в прод-режиме (HTTPS-cookie) не задан явный
    MICHI_SECRET_KEY; иначе None. Без него подпись cookie держится на
    data/secret.key (пропадёт вместе с томом → все разлогинятся) или на эфемерном
    ключе процесса (read-only ФС → сбрасывается на каждом рестарте)."""
    secure = os.environ.get("MICHI_COOKIE_SECURE", "0") == "1"
    if secure and not os.environ.get("MICHI_SECRET_KEY"):
        return ("MICHI_SECRET_KEY не задан в прод-режиме (MICHI_COOKIE_SECURE=1): "
                "cookie подписываются ключом из data/secret.key или эфемерным ключом "
                "процесса — при потере тома или на read-only ФС все пользователи "
                "потеряют доступ к своему прогрессу. Задайте постоянный секрет "
                "(напр. `fly secrets set MICHI_SECRET_KEY=$(openssl rand -hex 32)`).")
    return None


@asynccontextmanager
async def lifespan(_app):
    db.init_db()
    warning = _secret_key_warning()
    if warning:
        log.warning(warning)
    task = asyncio.create_task(_cleanup_loop()) if _CLEANUP_ENABLED else None
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title="MICHI prototype", lifespan=lifespan)

# Secure-флаг cookie ставим в проде (HTTPS): MICHI_COOKIE_SECURE=1. Локально по
# http он бы мешал отдавать cookie, поэтому по умолчанию выключен.
_COOKIE_SECURE = os.environ.get("MICHI_COOKIE_SECURE", "0") == "1"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 5   # ~5 лет

# Content-Security-Policy под реальные ресурсы приложения. Свой JS только локальный
# (app.js/art.js/…), внешних скриптов нет — но в коде есть инлайновый <script>
# (тема до отрисовки), инлайновые обработчики onload/onerror у картинок-слотов и
# инлайновые style= → script/style требуют 'unsafe-inline'. Источники при этом
# заперты: скрипты/стили/шрифты/коннекты/картинки/медиа — только свой origin
# (шрифты self-hosted, внешних запросов нет), фрейминг запрещён.
_CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline'",
    "font-src 'self'",
    "img-src 'self' data:",
    "connect-src 'self'",
    "media-src 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
])


def _security_headers(secure=None):
    """Заголовки безопасности для каждого ответа. HSTS — только в прод-режиме
    (за TLS), иначе по http он бессмыслен."""
    if secure is None:
        secure = _COOKIE_SECURE
    h = {
        "Content-Security-Policy": _CSP,
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-Frame-Options": "DENY",
        "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    }
    if secure:
        h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return h


@app.middleware("http")
async def _identify(request: Request, call_next):
    """Анонимная сессия: на каждом запросе берём uid из подписанной cookie, на
    первом визите — выдаём новый и ставим cookie (см. identity.py)."""
    # Рейт-лимит только на /api/*: статика дёшева и кэшируется, а абуз-вектор —
    # поток запросов без cookie, плодящий per-user базы (см. ratelimit.py).
    if request.url.path.startswith("/api/"):
        allowed, retry = ratelimit.check(ratelimit.client_ip(request))
        if not allowed:
            return JSONResponse(
                {"detail": "Слишком много запросов — подождите немного"},
                status_code=429, headers={"Retry-After": str(retry)},
            )
    uid = identity.parse(request.cookies.get(identity.COOKIE_NAME))
    fresh = uid is None
    token = None
    if fresh:
        uid, token = identity.new_token()
    request.state.uid = uid
    response = await call_next(request)
    if fresh:
        response.set_cookie(
            identity.COOKIE_NAME, token, max_age=_COOKIE_MAX_AGE,
            httponly=True, samesite="lax", secure=_COOKIE_SECURE, path="/",
        )
    return response


# Регистрируется ПОСЛЕ _identify → внешний слой: проставляет заголовки на любой
# ответ, включая 429 от рейт-лимита и статику.
@app.middleware("http")
async def _security(request: Request, call_next):
    response = await call_next(request)
    for key, value in _security_headers().items():
        response.headers[key] = value
    return response


def _uid(request: Request) -> str:
    return request.state.uid


def _tz_offset_min(request: Request):
    """Смещение пользователя от UTC в минутах из заголовка X-TZ-Offset (его шлёт
    фронт: -new Date().getTimezoneOffset()). На публичном хостинге без него у всех
    был бы UTC-день сервера; нет заголовка → None (серверные локальные сутки).
    Зажато в ±14 ч, чтобы мусорное значение не ломало SQL-сдвиг даты."""
    raw = request.headers.get("x-tz-offset")
    if raw is None:
        return None
    try:
        return max(-840, min(840, int(raw)))
    except ValueError:
        return None


def _lesson_statuses(conn):
    rows = conn.execute("SELECT * FROM lesson_progress").fetchall()
    progress = {r["lesson_id"]: r for r in rows}

    def completed(lid):
        r = progress.get(lid)
        return bool(r) and r["status"] == "completed"

    out = {}
    # Курсы каны открываются независимо: первый урок каждого курса доступен
    # сразу, внутри курса — последовательная разблокировка. Словарные уроки
    # дополнительно требуют всю кану своих слов (requires, принцип i+1).
    for course in COURSES:
        prev_completed = True
        for lid in course["lesson_ids"]:
            if completed(lid):
                row = progress[lid]
                out[lid] = {"status": "completed", "score": row["score"],
                            "completed_at": row["completed_at"]}
                prev_completed = True
                continue
            requires = LESSON_BY_ID[lid].get("requires", [])
            kana_ready = all(completed(rid) for rid in requires)
            status = "available" if prev_completed and kana_ready else "locked"
            out[lid] = {"status": status, "score": None, "completed_at": None}
            if status == "locked" and prev_completed and not kana_ready:
                out[lid]["locked_hint"] = (
                    "Откроется после освоения хираганы"
                    if LESSON_BY_ID[lid].get("type") == "kanji"
                    else "Откроется, когда выучите всю кану этих слов")
            prev_completed = False
    return out


def _streak(conn, tz_offset_min=None):
    # Дни считаем по локальным суткам пользователя: занятие после полуночи — «сегодня»
    rev_day = srs_engine.day_sql("reviewed_at", tz_offset_min)
    comp_day = srs_engine.day_sql("completed_at", tz_offset_min)
    days = {r["d"] for r in conn.execute(
        f"SELECT DISTINCT {rev_day} AS d FROM reviews"
    )} | {r["d"] for r in conn.execute(
        f"SELECT DISTINCT {comp_day} AS d FROM lesson_progress "
        "WHERE completed_at IS NOT NULL"
    )}
    today = srs_engine.local_today(tz_offset_min)
    streak, day = 0, today
    if today.isoformat() not in days:
        day = today - timedelta(days=1)  # сегодня ещё не занимался — серия не сгорела
    while day.isoformat() in days:
        streak += 1
        day -= timedelta(days=1)
    return streak


# ---------- Сегодня ----------

@app.get("/api/overview")
def overview(request: Request):
    tz = _tz_offset_min(request)
    conn = db.connect(_uid(request), create_if_missing=False)
    try:
        settings = db.get_settings(conn)
        c = srs_engine.counts(conn, settings, tz)
        statuses = _lesson_statuses(conn)
        next_lesson = next(
            (lid for lid in LESSON_ORDER if statuses[lid]["status"] == "available"), None)
        today = srs_engine.local_today(tz).isoformat()
        today_row = conn.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(correct), 0) AS correct "
            f"FROM reviews WHERE {srs_engine.day_sql('reviewed_at', tz)} = ?", (today,)
        ).fetchone()
        # Карточки, в которых сегодня ошиблись — для «разбора ошибок дня»
        mistakes_today = conn.execute(
            "SELECT COUNT(DISTINCT card_id) AS c FROM reviews "
            f"WHERE correct = 0 AND {srs_engine.day_sql('reviewed_at', tz)} = ?", (today,)
        ).fetchone()["c"]
        courses = [
            {"id": course["id"], "title": course["title"],
             "lessons_total": len(course["lesson_ids"]),
             "lessons_completed": sum(
                 1 for lid in course["lesson_ids"]
                 if statuses[lid]["status"] == "completed")}
            for course in COURSES
        ]
        return {
            "srs": c,
            "streak": _streak(conn, tz),
            "xp": gamification.xp_summary(conn),
            "today": {
                "reviews": today_row["total"],
                "accuracy": round(today_row["correct"] / today_row["total"] * 100)
                if today_row["total"] else None,
            },
            "next_lesson": (
                {"id": next_lesson, "title": LESSON_BY_ID[next_lesson]["title"],
                 "subtitle": LESSON_BY_ID[next_lesson].get("subtitle", "")}
                if next_lesson else None
            ),
            "courses": courses,
            "mistakes_today": mistakes_today,
        }
    finally:
        conn.close()


# ---------- Уроки ----------

# «Регионы» курса — группировка уроков в духе карты Японии (раздел 8.1)
def _lesson_group(lesson_id):
    lesson = LESSON_BY_ID[lesson_id]
    # Ворота юнита (id вида «v-g1») не парсятся как «буква+число» — у них свой
    # id курса и unit; кладём их в тот же регион, что и уроки этого юнита,
    # чтобы плитка ворот встала в конце своего блока.
    if lesson.get("type") == "gate_test":
        unit = lesson.get("unit", 1)
        course = lesson.get("course")
        if course == "n5":
            return {"id": f"n5-u{unit}", "jp": "単語",
                    "title": f"Первые слова · Юнит {unit} — {VOCAB_UNITS.get(unit, '')}"}
        if course == "kanji":
            return {"id": f"kanji-u{unit}", "jp": "漢字",
                    "title": f"Кандзи · {KANJI_UNITS.get(unit, '')}"}
        if course == "grammar":
            return {"id": f"grammar-u{unit}", "jp": "文法",
                    "title": f"Грамматика · {GRAMMAR_UNITS.get(unit, '')}"}
    course, n = lesson_id[0], int(lesson_id[1:])
    if course == "l":  # хирагана
        if n <= 10:
            return {"id": "h-gojuon", "jp": "ひらがな", "title": "Хирагана: годзюон"}
        if n <= 13:
            return {"id": "h-dakuten", "jp": "濁点", "title": "Хирагана: дакутэн"}
        if n <= 16:
            return {"id": "h-yoon", "jp": "拗音", "title": "Хирагана: ёон"}
        return {"id": "h-rules", "jp": "促音", "title": "Хирагана: правила"}
    if course == "v":  # лексика N5 — регион на каждый тематический юнит
        unit = LESSON_BY_ID[lesson_id].get("unit", 1)
        return {"id": f"n5-u{unit}", "jp": "単語",
                "title": f"Первые слова · Юнит {unit} — {VOCAB_UNITS.get(unit, '')}"}
    if course == "j":  # кандзи — регион на тематический юнит
        unit = LESSON_BY_ID[lesson_id].get("unit", 1)
        return {"id": f"kanji-u{unit}", "jp": "漢字",
                "title": f"Кандзи · {KANJI_UNITS.get(unit, '')}"}
    if course == "g":  # грамматика — регион на тематический юнит
        unit = LESSON_BY_ID[lesson_id].get("unit", 1)
        return {"id": f"grammar-u{unit}", "jp": "文法",
                "title": f"Грамматика · {GRAMMAR_UNITS.get(unit, '')}"}
    # катакана
    if n <= 10:
        return {"id": "k-gojuon", "jp": "カタカナ", "title": "Катакана: годзюон"}
    if n <= 13:
        return {"id": "k-dakuten", "jp": "濁点", "title": "Катакана: дакутэн"}
    if n <= 16:
        return {"id": "k-yoon", "jp": "拗音", "title": "Катакана: ёон"}
    if n == 17:
        return {"id": "k-rules", "jp": "促音", "title": "Катакана: правила"}
    return {"id": "k-hell", "jp": "地獄", "title": "Катакана-ад"}


@app.get("/api/lessons")
def list_lessons(request: Request):
    conn = db.connect(_uid(request), create_if_missing=False)
    try:
        statuses = _lesson_statuses(conn)
        out = []
        for l in LESSONS:
            kana = l.get("kana", [])
            is_gate = l.get("type") == "gate_test"
            out.append(
                {"id": l["id"], "title": l["title"], "subtitle": l.get("subtitle", ""),
                 "kana_count": len(kana),
                 "icon": l.get("icon") or (kana[0] if kana else "っ"),
                 "type": l.get("type"),
                 "pass_mark": GATE_PASS if is_gate else None,
                 "group": _lesson_group(l["id"]),
                 **statuses[l["id"]]})
        return out
    finally:
        conn.close()


@app.get("/api/lessons/{lesson_id}")
def get_lesson(lesson_id: str, request: Request):
    if lesson_id not in LESSON_BY_ID:
        raise HTTPException(404, "Урок не найден")
    conn = db.connect(_uid(request), create_if_missing=False)
    try:
        statuses = _lesson_statuses(conn)
        if statuses[lesson_id]["status"] == "locked":
            raise HTTPException(403, "Сначала завершите предыдущий урок")
    finally:
        conn.close()
    lesson = LESSON_BY_ID[lesson_id]
    return {"id": lesson_id, "title": lesson["title"],
            "steps": make_lesson_steps(lesson_id)}


class LessonResult(BaseModel):
    score: float = Field(ge=0, le=1)  # доля верных ответов


@app.post("/api/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: str, result: LessonResult, request: Request):
    if lesson_id not in LESSON_BY_ID:
        raise HTTPException(404, "Урок не найден")
    lesson = LESSON_BY_ID[lesson_id]
    conn = db.connect(_uid(request))
    try:
        if _lesson_statuses(conn)[lesson_id]["status"] == "locked":
            raise HTTPException(403, "Сначала завершите предыдущий урок")
        # Тест-ворота юнита (раздел 3): засчитывается только при ≥ 80%. Ниже
        # порога — попытка записывается (лучший балл, счётчик), но ворота не
        # «completed», поэтому следующий юнит не открывается и можно пересдать.
        if lesson.get("type") == "gate_test" and result.score < GATE_PASS:
            with conn:
                conn.execute(
                    "INSERT INTO lesson_progress(lesson_id, status, score, attempts) "
                    "VALUES (?, 'available', ?, 1) "
                    "ON CONFLICT(lesson_id) DO UPDATE SET "
                    "score=MAX(COALESCE(lesson_progress.score, 0), excluded.score), "
                    "attempts=lesson_progress.attempts+1",
                    (lesson_id, result.score),
                )
            return {"ok": True, "is_gate": True, "passed": False,
                    "score": result.score, "pass_mark": GATE_PASS, "cards_created": 0}
        now = datetime.now(timezone.utc).isoformat()
        with conn:
            conn.execute(
                "INSERT INTO lesson_progress(lesson_id, status, score, attempts, completed_at) "
                "VALUES (?, 'completed', ?, 1, ?) "
                "ON CONFLICT(lesson_id) DO UPDATE SET status='completed', "
                "score=MAX(COALESCE(lesson_progress.score, 0), excluded.score), "
                "attempts=lesson_progress.attempts+1, completed_at=excluded.completed_at",
                (lesson_id, result.score, now),
            )
        # Урок может создавать карточки разных типов (слово -> JP→RU и RU→JP)
        by_type = {}
        for item_type, item_id in srs_items_for_lesson(lesson):
            by_type.setdefault(item_type, []).append(item_id)
        created = 0
        for item_type, ids in by_type.items():
            created += len(srs_engine.create_cards(conn, item_type, ids))
        return {"ok": True, "cards_created": created,
                "is_gate": lesson.get("type") == "gate_test", "passed": True}
    finally:
        conn.close()


# ---------- SRS ----------

@app.get("/api/srs/queue")
def srs_queue(request: Request, limit: int = 20):
    tz = _tz_offset_min(request)
    conn = db.connect(_uid(request), create_if_missing=False)
    try:
        settings = db.get_settings(conn)
        rows = srs_engine.get_queue(conn, settings, limit=limit, tz_offset_min=tz)
        items = []
        for r in rows:
            ex = review_exercise(r["item_type"], r["item_id"], reps=r["reps"])
            if ex is None:
                continue
            items.append({
                "card_id": r["id"],
                "is_new": r["reps"] == 0,
                "is_leech": bool(r["is_leech"]),
                "exercise": ex,
                "info": item_info(r["item_type"], r["item_id"]),
            })
        return {"items": items, "counts": srs_engine.counts(conn, settings, tz)}
    finally:
        conn.close()


class Answer(BaseModel):
    card_id: int
    correct: bool
    duration_ms: int | None = None
    exercise_type: str = ""
    used_hint: bool = False


@app.post("/api/srs/answer")
def srs_answer(answer: Answer, request: Request):
    tz = _tz_offset_min(request)
    conn = db.connect(_uid(request))
    try:
        row = conn.execute(
            "SELECT * FROM srs_cards WHERE id = ?", (answer.card_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(404, "Карточка не найдена")
        settings = db.get_settings(conn)
        return srs_engine.answer_card(
            conn, settings, row, answer.correct, answer.duration_ms,
            answer.exercise_type, answer.used_hint, tz,
        )
    finally:
        conn.close()


# ---------- Разбор ошибок дня (практика, не влияет на расписание SRS) ----------

@app.get("/api/review/mistakes")
def review_mistakes(request: Request, limit: int = 30):
    """Карточки, в которых пользователь сегодня ошибся, как набор упражнений для
    «работы над ошибками». Это практика: фронт НЕ отправляет ответы в SRS, поэтому
    расписание/статистика не затрагиваются (эффект тестирования + «остывание»)."""
    tz = _tz_offset_min(request)
    conn = db.connect(_uid(request), create_if_missing=False)
    try:
        today = srs_engine.local_today(tz).isoformat()
        rows = conn.execute(
            "SELECT id, item_type, item_id, reps FROM srs_cards WHERE id IN ("
            "  SELECT card_id FROM reviews "
            f"  WHERE correct = 0 AND {srs_engine.day_sql('reviewed_at', tz)} = ?"
            ") ORDER BY id", (today,)
        ).fetchall()
    finally:
        conn.close()
    items = []
    for r in rows:
        ex = review_exercise(r["item_type"], r["item_id"], reps=r["reps"])
        if ex is None:                      # осиротевшая карточка — пропускаем
            continue
        items.append({"exercise": ex, "info": item_info(r["item_type"], r["item_id"])})
        if len(items) >= limit:
            break
    return {"items": items}


# ---------- ИИ-разбор ошибок «Сэнсэй» (SRS.md 7.2) ----------

class ExplainRequest(BaseModel):
    item_type: str = ""
    item_id: str = ""
    exercise_type: str = ""
    prompt: str = ""
    correct_answer: str = ""
    given_answer: str = ""
    choices: list[str] = Field(default_factory=list)


@app.get("/api/ai/status")
def ai_status(request: Request):
    """Доступен ли ИИ-разбор (флаг/ключ/библиотека) + дневная квота — для UI."""
    avail = ai_tutor.available()
    out = {"available": avail}
    if avail:
        out.update(ai_tutor.usage(_uid(request)))
        out["provider"] = ai_tutor.provider_label()
    return out


def _item_type_for(exercise_type: str, explicit: str) -> str:
    """item_type для справки item_info: явный приоритетнее, иначе по типу упражнения."""
    if explicit:
        return explicit
    if exercise_type.startswith("kana"):
        return "kana"
    if exercise_type.startswith("kanji") or exercise_type == "word_kanji":
        return "kanji"
    if exercise_type.startswith("vocab") or exercise_type == "dictation":
        return "vocab"
    if exercise_type in ("particle_choice", "grammar_choice", "sentence_scramble",
                         "grammar_cloze", "verb_conjugation"):
        return "grammar"
    return ""


@app.post("/api/ai/explain")
def ai_explain(req: ExplainRequest, request: Request):
    if not ai_tutor.available():
        raise HTTPException(503, "ИИ-разбор недоступен")
    item_type = _item_type_for(req.exercise_type, req.item_type)
    info = item_info(item_type, req.item_id) if req.item_id else {}
    context = {
        "item_type": item_type,
        "item_id": req.item_id,
        "exercise_type": req.exercise_type,
        "prompt": req.prompt,
        "correct_answer": req.correct_answer,
        "given_answer": req.given_answer,
        "choices": req.choices,
        "title": info.get("title"),
        "sub": info.get("sub"),
        "hint": info.get("hint"),
    }
    result = ai_tutor.explain(context, _uid(request))
    if not result.get("available"):
        raise HTTPException(503, "ИИ-разбор временно недоступен")
    return result


# ---------- Озвучка (Edge TTS, нейроголоса) ----------
# На публичном хостинге серверный Edge TTS под потоком людей Microsoft троттлит,
# а дисковый кэш растёт без границ. MICHI_TTS_ENABLED=0 выключает серверную
# озвучку — фронт мягко откатывается на браузерный голос (Web Speech): пустой
# список голосов → neuralOk=false, а ошибка на /api/tts → onerror → speakBrowser.
_TTS_SERVER_ENABLED = os.environ.get("MICHI_TTS_ENABLED", "1") != "0"


@app.get("/api/tts/voices")
async def tts_voices():
    if not _TTS_SERVER_ENABLED:
        return []
    return await tts.list_voices()


@app.get("/api/tts")
async def tts_synthesize(text: str, voice: str = tts.DEFAULT_VOICE):
    if not _TTS_SERVER_ENABLED:
        raise HTTPException(503, "Серверная озвучка выключена")
    if not text.strip():
        raise HTTPException(400, "Пустой текст")
    try:
        path, media_type = await tts.synthesize(text, voice)
    except Exception:
        raise HTTPException(502, "Озвучка недоступна (нет сети?)")
    return FileResponse(path, media_type=media_type,
                        headers={"Cache-Control": "public, max-age=31536000"})


# ---------- Статистика ----------

@app.get("/api/stats")
def stats(request: Request):
    tz = _tz_offset_min(request)
    conn = db.connect(_uid(request), create_if_missing=False)
    try:
        settings = db.get_settings(conn)
        states = {r["state"]: r["c"] for r in conn.execute(
            "SELECT state, COUNT(*) AS c FROM srs_cards WHERE reps > 0 GROUP BY state"
        )}
        new_cards = conn.execute(
            "SELECT COUNT(*) AS c FROM srs_cards WHERE reps = 0").fetchone()["c"]

        def retention(days):
            row = conn.execute(
                "SELECT COUNT(*) AS total, COALESCE(SUM(correct), 0) AS ok FROM reviews "
                "WHERE state_before IN (2, 3) AND reviewed_at >= datetime('now', ?)",
                (f"-{days} days",),
            ).fetchone()
            return round(row["ok"] / row["total"] * 100) if row["total"] else None

        # Все 14 дней, включая нулевые — иначе график из одного дня
        # превращается в сплошной столбец на всю ширину
        act_days = 14
        start = (srs_engine.local_today(tz) - timedelta(days=act_days - 1))
        rev_day = srs_engine.day_sql("reviewed_at", tz)
        act_rows = conn.execute(
            f"SELECT {rev_day} AS d, COUNT(*) AS c, "
            "COALESCE(SUM(correct),0) AS ok FROM reviews "
            f"WHERE {rev_day} >= ? "
            f"GROUP BY {rev_day}", (start.isoformat(),)
        ).fetchall()
        act_by_day = {r["d"]: r for r in act_rows}
        activity = [
            (start + timedelta(days=i)).isoformat() for i in range(act_days)
        ]

        hardest = conn.execute(
            "SELECT item_type, item_id, lapses, is_leech FROM srs_cards "
            "WHERE lapses > 0 ORDER BY lapses DESC LIMIT 8"
        ).fetchall()

        return {
            "cards": {
                "new": new_cards,
                "learning": states.get(1, 0),
                "review": states.get(2, 0),
                "relearning": states.get(3, 0),
            },
            "retention": {"week": retention(7), "month": retention(30)},
            "activity": [
                {"date": d,
                 "reviews": act_by_day[d]["c"] if d in act_by_day else 0,
                 "accuracy": round(act_by_day[d]["ok"] / act_by_day[d]["c"] * 100)
                 if d in act_by_day else None}
                for d in activity
            ],
            "forecast": srs_engine.forecast(conn, days=14, tz_offset_min=tz),
            "hardest": [
                {"char": info["title"], "romaji": info["sub"],
                 "lapses": r["lapses"], "is_leech": bool(r["is_leech"])}
                for r in hardest
                for info in [item_info(r["item_type"], r["item_id"])]
            ],
            "settings": settings,
        }
    finally:
        conn.close()


# ---------- Настройки SRS ----------

class SrsSettingsPatch(BaseModel):
    # Дневная нагрузка (4.4) и целевое удержание FSRS (4.1). Каждое поле
    # опционально — UI шлёт только изменившееся. Границы оберегают очередь и
    # планировщик от значений, которые их ломают (retention — проверенный
    # рабочий диапазон py-fsrs).
    new_per_day: int | None = Field(default=None, ge=0, le=100)
    reviews_per_day: int | None = Field(default=None, ge=0, le=2000)
    desired_retention: float | None = Field(default=None, ge=0.75, le=0.97)


@app.get("/api/settings")
def settings_get(request: Request):
    conn = db.connect(_uid(request), create_if_missing=False)
    try:
        return db.get_settings(conn)
    finally:
        conn.close()


@app.post("/api/settings")
def settings_update(patch: SrsSettingsPatch, request: Request):
    changes = patch.model_dump(exclude_none=True)
    conn = db.connect(_uid(request))
    try:
        for key, value in changes.items():
            db.set_setting(conn, key, value)
        return db.get_settings(conn)
    finally:
        conn.close()


# ---------- UI-настройки клиента (тема/язык/озвучка/цель/…) ----------
# Зеркало localStorage в БД: настройки переносятся на другое устройство и
# попадают в резервную копию (раньше бэкап покрывал только SRS). Источник истины
# на клиенте — localStorage; сюда он пишет сквозным зеркалированием при изменении
# и подтягивает на старте (после импорта/на новом устройстве).

@app.get("/api/prefs")
def prefs_get(request: Request):
    conn = db.connect(_uid(request), create_if_missing=False)
    try:
        return db.get_ui_prefs(conn)
    finally:
        conn.close()


@app.post("/api/prefs")
def prefs_set(patch: dict[str, str | None], request: Request):
    conn = db.connect(_uid(request))
    try:
        for key, value in patch.items():
            db.set_ui_pref(conn, key, value)   # неизвестные ключи отбрасываются
        return db.get_ui_prefs(conn)
    finally:
        conn.close()


# ---------- Достижения ----------

@app.get("/api/achievements")
def achievements(request: Request):
    conn = db.connect(_uid(request), create_if_missing=False)
    try:
        data = gamification.achievements(conn, _streak(conn, _tz_offset_min(request)))
        data["xp"] = gamification.xp_summary(conn)
        return data
    finally:
        conn.close()


# ---------- Справочник изученного («Словарь») ----------
# Все элементы, попавшие в SRS (т.е. введённые на уроках), свёрнутые из карточек
# в логические элементы (слово = 2 карточки, кандзи = 3) и сгруппированные по
# курсам. Экран для повторения по запросу — в отличие от очереди SRS по графику.
_LEARNED_TITLES = {"hiragana": "Хирагана", "katakana": "Катакана", "n5": "Слова N5",
                   "kanji": "Кандзи", "grammar": "Грамматика"}
_LEARNED_ORDER = ("hiragana", "katakana", "n5", "kanji", "grammar")


def _learned_display(item_type, item_id):
    """(course, {title, sub, tts, extra}) для элемента — или None, если незнаком."""
    if item_type == "kana":
        info = KANA_BY_CHAR.get(item_id)
        if info:
            course = "hiragana" if info.get("script") == "h" else "katakana"
            return course, {"title": item_id, "sub": info["romaji"], "tts": item_id,
                            "mn": _mnemonics_for(info)}
    elif item_type.startswith("kanji"):
        k = KANJI_BY_CHAR.get(item_id)
        if k:
            return "kanji", {"title": k["char"], "sub": k["meaning"],
                             "tts": k["reading"], "extra": k["reading"],
                             "mn": [m for m in [k.get("mnemonic")] if m]}
    elif item_type.startswith("vocab"):
        w = VOCAB_BY_ID.get(item_id)
        if w:
            return "n5", {"title": w["kana"], "sub": w["ru"],
                          "tts": w["kana"], "extra": w["romaji"]}
    elif item_type == "grammar":
        p = GRAMMAR_BY_ID.get(item_id)
        if p:
            # Озвучка точки — первый пример целиком (частицы вроде は в контексте
            # читаются верно: «wa», а не «ha»); структура с A/B непроизносима.
            ex = (p.get("examples") or [None])[0]
            tts = (ex.get("reading") or "".join(ex["tokens"])) if ex else None
            return "grammar", {"title": p["title"], "sub": p["meaning"],
                               "tts": tts, "extra": p.get("structure")}
    return None


@app.get("/api/learned")
def learned(request: Request):
    conn = db.connect(_uid(request), create_if_missing=False)
    try:
        settings = db.get_settings(conn)
        rows = conn.execute(
            "SELECT item_type, item_id, state, reps, is_leech, fsrs FROM srs_cards ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    # «Сила памяти» (8/USP): текущая вероятность вспомнить по FSRS (retrievability).
    # Для элемента из нескольких карточек (слово=2, кандзи=3) берём минимум —
    # элемент крепок настолько, насколько крепок его слабейший навык.
    scheduler = srs_engine.make_scheduler(settings)

    groups, order = {}, {}     # course -> {item_id: agg}; course -> [item_id, ...]
    for r in rows:
        disp = _learned_display(r["item_type"], r["item_id"])
        if disp is None:
            continue
        course, fields = disp
        bucket = groups.setdefault(course, {})
        a = bucket.get(r["item_id"])
        if a is None:
            a = bucket[r["item_id"]] = {"disp": fields, "total": 0, "reviewed": 0,
                                        "reps": 0, "leech": False, "r_min": None}
            order.setdefault(course, []).append(r["item_id"])
        a["total"] += 1
        a["reps"] += r["reps"]
        if r["reps"] > 0 and r["state"] == 2:   # state 2 = review (в долгой памяти)
            a["reviewed"] += 1
        if r["reps"] > 0:                       # сила памяти — только по показанным
            rr = srs_engine.retrievability(scheduler, r)
            a["r_min"] = rr if a["r_min"] is None else min(a["r_min"], rr)
        if r["is_leech"]:
            a["leech"] = True

    def state_of(a):
        if a["reps"] == 0:
            return "new"
        return "review" if a["reviewed"] >= a["total"] else "learning"

    out = []
    for cid in _LEARNED_ORDER:
        ids = order.get(cid)
        if not ids:
            continue
        items = [{**groups[cid][iid]["disp"], "state": state_of(groups[cid][iid]),
                  "leech": groups[cid][iid]["leech"],
                  "strength": (round(groups[cid][iid]["r_min"] * 100)
                               if groups[cid][iid]["r_min"] is not None else None)}
                 for iid in ids]
        out.append({"id": cid, "title": _LEARNED_TITLES[cid],
                    "count": len(items), "items": items})
    return {"courses": out}


# ---------- Резервная копия данных ----------

@app.get("/api/export")
def export_db(request: Request):
    """Скачать консистентный снимок своего прогресса одним SQLite-файлом."""
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db.backup_to(tmp, _uid(request))
    name = f"michi-backup-{datetime.now().date().isoformat()}.db"
    return FileResponse(tmp, media_type="application/octet-stream", filename=name,
                        background=BackgroundTask(os.remove, tmp))


# Личная база — десятки тысяч карточек; реальный бэкап измеряется мегабайтами.
# Лимит отсекает «залив на 2 ГБ» (DoS по памяти/диску) до чтения тела целиком.
_IMPORT_MAX_BYTES = 64 * 1024 * 1024


@app.post("/api/import")
async def import_db(request: Request):
    """Восстановить свой прогресс из ранее скачанной копии (перезаписывает текущий).
    Файл шлётся сырым телом запроса — поэтому python-multipart не нужен."""
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > _IMPORT_MAX_BYTES:
        raise HTTPException(413, "Файл слишком большой")
    data = await request.body()
    if not data:
        raise HTTPException(400, "Пустой файл")
    if len(data) > _IMPORT_MAX_BYTES:   # на случай, если Content-Length соврал
        raise HTTPException(413, "Файл слишком большой")
    fd, tmp = tempfile.mkstemp(suffix=".db")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        if not db.is_michi_db(tmp):
            raise HTTPException(400, "Это не резервная копия MICHI")
        try:
            cards, reviews = db.restore_from(tmp, _uid(request))
        except sqlite3.OperationalError:
            raise HTTPException(409, "База занята — закройте другие вкладки и повторите")
    finally:
        os.remove(tmp)
    return {"ok": True, "cards": cards, "reviews": reviews}


# ---------- Удаление своих данных (право «начать с чистого листа») ----------

@app.post("/api/account/delete")
def account_delete(request: Request):
    """Безвозвратно стереть все данные текущего пользователя и выдать новую
    анонимную сессию (новый uid в cookie) — чтобы не осталось привязки к старым
    данным. Затрагивает только базу этого пользователя."""
    db.delete_user(_uid(request))
    uid, token = identity.new_token()
    resp = JSONResponse({"ok": True})
    # Запрос пришёл с валидной cookie → middleware _identify свою cookie не ставит
    # (fresh=False), поэтому наша ротация uid сохраняется.
    resp.set_cookie(
        identity.COOKIE_NAME, token, max_age=_COOKIE_MAX_AGE,
        httponly=True, samesite="lax", secure=_COOKIE_SECURE, path="/",
    )
    return resp


# Статика — в самом конце, чтобы не перехватывать /api/*
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
