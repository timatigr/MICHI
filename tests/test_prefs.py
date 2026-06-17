# -*- coding: utf-8 -*-
"""UI-настройки клиента (db.get_ui_prefs/set_ui_pref, main.prefs_get/prefs_set).

Зеркало localStorage в БД: переносится между устройствами и попадает в бэкап.
Аллой-лист (db.UI_PREF_KEYS) защищает таблицу от посторонних ключей.
"""
import sqlite3

import pytest

from app import db, main


@pytest.fixture
def patched_db(tmp_path, monkeypatch):
    dbfile = str(tmp_path / "prefs_test.db")

    def _connect():
        c = sqlite3.connect(dbfile)
        c.row_factory = sqlite3.Row
        c.executescript(db.SCHEMA)
        return c

    monkeypatch.setattr(db, "connect", _connect)
    return _connect


def test_set_and_get(patched_db):
    out = main.prefs_set({"michi_theme": "dark", "michi_daily_goal": "40"})
    assert out == {"michi_theme": "dark", "michi_daily_goal": "40"}
    assert main.prefs_get() == out                    # перечитали из БД — то же


def test_update_then_delete(patched_db):
    main.prefs_set({"michi_lang": "en"})
    main.prefs_set({"michi_lang": "ru"})              # обновление значения
    assert main.prefs_get()["michi_lang"] == "ru"
    main.prefs_set({"michi_lang": None})              # None удаляет ключ
    assert "michi_lang" not in main.prefs_get()


def test_unknown_keys_ignored(patched_db):
    # посторонние и транзиентные ключи в БД не попадают (только аллой-лист)
    main.prefs_set({"michi_theme": "light", "evil": "x", "michi_lesson_resume": "{}"})
    assert main.prefs_get() == {"michi_theme": "light"}


def test_values_stored_verbatim(patched_db):
    # michi_tts/haptics — JSON-строки localStorage; храним как есть, без разбора
    blob = '{"source":"neural","volume":0.7}'
    main.prefs_set({"michi_tts": blob})
    assert main.prefs_get()["michi_tts"] == blob
