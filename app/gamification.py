# -*- coding: utf-8 -*-
"""Геймификация v1 (SRS.md раздел 8): XP, уровень аккаунта, достижения.

Принцип 12.6/13.2 — журнал ответов и прогресс уроков единственный источник
правды: XP и достижения ВЫЧИСЛЯЮТСЯ из reviews/lesson_progress, отдельного
состояния не храним (нечего рассинхронизировать). Дневная цель — клиентская
настройка (localStorage), сравнивается с today.xp на фронте.
"""
import math

from .content.registry import COURSES

XP_PER_REVIEW = 2     # повторение SRS (8.1: за повторения не меньше, чем за новое)
XP_PER_LESSON = 20    # завершённый урок/ворота


def _scalar(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row and row[0] is not None else 0


def _stats(conn, streak):
    """Сводка по журналам — основа и для XP, и для предикатов достижений."""
    last = {c["id"]: (c["lesson_ids"][-1] if c["lesson_ids"] else None) for c in COURSES}

    def done(lid):
        return bool(lid) and _scalar(
            conn, "SELECT COUNT(*) FROM lesson_progress WHERE lesson_id=? "
                  "AND status='completed'", (lid,))

    best_acc = _scalar(conn,
        "SELECT COALESCE(MAX(acc),0) FROM (SELECT SUM(correct)*100.0/COUNT(*) AS acc "
        "FROM reviews GROUP BY date(reviewed_at,'localtime') HAVING COUNT(*) >= 20)")
    return {
        "lessons_completed": _scalar(conn,
            "SELECT COUNT(*) FROM lesson_progress WHERE status='completed'"),
        "gates_passed": _scalar(conn,
            "SELECT COUNT(*) FROM lesson_progress WHERE status='completed' "
            "AND lesson_id LIKE '%-g%'"),
        "reviews_total": _scalar(conn, "SELECT COUNT(*) FROM reviews"),
        "cards_review": _scalar(conn,
            "SELECT COUNT(*) FROM srs_cards WHERE state=2 AND reps>0"),
        "kanji_learned": _scalar(conn,
            "SELECT COUNT(DISTINCT item_id) FROM srs_cards "
            "WHERE item_type LIKE 'kanji%' AND reps>0"),
        "words_learned": _scalar(conn,
            "SELECT COUNT(DISTINCT item_id) FROM srs_cards "
            "WHERE item_type LIKE 'vocab%' AND reps>0"),
        "best_day_accuracy": round(best_acc),
        "night_review": _scalar(conn,
            "SELECT COUNT(*) FROM reviews WHERE CAST(strftime('%H',reviewed_at,'localtime') "
            "AS INTEGER) < 5") > 0,
        "hiragana_done": done(last.get("hiragana")),
        "katakana_done": done(last.get("katakana")),
        "streak": streak,
    }


def _level(total_xp):
    """Квадратичная кривая (8.1): уровень n требует 50·(n-1)² суммарного XP."""
    level = int(math.isqrt(total_xp // 50)) + 1
    floor_xp = 50 * (level - 1) ** 2
    next_xp = 50 * level ** 2
    span = next_xp - floor_xp
    return {"level": level, "into_level": total_xp - floor_xp, "level_span": span,
            "percent": round((total_xp - floor_xp) / span * 100) if span else 0}


def xp_summary(conn):
    today = "date(reviewed_at,'localtime') = date('now','localtime')"
    reviews = _scalar(conn, "SELECT COUNT(*) FROM reviews")
    reviews_today = _scalar(conn, f"SELECT COUNT(*) FROM reviews WHERE {today}")
    lessons = _scalar(conn, "SELECT COUNT(*) FROM lesson_progress WHERE status='completed'")
    lessons_today = _scalar(conn,
        "SELECT COUNT(*) FROM lesson_progress WHERE status='completed' "
        "AND date(completed_at,'localtime') = date('now','localtime')")
    total = reviews * XP_PER_REVIEW + lessons * XP_PER_LESSON
    today_xp = reviews_today * XP_PER_REVIEW + lessons_today * XP_PER_LESSON
    return {"total": total, "today": today_xp, **_level(total)}


# Определения достижений (8.3): id, заголовок, описание, иконка, редкость,
# и предикат над сводкой _stats. unlocked вычисляется на лету.
_TIER = ("bronze", "silver", "gold", "legend")
ACHIEVEMENTS = [
    ("first_lesson", "Первый шаг", "Завершите первый урок", "🌱", 0, lambda s: s["lessons_completed"] >= 1),
    ("first_review", "Первое повторение", "Сделайте первое SRS-повторение", "🔁", 0, lambda s: s["reviews_total"] >= 1),
    ("first_kanji", "Первый кандзи", "Выучите первый иероглиф", "字", 0, lambda s: s["kanji_learned"] >= 1),
    ("gate_first", "Врата открыты", "Сдайте первый тест-ворота юнита", "⛩", 1, lambda s: s["gates_passed"] >= 1),
    ("lessons_10", "Прилежный", "10 пройденных уроков", "📘", 0, lambda s: s["lessons_completed"] >= 10),
    ("lessons_30", "Усердный", "30 пройденных уроков", "📗", 1, lambda s: s["lessons_completed"] >= 30),
    ("lessons_60", "Марафонец", "60 пройденных уроков", "📚", 2, lambda s: s["lessons_completed"] >= 60),
    ("rev_100", "Сотня", "100 повторений", "💯", 0, lambda s: s["reviews_total"] >= 100),
    ("rev_500", "Пятьсот", "500 повторений", "🌀", 1, lambda s: s["reviews_total"] >= 500),
    ("rev_1000", "Тысяча", "1000 повторений", "🎯", 2, lambda s: s["reviews_total"] >= 1000),
    ("streak_3", "Три дня подряд", "Серия 3 дня", "🔥", 0, lambda s: s["streak"] >= 3),
    ("streak_7", "Неделя в строю", "Серия 7 дней", "🔥", 1, lambda s: s["streak"] >= 7),
    ("streak_30", "Месяц пути", "Серия 30 дней", "🔥", 2, lambda s: s["streak"] >= 30),
    ("streak_100", "Сто дней", "Серия 100 дней", "🏔", 3, lambda s: s["streak"] >= 100),
    ("hiragana_done", "Хирагана покорена", "Пройдите весь курс хираганы", "あ", 1, lambda s: s["hiragana_done"]),
    ("katakana_done", "Катакана покорена", "Пройдите весь курс катаканы", "ア", 1, lambda s: s["katakana_done"]),
    ("kanji_10", "Десять знаков", "10 изученных кандзи", "十", 0, lambda s: s["kanji_learned"] >= 10),
    ("kanji_30", "Тридцать знаков", "30 изученных кандзи", "卅", 2, lambda s: s["kanji_learned"] >= 30),
    ("words_50", "Полсотни слов", "50 изученных слов", "📝", 1, lambda s: s["words_learned"] >= 50),
    ("words_150", "Полтораста слов", "150 изученных слов", "📖", 2, lambda s: s["words_learned"] >= 150),
    ("memory_20", "Долгая память", "20 карточек в долгой памяти", "🧠", 1, lambda s: s["cards_review"] >= 20),
    ("memory_50", "Крепкая память", "50 карточек в долгой памяти", "💎", 2, lambda s: s["cards_review"] >= 50),
    ("accuracy_day", "Снайпер", "День с точностью ≥90% (от 20 повторений)", "🎖", 2, lambda s: s["best_day_accuracy"] >= 90),
    ("night_owl", "Ночная сова", "Занятие между полуночью и 5 утра", "🦉", 1, lambda s: s["night_review"]),
    ("level_5", "Бывалый", "Достигните 5-го уровня аккаунта", "⭐", 2, lambda s: s.get("level", 1) >= 5),
]


def achievements(conn, streak):
    s = _stats(conn, streak)
    s["level"] = xp_summary(conn)["level"]
    items = [{"id": aid, "title": title, "desc": desc, "icon": icon,
              "tier": _TIER[tier], "unlocked": bool(pred(s))}
             for aid, title, desc, icon, tier, pred in ACHIEVEMENTS]
    return {"items": items, "unlocked": sum(1 for i in items if i["unlocked"]),
            "total": len(items)}
