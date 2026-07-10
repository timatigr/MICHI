# -*- coding: utf-8 -*-
"""Анонимная идентификация пользователя через подписанный cookie.

Публичный хостинг: один общий сайт, но прогресс у каждого свой. На первом визите
выдаём анонимный идентификатор и кладём его в cookie, подписанную серверным
секретом (HMAC) — чтобы клиент не мог выдать себя за чужой uid, подобрав его.
Никаких паролей: ноль трения, прогресс привязан к браузеру. Полноценный вход
(синхронизация между устройствами) — следующий этап поверх этого же uid.

Секрет берём из MICHI_SECRET_KEY. Если он не задан (локальная разработка),
генерируем случайный и сохраняем в data/secret.key, чтобы cookie переживали
перезапуск. В проде MICHI_SECRET_KEY задаётся в окружении.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from pathlib import Path

COOKIE_NAME = "michi_uid"
_SECRET_ENV = "MICHI_SECRET_KEY"
_SECRET_FILE = Path(__file__).resolve().parent.parent / "data" / "secret.key"

# uid идёт в имя файла базы — допускаем только безопасные символы (urlsafe base64).
_UID_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")

# Запасной секрет на время жизни процесса: если ни env, ни файл недоступны
# (read-only ФС), cookie всё равно подписываются — просто сбросятся на рестарте.
_PROCESS_SECRET = secrets.token_bytes(32)

# Секрет из файла кэшируется после первого чтения: подпись проверяется на КАЖДОМ
# запросе (дважды: parse и, у новичков, sign), и без кэша это два дисковых чтения
# на запрос. Файл при жизни процесса не меняется (смена секрета = рестарт).
# Env-путь не кэшируем: он дёшев, а тесты подменяют его monkeypatch-ем.
_FILE_SECRET: bytes | None = None


def _secret() -> bytes:
    global _FILE_SECRET
    env = os.environ.get(_SECRET_ENV)
    if env:
        return env.encode("utf-8")
    if _FILE_SECRET is not None:
        return _FILE_SECRET
    try:
        if _SECRET_FILE.exists():
            _FILE_SECRET = _SECRET_FILE.read_bytes()
            return _FILE_SECRET
        _SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
        s = secrets.token_bytes(32)
        _SECRET_FILE.write_bytes(s)
        _FILE_SECRET = s
        return s
    except Exception:
        return _PROCESS_SECRET


def _sign(uid: str) -> str:
    mac = hmac.new(_secret(), uid.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"{uid}.{mac}"


def parse(token: str | None) -> str | None:
    """uid из cookie, если подпись валидна и формат безопасен; иначе None."""
    if not token or "." not in token:
        return None
    uid, _, mac = token.rpartition(".")
    if not _UID_RE.match(uid):
        return None
    expected = hmac.new(_secret(), uid.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return uid if hmac.compare_digest(mac, expected) else None


def new_token() -> tuple[str, str]:
    """(uid, подписанный токен для cookie) для нового анонимного пользователя."""
    uid = secrets.token_urlsafe(16)   # 22 urlsafe-символа, подходит под _UID_RE
    return uid, _sign(uid)
