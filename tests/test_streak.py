# -*- coding: utf-8 -*-
"""Серия дней и «щиты выходного» (_streak_info в app.main).

Правила: каждые 7 подряд активных дней дают щит (запас ≤ 2); пропуск ровно
одного дня при наличии щита не сжигает серию (щит тратится); пропуск 2+ дней
подряд сжигает всегда. Всё выводится из журнала — состояние в БД не добавлялось.
"""
from datetime import date, timedelta

from app import main


def _practice_on(conn, d):
    """Активность в локальный день d: полдень UTC попадает в те же локальные
    сутки при смещениях до ±11 часов — детерминированно для тестовой машины."""
    cur = conn.execute(
        "INSERT INTO srs_cards(item_type, item_id, fsrs, state, reps) "
        "VALUES ('kana', ?, '{}', 2, 1)", (f"т{d}",))
    conn.execute(
        "INSERT INTO reviews(card_id, reviewed_at, rating, correct) "
        "VALUES (?, ?, 3, 1)", (cur.lastrowid, f"{d.isoformat()} 12:00:00"))


def _seed(conn, offsets):
    """offsets — дни назад от сегодня (0 = сегодня), в любом порядке."""
    today = date.today()
    with conn:
        for n in offsets:
            _practice_on(conn, today - timedelta(days=n))


def test_empty_journal(conn):
    assert main._streak_info(conn) == {"streak": 0, "freezes": 0}


def test_consecutive_days(conn):
    _seed(conn, [2, 1, 0])
    assert main._streak_info(conn) == {"streak": 3, "freezes": 0}


def test_yesterday_only_still_alive(conn):
    # Сегодня ещё не занимался — серия не сгорела
    _seed(conn, [1])
    assert main._streak_info(conn) == {"streak": 1, "freezes": 0}


def test_gap_without_shield_breaks(conn):
    # 3 дня, пропуск, сегодня: щита ещё нет — серия началась заново
    _seed(conn, [5, 4, 3, 1, 0])
    assert main._streak_info(conn) == {"streak": 2, "freezes": 0}


def test_seven_days_earn_shield(conn):
    _seed(conn, range(7))
    assert main._streak_info(conn) == {"streak": 7, "freezes": 1}


def test_shield_bridges_single_gap(conn):
    # 7 дней → щит; выходной; возвращение — серия жива, щит потрачен
    _seed(conn, [8, 7, 6, 5, 4, 3, 2, 0])
    assert main._streak_info(conn) == {"streak": 8, "freezes": 0}


def test_shield_covers_missed_yesterday(conn):
    # Вчера пропущен, сегодня ещё не занимался, но щит есть — серия жива
    _seed(conn, [8, 7, 6, 5, 4, 3, 2])
    assert main._streak_info(conn) == {"streak": 7, "freezes": 1}


def test_no_shield_missed_yesterday_dies(conn):
    _seed(conn, [5, 4, 3, 2])
    assert main._streak_info(conn) == {"streak": 0, "freezes": 0}


def test_two_day_gap_breaks_even_with_shield(conn):
    # Щит кроет ровно один день: пропуск двух подряд сжигает серию
    _seed(conn, [9, 8, 7, 6, 5, 4, 3, 0])
    assert main._streak_info(conn) == {"streak": 1, "freezes": 0}


def test_shields_stack_to_max_two(conn):
    _seed(conn, range(21))
    assert main._streak_info(conn) == {"streak": 21, "freezes": 2}


def test_overview_exposes_freezes(client):
    r = client.get("/api/overview")
    assert r.status_code == 200
    body = r.json()
    assert "streak_freezes" in body and body["streak_freezes"] == 0
