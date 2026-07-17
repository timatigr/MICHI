# -*- coding: utf-8 -*-
"""Прегенерация озвучки всего курса в tts_baked/ (нейроголоса Edge TTS).

Зачем: на публичном хостинге живой синтез выключен (MICHI_TTS_ENABLED=0 —
Microsoft троттлит Edge TTS под потоком посетителей), и без этого скрипта
посетители слышат браузерный голос — медленный, а у части систем японского
голоса нет вовсе. Готовые файлы /api/tts раздаёт мгновенно (и SW кэширует
их офлайн), не делая НИ ОДНОГО обращения к Microsoft в рантайме.

Обход контента собирает всё, что клиент может озвучить (data-tts / speak()):
шаги всех уроков, все ротации SRS-упражнений, раунды мини-игр, спряжения
глаголов, чтения примеров грамматики, свиток истории, сезоны, приветствия.
Пропущенная фраза — не поломка: /api/tts ответит 503, и фронт озвучит её
голосом браузера (см. app/main.py, комментарий у роутов озвучки).

Запуск из корня репозитория:
    python -m scripts.build_tts                    # все три Edge-голоса
    python -m scripts.build_tts --voices nanami    # быстрее: только Нанами
    python -m scripts.build_tts --vv-speakers 3,2  # + аниме-голоса VOICEVOX
    python -m scripts.build_tts --dry-run          # только посчитать фразы

Аниме-голоса (--vv-speakers, id стилей движка: 3 — Дзундамон, 2 — Сикоку
Мэтан): нужен запущенный локальный движок VOICEVOX (https://voicevox.hiroshiba.jp/,
адрес — MICHI_VOICEVOX_URL или 127.0.0.1:50021) и пакет lameenc
(requirements-dev.txt): WAV движка пережимается в mp3 — в разы легче для
репозитория. Рядом пишется манифест voices.json — по нему /api/tts/voices
показывает аниме-голоса посетителям БЕЗ живого движка на сервере.

Повторный запуск дозаписывает недостающее (кэш ключуется sha1(голос|текст)).
После добавления контента (/add-content) перезапустить и закоммитить новые
файлы: tts_baked/ коммитится в репозиторий и попадает в Docker-образ.
"""
import argparse
import asyncio
import hashlib
import io
import json
import re
import sys
import urllib.parse
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Консоль Windows по умолчанию cp1252 — японские фразы в логе роняли print
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app import tts                                # noqa: E402
from app.content import seasons, story             # noqa: E402
from app.content.registry import (                 # noqa: E402
    GRAMMAR_BY_ID, KANA_BY_CHAR, KANJI_BY_CHAR, LESSON_ORDER, VOCAB_BY_ID,
)
from app.content.verbs import VERBS, conjugate     # noqa: E402
from app.exercises import (                        # noqa: E402
    _sentence_reading, counter_rounds, exam_paper, kanji_forge_rounds,
    make_lesson_steps, minimal_pair_rounds, pitch_rounds, review_exercise,
    shiritori_rounds,
)

# Хирагана, катакана (+ фонетические расширения и полуширинная), кандзи, 々
_JAPANESE = re.compile(r"[぀-ヿㇰ-ㇿ一-鿿ｦ-ﾟ々]")

# Ключи, значения которых фронт передаёт в speak()/data-tts (см. app.js)
_SPEAK_KEYS = {"tts", "answer_tts", "char", "jp", "r", "reading", "kana"}


def _walk(obj, out):
    """Рекурсивно собрать озвучиваемые строки из любого JSON-подобного payload."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _SPEAK_KEYS and isinstance(v, str) and _JAPANESE.search(v):
                out.add(v)
            else:
                _walk(v, out)
    elif isinstance(obj, (list, tuple, set)):
        for v in obj:
            _walk(v, out)


def collect_texts():
    """Всё, что курс может произнести. Собираем с запасом: лишний короткий
    клип дешевле, чем «немая» фраза у посетителя."""
    texts = set()

    # Шаги всех уроков (интро, примеры, упражнения урока)
    for lid in LESSON_ORDER:
        _walk(make_lesson_steps(lid), texts)

    # Все ротации SRS-упражнений (reps выбирает тип из матрицы, 6 покрывает все)
    items = ([("kana", c) for c in KANA_BY_CHAR]
             + [(t, c) for c in KANJI_BY_CHAR
                for t in ("kanji_meaning", "kanji_reading", "kanji_writing")]
             + [("grammar", g) for g in GRAMMAR_BY_ID]
             + [(t, w) for w in VOCAB_BY_ID
                for t in ("vocab_jp_ru", "vocab_ru_jp")])
    for item_type, item_id in items:
        for reps in range(6):
            _walk(review_exercise(item_type, item_id, reps), texts)

    # Внутри упражнений random (выбор примера/глагола) — эти источники
    # перечисляем напрямую, полностью:
    for p in GRAMMAR_BY_ID.values():
        for e in p["examples"]:
            texts.add(_sentence_reading(e))
    for v in VERBS:
        for form in ("masu", "mashita", "masen", "te"):
            texts.add(conjugate(v, form))

    # Мини-игры: щедрый limit + повторы против random.sample внутри
    all_words = list(VOCAB_BY_ID.values())
    all_kanji = set(KANJI_BY_CHAR)
    for _ in range(15):
        _walk(minimal_pair_rounds(9999), texts)
        _walk(counter_rounds(9999), texts)
        _walk(pitch_rounds(9999), texts)
        _walk(kanji_forge_rounds(all_kanji, 9999), texts)
        _walk(shiritori_rounds(all_words, 9999), texts)
        _walk(exam_paper(listening=True), texts)

    # Свиток истории: фронт озвучивает склеенные сцены (render_scene)
    for ch in story.CHAPTERS:
        for scene in ch["scenes"]:
            _walk(story.render_scene(scene), texts)

    # Письма сезонов на «Сегодня»
    _walk(seasons.SEKKI, texts)

    # Приветствия шапки «Сегодня» и тест-фраза из настроек (см. app.js)
    texts |= {"こんにちは", "おはよう", "こんばんは", "こんにちは。ミチへようこそ。"}

    return texts


async def synth_all(texts, voice_ids, jobs):
    sem = asyncio.Semaphore(jobs)
    done, failed = 0, []
    total = len(texts) * len(voice_ids)

    async def one(text, vid):
        nonlocal done
        async with sem:
            for attempt in range(4):
                try:
                    await tts.synthesize(text, vid)
                    break
                except Exception as e:                      # сеть/троттлинг — ждём и повторяем
                    if attempt == 3:
                        failed.append((vid, text, repr(e)))
                        break
                    await asyncio.sleep(1.5 * 2 ** attempt)
            done += 1
            if done % 100 == 0 or done == total:
                print(f"  {done}/{total}…", flush=True)

    await asyncio.gather(*(one(t, v) for t in sorted(texts) for v in voice_ids))
    return failed


# --- Аниме-голоса VOICEVOX: движок → WAV → mp3 в tts_baked/ ---

def _wav_to_mp3(wav_bytes):
    """Пережать WAV движка (24кГц 16-бит моно) в mp3 ~48кбит/с без ffmpeg."""
    import lameenc  # dev-зависимость; нужна только для --vv-speakers
    with wave.open(io.BytesIO(wav_bytes)) as w:
        assert w.getsampwidth() == 2, "ожидается 16-битный WAV"
        rate, channels = w.getframerate(), w.getnchannels()
        pcm = w.readframes(w.getnframes())
    enc = lameenc.Encoder()
    enc.set_bit_rate(48)
    enc.set_in_sample_rate(rate)
    enc.set_channels(channels)
    enc.set_quality(2)
    return bytes(enc.encode(pcm)) + bytes(enc.flush())


def _vv_synth_mp3(text, speaker):
    """Синтез одной фразы движком + пережатие. Ключ и _prepare — как в app/tts.py:
    /api/tts найдёт файл тем же sha1(vv:id|подготовленный текст)."""
    prepared = tts._prepare(text)
    key = hashlib.sha1(f"vv:{speaker}|{prepared}".encode("utf-8")).hexdigest()
    path = tts.BAKED_DIR / f"{key}.mp3"
    if path.exists():
        return
    query = tts._vv_post(
        f"/audio_query?text={urllib.parse.quote(prepared)}&speaker={speaker}")
    wav = tts._vv_post(f"/synthesis?speaker={speaker}", query, timeout=60)
    tmp = tts._tmp_for(path)
    tmp.write_bytes(_wav_to_mp3(wav))
    tmp.replace(path)


async def synth_vv_all(texts, speakers, jobs):
    sem = asyncio.Semaphore(jobs)
    done, failed = 0, []
    total = len(texts) * len(speakers)

    async def one(text, sp):
        nonlocal done
        async with sem:
            for attempt in range(3):
                try:
                    await asyncio.to_thread(_vv_synth_mp3, text, sp)
                    break
                except Exception as e:
                    if attempt == 2:
                        failed.append((f"vv:{sp}", text, repr(e)))
                        break
                    await asyncio.sleep(1.5 * 2 ** attempt)
            done += 1
            if done % 100 == 0 or done == total:
                print(f"  vv {done}/{total}…", flush=True)

    await asyncio.gather(*(one(t, s) for t in sorted(texts) for s in speakers))
    return failed


def write_vv_manifest(speakers):
    """voices.json: id+лейблы прегенерированных аниме-голосов — по нему
    /api/tts/voices показывает их без живого движка. Слияние с прежним
    манифестом: повторный прогон с другим набором не теряет старые голоса."""
    live = {v["id"]: v["label"] for v in asyncio.run(tts.voicevox_voices())}
    path = tts.BAKED_DIR / "voices.json"
    merged = {}
    try:
        merged = {v["id"]: v["label"]
                  for v in json.loads(path.read_text("utf-8"))}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    for sp in speakers:
        vid = f"vv:{sp}"
        merged[vid] = live.get(vid, f"VOICEVOX #{sp} — аниме")
    path.write_text(
        json.dumps([{"id": i, "label": l} for i, l in sorted(merged.items())],
                   ensure_ascii=False, indent=1),
        encoding="utf-8")
    return merged


def main():
    ap = argparse.ArgumentParser(description="Прегенерация озвучки курса (Edge TTS)")
    ap.add_argument("--voices", default=",".join(v["id"] for v in tts.EDGE_VOICES),
                    help="id голосов через запятую (по умолчанию все Edge)")
    ap.add_argument("--jobs", type=int, default=4,
                    help="параллельных синтезов (не задирать: троттлинг Microsoft)")
    ap.add_argument("--vv-speakers", default="",
                    help="id стилей VOICEVOX через запятую (3 — Дзундамон, "
                         "2 — Сикоку Мэтан); нужен запущенный движок")
    ap.add_argument("--vv-jobs", type=int, default=2,
                    help="параллельных синтезов VOICEVOX (движок на CPU)")
    ap.add_argument("--dry-run", action="store_true",
                    help="только собрать и посчитать фразы, без синтеза")
    args = ap.parse_args()

    voice_ids = [v.strip() for v in args.voices.split(",") if v.strip()]
    unknown = [v for v in voice_ids if v not in tts.EDGE_BY_ID]
    if unknown:
        sys.exit(f"Неизвестные голоса: {unknown}; доступны: {list(tts.EDGE_BY_ID)}")
    vv_speakers = [s.strip() for s in args.vv_speakers.split(",") if s.strip()]
    if any(not s.isdigit() for s in vv_speakers):
        sys.exit(f"--vv-speakers ждёт числовые id стилей, получено: {vv_speakers}")
    if vv_speakers and not asyncio.run(tts.voicevox_voices()):
        sys.exit("Движок VOICEVOX не отвечает — запустите его "
                 "(https://voicevox.hiroshiba.jp/) или уберите --vv-speakers")

    texts = collect_texts()
    print(f"Фраз собрано: {len(texts)}; голосов: {len(voice_ids)} "
          f"({', '.join(voice_ids)}) → файлов: {len(texts) * len(voice_ids)}")
    if args.dry_run:
        longest = sorted(texts, key=len)[-5:]
        print("Самые длинные:", *longest, sep="\n  ")
        return

    # Синтез пишем сразу в tts_baked/: CACHE_DIR перенаправляется туда, а
    # _cached() тогда смотрит только в baked — уже готовые файлы пропускаются.
    tts.BAKED_DIR.mkdir(exist_ok=True)
    tts.CACHE_DIR = tts.BAKED_DIR

    failed = asyncio.run(synth_all(texts, voice_ids, args.jobs)) if voice_ids else []
    if vv_speakers:
        failed += asyncio.run(synth_vv_all(texts, vv_speakers, args.vv_jobs))
        labels = write_vv_manifest(vv_speakers)
        print("Манифест voices.json:",
              ", ".join(labels[f"vv:{s}"] for s in vv_speakers))
    # Оборванный синтез оставляет *.tmp (атомарная запись через replace) — убрать,
    # чтобы мусор не попадал в коммит
    for stale in tts.BAKED_DIR.glob("*.tmp"):
        stale.unlink(missing_ok=True)
    n_files = sum(1 for _ in tts.BAKED_DIR.glob("*.mp3"))
    size_mb = sum(p.stat().st_size for p in tts.BAKED_DIR.glob("*.mp3")) / 1e6
    print(f"Готово: {n_files} файлов, {size_mb:.1f} МБ в {tts.BAKED_DIR}")
    if failed:
        print(f"НЕ удалось ({len(failed)}) — перезапустите скрипт позже:")
        for vid, text, err in failed[:20]:
            print(f"  [{vid}] {text!r}: {err}")


if __name__ == "__main__":
    main()
