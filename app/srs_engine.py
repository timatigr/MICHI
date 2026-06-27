# -*- coding: utf-8 -*-
"""SRS-движок на FSRS (SRS.md, раздел 4).

- Планирование: py-fsrs (FSRS v6), learning-шаги 1 мин → 10 мин (4.2).
- Авто-оценка (4.2): ошибка → Again; верно, но дольше p75 → Hard;
  верно быстрее p25 → Easy; иначе Good. Перцентили считаются по
  последним верным ответам пользователя.
- Очередь (4.4): просроченные по возрастанию retrievability (риск
  забывания), затем новые в пределах дневного лимита.
- Пиявки (4.2): >= 6 ошибок в Review → пометка is_leech.
"""
import json
import random
from datetime import datetime, timedelta, timezone

from fsrs import Card, Rating, Scheduler, State

from .content.registry import item_exists

LEECH_LAPSES = 6
# Дефолтные пороги авто-оценки, пока мало собственной статистики (мс).
# У письма свой темп — пороги считаются раздельно по типам упражнений.
DEFAULT_THRESHOLDS = {"kana_tracing": (4000, 15000), "kana_word_build": (3000, 12000)}
DEFAULT_P25, DEFAULT_P75 = 1500, 6000
MIN_SAMPLES = 20
# Learning-карточки, которые "дозреют" в ближайшие минуты, отдаём в ту же сессию
LEARNING_LOOKAHEAD = timedelta(minutes=15)


def _now():
    return datetime.now(timezone.utc)


def local_today(tz_offset_min=None):
    """Дата «сегодня» по локальным суткам пользователя.

    Дневные сущности (стрик, лимиты, «сегодня») живут по локальным суткам.
    tz_offset_min — смещение пользователя от UTC в минутах (восточнее = плюс).
    None → серверные локальные сутки (одно-пользовательский/локальный режим, как было).
    На публичном хостинге фронт шлёт смещение, иначе у всех был бы UTC-день сервера."""
    if tz_offset_min is None:
        return datetime.now().date()
    return (datetime.now(timezone.utc) + timedelta(minutes=int(tz_offset_min))).date()


def day_sql(col, tz_offset_min=None):
    """SQLite-выражение «дата столбца (UTC ISO) по локальным суткам пользователя»."""
    if tz_offset_min is None:
        return f"date({col}, 'localtime')"
    return f"date({col}, '{int(tz_offset_min):+d} minutes')"


def hour_sql(col, tz_offset_min=None):
    """SQLite-выражение «час столбца (UTC ISO) по локальному времени пользователя»
    (строка '00'–'23'). Симметрично day_sql — для «ночных» предикатов
    геймификации, чтобы «ночная сова» считалась по местной ночи, а не серверной."""
    if tz_offset_min is None:
        return f"strftime('%H', {col}, 'localtime')"
    return f"strftime('%H', {col}, '{int(tz_offset_min):+d} minutes')"


def make_scheduler(settings):
    return Scheduler(desired_retention=float(settings.get("desired_retention", 0.9)))


def create_cards(conn, item_type, item_ids):
    """Создать SRS-карточки (вызывается при завершении урока). Идемпотентно."""
    created = []
    with conn:
        for item_id in item_ids:
            card = Card()
            cur = conn.execute(
                "INSERT OR IGNORE INTO srs_cards"
                "(item_type, item_id, fsrs, state, due_at, stability, last_review) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (item_type, item_id, json.dumps(card.to_dict()),
                 card.state.value, card.due.isoformat(),
                 card.stability,
                 card.last_review.isoformat() if card.last_review else None),
            )
            if cur.rowcount:
                created.append(item_id)
    return created


def remove_orphans(conn):
    """Удалить «осиротевшие» карточки (item_id больше не резолвится в контент)
    вместе с их записями в журнале. Возвращает число удалённых карточек.

    НЕ вызывается автоматически: потеря прогресса необратима, а в обычной работе
    движок такие карточки и так игнорирует (counts/get_queue/forecast их не
    считают). Это ручная очистка — когда контент удалён осознанно и насовсем."""
    rows = conn.execute("SELECT id, item_type, item_id FROM srs_cards").fetchall()
    orphans = [(r["id"],) for r in rows if not item_exists(r["item_type"], r["item_id"])]
    if orphans:
        with conn:
            conn.executemany("DELETE FROM reviews WHERE card_id = ?", orphans)
            conn.executemany("DELETE FROM srs_cards WHERE id = ?", orphans)
    return len(orphans)


def _auto_thresholds(conn, exercise_type):
    rows = conn.execute(
        "SELECT duration_ms FROM reviews "
        "WHERE correct = 1 AND duration_ms BETWEEN 200 AND 60000 "
        "AND exercise_type = ? ORDER BY id DESC LIMIT 200",
        (exercise_type,),
    ).fetchall()
    times = sorted(r["duration_ms"] for r in rows)
    if len(times) < MIN_SAMPLES:
        return DEFAULT_THRESHOLDS.get(exercise_type, (DEFAULT_P25, DEFAULT_P75))
    p25 = times[len(times) // 4]
    p75 = times[(len(times) * 3) // 4]
    return p25, max(p75, p25 + 500)


def auto_rate(conn, correct, duration_ms, exercise_type="", used_hint=False):
    """Раздел 4.2: автоматическая оценка для упражнений с проверкой."""
    if not correct:
        return Rating.Again
    p25, p75 = _auto_thresholds(conn, exercise_type)
    if used_hint or (duration_ms is not None and duration_ms > p75):
        return Rating.Hard
    if duration_ms is not None and duration_ms < p25:
        return Rating.Easy
    return Rating.Good


def answer_card(conn, settings, card_row, correct, duration_ms,
                exercise_type, used_hint=False, tz_offset_min=None):
    """Применить ответ: FSRS-пересчёт, журнал, пиявки. Возвращает сводку."""
    scheduler = make_scheduler(settings)
    card = Card.from_dict(json.loads(card_row["fsrs"]))
    state_before = card.state.value
    rating = auto_rate(conn, correct, duration_ms, exercise_type, used_hint)
    now = _now()

    card, _log = scheduler.review_card(card, rating, review_datetime=now)

    reps = card_row["reps"] + 1
    lapses = card_row["lapses"] + (1 if rating == Rating.Again and state_before in (2, 3) else 0)
    is_leech = 1 if lapses >= LEECH_LAPSES else card_row["is_leech"]
    introduced_on = card_row["introduced_on"] or local_today(tz_offset_min).isoformat()

    with conn:
        conn.execute(
            "UPDATE srs_cards SET fsrs=?, state=?, due_at=?, reps=?, lapses=?, "
            "is_leech=?, introduced_on=?, stability=?, last_review=? WHERE id=?",
            (json.dumps(card.to_dict()), card.state.value, card.due.isoformat(),
             reps, lapses, is_leech, introduced_on,
             card.stability,
             card.last_review.isoformat() if card.last_review else None,
             card_row["id"]),
        )
        conn.execute(
            "INSERT INTO reviews(card_id, reviewed_at, rating, state_before, "
            "correct, duration_ms, exercise_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (card_row["id"], now.isoformat(), rating.value, state_before,
             1 if correct else 0, duration_ms, exercise_type),
        )

    return {
        "rating": rating.value,
        "rating_label": {1: "Снова", 2: "Трудно", 3: "Хорошо", 4: "Легко"}[rating.value],
        "next_due": card.due.isoformat(),
        "state": card.state.value,
        "is_leech": bool(is_leech),
        "stability": card.stability,
        "difficulty": card.difficulty,
    }


def _retrievability(scheduler, card_row):
    # Быстрый путь: считаем R из денормализованных колонок (stability/last_review)
    # по формуле FSRS-v6 — без парсинга JSON на каждую карточку. Паритет с
    # библиотекой закреплён тестом (tests/test_srs.py). Приватные _FACTOR/_DECAY
    # зависят только от параметров модели (не от desired_retention) → константны.
    keys = card_row.keys()
    stability = card_row["stability"] if "stability" in keys else None
    last = card_row["last_review"] if "last_review" in keys else None
    if stability and last:
        try:
            elapsed = max(0, (_now() - datetime.fromisoformat(last)).days)
            return (1 + scheduler._FACTOR * elapsed / stability) ** scheduler._DECAY
        except Exception:
            pass
    # Фолбэк: старая строка без колонок (до миграции) — разбираем JSON.
    card = Card.from_dict(json.loads(card_row["fsrs"]))
    try:
        return float(scheduler.get_card_retrievability(card))
    except Exception:
        return 1.0


def retrievability(scheduler, card_row):
    """Текущая вероятность вспомнить карточку (FSRS R, 0..1) — публичная обёртка
    для «силы памяти» в /api/learned. card_row должен содержать колонку fsrs."""
    return _retrievability(scheduler, card_row)


def new_introduced_today(conn, tz_offset_min=None):
    today = local_today(tz_offset_min).isoformat()
    return conn.execute(
        "SELECT COUNT(*) AS c FROM srs_cards WHERE introduced_on = ?", (today,)
    ).fetchone()["c"]


def reviews_done_today(conn, tz_offset_min=None):
    today = local_today(tz_offset_min).isoformat()
    return conn.execute(
        f"SELECT COUNT(*) AS c FROM reviews WHERE {day_sql('reviewed_at', tz_offset_min)} = ?",
        (today,),
    ).fetchone()["c"]


def get_queue(conn, settings, limit=30, tz_offset_min=None):
    """Очередь сессии по правилам раздела 4.4."""
    scheduler = make_scheduler(settings)
    now = _now()
    horizon = (now + LEARNING_LOOKAHEAD).isoformat()

    due = conn.execute(
        "SELECT * FROM srs_cards WHERE reps > 0 AND due_at <= ? "
        "ORDER BY due_at LIMIT 500",
        (horizon,),
    ).fetchall()
    # Осиротевшие карточки (item_id больше не резолвится) пропускаем — не подаём
    # их в сессию (review_exercise вернул бы None) и не даём перекосить счётчики.
    due = [r for r in due if item_exists(r["item_type"], r["item_id"])]
    # Просроченные — по возрастанию вероятности вспоминания (риск забывания)
    due = sorted(due, key=lambda r: _retrievability(scheduler, r))

    reviews_left = max(
        int(settings["reviews_per_day"]) - reviews_done_today(conn, tz_offset_min), 0)
    queue = list(due[:min(limit, reviews_left) if reviews_left else 0])

    # Новые карточки в пределах дневного лимита
    new_left = max(
        int(settings["new_per_day"]) - new_introduced_today(conn, tz_offset_min), 0)
    slots = max(limit - len(queue), 0)
    need = min(new_left, slots)
    if need:
        fresh = conn.execute(
            "SELECT * FROM srs_cards WHERE reps = 0 ORDER BY id LIMIT 500"
        ).fetchall()
        fresh = [r for r in fresh if item_exists(r["item_type"], r["item_id"])][:need]
        queue.extend(fresh)

    # Перемешивание подачи (4.4), родственные знаки не идут подряд
    if len(queue) > 3:
        head, tail = queue[:1], queue[1:]
        random.shuffle(tail)
        queue = head + tail
    return queue


def counts(conn, settings, tz_offset_min=None):
    # Тот же горизонт И тот же дневной лимит, что в get_queue, иначе числа на
    # кнопке «Начать сессию» расходятся с фактической очередью: при исчерпанном
    # лимите повторений сессия не отдаст просроченные карточки, а счётчик их
    # показывал бы.
    horizon = (_now() + LEARNING_LOOKAHEAD).isoformat()
    # Считаем только резолвимые карточки — иначе «due»/«новые» на кнопке обещали
    # бы осиротевшие карточки, которых сессия не покажет (см. get_queue).
    due_rows = conn.execute(
        "SELECT item_type, item_id FROM srs_cards WHERE reps > 0 AND due_at <= ?",
        (horizon,),
    ).fetchall()
    due_count = sum(1 for r in due_rows if item_exists(r["item_type"], r["item_id"]))
    new_rows = conn.execute(
        "SELECT item_type, item_id FROM srs_cards WHERE reps = 0"
    ).fetchall()
    new_total = sum(1 for r in new_rows if item_exists(r["item_type"], r["item_id"]))
    done_today = reviews_done_today(conn, tz_offset_min)
    reviews_left = max(int(settings["reviews_per_day"]) - done_today, 0)
    new_left_today = max(
        int(settings["new_per_day"]) - new_introduced_today(conn, tz_offset_min), 0)
    return {
        "due": min(due_count, reviews_left),
        "new_available": min(new_total, new_left_today),
        "new_total": new_total,
        "reviews_done_today": done_today,
    }


# Упреждающее повторение (USP «сила памяти»): карточки, которые скоро войдут в
# «зону забывания» — станут due в ближайшие UPCOMING_WINDOW, но ещё НЕ просрочены
# (то есть в обычную очередь пока не попадают). Освежить их сейчас дешевле, чем
# потом переучивать сорвавшуюся «пиявку»; ответы идут через обычный answer_card —
# это настоящий ранний повтор, FSRS сам учтёт ранний показ (меньший прирост S).
UPCOMING_WINDOW = timedelta(days=2)


def _upcoming_rows(conn, full=False):
    now = _now()
    after = (now + LEARNING_LOOKAHEAD).isoformat()   # строго позже обычной очереди
    until = (now + UPCOMING_WINDOW).isoformat()
    cols = "*" if full else "item_type, item_id"
    rows = conn.execute(
        f"SELECT {cols} FROM srs_cards WHERE reps > 0 AND due_at > ? AND due_at <= ? "
        "ORDER BY due_at LIMIT 500",
        (after, until),
    ).fetchall()
    return [r for r in rows if item_exists(r["item_type"], r["item_id"])]


def upcoming(conn, limit=20):
    """Карточки для упреждающего повторения (см. UPCOMING_WINDOW), ближайшие к due."""
    return _upcoming_rows(conn, full=True)[:limit]


def upcoming_count(conn):
    """Сколько карточек скоро войдёт в зону забывания (для подсказки на «Сегодня»)."""
    return len(_upcoming_rows(conn))


def forecast(conn, days=14, tz_offset_min=None):
    """Сколько карточек станет due в каждый из ближайших дней."""
    rows = conn.execute(
        f"SELECT item_type, item_id, {day_sql('due_at', tz_offset_min)} AS d "
        "FROM srs_cards WHERE reps > 0"
    ).fetchall()
    by_date = {}
    for r in rows:                              # осиротевшие карточки не учитываем
        if item_exists(r["item_type"], r["item_id"]):
            by_date[r["d"]] = by_date.get(r["d"], 0) + 1
    today = local_today(tz_offset_min)
    out = []
    backlog = sum(c for d, c in by_date.items() if d and d < today.isoformat())
    for i in range(days):
        d = today + timedelta(days=i)
        c = by_date.get(d.isoformat(), 0)
        if i == 0:
            c += backlog
        out.append({"date": d.isoformat(), "count": c})
    return out
