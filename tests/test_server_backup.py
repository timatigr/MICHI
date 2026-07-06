# -*- coding: utf-8 -*-
"""Серверный бэкап данных владельца (app/backup.py).

Инварианты:
- снапшот собирает КОНСИСТЕНТНЫЕ копии всех пользовательских баз + secret.key
  и они читаемы после распаковки;
- нет пользовательских баз → бэкапа нет (ни архива, ни каталога-мусора);
- ротация оставляет ровно keep новейших архивов;
- повторный прогон при свежем архиве пропускается (auto-stop машины Fly
  просыпаются на каждый визит — бэкап не должен плодиться), force его снимает;
- выгрузка в S3-совместимое хранилище шлёт корректный PUT с подписью SigV4
  (проверяется реальным HTTP-запросом на локальный сервер).
"""
import hashlib
import tarfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app import backup, db


@pytest.fixture
def data_env(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", tmp_path / "users")
    monkeypatch.setenv("MICHI_BACKUP_DIR", str(tmp_path / "backups"))
    for var in ("MICHI_BACKUP_KEEP", "MICHI_BACKUP_S3_ENDPOINT",
                "MICHI_BACKUP_S3_BUCKET", "MICHI_BACKUP_S3_ACCESS_KEY",
                "MICHI_BACKUP_S3_SECRET_KEY"):
        monkeypatch.delenv(var, raising=False)
    return tmp_path


def _make_user(uid):
    c = db.connect(uid)
    with c:
        c.execute("INSERT INTO srs_cards(item_type, item_id, fsrs, state) "
                  "VALUES ('kana', 'あ', '{}', 1)")
    c.close()


def test_snapshot_packs_users_and_secret(data_env, tmp_path):
    _make_user("userA0000000000000A")
    _make_user("userB0000000000000B")
    (tmp_path / "secret.key").write_bytes(b"s" * 32)

    path = backup.snapshot()
    assert path is not None and path.exists()

    with tarfile.open(path) as tar:
        names = set(tar.getnames())
        assert names == {"users/userA0000000000000A.db",
                         "users/userB0000000000000B.db", "secret.key"}
        tar.extractall(tmp_path / "restored", filter="data")

    # распакованная база — валидная michi-база с тем же содержимым
    restored = tmp_path / "restored" / "users" / "userA0000000000000A.db"
    assert db.is_michi_db(restored)
    import sqlite3
    c = sqlite3.connect(restored)
    try:
        assert c.execute("SELECT COUNT(*) FROM srs_cards").fetchone()[0] == 1
    finally:
        c.close()


def test_snapshot_nothing_to_backup(data_env):
    assert backup.snapshot() is None
    assert backup.run() == {"skipped": "empty"}
    assert not backup.backup_dir().exists() or not list(backup.backup_dir().iterdir())


def test_broken_db_is_skipped_but_backup_proceeds(data_env):
    _make_user("gooduser00000000000")
    (db.DATA_DIR / "broken0000000000000.db").write_text("это не sqlite",
                                                        encoding="utf-8")

    path = backup.snapshot()
    with tarfile.open(path) as tar:
        assert tar.getnames() == ["users/gooduser00000000000.db"]


def test_prune_keeps_newest(data_env):
    d = backup.backup_dir()
    d.mkdir(parents=True)
    for i in range(1, 6):
        (d / f"{backup.ARCHIVE_PREFIX}2026010{i}-000000.tar.gz").write_bytes(b"x")

    assert backup.prune(keep=2) == 3
    left = sorted(p.name for p in d.glob("*.tar.gz"))
    assert left == [f"{backup.ARCHIVE_PREFIX}20260104-000000.tar.gz",
                    f"{backup.ARCHIVE_PREFIX}20260105-000000.tar.gz"]
    # keep=0 — хранить всё
    assert backup.prune(keep=0) == 0


def test_run_skips_when_fresh_archive_exists(data_env):
    _make_user("userC0000000000000C")
    first = backup.run()
    assert "archive" in first and "skipped" not in first

    again = backup.run()
    assert again["skipped"] == "recent"

    forced = backup.run(force=True)
    assert "skipped" not in forced and forced["archive"] != first["archive"]
    assert len(list(backup.backup_dir().glob("*.tar.gz"))) == 2


class _S3Handler(BaseHTTPRequestHandler):
    seen = None   # заполняется тестом

    def do_PUT(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        # имена заголовков — к нижнему регистру: urllib их капитализирует
        _S3Handler.seen = {"path": self.path, "body": body,
                           "headers": {k.lower(): v for k, v in self.headers.items()}}
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):   # тишина в выводе pytest
        pass


def test_upload_s3_sends_signed_put(data_env, tmp_path, monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), _S3Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        endpoint = f"http://127.0.0.1:{server.server_port}"
        monkeypatch.setenv("MICHI_BACKUP_S3_ENDPOINT", endpoint)
        monkeypatch.setenv("MICHI_BACKUP_S3_BUCKET", "bkt")
        monkeypatch.setenv("MICHI_BACKUP_S3_ACCESS_KEY", "AKTEST")
        monkeypatch.setenv("MICHI_BACKUP_S3_SECRET_KEY", "SKTEST")

        payload = b"fake-archive-bytes"
        archive = tmp_path / "michi-data-20260101-000000.tar.gz"
        archive.write_bytes(payload)

        url = backup.upload_s3(archive)

        assert url == f"{endpoint}/bkt/michi/{archive.name}"
        seen = _S3Handler.seen
        assert seen["path"] == f"/bkt/michi/{archive.name}"
        assert seen["body"] == payload
        auth = seen["headers"]["authorization"]
        assert auth.startswith("AWS4-HMAC-SHA256 Credential=AKTEST/")
        assert "SignedHeaders=host;x-amz-content-sha256;x-amz-date" in auth
        assert seen["headers"]["x-amz-content-sha256"] == \
            hashlib.sha256(payload).hexdigest()
    finally:
        server.shutdown()
        server.server_close()


def test_run_uploads_offsite_when_configured(data_env, monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), _S3Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        monkeypatch.setenv("MICHI_BACKUP_S3_ENDPOINT",
                           f"http://127.0.0.1:{server.server_port}")
        monkeypatch.setenv("MICHI_BACKUP_S3_BUCKET", "bkt")
        monkeypatch.setenv("MICHI_BACKUP_S3_ACCESS_KEY", "AKTEST")
        monkeypatch.setenv("MICHI_BACKUP_S3_SECRET_KEY", "SKTEST")

        _make_user("userD0000000000000D")
        info = backup.run(force=True)
        assert info["uploaded"].endswith(".tar.gz")
        assert _S3Handler.seen["path"].startswith("/bkt/michi/")
    finally:
        server.shutdown()
        server.server_close()


def test_upload_s3_not_configured_returns_none(data_env, tmp_path):
    f = tmp_path / "a.tar.gz"
    f.write_bytes(b"x")
    assert backup.upload_s3(f) is None
