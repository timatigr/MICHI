# -*- coding: utf-8 -*-
"""Удаляет давно заброшенные пустые базы анонимных пользователей.

Публичный хостинг: каждая запись анонимной сессии заводит data/users/<uid>.db.
Базы без учебной активности (ни одного повторения/урока/карточки), которые давно
не трогали, — мусор от случайных визитов и ботов. Этот скрипт их удаляет.

Запуск (например, ежедневно по cron на сервере):
    python scripts/cleanup_users.py [days]   # days по умолчанию 30
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app import db   # noqa: E402

if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    removed = db.cleanup_stale_users(days)
    print(f"Удалено заброшенных пустых баз: {removed}")
