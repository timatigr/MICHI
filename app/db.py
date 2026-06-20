# -*- coding: utf-8 -*-
"""SQLite-хранилище. Схема из SRS.md раздела 12; reviews — append-only журнал,
из которого состояние SRS восстановимо (принцип из раздела 13.2).

Публичный хостинг (анонимные сессии, см. identity.py): у каждого пользователя
своя база data/users/<uid>.db. Так весь код, что и так принимает соединение
параметром, остаётся без изменений, а экспорт/импорт естественно охватывают
ровно «мой прогресс» (это копия одного файла) — и импорт не может затронуть
чужие данные. Базу создаём лениво (на первой записи), чтобы боты/краулеры не
плодили пустые файлы; для незнакомого пользователя на чтении отдаём эфемерную
in-memory базу с начальным состоянием.
"""
import json
import re
import sqlite3
import time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "users"

# uid приходит уже провалидированным из identity.parse/new_token; страхуемся
# ещё раз, т.к. он попадает в имя файла (защита от обхода каталога).
_UID_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")

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


def _user_path(user_id):
    if not _UID_RE.match(user_id or ""):
        raise ValueError(f"некорректный идентификатор пользователя: {user_id!r}")
    return DATA_DIR / f"{user_id}.db"


def _prepare(conn):
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL: читатели не блокируют писателя — две вкладки не ловят "database is
    # locked"; busy_timeout даёт записи подождать вместо мгновенной ошибки.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    # Схема идемпотентна (IF NOT EXISTS) — заодно доукомплектовывает базу, заведённую
    # на более старой версии. Дёшево: пара CREATE/INSERT-IGNORE на крошечных таблицах.
    with conn:
        conn.executescript(SCHEMA)
        for k, v in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                (k, json.dumps(v)),
            )
    return conn


def connect(user_id, create_if_missing=True):
    """Соединение с базой пользователя (data/users/<uid>.db).

    create_if_missing=False и базы ещё нет → эфемерная in-memory база: чтения дают
    начальное состояние (ноль карточек, дефолтные настройки), файл на диске не
    появляется. Записи должны звать с create_if_missing=True (по умолчанию).
    """
    path = _user_path(user_id)
    if path.exists() or create_if_missing:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return _prepare(sqlite3.connect(path, timeout=5.0))
    return _prepare(sqlite3.connect(":memory:"))


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


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
    "michi_mnemo_fav", "michi_mnemo_custom",
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


def backup_to(dest_path, user_id):
    """Консистентный снимок базы пользователя в dest_path."""
    src = connect(user_id, create_if_missing=False)
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


def restore_from(src_path, user_id):
    """Перезаписать базу пользователя содержимым src_path. Перед перезаписью кладёт
    страховочную копию рядом (<uid>.db.bak). Возвращает (cards, reviews).
    Затрагивает только файл этого пользователя — чужие данные недостижимы."""
    path = _user_path(user_id)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup_to(str(path) + ".bak", user_id)
    live = connect(user_id, create_if_missing=True)
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


# ---------- Чистка заброшенных пустых баз (публичный хостинг) ----------
# Анонимная сессия плодит базу при любой записи (в т.ч. зашёл-потыкал-ушёл).
# Базы без какой-либо учебной активности и давно не трогавшиеся — мусор;
# периодический вызов (cron, scripts/cleanup_users.py) удаляет их вместе с
# WAL/страховочными файлами. Базы с прогрессом не трогаются никогда.
_EMPTY_IF_ZERO = ("reviews", "lesson_progress", "srs_cards")


def cleanup_stale_users(max_age_days=30):
    """Удалить заброшенные (старше max_age_days) базы без учебной активности.
    Возвращает число удалённых пользователей."""
    if not DATA_DIR.exists():
        return 0
    cutoff = time.time() - max_age_days * 86400
    removed = 0
    for path in DATA_DIR.glob("*.db"):
        try:
            if path.stat().st_mtime > cutoff:
                continue
            probe = sqlite3.connect(path)
            try:
                empty = all(
                    probe.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0
                    for t in _EMPTY_IF_ZERO)
            finally:
                probe.close()
        except sqlite3.DatabaseError:
            continue   # битый/чужой файл — не наш, не трогаем
        if not empty:
            continue
        for suffix in ("", "-wal", "-shm", ".bak"):
            Path(str(path) + suffix).unlink(missing_ok=True)
        removed += 1
    return removed
