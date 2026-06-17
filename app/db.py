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

-- UI-настройки клиента (тема/язык/озвучка/цель/…). Зеркало localStorage,
-- чтобы настройки переносились между устройствами и попадали в бэкап.
CREATE TABLE IF NOT EXISTS ui_prefs (
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
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL: читатели не блокируют писателя — две вкладки не ловят "database is
    # locked"; busy_timeout даёт записи подождать вместо мгновенной ошибки.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
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


# ---------- UI-настройки клиента (зеркало localStorage) ----------
# Значения хранятся как есть (строки localStorage; michi_tts/haptics — JSON-строки).
# Аллой-лист защищает таблицу от мусора и фиксирует, что именно синхронизируется.
UI_PREF_KEYS = {
    "michi_theme", "michi_lang", "michi_tts", "michi_haptics",
    "michi_daily_goal", "michi_romaji", "michi_onboarded",
}


def get_ui_prefs(conn):
    return {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM ui_prefs")}


def set_ui_pref(conn, key, value):
    """value: строка (записать/обновить) или None (удалить). Неизвестные ключи
    игнорируются — это не общий key-value стор."""
    if key not in UI_PREF_KEYS:
        return
    with conn:
        if value is None:
            conn.execute("DELETE FROM ui_prefs WHERE key = ?", (key,))
        else:
            conn.execute(
                "INSERT INTO ui_prefs(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )


# ---------- Резервная копия (бэкап/восстановление прогресса) ----------
# Весь прогресс — в одном SQLite-файле. Снимок снимаем/восстанавливаем через
# backup API SQLite: он транзакционно консистентен и не воюет с WAL и блоками
# открытых соединений (в отличие от копирования файла «на лету»).

_EXPECTED_TABLES = {"srs_cards", "reviews", "lesson_progress", "settings"}


def backup_to(dest_path):
    """Консистентный снимок текущей БД в dest_path."""
    src = connect()
    try:
        dst = sqlite3.connect(dest_path)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()


def is_michi_db(path):
    """Похож ли файл на нашу базу: читаемый SQLite с ожидаемыми таблицами."""
    try:
        c = sqlite3.connect(path)
        try:
            tables = {r[0] for r in c.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            c.close()
    except sqlite3.DatabaseError:
        return False
    return _EXPECTED_TABLES <= tables


def restore_from(src_path):
    """Перезаписать текущую БД содержимым src_path. Перед перезаписью кладёт
    страховочную копию рядом (<DB_PATH>.bak). Возвращает (cards, reviews)."""
    backup_to(str(DB_PATH) + ".bak")
    live = connect()
    try:
        incoming = sqlite3.connect(src_path)
        try:
            incoming.backup(live)          # перезаписываем живую базу копией
        finally:
            incoming.close()
        # Копия может быть старее текущей схемы (напр. без ui_prefs) — точечно
        # доукомплектовываем таблицы, добавленные после появления бэкапов (только
        # CREATE TABLE: re-run всей SCHEMA пересоздавал бы и индексы, а индекс на
        # колонку, которой нет в древней копии, упал бы). Иначе /api/prefs упёрся
        # бы в отсутствующую таблицу до перезапуска сервера.
        live.execute("CREATE TABLE IF NOT EXISTS ui_prefs ("
                     "key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        cards = live.execute("SELECT COUNT(*) FROM srs_cards").fetchone()[0]
        reviews = live.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    finally:
        live.close()
    return cards, reviews
