# -*- coding: utf-8 -*-
"""Справочник изученного («Словарь»): раскладка карточек по курсам.

Тестируем чистую функцию-маппер _learned_display (БД не трогает): карточки
сворачиваются в логические элементы и попадают в верный курс.
"""
from app.content.registry import GRAMMAR, KANA, KANJI, VOCAB
from app.main import _learned_display


def test_kana_routes_by_script():
    h = next(k for k in KANA if k.get("script") == "h")
    course, d = _learned_display("kana", h["char"])
    assert course == "hiragana"
    assert d["title"] == h["char"] and d["tts"] == h["char"] and d["sub"] == h["romaji"]
    k = next(k for k in KANA if k.get("script") == "k")
    assert _learned_display("kana", k["char"])[0] == "katakana"


def test_vocab_both_cards_map_to_one_n5_item():
    w = VOCAB[0]
    for item_type in ("vocab_jp_ru", "vocab_ru_jp"):
        course, d = _learned_display(item_type, w["id"])
        assert course == "n5"
        assert d["title"] == w["kana"] and d["sub"] == w["ru"] and d["tts"] == w["kana"]


def test_kanji_three_skills_map_to_one_kanji_item():
    k = KANJI[0]
    for item_type in ("kanji_meaning", "kanji_reading", "kanji_writing"):
        course, d = _learned_display(item_type, k["char"])
        assert course == "kanji"
        assert d["title"] == k["char"] and d["sub"] == k["meaning"]


def test_grammar_maps_to_grammar_course():
    g = GRAMMAR[0]
    course, d = _learned_display("grammar", g["id"])
    assert course == "grammar"
    assert d["title"] == g["title"]
    # Озвучка точки — её первый пример целиком (раньше молчала в словаре)
    ex = g["examples"][0]
    assert d["tts"] == (ex.get("reading") or "".join(ex["tokens"]))


def test_unknown_items_return_none():
    assert _learned_display("kana", "НЕТ_ТАКОГО") is None
    assert _learned_display("vocab_jp_ru", "no_such_word") is None
    assert _learned_display("kanji_meaning", "Z") is None
    assert _learned_display("mystery", "x") is None


def test_learned_reports_memory_strength(client):
    """«Сила памяти»: новые карточки — strength None, после повторения — число 0..100."""
    lessons = client.get("/api/lessons").json()
    lid = next(l for l in lessons if l["status"] == "available")["id"]
    client.post(f"/api/lessons/{lid}/complete", json={"score": 1.0})

    items = [it for c in client.get("/api/learned").json()["courses"] for it in c["items"]]
    assert items, "после урока должны быть изученные элементы"
    assert all("strength" in it for it in items)
    assert all(it["strength"] is None for it in items if it["state"] == "new")

    card = client.get("/api/srs/queue?limit=20").json()["items"][0]
    client.post("/api/srs/answer", json={
        "card_id": card["card_id"], "correct": True,
        "exercise_type": card["exercise"]["type"]})
    after = [it for c in client.get("/api/learned").json()["courses"] for it in c["items"]]
    strengths = [it["strength"] for it in after if it["strength"] is not None]
    assert strengths, "после повторения должна появиться числовая сила памяти"
    assert all(0 <= s <= 100 for s in strengths)
