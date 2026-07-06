# -*- coding: utf-8 -*-
"""Серверная резервная копия всех данных сайта (страховка владельца).

Не путать с пользовательским экспортом (db.backup_to): тот сохраняет прогресс
одного пользователя по его собственному запросу. Здесь — защита от потери тома
целиком: единственная копия прогресса ВСЕХ посетителей лежит на одном диске
(data/), и без резервной копии авария диска = безвозвратная потеря всего.

Как снимается: каждый data/users/*.db копируется через SQLite backup API
(транзакционно консистентно, дружит с WAL и открытыми соединениями — копировать
файлы «на лету» нельзя), плюс data/secret.key (без него после восстановления
разлогинятся все, если секрет не задан через MICHI_SECRET_KEY). Всё пакуется в
один архив data/backups/michi-data-*.tar.gz с ротацией старых.

Offsite: локальный архив не переживёт потерю тома, поэтому при заданных
MICHI_BACKUP_S3_* архив дополнительно выгружается в любое S3-совместимое
хранилище (Cloudflare R2, Backblaze B2, AWS S3, MinIO…). Подпись запроса —
AWS Signature V4 на чистой stdlib: boto3 не тянем ради одного PUT. Ротацию
удалённых копий делайте lifecycle-политикой бакета — ключу с сервера лучше
вообще не давать прав на удаление (тогда взлом сервера не сотрёт бэкапы).

Восстановление: распаковать архив в data/ нового тома
(tar -xzf michi-data-*.tar.gz -C data) и перезапустить сервер.

Переменные окружения:
  MICHI_BACKUP_ENABLED=0          — выключить фоновые бэкапы (по умолч. включены)
  MICHI_BACKUP_DIR=…              — куда класть архивы (по умолч. data/backups)
  MICHI_BACKUP_KEEP=14            — сколько локальных архивов хранить (0 = все)
  MICHI_BACKUP_INTERVAL_HOURS=24  — период фонового цикла
  MICHI_BACKUP_S3_ENDPOINT=https://<account>.r2.cloudflarestorage.com
  MICHI_BACKUP_S3_BUCKET=…        — бакет
  MICHI_BACKUP_S3_ACCESS_KEY=… / MICHI_BACKUP_S3_SECRET_KEY=… — ключи доступа
  MICHI_BACKUP_S3_REGION=auto     — регион подписи (R2: auto; AWS: eu-central-1…)
  MICHI_BACKUP_S3_PREFIX=michi    — префикс ключей в бакете

Ручной запуск: python scripts/backup_data.py
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import sqlite3
import tarfile
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit

from . import db

log = logging.getLogger("michi.backup")

ARCHIVE_PREFIX = "michi-data-"


def enabled() -> bool:
    return os.environ.get("MICHI_BACKUP_ENABLED", "1") != "0"


def _int_env(name, default, minimum=1):
    try:
        return max(minimum, int(os.environ.get(name, default)))
    except ValueError:
        return default


def backup_dir() -> Path:
    env = os.environ.get("MICHI_BACKUP_DIR")
    return Path(env) if env else db.DATA_DIR.parent / "backups"


def keep_count() -> int:
    return _int_env("MICHI_BACKUP_KEEP", 14, minimum=0)


def interval_sec() -> int:
    return _int_env("MICHI_BACKUP_INTERVAL_HOURS", 24) * 3600


def _snapshot_db(src: Path, dst: Path) -> None:
    """Консистентная копия одной базы через SQLite backup API.

    Сначала read-only соединение: оно гарантированно не трогает файл и его
    mtime, по которому работает автоочистка заброшенных баз. Если ro-режим
    не может прочитать базу (WAL требует восстановления после сбоя) — фолбэк
    на обычное соединение."""
    def copy(conn):
        conn.execute("PRAGMA busy_timeout = 5000")
        out = sqlite3.connect(dst)
        try:
            conn.backup(out)
        finally:
            out.close()

    try:
        conn = sqlite3.connect(src.as_uri() + "?mode=ro", uri=True)
        try:
            copy(conn)
            return
        finally:
            conn.close()
    except sqlite3.Error:
        dst.unlink(missing_ok=True)
    conn = sqlite3.connect(src, timeout=5.0)
    try:
        copy(conn)
    finally:
        conn.close()


def snapshot() -> Path | None:
    """Собрать архив-снимок: все базы data/users/*.db + secret.key.

    Возвращает путь архива; None — если бэкапить нечего (ни одной базы или ни
    одна не читается). Битые файлы пропускаются с предупреждением: один
    повреждённый файл не должен срывать бэкап остальных."""
    users = sorted(db.DATA_DIR.glob("*.db")) if db.DATA_DIR.exists() else []
    if not users:
        return None
    dest = backup_dir()
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    final = dest / f"{ARCHIVE_PREFIX}{stamp}.tar.gz"
    n = 1
    while final.exists():   # два прогона в одну секунду (ручной запуск, тесты)
        final = dest / f"{ARCHIVE_PREFIX}{stamp}-{n}.tar.gz"
        n += 1
    secret = db.DATA_DIR.parent / "secret.key"
    with tempfile.TemporaryDirectory(dir=dest) as tmp_dir:
        tmp = Path(tmp_dir)
        copies = []
        for src in users:
            dst = tmp / src.name
            try:
                _snapshot_db(src, dst)
            except sqlite3.Error:
                log.warning("Бэкап: файл пропущен (не читается): %s", src.name)
                continue
            copies.append(dst)
        if not copies:
            return None
        tmp_tar = tmp / "archive.tar.gz"
        with tarfile.open(tmp_tar, "w:gz") as tar:
            for c in copies:
                tar.add(c, arcname=f"users/{c.name}")
            if secret.exists():
                tar.add(secret, arcname="secret.key")
        # Атомично: недописанный архив не должен быть виден ротации/выгрузке.
        os.replace(tmp_tar, final)
    return final


def prune(keep: int | None = None) -> int:
    """Удалить старые локальные архивы, оставив keep новейших (0 = хранить все).
    Возвращает число удалённых."""
    keep = keep_count() if keep is None else keep
    d = backup_dir()
    if keep <= 0 or not d.exists():
        return 0
    archives = sorted(d.glob(ARCHIVE_PREFIX + "*.tar.gz"))
    removed = 0
    for p in archives[:-keep]:
        p.unlink(missing_ok=True)
        removed += 1
    return removed


def latest_archive() -> Path | None:
    d = backup_dir()
    if not d.exists():
        return None
    archives = sorted(d.glob(ARCHIVE_PREFIX + "*.tar.gz"))
    return archives[-1] if archives else None


# ---------- Offsite: S3-совместимое хранилище (R2 / B2 / S3 / MinIO) ----------

def s3_config() -> dict | None:
    """Настройки offsite-выгрузки из MICHI_BACKUP_S3_*; None — не настроено
    (это норма: локальные архивы работают и без offsite)."""
    endpoint = os.environ.get("MICHI_BACKUP_S3_ENDPOINT", "").rstrip("/")
    bucket = os.environ.get("MICHI_BACKUP_S3_BUCKET", "")
    access = os.environ.get("MICHI_BACKUP_S3_ACCESS_KEY", "")
    secret = os.environ.get("MICHI_BACKUP_S3_SECRET_KEY", "")
    if not (endpoint and bucket and access and secret):
        return None
    return {
        "endpoint": endpoint, "bucket": bucket, "access": access, "secret": secret,
        "region": os.environ.get("MICHI_BACKUP_S3_REGION", "auto"),
        "prefix": os.environ.get("MICHI_BACKUP_S3_PREFIX", "michi").strip("/"),
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sigv4_headers(cfg, method, host, canonical_uri, payload_hash, now=None):
    """Заголовки подписи AWS Signature V4 для одного запроса без query string.
    Подписываются host, x-amz-content-sha256 и x-amz-date."""
    now = now or datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    day = now.strftime("%Y%m%d")
    headers = {"host": host, "x-amz-content-sha256": payload_hash,
               "x-amz-date": amz_date}
    signed = ";".join(sorted(headers))
    canonical = "\n".join([
        method, canonical_uri, "",                                # пустой query
        "".join(f"{k}:{headers[k]}\n" for k in sorted(headers)),
        signed, payload_hash,
    ])
    scope = f"{day}/{cfg['region']}/s3/aws4_request"
    to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope,
                         hashlib.sha256(canonical.encode()).hexdigest()])
    key = ("AWS4" + cfg["secret"]).encode()
    for part in (day, cfg["region"], "s3", "aws4_request"):
        key = hmac.new(key, part.encode(), hashlib.sha256).digest()
    signature = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
    return {
        "Authorization": (f"AWS4-HMAC-SHA256 Credential={cfg['access']}/{scope}, "
                          f"SignedHeaders={signed}, Signature={signature}"),
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
    }


def upload_s3(path: Path, cfg: dict | None = None) -> str | None:
    """Выгрузить архив в S3-совместимое хранилище (PUT, path-style адресация).
    Возвращает URL объекта; None — если S3 не настроен. Ошибка сети/HTTP →
    исключение: молча потерять offsite-копию хуже, чем шумно упасть в лог."""
    cfg = s3_config() if cfg is None else cfg
    if cfg is None:
        return None
    key = f"{cfg['prefix']}/{path.name}" if cfg["prefix"] else path.name
    canonical_uri = quote(f"/{cfg['bucket']}/{key}", safe="/-_.~")
    url = cfg["endpoint"] + canonical_uri
    headers = _sigv4_headers(cfg, "PUT", urlsplit(cfg["endpoint"]).netloc,
                             canonical_uri, _sha256_file(path))
    headers["Content-Type"] = "application/gzip"
    headers["Content-Length"] = str(path.stat().st_size)
    with open(path, "rb") as f:
        req = urllib.request.Request(url, data=f, method="PUT", headers=headers)
        with urllib.request.urlopen(req, timeout=600):
            pass   # 2xx — успех; на 4xx/5xx urlopen сам поднимает HTTPError
    return url


def run(force: bool = False) -> dict:
    """Полный прогон: снапшот → локальная ротация → offsite (если настроен).

    force=False пропускает прогон при свежем архиве (моложе ~интервала): на
    auto-stop машинах (Fly) старт случается на каждом «пробуждении», и без этой
    проверки каждый визит после простоя рождал бы новый архив."""
    if not force:
        last = latest_archive()
        if last and time.time() - last.stat().st_mtime < interval_sec() * 0.9:
            return {"skipped": "recent", "archive": str(last)}
    path = snapshot()
    if path is None:
        return {"skipped": "empty"}
    result = {"archive": str(path), "size": path.stat().st_size, "pruned": prune()}
    uploaded = upload_s3(path)
    if uploaded:
        result["uploaded"] = uploaded
    return result
