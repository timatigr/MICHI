# -*- coding: utf-8 -*-
"""Озвучка: маршрутизация голосов и серверный VOICEVOX (без сети).

Ключевой инвариант публичного хостинга: MICHI_VOICEVOX_URL указывает на
контейнер движка рядом с приложением — аниме-голоса получают все посетители,
ничего не устанавливая (синтез серверный, браузер ходит только в /api/tts).
"""
import asyncio
import json

import pytest

from app import tts


@pytest.fixture(autouse=True)
def _fresh_vv_cache(monkeypatch):
    """Каждый тест — со сброшенным кэшем списка голосов."""
    monkeypatch.setattr(tts, "_vv_cache", {"ts": 0.0, "voices": [], "url": ""})


def test_vv_url_default_and_env(monkeypatch):
    monkeypatch.delenv("MICHI_VOICEVOX_URL", raising=False)
    assert tts._vv_url() == tts.DEFAULT_VOICEVOX_URL
    monkeypatch.setenv("MICHI_VOICEVOX_URL", "http://voicevox:50021/")
    assert tts._vv_url() == "http://voicevox:50021"   # хвостовой / срезан


def test_voices_include_voicevox_from_engine(monkeypatch):
    """Движок отвечает — его голоса появляются в общем списке после Edge."""
    speakers = [
        {"name": "ずんだもん", "styles": [{"name": "ノーマル", "id": 3}]},
        {"name": "四国めたん", "styles": [{"name": "あまあま", "id": 0},
                                          {"name": "ノーマル", "id": 2}]},
    ]
    monkeypatch.setattr(tts, "_vv_get",
                        lambda path, timeout=2: json.dumps(speakers).encode())
    voices = asyncio.run(tts.list_voices())
    ids = [v["id"] for v in voices]
    assert ids[:3] == ["nanami", "nanami-kawaii", "keita"]   # Edge всегда первым
    assert "vv:3" in ids and "vv:2" in ids                   # берётся стиль «ノーマル»
    zunda = next(v for v in voices if v["id"] == "vv:3")
    assert "Дзундамон" in zunda["label"] and "VOICEVOX" in zunda["label"]


def test_voices_degrade_without_engine(monkeypatch):
    """Движок недоступен — остаются только Edge-голоса, без ошибок."""
    def boom(path, timeout=2):
        raise OSError("connection refused")
    monkeypatch.setattr(tts, "_vv_get", boom)
    voices = asyncio.run(tts.list_voices())
    assert [v["id"] for v in voices] == ["nanami", "nanami-kawaii", "keita"]


def test_voices_cache_keyed_by_url(monkeypatch):
    """Смена MICHI_VOICEVOX_URL сбрасывает 60-секундный кэш списка."""
    calls = {"n": 0}

    def fake(path, timeout=2):
        calls["n"] += 1
        return json.dumps(
            [{"name": "ずんだもん", "styles": [{"name": "ノーマル", "id": 3}]}]).encode()

    monkeypatch.setattr(tts, "_vv_get", fake)
    monkeypatch.delenv("MICHI_VOICEVOX_URL", raising=False)
    asyncio.run(tts.voicevox_voices())
    asyncio.run(tts.voicevox_voices())          # кэш — второй раз не ходим
    assert calls["n"] == 1
    monkeypatch.setenv("MICHI_VOICEVOX_URL", "http://voicevox:50021")
    asyncio.run(tts.voicevox_voices())          # новый адрес — свежий запрос
    assert calls["n"] == 2


def test_synthesize_voicevox_routes_and_caches(monkeypatch, tmp_path):
    """vv:-голос идёт в движок (audio_query → synthesis) и кэшируется на диск."""
    monkeypatch.setattr(tts, "CACHE_DIR", tmp_path)
    calls = []

    def fake_post(path, body=b"", timeout=20):
        calls.append(path)
        return b'{"q":1}' if path.startswith("/audio_query") else b"RIFFwav"

    monkeypatch.setattr(tts, "_vv_post", fake_post)

    path, media = asyncio.run(tts.synthesize("ねこ", "vv:3"))
    assert media == "audio/wav" and path.read_bytes() == b"RIFFwav"
    assert [p.split("?")[0] for p in calls] == ["/audio_query", "/synthesis"]

    asyncio.run(tts.synthesize("ねこ", "vv:3"))   # кэш: движок не дёргаем
    assert len(calls) == 2


def test_synthesize_rejects_bad_speaker():
    with pytest.raises(ValueError):
        asyncio.run(tts.synthesize("ねこ", "vv:3; rm -rf"))
