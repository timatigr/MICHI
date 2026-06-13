# -*- coding: utf-8 -*-
"""SRS-движок: создание карточек, авто-оценка, пиявки, счётчики, прогноз."""
from fsrs import Rating, State

from app import srs_engine


def test_create_cards_is_idempotent(conn):
    assert srs_engine.create_cards(conn, "kana", ["あ", "い"]) == ["あ", "い"]
    assert srs_engine.create_cards(conn, "kana", ["あ", "い"]) == []  # уже есть
    n = conn.execute("SELECT COUNT(*) AS c FROM srs_cards").fetchone()["c"]
    assert n == 2


def test_auto_rate_incorrect_is_again(conn):
    assert srs_engine.auto_rate(conn, False, 1000) == Rating.Again


def test_auto_rate_fast_correct_is_easy(conn):
    # быстрее дефолтного p25 (1500 мс) и без подсказки
    assert srs_engine.auto_rate(conn, True, 800) == Rating.Easy


def test_auto_rate_slow_correct_is_hard(conn):
    # медленнее дефолтного p75 (6000 мс)
    assert srs_engine.auto_rate(conn, True, 9000) == Rating.Hard


def test_auto_rate_hint_is_hard(conn):
    assert srs_engine.auto_rate(conn, True, 1000, used_hint=True) == Rating.Hard


def test_auto_rate_normal_correct_is_good(conn):
    assert srs_engine.auto_rate(conn, True, 3000) == Rating.Good


def _row(conn, item_id):
    return conn.execute(
        "SELECT * FROM srs_cards WHERE item_id = ?", (item_id,)).fetchone()


def test_leech_marked_after_six_lapses(conn, settings):
    srs_engine.create_cards(conn, "kana", ["か"])
    # вывести карточку в Review верными ответами
    for _ in range(6):
        r = _row(conn, "か")
        if r["state"] == State.Review.value:
            break
        srs_engine.answer_card(conn, settings, r, True, 1000, "kana_recognition")
    assert _row(conn, "か")["state"] == State.Review.value

    # шесть провалов из Review/Relearning → пиявка (4.2)
    for _ in range(srs_engine.LEECH_LAPSES):
        srs_engine.answer_card(
            conn, settings, _row(conn, "か"), False, 1000, "kana_recognition")

    final = _row(conn, "か")
    assert final["lapses"] >= srs_engine.LEECH_LAPSES
    assert final["is_leech"] == 1


def test_answer_card_writes_review_log(conn, settings):
    srs_engine.create_cards(conn, "kana", ["さ"])
    srs_engine.answer_card(conn, settings, _row(conn, "さ"), True, 1200, "kana_recognition")
    log = conn.execute("SELECT COUNT(*) AS c FROM reviews").fetchone()["c"]
    assert log == 1


def test_counts_shape(conn, settings):
    srs_engine.create_cards(conn, "kana", ["あ", "い", "う"])
    c = srs_engine.counts(conn, settings)
    assert set(c) == {"due", "new_available", "new_total", "reviews_done_today"}
    assert c["new_total"] == 3


def test_forecast_length_and_shape(conn):
    out = srs_engine.forecast(conn, days=7)
    assert len(out) == 7
    assert all(set(d) == {"date", "count"} for d in out)
