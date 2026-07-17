# -*- coding: utf-8 -*-
"""«Диктант» 書き取り: услышал → записал (слово) / собрал из плиток (предложение).

Инварианты: материал только из переданного изученного (i+1); слова идут
свободным вводом с кана+ромадзи в accept; предложения — сборка с аудио-промптом
(звук вместо перевода) и фолбэком на перевод для офлайна.
"""
from app.content.registry import GRAMMAR_BY_ID, VOCAB_BY_ID
from app.exercises import _sentence_reading, dictation_rounds, sentence_dictation

WORDS = list(VOCAB_BY_ID.values())[:20]
POINTS = [p for p in GRAMMAR_BY_ID.values() if p.get("examples")][:4]


def test_sentence_dictation_audio_prompt():
    p = POINTS[0]
    e = p["examples"][0]
    ex = sentence_dictation(p, e)
    assert ex["type"] == "sentence_scramble"          # общий клиентский рендер
    assert ex["prompt"]["style"] == "audio"
    assert ex["prompt"]["tts"] == _sentence_reading(e)
    assert ex["prompt"]["fallback_text"] == e["ru"]   # офлайн: перевод вместо звука
    assert not ex["speak_after"]                      # звук и есть задание
    assert sorted(ex["tiles"]) == sorted(ex["answer_tokens"])


def test_rounds_mix_words_and_sentences():
    rounds = dictation_rounds(WORDS, POINTS, limit=9)
    assert len(rounds) == 9
    types = {r["type"] for r in rounds}
    assert types == {"dictation", "sentence_scramble"}
    n_sent = sum(1 for r in rounds if r["type"] == "sentence_scramble")
    assert n_sent == 3                                # ~треть — предложения
    for r in rounds:
        assert r["prompt"]["style"] == "audio"
        assert r["prompt"]["tts"]                     # всё озвучиваемо
        if r["type"] == "dictation":
            assert r["answer"] in r["accept"]         # кана принимается всегда


def test_rounds_only_words_without_grammar():
    rounds = dictation_rounds(WORDS, [], limit=8)
    assert rounds and all(r["type"] == "dictation" for r in rounds)


def test_rounds_shrink_with_scarce_material():
    rounds = dictation_rounds(WORDS[:2], [], limit=8)
    assert len(rounds) == 2                           # как мин. пары: сколько есть
    assert dictation_rounds([], [], limit=8) == []


def test_api_requires_learned_material(client):
    """Свежий пользователь без изученного — пустые раунды, не ошибка."""
    assert client.get("/api/dictation/rounds").json() == {"rounds": []}
