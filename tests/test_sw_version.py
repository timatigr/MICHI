# -*- coding: utf-8 -*-
"""Версия Service Worker привязана к хэшу оболочки (scripts/stamp_sw.py).

Тревога-инвариант: если кто-то правит оболочку (app.js/style.css/…), но забыл
перештамповать sw.js, версия SW разойдётся с содержимым → у пользователей после
деплоя залипнет старый JS. Тест ловит это в pytest (а значит и в precommit-хуке).
Чинится одной командой: `python scripts/stamp_sw.py`.
"""
import importlib.util
import pathlib
import re

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SW = _ROOT / "static" / "sw.js"


def _load_stamp():
    spec = importlib.util.spec_from_file_location(
        "stamp_sw", _ROOT / "scripts" / "stamp_sw.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_version_is_short_hex_and_deterministic():
    stamp = _load_stamp()
    text = _SW.read_text(encoding="utf-8")
    v = stamp.compute_version(text)
    assert re.fullmatch(r"[0-9a-f]{12}", v)              # 12 hex
    assert v == stamp.compute_version(text)              # детерминирован


def test_committed_sw_is_stamped():
    """Закоммиченный sw.js должен быть уже заштампован под текущую оболочку."""
    stamp = _load_stamp()
    text = _SW.read_text(encoding="utf-8")
    declared = re.search(r'const VERSION\s*=\s*"([^"]*)"', text).group(1)
    assert declared == stamp.compute_version(text), (
        "sw.js не заштампован под текущую оболочку — выполните "
        "`python scripts/stamp_sw.py` и закоммитьте sw.js")
