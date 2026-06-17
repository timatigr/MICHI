# -*- coding: utf-8 -*-
"""Генераторы упражнений и сценарии уроков."""
from app.content.registry import (
    COURSES, GRAMMAR, KANA, KANJI_BY_CHAR, LESSON_BY_ID, VOCAB,
)
from app.exercises import (
    dictation, grammar_cloze, make_lesson_steps, review_exercise, vocab_choice,
    vocab_input, vocab_match, vocab_reverse_choice, word_kanji,
)


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


def test_input_exercises_accept_kana_and_romaji():
    """vocab_input / dictation принимают и кану, и ромадзи (без IME)."""
    w = VOCAB[0]
    for ex in (vocab_input(w), dictation(w)):
        assert ex["answer"] == w["kana"]
        # клиентская нормализация: нижний регистр без пробелов
        norm = w["romaji"].lower().replace(" ", "")
        assert w["kana"] in ex["accept"]
        assert norm in ex["accept"]


def test_choice_options_never_duplicate_the_answer():
    """Варианты выбора уникальны и верный вариант — это перевод/запись слова.
    Ловит коллизию у слов-дублей (いい заведено как существ. и как い-прил.):
    дистрактор не должен совпасть с ответом, иначе две одинаковые кнопки и
    «неверный» правильный вариант. Генерация рандомная — гоняем несколько раз."""
    for w in VOCAB:
        for _ in range(8):
            c = vocab_choice(w)
            assert len(c["options"]) == len(set(c["options"])), f"{w['id']}: {c['options']}"
            assert c["options"][c["answer"]] == w["ru"]
            r = vocab_reverse_choice(w)
            assert len(r["options"]) == len(set(r["options"])), f"{w['id']}: {r['options']}"
            assert r["options"][r["answer"]] == w["kana"]


def test_dictation_has_offline_fallback():
    """Диктант без сети должен деградировать к показу перевода, а не пустоты."""
    ex = dictation(VOCAB[0])
    assert ex["prompt"]["style"] == "audio"
    assert ex["prompt"]["fallback_text"] == VOCAB[0]["ru"]


def test_vocab_match_pairs_are_consistent():
    """Доска сопоставления: уникальные id, у каждой пары jp/ru/tts."""
    ex = vocab_match(VOCAB[:5])
    assert ex["type"] == "vocab_match"
    ids = [p["id"] for p in ex["pairs"]]
    assert len(ids) == len(set(ids)) == 5
    for p in ex["pairs"]:
        assert p["jp"] and p["ru"] and p["tts"]


def test_vocab_lesson_has_match_board():
    """В уроке лексики есть доска сопоставления."""
    steps = make_lesson_steps("v01")
    assert any(s["type"] == "exercise" and s["exercise"]["type"] == "vocab_match"
               for s in steps)


def test_grammar_cloze_bank_covers_all_answers():
    """Мульти-пропуск: каждый верный ответ есть в общем банке, банк без дублей."""
    parts = [p for p in GRAMMAR if p["skill"] == "particle"]
    ex = grammar_cloze(parts)
    assert ex["type"] == "grammar_cloze" and ex["rows"]
    assert len(ex["bank"]) == len(set(ex["bank"]))
    for r in ex["rows"]:
        assert r["answer"] in ex["bank"]
        assert r["tokens"][r["key"]] == r["answer"]


def test_some_grammar_lesson_has_cloze_board():
    grammar_lids = [l for c in COURSES if c["id"] == "grammar" for l in c["lesson_ids"]]
    found = any(
        s["type"] == "exercise" and s["exercise"]["type"] == "grammar_cloze"
        for lid in grammar_lids if lid.startswith("g")
        for s in make_lesson_steps(lid))
    assert found


def test_word_kanji_links_reading_to_spelling():
    """Связь кандзи↔слово: верный вариант — запись слова, среди вариантов уник."""
    ex = word_kanji({"w": "日本", "r": "にほん", "ru": "Япония"})
    assert ex["type"] == "word_kanji"
    assert ex["options"][ex["answer"]] == "日本"
    assert len(ex["options"]) == len(set(ex["options"]))
    assert ex["options_are_kana"]


def test_kanji_lessons_link_words_with_known_kanji():
    """Хотя бы один урок кандзи содержит дрилл «запиши слово кандзи», и каждый
    кандзи в ответе — реальный знак курса (введён к этому моменту, i+1)."""
    kanji_lids = [l for c in COURSES if c["id"] == "kanji" for l in c["lesson_ids"]
                  if l.startswith("j") and "-g" not in l]
    introduced, found = set(), False
    for lid in kanji_lids:
        # знаки этого урока вводятся в нём же — доступны его word_kanji-дриллам
        introduced.update(LESSON_BY_ID[lid].get("kanji", []))
        for s in make_lesson_steps(lid):
            ex = s.get("exercise") if s["type"] == "exercise" else None
            if ex and ex["type"] == "word_kanji":
                found = True
                kanji_chars = [c for c in ex["item_id"] if c in KANJI_BY_CHAR]
                assert len(kanji_chars) >= 2          # реально многосложное слово
                assert all(c in introduced for c in kanji_chars)  # i+1
    assert found
    """В ротацию воспроизведения/распознавания добавлены ввод и диктант."""
    wid = next(w["id"] for w in VOCAB)
    ru_types = {review_exercise("vocab_ru_jp", wid, reps=r)["type"] for r in range(3)}
    jp_types = {review_exercise("vocab_jp_ru", wid, reps=r)["type"] for r in range(3)}
    assert "vocab_input" in ru_types
    assert "dictation" in jp_types
