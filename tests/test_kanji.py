# -*- coding: utf-8 -*-
"""Курс кандзи: три навыка-карточки, генераторы и сценарий урока."""
from app.content.registry import (
    COURSES, KANJI, KANJI_BY_CHAR, LESSON_BY_ID, srs_items_for_lesson,
)
from app.exercises import (
    item_info, kanji_meaning, kanji_reading, make_lesson_steps, review_exercise,
)


def test_kanji_course_registered():
    ids = [c["id"] for c in COURSES]
    assert "kanji" in ids
    kanji_course = next(c for c in COURSES if c["id"] == "kanji")
    assert kanji_course["lesson_ids"]  # есть уроки


def test_each_kanji_has_required_fields():
    for k in KANJI:
        assert k["char"] and k["meaning"] and k["reading"]
        assert k["examples"], f"{k['char']} без примеров"
        assert k["reading"] == k["examples"][0]["r"]  # каноничное чтение = первый пример


def test_kanji_lesson_makes_three_skill_cards_per_char():
    lesson = LESSON_BY_ID["j01"]
    items = srs_items_for_lesson(lesson)
    assert {t for t, _ in items} == {"kanji_meaning", "kanji_reading", "kanji_writing"}
    assert len(items) == 3 * len(lesson["kanji"])


def test_kanji_lesson_steps_have_intro_and_exercises():
    steps = make_lesson_steps("j01")
    types = {s["type"] for s in steps}
    assert "intro_kanji" in types
    ex_types = {s["exercise"]["type"] for s in steps if s["type"] == "exercise"}
    assert "kanji_meaning" in ex_types
    assert "kanji_reading" in ex_types


def test_review_exercise_kanji_skills():
    ch = KANJI[0]["char"]
    assert review_exercise("kanji_meaning", ch)["type"] == "kanji_meaning"
    assert review_exercise("kanji_reading", ch)["type"] == "kanji_reading"
    w = review_exercise("kanji_writing", ch)
    # написание появляется только при наличии данных черт KanjiVG
    assert w is None or w["type"] == "kanji_tracing"
    assert review_exercise("kanji_meaning", "НЕТ") is None


def test_kanji_reading_hides_answer_until_response():
    ex = kanji_reading(KANJI_BY_CHAR["一"])
    assert ex["prompt"]["tts"] is None      # не озвучиваем чтение заранее
    assert ex["answer_tts"]                  # но даём озвучку после ответа
    assert ex["options"][ex["answer"]] == KANJI_BY_CHAR["一"]["reading"]


def test_kanji_meaning_answer_is_correct_meaning():
    ex = kanji_meaning(KANJI_BY_CHAR["十"])
    assert ex["options"][ex["answer"]] == "десять"


def test_item_info_kanji():
    info = item_info("kanji_meaning", "五")
    assert info["title"] == "五"
    assert info["sub"] == "пять"


def test_kanji_components_reference_known_kanji():
    for k in KANJI:
        for c in k.get("components", []):
            assert c["char"] in KANJI_BY_CHAR, \
                f"{k['char']}: компонент {c['char']} не введён как кандзи"


def test_kanji_components_introduced_earlier():
    """i+1 (6.3): компонент вводится в более раннем уроке, чем составной знак."""
    order = {}
    kanji_course = next(c for c in COURSES if c["id"] == "kanji")
    for pos, lid in enumerate(kanji_course["lesson_ids"]):
        # в курс вставлены тесты-ворота юнита (gate_test) — у них нет "kanji"
        for ch in LESSON_BY_ID[lid].get("kanji", []):
            order.setdefault(ch, pos)
    for k in KANJI:
        kp = order[k["char"]]
        for c in k.get("components", []):
            assert order[c["char"]] < kp, \
                f"{k['char']} (урок {kp}) использует {c['char']} из урока {order[c['char']]}"


def test_kanji_reading_options_are_unique_and_correct():
    for k in KANJI:
        ex = kanji_reading(k)
        assert len(set(ex["options"])) == len(ex["options"]), \
            f"{k['char']}: повтор в вариантах {ex['options']}"
        assert ex["options"][ex["answer"]] == k["reading"]
