# -*- coding: utf-8 -*-
"""Метрики владельца публичного сайта: агрегаты по всем пользователям.

На фронте нет ни аналитики, ни трекеров (и это фича) — но владельцу всё равно
нужно понимать, живёт ли продукт: сколько людей занимается, возвращаются ли
они (retention), где бросают (воронка уроков). Все ответы уже лежат в журналах
per-user баз — этот скрипт их агрегирует офлайн.

Базы открываются строго read-only (mode=ro): скрипт не меняет ни данные, ни
mtime файлов (по mtime работает автоочистка заброшенных баз). Дни считаются
по UTC — для агрегатов владельца этой точности достаточно.

Запуск (локально или на сервере рядом с data/):
    python scripts/owner_stats.py [--days N] [--json]

  --days N  окно ежедневной таблицы (DAU/новые/ответы), по умолчанию 14
  --json    машиночитаемый вывод вместо текстового отчёта
"""
import argparse
import json
import sqlite3
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db                          # noqa: E402
from app.content.registry import LESSON_ORDER   # noqa: E402

# Пауза между ответами, после которой считаем, что началась новая сессия.
SESSION_GAP = timedelta(minutes=30)

_LESSON_INDEX = {lid: i for i, lid in enumerate(LESSON_ORDER)}


def _parse_dt(iso):
    """ISO-строка → datetime в UTC; None, если не разобрать."""
    try:
        dt = datetime.fromisoformat(iso)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _read_user(path):
    """Сырьё по одному пользователю из его базы (read-only) или None (битая)."""
    try:
        conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        try:
            reviews = conn.execute(
                "SELECT reviewed_at, correct FROM reviews ORDER BY reviewed_at"
            ).fetchall()
            lessons = conn.execute(
                "SELECT lesson_id, completed_at FROM lesson_progress "
                "WHERE status = 'completed'"
            ).fetchall()
        finally:
            conn.close()
    except sqlite3.Error:
        return None

    times = sorted(t for t in (_parse_dt(r[0]) for r in reviews) if t)
    days = {t.date() for t in times}
    for _, completed_at in lessons:
        t = _parse_dt(completed_at)
        if t:
            days.add(t.date())
    return {
        "days": days,                                  # дни любой активности (UTC)
        "review_times": times,                         # для нарезки сессий
        "reviews": len(reviews),
        "correct": sum(1 for r in reviews if r[1]),
        "completed": [lid for lid, _ in lessons],
    }


def _sessions(times):
    """Длительности сессий в минутах: ответы с паузой ≤ SESSION_GAP — одна сессия."""
    spans, start, prev = [], None, None
    for t in times:
        if prev is not None and t - prev > SESSION_GAP:
            spans.append((prev - start).total_seconds() / 60)
            start = t
        if start is None:
            start = t
        prev = t
    if start is not None:
        spans.append((prev - start).total_seconds() / 60)
    return spans


def _retention(users, today):
    """Классический Dn: доля когорты, активная ровно на n-й день после первого."""
    out = {}
    for n in (1, 7, 30):
        eligible = [u for u in users if u["days"]
                    and min(u["days"]) <= today - timedelta(days=n)]
        retained = [u for u in eligible
                    if min(u["days"]) + timedelta(days=n) in u["days"]]
        out[f"D{n}"] = {
            "eligible": len(eligible),
            "retained": len(retained),
            "rate": round(len(retained) / len(eligible), 3) if eligible else None,
        }
    return out


def collect(data_dir=None, window_days=14):
    """Агрегировать метрики по всем базам каталога. Возвращает словарь отчёта."""
    data_dir = Path(data_dir) if data_dir else db.DATA_DIR
    users, skipped = [], 0
    paths = sorted(data_dir.glob("*.db")) if data_dir.exists() else []
    for path in paths:
        u = _read_user(path)
        if u is None:
            skipped += 1
        else:
            users.append(u)

    today = datetime.now(timezone.utc).date()
    active = [u for u in users if u["days"]]

    daily = []
    for off in range(window_days - 1, -1, -1):
        day = today - timedelta(days=off)
        daily.append({
            "day": day.isoformat(),
            "new_users": sum(1 for u in active if min(u["days"]) == day),
            "dau": sum(1 for u in active if day in u["days"]),
            "reviews": sum(sum(1 for t in u["review_times"] if t.date() == day)
                           for u in active),
        })

    spans = [s for u in active for s in _sessions(u["review_times"])]
    total_reviews = sum(u["reviews"] for u in users)
    total_correct = sum(u["correct"] for u in users)

    def furthest(u):
        idx = [_LESSON_INDEX[lid] for lid in u["completed"] if lid in _LESSON_INDEX]
        return (max(idx) + 1) / len(LESSON_ORDER) if idx else 0.0

    funnel = [
        ("заходили (есть база)", len(users)),
        ("есть учебная активность", len(active)),
        ("завершён ≥1 урок", sum(1 for u in users if u["completed"])),
        ("завершено ≥5 уроков", sum(1 for u in users if len(u["completed"]) >= 5)),
        ("завершено ≥20 уроков", sum(1 for u in users if len(u["completed"]) >= 20)),
        ("пройдено ≥10% пути", sum(1 for u in users if furthest(u) >= 0.10)),
        ("пройдено ≥50% пути", sum(1 for u in users if furthest(u) >= 0.50)),
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window_days": window_days,
        "users": {
            "total": len(users),
            "active": len(active),
            "returned": sum(1 for u in active if len(u["days"]) >= 2),
            "skipped_files": skipped,
        },
        "totals": {
            "reviews": total_reviews,
            "accuracy": round(total_correct / total_reviews, 3) if total_reviews else None,
            "lessons_completed": sum(len(u["completed"]) for u in users),
        },
        "retention": _retention(active, today),
        "sessions": {
            "count": len(spans),
            "median_minutes": round(statistics.median(spans), 1) if spans else None,
        },
        "daily": daily,
        "funnel": [{"step": s, "users": n} for s, n in funnel],
    }


def _pct(rate):
    return "—" if rate is None else f"{rate * 100:.0f}%"


def render(stats):
    """Текстовый отчёт по-русски."""
    u, t, r = stats["users"], stats["totals"], stats["retention"]
    lines = [
        f"MICHI — метрики владельца ({stats['generated_at']}, дни по UTC)",
        "",
        f"Пользователи: всего {u['total']}, с активностью {u['active']}, "
        f"возвращались {u['returned']}"
        + (f" (битых файлов пропущено: {u['skipped_files']})" if u["skipped_files"] else ""),
        f"Ответы: {t['reviews']} (точность {_pct(t['accuracy'])}), "
        f"завершено уроков: {t['lessons_completed']}",
        f"Сессии: {stats['sessions']['count']}, медиана "
        + (f"{stats['sessions']['median_minutes']} мин"
           if stats["sessions"]["median_minutes"] is not None else "—"),
        "",
        "Retention (когорта = все с активностью, день n после первого дня):",
    ]
    for name, d in r.items():
        lines.append(f"  {name}: {_pct(d['rate'])}  "
                     f"({d['retained']}/{d['eligible']} допустимых)")
    lines += ["", "Воронка:"]
    width = max(len(f["step"]) for f in stats["funnel"])
    for f in stats["funnel"]:
        lines.append(f"  {f['step']:<{width}}  {f['users']}")
    lines += ["", f"По дням (последние {stats['window_days']}):",
              "  день        новые  DAU  ответы"]
    for d in stats["daily"]:
        lines.append(f"  {d['day']}  {d['new_users']:>5}  {d['dau']:>3}  {d['reviews']:>6}")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description="Метрики владельца по базам пользователей")
    p.add_argument("--days", type=int, default=14, help="окно ежедневной таблицы")
    p.add_argument("--json", action="store_true", help="вывод в JSON")
    args = p.parse_args(argv)
    stats = collect(window_days=max(1, args.days))
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print(render(stats))


if __name__ == "__main__":
    main()
