# -*- coding: utf-8 -*-
"""Радар путаницы: запись/агрегация пар «выбрал X вместо Y» и миграция схемы v3."""
import sqlite3

from app import db


def test_record_and_top(conn):
    db.record_confusion(conn, "kana", "あ", "お")
    db.record_confusion(conn, "kana", "あ", "お")
    db.record_confusion(conn, "kana", "シ", "ツ")
    top = db.top_confusions(conn)
    assert top[0]["item_id"] == "あ" and top[0]["confused_with"] == "お"
    assert top[0]["count"] == 2                       # пара инкрементируется
    assert ("シ", "ツ") in {(r["item_id"], r["confused_with"]) for r in top}


def test_record_ignores_self_and_empty(conn):
    db.record_confusion(conn, "kana", "あ", "あ")     # знак сам с собой
    db.record_confusion(conn, "kana", "", "お")
    db.record_confusion(conn, "kana", "あ", "")
    assert db.top_confusions(conn) == []


def test_top_respects_limit(conn):
    for c in "かきくけこさしすせそ":
        db.record_confusion(conn, "kana", "あ", c)
    assert len(db.top_confusions(conn, limit=3)) == 3


def _complete_first_lesson(client):
    lessons = client.get("/api/lessons").json()
    lid = next(l for l in lessons if l["status"] == "available")["id"]
    client.post(f"/api/lessons/{lid}/complete", json={"score": 1.0})


def test_confusions_empty_for_fresh_user(client):
    assert client.get("/api/confusions").json()["pairs"] == []
    assert client.get("/api/confusions/rounds").json()["rounds"] == []


def test_wrong_kana_answer_records_and_surfaces(client):
    _complete_first_lesson(client)
    card = client.get("/api/srs/queue?limit=20").json()["items"][0]
    correct = card["exercise"]["item_id"]
    wrong = "お" if correct != "お" else "あ"
    client.post("/api/srs/answer", json={
        "card_id": card["card_id"], "correct": False,
        "exercise_type": card["exercise"]["type"], "confused_with": wrong,
    })
    pairs = client.get("/api/confusions").json()["pairs"]
    assert pairs and pairs[0]["a"] == correct and pairs[0]["b"] == wrong
    assert pairs[0]["count"] >= 1 and pairs[0]["a_romaji"]
    # дрилл строит различение из этой пары: верный знак по чтению из двух
    rounds = client.get("/api/confusions/rounds").json()["rounds"]
    assert rounds and set(rounds[0]["options"]) == {correct, wrong}
    assert rounds[0]["options"][rounds[0]["answer"]] == correct


def test_correct_answer_records_no_confusion(client):
    _complete_first_lesson(client)
    card = client.get("/api/srs/queue?limit=20").json()["items"][0]
    client.post("/api/srs/answer", json={
        "card_id": card["card_id"], "correct": True,
        "exercise_type": card["exercise"]["type"], "confused_with": "お",
    })
    assert client.get("/api/confusions").json()["pairs"] == []


def test_migration_v2_to_v3_creates_confusions(tmp_path):
    """База v2 без confusions поднимается до текущей версии и получает таблицу."""
    p = tmp_path / "old.db"
    c = sqlite3.connect(p)
    c.execute("PRAGMA user_version = 2")
    c.execute("CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    c.commit()
    c.close()
    conn = db._prepare(sqlite3.connect(p))
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == db.SCHEMA_VERSION
        db.record_confusion(conn, "kana", "ソ", "ン")          # таблица пишется
        assert db.top_confusions(conn)[0]["item_id"] == "ソ"
    finally:
        conn.close()
