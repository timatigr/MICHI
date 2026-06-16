# -*- coding: utf-8 -*-
"""Спряжение глаголов N5 (тип 29 verb_conjugation)."""
import pytest

from app.content.verbs import VERB_BY_DICT, conjugate, distractors
from app.exercises import verb_conjugation


@pytest.mark.parametrize("dic,form,expected", [
    ("のむ", "masu", "のみます"),
    ("のむ", "mashita", "のみました"),
    ("のむ", "masen", "のみません"),
    ("のむ", "te", "のんで"),
    ("たべる", "masu", "たべます"),
    ("たべる", "te", "たべて"),
    ("かく", "te", "かいて"),
    ("はなす", "te", "はなして"),
    ("まつ", "te", "まって"),
    ("かう", "masu", "かいます"),
    ("かう", "te", "かって"),
    ("いく", "te", "いって"),     # исключение
    ("いく", "masu", "いきます"),
    ("する", "masu", "します"),
    ("する", "te", "して"),
    ("くる", "masu", "きます"),
    ("くる", "te", "きて"),
])
def test_conjugate(dic, form, expected):
    assert conjugate(VERB_BY_DICT[dic], form) == expected


def test_distractors_exclude_answer_and_are_unique():
    v = VERB_BY_DICT["のむ"]
    for form in ("masu", "mashita", "masen", "te"):
        ans = conjugate(v, form)
        ds = distractors(v, form, ans)
        assert len(ds) == 3
        assert ans not in ds
        assert len(set(ds)) == 3


def test_verb_conjugation_exercise_well_formed():
    ex = verb_conjugation(VERB_BY_DICT["のむ"], "masu")
    assert ex["type"] == "verb_conjugation"
    assert ex["options"][ex["answer"]] == "のみます"
    assert len(ex["options"]) == 4 and len(set(ex["options"])) == 4
    assert ex["options_are_kana"]
