# -*- coding: utf-8 -*-
"""Заголовки безопасности (main._security_headers + middleware)."""
from app import main


def test_headers_present_on_static_and_api(client):
    for url in ("/", "/api/overview"):
        h = client.get(url).headers
        assert "Content-Security-Policy" in h
        assert "'self'" in h["Content-Security-Policy"]
        assert h["X-Content-Type-Options"] == "nosniff"
        assert h["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert h["X-Frame-Options"] == "DENY"


def test_csp_allows_app_resources():
    csp = main._CSP
    assert "frame-ancestors 'none'" in csp                       # анти-кликджекинг
    assert "font-src 'self'" in csp                              # шрифты self-hosted
    assert "style-src 'self' 'unsafe-inline'" in csp            # стили — только свой origin
    # Шрифты self-hosted: внешних запросов к Google Fonts быть не должно
    assert "googleapis.com" not in csp
    assert "gstatic.com" not in csp
    assert "img-src 'self' data:" in csp                         # PNG-слоты + data: favicon
    assert "media-src 'self'" in csp                             # <audio> озвучки /api/tts


def test_hsts_only_in_prod():
    assert "Strict-Transport-Security" in main._security_headers(secure=True)
    assert "Strict-Transport-Security" not in main._security_headers(secure=False)
