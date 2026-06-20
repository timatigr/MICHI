# -*- coding: utf-8 -*-
"""Лёгкий рейт-лимит по IP в памяти процесса (для одно-машинного деплоя).

Публичный хостинг: middleware выдаёт новый uid на каждый запрос без cookie, а
пишущие ручки лениво создают per-user базу — значит поток запросов без cookie от
бота может плодить базы и забивать диск. Скользящее окно на IP режет такой поток
в зародыше (для живого пользователя лимит незаметен). Состояние — в памяти: на
одной машине (см. fly.toml: одна машина + том) этого достаточно; за несколькими
инстансами лимит надо выносить в общий стор или на обратный прокси.

Источник IP за обратным прокси — заголовки прокси (Fly-Client-IP / X-Forwarded-For);
подделать их может лишь тот, кто ходит мимо прокси, поэтому на проде прокси
обязателен (TLS и так на нём). Параметры окна — через env:
  MICHI_RATELIMIT_ENABLED=0   — выключить совсем;
  MICHI_RATE_WINDOW_SEC=N     — длина окна в секундах (по умолчанию 10);
  MICHI_RATE_MAX=N            — сколько запросов к /api/* на IP за окно (по умолч. 60).
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)
_last_sweep = 0.0


def _int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


def _enabled() -> bool:
    return os.environ.get("MICHI_RATELIMIT_ENABLED", "1") != "0"


def _window() -> int:
    return _int_env("MICHI_RATE_WINDOW_SEC", 10)


def _limit() -> int:
    return _int_env("MICHI_RATE_MAX", 60)


def client_ip(request) -> str:
    """Реальный IP клиента за обратным прокси (иначе — адрес прямого соединения)."""
    hdr = request.headers
    for name in ("fly-client-ip", "x-real-ip"):
        v = hdr.get(name)
        if v:
            return v.strip()
    xff = hdr.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "?"


def _maybe_sweep(now: float, window: int) -> None:
    """Периодически выкидываем протухшие/пустые IP, чтобы словарь не рос без границ."""
    global _last_sweep
    if now - _last_sweep < window:
        return
    _last_sweep = now
    cutoff = now - window
    for ip in list(_hits.keys()):
        dq = _hits[ip]
        while dq and dq[0] <= cutoff:
            dq.popleft()
        if not dq:
            del _hits[ip]


def check(ip: str, now: float | None = None) -> tuple[bool, int]:
    """(allowed, retry_after_sec). allowed=False → лимит на этот IP превышен."""
    if not _enabled():
        return True, 0
    now = time.monotonic() if now is None else now
    window = _window()
    limit = _limit()
    with _lock:
        _maybe_sweep(now, window)
        dq = _hits[ip]
        cutoff = now - window
        while dq and dq[0] <= cutoff:
            dq.popleft()
        if len(dq) >= limit:
            retry = max(1, int(dq[0] + window - now) + 1)
            return False, retry
        dq.append(now)
        return True, 0


def reset() -> None:
    """Сброс состояния (для тестов)."""
    global _last_sweep
    with _lock:
        _hits.clear()
        _last_sweep = 0.0
