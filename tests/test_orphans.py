# -*- coding: utf-8 -*-
"""Защита от «осиротевших» SRS-карточек.

Инвариант: весь контент, который создаётся завершением урока, должен резолвиться
и собираться в упражнение. И обратно — карточку с исчезнувшим item_id движок
обязан игнорировать (не считать в due/new, не подавать в очередь), а ручная
очистка remove_orphans — удалять вместе с журналом.
"""
import json

from fsrs import Card

from app import srs_engine
from app.content.registry import LESSONS, item_exists, srs_items_for_lesson
from app.exercises import item_info, review_exercise


def test_every_created_item_resolves():
    """Каждая (item_type, item_id), создаваемая уроком, резолвится и собирается
    в упражнение. Ловит будущий рассинхрон: переименовали id слова/кандзи, а урок
    или KanjiVG-черты остались со старым — карточка осиротеет ещё при создании."""
    seen = 0
    for lesson in LESSONS:
        for item_type, item_id in srs_items_for_lesson(lesson):
            seen += 1
            assert item_exists(item_type, item_id), \
                f"{lesson['id']}: {item_type}/{item_id} не резолвится"
            assert review_exercise(item_type, item_id, reps=0) is not None, \
                f"{item_type}/{item_id}: review_exercise=None (нет черт/данных?)"
            info = item_info(item_type, item_id)
            assert info["title"] != item_id or info["sub"], \
                f"{item_type}/{item_id}: item_info — голый фолбэк на id"
    assert seen > 0


def test_item_exists_rejects_unknown():
    assert not item_exists("kana", "Ω")
    assert not item_exists("vocab_jp_ru", "nope_id")
    assert not item_exists("kanji_meaning", "X")
    assert not item_exists("grammar", "g999")
    assert not item_exists("board", "match:whatever")   # тип-доска картой не бывает


def _add_card(conn, item_type, item_id, reps=0, due_at=None):
    card = Card()
    conn.execute(
        "INSERT INTO srs_cards(item_type, item_id, fsrs, state, due_at, reps) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (item_type, item_id, json.dumps(card.to_dict()), card.state.value,
         due_at or card.due.isoformat(), reps))
    conn.commit()


def test_counts_and_queue_ignore_orphan_new(conn, settings):
    srs_engine.create_cards(conn, "kana", ["あ"])     # живая новая карточка
    _add_card(conn, "kana", "Ω")                       # знака нет в реестре

    assert srs_engine.counts(conn, settings)["new_total"] == 1
    ids = {r["item_id"] for r in srs_engine.get_queue(conn, settings)}
    assert "あ" in ids and "Ω" not in ids


def test_orphan_due_card_not_counted_or_served(conn, settings):
    past = "2000-01-01T00:00:00+00:00"
    _add_card(conn, "vocab_jp_ru", "ghost", reps=3, due_at=past)

    assert srs_engine.counts(conn, settings)["due"] == 0
    assert srs_engine.get_queue(conn, settings) == []


def test_forecast_excludes_orphans(conn):
    _add_card(conn, "kana", "Ω", reps=2)               # осиротевшая, reps>0
    assert sum(d["count"] for d in srs_engine.forecast(conn)) == 0


def test_remove_orphans_deletes_card_and_journal(conn, settings):
    srs_engine.create_cards(conn, "kana", ["か"])
    live = conn.execute("SELECT * FROM srs_cards WHERE item_id='か'").fetchone()
    srs_engine.answer_card(conn, settings, live, True, 1000, "kana_recognition")

    _add_card(conn, "kana", "Ω")
    oid = conn.execute("SELECT id FROM srs_cards WHERE item_id='Ω'").fetchone()["id"]
    conn.execute("INSERT INTO reviews(card_id, reviewed_at, rating) VALUES (?, ?, ?)",
                 (oid, "2020-01-01T00:00:00+00:00", 3))
    conn.commit()

    assert srs_engine.remove_orphans(conn) == 1
    # осиротевшая карточка и её журнал удалены
    assert conn.execute("SELECT COUNT(*) AS c FROM srs_cards WHERE item_id='Ω'").fetchone()["c"] == 0
    assert conn.execute("SELECT COUNT(*) AS c FROM reviews WHERE card_id=?", (oid,)).fetchone()["c"] == 0
    # живая карточка и её журнал не тронуты
    assert conn.execute("SELECT COUNT(*) AS c FROM srs_cards WHERE item_id='か'").fetchone()["c"] == 1
    assert conn.execute("SELECT COUNT(*) AS c FROM reviews").fetchone()["c"] == 1
    assert srs_engine.remove_orphans(conn) == 0         # идемпотентно
