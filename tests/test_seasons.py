# -*- coding: utf-8 -*-
"""Письма сезонов 二十四節気: датасет и определение текущего сезона по дате."""
import datetime

from app.content.seasons import SEKKI, current_sekki


def test_sekki_dataset_shape():
    for s in SEKKI:
        assert s["kanji"] and s["reading"] and s["ru"] and s["emoji"]
        assert isinstance(s["start"], tuple) and len(s["start"]) == 2
    assert SEKKI == sorted(SEKKI, key=lambda s: s["start"])   # по календарю
    assert len({s["kanji"] for s in SEKKI}) == 24             # 24 разных сезона


def test_current_sekki_boundaries():
    d = datetime.date
    assert current_sekki(d(2026, 6, 21))["kanji"] == "夏至"   # ровно на старте
    assert current_sekki(d(2026, 6, 26))["kanji"] == "夏至"   # внутри сезона
    assert current_sekki(d(2026, 7, 7))["kanji"] == "小暑"    # следующий
    assert current_sekki(d(2026, 1, 1))["kanji"] == "冬至"    # до 小寒 — ещё прошлогодний
    assert current_sekki(d(2026, 1, 6))["kanji"] == "小寒"
    assert current_sekki(d(2026, 3, 21))["kanji"] == "春分"
    assert current_sekki(d(2026, 12, 31))["kanji"] == "冬至"


def test_current_sekki_covers_all_days():
    days = (datetime.date(2026, 1, 1) + datetime.timedelta(n) for n in range(365))
    got = {current_sekki(d)["kanji"] for d in days}
    assert got == {s["kanji"] for s in SEKKI}                 # каждый сезон выпадает
