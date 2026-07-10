# -*- coding: utf-8 -*-
"""UI-настройки клиента (GET/POST /api/prefs).

Зеркало localStorage в БД: переносится между устройствами и попадает в бэкап.
Аллой-лист (db.UI_PREF_KEYS) защищает таблицу от посторонних ключей. Ходим через
TestClient — префы хранятся в персональной базе пользователя.
"""


def test_set_and_get(client):
    out = client.post("/api/prefs", json={
        "michi_theme": "dark", "michi_daily_goal": "40"}).json()
    assert out == {"michi_theme": "dark", "michi_daily_goal": "40"}
    assert client.get("/api/prefs").json() == out          # перечитали из БД — то же


def test_update_then_delete(client):
    client.post("/api/prefs", json={"michi_lang": "en"})
    client.post("/api/prefs", json={"michi_lang": "ru"})   # обновление значения
    assert client.get("/api/prefs").json()["michi_lang"] == "ru"
    client.post("/api/prefs", json={"michi_lang": None})   # None удаляет ключ
    assert "michi_lang" not in client.get("/api/prefs").json()


def test_unknown_keys_ignored(client):
    # посторонние и транзиентные ключи в БД не попадают (только аллой-лист)
    client.post("/api/prefs", json={
        "michi_theme": "light", "evil": "x", "michi_lesson_resume": "{}"})
    assert client.get("/api/prefs").json() == {"michi_theme": "light"}


def test_values_stored_verbatim(client):
    # michi_tts/haptics — JSON-строки localStorage; храним как есть, без разбора
    blob = '{"source":"neural","volume":0.7}'
    client.post("/api/prefs", json={"michi_tts": blob})
    assert client.get("/api/prefs").json()["michi_tts"] == blob


def test_oversized_value_rejected(client):
    # Защита диска: мегабайтные «настройки» — абуз, отсекаются до записи (413).
    # Худший легитимный случай (словарь мнемоник, десятки КБ) проходит.
    big = "x" * 1_000_000
    assert client.post("/api/prefs", json={"michi_mnemo_custom": big}).status_code == 413
    assert "michi_mnemo_custom" not in client.get("/api/prefs").json()
    ok = "x" * 50_000
    assert client.post("/api/prefs", json={"michi_mnemo_custom": ok}).status_code == 200
