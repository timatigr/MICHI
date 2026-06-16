# -*- coding: utf-8 -*-
"""Резервная копия (db.backup_to / restore_from / is_michi_db).

Снимок и восстановление идут через SQLite backup API; восстановление кладёт
страховочный .bak и возвращает счётчики.
"""
import sqlite3

import pytest

from app import db


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """db.DB_PATH и db.connect указывают на изолированную файловую БД."""
    dbfile = tmp_path / "michi.db"
    monkeypatch.setattr(db, "DB_PATH", dbfile)

    def _connect():
        c = sqlite3.connect(dbfile)
        c.row_factory = sqlite3.Row
        c.executescript(db.SCHEMA)
        return c

    monkeypatch.setattr(db, "connect", _connect)
    return _connect


def _seed(connect, cards=1, reviews=1):
    c = connect()
    with c:
        for i in range(cards):
            c.execute("INSERT INTO srs_cards(item_type, item_id, fsrs, state, reps) "
                      "VALUES ('kana', ?, '{}', 1, 0)", (f"к{i}",))
        for _ in range(reviews):
            c.execute("INSERT INTO reviews(card_id, reviewed_at, rating) "
                      "VALUES (1, '2026-01-01T00:00:00', 3)")
    c.close()


def test_export_import_roundtrip(temp_db, tmp_path):
    _seed(temp_db, cards=3, reviews=5)
    snap = str(tmp_path / "snap.db")
    db.backup_to(snap)
    assert db.is_michi_db(snap)

    # стираем живую базу — как «переустановка»
    c = temp_db()
    with c:
        c.execute("DELETE FROM srs_cards")
        c.execute("DELETE FROM reviews")
    c.close()

    cards, reviews = db.restore_from(snap)
    assert (cards, reviews) == (3, 5)

    c = temp_db()
    assert c.execute("SELECT COUNT(*) FROM srs_cards").fetchone()[0] == 3
    assert c.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 5
    c.close()


def test_restore_writes_safety_backup(temp_db, tmp_path):
    _seed(temp_db, cards=2, reviews=0)
    snap = str(tmp_path / "snap.db")
    db.backup_to(snap)
    db.restore_from(snap)
    bak = tmp_path / "michi.db.bak"
    assert bak.exists() and db.is_michi_db(str(bak))


def test_is_michi_db_rejects_non_sqlite(tmp_path):
    junk = tmp_path / "x.db"
    junk.write_bytes(b"definitely not a database")
    assert db.is_michi_db(str(junk)) is False


def test_is_michi_db_rejects_foreign_schema(tmp_path):
    other = tmp_path / "other.db"
    c = sqlite3.connect(str(other))
    with c:
        c.execute("CREATE TABLE notes (id INTEGER)")
    c.close()
    assert db.is_michi_db(str(other)) is False
