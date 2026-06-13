# -*- coding: utf-8 -*-
"""SQLite-хранилище. Упрощённая версия схемы из SRS.md раздела 12:
один пользователь, поэтому без таблицы users; reviews — append-only журнал,
из которого состояние SRS восстановимо (принцип из раздела 13.2).
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "michi.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS srs_cards (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type   TEXT NOT NULL,              -- 'kana' (далее: vocab, kanji, grammar)
    item_id     TEXT NOT NULL,              -- сам знак: 'あ', 'きゃ'
    fsrs        TEXT NOT NULL,              -- JSON fsrs.Card.to_dict()
    state       INTEGER NOT NULL,           -- 1 learning / 2 review / 3 relearning
    due_at      TEXT,                       -- ISO, денормализовано для выборок
    reps        INTEGER NOT NULL DEFAULT 0,
    lapses      INTEGER NOT NULL DEFAULT 0,
    is_leech    INTEGER NOT NULL DEFAULT 0,
    introduced_on TEXT,                     -- дата первого показа (лимит новых/день)
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(item_type, item_id)
);
CREATE INDEX IF NOT EXISTS idx_cards_due ON srs_cards(due_at);

CREATE TABLE IF NOT EXISTS reviews (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id       INTEGER NOT NULL REFERENCES srs_cards(id),
    reviewed_at   TEXT NOT NULL,
    rating        INTEGER NOT NULL,         -- 1 Again / 2 Hard / 3 Good / 4 Easy
    state_before  INTEGER,
    correct       INTEGER,
    duration_ms   INTEGER,
    exercise_type TEXT
);
CREATE INDEX IF NOT EXISTS idx_reviews_at ON reviews(reviewed_at);

CREATE TABLE IF NOT EXISTS lesson_progress (
    lesson_id    TEXT PRIMARY KEY,
    status       TEXT NOT NULL DEFAULT 'available',  -- available / completed
    score        REAL,
    attempts     INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

DEFAULT_SETTINGS = {
    "new_per_day": 12,        # раздел 4.4
    "reviews_per_day": 150,
    "desired_retention": 0.9,
}


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = connect()
    with conn:
        conn.executescript(SCHEMA)
        for k, v in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                (k, json.dumps(v)),
            )
    conn.close()


def get_settings(conn):
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {r["key"]: json.loads(r["value"]) for r in rows}


def set_setting(conn, key, value):
    with conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, json.dumps(value)),
        )
