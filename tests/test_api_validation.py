# -*- coding: utf-8 -*-
"""Валидация границ параметров API.

Отрицательный limit в срезах вида queue[:limit] молча отдавал бы почти всю
выборку без лимита, а неограниченный duration_ms (10**30) ронял бы запись в
SQLite переполнением 64 бит (500 вместо 422). Границы объявлены в app.main
(Query(**_LIMIT), Field у Answer) — здесь закрепляем контракт.
"""


def test_limit_bounds_rejected(client):
    for url in ("/api/srs/queue", "/api/srs/upcoming", "/api/review/mistakes",
                "/api/listen/pairs", "/api/counters/rounds", "/api/pitch/rounds",
                "/api/confusions", "/api/confusions/rounds",
                "/api/forge/rounds", "/api/shiritori/rounds"):
        assert client.get(f"{url}?limit=-5").status_code == 422, url
        assert client.get(f"{url}?limit=100000").status_code == 422, url
        assert client.get(url).status_code == 200, url          # дефолт валиден


def test_answer_duration_bounded(client):
    huge = {"card_id": 1, "correct": True, "duration_ms": 10 ** 30}
    assert client.post("/api/srs/answer", json=huge).status_code == 422
    neg = {"card_id": 1, "correct": True, "duration_ms": -1}
    assert client.post("/api/srs/answer", json=neg).status_code == 422
