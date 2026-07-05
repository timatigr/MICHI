# -*- coding: utf-8 -*-
"""Пробный мини-тест N5: структура билета и эндпоинт.

Экзамен — оценка по всей программе (i+1 сознательно не действует) и строго
read-only: эндпоинту не нужна БД, фронт не шлёт ответы в SRS.
"""
from app.exercises import EXAM_TIME_LIMIT_SEC, exam_paper


def _total(paper):
    return sum(len(s["exercises"]) for s in paper["sections"])


def test_exam_structure_with_listening():
    paper = exam_paper(listening=True, seed=7)
    assert [s["id"] for s in paper["sections"]] == [
        "moji", "goi", "kanji", "bunpou", "choukai"]
    assert _total(paper) == 30
    assert paper["time_limit_sec"] == EXAM_TIME_LIMIT_SEC
    for s in paper["sections"]:
        assert s["title"] and s["jp"]
        for ex in s["exercises"]:
            assert ex and ex.get("type")


def test_exam_without_listening():
    paper = exam_paper(listening=False, seed=7)
    ids = [s["id"] for s in paper["sections"]]
    assert "choukai" not in ids and len(ids) == 4
    assert _total(paper) == 26


def test_exam_listening_is_audio_only():
    cho = next(s for s in exam_paper(listening=True, seed=1)["sections"]
               if s["id"] == "choukai")
    assert len(cho["exercises"]) == 4
    assert all(ex["type"] == "vocab_audio" for ex in cho["exercises"])


def test_exam_sections_mix_types():
    paper = exam_paper(listening=True, seed=3)
    by_id = {s["id"]: s for s in paper["sections"]}
    goi_types = {ex["type"] for ex in by_id["goi"]["exercises"]}
    assert "vocab_choice" in goi_types and "vocab_reverse_choice" in goi_types
    kanji_types = {ex["type"] for ex in by_id["kanji"]["exercises"]}
    assert kanji_types == {"kanji_meaning", "kanji_reading"}
    # грамматика ревью-ветки — одиночный пропуск: выбор частицы/формы
    assert all(ex["type"] in ("particle_choice", "grammar_choice")
               for ex in by_id["bunpou"]["exercises"])


def test_exam_random_without_seed():
    # без seed — валидный билет (не падает на реальных реестрах)
    paper = exam_paper()
    assert _total(paper) == 30


def test_exam_endpoint(make_client):
    c = make_client()
    r = c.get("/api/exam")
    assert r.status_code == 200
    data = r.json()
    assert len(data["sections"]) == 5 and data["time_limit_sec"] > 0
    r2 = c.get("/api/exam?listening=0")
    assert len(r2.json()["sections"]) == 4
