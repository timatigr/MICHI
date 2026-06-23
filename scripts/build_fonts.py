# -*- coding: utf-8 -*-
"""Сборка self-hosted шрифтов (static/fonts/ + static/fonts.css) из Google Fonts.

Зачем: не зависеть от Google Fonts в рантайме (приватность — Google не видит IP,
быстрее FCP, работает офлайн через Service Worker). Inter берём вариативный со
срезами latin/latin-ext/cyrillic (RU/EN-интерфейс), Noto Sans JP субсетим по
ТОЧНОМУ набору японских глифов курса (Google text=API) — ~60 КБ на начертание
вместо мегабайтов.

Запуск (нужен интернет): .venv\\Scripts\\python scripts\\build_fonts.py
Перезапускать после добавления нового контента (кандзи/слова/грамматика), иначе
новый японский глиф не попадёт в субсет и отрисуется системным фолбэком.
"""
import glob
import hashlib
import pathlib
import re
import urllib.parse
import urllib.request

# Современный UA обязателен: иначе Google Fonts отдаёт ttf вместо woff2.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "static" / "fonts"
# Где искать японские глифы: весь контент + захардкоженный в статике японский.
SOURCES = (glob.glob(str(ROOT / "app" / "content" / "*.py"))
           + glob.glob(str(ROOT / "static" / "*.js"))
           + [str(ROOT / "static" / "index.html")])
INTER_RANGES = {"latin", "latin-ext", "cyrillic", "cyrillic-ext"}


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=60).read()


def _is_jp(ch: str) -> bool:
    o = ord(ch)
    return (0x3000 <= o <= 0x30FF       # CJK-пунктуация + хирагана + катакана
            or 0x4E00 <= o <= 0x9FFF    # CJK unified (кандзи)
            or 0x31F0 <= o <= 0x31FF    # катакана фонетич. расширение
            or 0xFF00 <= o <= 0xFFEF)   # полу-/полноширинные формы


def _jp_glyphs() -> str:
    chars = set()
    for f in SOURCES:
        for ch in pathlib.Path(f).read_text(encoding="utf-8"):
            if _is_jp(ch):
                chars.add(ch)
    return "".join(sorted(chars))


def _localize(css: str, prefix: str) -> str:
    """Скачать каждый gstatic-woff2 (в т.ч. text-субсет /l/font?kit=...),
    сохранить под именем по хэшу содержимого и переписать src на локальный путь."""
    for url in sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css))):
        data = _fetch(url)
        name = f"{prefix}-{hashlib.sha1(data).hexdigest()[:10]}.woff2"
        (FONTS_DIR / name).write_bytes(data)
        css = css.replace(url, f"fonts/{name}")
    return css


def main() -> None:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for old in FONTS_DIR.glob("*.woff2"):       # чистим прошлую сборку
        old.unlink()

    # Inter (вариативный): оставляем только нужные интерфейсу срезы.
    inter_css = _fetch("https://fonts.googleapis.com/css2?family=Inter:"
                       "wght@400;500;600;700&display=swap").decode()
    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{.*?\})", inter_css, re.S)
    inter = _localize("\n".join(b for label, b in blocks if label in INTER_RANGES), "inter")

    # Noto Sans JP: каждое начертание отдельным запросом с субсетом по тексту курса
    # (один общий запрос вернул бы один файл на все начертания).
    glyphs = _jp_glyphs()
    noto_parts = []
    for wght in (400, 500, 700):
        url = (f"https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@{wght}"
               "&display=swap&text=" + urllib.parse.quote(glyphs))
        noto_parts.append(_fetch(url).decode())
    noto = _localize("\n".join(noto_parts), "notojp")

    header = ("/* MICHI — self-host шрифтов (без Google Fonts: приватность + офлайн).\n"
              "   ГЕНЕРИРУЕТСЯ scripts/build_fonts.py — править генератор, не этот файл.\n"
              "   Inter: вариативный, срезы latin/latin-ext/cyrillic для RU/EN-UI.\n"
              "   Noto Sans JP: субсет по глифам курса (Google text=API), по начертаниям. */\n")
    (ROOT / "static" / "fonts.css").write_text(header + inter + "\n" + noto + "\n",
                                               encoding="utf-8")

    files = sorted(FONTS_DIR.glob("*.woff2"))
    total = sum(p.stat().st_size for p in files)
    print(f"Японских глифов в субсете: {len(glyphs)}")
    print(f"Файлов woff2: {len(files)} | всего {total // 1024} КБ")


if __name__ == "__main__":
    main()
