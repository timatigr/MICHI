# -*- coding: utf-8 -*-
"""Геймификация v1: XP, уровень, достижения (раздел 8)."""
from app import gamification


def _add_lesson(conn, lid="v01"):
    conn.execute("INSERT INTO lesson_progress(lesson_id, status, completed_at) "
                 "VALUES (?, 'completed', datetime('now'))", (lid,))


def _add_card_review(conn, item_type="kana", item_id="あ", correct=1):
    cur = conn.execute(
        "INSERT INTO srs_cards(item_type, item_id, fsrs, state, reps) "
        "VALUES (?, ?, '{}', 2, 1)", (item_type, item_id))
    conn.execute("INSERT INTO reviews(card_id, reviewed_at, rating, correct) "
                 "VALUES (?, datetime('now'), 3, ?)", (cur.lastrowid, correct))


def test_xp_empty(conn):
    xp = gamification.xp_summary(conn)
    assert xp["total"] == 0 and xp["today"] == 0 and xp["level"] == 1


def test_xp_accumulates(conn):
    with conn:
        _add_lesson(conn)                     # +20
        _add_card_review(conn, "kana", "あ")  # +2
        _add_card_review(conn, "kana", "い")  # +2
    xp = gamification.xp_summary(conn)
    assert xp["total"] == 24
    assert xp["today"] == 24                  # всё сделано «сегодня»


def test_level_curve(conn):
    # уровень n требует 50·(n-1)²: 0→L1, 50→L2, 200→L3
    assert gamification._level(0)["level"] == 1
    assert gamification._level(50)["level"] == 2
    assert gamification._level(200)["level"] == 3
    assert 0 <= gamification._level(120)["percent"] <= 100


def test_achievements_unlock(conn):
    a0 = gamification.achievements(conn, streak=0)
    assert a0["total"] == len(gamification.ACHIEVEMENTS)
    locked = {i["id"]: i["unlocked"] for i in a0["items"]}
    assert locked["first_lesson"] is False
    with conn:
        _add_lesson(conn)
    a1 = gamification.achievements(conn, streak=0)
    by = {i["id"]: i["unlocked"] for i in a1["items"]}
    assert by["first_lesson"] is True
    assert a1["unlocked"] >= 1


def test_achievements_streak_predicate(conn):
    a = gamification.achievements(conn, streak=7)
    by = {i["id"]: i["unlocked"] for i in a["items"]}
    assert by["streak_3"] and by["streak_7"]
    assert not by["streak_30"]


def test_night_owl_uses_user_timezone(conn):
    # Повтор в 02:00 UTC: «ночь» (<5 ч) только в поясах около UTC; для UTC+4 —
    # уже 06:00. Достижение «ночная сова» должно считаться по дню пользователя,
    # а не сервера (F1: рассинхрон TZ в геймификации).
    with conn:
        cur = conn.execute(
            "INSERT INTO srs_cards(item_type,item_id,fsrs,state,reps) "
            "VALUES('kana','あ','{}',2,1)")
        conn.execute(
            "INSERT INTO reviews(card_id,reviewed_at,rating,correct) "
            "VALUES(?, '2026-06-19T02:00:00+00:00', 3, 1)", (cur.lastrowid,))
    assert gamification._stats(conn, 0, tz_offset_min=0)["night_review"] is True
    assert gamification._stats(conn, 0, tz_offset_min=240)["night_review"] is False
