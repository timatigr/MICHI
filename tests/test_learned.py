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
    assert d["title"] == g["title"] and d["tts"] is None


def test_unknown_items_return_none():
    assert _learned_display("kana", "НЕТ_ТАКОГО") is None
    assert _learned_display("vocab_jp_ru", "no_such_word") is None
    assert _learned_display("kanji_meaning", "Z") is None
    assert _learned_display("mystery", "x") is None
