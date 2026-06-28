# -*- coding: utf-8 -*-
"""Pitch-акцент (高低アクセント) слов N5: контур тона для карточек и словаря.

Данные (word_id -> позиция спада) лежат в pitch_data.py (генерируется из
открытого датасета, см. scripts/fetch_pitch.py). Здесь — чистая логика
токийского стандарта: разбиение на моры, классификация паттерна
(平板/頭高/中高/尾高) и контур «высоко/низко» по морам. Без БД и SRS — это
справочная надстройка над словом (произношение), а не отдельная SRS-карточка.

Правила (drop = мора, ПОСЛЕ которой тон падает; 0 = спада нет):
  • 0  平板 heiban    — 1-я мора низкая, дальше высоко, частица остаётся высокой;
  • 1  頭高 atamadaka — 1-я высокая, дальше низко;
  • =N 尾高 odaka     — низкая-высоко…высоко, спад приходится на частицу;
  • иначе 中高 nakadaka — низкая, подъём, спад внутри слова.
"""
from .pitch_data import PITCH
from .vocab_n5 import WORD_BY_ID

# Малая кана сливается с предыдущей морой; っ, ん, ー — самостоятельные моры
# (так же моры считает датасет акцентов, поэтому drop совпадает с нашим индексом).
_SMALL = set("ゃゅょャュョぁぃぅぇぉァィゥェォ")


def mora_split(kana):
    """Разбить запись каной на моры."""
    out = []
    for ch in kana:
        if ch in _SMALL and out:
            out[-1] += ch
        else:
            out.append(ch)
    return out


def pattern(drop, n):
    """Имя паттерна по позиции спада и числу мор."""
    if drop == 0:
        return "heiban"
    if drop == 1:
        return "atamadaka"
    if drop >= n:
        return "odaka"
    return "nakadaka"


def _contour(drop, n):
    """(высокий тон по морам [1..n], высока ли присоединяемая частица)."""
    highs = []
    for i in range(1, n + 1):
        if drop == 1:
            highs.append(i == 1)
        elif drop == 0:
            highs.append(i > 1)
        else:
            highs.append(1 < i <= drop)
    return highs, drop == 0          # частица высокая только у 平板


def pitch_for(word_id):
    """Контур тона слова для фронта или None, если данных нет."""
    drop = PITCH.get(word_id)
    word = WORD_BY_ID.get(word_id)
    if drop is None or not word:
        return None
    moras = mora_split(word["kana"])
    highs, particle_high = _contour(drop, len(moras))
    return {
        "drop": drop,
        "pattern": pattern(drop, len(moras)),
        "moras": moras,
        "highs": highs,
        "particle_high": particle_high,
    }
