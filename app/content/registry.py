# -*- coding: utf-8 -*-
"""Реестр курсов: кана (хирагана + катакана) и лексика N5 в одном
учебном порядке. Единая точка импорта для движка упражнений и API."""

from . import hiragana, katakana, kanji, vocab_n5

for _k in hiragana.KANA:
    _k.setdefault("script", "h")
for _k in katakana.KANA:
    _k.setdefault("script", "k")

KANA = hiragana.KANA + katakana.KANA
KANA_BY_CHAR = {k["char"]: k for k in KANA}

for _l in hiragana.LESSONS + katakana.LESSONS:
    _l.setdefault("type", "kana")
for _l in vocab_n5.LESSONS:
    _l.setdefault("type", "vocab")
for _l in kanji.LESSONS:
    _l.setdefault("type", "kanji")

LESSONS = hiragana.LESSONS + katakana.LESSONS + vocab_n5.LESSONS + kanji.LESSONS
LESSON_BY_ID = {l["id"]: l for l in LESSONS}
LESSON_ORDER = [l["id"] for l in LESSONS]

WORDS = {**hiragana.WORDS, **katakana.WORDS}
TRAP_GROUPS = hiragana.TRAP_GROUPS + katakana.TRAP_GROUPS

VOCAB = vocab_n5.WORDS
VOCAB_BY_ID = vocab_n5.WORD_BY_ID
VOCAB_UNITS = vocab_n5.UNITS

KANJI = kanji.KANJI
KANJI_BY_CHAR = kanji.KANJI_BY_CHAR
KANJI_UNITS = kanji.UNITS

SMALL_YOON = {"ゃ", "ゅ", "ょ", "ャ", "ュ", "ョ"}


def tokenize_kana(word):
    """きょう -> [きょ, う]; きって -> [き, っ, て]."""
    tokens = []
    for ch in word:
        if ch in SMALL_YOON and tokens:
            tokens[-1] += ch
        else:
            tokens.append(ch)
    return tokens


# Какой урок вводит каждый знак (для prereq-проверок)
_LESSON_OF_CHAR = {}
for _l in LESSONS:
    for _c in _l.get("kana", []):
        _LESSON_OF_CHAR.setdefault(_c, _l["id"])

# Словарный урок открывается, когда изучена вся кана его слов (принцип i+1):
# requires — уроки каны, вводящие нужные знаки
for _l in vocab_n5.LESSONS:
    _req = set()
    for _wid in _l["words"]:
        for _t in tokenize_kana(vocab_n5.WORD_BY_ID[_wid]["kana"]):
            _lid = _LESSON_OF_CHAR.get(_t)
            if _lid:
                _req.add(_lid)
    _l["requires"] = sorted(_req)

# Кандзи вводится после каны (2.3): первый урок кандзи открывается, когда
# пройдена вся хирагана (её чтения записаны хираганой).
if kanji.LESSONS and hiragana.LESSONS:
    kanji.LESSONS[0].setdefault("requires", [hiragana.LESSONS[-1]["id"]])

COURSES = [
    {"id": "hiragana", "title": "Хирагана", "lesson_ids": [l["id"] for l in hiragana.LESSONS]},
    {"id": "katakana", "title": "Катакана", "lesson_ids": [l["id"] for l in katakana.LESSONS]},
    {"id": "n5", "title": "Слова N5", "lesson_ids": [l["id"] for l in vocab_n5.LESSONS]},
    {"id": "kanji", "title": "Кандзи", "lesson_ids": [l["id"] for l in kanji.LESSONS]},
]


def srs_items_for_lesson(lesson):
    """Какие SRS-карточки создаёт завершение урока: [(item_type, item_id), ...].
    Слово даёт две карточки (2.5), кандзи — три навыка-карточки (6.4)."""
    if lesson.get("type") == "vocab":
        return ([("vocab_jp_ru", wid) for wid in lesson["words"]] +
                [("vocab_ru_jp", wid) for wid in lesson["words"]])
    if lesson.get("type") == "kanji":
        return ([("kanji_meaning", c) for c in lesson["kanji"]] +
                [("kanji_reading", c) for c in lesson["kanji"]] +
                [("kanji_writing", c) for c in lesson["kanji"]])
    return [("kana", c) for c in lesson["kana"]]


def kana_known_by(lesson_id):
    """Все знаки, введённые к концу данного урока (сквозь оба курса)."""
    known = []
    for l in LESSONS:
        known.extend(l["kana"])
        if l["id"] == lesson_id:
            break
    return set(known)


def traps_for_lesson(lesson_id):
    """Группы-ловушки, в которых участвует кана этого урока (все знаки знакомы)."""
    lesson = LESSON_BY_ID[lesson_id]
    known = kana_known_by(lesson_id)
    new_kana = set(lesson["kana"])
    return [g for g in TRAP_GROUPS if set(g) <= known and set(g) & new_kana]
