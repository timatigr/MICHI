# -*- coding: utf-8 -*-
"""Штамповка версии Service Worker из хэша кэшируемой оболочки.

Браузер обновляет Service Worker, только если меняются БАЙТЫ самого sw.js
(он байт-сравнивает скрипт). Раньше VERSION бампался руками — забыл при деплое
→ у пользователей залипал старый JS навсегда (новый кэш не создавался). Этот
скрипт вычисляет хэш по файлам оболочки (список берётся из массива SHELL в самом
sw.js) и вписывает его в VERSION. Итог: sw.js меняется ровно тогда, когда
меняется что-то из оболочки — и ни секундой раньше (одинаковая оболочка → тот же
хэш → без лишнего сброса кэша).

sw.js в SHELL не входит, поэтому смена VERSION не влияет на сам хэш → скрипт
идемпотентен (повторный запуск ничего не трогает). Чистый stdlib, без
зависимостей. Запускается в Dockerfile при сборке (после COPY static), так что
прод-образ всегда отдаёт sw.js, согласованный со своей оболочкой.
"""
import hashlib
import pathlib
import re
import sys

STATIC = pathlib.Path(__file__).resolve().parent.parent / "static"
SW = STATIC / "sw.js"


def shell_files(sw_text):
    """Файлы оболочки по массиву SHELL в sw.js. URL-путь → файл в static/;
    «/» и «/index.html» оба указывают на index.html (дедуп по факту файла)."""
    m = re.search(r"const SHELL\s*=\s*\[(.*?)\]", sw_text, re.S)
    if not m:
        return []
    files, seen = [], set()
    for p in re.findall(r'"([^"]+)"', m.group(1)):
        f = STATIC / (p.lstrip("/") or "index.html")
        rp = f.resolve()
        if f.is_file() and rp not in seen:
            seen.add(rp)
            files.append(f)
    return sorted(files, key=lambda f: f.name)


def compute_version(sw_text):
    """12-символьный hex-хэш по именам и содержимому файлов оболочки."""
    h = hashlib.sha256()
    for f in shell_files(sw_text):
        h.update(f.name.encode("utf-8"))
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:12]


def stamp():
    """Привести VERSION в sw.js к хэшу оболочки. Возвращает (version, changed)."""
    text = SW.read_text(encoding="utf-8")
    version = compute_version(text)
    new = re.sub(r'(const VERSION\s*=\s*)"[^"]*"', rf'\1"{version}"', text, count=1)
    if new != text:
        SW.write_text(new, encoding="utf-8")
    return version, new != text


def main():
    version, changed = stamp()
    print(f"sw.js: VERSION -> {version}" if changed
          else f"sw.js: версия уже актуальна ({version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
