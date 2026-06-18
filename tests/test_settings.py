# -*- coding: utf-8 -*-
"""API настроек SRS (GET/POST /api/settings).

Оживляет db.set_setting; границы Field оберегают очередь и планировщик
FSRS от значений, которые их ломают. Ходим через TestClient — настройки
теперь живут в персональной базе пользователя (анонимная cookie-сессия).
"""
import pytest
from pydantic import ValidationError

from app import db, main


def test_update_persists(client):
    out = client.post("/api/settings", json={
        "new_per_day": 20, "reviews_per_day": 300, "desired_retention": 0.95}).json()
    assert (out["new_per_day"], out["reviews_per_day"], out["desired_retention"]) \
        == (20, 300, 0.95)
    assert client.get("/api/settings").json() == out      # перечитали из БД — то же


def test_partial_update_keeps_others(client):
    before = client.get("/api/settings").json()
    client.post("/api/settings", json={"new_per_day": 8})
    after = client.get("/api/settings").json()
    assert after["new_per_day"] == 8
    assert after["reviews_per_day"] == before["reviews_per_day"]
    assert after["desired_retention"] == before["desired_retention"]


def test_new_user_gets_defaults(client):
    # Незнакомый пользователь (чтение без создания базы) видит дефолты.
    assert client.get("/api/settings").json() == db.DEFAULT_SETTINGS


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
