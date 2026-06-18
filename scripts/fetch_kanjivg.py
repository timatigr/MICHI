# -*- coding: utf-8 -*-
"""Скачивает SVG-данные черт KanjiVG (CC BY-SA) для каны и кандзи
и складывает в компактные JSON: {знак: [path_d черты 1, черты 2, ...]}.

Кана -> kanjivg_kana.json, кандзи -> kanjivg_kanji.json.

Запуск (однократно): .venv\\Scripts\\python.exe scripts\\fetch_kanjivg.py
"""
import json
import re
import urllib.request
from pathlib import Path

CONTENT = Path(__file__).resolve().parent.parent / "app" / "content"
KANA_OUT = CONTENT / "kanjivg_kana.json"
KANJI_OUT = CONTENT / "kanjivg_kanji.json"

BASIC = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
DAKUTEN = "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
SMALL = "ゃゅょっ"
KATA_BASIC = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
KATA_DAKUTEN = "ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ"
KATA_SMALL = "ャュョッー"
KANA_CHARS = BASIC + DAKUTEN + SMALL + KATA_BASIC + KATA_DAKUTEN + KATA_SMALL

# Кандзи курса (раздел 6). Пополняется по мере добавления уроков кандзи.
KANJI_CHARS = ("一二三四五六七八九十日月火水木金土林森明本人大小中上下口目"
               "年時分半今何学校先生父母男女子友行来見聞話読書食飲"
               "高安新古多長東西南北山川天気雨"
               "百千万円出入立休国語外車電駅")

URL = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{:05x}.svg"
PATH_RE = re.compile(r'<path[^>]*\bd="([^"]+)"')


def fetch(char):
    url = URL.format(ord(char))
    with urllib.request.urlopen(url, timeout=30) as r:
        svg = r.read().decode("utf-8")
    # Порядок элементов <path> в документе KanjiVG = порядок черт
    return PATH_RE.findall(svg)


def fetch_set(chars, out):
    # Догружаем поверх уже скачанного (повторный запуск — только новые знаки)
    data = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    failed = []
    for ch in chars:
        if ch in data:
            continue
        try:
            strokes = fetch(ch)
        except Exception as e:
            print(f"SKIP {ch}: {e}")
            failed.append(ch)
            continue
        if not strokes:
            print(f"SKIP U+{ord(ch):04X}: no paths")
            failed.append(ch)
            continue
        data[ch] = strokes
        # Кодпоинт вместо самого знака — консоль Windows (cp1251) не печатает кану/кандзи
        print(f"U+{ord(ch):04X} ok ({len(strokes)} strokes)")
    out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    fail = ", failed: " + " ".join(f"U+{ord(c):04X}" for c in failed) if failed else ""
    print(f"saved {len(data)} chars -> {out.name}{fail}")


def main():
    fetch_set(KANA_CHARS, KANA_OUT)
    fetch_set(KANJI_CHARS, KANJI_OUT)


if __name__ == "__main__":
    main()
