# -*- coding: utf-8 -*-
"""Общие фикстуры тестов: изолированная in-memory БД и настройки по умолчанию.

srs_engine принимает соединение и settings параметрами, поэтому тесты не
трогают рабочий michi.db — каждый тест получает свежую базу в памяти.
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
