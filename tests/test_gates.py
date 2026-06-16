# -*- coding: utf-8 -*-
"""Тесты-ворота юнита (SRS.md раздел 3): порог 80% и корректная выдача.

Регрессии, которые здесь стерегутся:
- `_lesson_group` не должен падать на id ворот (вида «v-g1»);
- провал ворот (< 80%) не завершает их и не открывает следующий юнит;
- сдача ворот (≥ 80%) завершает их и открывает следующий юнит.
"""
import sqlite3

import pytest

from app import db, main
from app.content.registry import GATE_PASS, LESSON_ORDER, LESSONS

GATES = [l for l in LESSONS if l.get("type") == "gate_test"]


def test_lesson_group_handles_every_id():
    # Раньше падало с ValueError на «v-g1»: int('-g1')
    for l in LESSONS:
        g = main._lesson_group(l["id"])
        assert "id" in g and g["title"]


def test_gate_shares_region_with_its_unit():
    # Плитка ворот должна попадать в тот же регион, что и уроки её юнита
    for gate in GATES:
        unit_lesson = next(LESSONS[i] for i, l in enumerate(LESSONS)
                           if l["id"] == gate["src_lessons"][-1])
        assert main._lesson_group(gate["id"])["id"] == \
            main._lesson_group(unit_lesson["id"])["id"]


@pytest.fixture
def patched_db(tmp_path, monkeypatch):
    """Подменяет db.connect на изолированную файловую БД (а не michi.db)."""
    dbfile = str(tmp_path / "gate_test.db")

    def _connect():
        c = sqlite3.connect(dbfile)
        c.row_factory = sqlite3.Row
        c.executescript(db.SCHEMA)
        return c

    monkeypatch.setattr(db, "connect", _connect)
    return _connect


def _seed_completed_until(connect, gate_id):
    """Помечает все уроки до ворот пройденными, чтобы ворота стали доступны."""
    c = connect()
    with c:
        for lid in LESSON_ORDER:
            if lid == gate_id:
                break
            c.execute(
                "INSERT OR REPLACE INTO lesson_progress"
                "(lesson_id, status, score, attempts, completed_at) "
                "VALUES (?, 'completed', 1.0, 1, '2026-01-01T00:00:00')", (lid,))
    c.close()


def test_failing_gate_does_not_unlock_next_unit(patched_db):
    gate = GATES[0]
    next_id = LESSON_ORDER[LESSON_ORDER.index(gate["id"]) + 1]
    _seed_completed_until(patched_db, gate["id"])

    res = main.complete_lesson(gate["id"], main.LessonResult(score=0.5))
    assert res["is_gate"] and res["passed"] is False

    conn = patched_db()
    statuses = main._lesson_statuses(conn)
    conn.close()
    assert statuses[gate["id"]]["status"] != "completed"   # ворота не сданы
    assert statuses[next_id]["status"] == "locked"          # юнит не открылся


def test_passing_gate_unlocks_next_unit(patched_db):
    gate = GATES[0]
    next_id = LESSON_ORDER[LESSON_ORDER.index(gate["id"]) + 1]
    _seed_completed_until(patched_db, gate["id"])

    res = main.complete_lesson(gate["id"], main.LessonResult(score=GATE_PASS))
    assert res["is_gate"] and res["passed"] is True

    conn = patched_db()
    statuses = main._lesson_statuses(conn)
    conn.close()
    assert statuses[gate["id"]]["status"] == "completed"
    assert statuses[next_id]["status"] == "available"
