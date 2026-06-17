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


def _local_today():
    """Дневные сущности (стрик, лимиты, «сегодня») живут по локальным суткам
    пользователя; в SQL им соответствует date(..., 'localtime')."""
    return datetime.now().date()


def make_scheduler(settings):
    return Scheduler(desired_retention=float(settings.get("desired_retention", 0.9)))


def create_cards(conn, item_type, item_ids):
    """Создать SRS-карточки (вызывается при завершении урока). Идемпотентно."""
    created = []
    with conn:
        for item_id in item_ids:
            card = Card()
            cur = conn.execute(
                "INSERT OR IGNORE INTO srs_cards(item_type, item_id, fsrs, state, due_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (item_type, item_id, json.dumps(card.to_dict()),
                 card.state.value, card.due.isoformat()),
            )
            if cur.rowcount:
                created.append(item_id)
    return created


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
                exercise_type, used_hint=False):
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
    introduced_on = card_row["introduced_on"] or _local_today().isoformat()

    with conn:
        conn.execute(
            "UPDATE srs_cards SET fsrs=?, state=?, due_at=?, reps=?, lapses=?, "
            "is_leech=?, introduced_on=? WHERE id=?",
            (json.dumps(card.to_dict()), card.state.value, card.due.isoformat(),
             reps, lapses, is_leech, introduced_on, card_row["id"]),
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
        "interval_human": _humanize(card.due - now),
        "state": card.state.value,
        "is_leech": bool(is_leech),
        "stability": card.stability,
        "difficulty": card.difficulty,
    }


def _humanize(delta):
    secs = max(delta.total_seconds(), 0)
    if secs < 90:
        return "через минуту"
    if secs < 3600:
        return f"через {round(secs / 60)} мин"
    if secs < 86400 * 1.5:
        return f"через {round(secs / 3600)} ч"
    days = round(secs / 86400)
    return f"через {days} дн"


def _retrievability(scheduler, card_row):
    card = Card.from_dict(json.loads(card_row["fsrs"]))
    try:
        return float(scheduler.get_card_retrievability(card))
    except Exception:
        return 1.0


def new_introduced_today(conn):
    today = _local_today().isoformat()
    return conn.execute(
        "SELECT COUNT(*) AS c FROM srs_cards WHERE introduced_on = ?", (today,)
    ).fetchone()["c"]


def reviews_done_today(conn):
    today = _local_today().isoformat()
    return conn.execute(
        "SELECT COUNT(*) AS c FROM reviews WHERE date(reviewed_at, 'localtime') = ?",
        (today,),
    ).fetchone()["c"]


def get_queue(conn, settings, limit=30):
    """Очередь сессии по правилам раздела 4.4."""
    scheduler = make_scheduler(settings)
    now = _now()
    horizon = (now + LEARNING_LOOKAHEAD).isoformat()

    due = conn.execute(
        "SELECT * FROM srs_cards WHERE reps > 0 AND due_at <= ? "
        "ORDER BY due_at LIMIT 500",
        (horizon,),
    ).fetchall()
    # Просроченные — по возрастанию вероятности вспоминания (риск забывания)
    due = sorted(due, key=lambda r: _retrievability(scheduler, r))

    reviews_left = max(int(settings["reviews_per_day"]) - reviews_done_today(conn), 0)
    queue = list(due[:min(limit, reviews_left) if reviews_left else 0])

    # Новые карточки в пределах дневного лимита
    new_left = max(int(settings["new_per_day"]) - new_introduced_today(conn), 0)
    slots = max(limit - len(queue), 0)
    if new_left and slots:
        fresh = conn.execute(
            "SELECT * FROM srs_cards WHERE reps = 0 ORDER BY id LIMIT ?",
            (min(new_left, slots),),
        ).fetchall()
        queue.extend(fresh)

    # Перемешивание подачи (4.4), родственные знаки не идут подряд
    if len(queue) > 3:
        head, tail = queue[:1], queue[1:]
        random.shuffle(tail)
        queue = head + tail
    return queue


def counts(conn, settings):
    # Тот же горизонт И тот же дневной лимит, что в get_queue, иначе числа на
    # кнопке «Начать сессию» расходятся с фактической очередью: при исчерпанном
    # лимите повторений сессия не отдаст просроченные карточки, а счётчик их
    # показывал бы.
    horizon = (_now() + LEARNING_LOOKAHEAD).isoformat()
    due_count = conn.execute(
        "SELECT COUNT(*) AS c FROM srs_cards WHERE reps > 0 AND due_at <= ?",
        (horizon,),
    ).fetchone()["c"]
    new_total = conn.execute(
        "SELECT COUNT(*) AS c FROM srs_cards WHERE reps = 0"
    ).fetchone()["c"]
    done_today = reviews_done_today(conn)
    reviews_left = max(int(settings["reviews_per_day"]) - done_today, 0)
    new_left_today = max(int(settings["new_per_day"]) - new_introduced_today(conn), 0)
    return {
        "due": min(due_count, reviews_left),
        "new_available": min(new_total, new_left_today),
        "new_total": new_total,
        "reviews_done_today": done_today,
    }


def forecast(conn, days=14):
    """Сколько карточек станет due в каждый из ближайших дней."""
    rows = conn.execute(
        "SELECT date(due_at, 'localtime') AS d, COUNT(*) AS c FROM srs_cards "
        "WHERE reps > 0 GROUP BY date(due_at, 'localtime')"
    ).fetchall()
    by_date = {r["d"]: r["c"] for r in rows}
    today = _local_today()
    out = []
    backlog = sum(c for d, c in by_date.items() if d and d < today.isoformat())
    for i in range(days):
        d = today + timedelta(days=i)
        c = by_date.get(d.isoformat(), 0)
        if i == 0:
            c += backlog
        out.append({"date": d.isoformat(), "count": c})
    return out
