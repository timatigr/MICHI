# -*- coding: utf-8 -*-
"""Рейт-лимит по IP (app/ratelimit.py) и его подключение к /api/*."""
import pytest

from app import ratelimit


@pytest.fixture(autouse=True)
def _enable_small_limit(monkeypatch):
    """Включаем лимитер с маленьким окном/порогом и чистим состояние вокруг теста."""
    monkeypatch.setenv("MICHI_RATELIMIT_ENABLED", "1")
    monkeypatch.setenv("MICHI_RATE_WINDOW_SEC", "10")
    monkeypatch.setenv("MICHI_RATE_MAX", "3")
    ratelimit.reset()
    yield
    ratelimit.reset()


def test_allows_up_to_limit_then_blocks():
    for _ in range(3):
        assert ratelimit.check("1.2.3.4", now=100.0)[0]
    allowed, retry = ratelimit.check("1.2.3.4", now=100.0)
    assert not allowed and retry >= 1


def test_window_slides_and_recovers():
    for _ in range(3):
        ratelimit.check("1.2.3.4", now=100.0)
    assert not ratelimit.check("1.2.3.4", now=105.0)[0]   # ещё внутри окна
    assert ratelimit.check("1.2.3.4", now=111.0)[0]       # окно (10с) прошло


def test_separate_ips_are_independent():
    for _ in range(3):
        assert ratelimit.check("1.1.1.1", now=100.0)[0]
    assert ratelimit.check("2.2.2.2", now=100.0)[0]       # другой IP не задет


def test_disabled_flag_lets_everything_through(monkeypatch):
    monkeypatch.setenv("MICHI_RATELIMIT_ENABLED", "0")
    for _ in range(50):
        assert ratelimit.check("9.9.9.9", now=100.0)[0]


def test_client_ip_prefers_proxy_headers():
    class Req:
        def __init__(self, headers, host):
            self.headers = headers
            self.client = type("C", (), {"host": host})()

    assert ratelimit.client_ip(Req({"fly-client-ip": "9.9.9.9"}, "10.0.0.1")) == "9.9.9.9"
    assert ratelimit.client_ip(
        Req({"x-forwarded-for": "1.1.1.1, 2.2.2.2"}, "10.0.0.1")) == "1.1.1.1"
    assert ratelimit.client_ip(Req({}, "10.0.0.1")) == "10.0.0.1"


def test_api_returns_429_when_exhausted(make_client, monkeypatch):
    monkeypatch.setenv("MICHI_RATELIMIT_ENABLED", "1")
    monkeypatch.setenv("MICHI_RATE_MAX", "3")
    monkeypatch.setenv("MICHI_RATE_WINDOW_SEC", "30")
    client = make_client()
    ratelimit.reset()
    codes = [client.get("/api/overview").status_code for _ in range(6)]
    assert codes.count(200) == 3
    assert codes[-1] == 429
    assert "Retry-After" in client.get("/api/overview").headers
