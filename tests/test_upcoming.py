# -*- coding: utf-8 -*-
"""Упреждающее повторение: карточки, которые скоро войдут в зону забывания
(srs_engine.upcoming/upcoming_count) и их выдача через API."""
from datetime import datetime, timedelta, timezone

from app import srs_engine


def _now():
    return datetime.now(timezone.utc)


def _set_due(conn, item_id, due, reps=1, state=2):
    conn.execute(
        "UPDATE srs_cards SET reps=?, state=?, due_at=? WHERE item_id=?",
        (reps, state, due.isoformat(), item_id))
    conn.commit()


def test_upcoming_window_selects_soon_but_not_overdue(conn):
    srs_engine.create_cards(conn, "kana", ["あ", "い", "う", "え"])
    now = _now()
    _set_due(conn, "あ", now - timedelta(hours=1))            # уже просрочена → в обычной очереди
    _set_due(conn, "い", now + timedelta(hours=12))           # в окне → upcoming
    _set_due(conn, "う", now + timedelta(days=1, hours=18))   # в окне (<2 дн) → upcoming
    _set_due(conn, "え", now + timedelta(days=5))             # далеко → не upcoming
    assert {r["item_id"] for r in srs_engine.upcoming(conn)} == {"い", "う"}
    assert srs_engine.upcoming_count(conn) == 2


def test_upcoming_ordered_by_due_and_capped(conn):
    chars = ["か", "き", "く", "け", "こ"]
    srs_engine.create_cards(conn, "kana", chars)
    now = _now()
    for i, c in enumerate(chars):                            # все в окне, разное время
        _set_due(conn, c, now + timedelta(hours=2 + i))
    rows = srs_engine.upcoming(conn, limit=3)
    assert [r["item_id"] for r in rows] == ["か", "き", "く"]  # ближайшие к due, лимит соблюдён


def test_upcoming_excludes_new_cards(conn):
    srs_engine.create_cards(conn, "kana", ["さ"])             # reps=0 (новая)
    conn.execute("UPDATE srs_cards SET due_at=? WHERE item_id='さ'",
                 ((_now() + timedelta(hours=6)).isoformat(),))
    conn.commit()
    assert srs_engine.upcoming_count(conn) == 0               # новые карточки не считаются


def test_overview_exposes_upcoming(client):
    body = client.get("/api/overview").json()
    assert "upcoming" in body and isinstance(body["upcoming"], int)


def test_upcoming_endpoint_shape(client):
    body = client.get("/api/srs/upcoming").json()
    assert "items" in body and isinstance(body["items"], list)
