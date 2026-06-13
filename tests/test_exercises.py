# -*- coding: utf-8 -*-
"""Генераторы упражнений и сценарии уроков."""
from app.content.registry import COURSES, KANA
from app.exercises import make_lesson_steps, review_exercise


def test_kana_lesson_steps_have_intro_and_valid_exercises():
    lid = COURSES[0]["lesson_ids"][0]
    steps = make_lesson_steps(lid)
    types = {s["type"] for s in steps}
    assert "intro_text" in types
    assert "exercise" in types
    for s in steps:
        if s["type"] == "exercise":
            assert "type" in s["exercise"]  # у упражнения есть машинное имя


def test_vocab_lesson_steps_build():
    steps = make_lesson_steps("v01")
    assert any(s["type"] == "intro_word" for s in steps)
    assert any(s["type"] == "exercise" for s in steps)


def test_review_exercise_rotates_by_reps():
    """Антиповторяемость (раздел 5): соседние повторения — разные типы."""
    ch = KANA[0]["char"]
    a = review_exercise("kana", ch, reps=0)
    b = review_exercise("kana", ch, reps=1)
    assert a["type"] != b["type"]


def test_review_exercise_unknown_item_returns_none():
    assert review_exercise("kana", "НЕТ_ТАКОГО_ЗНАКА") is None
    assert review_exercise("vocab_jp_ru", "no_such_word") is None
