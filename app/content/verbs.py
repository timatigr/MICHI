# -*- coding: utf-8 -*-
"""Глаголы N5 и их спряжение (SRS.md, разделы 3.1, 5.4 тип 29).

Минимальный конъюгатор для самых частотных форм N5: вежливые ます / ました /
ません и て-форма. Группа задаётся явно (1 — годан/у-глаголы, 2 — итидан/
ру-глаголы, 3 — неправильные する・くる), потому что по виду словарной формы
итидан и годан на -る не различить (かえる «возвращаться» — годан).

Поле `te` переопределяет て-форму для исключений (いく → いって).
"""

VERBS = [
    {"dict": "たべる", "group": 2, "romaji": "taberu", "ru": "есть, кушать"},
    {"dict": "みる",   "group": 2, "romaji": "miru",   "ru": "смотреть"},
    {"dict": "おきる", "group": 2, "romaji": "okiru",  "ru": "вставать"},
    {"dict": "ねる",   "group": 2, "romaji": "neru",   "ru": "спать, ложиться"},
    {"dict": "のむ",   "group": 1, "romaji": "nomu",   "ru": "пить"},
    {"dict": "よむ",   "group": 1, "romaji": "yomu",   "ru": "читать"},
    {"dict": "かく",   "group": 1, "romaji": "kaku",   "ru": "писать"},
    {"dict": "きく",   "group": 1, "romaji": "kiku",   "ru": "слушать, спрашивать"},
    {"dict": "はなす", "group": 1, "romaji": "hanasu", "ru": "говорить"},
    {"dict": "まつ",   "group": 1, "romaji": "matsu",  "ru": "ждать"},
    {"dict": "かう",   "group": 1, "romaji": "kau",    "ru": "покупать"},
    {"dict": "あう",   "group": 1, "romaji": "au",     "ru": "встречаться"},
    {"dict": "いく",   "group": 1, "romaji": "iku",    "ru": "идти, ехать", "te": "いって"},
    {"dict": "する",   "group": 3, "romaji": "suru",   "ru": "делать"},
    {"dict": "くる",   "group": 3, "romaji": "kuru",   "ru": "приходить"},
]

VERB_BY_DICT = {v["dict"]: v for v in VERBS}

# Сдвиг последней моры по рядам годзюон
I_ROW = {"う": "い", "く": "き", "ぐ": "ぎ", "す": "し", "つ": "ち",
         "ぬ": "に", "ぶ": "び", "む": "み", "る": "り"}
A_ROW = {"う": "わ", "く": "か", "ぐ": "が", "す": "さ", "つ": "た",
         "ぬ": "な", "ぶ": "ば", "む": "ま", "る": "ら"}
# Эвфонические окончания て-формы годан-глаголов
TE = {"う": "って", "つ": "って", "る": "って", "ぬ": "んで", "ぶ": "んで",
      "む": "んで", "く": "いて", "ぐ": "いで", "す": "して"}

FORM_LABEL = {"masu": "ます-форма", "mashita": "ました (прош.)",
              "masen": "ません (отриц.)", "te": "て-форма"}
_SUFFIX = {"masu": "ます", "mashita": "ました", "masen": "ません"}


def masu_stem(v):
    """Основа вежливой формы (перед ます)."""
    d = v["dict"]
    if v["group"] == 2:
        return d[:-1]
    if v["group"] == 3:
        return "し" if d == "する" else "き"   # くる → き
    return d[:-1] + I_ROW[d[-1]]


def conjugate(v, form):
    d = v["dict"]
    if form in _SUFFIX:
        return masu_stem(v) + _SUFFIX[form]
    if form == "te":
        if "te" in v:
            return v["te"]
        if v["group"] == 2:
            return d[:-1] + "て"
        if v["group"] == 3:
            return "して" if d == "する" else "きて"
        return d[:-1] + TE[d[-1]]
    raise ValueError(form)


def distractors(v, form, answer, n=3):
    """Правдоподобные неверные формы (типичные ошибки спряжения).
    Добор — формами других глаголов, чтобы вариантов всегда хватало."""
    d = v["dict"]
    cands = []
    if form in _SUFFIX:
        suf = _SUFFIX[form]
        cands.append(d + suf)            # без изменения основы
        cands.append(d[:-1] + suf)       # отброшен слог (итидан-стиль)
        if d[-1] in A_ROW:
            cands.append(d[:-1] + A_ROW[d[-1]] + suf)
        if v["group"] == 2 and d[-1] == "る":
            cands.append(d[:-1] + "り" + suf)   # ошибочно как годан
    else:  # te
        for end in set(TE.values()):
            cands.append(d[:-1] + end)
        cands.append(d[:-1] + "て")
    # добор формами других глаголов
    for ov in VERBS:
        if ov["dict"] != d:
            cands.append(conjugate(ov, form))
    out = []
    for c in cands:
        if c != answer and c not in out:
            out.append(c)
        if len(out) == n:
            break
    return out
