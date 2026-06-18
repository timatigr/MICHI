# -*- coding: utf-8 -*-
"""Курс грамматики: точки-конструкции, генераторы упражнений, сценарий урока."""
from app.content.grammar import PARTICLE_POOL
from app.content.registry import (
    COURSES, GRAMMAR, GRAMMAR_BY_ID, LESSON_BY_ID, srs_items_for_lesson,
)
from app.exercises import (
    grammar_choice, item_info, make_lesson_steps, particle_choice,
    review_exercise, sentence_scramble,
)


def test_grammar_course_registered():
    ids = [c["id"] for c in COURSES]
    assert "grammar" in ids
    course = next(c for c in COURSES if c["id"] == "grammar")
    assert course["lesson_ids"]


def test_each_point_has_required_fields():
    for p in GRAMMAR:
        assert p["id"] and p["title"] and p["structure"] and p["meaning"]
        assert p["skill"] in ("particle", "construction")
        assert p["examples"], f"{p['id']} без примеров"
        for e in p["examples"]:
            assert e["tokens"], f"{p['id']}: пустые tokens"
            assert 0 <= e["key"] < len(e["tokens"]), f"{p['id']}: key вне tokens"
            assert e.get("ru"), f"{p['id']}: пример без перевода"


def test_construction_points_have_distractors():
    """grammar_choice неоткуда взять дистракторы, кроме как из примера."""
    for p in GRAMMAR:
        if p["skill"] == "construction":
            for e in p["examples"]:
                wrong = [d for d in e.get("distractors", []) if d != e["tokens"][e["key"]]]
                assert len(wrong) >= 3, f"{p['id']}: мало дистракторов для grammar_choice"


def test_grammar_lesson_makes_one_card_per_point():
    lesson = LESSON_BY_ID["g01"]
    items = srs_items_for_lesson(lesson)
    assert {t for t, _ in items} == {"grammar"}
    assert [i for _, i in items] == lesson["points"]


def test_grammar_lesson_steps_have_intro_and_exercises():
    steps = make_lesson_steps("g01")
    types = {s["type"] for s in steps}
    assert "intro_grammar" in types
    ex_types = {s["exercise"]["type"] for s in steps if s["type"] == "exercise"}
    # есть и узнавание (cloze), и продукция (сборка)
    assert ex_types & {"particle_choice", "grammar_choice"}
    assert "sentence_scramble" in ex_types


def test_particle_choice_answer_and_distractors():
    p = GRAMMAR_BY_ID["wa"]
    ex = particle_choice(p, p["examples"][0])
    assert ex["type"] == "particle_choice"
    assert ex["options"][ex["answer"]] == "は"
    assert len(set(ex["options"])) == len(ex["options"])      # без повторов
    assert all(o in PARTICLE_POOL for o in ex["options"])     # только частицы
    assert "＿＿" in ex["prompt"]["text"]                       # пропуск показан
    assert ex["prompt"]["tts"] is None and ex["answer_tts"]   # чтение — после ответа


def test_grammar_choice_answer_is_correct_form():
    p = GRAMMAR_BY_ID["desu"]
    e = p["examples"][0]
    ex = grammar_choice(p, e)
    assert ex["type"] == "grammar_choice"
    assert ex["options"][ex["answer"]] == e["tokens"][e["key"]]
    assert len(set(ex["options"])) == len(ex["options"])


def test_sentence_scramble_rebuilds_sentence():
    p = GRAMMAR_BY_ID["wa"]
    e = p["examples"][0]
    ex = sentence_scramble(p, e)
    assert ex["type"] == "sentence_scramble"
    assert ex["answer_tokens"] == e["tokens"]
    assert sorted(ex["tiles"]) == sorted(e["tokens"])  # те же плитки, иной порядок


def test_review_exercise_grammar_rotates():
    pid = GRAMMAR[0]["id"]
    cloze = review_exercise("grammar", pid, reps=0)
    build = review_exercise("grammar", pid, reps=1)
    assert cloze["type"] in ("particle_choice", "grammar_choice")
    assert build["type"] == "sentence_scramble"
    assert review_exercise("grammar", "НЕТ") is None


def test_item_info_grammar():
    info = item_info("grammar", "wa")
    assert info["title"] == "は"
    assert "тем" in info["sub"].lower()  # «выделяет тему…»


def test_grammar_requires_point_to_learned_vocab():
    """i+1: грамматический урок открывается только после нужной лексики."""
    for lid in ("g01", "g02", "g03", "g04", "g05"):
        assert LESSON_BY_ID[lid]["requires"], f"{lid} без requires"


# ===================== Юнит 3 — новые точки =====================

UNIT3_LESSONS = ("g04", "g05")
UNIT3_POINTS = (
    "i_adj", "i_adj_past", "na_adj", "masu", "mashita", "masen", "e_dir", "to_with",
)


def test_point_ids_unique():
    ids = [p["id"] for p in GRAMMAR]
    assert len(ids) == len(set(ids)), "дубли id грамматических точек"


def test_unit3_points_exist_and_well_formed():
    for pid in UNIT3_POINTS:
        p = GRAMMAR_BY_ID[pid]
        assert p["skill"] in ("particle", "construction")
        assert p["title"] and p["structure"] and p["meaning"]
        assert p["register"] in ("neutral", "polite", "casual")
        assert p["explanation"] and p["caution"]
        assert p["examples"], f"{pid} без примеров"
        for e in p["examples"]:
            assert 0 <= e["key"] < len(e["tokens"]), f"{pid}: key вне tokens"
            assert e["tokens"][e["key"]], f"{pid}: пустой проверяемый токен"
            assert e.get("ru"), f"{pid}: пример без перевода"


def test_unit3_construction_distractors_distinct_from_answer():
    """construction-точки: дистракторы — реальные неверные формы, не равные ответу."""
    for pid in UNIT3_POINTS:
        p = GRAMMAR_BY_ID[pid]
        if p["skill"] != "construction":
            continue
        for e in p["examples"]:
            answer = e["tokens"][e["key"]]
            wrong = [d for d in e.get("distractors", []) if d != answer]
            assert len(wrong) >= 3, f"{pid}: мало дистракторов"
            assert len(set(wrong)) == len(wrong), f"{pid}: дубли дистракторов"


def test_unit3_particle_answers_in_pool():
    """particle-точки: проверяемый токен — частица из пула (для particle_choice)."""
    for pid in UNIT3_POINTS:
        p = GRAMMAR_BY_ID[pid]
        if p["skill"] != "particle":
            continue
        for e in p["examples"]:
            assert e["tokens"][e["key"]] in PARTICLE_POOL, f"{pid}: ключ не частица из пула"


def test_unit3_lessons_registered_in_unit3():
    for lid in UNIT3_LESSONS:
        lesson = LESSON_BY_ID[lid]
        assert lesson["unit"] == 3, f"{lid} не в юните 3"
        assert lesson["points"], f"{lid} без точек"
        for pid in lesson["points"]:
            assert pid in GRAMMAR_BY_ID, f"{lid}: неизвестная точка {pid}"


def test_unit3_lessons_cover_all_new_points():
    covered = [pid for lid in UNIT3_LESSONS for pid in LESSON_BY_ID[lid]["points"]]
    assert set(covered) == set(UNIT3_POINTS)


def test_unit3_lesson_makes_one_card_per_point():
    for lid in UNIT3_LESSONS:
        lesson = LESSON_BY_ID[lid]
        items = srs_items_for_lesson(lesson)
        assert {t for t, _ in items} == {"grammar"}
        assert [i for _, i in items] == lesson["points"]


# ===================== Юниты 4–9 — новые точки =====================

from app.content import vocab_n5  # noqa: E402

NEW_LESSONS = ("g06", "g07", "g08", "g09", "g10", "g11", "g12", "g13", "g14", "g15")
NEW_POINTS = (
    # Юнит 4 — указатели
    "kore_sore_are", "kono_sono_ano", "koko_soko_asoko",
    # Юнит 5 — существование
    "ga_subject", "aru", "iru",
    # Юнит 6 — желания/предложения
    "tai", "mashou", "masenka",
    # Юнит 7 — причина/сравнение
    "kara_reason", "yori", "nohou_ga", "ichiban", "suki_ga",
    # Юнит 8 — て-форма
    "te_kudasai", "te_iru", "te_mo_ii", "te_wa_ikenai",
    # Юнит 9 — простая форма и связки
    "nai_form", "ta_form", "deshou", "ne", "yo", "ya",
    # Юнит 10 — отрицание и прошлое
    "dewa_nai", "deshita", "i_adj_neg",
    # Юнит 11 — соединяем мысли
    "kara_made", "ga_but", "toki",
    # Юнит 12 — просьбы и наречия
    "naide_kudasai", "adverb_form",
)


def test_new_points_exist_and_well_formed():
    for pid in NEW_POINTS:
        p = GRAMMAR_BY_ID[pid]
        assert p["skill"] in ("particle", "construction")
        assert p["title"] and p["structure"] and p["meaning"]
        assert p["register"] in ("neutral", "polite", "casual")
        assert p["explanation"] and p["caution"]
        assert p["examples"], f"{pid} без примеров"
        for e in p["examples"]:
            assert 0 <= e["key"] < len(e["tokens"]), f"{pid}: key вне tokens"
            assert e["tokens"][e["key"]], f"{pid}: пустой проверяемый токен"
            assert e.get("ru"), f"{pid}: пример без перевода"


def test_new_construction_distractors_distinct_from_answer():
    for pid in NEW_POINTS:
        p = GRAMMAR_BY_ID[pid]
        if p["skill"] != "construction":
            continue
        for e in p["examples"]:
            answer = e["tokens"][e["key"]]
            wrong = [d for d in e.get("distractors", []) if d != answer]
            assert len(wrong) >= 3, f"{pid}: мало дистракторов"
            assert len(set(wrong)) == len(wrong), f"{pid}: дубли дистракторов"


def test_new_particle_answers_in_pool():
    for pid in NEW_POINTS:
        p = GRAMMAR_BY_ID[pid]
        if p["skill"] != "particle":
            continue
        for e in p["examples"]:
            assert e["tokens"][e["key"]] in PARTICLE_POOL, f"{pid}: ключ не частица из пула"


def test_new_lessons_registered_and_cover_points():
    covered = []
    for lid in NEW_LESSONS:
        lesson = LESSON_BY_ID[lid]
        assert lesson["points"], f"{lid} без точек"
        assert lesson["requires"], f"{lid} без requires"
        for pid in lesson["points"]:
            assert pid in GRAMMAR_BY_ID, f"{lid}: неизвестная точка {pid}"
            covered.append(pid)
    assert set(covered) == set(NEW_POINTS)


def test_new_lessons_unit_matches_points_unit():
    """Каждый урок привязан к своему юниту, юнит зарегистрирован в UNITS."""
    from app.content.grammar import UNITS
    for lid in NEW_LESSONS:
        lesson = LESSON_BY_ID[lid]
        assert lesson["unit"] in UNITS, f"{lid}: юнит {lesson['unit']} нет в UNITS"


def test_new_lessons_one_card_per_point():
    for lid in NEW_LESSONS:
        lesson = LESSON_BY_ID[lid]
        items = srs_items_for_lesson(lesson)
        assert {t for t, _ in items} == {"grammar"}
        assert [i for _, i in items] == lesson["points"]


# --- i+1: примеры строятся только из уже изученной лексики ---

# Грамматические токены, не являющиеся словарной единицей: частицы,
# связки, окончания и формы глаголов/прилагательных, вводимые самими точками.
_GRAMMAR_TOKENS = set(PARTICLE_POOL) | {
    "です", "でした", "だ", "でしょう",
    # указатели こ・そ・あ・ど
    "これ", "それ", "あれ", "この", "その", "あの",
    "ここ", "そこ", "あそこ", "のほうが", "いちばん",
    # глаголы существования
    "あります", "ありません", "います", "いません",
}


def _vocab_kana_upto(req_lesson_id):
    """Множество слов (kana), освоенных к моменту открытия урока с данным
    requires (включительно по порядку словарных уроков v01…)."""
    order = [l["id"] for l in vocab_n5.LESSONS]
    if req_lesson_id not in order:
        return None
    cutoff = order.index(req_lesson_id)
    learned = set()
    for l in vocab_n5.LESSONS[: cutoff + 1]:
        for wid in l["words"]:
            learned.add(vocab_n5.WORD_BY_ID[wid]["kana"])
    return learned


def _is_inflection_of_known(token, known_kana):
    """Токен — словоформа известного глагола/прилагательного (ます-форма,
    て-форма, ～たい, ～ない, ～た, прошедшее ～かった и т. п.)?"""
    # отрезаем хвосты-распространённые окончания и ищем общий корень
    stems = set()
    for k in known_kana:
        if len(k) >= 2:
            stems.add(k[:-1])  # корень без последней моры (る/む/く/い…)
            stems.add(k[:-2]) if len(k) >= 3 else None
    return any(token.startswith(s) and s for s in stems if len(s) >= 1)


def test_new_examples_use_only_learned_vocab():
    """Каждый не-грамматический токен примера должен быть уже изученным словом
    (или его словоформой) к моменту открытия урока (i+1)."""
    point_to_lesson = {}
    for lid in NEW_LESSONS:
        for pid in LESSON_BY_ID[lid]["points"]:
            point_to_lesson[pid] = lid
    for pid in NEW_POINTS:
        lesson = LESSON_BY_ID[point_to_lesson[pid]]
        known = set()
        for req in lesson["requires"]:
            up = _vocab_kana_upto(req)
            if up:
                known |= up
        p = GRAMMAR_BY_ID[pid]
        for e in p["examples"]:
            for i, tok in enumerate(e["tokens"]):
                if i == e["key"]:
                    continue  # проверяемая форма — грамматика точки
                if tok in _GRAMMAR_TOKENS or tok in known:
                    continue
                assert _is_inflection_of_known(tok, known), (
                    f"{pid}: токен «{tok}» не из изученной лексики "
                    f"(урок {lesson['id']}, requires {lesson['requires']})"
                )
