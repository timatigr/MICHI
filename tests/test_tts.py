# -*- coding: utf-8 -*-
"""Озвучка: маршрутизация голосов и серверный VOICEVOX (без сети).

Ключевой инвариант публичного хостинга: MICHI_VOICEVOX_URL указывает на
контейнер движка рядом с приложением — аниме-голоса получают все посетители,
ничего не устанавливая (синтез серверный, браузер ходит только в /api/tts).
"""
import asyncio
import hashlib
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
    # Иначе живой синтез найдёт настоящий прегенерированный файл фразы
    monkeypatch.setattr(tts, "BAKED_DIR", tmp_path / "baked")
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


# --- Прегенерированная озвучка (tts_baked/, публичный хостинг) ---
# Инвариант: с MICHI_TTS_ENABLED=0 нейроголос жив за счёт готовых файлов,
# живого синтеза нет, промах мимо кэша — мягкий фолбэк (503 → голос браузера).

def _bake(dirpath, text, voice="nanami"):
    """Файл в кэше именно так, как его ищет synthesize: sha1(голос|текст),
    текст — после _prepare (короткие фразы получают завершающую точку)."""
    prepared = tts._prepare(text)
    key = hashlib.sha1(f"{voice}|{prepared}".encode("utf-8")).hexdigest()
    p = dirpath / f"{key}.mp3"
    p.write_bytes(b"ID3fake")
    return p


def test_baked_voices_empty_without_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(tts, "BAKED_DIR", tmp_path / "missing")
    assert tts.baked_voices() == []


def test_synthesize_serves_baked_without_synth(monkeypatch, tmp_path):
    monkeypatch.setattr(tts, "BAKED_DIR", tmp_path)
    monkeypatch.setattr(tts, "CACHE_DIR", tmp_path / "runtime")
    _bake(tmp_path, "ねこ")
    assert [v["id"] for v in tts.baked_voices()] == ["nanami", "nanami-kawaii", "keita"]

    path, media = asyncio.run(tts.synthesize("ねこ", "nanami", allow_synth=False))
    assert media == "audio/mpeg" and path.read_bytes() == b"ID3fake"

    with pytest.raises(FileNotFoundError):
        asyncio.run(tts.synthesize("いぬ", "nanami", allow_synth=False))


def test_api_tts_baked_mode(make_client, monkeypatch, tmp_path):
    """Роуты при выключенном синтезе: голоса из baked, попадание 200, промах 503."""
    from app import main
    monkeypatch.setattr(main, "_TTS_SYNTH_ENABLED", False)
    monkeypatch.setattr(tts, "BAKED_DIR", tmp_path)
    monkeypatch.setattr(tts, "CACHE_DIR", tmp_path / "runtime")
    _bake(tmp_path, "ねこ")
    c = make_client()

    ids = [v["id"] for v in c.get("/api/tts/voices").json()]
    assert ids == ["nanami", "nanami-kawaii", "keita"]   # без VOICEVOX: движка нет

    r = c.get("/api/tts", params={"text": "ねこ", "voice": "nanami"})
    assert r.status_code == 200 and r.content == b"ID3fake"
    assert r.headers["cache-control"] == "public, max-age=31536000"

    assert c.get("/api/tts", params={"text": "いぬ"}).status_code == 503


def test_api_tts_voices_empty_without_baked(make_client, monkeypatch, tmp_path):
    """Синтез выключен и baked не собран — поведение как раньше: голосов нет."""
    from app import main
    monkeypatch.setattr(main, "_TTS_SYNTH_ENABLED", False)
    monkeypatch.setattr(tts, "BAKED_DIR", tmp_path / "missing")
    assert make_client().get("/api/tts/voices").json() == []


def test_baked_vv_mp3_served_without_engine(monkeypatch, tmp_path):
    """Прегенерированный аниме-голос (mp3) раздаётся без живого движка."""
    monkeypatch.setattr(tts, "BAKED_DIR", tmp_path)
    monkeypatch.setattr(tts, "CACHE_DIR", tmp_path / "runtime")
    _bake(tmp_path, "ねこ", voice="vv:3")
    path, media = asyncio.run(tts.synthesize("ねこ", "vv:3", allow_synth=False))
    assert media == "audio/mpeg" and path.read_bytes() == b"ID3fake"
    with pytest.raises(FileNotFoundError):
        asyncio.run(tts.synthesize("いぬ", "vv:3", allow_synth=False))


def test_baked_voices_include_vv_manifest(monkeypatch, tmp_path):
    """voices.json (пишет scripts/build_tts.py) добавляет аниме-голоса к Edge."""
    monkeypatch.setattr(tts, "BAKED_DIR", tmp_path)
    _bake(tmp_path, "ねこ")
    (tmp_path / "voices.json").write_text(
        json.dumps([{"id": "vv:3", "label": "Дзундамон — аниме (VOICEVOX)"}]),
        encoding="utf-8")
    ids = [v["id"] for v in tts.baked_voices()]
    assert ids == ["nanami", "nanami-kawaii", "keita", "vv:3"]


def test_baked_voices_survive_broken_manifest(monkeypatch, tmp_path):
    """Битый voices.json не роняет список — остаются Edge-голоса."""
    monkeypatch.setattr(tts, "BAKED_DIR", tmp_path)
    _bake(tmp_path, "ねこ")
    (tmp_path / "voices.json").write_text("{оборванный", encoding="utf-8")
    assert [v["id"] for v in tts.baked_voices()] == ["nanami", "nanami-kawaii", "keita"]
