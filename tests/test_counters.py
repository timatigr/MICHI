# -*- coding: utf-8 -*-
"""Счётные суффиксы 助数詞: датасет и мини-игра."""
from app.content.counters import COUNTERS
from app.exercises import counter_rounds


def test_counters_dataset_shape():
    chars = set()
    for c in COUNTERS:
        assert c["counter"] and c["reading"] and c["meaning"]
        assert c["nouns"], f"{c['counter']} без примеров"
        for n in c["nouns"]:
            assert n["kana"] and n["ru"] and n["emoji"]
        chars.add(c["counter"])
    assert len(chars) == len(COUNTERS)               # счётные слова уникальны


def test_nouns_are_globally_unique():
    """Каждый предмет относится к одному счётному слову — иначе у раунда два
    верных ответа."""
    seen = {}
    for c in COUNTERS:
        for n in c["nouns"]:
            assert n["kana"] not in seen, \
                f"{n['kana']} и у {seen.get(n['kana'])}, и у {c['counter']}"
            seen[n["kana"]] = c["counter"]


def test_counter_rounds_answer_is_correct_counter():
    rounds = counter_rounds(limit=8)
    assert 1 <= len(rounds) <= 8
    valid = {c["counter"] for c in COUNTERS}
    for r in rounds:
        assert 2 <= r["count"] <= 5
        opts = [o["counter"] for o in r["options"]]
        assert len(set(opts)) == len(opts)           # без дублей-вариантов
        assert set(opts) <= valid
        ans = r["options"][r["answer"]]["counter"]
        owner = next(c["counter"] for c in COUNTERS
                     if any(n["kana"] == r["noun"]["kana"] for n in c["nouns"]))
        assert ans == owner                          # ответ — счётчик этого предмета


def test_counter_rounds_limit_zero():
    assert counter_rounds(limit=0) == []
