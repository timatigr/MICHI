# -*- coding: utf-8 -*-
"""Pitch-акцент 高低アクセント: моры, классификация паттерна, контур и данные."""
from app.content import pitch
from app.content.pitch_data import PITCH
from app.content.vocab_n5 import WORD_BY_ID


def test_mora_split_handles_small_kana_and_specials():
    assert pitch.mora_split("きゃく") == ["きゃ", "く"]          # малая ゃ слилась
    assert pitch.mora_split("がっこう") == ["が", "っ", "こ", "う"]  # っ — отдельная мора
    assert pitch.mora_split("せんせい") == ["せ", "ん", "せ", "い"]  # ん — мора
    assert pitch.mora_split("コーヒー") == ["コ", "ー", "ヒ", "ー"]  # ー — мора


def test_pattern_classification():
    assert pitch.pattern(0, 3) == "heiban"
    assert pitch.pattern(1, 3) == "atamadaka"
    assert pitch.pattern(2, 3) == "nakadaka"
    assert pitch.pattern(3, 3) == "odaka"      # спад на последней = на частице


def test_contour_known_words():
    # わたし [0] 平板: низкая-высокая-высокая, частица высокая
    p = pitch.pitch_for("watashi")
    assert p["pattern"] == "heiban"
    assert p["highs"] == [False, True, True] and p["particle_high"] is True
    # あなた [2] 中高: низкая-высокая-низкая, частица низкая
    p = pitch.pitch_for("anata")
    assert p["pattern"] == "nakadaka"
    assert p["highs"] == [False, True, False] and p["particle_high"] is False


def test_atamadaka_contour():
    """頭高: первая мора высокая, остальные низкие (синтетически, drop=1)."""
    highs, particle = pitch._contour(1, 4)
    assert highs == [True, False, False, False] and particle is False


def test_pitch_for_unknown_is_none():
    assert pitch.pitch_for("нет-такого-слова") is None


def test_data_keys_are_real_words():
    for wid in PITCH:
        assert wid in WORD_BY_ID, f"pitch_data ссылается на несуществующее слово {wid!r}"


def test_drop_within_mora_range():
    """Позиция спада не превышает число мор слова (иначе данные битые)."""
    for wid, drop in PITCH.items():
        n = len(pitch.mora_split(WORD_BY_ID[wid]["kana"]))
        assert 0 <= drop <= n, f"{wid}: drop={drop} вне [0,{n}]"


def test_coverage_is_substantial():
    """Покрытие должно быть значимым (иначе матчинг сломался)."""
    assert len(PITCH) >= 200, f"слишком мало слов с акцентом: {len(PITCH)}"
