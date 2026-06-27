# -*- coding: utf-8 -*-
"""Секрет подписи cookie в прод-режиме: предупреждение (main._secret_key_warning)
и fail-fast при старте (main._enforce_secret_key)."""
import pytest

from app import main


def test_no_warning_in_local_mode(monkeypatch):
    monkeypatch.delenv("MICHI_COOKIE_SECURE", raising=False)
    monkeypatch.delenv("MICHI_SECRET_KEY", raising=False)
    assert main._secret_key_warning() is None       # локально (http) — секрет не обязателен


def test_no_warning_when_secret_set(monkeypatch):
    monkeypatch.setenv("MICHI_COOKIE_SECURE", "1")
    monkeypatch.setenv("MICHI_SECRET_KEY", "x" * 32)
    assert main._secret_key_warning() is None       # прод + явный секрет — всё ок


def test_warns_in_prod_without_secret(monkeypatch):
    monkeypatch.setenv("MICHI_COOKIE_SECURE", "1")
    monkeypatch.delenv("MICHI_SECRET_KEY", raising=False)
    w = main._secret_key_warning()
    assert w and "MICHI_SECRET_KEY" in w            # прод без секрета — предупреждаем


def test_enforce_secret_key_raises_in_prod(monkeypatch):
    # Fail-fast: прод-режим без секрета — сервер не должен подняться.
    monkeypatch.setenv("MICHI_COOKIE_SECURE", "1")
    monkeypatch.delenv("MICHI_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MICHI_SECRET_KEY"):
        main._enforce_secret_key()


def test_enforce_secret_key_ok_with_secret(monkeypatch):
    monkeypatch.setenv("MICHI_COOKIE_SECURE", "1")
    monkeypatch.setenv("MICHI_SECRET_KEY", "x" * 32)
    main._enforce_secret_key()                      # явный секрет — старт разрешён


def test_enforce_secret_key_ok_local(monkeypatch):
    monkeypatch.delenv("MICHI_COOKIE_SECURE", raising=False)
    monkeypatch.delenv("MICHI_SECRET_KEY", raising=False)
    main._enforce_secret_key()                      # локально (http) — секрет не нужен
