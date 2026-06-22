# -*- coding: utf-8 -*-
"""Резервная копия (db.backup_to / restore_from / is_michi_db).

Снимок и восстановление идут через SQLite backup API; восстановление кладёт
страховочный .bak и возвращает счётчики. Работает с персональной базой
пользователя (data/users/<uid>.db) — каталог баз изолирован во временной папке.
"""
import pathlib
import sqlite3

import pytest

from app import db

UID = "backuptestuser000000"          # подходит под db._UID_RE (16–64 urlsafe)


@pytest.fixture
def uid(tmp_path, monkeypatch):
    """Изолирует каталог per-user баз и отдаёт фиксированный uid для теста."""
    monkeypatch.setattr(db, "DATA_DIR", tmp_path / "users")
    return UID


def _seed(uid, cards=1, reviews=1):
    c = db.connect(uid)
    with c:
        for i in range(cards):
            c.execute("INSERT INTO srs_cards(item_type, item_id, fsrs, state, reps) "
                      "VALUES ('kana', ?, '{}', 1, 0)", (f"к{i}",))
        for _ in range(reviews):
            c.execute("INSERT INTO reviews(card_id, reviewed_at, rating) "
                      "VALUES (1, '2026-01-01T00:00:00', 3)")
    c.close()


def test_export_import_roundtrip(uid, tmp_path):
    _seed(uid, cards=3, reviews=5)
    snap = str(tmp_path / "snap.db")
    db.backup_to(snap, uid)
    assert db.is_michi_db(snap)

    # стираем живую базу — как «переустановка» (сначала журнал: FK reviews→cards)
    c = db.connect(uid)
    with c:
        c.execute("DELETE FROM reviews")
        c.execute("DELETE FROM srs_cards")
    c.close()

    cards, reviews = db.restore_from(snap, uid)
    assert (cards, reviews) == (3, 5)

    c = db.connect(uid)
    assert c.execute("SELECT COUNT(*) FROM srs_cards").fetchone()[0] == 3
    assert c.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 5
    c.close()


def test_restore_writes_safety_backup(uid):
    _seed(uid, cards=2, reviews=0)
    snap = str(db._user_path(uid)) + ".snap"
    db.backup_to(snap, uid)
    db.restore_from(snap, uid)
    bak = pathlib.Path(str(db._user_path(uid)) + ".bak")
    assert bak.exists() and db.is_michi_db(str(bak))


def test_ui_prefs_survive_backup_roundtrip(uid, tmp_path):
    """UI-настройки лежат в той же БД → бэкап их переносит (раньше — только SRS)."""
    c = db.connect(uid)
    with c:
        c.execute("INSERT INTO ui_prefs(key, value) VALUES ('michi_theme', 'dark')")
        c.execute("INSERT INTO ui_prefs(key, value) VALUES ('michi_lang', 'en')")
    c.close()
    snap = str(tmp_path / "snap.db")
    db.backup_to(snap, uid)

    c = db.connect(uid)                                    # стираем живые настройки
    with c:
        c.execute("DELETE FROM ui_prefs")
    c.close()

    db.restore_from(snap, uid)
    c = db.connect(uid)
    prefs = {r["key"]: r["value"] for r in c.execute("SELECT key, value FROM ui_prefs")}
    c.close()
    assert prefs == {"michi_theme": "dark", "michi_lang": "en"}


def test_restore_old_backup_recreates_ui_prefs(uid, tmp_path):
    """Старая копия (без ui_prefs) восстанавливается, а таблица доукомплектовывается
    схемой — иначе /api/prefs упёрся бы в её отсутствие до перезапуска сервера."""
    old = str(tmp_path / "old.db")
    oc = sqlite3.connect(old)
    with oc:
        oc.execute("CREATE TABLE srs_cards (id INTEGER PRIMARY KEY, item_type TEXT, "
                   "item_id TEXT, fsrs TEXT, state INTEGER, reps INTEGER DEFAULT 0)")
        oc.execute("CREATE TABLE reviews (id INTEGER PRIMARY KEY, card_id INTEGER, "
                   "reviewed_at TEXT, rating INTEGER)")
        oc.execute("CREATE TABLE lesson_progress (lesson_id TEXT PRIMARY KEY)")
        oc.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT)")
    oc.close()
    assert db.is_michi_db(old)                             # старый бэкап остаётся валидным

    db.restore_from(old, uid)

    raw = sqlite3.connect(db._user_path(uid))              # без SCHEMA — проверяем сам файл
    tables = {r[0] for r in raw.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    raw.close()
    assert "ui_prefs" in tables


def test_delete_user_removes_all_files(uid):
    _seed(uid, cards=2, reviews=1)
    snap = str(db._user_path(uid)) + ".snap"
    db.backup_to(snap, uid)
    db.restore_from(snap, uid)                       # создаёт страховочный <uid>.db.bak
    path = db._user_path(uid)
    assert path.exists() and pathlib.Path(str(path) + ".bak").exists()

    assert db.delete_user(uid) is True
    for suffix in ("", "-wal", "-shm", ".bak"):       # ни основного, ни sidecar-файлов
        assert not pathlib.Path(str(path) + suffix).exists()


def test_delete_user_idempotent_when_absent(uid):
    assert db.delete_user(uid) is False               # нечего удалять — не падает


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
