# -*- coding: utf-8 -*-
"""Общие фикстуры тестов.

Движковые тесты работают с изолированной in-memory БД (фикстуры conn/settings):
srs_engine принимает соединение и settings параметрами, поэтому тесты не трогают
рабочие базы. API-тесты ходят через TestClient (фикстуры client/make_client) —
каждый клиент = свой «браузер» со своей cookie-сессией и своей per-user базой в
изолированном каталоге (db.DATA_DIR подменён на временный).
"""
import sqlite3

import pytest

from app import db


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(db.SCHEMA)
    yield c
    c.close()


@pytest.fixture
def settings():
    return dict(db.DEFAULT_SETTINGS)


@pytest.fixture
def make_client(tmp_path, monkeypatch):
    """Фабрика TestClient'ов поверх изолированного каталога per-user баз.

    Разные клиенты получают разные анонимные cookie-сессии (uid) и потому не
    видят данных друг друга — это позволяет проверять изоляцию пользователей.
    MICHI_SECRET_KEY задаём, чтобы подпись cookie не писала secret.key в репозиторий.
    """
    monkeypatch.setattr(db, "DATA_DIR", tmp_path / "users")
    monkeypatch.setenv("MICHI_SECRET_KEY", "test-secret-key-not-for-prod")
    # Рейт-лимит — инфраструктурная защита, не предмет API-тестов: они шлют много
    # запросов с одного «IP» (TestClient) и иначе ловили бы 429. Сам лимитер
    # включается явно в tests/test_ratelimit.py.
    monkeypatch.setenv("MICHI_RATELIMIT_ENABLED", "0")
    from fastapi.testclient import TestClient

    from app import main

    return lambda: TestClient(main.app)


@pytest.fixture
def client(make_client):
    return make_client()
