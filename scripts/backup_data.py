# -*- coding: utf-8 -*-
"""Снять серверный бэкап всех данных сайта прямо сейчас.

Консистентный снимок всех баз data/users/*.db + secret.key → tar.gz в
data/backups/ с ротацией; при настроенных MICHI_BACKUP_S3_* архив дополнительно
выгружается offsite (подробности и переменные окружения — app/backup.py).

Сервер и так делает это сам раз в сутки (MICHI_BACKUP_ENABLED); скрипт — для
ручного прогона перед рискованными работами и для внешнего cron.

Запуск: python scripts/backup_data.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app import backup   # noqa: E402

if __name__ == "__main__":
    info = backup.run(force=True)
    if info.get("skipped") == "empty":
        print("Бэкапить нечего: ни одной пользовательской базы.")
        sys.exit(0)
    print(f"Архив: {info['archive']} ({info['size'] / 1024:.0f} КиБ)")
    if info.get("pruned"):
        print(f"Ротация: удалено старых архивов: {info['pruned']}")
    if info.get("uploaded"):
        print(f"Offsite: {info['uploaded']}")
    else:
        print("Offsite не настроен (MICHI_BACKUP_S3_*) — архив только на этом диске.")
