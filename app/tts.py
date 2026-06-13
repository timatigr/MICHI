# -*- coding: utf-8 -*-
"""Озвучка: нейроголоса Edge TTS + аниме-голоса VOICEVOX (если установлен).

- Edge TTS (онлайн, бесплатно): Нанами/Кэйта + «кавайный» вариант Нанами
  (поднятый тон и чуть живее темп).
- VOICEVOX (https://voicevox.hiroshiba.jp/ — бесплатный локальный движок
  аниме-голосов: Дзундамон, Сикоку Мэтан и др.): если движок запущен на
  127.0.0.1:50021, его голоса автоматически появляются в списке.

Файлы кэшируются на диске; скорость/громкость применяются на клиенте.
"""
import asyncio
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import edge_tts

CACHE_DIR = Path(__file__).resolve().parent.parent / "tts_cache"
CACHE_DIR.mkdir(exist_ok=True)

MAX_TEXT_LEN = 120
DEFAULT_VOICE = "nanami"

EDGE_VOICES = [
    {"id": "nanami",        "label": "Нанами — женский",
     "voice": "ja-JP-NanamiNeural", "pitch": "+0Hz",  "rate": "+0%"},
    {"id": "nanami-kawaii", "label": "Нанами-тян — кавайный ✿",
     "voice": "ja-JP-NanamiNeural", "pitch": "+30Hz", "rate": "+8%"},
    {"id": "keita",         "label": "Кэйта — мужской",
     "voice": "ja-JP-KeitaNeural",  "pitch": "+0Hz",  "rate": "+0%"},
]
EDGE_BY_ID = {v["id"]: v for v in EDGE_VOICES}
# Старые сохранённые настройки клиентов
LEGACY_IDS = {"ja-JP-NanamiNeural": "nanami", "ja-JP-KeitaNeural": "keita"}

# --- VOICEVOX (локальный движок аниме-голосов) ---
VOICEVOX_URL = "http://127.0.0.1:50021"
VV_NAME_RU = {
    "ずんだもん": "Дзундамон",
    "四国めたん": "Сикоку Мэтан",
    "春日部つむぎ": "Касукабэ Цумуги",
    "雨晴はう": "Амэхарэ Хау",
    "波音リツ": "Намине Рицу",
    "冥鳴ひまり": "Мэймэй Химари",
}
_vv_cache = {"ts": 0.0, "voices": []}


def _vv_get(path, timeout=2):
    with urllib.request.urlopen(VOICEVOX_URL + path, timeout=timeout) as r:
        return r.read()


def _vv_post(path, body=b"", timeout=20):
    req = urllib.request.Request(
        VOICEVOX_URL + path, data=body, method="POST",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


async def voicevox_voices():
    """Список голосов VOICEVOX; пусто, если движок не запущен. Кэш 60 с."""
    if time.time() - _vv_cache["ts"] < 60:
        return _vv_cache["voices"]

    def probe():
        speakers = json.loads(_vv_get("/speakers"))
        out = []
        for sp in speakers:
            styles = sp.get("styles") or []
            style = next((s for s in styles if s.get("name") == "ノーマル"),
                         styles[0] if styles else None)
            if style is None:
                continue
            name = VV_NAME_RU.get(sp["name"], sp["name"])
            out.append({"id": f"vv:{style['id']}",
                        "label": f"{name} — аниме (VOICEVOX)"})
        return out[:8]

    try:
        voices = await asyncio.to_thread(probe)
    except Exception:
        voices = []
    _vv_cache.update(ts=time.time(), voices=voices)
    return voices


async def list_voices():
    public_edge = [{"id": v["id"], "label": v["label"]} for v in EDGE_VOICES]
    return public_edge + await voicevox_voices()


def _prepare(text: str) -> str:
    """Edge TTS обрезает хвост у очень коротких фраз (одиночные слоги
    вроде «い»). Точка в конце даёт движку законченную фразу с
    естественным затуханием — обрыва не слышно."""
    text = text.strip()[:MAX_TEXT_LEN]
    if len(text) <= 4 and not text.endswith(("。", "！", "？")):
        text += "。"
    return text


async def synthesize(text: str, voice: str):
    """Вернуть (путь к файлу, media_type); синтез при отсутствии в кэше."""
    voice = LEGACY_IDS.get(voice, voice)
    text = _prepare(text)

    if voice.startswith("vv:"):
        speaker = voice[3:]
        if not speaker.isdigit():
            raise ValueError("bad voicevox speaker")
        key = hashlib.sha1(f"{voice}|{text}".encode("utf-8")).hexdigest()
        path = CACHE_DIR / f"{key}.wav"
        if not path.exists():
            def synth():
                query = _vv_post(
                    f"/audio_query?text={urllib.parse.quote(text)}&speaker={speaker}")
                return _vv_post(f"/synthesis?speaker={speaker}", query)
            wav = await asyncio.to_thread(synth)
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(wav)
            tmp.replace(path)
        return path, "audio/wav"

    v = EDGE_BY_ID.get(voice, EDGE_BY_ID[DEFAULT_VOICE])
    key = hashlib.sha1(f"{v['id']}|{text}".encode("utf-8")).hexdigest()
    path = CACHE_DIR / f"{key}.mp3"
    if not path.exists():
        tmp = path.with_suffix(".tmp")
        await edge_tts.Communicate(
            text, v["voice"], pitch=v["pitch"], rate=v["rate"]).save(str(tmp))
        tmp.replace(path)
    return path, "audio/mpeg"
