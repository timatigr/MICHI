# -*- coding: utf-8 -*-
"""Тесты-ворота юнита (SRS.md раздел 3): порог 80% и корректная выдача.

Регрессии, которые здесь стерегутся:
- `_lesson_group` не должен падать на id ворот (вида «v-g1»);
- провал ворот (< 80%) не завершает их и не открывает следующий юнит;
- сдача ворот (≥ 80%) завершает их и открывает следующий юнит.

Прогресс лежит в персональной базе пользователя — ходим через TestClient и
засеваем предыдущие уроки прямо в его базу (uid берём из cookie сессии).
"""
from app import db, identity, main
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


def _uid(client):
    client.get("/api/overview")                            # выдаёт cookie-сессию
    return identity.parse(client.cookies.get(identity.COOKIE_NAME))


def _seed_completed_until(uid, gate_id):
    """Помечает все уроки до ворот пройденными, чтобы ворота стали доступны."""
    c = db.connect(uid)
    with c:
        for lid in LESSON_ORDER:
            if lid == gate_id:
                break
            c.execute(
                "INSERT OR REPLACE INTO lesson_progress"
                "(lesson_id, status, score, attempts, completed_at) "
                "VALUES (?, 'completed', 1.0, 1, '2026-01-01T00:00:00')", (lid,))
    c.close()


def _statuses(client):
    return {l["id"]: l["status"] for l in client.get("/api/lessons").json()}


def test_failing_gate_does_not_unlock_next_unit(client):
    gate = GATES[0]
    next_id = LESSON_ORDER[LESSON_ORDER.index(gate["id"]) + 1]
    _seed_completed_until(_uid(client), gate["id"])

    res = client.post(f"/api/lessons/{gate['id']}/complete", json={"score": 0.5}).json()
    assert res["is_gate"] and res["passed"] is False

    st = _statuses(client)
    assert st[gate["id"]] != "completed"                   # ворота не сданы
    assert st[next_id] == "locked"                         # юнит не открылся


def test_passing_gate_unlocks_next_unit(client):
    gate = GATES[0]
    next_id = LESSON_ORDER[LESSON_ORDER.index(gate["id"]) + 1]
    _seed_completed_until(_uid(client), gate["id"])

    res = client.post(f"/api/lessons/{gate['id']}/complete",
                      json={"score": GATE_PASS}).json()
    assert res["is_gate"] and res["passed"] is True

    st = _statuses(client)
    assert st[gate["id"]] == "completed"
    assert st[next_id] == "available"
