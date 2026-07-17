# -*- coding: utf-8 -*-
"""Озвучка: нейроголоса Edge TTS + аниме-голоса VOICEVOX (если установлен).

- Edge TTS (онлайн, бесплатно): Нанами/Кэйта + «кавайный» вариант Нанами
  (поднятый тон и чуть живее темп).
- VOICEVOX (https://voicevox.hiroshiba.jp/ — бесплатный движок аниме-голосов:
  Дзундамон, Сикоку Мэтан и др.): если движок доступен, его голоса
  автоматически появляются в списке. Локально — установленный движок на
  127.0.0.1:50021; на публичном сервере — свой контейнер voicevox_engine
  через MICHI_VOICEVOX_URL: аниме-голоса получают ВСЕ посетители сайта,
  ничего не устанавливая (синтез серверный, браузер ходит только в /api/tts).

Файлы кэшируются на диске; скорость/громкость применяются на клиенте.

Два уровня кэша:
- tts_baked/ — прегенерированная озвучка всего курса (scripts/build_tts.py),
  коммитится в репозиторий и попадает в образ. Благодаря ей на публичном
  хостинге нейроголос работает БЕЗ живого синтеза (MICHI_TTS_ENABLED=0):
  Edge TTS под потоком посетителей Microsoft троттлит, а готовые файлы
  раздаются мгновенно.
- tts_cache/ — рантайм-кэш фраз, синтезированных на лету (локальная
  разработка, VOICEVOX); не коммитится.
"""
import asyncio
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

import edge_tts

_ROOT = Path(__file__).resolve().parent.parent
BAKED_DIR = _ROOT / "tts_baked"
CACHE_DIR = _ROOT / "tts_cache"
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

# --- VOICEVOX (движок аниме-голосов: локальный или контейнер рядом с приложением) ---
DEFAULT_VOICEVOX_URL = "http://127.0.0.1:50021"


def _vv_url() -> str:
    """Адрес движка. Читается на каждый запрос (не на импорт): тесты и
    docker-compose задают MICHI_VOICEVOX_URL (например, http://voicevox:50021)."""
    return os.environ.get("MICHI_VOICEVOX_URL", DEFAULT_VOICEVOX_URL).rstrip("/")


VV_NAME_RU = {
    "ずんだもん": "Дзундамон",
    "四国めたん": "Сикоку Мэтан",
    "春日部つむぎ": "Касукабэ Цумуги",
    "雨晴はう": "Амэхарэ Хау",
    "波音リツ": "Намине Рицу",
    "冥鳴ひまり": "Мэймэй Химари",
}
_vv_cache = {"ts": 0.0, "voices": [], "url": ""}


def _vv_get(path, timeout=2):
    with urllib.request.urlopen(_vv_url() + path, timeout=timeout) as r:
        return r.read()


def _vv_post(path, body=b"", timeout=20):
    req = urllib.request.Request(
        _vv_url() + path, data=body, method="POST",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


async def voicevox_voices():
    """Список голосов VOICEVOX; пусто, если движок не запущен. Кэш 60 с
    (ключуется адресом движка — смена MICHI_VOICEVOX_URL сбрасывает)."""
    if _vv_cache["url"] == _vv_url() and time.time() - _vv_cache["ts"] < 60:
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
    _vv_cache.update(ts=time.time(), voices=voices, url=_vv_url())
    return voices


async def list_voices():
    public_edge = [{"id": v["id"], "label": v["label"]} for v in EDGE_VOICES]
    return public_edge + await voicevox_voices()


def baked_voices():
    """Голоса, доступные без живого синтеза: Edge-список, если рядом лежит
    прегенерированный кэш (scripts/build_tts.py), плюс аниме-голоса VOICEVOX
    из манифеста voices.json (пишется тем же скриптом при --vv-speakers:
    сами файлы прегенерированы, живой движок посетителям не нужен). Пусто
    (кэш не собран) — фронт мягко откатится на голос браузера, как раньше."""
    if not (BAKED_DIR.is_dir() and any(BAKED_DIR.glob("*.mp3"))):
        return []
    voices = [{"id": v["id"], "label": v["label"]} for v in EDGE_VOICES]
    try:
        extra = json.loads((BAKED_DIR / "voices.json").read_text("utf-8"))
        voices += [{"id": v["id"], "label": v["label"]} for v in extra]
    except (OSError, ValueError, KeyError, TypeError):
        pass  # манифеста нет / битый — только Edge
    return voices


def _cached(filename: str):
    """Готовый файл в одном из кэшей: прегенерированный → рантаймовый."""
    for d in (BAKED_DIR, CACHE_DIR):
        p = d / filename
        if p.exists():
            return p
    return None


def _prepare(text: str) -> str:
    """Edge TTS обрезает хвост у очень коротких фраз (одиночные слоги
    вроде «い»). Точка в конце даёт движку законченную фразу с
    естественным затуханием — обрыва не слышно."""
    text = text.strip()[:MAX_TEXT_LEN]
    if len(text) <= 4 and not text.endswith(("。", "！", "？")):
        text += "。"
    return text


def _tmp_for(path: Path) -> Path:
    """Уникальный временный файл рядом с целью: два одновременных запроса на одну
    и ту же фразу пишут в РАЗНЫЕ tmp и атомарно replace-ят (общий .tmp мог
    повредиться при гонке)."""
    return path.with_name(f"{path.stem}.{os.getpid()}.{time.time_ns()}.tmp")


async def synthesize(text: str, voice: str, allow_synth: bool = True):
    """Вернуть (путь к файлу, media_type); синтез при отсутствии в кэше.

    allow_synth=False (публичный хостинг, MICHI_TTS_ENABLED=0): раздаём только
    готовые файлы; промах → FileNotFoundError, роут отвечает 503, и фронт
    озвучивает эту фразу голосом браузера."""
    voice = LEGACY_IDS.get(voice, voice)
    text = _prepare(text)

    if voice.startswith("vv:"):
        speaker = voice[3:]
        if not speaker.isdigit():
            raise ValueError("bad voicevox speaker")
        key = hashlib.sha1(f"{voice}|{text}".encode("utf-8")).hexdigest()
        # Прегенерированные аниме-голоса пережаты в mp3 (WAV в разы тяжелее
        # для репозитория/образа); рантайм-кэш живого синтеза остаётся WAV.
        hit = _cached(f"{key}.mp3")
        if hit is not None:
            return hit, "audio/mpeg"
        hit = _cached(f"{key}.wav")
        if hit is not None:
            return hit, "audio/wav"
        if not allow_synth:
            raise FileNotFoundError(f"{key}.wav")
        path = CACHE_DIR / f"{key}.wav"

        def synth():
            query = _vv_post(
                f"/audio_query?text={urllib.parse.quote(text)}&speaker={speaker}")
            return _vv_post(f"/synthesis?speaker={speaker}", query)
        wav = await asyncio.to_thread(synth)
        tmp = _tmp_for(path)
        tmp.write_bytes(wav)
        tmp.replace(path)
        return path, "audio/wav"

    v = EDGE_BY_ID.get(voice, EDGE_BY_ID[DEFAULT_VOICE])
    key = hashlib.sha1(f"{v['id']}|{text}".encode("utf-8")).hexdigest()
    hit = _cached(f"{key}.mp3")
    if hit is not None:
        return hit, "audio/mpeg"
    if not allow_synth:
        raise FileNotFoundError(f"{key}.mp3")
    path = CACHE_DIR / f"{key}.mp3"
    tmp = _tmp_for(path)
    await edge_tts.Communicate(
        text, v["voice"], pitch=v["pitch"], rate=v["rate"]).save(str(tmp))
    tmp.replace(path)
    return path, "audio/mpeg"
