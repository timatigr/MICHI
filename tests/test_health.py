# -*- coding: utf-8 -*-
"""Проверка живости /api/health (аптайм-мониторинг на публичном хостинге).

Инварианты: всегда 200 {"ok": true}; пинг монитора раз в минуту не должен
плодить состояния — ни одной per-user базы от таких запросов не появляется.
"""
from app import db


def test_health_ok_and_stateless(make_client):
    c = make_client()
    r = c.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    assert not db.DATA_DIR.exists() or list(db.DATA_DIR.glob("*.db")) == []
