# -*- coding: utf-8 -*-
"""Метрики владельца (scripts/owner_stats.py).

Инварианты:
- агрегаты (пользователи, DAU, retention D1/D7/D30, воронка, сессии) считаются
  верно на известной картине активности;
- базы открываются read-only и mtime файлов не меняется (по mtime работает
  автоочистка заброшенных баз — скрипт статистики не должен «омолаживать» их);
- битые файлы пропускаются, не срывая отчёт.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app import db
from app.content.registry import LESSON_ORDER

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import owner_stats   # noqa: E402


def _at(days_ago, hour=12, minute=0):
    d = datetime.now(timezone.utc).date() - timedelta(days=days_ago)
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=timezone.utc)


def _mk_user(uid, review_times, lessons=()):
    c = db.connect(uid)
    with c:
        c.execute("INSERT INTO srs_cards(item_type, item_id, fsrs, state) "
                  "VALUES ('kana', 'あ', '{}', 1)")
        cid = c.execute("SELECT id FROM srs_cards").fetchone()["id"]
        for t in review_times:
            c.execute("INSERT INTO reviews(card_id, reviewed_at, rating, correct, "
                      "duration_ms, exercise_type) VALUES (?, ?, 3, 1, 1000, 'x')",
                      (cid, t.isoformat()))
        for lid in lessons:
            c.execute("INSERT INTO lesson_progress(lesson_id, status, completed_at) "
                      "VALUES (?, 'completed', ?)", (lid, review_times[-1].isoformat()))
    c.close()


@pytest.fixture
def two_users(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", tmp_path / "users")
    # A: первый день — 8 дней назад (3 ответа одной сессией), вернулся на D1;
    #    завершил первый урок пути.
    _mk_user("userA0000000000000A",
             [_at(8, 12, 0), _at(8, 12, 10), _at(8, 12, 20), _at(7, 9)],
             lessons=[LESSON_ORDER[0]])
    # B: новичок — единственный ответ сегодня.
    _mk_user("userB0000000000000B", [_at(0, 10)])
    return tmp_path / "users"


def test_aggregates(two_users):
    s = owner_stats.collect(two_users)

    assert s["users"] == {"total": 2, "active": 2, "returned": 1,
                          "skipped_files": 0}
    assert s["totals"] == {"reviews": 5, "accuracy": 1.0, "lessons_completed": 1}

    # retention: когорта D1 — только A (B слишком свежий), A вернулся на D1;
    # на D7 A не приходил; для D30 никто ещё не «дозрел».
    assert s["retention"]["D1"] == {"eligible": 1, "retained": 1, "rate": 1.0}
    assert s["retention"]["D7"] == {"eligible": 1, "retained": 0, "rate": 0.0}
    assert s["retention"]["D30"] == {"eligible": 0, "retained": 0, "rate": None}

    # сессии: у A две (день −8 и день −7), у B одна
    assert s["sessions"]["count"] == 3

    daily = {d["day"]: d for d in s["daily"]}
    today = datetime.now(timezone.utc).date()
    assert daily[today.isoformat()]["dau"] == 1
    assert daily[today.isoformat()]["reviews"] == 1
    assert daily[(today - timedelta(days=7)).isoformat()]["dau"] == 1
    assert daily[(today - timedelta(days=8)).isoformat()]["new_users"] == 1

    funnel = {f["step"]: f["users"] for f in s["funnel"]}
    assert funnel["заходили (есть база)"] == 2
    assert funnel["завершён ≥1 урок"] == 1
    assert funnel["завершено ≥5 уроков"] == 0


def test_broken_db_skipped(two_users):
    (two_users / "junk0000000000000000.db").write_text("не sqlite", encoding="utf-8")
    s = owner_stats.collect(two_users)
    assert s["users"]["skipped_files"] == 1
    assert s["users"]["total"] == 2          # живые базы посчитаны как раньше


def test_read_only_does_not_touch_mtime(two_users):
    target = two_users / "userA0000000000000A.db"
    before = target.stat().st_mtime_ns
    owner_stats.collect(two_users)
    assert target.stat().st_mtime_ns == before


def test_render_smoke(two_users):
    text = owner_stats.render(owner_stats.collect(two_users))
    assert "Retention" in text and "Воронка" in text and "D7" in text


def test_empty_dir(tmp_path):
    s = owner_stats.collect(tmp_path / "nope")
    assert s["users"]["total"] == 0
    assert s["retention"]["D1"]["rate"] is None
    assert s["sessions"]["median_minutes"] is None
    owner_stats.render(s)   # не падает на пустоте
