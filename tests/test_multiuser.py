# -*- coding: utf-8 -*-
"""Изоляция пользователей на публичном хостинге (анонимные cookie-сессии).

Инварианты:
- два разных «браузера» (клиента) получают разные uid и не видят данных друг друга;
- анонимный визит только на чтение не создаёт файл базы (защита от ботов/краулеров,
  которые иначе плодили бы пустые базы);
- uid стабилен между запросами одного клиента (cookie переживает запросы).
"""
from app import db, identity


def test_two_users_have_separate_data(make_client):
    a, b = make_client(), make_client()

    a.post("/api/settings", json={"new_per_day": 33})
    a.post("/api/prefs", json={"michi_theme": "dark"})

    # A видит своё
    assert a.get("/api/settings").json()["new_per_day"] == 33
    assert a.get("/api/prefs").json() == {"michi_theme": "dark"}
    # B не видит чужого — у него дефолты и пустые префы
    assert b.get("/api/settings").json()["new_per_day"] == db.DEFAULT_SETTINGS["new_per_day"]
    assert b.get("/api/prefs").json() == {}


def test_clients_get_distinct_uids(make_client):
    a, b = make_client(), make_client()
    a.get("/api/overview")
    b.get("/api/overview")
    uid_a = identity.parse(a.cookies.get(identity.COOKIE_NAME))
    uid_b = identity.parse(b.cookies.get(identity.COOKIE_NAME))
    assert uid_a and uid_b and uid_a != uid_b


def test_uid_is_stable_across_requests(make_client):
    c = make_client()
    c.get("/api/overview")
    uid1 = identity.parse(c.cookies.get(identity.COOKIE_NAME))
    c.get("/api/lessons")
    uid2 = identity.parse(c.cookies.get(identity.COOKIE_NAME))
    assert uid1 is not None and uid1 == uid2


def test_read_only_visit_creates_no_db_file(make_client):
    c = make_client()
    c.get("/api/overview")
    c.get("/api/lessons")
    c.get("/api/stats")
    c.get("/api/learned")
    assert not db.DATA_DIR.exists() or list(db.DATA_DIR.glob("*.db")) == []


def test_writing_creates_db_file(make_client):
    c = make_client()
    c.post("/api/prefs", json={"michi_theme": "dark"})
    assert db.DATA_DIR.exists() and list(db.DATA_DIR.glob("*.db"))


def test_account_delete_wipes_data_and_rotates_uid(make_client):
    c = make_client()
    c.post("/api/settings", json={"new_per_day": 33})
    c.post("/api/prefs", json={"michi_theme": "dark"})
    uid_before = identity.parse(c.cookies.get(identity.COOKIE_NAME))
    assert db._user_path(uid_before).exists()

    r = c.post("/api/account/delete")
    assert r.status_code == 200 and r.json()["ok"] is True

    # данные старого пользователя стёрты с диска
    assert not db._user_path(uid_before).exists()
    # выдан новый uid, и он начинает с чистого листа (дефолты, пустые префы)
    uid_after = identity.parse(c.cookies.get(identity.COOKIE_NAME))
    assert uid_after and uid_after != uid_before
    assert c.get("/api/settings").json()["new_per_day"] == db.DEFAULT_SETTINGS["new_per_day"]
    assert c.get("/api/prefs").json() == {}


def test_account_delete_only_touches_own_data(make_client):
    a, b = make_client(), make_client()
    a.post("/api/prefs", json={"michi_theme": "dark"})
    b.post("/api/prefs", json={"michi_theme": "light"})
    a.post("/api/account/delete")
    assert b.get("/api/prefs").json() == {"michi_theme": "light"}   # B не затронут


def test_cleanup_removes_only_empty_old(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", tmp_path / "users")
    # пустой пользователь — только UI-настройка, без учебной активности
    c = db.connect("emptyuser0000000000")
    with c:
        c.execute("INSERT INTO ui_prefs(key, value) VALUES ('michi_theme', 'dark')")
    c.close()
    # активный — есть карточка
    c = db.connect("activeuser000000000")
    with c:
        c.execute("INSERT INTO srs_cards(item_type, item_id, fsrs, state) "
                  "VALUES ('kana', 'あ', '{}', 1)")
    c.close()

    assert db.cleanup_stale_users(max_age_days=0) == 1
    assert not db._user_path("emptyuser0000000000").exists()   # пустой удалён
    assert db._user_path("activeuser000000000").exists()       # активный цел


def test_cleanup_keeps_recent_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", tmp_path / "users")
    c = db.connect("recentuser000000000")
    with c:
        c.execute("INSERT INTO ui_prefs(key, value) VALUES ('michi_theme', 'dark')")
    c.close()
    # свежую базу не трогаем, хоть и пустую (порог 30 дней)
    assert db.cleanup_stale_users(max_age_days=30) == 0
    assert db._user_path("recentuser000000000").exists()
