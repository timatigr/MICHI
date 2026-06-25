# -*- coding: utf-8 -*-
"""Курс кандзи: три навыка-карточки, генераторы и сценарий урока."""
from app.content.registry import (
    COURSES, KANJI, KANJI_BY_CHAR, LESSON_BY_ID, RADICALS, srs_items_for_lesson,
)
from collections import Counter

from app.exercises import (
    item_info, kanji_forge_rounds, kanji_meaning, kanji_reading, make_lesson_steps,
    review_exercise,
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
    """Компонент — либо изученный кандзи, либо радикал из RADICALS (6.3)."""
    for k in KANJI:
        for c in k.get("components", []):
            assert c["char"] in KANJI_BY_CHAR or c["char"] in RADICALS, \
                f"{k['char']}: компонент {c['char']} не кандзи и не радикал"


def test_radical_components_use_canonical_image_name():
    """Радикал-компонент подписан своим именем-образом из RADICALS (6.3)."""
    for k in KANJI:
        for c in k.get("components", []):
            if c["char"] in RADICALS and c["char"] not in KANJI_BY_CHAR:
                assert c["meaning"] == RADICALS[c["char"]], \
                    f"{k['char']}: радикал {c['char']} подписан '{c['meaning']}', " \
                    f"а в RADICALS — '{RADICALS[c['char']]}'"


def test_radicals_are_not_also_taught_kanji():
    """Радикалы — это отдельный пласт неканзи-компонентов, не дубли курса."""
    for ch in RADICALS:
        assert ch not in KANJI_BY_CHAR, \
            f"{ch} есть и в RADICALS, и в курсе кандзи — выберите что-то одно"


def test_kanji_components_introduced_earlier():
    """i+1 (6.3): компонент-КАНДЗИ вводится в более раннем уроке, чем составной
    знак. Радикалы (неканзи) от этого правила освобождены — они показываются
    прямо в разборе со своим именем-образом."""
    order = {}
    kanji_course = next(c for c in COURSES if c["id"] == "kanji")
    for pos, lid in enumerate(kanji_course["lesson_ids"]):
        # в курс вставлены тесты-ворота юнита (gate_test) — у них нет "kanji"
        for ch in LESSON_BY_ID[lid].get("kanji", []):
            order.setdefault(ch, pos)
    for k in KANJI:
        kp = order[k["char"]]
        for c in k.get("components", []):
            if c["char"] not in KANJI_BY_CHAR:
                continue  # радикал — не требует предварительного урока
            assert order[c["char"]] < kp, \
                f"{k['char']} (урок {kp}) использует {c['char']} из урока {order[c['char']]}"


def test_kanji_reading_options_are_unique_and_correct():
    for k in KANJI:
        ex = kanji_reading(k)
        assert len(set(ex["options"])) == len(ex["options"]), \
            f"{k['char']}: повтор в вариантах {ex['options']}"
        assert ex["options"][ex["answer"]] == k["reading"]


# --- Кузница кандзи: сборка из компонентов ---

def _decomposable_chars():
    return {k["char"] for k in KANJI if len(k.get("components") or []) >= 2}


def test_forge_empty_without_learned_kanji():
    assert kanji_forge_rounds(set(), limit=5) == []


def test_forge_rounds_only_learned_decomposable():
    decomp = _decomposable_chars()
    assert decomp, "в курсе нет разложимых кандзи — «Кузница» осталась бы пустой"
    rounds = kanji_forge_rounds(decomp, limit=99)
    assert rounds and len(rounds) <= len(decomp)
    for r in rounds:
        assert r["char"] in decomp
        assert len(r["components"]) >= 2


def test_forge_tiles_cover_components_as_multiset():
    """Плитки содержат все компоненты цели с учётом повторов (林 = 木 + 木)."""
    rounds = kanji_forge_rounds(_decomposable_chars(), limit=99)
    for r in rounds:
        tiles = Counter(t["char"] for t in r["tiles"])
        need = Counter(c["char"] for c in r["components"])
        for ch, cnt in need.items():
            assert tiles[ch] >= cnt, f"{r['char']}: плиток {ch} меньше, чем нужно"


def test_forge_respects_i_plus_one():
    """Не выученный кандзи не попадает в «Кузницу», даже если разложим."""
    decomp = sorted(_decomposable_chars())
    learned = set(decomp[:1])                       # выучен только один
    rounds = kanji_forge_rounds(learned, limit=99)
    assert {r["char"] for r in rounds} <= learned
