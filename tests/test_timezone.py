# -*- coding: utf-8 -*-
"""Локальные сутки пользователя на публичном хостинге (per-user TZ-offset).

reviewed_at/due_at хранятся в UTC; «день» (серия, «сегодня», дневные лимиты)
считается по смещению пользователя из заголовка X-TZ-Offset. None → серверные
локальные сутки (как в одно-пользовательском режиме)."""
import datetime as dt

from app import main, srs_engine


def test_day_sql_buckets_by_user_local_midnight(conn):
    # Повторение в 23:30 UTC 19 июня попадает в разные «дни» при разном смещении.
    conn.execute("INSERT INTO srs_cards(item_type,item_id,fsrs,state) "
                 "VALUES('kana','あ','{}',1)")
    conn.execute("INSERT INTO reviews(card_id,reviewed_at,rating) "
                 "VALUES(1,'2026-06-19T23:30:00+00:00',3)")

    def day(tz):
        return conn.execute(
            f"SELECT {srs_engine.day_sql('reviewed_at', tz)} AS d FROM reviews"
        ).fetchone()["d"]

    assert day(0) == "2026-06-19"        # UTC
    assert day(60) == "2026-06-20"       # UTC+1 — уже завтра (00:30)
    assert day(-60) == "2026-06-19"      # UTC-1 — ещё 22:30 того же дня


def test_hour_sql_buckets_by_user_local_time(conn):
    # Повтор в 02:00 UTC — «ночь» только в поясах около UTC; для UTC+4 это утро.
    # Подпирает «ночную сову» и «XP за сегодня» в геймификации (per-user TZ).
    conn.execute("INSERT INTO srs_cards(item_type,item_id,fsrs,state) "
                 "VALUES('kana','あ','{}',1)")
    conn.execute("INSERT INTO reviews(card_id,reviewed_at,rating) "
                 "VALUES(1,'2026-06-19T02:00:00+00:00',3)")

    def hour(tz):
        return conn.execute(
            f"SELECT CAST({srs_engine.hour_sql('reviewed_at', tz)} AS INTEGER) AS h "
            "FROM reviews"
        ).fetchone()["h"]

    assert hour(0) == 2          # UTC — 02:00 (ночь)
    assert hour(240) == 6        # UTC+4 — 06:00 (уже утро)
    assert hour(-180) == 23      # UTC-3 — 23:00 предыдущего дня


def test_local_today_modes():
    assert srs_engine.local_today() == dt.datetime.now().date()   # None → серверные сутки
    assert isinstance(srs_engine.local_today(180), dt.date)       # со смещением — тоже дата


def _req(headers):
    return type("R", (), {"headers": headers})()


def test_tz_offset_parsing_and_clamp():
    assert main._tz_offset_min(_req({})) is None                       # нет заголовка
    assert main._tz_offset_min(_req({"x-tz-offset": "180"})) == 180    # UTC+3
    assert main._tz_offset_min(_req({"x-tz-offset": "-300"})) == -300  # UTC-5
    assert main._tz_offset_min(_req({"x-tz-offset": "bad"})) is None   # мусор
    assert main._tz_offset_min(_req({"x-tz-offset": "99999"})) == 840  # зажато ±14ч


def test_overview_accepts_tz_header(client):
    # Сквозной путь: заголовок принимается, overview не падает и считает «сегодня».
    r = client.get("/api/overview", headers={"X-TZ-Offset": "120"})
    assert r.status_code == 200
    assert "today" in r.json() and "streak" in r.json()
