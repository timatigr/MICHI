# -*- coding: utf-8 -*-
"""MICHI — прототип core loop: API уроков, SRS и статистики.

Упрощённый аналог контракта из SRS.md раздела 13.2 (без auth — один
пользователь, локальный запуск).
"""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import db, srs_engine, tts
from .content.registry import (
    COURSES, LESSON_BY_ID, LESSON_ORDER, LESSONS, VOCAB_UNITS,
    srs_items_for_lesson,
)
from .exercises import item_info, make_lesson_steps, review_exercise

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_app):
    db.init_db()
    yield


app = FastAPI(title="MICHI prototype", lifespan=lifespan)


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
                out[lid]["locked_hint"] = "Откроется, когда выучите всю кану этих слов"
            prev_completed = False
    return out


def _streak(conn):
    # Дни считаем по локальному времени: занятие после полуночи — это «сегодня»
    days = {r["d"] for r in conn.execute(
        "SELECT DISTINCT date(reviewed_at, 'localtime') AS d FROM reviews"
    )} | {r["d"] for r in conn.execute(
        "SELECT DISTINCT date(completed_at, 'localtime') AS d FROM lesson_progress "
        "WHERE completed_at IS NOT NULL"
    )}
    today = datetime.now().date()
    streak, day = 0, today
    if today.isoformat() not in days:
        day = today - timedelta(days=1)  # сегодня ещё не занимался — серия не сгорела
    while day.isoformat() in days:
        streak += 1
        day -= timedelta(days=1)
    return streak


# ---------- Сегодня ----------

@app.get("/api/overview")
def overview():
    conn = db.connect()
    try:
        settings = db.get_settings(conn)
        c = srs_engine.counts(conn, settings)
        statuses = _lesson_statuses(conn)
        next_lesson = next(
            (lid for lid in LESSON_ORDER if statuses[lid]["status"] == "available"), None)
        today = datetime.now().date().isoformat()
        today_row = conn.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(correct), 0) AS correct "
            "FROM reviews WHERE date(reviewed_at, 'localtime') = ?", (today,)
        ).fetchone()
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
            "streak": _streak(conn),
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
        }
    finally:
        conn.close()


# ---------- Уроки ----------

# «Регионы» курса — группировка уроков в духе карты Японии (раздел 8.1)
def _lesson_group(lesson_id):
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
                "title": f"Слова N5 · Юнит {unit} — {VOCAB_UNITS.get(unit, '')}"}
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
def list_lessons():
    conn = db.connect()
    try:
        statuses = _lesson_statuses(conn)
        out = []
        for l in LESSONS:
            kana = l.get("kana", [])
            out.append(
                {"id": l["id"], "title": l["title"], "subtitle": l.get("subtitle", ""),
                 "kana_count": len(kana),
                 "icon": l.get("icon") or (kana[0] if kana else "っ"),
                 "group": _lesson_group(l["id"]),
                 **statuses[l["id"]]})
        return out
    finally:
        conn.close()


@app.get("/api/lessons/{lesson_id}")
def get_lesson(lesson_id: str):
    if lesson_id not in LESSON_BY_ID:
        raise HTTPException(404, "Урок не найден")
    conn = db.connect()
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
def complete_lesson(lesson_id: str, result: LessonResult):
    if lesson_id not in LESSON_BY_ID:
        raise HTTPException(404, "Урок не найден")
    lesson = LESSON_BY_ID[lesson_id]
    conn = db.connect()
    try:
        if _lesson_statuses(conn)[lesson_id]["status"] == "locked":
            raise HTTPException(403, "Сначала завершите предыдущий урок")
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
        return {"ok": True, "cards_created": created}
    finally:
        conn.close()


# ---------- SRS ----------

@app.get("/api/srs/queue")
def srs_queue(limit: int = 20):
    conn = db.connect()
    try:
        settings = db.get_settings(conn)
        rows = srs_engine.get_queue(conn, settings, limit=limit)
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
        return {"items": items, "counts": srs_engine.counts(conn, settings)}
    finally:
        conn.close()


class Answer(BaseModel):
    card_id: int
    correct: bool
    duration_ms: int | None = None
    exercise_type: str = ""
    used_hint: bool = False


@app.post("/api/srs/answer")
def srs_answer(answer: Answer):
    conn = db.connect()
    try:
        row = conn.execute(
            "SELECT * FROM srs_cards WHERE id = ?", (answer.card_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(404, "Карточка не найдена")
        settings = db.get_settings(conn)
        return srs_engine.answer_card(
            conn, settings, row, answer.correct, answer.duration_ms,
            answer.exercise_type, answer.used_hint,
        )
    finally:
        conn.close()


# ---------- Озвучка (Edge TTS, нейроголоса) ----------

@app.get("/api/tts/voices")
async def tts_voices():
    return await tts.list_voices()


@app.get("/api/tts")
async def tts_synthesize(text: str, voice: str = tts.DEFAULT_VOICE):
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
def stats():
    conn = db.connect()
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
        start = (datetime.now().date() - timedelta(days=act_days - 1))
        act_rows = conn.execute(
            "SELECT date(reviewed_at, 'localtime') AS d, COUNT(*) AS c, "
            "COALESCE(SUM(correct),0) AS ok FROM reviews "
            "WHERE date(reviewed_at, 'localtime') >= ? "
            "GROUP BY date(reviewed_at, 'localtime')", (start.isoformat(),)
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
            "forecast": srs_engine.forecast(conn, days=14),
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


# Статика — в самом конце, чтобы не перехватывать /api/*
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
