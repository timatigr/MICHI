# -*- coding: utf-8 -*-
"""«Свиток истории» 物語 — растущая микро-история на изученном словаре (i+1).

USP «обучение через контекст»: вместо изолированных карточек ученик читает
связные предложения — но только из того, что уже выучил. Каждая глава
открывается, когда пройдены её уроки (`requires`), и собрана ТОЛЬКО из изученных
слов: содержательные токены — id слов из vocab_n5 (`WORD_BY_ID`), а «клей» —
частицы и знаки из `ALLOWED_LITERALS`. Принцип i+1 проверяется автоматически
(tests/test_story.py), как и для уроков лексики (registry.requires).

Это чистый контент: ни БД, ни SRS. Чтение — практика и нарративная награда за
прогресс («что дальше?»), а не тест.
"""
from .vocab_n5 import WORD_BY_ID

# «Клей» предложения: частицы, связки и пунктуация. Вся их кана знакома из курса
# хираганы, поэтому они читаемы с самого начала; содержательное — только ссылки
# на изученные слова (id). Инвариант-тест следит, чтобы литералы не выходили за
# этот набор (иначе в историю просочилось бы непройденное «слово»).
ALLOWED_LITERALS = {
    "は", "が", "を", "に", "で", "へ", "と", "も", "の", "や",
    "か", "ね", "よ", "、", "。", "…", "「", "」",
}

# Главы в порядке открытия. requires — id уроков лексики (см. vocab_n5.LESSONS);
# глава открывается, когда ВСЕ они пройдены. scenes[*].t — токены: id слова или
# литерал из ALLOWED_LITERALS; ru — перевод сцены.
CHAPTERS = [
    {
        "id": "ch1", "jp": "であい", "title": "Встреча",
        "requires": ["v01", "v02", "v03"],
        "scenes": [
            {"t": ["konnichiwa", "。"], "ru": "Здравствуйте."},
            {"t": ["watashi", "は", "gakusei", "desu", "。"], "ru": "Я студент."},
            {"t": ["anata", "は", "sensei", "desu", "か", "。"], "ru": "Вы учитель?"},
            {"t": ["hai", "、", "nihongo", "の", "sensei", "desu", "。"],
             "ru": "Да, я учитель японского."},
            {"t": ["arigatou", "。"], "ru": "Спасибо."},
        ],
    },
    {
        "id": "ch2", "jp": "すうじ", "title": "Числа и дни",
        "requires": ["v04", "v05", "v06"],
        "scenes": [
            {"t": ["kyou", "は", "getsuyoubi", "desu", "。"], "ru": "Сегодня понедельник."},
            {"t": ["ima", "、", "asa", "desu", "。"], "ru": "Сейчас утро."},
            {"t": ["ashita", "は", "kayoubi", "desu", "。"], "ru": "Завтра вторник."},
            {"t": ["ichi", "、", "ni_num", "、", "san_num", "。"], "ru": "Один, два, три."},
        ],
    },
    {
        "id": "ch3", "jp": "ごはん", "title": "За столом",
        "requires": ["v07", "v08", "v09"],
        "scenes": [
            {"t": ["gohan", "を", "taberu", "。"], "ru": "Ем рис."},
            {"t": ["mizu", "を", "nomu", "。"], "ru": "Пью воду."},
            {"t": ["oishii", "desu", "ね", "。"], "ru": "Вкусно, правда?"},
            {"t": ["arigatou", "。"], "ru": "Спасибо."},
        ],
    },
    {
        "id": "ch4", "jp": "うち", "title": "Дом",
        "requires": ["v10", "v11", "v12"],
        "scenes": [
            {"t": ["watashi", "の", "uchi", "desu", "。"], "ru": "Это мой дом."},
            {"t": ["heya", "に", "tsukue", "と", "isu", "。"], "ru": "В комнате стол и стул."},
            {"t": ["terebi", "を", "miru", "。"], "ru": "Смотрю телевизор."},
            {"t": ["yoru", "、", "neru", "。"], "ru": "Ночью сплю."},
        ],
    },
    {
        "id": "ch5", "jp": "あさ", "title": "Утро и день",
        "requires": ["v13", "v14"],
        "scenes": [
            {"t": ["asa", "、", "okiru", "。"], "ru": "Утром встаю."},
            {"t": ["nihongo", "を", "narau", "。"], "ru": "Учу японский."},
            {"t": ["sensei", "が", "oshieru", "。"], "ru": "Учитель объясняет."},
            {"t": ["yoru", "、", "uchi", "に", "kaeru", "。"], "ru": "Вечером возвращаюсь домой."},
        ],
    },
    {
        "id": "ch6", "jp": "たのしい", "title": "Какой день",
        "requires": ["v15", "v16"],
        "scenes": [
            {"t": ["kyou", "は", "atsui", "desu", "。"], "ru": "Сегодня жарко."},
            {"t": ["nihongo", "は", "muzukashii", "desu", "か", "。"], "ru": "Японский трудный?"},
            {"t": ["iie", "、", "yasashii", "desu", "。"], "ru": "Нет, лёгкий."},
            {"t": ["tomodachi", "は", "yasashii", "desu", "。"], "ru": "Друг добрый."},
        ],
    },
]

CHAPTER_BY_ID = {c["id"]: c for c in CHAPTERS}


def _token_kana(token):
    """Кана токена: для слова — его запись из словаря, для литерала — он сам."""
    word = WORD_BY_ID.get(token)
    return word["kana"] if word else token


def render_scene(scene):
    """Сцена для фронта: склеенная японская строка + чтение (= она же, всё каной)
    + перевод + текст для озвучки."""
    jp = "".join(_token_kana(t) for t in scene["t"])
    return {"jp": jp, "reading": jp, "ru": scene["ru"], "tts": jp}


def content_word_ids(chapter):
    """id слов (не литералов), использованных в главе — для инвариант-теста i+1."""
    ids = set()
    for scene in chapter["scenes"]:
        for t in scene["t"]:
            if t not in ALLOWED_LITERALS:
                ids.add(t)
    return ids


def chapters_for(completed):
    """Главы со статусом для набора пройденных уроков (completed — множество id
    уроков). Глава открыта, когда пройдены все её requires; сцены раскрываются
    только у открытых глав. Чистая функция — тонкий HTTP-эндпоинт зовёт её."""
    out = []
    for ch in CHAPTERS:
        unlocked = all(r in completed for r in ch["requires"])
        out.append({
            "id": ch["id"], "jp": ch["jp"], "title": ch["title"], "unlocked": unlocked,
            "scenes": [render_scene(s) for s in ch["scenes"]] if unlocked else [],
        })
    return out
