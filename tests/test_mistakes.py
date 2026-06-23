# -*- coding: utf-8 -*-
"""«Разбор ошибок дня»: overview.mistakes_today + /api/review/mistakes (практика).

Эндпоинт read-only: карточки, в которых сегодня ошиблись, отдаются как упражнения,
но фронт ответы не шлёт — расписание/журнал не меняются (проверяем здесь только
выдачу набора, не запись).
"""


def _first_available_lesson(client):
    lessons = client.get("/api/lessons").json()
    return next(l for l in lessons if l["status"] == "available")


def test_no_mistakes_for_fresh_user(client):
    assert client.get("/api/overview").json()["mistakes_today"] == 0
    assert client.get("/api/review/mistakes").json()["items"] == []


def test_wrong_answer_today_shows_in_mistakes(client):
    # Пройти первый урок → создаются SRS-карточки
    lid = _first_available_lesson(client)["id"]
    client.post(f"/api/lessons/{lid}/complete", json={"score": 1.0})

    # Ответить на одну карточку из очереди неверно
    queue = client.get("/api/srs/queue?limit=20").json()["items"]
    assert queue, "после урока очередь не должна быть пустой"
    card = queue[0]
    client.post("/api/srs/answer", json={
        "card_id": card["card_id"], "correct": False,
        "exercise_type": card["exercise"]["type"],
    })

    # overview видит сегодняшнюю ошибку
    assert client.get("/api/overview").json()["mistakes_today"] >= 1

    # эндпоинт практики отдаёт её как упражнение
    items = client.get("/api/review/mistakes").json()["items"]
    assert len(items) >= 1
    assert "exercise" in items[0] and "type" in items[0]["exercise"]


def test_correct_answer_not_counted_as_mistake(client):
    lid = _first_available_lesson(client)["id"]
    client.post(f"/api/lessons/{lid}/complete", json={"score": 1.0})
    card = client.get("/api/srs/queue?limit=20").json()["items"][0]
    client.post("/api/srs/answer", json={
        "card_id": card["card_id"], "correct": True,
        "exercise_type": card["exercise"]["type"],
    })
    assert client.get("/api/overview").json()["mistakes_today"] == 0
    assert client.get("/api/review/mistakes").json()["items"] == []
