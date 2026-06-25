# -*- coding: utf-8 -*-
"""Минимальные пары на слух: контент, генератор раундов и эндпоинт."""
from app.content.minimal_pairs import PAIRS
from app.exercises import minimal_pair_rounds


def test_pairs_wellformed():
    assert PAIRS, "пары не должны быть пустыми"
    for p in PAIRS:
        assert p["kind"] in ("long", "geminate")
        for side in ("a", "b"):
            w = p[side]
            assert w["kana"] and w["romaji"] and w["ru"]
        assert p["a"]["kana"] != p["b"]["kana"]          # это пара, а не дубль
        # различие должно быть «в одну мору» — длины каны отличаются на 1
        assert abs(len(p["a"]["kana"]) - len(p["b"]["kana"])) == 1


def test_rounds_shape_and_answer_points_at_played():
    rounds = minimal_pair_rounds(8)
    assert 1 <= len(rounds) <= len(PAIRS)
    for r in rounds:
        assert len(r["options"]) == 2 == len(r["romaji"]) == len(r["meanings"])
        assert r["options"][r["answer"]] == r["tts"]     # верный = проигранное слово
        assert r["tts"] in r["options"]


def test_rounds_respects_limit():
    assert len(minimal_pair_rounds(3)) == 3
    assert len(minimal_pair_rounds(999)) == len(PAIRS)   # не больше, чем есть пар


def test_endpoint_shape(client):
    body = client.get("/api/listen/pairs?limit=5").json()
    assert "rounds" in body and 1 <= len(body["rounds"]) <= 5
    r = body["rounds"][0]
    assert set(r) >= {"tts", "options", "romaji", "meanings", "answer", "kind"}
    assert r["options"][r["answer"]] == r["tts"]
