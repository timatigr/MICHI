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

from .content.counters import COUNTERS
from .content.grammar import PARTICLE_POOL
from .content.minimal_pairs import PAIRS as MINIMAL_PAIRS
from .content.verbs import (
    FORM_LABEL as VERB_FORM_LABEL, VERBS, conjugate as conjugate_verb,
    distractors as verb_distractors,
)
from .content.registry import (
    GRAMMAR_BY_ID, KANA, KANA_BY_CHAR, KANJI, KANJI_BY_CHAR, LESSON_BY_ID, LESSONS,
    VOCAB, VOCAB_BY_ID, WORDS, gate_items, kana_known_by, tokenize_kana,
    traps_for_lesson,
)

# Не годятся в дистракторы сборки слова: служебные знаки
NON_TILE = {"っ", "ッ", "ー"}

_CONTENT = Path(__file__).resolve().parent / "content"


def _load_strokes(name):
    p = _CONTENT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# Черты каны и кандзи в одном словаре: тип знака различает item_type
STROKES = {**_load_strokes("kanjivg_kana.json"), **_load_strokes("kanjivg_kanji.json")}

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
    # Дистракторы, совпадающие с верным ответом по значению, дали бы две
    # одинаковые кнопки (а «неверный» правильный вариант засчитался бы ошибкой).
    # Это случается, когда два разных элемента делят перевод/запись — напр.
    # いい заведено и как существ., и как い-прил. Отсекаем такие и дубли между собой.
    seen = {correct}
    uniq = []
    for d in distractors:
        if d not in seen:
            seen.add(d)
            uniq.append(d)
    options = [correct] + uniq
    random.shuffle(options)
    return options, options.index(correct)


def _mnemonics_for(info):
    """Полный список ассоциаций знака: основная + альтернативы (6.6).

    Обратная совместимость: поле `mnemonic` остаётся первым/каноничным,
    `mnemonics` — необязательные дополнительные варианты «на выбор».
    """
    out = []
    for m in [info.get("mnemonic"), *info.get("mnemonics", [])]:
        if m and m not in out:
            out.append(m)
    return out


def _confusables(option_chars, correct):
    """Ассоциации знаков-дистракторов (только для вариантов-каны): фронт
    показывает «не путай X с Y» при выборе похожего знака."""
    out = {}
    for c in option_chars:
        if c == correct:
            continue
        m = KANA_BY_CHAR.get(c, {}).get("mnemonic")
        if m:
            out[c] = m
    return out


def kana_recognition(char):
    """Тип 1: знак -> выбор чтения из 4."""
    info = KANA_BY_CHAR[char]
    options, answer = _with_options(info["romaji"], _romaji_distractors(char))
    return {"type": "kana_recognition", "item_id": char,
            "prompt": {"text": char, "tts": char, "style": "jp"},
            "question": "Как читается этот знак?",
            "options": options, "answer": answer,
            "mnemonics": _mnemonics_for(info)}


def kana_reverse(char):
    """Тип 2: звук/ромадзи -> выбор знака среди похожих."""
    info = KANA_BY_CHAR[char]
    options, answer = _with_options(char, _kana_distractors(char))
    return {"type": "kana_reverse", "item_id": char,
            "prompt": {"text": info["romaji"], "tts": char},
            "question": "Какой знак так читается?",
            "options": options, "answer": answer, "options_are_kana": True,
            "mnemonics": _mnemonics_for(info),
            "confusables": _confusables(options, char)}


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
            "options": options, "answer": options.index(char), "options_are_kana": True,
            "mnemonics": _mnemonics_for(info),
            "confusables": _confusables(options, char)}


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
    # Исключаем не только само слово, но и любые с тем же значением/записью:
    # иначе у слов-дублей (напр. いい) дистрактор совпал бы с верным ответом.
    target = word[key]
    pool = [w[key] for w in VOCAB if w["id"] != word["id"] and w[key] != target]
    random.shuffle(pool)
    out = []
    for v in pool:
        if v not in out:
            out.append(v)
        if len(out) == n:
            break
    return out


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


def vocab_match(words):
    """Тип 11: сопоставить слова и переводы (до 5 пар на доске). Быстрое
    связывание формы и смысла; используется в уроках как консолидация."""
    pairs = [{"id": w["id"], "jp": w["kana"], "ru": w["ru"], "tts": w["kana"]}
             for w in words]
    return {"type": "vocab_match",
            "item_id": "match:" + "+".join(w["id"] for w in words),
            "question": "Сопоставьте слова и переводы", "pairs": pairs}


def _input_accept(word):
    """Что принимаем при свободном вводе: кана и ромадзи (без японской IME).
    Нормализация совпадает с клиентской (нижний регистр, без пробелов)."""
    return sorted({word["kana"], word["romaji"].lower().replace(" ", "")})


def vocab_input(word):
    """Тип 10: перевод -> свободный ввод слова (каной или ромадзи).
    Активное воспроизведение; озвучка после ответа (speak_after выдала бы его)."""
    return {"type": "vocab_input", "item_id": word["id"],
            "prompt": {"text": word["ru"], "tts": word["kana"]},
            "question": "Введите слово по-японски",
            "answer": word["kana"], "accept": _input_accept(word),
            "answer_tts": word["kana"], "speak_after": True}


def dictation(word):
    """Тип 37: аудио -> запись услышанного (каной или ромадзи). Первое
    упражнение на аудирование (5.5). Без сети — деградирует к показу перевода."""
    return {"type": "dictation", "item_id": word["id"],
            "prompt": {"text": "", "tts": word["kana"], "style": "audio",
                       "fallback_text": word["ru"]},
            "question": "Запишите, что услышали",
            "answer": word["kana"], "accept": _input_accept(word),
            "answer_tts": word["kana"]}


# ---------- Кандзи (раздел 5.3, три навыка-карточки) ----------

def _kanji_meaning_distractors(char, n=3):
    pool = [k["meaning"] for k in KANJI if k["char"] != char]
    random.shuffle(pool)
    return pool[:n]


def _kanji_reading_distractors(char, n=3):
    # Исключаем чтение, равное верному: разные кандзи делят чтения (日/火 = ひ),
    # иначе верный вариант мог бы попасть и в дистракторы
    target = KANJI_BY_CHAR[char]["reading"]
    pool = [k["reading"] for k in KANJI
            if k["char"] != char and k.get("reading") and k["reading"] != target]
    random.shuffle(pool)
    out = []
    for r in pool:
        if r not in out:
            out.append(r)
        if len(out) == n:
            break
    return out


def kanji_meaning(k):
    """Тип 18: кандзи -> выбор значения из 4."""
    options, answer = _with_options(k["meaning"], _kanji_meaning_distractors(k["char"]))
    return {"type": "kanji_meaning", "item_id": k["char"],
            "prompt": {"text": k["char"], "tts": None, "style": "jp"},
            "question": "Что значит этот иероглиф?",
            "options": options, "answer": answer,
            "mnemonics": [m for m in [k.get("mnemonic")] if m]}


def kanji_reading(k):
    """Тип 20: чтение кандзи в слове -> выбор каны из 4.
    Озвучка не играет до ответа (выдала бы чтение) — speak_after на клиенте."""
    word = k["examples"][0]
    options, answer = _with_options(k["reading"], _kanji_reading_distractors(k["char"]))
    return {"type": "kanji_reading", "item_id": k["char"],
            "prompt": {"text": word["w"], "tts": None, "style": "jp"},
            "question": "Как читается это слово?",
            "options": options, "answer": answer, "options_are_kana": True,
            "answer_tts": word["r"],
            "mnemonics": [m for m in [k.get("mnemonic_reading")] if m]}


def _is_kanji(c):
    return c in KANJI_BY_CHAR


def _kanji_count(w):
    return sum(1 for c in w if _is_kanji(c))


# Слова-примеры из кандзи-курса с ≥2 кандзи — пул для дистракторов «запиши кандзи»
_KANJI_WORDS = []
_seen_kw = set()
for _k in KANJI:
    for _ex in _k.get("examples", []):
        if _kanji_count(_ex["w"]) >= 2 and _ex["w"] not in _seen_kw:
            _seen_kw.add(_ex["w"])
            _KANJI_WORDS.append(_ex)


def _kanji_introduced_through(lesson_id):
    """Все кандзи, введённые в курсе к концу данного урока (для i+1-связи)."""
    known = set()
    for l in LESSONS:
        if l.get("type") == "kanji":
            known.update(l.get("kanji", []))
        if l["id"] == lesson_id:
            break
    return known


def word_kanji(example):
    """Связь кандзи↔слово N5 (USP «единый граф знаний», 6.5): по чтению и
    значению выбрать запись слова кандзи. Дистракторы — другие слова курса."""
    answer = example["w"]
    pool = [e["w"] for e in _KANJI_WORDS if e["w"] != answer]
    same_len = [w for w in pool if len(w) == len(answer)]
    random.shuffle(same_len)
    random.shuffle(pool)
    distractors = (same_len + [w for w in pool if w not in same_len])[:3]
    options, idx = _with_options(answer, distractors)
    return {"type": "word_kanji", "item_id": answer,
            "prompt": {"text": example["r"], "tts": None, "style": "jp-sentence"},
            "question": f"«{example['ru']}» — запишите кандзи",
            "question_i18n": {"key": "«{x}» — запишите кандзи", "vars": {"x": example["ru"]}},
            "options": options, "answer": idx,
            "options_are_kana": True, "answer_tts": example["r"]}


def kanji_writing(char, mode="memory"):
    """Тип 21: написание кандзи. Тот же пайплайн проверки черт, что у каны (6.7)."""
    strokes = STROKES.get(char)
    if not strokes:
        return None
    k = KANJI_BY_CHAR[char]
    return {"type": "kanji_tracing", "item_id": char, "mode": mode,
            "prompt": {"text": k["meaning"], "tts": k["reading"]},
            "question": "Обведите иероглиф по контуру"
            if mode == "trace" else "Напишите иероглиф по памяти",
            "char": char, "strokes": strokes}


# ---------- Грамматика (раздел 5.4) ----------

def _sentence_reading(example):
    """Озвучка предложения: явное чтение или склейка токенов (всё каной)."""
    return example.get("reading") or "".join(example["tokens"])


def _cloze_prompt(tokens, key):
    """Предложение с пропуском на месте проверяемого элемента."""
    return "".join("＿＿" if i == key else t for i, t in enumerate(tokens))


def particle_choice(point, example):
    """Тип 27: предложение с пропуском частицы -> выбор из 4."""
    tokens, key = example["tokens"], example["key"]
    correct = tokens[key]
    distractors = [p for p in PARTICLE_POOL if p != correct]
    random.shuffle(distractors)
    options, answer = _with_options(correct, distractors[:3])
    return {"type": "particle_choice", "item_id": point["id"],
            "prompt": {"text": _cloze_prompt(tokens, key), "tts": None, "style": "jp-sentence"},
            "question": "Какая частица подходит?",
            "options": options, "answer": answer, "options_are_kana": True,
            "answer_tts": _sentence_reading(example)}


def grammar_choice(point, example):
    """Тип 30: выбор верной формы/конструкции в пропуске."""
    tokens, key = example["tokens"], example["key"]
    correct = tokens[key]
    distractors = [d for d in example.get("distractors", []) if d != correct]
    options, answer = _with_options(correct, distractors[:3])
    return {"type": "grammar_choice", "item_id": point["id"],
            "prompt": {"text": _cloze_prompt(tokens, key), "tts": None, "style": "jp-sentence"},
            "question": "Выберите верную форму",
            "options": options, "answer": answer, "options_are_kana": True,
            "answer_tts": _sentence_reading(example)}


def sentence_scramble(point, example):
    """Тип 28: собрать предложение из перемешанных слов.

    Принимается один каноничный порядок (для базовых N5-фраз он однозначен)."""
    tokens = example["tokens"]
    tiles = list(tokens)
    for _ in range(8):  # перемешать так, чтобы не совпасть с верным порядком
        random.shuffle(tiles)
        if tiles != tokens or len(tokens) < 2:
            break
    return {"type": "sentence_scramble", "item_id": point["id"],
            "prompt": {"text": example["ru"], "tts": _sentence_reading(example)},
            "question": "Соберите предложение",
            "tiles": tiles, "answer_tokens": tokens, "speak_after": True}


def _grammar_cloze(point, example):
    """Cloze по типу точки: частица -> particle_choice, иначе grammar_choice."""
    if point["skill"] == "particle":
        return particle_choice(point, example)
    return grammar_choice(point, example)


def grammar_cloze(points, max_rows=4):
    """Тип 34: несколько предложений с пропусками частиц и общий банк ответов.
    Частичный зачёт — каждый пропуск проверяется отдельно (на клиенте). Берём
    только точки-частицы, чтобы банк был однородным."""
    parts = [p for p in points if p["skill"] == "particle"]
    random.shuffle(parts)
    rows, answers = [], set()
    for p in parts[:max_rows]:
        e = random.choice(p["examples"])
        ans = e["tokens"][e["key"]]
        rows.append({"id": p["id"], "tokens": e["tokens"], "key": e["key"],
                     "answer": ans, "ru": e["ru"], "tts": _sentence_reading(e)})
        answers.add(ans)
    extras = [x for x in PARTICLE_POOL if x not in answers]
    random.shuffle(extras)
    bank = sorted(answers | set(extras[:2]))
    return {"type": "grammar_cloze",
            "item_id": "gcloze:" + "+".join(r["id"] for r in rows),
            "question": "Заполните пропуски частицами", "rows": rows, "bank": bank}


# Грамматические точки вежливых форм -> какую форму глагола дриллить (тип 29)
VERB_FORM_OF = {"masu": "masu", "mashita": "mashita", "masen": "masen"}


def verb_conjugation(verb, form):
    """Тип 29: поставить глагол из словарной формы в целевую (ます/ました/
    ません/て). Выбор из 4 — дистракторы это типичные ошибки спряжения."""
    answer = conjugate_verb(verb, form)
    options, idx = _with_options(answer, verb_distractors(verb, form, answer))
    return {"type": "verb_conjugation", "item_id": verb["dict"],
            "prompt": {"text": verb["dict"], "tts": None, "style": "jp"},
            "question": f"«{verb['ru']}» → {VERB_FORM_LABEL[form]}",
            "question_i18n": {"key": "«{v}» → {f}",
                              "vars": {"v": verb["ru"], "f": VERB_FORM_LABEL[form]}},
            "options": options, "answer": idx,
            "options_are_kana": True, "answer_tts": answer}


def minimal_pair_rounds(n=8):
    """Раунды дрилла «минимальные пары на слух» (5.5): в каждом проигрывается одно
    слово пары, надо выбрать услышанное из двух почти одинаковых. Позиция вариантов
    перемешана, чтобы не была подсказкой; played-слово выбирается случайно."""
    rounds = []
    n = max(0, min(n, len(MINIMAL_PAIRS)))     # отрицательный limit не должен ронять sample
    for p in random.sample(MINIMAL_PAIRS, n):
        opts = [p["a"], p["b"]]
        random.shuffle(opts)
        target = p[random.choice(["a", "b"])]
        rounds.append({
            "tts": target["kana"],
            "options": [o["kana"] for o in opts],
            "romaji": [o["romaji"] for o in opts],
            "meanings": [o["ru"] for o in opts],
            "answer": opts.index(target),
            "kind": p["kind"],
        })
    return rounds


# ---------- Счётные суффиксы 助数詞: какой счётчик к какому предмету ----------

def counter_rounds(limit=8):
    """Раунды «счётных суффиксов»: дан предмет (эмодзи × N) — выбрать верное
    счётное слово из 4. Чистая практика (как минимальные пары), без БД/SRS."""
    pairs = [(c, n) for c in COUNTERS for n in c["nouns"]]
    random.shuffle(pairs)
    n = max(0, min(limit, len(pairs)))
    rounds = []
    for c, noun in pairs[:n]:
        others = [x for x in COUNTERS if x["counter"] != c["counter"]]
        random.shuffle(others)
        opts = [c] + others[:3]
        random.shuffle(opts)
        rounds.append({
            "noun": {"kana": noun["kana"], "ru": noun["ru"],
                     "emoji": noun["emoji"], "tts": noun["kana"]},
            "count": random.randint(2, 5),
            "options": [{"counter": o["counter"], "reading": o["reading"],
                         "meaning": o["meaning"]} for o in opts],
            "answer": opts.index(c),
        })
    return rounds


# ---------- Сиритори しりとり: словесная цепочка (USP, японская игра) ----------
# Каждое слово начинается с последней каны предыдущего (りんご→ごりら→…). Строим
# реальную цепочку из ИЗУЧЕННЫХ слов (i+1), чистая практика — в SRS не пишет.
# Берём только слова, целиком записанные хираганой: так совпадение «хвост→голова»
# считается посимвольно без путаницы катакана/хирагана и долготы ー.
_SHIRI_SMALL = set("ゃゅょぁぃぅぇぉゎっ")


def _is_hiragana_word(kana):
    return bool(kana) and all("ぁ" <= c <= "ゖ" for c in kana)


def _shiri_tail(kana):
    """Кана, на которую слово «заканчивается» для сиритори (или '' — не годится)."""
    s = (kana or "").rstrip("ー")
    if not s:
        return ""
    c = s[-1]
    return "" if c in _SHIRI_SMALL else c


def _shiri_head(kana):
    return kana[0] if kana else ""


def _shiri_build_chain(start, by_head, limit):
    chain, used = [start], {start["kana"]}
    cur = start
    while len(chain) <= limit:
        need = _shiri_tail(cur["kana"])
        cands = [w for w in by_head.get(need, [])
                 if w["kana"] not in used and _shiri_tail(w["kana"]) and not w["kana"].endswith("ん")]
        if not cands:
            break
        nxt = random.choice(cands)
        chain.append(nxt)
        used.add(nxt["kana"])
        cur = nxt
    return chain


def shiritori_rounds(words, limit=8):
    """Раунды сиритори: реальная цепочка из изученных слов. Каждый раунд — шаг
    цепочки: дано текущее слово, выбрать продолжение (на его последнюю кану) из
    вариантов. Возвращает столько шагов, сколько удалось связать (как мин. пары)."""
    pool = [w for w in words if _is_hiragana_word(w["kana"])]
    by_head = {}
    for w in pool:
        by_head.setdefault(_shiri_head(w["kana"]), []).append(w)
    starts = [w for w in pool if _shiri_tail(w["kana"]) and not w["kana"].endswith("ん")]
    random.shuffle(starts)
    chain = []
    for s in starts:                       # ищем стартовое слово с продолжением
        c = _shiri_build_chain(s, by_head, limit)
        if len(c) > len(chain):
            chain = c
        if len(chain) > limit:
            break
    if len(chain) < 2:
        return []
    rounds = []
    for i in range(len(chain) - 1):
        cur, nxt = chain[i], chain[i + 1]
        need = _shiri_tail(cur["kana"])
        distract = [w for w in pool if _shiri_head(w["kana"]) != need
                    and w["kana"] not in (cur["kana"], nxt["kana"])]
        random.shuffle(distract)
        opts, seen = [nxt], {nxt["kana"]}
        for d in distract:
            if d["kana"] not in seen:
                opts.append(d)
                seen.add(d["kana"])
            if len(opts) == 4:
                break
        if len(opts) < 2:
            continue
        random.shuffle(opts)
        rounds.append({
            "current": {"kana": cur["kana"], "romaji": cur["romaji"],
                        "ru": cur["ru"], "tts": cur["kana"]},
            "need": need,
            "options": [{"kana": w["kana"], "ru": w["ru"], "tts": w["kana"]} for w in opts],
            "answer": opts.index(nxt),
        })
    return rounds[:limit]


def _decomposable_kanji():
    """Кандзи, у которых есть разбор на ≥2 компонента (6.3) — пул для «Кузницы»."""
    return [k for k in KANJI if len(k.get("components") or []) >= 2]


def kanji_forge_rounds(learned_chars, limit=8):
    """Раунды «Кузницы кандзи 鍛冶»: собрать иероглиф из компонентов-радикалов
    (обратная сторона разбора 6.3, USP «граф знаний»). Только изученные разложимые
    кандзи (i+1). Чистая практика — в SRS ничего не пишется. Учитывает повторы
    компонентов (林 = 木 + 木): цель — мультимножество, в плитках столько же копий."""
    pool = [k for k in _decomposable_kanji() if k["char"] in learned_chars]
    if not pool:
        return []
    # карта «компонент → значение-образ» по всем разложимым кандзи (для дистракторов)
    comp_meaning = {}
    for k in _decomposable_kanji():
        for c in k["components"]:
            if c.get("char"):
                comp_meaning.setdefault(c["char"], c.get("meaning", ""))
    n = max(0, min(limit, len(pool)))
    rounds = []
    for k in random.sample(pool, n):
        comps = [{"char": c["char"], "meaning": c.get("meaning", "")}
                 for c in k["components"] if c.get("char")]
        target = {c["char"] for c in comps}
        extra = [ch for ch in comp_meaning if ch not in target]
        random.shuffle(extra)
        tiles = comps + [{"char": ch, "meaning": comp_meaning[ch]} for ch in extra[:3]]
        random.shuffle(tiles)
        rounds.append({
            "char": k["char"], "meaning": k["meaning"],
            "reading": k.get("reading", ""), "tts": k.get("reading") or k["char"],
            "components": comps, "tiles": tiles,
        })
    return rounds


def item_info(item_type, item_id):
    """Карточка-справка для фидбека в SRS-сессии и статистики."""
    if item_type == "kana":
        k = KANA_BY_CHAR.get(item_id)
        if k:
            return {"title": item_id, "sub": k["romaji"], "hint": k.get("mnemonic")}
    elif item_type.startswith("kanji"):
        k = KANJI_BY_CHAR.get(item_id)
        if k:
            hint = f"{k['char']} — {k['meaning']} ({k['reading']}). {k.get('mnemonic', '')}".strip()
            if k.get("mnemonic_reading"):
                hint = f"{hint} {k['mnemonic_reading']}".strip()
            return {"title": k["char"], "sub": k["meaning"], "hint": hint}
    elif item_type == "grammar":
        p = GRAMMAR_BY_ID.get(item_id)
        if p:
            return {"title": p["title"], "sub": p["meaning"],
                    "hint": f"{p['structure']} — {p['meaning']}. {p.get('caution', '')}".strip()}
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

    if item_type.startswith("kanji"):
        k = KANJI_BY_CHAR.get(item_id)
        if k is None:
            return None
        if item_type == "kanji_meaning":
            return kanji_meaning(k)
        if item_type == "kanji_reading":
            return kanji_reading(k)
        if item_type == "kanji_writing":
            return kanji_writing(item_id, mode="memory")
        return None

    if item_type == "grammar":
        p = GRAMMAR_BY_ID.get(item_id)
        if p is None:
            return None
        # Точки вежливых форм глагола подкрепляем дриллом спряжения (тип 29)
        if item_id in VERB_FORM_OF and reps % 3 == 1:
            return verb_conjugation(random.choice(VERBS), VERB_FORM_OF[item_id])
        example = random.choice(p["examples"])
        # ротация: cloze (узнавание) <-> сборка предложения (продукция), 5.4
        return (_grammar_cloze(p, example) if reps % 2 == 0
                else sentence_scramble(p, example))

    word = VOCAB_BY_ID.get(item_id)
    if word is None:
        return None
    if item_type == "vocab_jp_ru":      # распознавание (+ диктант на слух)
        types = [vocab_choice, vocab_audio, dictation]
    elif item_type == "vocab_ru_jp":    # воспроизведение (+ свободный ввод)
        types = [vocab_reverse_choice, vocab_build, vocab_input]
    else:
        return None
    return types[reps % len(types)](word)


def _intro_step(char):
    info = KANA_BY_CHAR[char]
    step = {"type": "intro_kana", "char": char, "romaji": info["romaji"],
            "kind": info["kind"], "tts": char,
            "mnemonic": info.get("mnemonic"), "mnemonics": _mnemonics_for(info),
            "note": info.get("note")}
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

    # Быстрое связывание: доска сопоставления (до 5 пар)
    if len(words) >= 3:
        steps.append({"type": "exercise",
                      "exercise": vocab_match(random.sample(words, min(5, len(words))))})

    # Смешанная проверка: на слух и в обратную сторону
    mixed = [vocab_audio(w) if i % 2 else vocab_reverse_choice(w)
             for i, w in enumerate(words)]
    random.shuffle(mixed)
    steps.extend({"type": "exercise", "exercise": e} for e in mixed)

    # Воспроизведение: часть слов собрать из плиток, часть — ввести свободно
    produce = random.sample(words, min(4, len(words)))
    for i, w in enumerate(produce):
        steps.append({"type": "exercise",
                      "exercise": vocab_input(w) if i % 2 else vocab_build(w)})

    return steps


def _intro_kanji_step(k):
    step = {"type": "intro_kanji", "char": k["char"], "meaning": k["meaning"],
            "on": k.get("on", []), "kun": k.get("kun", []),
            "examples": k.get("examples", []), "mnemonic": k.get("mnemonic"),
            "mnemonic_reading": k.get("mnemonic_reading"),
            "tts": k["reading"]}
    if k.get("components"):  # 6.3: разбор знака на изученные компоненты
        step["components"] = k["components"]
    if k["char"] in STROKES:  # 6.2: анимация порядка черт при знакомстве
        step["strokes"] = STROKES[k["char"]]
    return step


def _kanji_lesson_steps(lesson):
    """Урок кандзи (6.2): знакомство с порядком черт -> трассировка -> значение
    -> чтение -> написание по памяти. Каждый знак сразу закрепляется."""
    steps = [{"type": "intro_text", "title": lesson["title"],
              "subtitle": lesson.get("subtitle", ""), "text": lesson["intro"],
              "icon": lesson.get("icon", "")}]
    kanji = [KANJI_BY_CHAR[c] for c in lesson["kanji"]]

    for k in kanji:
        steps.append(_intro_kanji_step(k))
        if k["char"] in STROKES:  # трассировка сразу после знакомства
            steps.append({"type": "exercise",
                          "exercise": kanji_writing(k["char"], mode="trace")})
        steps.append({"type": "exercise", "exercise": kanji_meaning(k)})

    # Смешанная проверка: чтение в слове
    reading = [kanji_reading(k) for k in kanji]
    random.shuffle(reading)
    steps.extend({"type": "exercise", "exercise": e} for e in reading)

    # Значение вперемешку — закрепление
    meaning = [kanji_meaning(k) for k in kanji]
    random.shuffle(meaning)
    steps.extend({"type": "exercise", "exercise": e} for e in meaning)

    # Написание по памяти
    for k in random.sample(kanji, min(3, len(kanji))):
        if k["char"] in STROKES:
            steps.append({"type": "exercise",
                          "exercise": kanji_writing(k["char"], mode="memory")})

    # Связь со словами N5 (6.5): записать слово этого юнита кандзи — но только
    # из уже введённых знаков (i+1), и слово должно быть ≥2 кандзи
    known = _kanji_introduced_through(lesson["id"])
    spellable, seen = [], set()
    for k in kanji:
        for ex in k.get("examples", []):
            w = ex["w"]
            if (w not in seen and _kanji_count(w) >= 2
                    and all(not _is_kanji(c) or c in known for c in w)):
                seen.add(w)
                spellable.append(ex)
    for ex in spellable[:4]:
        steps.append({"type": "exercise", "exercise": word_kanji(ex)})
    return steps


def _intro_grammar_step(p):
    return {"type": "intro_grammar", "title": p["title"],
            "structure": p["structure"], "meaning": p["meaning"],
            "register": p.get("register"), "explanation": p.get("explanation", []),
            "caution": p.get("caution"),
            "examples": [{"jp": "".join(e["tokens"]), "ru": e["ru"],
                          "tts": _sentence_reading(e)} for e in p["examples"]]}


def _grammar_lesson_steps(lesson):
    """Урок грамматики (2.4): объяснение точки -> узнавание (cloze) ->
    продукция (сборка предложения). Каждая точка закрепляется сразу."""
    steps = [{"type": "intro_text", "title": lesson["title"],
              "subtitle": lesson.get("subtitle", ""), "text": lesson["intro"],
              "icon": lesson.get("icon", "")}]
    points = [GRAMMAR_BY_ID[pid] for pid in lesson["points"]]

    for p in points:
        steps.append(_intro_grammar_step(p))
        steps.append({"type": "exercise",
                      "exercise": _grammar_cloze(p, p["examples"][0])})

    # Смешанная проверка узнавания по остальным примерам
    mixed = []
    for p in points:
        for e in (p["examples"][1:] or p["examples"]):
            mixed.append(_grammar_cloze(p, e))
    random.shuffle(mixed)
    steps.extend({"type": "exercise", "exercise": e} for e in mixed)

    # Мульти-пропуск частиц (тип 34), если в уроке набирается ≥3 точки-частицы
    if sum(1 for p in points if p["skill"] == "particle") >= 3:
        steps.append({"type": "exercise", "exercise": grammar_cloze(points)})

    # Дрилл спряжения для точек вежливых форм (тип 29): словарная -> целевая
    for p in points:
        if p["id"] in VERB_FORM_OF:
            for v in random.sample(VERBS, 3):
                steps.append({"type": "exercise",
                              "exercise": verb_conjugation(v, VERB_FORM_OF[p["id"]])})

    # Продукция: собрать предложение с конструкцией
    for p in points:
        steps.append({"type": "exercise",
                      "exercise": sentence_scramble(p, random.choice(p["examples"]))})
    return steps


def _gate_lesson_steps(lesson, n=12):
    """Тест-ворота юнита (раздел 3): только упражнения, без знакомств и
    подсказок — смешанная выборка по всем элементам юнита."""
    items = gate_items(lesson)
    random.shuffle(items)
    steps = [{"type": "intro_text", "title": lesson["title"],
              "subtitle": lesson.get("subtitle", ""),
              "text": "Тест-ворота юнита. Чтобы открыть следующий юнит, ответьте "
                      "верно минимум на 80%. Знакомств и подсказок здесь нет.",
              "icon": lesson.get("icon", "⛩")}]
    for item_type, item_id in items[:n]:
        ex = review_exercise(item_type, item_id, reps=random.randint(0, 3))
        if ex:
            steps.append({"type": "exercise", "exercise": ex})
    return steps


def make_lesson_steps(lesson_id):
    """Сценарий микроурока (2.1): знакомство -> распознавание -> воспроизведение
    -> слова -> ловушки. Чанки по 2–3 знака с мини-проверкой после каждого."""
    lesson = LESSON_BY_ID[lesson_id]
    if lesson.get("type") == "vocab":
        return _vocab_lesson_steps(lesson)
    if lesson.get("type") == "kanji":
        return _kanji_lesson_steps(lesson)
    if lesson.get("type") == "grammar":
        return _grammar_lesson_steps(lesson)
    if lesson.get("type") == "gate_test":
        return _gate_lesson_steps(lesson)
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
