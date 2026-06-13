# -*- coding: utf-8 -*-
"""Скачивает SVG-данные черт KanjiVG (CC BY-SA) для знаков хираганы
и складывает в компактный JSON: {знак: [path_d черты 1, черты 2, ...]}.

Запуск (однократно): .venv\\Scripts\\python.exe scripts\\fetch_kanjivg.py
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "app" / "content" / "kanjivg_kana.json"

BASIC = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
DAKUTEN = "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
SMALL = "ゃゅょっ"
KATA_BASIC = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
KATA_DAKUTEN = "ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ"
KATA_SMALL = "ャュョッー"
CHARS = BASIC + DAKUTEN + SMALL + KATA_BASIC + KATA_DAKUTEN + KATA_SMALL

URL = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{:05x}.svg"
PATH_RE = re.compile(r'<path[^>]*\bd="([^"]+)"')


def fetch(char):
    url = URL.format(ord(char))
    with urllib.request.urlopen(url, timeout=30) as r:
        svg = r.read().decode("utf-8")
    # Порядок элементов <path> в документе KanjiVG = порядок черт
    return PATH_RE.findall(svg)


def main():
    # Догружаем поверх уже скачанного (повторный запуск — только новые знаки)
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    failed = []
    for ch in CHARS:
        if ch in data:
            continue
        try:
            strokes = fetch(ch)
        except Exception as e:
            print(f"SKIP {ch}: {e}")
            failed.append(ch)
            continue
        if not strokes:
            print(f"SKIP {ch}: no paths")
            failed.append(ch)
            continue
        data[ch] = strokes
        print(f"{ch} ok ({len(strokes)} strokes)")
    OUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"saved {len(data)} chars -> {OUT}" + (f", failed: {failed}" if failed else ""))


if __name__ == "__main__":
    main()
