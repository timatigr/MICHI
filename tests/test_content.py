# -*- coding: utf-8 -*-
"""Инварианты учебного контента и реестра курсов."""
from app.content import registry, vocab_n5
from app.content.registry import (
    COURSES, LESSON_BY_ID, LESSONS, srs_items_for_lesson, tokenize_kana,
)

KANA_LESSON_IDS = {l["id"] for l in LESSONS if l.get("type") == "kana"}


def test_tokenize_yoon_and_sokuon():
    assert tokenize_kana("きょう") == ["きょ", "う"]   # ёон склеивается с базой
    assert tokenize_kana("きって") == ["き", "っ", "て"]  # сокуон — отдельный токен
    assert tokenize_kana("あい") == ["あ", "い"]


def test_courses_cover_all_lessons_without_overlap():
    in_courses = [lid for c in COURSES for lid in c["lesson_ids"]]
    assert sorted(in_courses) == sorted(l["id"] for l in LESSONS)
    assert len(in_courses) == len(set(in_courses))  # урок ровно в одном курсе


def test_vocab_lesson_makes_two_independent_cards_per_word():
    v = LESSON_BY_ID["v01"]
    items = srs_items_for_lesson(v)
    assert {t for t, _ in items} == {"vocab_jp_ru", "vocab_ru_jp"}
    assert len(items) == 2 * len(v["words"])


def test_kana_lesson_makes_one_card_per_kana():
    lid = COURSES[0]["lesson_ids"][0]
    lesson = LESSON_BY_ID[lid]
    items = srs_items_for_lesson(lesson)
    assert items == [("kana", c) for c in lesson["kana"]]


def test_i_plus_one_vocab_requires_only_kana_lessons():
    for l in vocab_n5.LESSONS:
        assert set(l["requires"]) <= KANA_LESSON_IDS


def test_i_plus_one_every_introduced_kana_is_in_requires():
    """Принцип i+1 (1.5, 2.1): если знак слова вводится каким-то уроком каны,
    этот урок обязан быть в requires словарного урока — иначе слово показалось
    бы раньше своей каны."""
    for l in vocab_n5.LESSONS:
        req = set(l["requires"])
        for wid in l["words"]:
            for tok in tokenize_kana(vocab_n5.WORD_BY_ID[wid]["kana"]):
                owner = registry._LESSON_OF_CHAR.get(tok)
                if owner is not None:
                    assert owner in req, (
                        f"{l['id']}: знак {tok!r} слова {wid} вводится в {owner}, "
                        f"которого нет в requires")
