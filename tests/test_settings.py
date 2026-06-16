# -*- coding: utf-8 -*-
"""API настроек SRS (main.settings_get / settings_update).

Оживляет db.set_setting; границы Field оберегают очередь и планировщик
FSRS от значений, которые их ломают.
"""
import json
import sqlite3

import pytest
from pydantic import ValidationError

from app import db, main


@pytest.fixture
def patched_db(tmp_path, monkeypatch):
    """db.connect → изолированная файловая БД, засеянная дефолтами (как init_db)."""
    dbfile = str(tmp_path / "settings_test.db")

    def _connect():
        c = sqlite3.connect(dbfile)
        c.row_factory = sqlite3.Row
        c.executescript(db.SCHEMA)
        return c

    monkeypatch.setattr(db, "connect", _connect)
    c = _connect()
    with c:
        for k, v in db.DEFAULT_SETTINGS.items():
            c.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                      (k, json.dumps(v)))
    c.close()
    return _connect


def test_update_persists(patched_db):
    out = main.settings_update(main.SrsSettingsPatch(
        new_per_day=20, reviews_per_day=300, desired_retention=0.95))
    assert (out["new_per_day"], out["reviews_per_day"], out["desired_retention"]) \
        == (20, 300, 0.95)
    assert main.settings_get() == out          # перечитали из БД — то же самое


def test_partial_update_keeps_others(patched_db):
    before = main.settings_get()
    main.settings_update(main.SrsSettingsPatch(new_per_day=8))
    after = main.settings_get()
    assert after["new_per_day"] == 8
    assert after["reviews_per_day"] == before["reviews_per_day"]
    assert after["desired_retention"] == before["desired_retention"]


def test_boundary_values_accepted():
    main.SrsSettingsPatch(new_per_day=0, reviews_per_day=0, desired_retention=0.75)
    main.SrsSettingsPatch(new_per_day=100, reviews_per_day=2000, desired_retention=0.97)


@pytest.mark.parametrize("kwargs", [
    {"new_per_day": 200}, {"new_per_day": -1},
    {"reviews_per_day": 5000},
    {"desired_retention": 0.5}, {"desired_retention": 1.0},
])
def test_out_of_range_rejected(kwargs):
    with pytest.raises(ValidationError):
        main.SrsSettingsPatch(**kwargs)
