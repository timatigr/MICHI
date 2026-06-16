# -*- coding: utf-8 -*-
"""Инварианты лексики N5 (app/content/vocab_n5.py).

Проверяем целостность общего списка слов и уроков: уникальность id,
обязательные поля, и что каждое слово ровно один раз входит в какой-то урок.
"""
from app.content.vocab_n5 import LESSONS, UNITS, WORD_BY_ID, WORDS


def test_word_ids_are_unique():
    ids = [w["id"] for w in WORDS]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"дублирующиеся id слов: {sorted(dupes)}"
    # WORD_BY_ID не должен «съесть» слова из-за коллизии id
    assert len(WORD_BY_ID) == len(WORDS)


def test_each_word_has_required_fields():
    for w in WORDS:
        for field in ("id", "kana", "romaji", "ru"):
            assert w.get(field), f"{w.get('id', w)}: пустое поле {field}"
        assert w["kana"].strip(), f"{w['id']}: kana без каны"


def test_each_word_belongs_to_exactly_one_lesson():
    seen = {}
    for lesson in LESSONS:
        for wid in lesson["words"]:
            assert wid in WORD_BY_ID, f"{lesson['id']}: неизвестный id {wid}"
            assert wid not in seen, (
                f"слово {wid} входит и в {seen[wid]}, и в {lesson['id']}"
            )
            seen[wid] = lesson["id"]
    orphans = set(WORD_BY_ID) - set(seen)
    assert not orphans, f"слова без урока: {sorted(orphans)}"


def test_lessons_have_required_fields_and_known_unit():
    for lesson in LESSONS:
        for field in ("id", "type", "unit", "title", "subtitle", "icon", "words"):
            assert lesson.get(field) not in (None, ""), (
                f"{lesson.get('id', lesson)}: пустое поле {field}"
            )
        assert lesson["type"] == "vocab"
        assert lesson["unit"] in UNITS, f"{lesson['id']}: юнит {lesson['unit']} не в UNITS"
        assert lesson["words"], f"{lesson['id']}: пустой список words"


def test_lesson_ids_are_unique():
    ids = [l["id"] for l in LESSONS]
    assert len(ids) == len(set(ids)), "дублирующиеся id уроков"


def test_new_units_present():
    """Новые тематические юниты за пределами быта — глаголы и прилагательные."""
    assert {5, 6} <= set(UNITS)
    new_lesson_ids = {l["id"] for l in LESSONS if l["unit"] in (5, 6)}
    assert {"v13", "v14", "v15", "v16"} <= new_lesson_ids


def test_expansion_units_present():
    """Расширение N5: юниты 7–14 (время, места, транспорт, семья, природа,
    тело, цвета, вопросы) и уроки v17–v24."""
    assert set(range(7, 15)) <= set(UNITS)
    expansion_lesson_ids = {l["id"] for l in LESSONS if l["unit"] in range(7, 15)}
    assert {f"v{n}" for n in range(17, 25)} <= expansion_lesson_ids


def test_kana_strings_are_unique():
    """Каждая запись каны уникальна: одинаковые слова не должны дублироваться
    под разными id."""
    kana = [w["kana"] for w in WORDS]
    dupes = {k for k in kana if kana.count(k) > 1}
    # Допустимое исключение: いい встречается как существит. (suki-блок) и
    # как い-прилагательное (ii_adj) — это сознательный дубль из базовой части.
    dupes -= {"いい"}
    assert not dupes, f"дублирующаяся кана: {sorted(dupes)}"


def test_vocab_size_grew():
    """После расширения в курсе не меньше 230 слов."""
    assert len(WORDS) >= 230, f"слов всего: {len(WORDS)}"
