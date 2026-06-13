# -*- coding: utf-8 -*-
"""Генераторы упражнений каны (SRS.md, раздел 5.1) и сценариев уроков.

Типы MVP: kana_recognition (1), kana_reverse (2), kana_tracing (3),
kana_word_build (4), kana_dakuten (5), kana_twins (7). Ответ включён в
payload — проверка на клиенте, результат с длительностью уходит в
авто-оценку SRS (4.2). Черты для прописей — KanjiVG (раздел 6.7).
"""
import json
import random
from pathlib import Path

from .content.registry import (
    KANA, KANA_BY_CHAR, LESSON_BY_ID, VOCAB, VOCAB_BY_ID, WORDS,
    kana_known_by, tokenize_kana, traps_for_lesson,
)

# Не годятся в дистракторы сборки слова: служебные знаки
NON_TILE = {"っ", "ッ", "ー"}

_STROKES_PATH = Path(__file__).resolve().parent / "content" / "kanjivg_kana.json"
STROKES = json.loads(_STROKES_PATH.read_text(encoding="utf-8")) if _STROKES_PATH.exists() else {}

# Триады/пары глухой–звонкий–полузвонкий для kana_dakuten
_DAKUTEN_SETS = {}
for k in KANA:
    base = k.get("base")
    if base and k["kind"] in ("dakuten", "handakuten"):
        _DAKUTEN_SETS.setdefault(base, [base]).append(k["char"])


_tokenize = tokenize_kana


def _romaji_distractors(char, n=3):
    info = KANA_BY_CHAR[char]
    pool = [KANA_BY_CHAR[c]["romaji"] for c in info.get("lookalikes", []) if c in KANA_BY_CHAR]
    same_kind = [k["romaji"] for k in KANA
                 if k["kind"] == info["kind"] and k["script"] == info["script"]
                 and k["char"] != char]
    random.shuffle(same_kind)
    out = []
    for r in pool + same_kind:
        if r != info["romaji"] and r not in out:
            out.append(r)
        if len(out) == n:
            break
    return out


def _kana_distractors(char, n=3):
    info = KANA_BY_CHAR[char]
    pool = [c for c in info.get("lookalikes", []) if c in KANA_BY_CHAR]
    same_kind = [k["char"] for k in KANA
                 if k["kind"] == info["kind"] and k["script"] == info["script"]
                 and k["char"] != char]
    random.shuffle(same_kind)
    out = []
    for c in pool + same_kind:
        if c != char and c not in out:
            out.append(c)
        if len(out) == n:
            break
    return out


def _with_options(correct, distractors):
    options = [correct] + distractors
    random.shuffle(options)
    return options, options.index(correct)


def kana_recognition(char):
    """Тип 1: знак -> выбор чтения из 4."""
    info = KANA_BY_CHAR[char]
    options, answer = _with_options(info["romaji"], _romaji_distractors(char))
    return {"type": "kana_recognition", "item_id": char,
            "prompt": {"text": char, "tts": char, "style": "jp"},
            "question": "Как читается этот знак?",
            "options": options, "answer": answer}


def kana_reverse(char):
    """Тип 2: звук/ромадзи -> выбор знака среди похожих."""
    info = KANA_BY_CHAR[char]
    options, answer = _with_options(char, _kana_distractors(char))
    return {"type": "kana_reverse", "item_id": char,
            "prompt": {"text": info["romaji"], "tts": char},
            "question": "Какой знак так читается?",
            "options": options, "answer": answer, "options_are_kana": True}


def kana_dakuten(char):
    """Тип 5: различение глухой/звонкий/полузвонкий (は/ば/ぱ)."""
    info = KANA_BY_CHAR[char]
    base = info.get("base", char)
    variants = _DAKUTEN_SETS.get(base)
    if not variants or char not in variants:
        return kana_reverse(char)
    options = list(variants)
    random.shuffle(options)
    return {"type": "kana_dakuten", "item_id": char,
            "prompt": {"text": info["romaji"], "tts": char},
            "question": "Выберите знак для этого звука",
            "options": options, "answer": options.index(char), "options_are_kana": True}


def _make_tiles(tokens, lesson_id=None):
    """Плитки для сборки слова: токены + 3 дистрактора той же письменности."""
    script = next((KANA_BY_CHAR[t[0]]["script"] for t in tokens if t[0] in KANA_BY_CHAR), "h")
    known = list(kana_known_by(lesson_id)) if lesson_id else [k["char"] for k in KANA]
    known = [c for c in known if KANA_BY_CHAR.get(c, {}).get("script") == script]
    distractor_pool = []
    for t in tokens:
        head = t[0]
        if head in KANA_BY_CHAR:
            distractor_pool.extend(KANA_BY_CHAR[head].get("lookalikes", []))
    distractor_pool.extend(known)
    random.shuffle(distractor_pool)
    distractors = []
    for c in distractor_pool:
        if c not in tokens and c not in distractors and c not in NON_TILE:
            distractors.append(c)
        if len(distractors) == 3:
            break
    tiles = tokens + distractors
    random.shuffle(tiles)
    return tiles


def kana_word_build(word, lesson_id=None):
    """Тип 4: аудио/перевод слова -> сборка из плиток."""
    tokens = _tokenize(word["kana"])
    return {"type": "kana_word_build", "item_id": word["kana"],
            "prompt": {"text": f"{word['romaji']} — {word['ru']}", "tts": word["kana"]},
            "question": "Соберите слово из плиток",
            "tiles": _make_tiles(tokens, lesson_id), "answer_tokens": tokens}


def kana_tracing(char, mode="trace"):
    """Тип 3: написание каны. mode: trace (по контуру) | memory (по памяти).

    Проверка на клиенте по пайплайну 6.7: число черт -> порядок ->
    направление -> форма (расстояние по точкам траектории).
    """
    strokes = STROKES.get(char)
    if not strokes:
        return None
    info = KANA_BY_CHAR[char]
    return {"type": "kana_tracing", "item_id": char, "mode": mode,
            "prompt": {"text": info["romaji"], "tts": char},
            "question": "Обведите знак по контуру"
            if mode == "trace" else "Напишите знак по памяти",
            "char": char, "strokes": strokes}


def kana_twins(group, rounds=8):
    """Тип 7: серия бинарных выборов по группе-ловушке."""
    series = []
    prev = None
    for _ in range(rounds):
        char = random.choice([c for c in group if c != prev] or group)
        prev = char
        options = list(group)
        random.shuffle(options)
        series.append({"prompt": KANA_BY_CHAR[char]["romaji"], "tts": char,
                       "options": options, "answer": options.index(char)})
    return {"type": "kana_twins", "item_id": "".join(group),
            "question": "Ловушки: выбирайте знак как можно быстрее",
            "series": series, "options_are_kana": True}


# ---------- Лексика (раздел 5.2) ----------

def _word_options(word, key, n=3):
    pool = [w[key] for w in VOCAB if w["id"] != word["id"]]
    random.shuffle(pool)
    return pool[:n]


def vocab_choice(word):
    """Тип 8: слово -> выбор перевода из 4."""
    options, answer = _with_options(word["ru"], _word_options(word, "ru"))
    return {"type": "vocab_choice", "item_id": word["id"],
            "prompt": {"text": word["kana"], "tts": word["kana"], "style": "jp"},
            "question": "Что означает это слово?",
            "options": options, "answer": answer}


def vocab_audio(word):
    """Тип 12: аудио -> выбор перевода (текст слова скрыт).
    fallback — ромадзи на случай недоступной озвучки (офлайн)."""
    options, answer = _with_options(word["ru"], _word_options(word, "ru"))
    return {"type": "vocab_audio", "item_id": word["id"],
            "prompt": {"text": "", "tts": word["kana"], "style": "audio",
                       "fallback": word["romaji"]},
            "question": "Послушайте и выберите перевод",
            "options": options, "answer": answer}


def vocab_reverse_choice(word):
    """Тип 9: перевод -> выбор японского слова из 4."""
    options, answer = _with_options(word["kana"], _word_options(word, "kana"))
    return {"type": "vocab_reverse_choice", "item_id": word["id"],
            "prompt": {"text": word["ru"], "tts": None},
            "question": "Как это по-японски?",
            "options": options, "answer": answer, "options_are_kana": True,
            "answer_tts": word["kana"]}


def vocab_build(word):
    """Воспроизведение: перевод -> сборка слова из плиток каны (без ромадзи)."""
    tokens = _tokenize(word["kana"])
    return {"type": "vocab_build", "item_id": word["id"],
            "prompt": {"text": word["ru"], "tts": word["kana"]},
            "question": "Соберите слово по-японски",
            "tiles": _make_tiles(tokens), "answer_tokens": tokens,
            "speak_after": True}


def item_info(item_type, item_id):
    """Карточка-справка для фидбека в SRS-сессии и статистики."""
    if item_type == "kana":
        k = KANA_BY_CHAR.get(item_id)
        if k:
            return {"title": item_id, "sub": k["romaji"], "hint": k.get("mnemonic")}
    else:
        w = VOCAB_BY_ID.get(item_id)
        if w:
            return {"title": w["kana"], "sub": w["ru"],
                    "hint": f"{w['kana']} ({w['romaji']}) — {w['ru']}"}
    return {"title": item_id, "sub": "", "hint": None}


def review_exercise(item_type, item_id, reps=0):
    """Выбор типа для SRS-повторения: ротация по матрице (раздел 5, антиповторяемость)."""
    if item_type == "kana":
        info = KANA_BY_CHAR.get(item_id)
        if info is None:
            return None
        types = [kana_recognition, kana_reverse]
        if info["kind"] in ("dakuten", "handakuten"):
            types.append(kana_dakuten)
        if item_id in STROKES:
            types.append(lambda c: kana_tracing(c, mode="memory"))
        return types[reps % len(types)](item_id)

    word = VOCAB_BY_ID.get(item_id)
    if word is None:
        return None
    if item_type == "vocab_jp_ru":      # распознавание
        types = [vocab_choice, vocab_audio]
    elif item_type == "vocab_ru_jp":    # воспроизведение
        types = [vocab_reverse_choice, vocab_build]
    else:
        return None
    return types[reps % len(types)](word)


def _intro_step(char):
    info = KANA_BY_CHAR[char]
    step = {"type": "intro_kana", "char": char, "romaji": info["romaji"],
            "kind": info["kind"], "tts": char,
            "mnemonic": info.get("mnemonic"), "note": info.get("note")}
    if char in STROKES:  # 2.1: анимация порядка черт при знакомстве
        step["strokes"] = STROKES[char]
    base = info.get("base")
    if base and info["kind"] == "dakuten":
        step["derivation"] = f"{base} ({KANA_BY_CHAR[base]['romaji']}) + ゛ = {char} ({info['romaji']})"
    elif base and info["kind"] == "handakuten":
        step["derivation"] = f"{base} ({KANA_BY_CHAR[base]['romaji']}) + ゜ = {char} ({info['romaji']})"
    elif base and info["kind"] == "yoon":
        small = char[1] if len(char) > 1 else ""
        step["derivation"] = f"{base} + маленькая {small} = {char} ({info['romaji']})"
    lookalikes = [c for c in info.get("lookalikes", []) if c in KANA_BY_CHAR]
    if lookalikes:
        step["lookalikes"] = [{"char": c, "romaji": KANA_BY_CHAR[c]["romaji"]} for c in lookalikes]
    return step


def _vocab_lesson_steps(lesson):
    """Урок лексики (2.5): знакомство со словом -> распознавание ->
    аудио/обратный выбор -> сборка (воспроизведение)."""
    steps = [{"type": "intro_text", "title": lesson["title"],
              "subtitle": lesson.get("subtitle", ""), "text": lesson["intro"],
              "icon": lesson.get("icon", "")}]
    words = [VOCAB_BY_ID[wid] for wid in lesson["words"]]

    chunk_size = 3
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        for w in chunk:
            steps.append({"type": "intro_word", "kana": w["kana"],
                          "romaji": w["romaji"], "ru": w["ru"],
                          "tts": w["kana"], "note": w.get("note")})
        quiz = [vocab_choice(w) for w in chunk]
        random.shuffle(quiz)
        steps.extend({"type": "exercise", "exercise": e} for e in quiz)

    # Смешанная проверка: на слух и в обратную сторону
    mixed = [vocab_audio(w) if i % 2 else vocab_reverse_choice(w)
             for i, w in enumerate(words)]
    random.shuffle(mixed)
    steps.extend({"type": "exercise", "exercise": e} for e in mixed)

    # Воспроизведение: собрать слово по переводу
    for w in random.sample(words, min(4, len(words))):
        steps.append({"type": "exercise", "exercise": vocab_build(w)})

    return steps


def make_lesson_steps(lesson_id):
    """Сценарий микроурока (2.1): знакомство -> распознавание -> воспроизведение
    -> слова -> ловушки. Чанки по 2–3 знака с мини-проверкой после каждого."""
    lesson = LESSON_BY_ID[lesson_id]
    if lesson.get("type") == "vocab":
        return _vocab_lesson_steps(lesson)
    kana_all = lesson["kana"]
    steps = [{"type": "intro_text", "title": lesson["title"],
              "subtitle": lesson.get("subtitle", ""), "text": lesson["intro"],
              "icon": lesson.get("icon") or (kana_all[0] if kana_all else "っ")}]

    kana_list = lesson["kana"]
    # Прописи — только для одиночных глифов; у дакутэн форма уже знакома
    traceable = [c for c in kana_list
                 if c in STROKES and KANA_BY_CHAR[c]["kind"] == "basic"]

    chunk_size = 3 if len(kana_list) <= 6 else 5
    for i in range(0, len(kana_list), chunk_size):
        chunk = kana_list[i:i + chunk_size]
        for c in chunk:
            steps.append(_intro_step(c))
            if c in traceable:  # 2.1: трассировка сразу после знакомства
                steps.append({"type": "exercise",
                              "exercise": kana_tracing(c, mode="trace")})
        quiz = [kana_recognition(c) for c in chunk]
        random.shuffle(quiz)
        steps.extend({"type": "exercise", "exercise": e} for e in quiz)

    # Смешанная проверка: воспроизведение (звук -> знак)
    mixed = []
    for c in kana_list:
        info = KANA_BY_CHAR[c]
        if info["kind"] in ("dakuten", "handakuten"):
            mixed.append(kana_dakuten(c))
        else:
            mixed.append(kana_reverse(c))
    random.shuffle(mixed)
    steps.extend({"type": "exercise", "exercise": e} for e in mixed)

    # 2.1: написание по памяти — закрепление моторики
    for c in random.sample(traceable, min(3, len(traceable))):
        steps.append({"type": "exercise", "exercise": kana_tracing(c, mode="memory")})

    # Слова из изученной каны
    words = list(WORDS.get(lesson_id, []))
    random.shuffle(words)
    for w in words[:4]:
        steps.append({"type": "exercise", "exercise": kana_word_build(w, lesson_id)})

    # Парные ловушки
    for group in traps_for_lesson(lesson_id)[:2]:
        steps.append({"type": "exercise", "exercise": kana_twins(group)})

    # Спец-урок-дрилл («катакана-ад», 2.2): серии по группам + общий микс
    drills = lesson.get("drills", [])
    if drills:
        for group in drills:
            steps.append({"type": "exercise", "exercise": kana_twins(group, rounds=10)})
        mix = [kana_reverse(c) for g in drills for c in g]
        random.shuffle(mix)
        steps.extend({"type": "exercise", "exercise": e} for e in mix)

    return steps
