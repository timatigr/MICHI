# -*- coding: utf-8 -*-
"""Генерация data-файла pitch-акцентов (高低アクセント) для лексики N5.

Источник — открытый датасет kanjium (`data/source_files/raw/accents.txt`),
формат `написание⇥чтение⇥позиции спада` (через запятую; 0 = 平板 heiban).

Слова N5 записаны каной, поэтому матчим по ЧТЕНИЮ. Акцент берём ТОЛЬКО когда он
однозначен — единственное значение спада среди всех написаний с этим чтением:
у омографов (はし 橋[2]/箸[1]/端[0]) по одной кане нельзя выбрать верный тон, и
лучше не показать ничего, чем показать неправильно. Неоднозначные и ненайденные
слова просто остаются без данных (контур тона не рисуется).

Перезапускать после добавления слов в vocab_n5. Можно скормить локальную копию
датасета через переменную окружения ACCENTS_FILE (иначе качает по сети).

Запись: app/content/pitch_data.py  (PITCH = {word_id: drop}).
"""
import os
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.content.vocab_n5 import WORDS  # noqa: E402

URL = ("https://raw.githubusercontent.com/mifunetoshiro/kanjium/"
       "master/data/source_files/raw/accents.txt")


def readings_to_accents(text):
    """чтение -> множество позиций спада (по всем написаниям с этим чтением)."""
    by_reading = {}
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        reading, acc = parts[1], parts[2]
        prim = acc.split(",")[0].strip()        # первый = основной вариант
        if not prim.lstrip("-").isdigit():
            continue
        by_reading.setdefault(reading, set()).add(int(prim))
    return by_reading


def match_pitch(by_reading):
    """word_id -> drop для слов с ОДНОЗНАЧНЫМ акцентом по чтению."""
    pitch = {}
    for w in WORDS:
        accs = by_reading.get(w["kana"])
        if accs and len(accs) == 1:
            pitch[w["id"]] = next(iter(accs))
    return pitch


def render(pitch):
    out = [
        "# -*- coding: utf-8 -*-",
        '"""Сгенерировано scripts/fetch_pitch.py — НЕ редактировать вручную.',
        "",
        "Pitch-акцент (高低アクセント) лексики N5: word_id -> позиция спада тона",
        "(номер моры, после которой тон падает; 0 = 平板 heiban, без спада).",
        "Источник — открытый датасет kanjium; взяты только однозначные по чтению",
        f"слова. Покрытие: {len(pitch)}/{len(WORDS)}.",
        '"""',
        "PITCH = {",
    ]
    for w in WORDS:                       # порядок словаря → стабильный diff
        if w["id"] in pitch:
            out.append(f"    {w['id']!r}: {pitch[w['id']]},")
    out.append("}")
    return "\n".join(out) + "\n"


def main():
    src = os.environ.get("ACCENTS_FILE")
    if src:
        text = pathlib.Path(src).read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(URL, timeout=90) as r:
            text = r.read().decode("utf-8")
    pitch = match_pitch(readings_to_accents(text))
    (ROOT / "app" / "content" / "pitch_data.py").write_text(
        render(pitch), encoding="utf-8")
    print(f"pitch_data.py: {len(pitch)}/{len(WORDS)} слов с акцентом")
    return 0


if __name__ == "__main__":
    sys.exit(main())
