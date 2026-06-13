# -*- coding: utf-8 -*-
"""Лексика N5 (SRS.md, разделы 2.5 и 3.1).

Слово -> две раздельные SRS-карточки с независимыми интервалами:
vocab_jp_ru (распознавание) и vocab_ru_jp (воспроизведение).

Слова записаны каной (хирагана + катакана для гайрайго). Кандзи-написание
появится отдельным навыком в курсе кандзи; здесь слово учится «на слух и
в чтении каной». Урок открывается, только когда изучена вся его кана
(принцип i+1, проверяется в registry через requires).
"""

# Тематические юниты (раздел 3.1). Каждый — 3 микроурока по ~10 слов.
UNITS = {
    1: "Знакомство",
    2: "Числа и время",
    3: "Еда и напитки",
    4: "Дом и быт",
}

WORDS = [
    # ======================= ЮНИТ 1 — Знакомство =======================
    # --- v01: приветствия и вежливость ---
    {"id": "konnichiwa",   "kana": "こんにちは",     "romaji": "konnichiwa",    "ru": "здравствуйте, добрый день"},
    {"id": "ohayou",       "kana": "おはよう",       "romaji": "ohayou",        "ru": "доброе утро",
     "note": "Вежливо: おはようございます (коллегам, старшим)."},
    {"id": "konbanwa",     "kana": "こんばんは",     "romaji": "konbanwa",      "ru": "добрый вечер"},
    {"id": "oyasumi",      "kana": "おやすみなさい",  "romaji": "oyasuminasai",  "ru": "спокойной ночи"},
    {"id": "sayounara",    "kana": "さようなら",     "romaji": "sayounara",     "ru": "до свидания"},
    {"id": "jaane",        "kana": "じゃあね",       "romaji": "jaane",         "ru": "пока! (неформально)"},
    {"id": "arigatou",     "kana": "ありがとう",     "romaji": "arigatou",      "ru": "спасибо",
     "note": "Вежливо: ありがとうございます."},
    {"id": "sumimasen",    "kana": "すみません",     "romaji": "sumimasen",     "ru": "извините; простите",
     "note": "Универсальное слово: извинение, «спасибо за хлопоты» и оклик официанта."},
    {"id": "hai",          "kana": "はい",          "romaji": "hai",           "ru": "да"},
    {"id": "iie",          "kana": "いいえ",         "romaji": "iie",           "ru": "нет"},
    # --- v02: я и люди вокруг ---
    {"id": "watashi",      "kana": "わたし",         "romaji": "watashi",       "ru": "я"},
    {"id": "anata",        "kana": "あなた",         "romaji": "anata",         "ru": "ты, вы",
     "note": "Японцы чаще обращаются по имени; あなた звучит подчёркнуто прямо."},
    {"id": "hito",         "kana": "ひと",          "romaji": "hito",          "ru": "человек"},
    {"id": "tomodachi",    "kana": "ともだち",       "romaji": "tomodachi",     "ru": "друг"},
    {"id": "sensei",       "kana": "せんせい",       "romaji": "sensei",        "ru": "учитель"},
    {"id": "gakusei",      "kana": "がくせい",       "romaji": "gakusei",       "ru": "студент, учащийся"},
    {"id": "namae",        "kana": "なまえ",         "romaji": "namae",         "ru": "имя"},
    {"id": "nihongo",      "kana": "にほんご",       "romaji": "nihongo",       "ru": "японский язык"},
    {"id": "dare",         "kana": "だれ",          "romaji": "dare",          "ru": "кто"},
    {"id": "minna",        "kana": "みんな",         "romaji": "minna",         "ru": "все, все вместе"},
    # --- v03: первые фразы ---
    {"id": "desu",         "kana": "です",          "romaji": "desu",          "ru": "есть, является (связка)",
     "note": "わたしは がくせい です — «я студент». Вежливая связка в конце фразы."},
    {"id": "wakarimasu",   "kana": "わかります",     "romaji": "wakarimasu",    "ru": "понимаю"},
    {"id": "wakarimasen",  "kana": "わかりません",    "romaji": "wakarimasen",   "ru": "не понимаю"},
    {"id": "onegaishimasu", "kana": "おねがいします", "romaji": "onegaishimasu", "ru": "пожалуйста (прошу)"},
    {"id": "douzo",        "kana": "どうぞ",         "romaji": "douzo",         "ru": "пожалуйста (вот, прошу)",
     "note": "Когда что-то предлагаете или передаёте: «прошу, вот»."},
    {"id": "doumo",        "kana": "どうも",         "romaji": "doumo",         "ru": "спасибо; весьма (разг.)"},
    {"id": "genki",        "kana": "げんき",         "romaji": "genki",         "ru": "бодрый, здоровый",
     "note": "おげんきですか — «как дела / как здоровье?»"},
    {"id": "suki",         "kana": "すき",          "romaji": "suki",          "ru": "нравится, любимый"},
    {"id": "ii",           "kana": "いい",          "romaji": "ii",            "ru": "хороший"},
    {"id": "daijoubu",     "kana": "だいじょうぶ",    "romaji": "daijoubu",      "ru": "всё в порядке, нормально"},

    # ======================= ЮНИТ 2 — Числа и время =======================
    # --- v04: числа 1–10 ---
    {"id": "ichi",         "kana": "いち",          "romaji": "ichi",          "ru": "один (1)"},
    {"id": "ni_num",       "kana": "に",            "romaji": "ni",            "ru": "два (2)"},
    {"id": "san_num",      "kana": "さん",          "romaji": "san",           "ru": "три (3)"},
    {"id": "yon",          "kana": "よん",          "romaji": "yon",           "ru": "четыре (4)",
     "note": "Второе чтение — し (shi); счёт людей/часов чаще через よん/し по-разному."},
    {"id": "go_num",       "kana": "ご",            "romaji": "go",            "ru": "пять (5)"},
    {"id": "roku",         "kana": "ろく",          "romaji": "roku",          "ru": "шесть (6)"},
    {"id": "nana",         "kana": "なな",          "romaji": "nana",          "ru": "семь (7)",
     "note": "Второе чтение — しち (shichi)."},
    {"id": "hachi",        "kana": "はち",          "romaji": "hachi",         "ru": "восемь (8)"},
    {"id": "kyuu",         "kana": "きゅう",         "romaji": "kyuu",          "ru": "девять (9)",
     "note": "Второе чтение — く (ku)."},
    {"id": "juu",          "kana": "じゅう",         "romaji": "juu",           "ru": "десять (10)"},
    # --- v05: части суток и счёт времени ---
    {"id": "ima",          "kana": "いま",          "romaji": "ima",           "ru": "сейчас"},
    {"id": "kyou",         "kana": "きょう",         "romaji": "kyou",          "ru": "сегодня"},
    {"id": "ashita",       "kana": "あした",         "romaji": "ashita",        "ru": "завтра"},
    {"id": "kinou",        "kana": "きのう",         "romaji": "kinou",         "ru": "вчера"},
    {"id": "asa",          "kana": "あさ",          "romaji": "asa",           "ru": "утро"},
    {"id": "hiru",         "kana": "ひる",          "romaji": "hiru",          "ru": "полдень, день"},
    {"id": "yoru",         "kana": "よる",          "romaji": "yoru",          "ru": "ночь, вечер"},
    {"id": "nanji",        "kana": "なんじ",         "romaji": "nanji",         "ru": "который час",
     "note": "いま なんじ ですか — «сколько сейчас времени?»"},
    {"id": "jikan",        "kana": "じかん",         "romaji": "jikan",         "ru": "время; час (длительность)"},
    # --- v06: дни недели ---
    {"id": "nichiyoubi",   "kana": "にちようび",      "romaji": "nichiyoubi",    "ru": "воскресенье"},
    {"id": "getsuyoubi",   "kana": "げつようび",      "romaji": "getsuyoubi",    "ru": "понедельник"},
    {"id": "kayoubi",      "kana": "かようび",       "romaji": "kayoubi",       "ru": "вторник"},
    {"id": "suiyoubi",     "kana": "すいようび",      "romaji": "suiyoubi",      "ru": "среда"},
    {"id": "mokuyoubi",    "kana": "もくようび",      "romaji": "mokuyoubi",     "ru": "четверг"},
    {"id": "kinyoubi",     "kana": "きんようび",      "romaji": "kinyoubi",      "ru": "пятница"},
    {"id": "doyoubi",      "kana": "どようび",       "romaji": "doyoubi",       "ru": "суббота"},
    {"id": "mainichi",     "kana": "まいにち",       "romaji": "mainichi",      "ru": "каждый день"},
    {"id": "shuumatsu",    "kana": "しゅうまつ",      "romaji": "shuumatsu",     "ru": "выходные, конец недели"},

    # ======================= ЮНИТ 3 — Еда и напитки =======================
    # --- v07: еда ---
    {"id": "gohan",        "kana": "ごはん",         "romaji": "gohan",         "ru": "варёный рис; еда"},
    {"id": "pan",          "kana": "パン",          "romaji": "pan",           "ru": "хлеб",
     "note": "Гайрайго (от порт. pão) — поэтому катаканой."},
    {"id": "niku",         "kana": "にく",          "romaji": "niku",          "ru": "мясо"},
    {"id": "sakana",       "kana": "さかな",         "romaji": "sakana",        "ru": "рыба"},
    {"id": "tamago",       "kana": "たまご",         "romaji": "tamago",        "ru": "яйцо"},
    {"id": "yasai",        "kana": "やさい",         "romaji": "yasai",         "ru": "овощи"},
    {"id": "kudamono",     "kana": "くだもの",       "romaji": "kudamono",      "ru": "фрукты"},
    {"id": "onigiri",      "kana": "おにぎり",       "romaji": "onigiri",       "ru": "онигири (рисовый колобок)"},
    {"id": "okashi",       "kana": "おかし",         "romaji": "okashi",        "ru": "сладости, закуски"},
    # --- v08: напитки ---
    {"id": "mizu",         "kana": "みず",          "romaji": "mizu",          "ru": "вода"},
    {"id": "ocha",         "kana": "おちゃ",         "romaji": "ocha",          "ru": "чай (зелёный)"},
    {"id": "koohii",       "kana": "コーヒー",       "romaji": "koohii",        "ru": "кофе",
     "note": "Долгота в гайрайго пишется чертой ー: コーヒー."},
    {"id": "gyuunyuu",     "kana": "ぎゅうにゅう",    "romaji": "gyuunyuu",      "ru": "молоко"},
    {"id": "juusu",        "kana": "ジュース",       "romaji": "juusu",         "ru": "сок"},
    {"id": "osake",        "kana": "おさけ",         "romaji": "osake",         "ru": "сакэ; алкоголь"},
    {"id": "biiru",        "kana": "ビール",         "romaji": "biiru",         "ru": "пиво"},
    {"id": "nomimono",     "kana": "のみもの",       "romaji": "nomimono",      "ru": "напиток"},
    # --- v09: за столом ---
    {"id": "taberu",       "kana": "たべる",         "romaji": "taberu",        "ru": "есть, кушать"},
    {"id": "nomu",         "kana": "のむ",          "romaji": "nomu",          "ru": "пить"},
    {"id": "oishii",       "kana": "おいしい",       "romaji": "oishii",        "ru": "вкусный"},
    {"id": "amai",         "kana": "あまい",         "romaji": "amai",          "ru": "сладкий"},
    {"id": "karai",        "kana": "からい",         "romaji": "karai",         "ru": "острый; солёный"},
    {"id": "resutoran",    "kana": "レストラン",      "romaji": "resutoran",     "ru": "ресторан"},
    {"id": "menyuu",       "kana": "メニュー",       "romaji": "menyuu",        "ru": "меню"},
    {"id": "itadakimasu",  "kana": "いただきます",    "romaji": "itadakimasu",   "ru": "«итадакимас» (перед едой)",
     "note": "Говорят перед едой — «приступаю», благодарность за пищу."},
    {"id": "gochisousama", "kana": "ごちそうさま",    "romaji": "gochisousama",  "ru": "«готисосама» (после еды)",
     "note": "После еды — «спасибо, было вкусно»."},

    # ======================= ЮНИТ 4 — Дом и быт =======================
    # --- v10: дом ---
    {"id": "uchi",         "kana": "うち",          "romaji": "uchi",          "ru": "дом, жильё; «у нас»"},
    {"id": "heya",         "kana": "へや",          "romaji": "heya",          "ru": "комната"},
    {"id": "daidokoro",    "kana": "だいどころ",      "romaji": "daidokoro",     "ru": "кухня"},
    {"id": "toire",        "kana": "トイレ",         "romaji": "toire",         "ru": "туалет"},
    {"id": "ofuro",        "kana": "おふろ",         "romaji": "ofuro",         "ru": "ванна (японская)"},
    {"id": "mado",         "kana": "まど",          "romaji": "mado",          "ru": "окно"},
    {"id": "doa",          "kana": "ドア",          "romaji": "doa",           "ru": "дверь (европейская)"},
    {"id": "isu",          "kana": "いす",          "romaji": "isu",           "ru": "стул"},
    {"id": "tsukue",       "kana": "つくえ",         "romaji": "tsukue",        "ru": "стол (письменный)"},
    # --- v11: вещи ---
    {"id": "hon",          "kana": "ほん",          "romaji": "hon",           "ru": "книга"},
    {"id": "kaban",        "kana": "かばん",         "romaji": "kaban",         "ru": "сумка, портфель"},
    {"id": "tokei",        "kana": "とけい",         "romaji": "tokei",         "ru": "часы"},
    {"id": "denwa",        "kana": "でんわ",         "romaji": "denwa",         "ru": "телефон"},
    {"id": "terebi",       "kana": "テレビ",         "romaji": "terebi",        "ru": "телевизор",
     "note": "Сокращение от テレビジョン (television)."},
    {"id": "pasokon",      "kana": "パソコン",       "romaji": "pasokon",       "ru": "компьютер (ПК)",
     "note": "От パーソナル・コンピューター — «персональный компьютер»."},
    {"id": "kasa",         "kana": "かさ",          "romaji": "kasa",          "ru": "зонт"},
    {"id": "kagi",         "kana": "かぎ",          "romaji": "kagi",          "ru": "ключ; замок"},
    {"id": "kami",         "kana": "かみ",          "romaji": "kami",          "ru": "бумага"},
    # --- v12: каждый день (глаголы) ---
    {"id": "iku",          "kana": "いく",          "romaji": "iku",           "ru": "идти, ехать"},
    {"id": "kuru",         "kana": "くる",          "romaji": "kuru",          "ru": "приходить"},
    {"id": "miru",         "kana": "みる",          "romaji": "miru",          "ru": "смотреть, видеть"},
    {"id": "kiku",         "kana": "きく",          "romaji": "kiku",          "ru": "слушать; спрашивать"},
    {"id": "yomu",         "kana": "よむ",          "romaji": "yomu",          "ru": "читать"},
    {"id": "kaku",         "kana": "かく",          "romaji": "kaku",          "ru": "писать; рисовать"},
    {"id": "suru",         "kana": "する",          "romaji": "suru",          "ru": "делать"},
    {"id": "neru",         "kana": "ねる",          "romaji": "neru",          "ru": "спать, ложиться"},
    {"id": "okiru",        "kana": "おきる",         "romaji": "okiru",         "ru": "вставать, просыпаться"},
]

WORD_BY_ID = {w["id"]: w for w in WORDS}

LESSONS = [
    # --- Юнит 1 — Знакомство ---
    {"id": "v01", "type": "vocab", "unit": 1, "title": "Приветствия", "subtitle": "10 слов", "icon": "挨",
     "words": ["konnichiwa", "ohayou", "konbanwa", "oyasumi", "sayounara",
               "jaane", "arigatou", "sumimasen", "hai", "iie"],
     "intro": "Первые настоящие слова! Все они записаны хираганой, которую вы уже знаете. "
              "Каждое слово станет двумя SRS-карточками: «узнать перевод» и «вспомнить японский»."},
    {"id": "v02", "type": "vocab", "unit": 1, "title": "Я и люди", "subtitle": "10 слов", "icon": "人",
     "words": ["watashi", "anata", "hito", "tomodachi", "sensei",
               "gakusei", "namae", "nihongo", "dare", "minna"],
     "intro": "Слова про себя и окружающих. Многие вы уже встречали в уроках каны — теперь они войдут в ваш активный словарь."},
    {"id": "v03", "type": "vocab", "unit": 1, "title": "Первые фразы", "subtitle": "10 слов", "icon": "話",
     "words": ["desu", "wakarimasu", "wakarimasen", "onegaishimasu", "douzo",
               "doumo", "genki", "suki", "ii", "daijoubu"],
     "intro": "Связка です, «понимаю/не понимаю» и вежливые слова — этого уже хватит на первый мини-диалог."},

    # --- Юнит 2 — Числа и время ---
    {"id": "v04", "type": "vocab", "unit": 2, "title": "Числа 1–10", "subtitle": "10 слов", "icon": "数",
     "words": ["ichi", "ni_num", "san_num", "yon", "go_num",
               "roku", "nana", "hachi", "kyuu", "juu"],
     "intro": "Основа счёта. У 4, 7 и 9 по два чтения — сначала запомните основное (よん, なな, きゅう), "
              "второе встретите в датах и времени."},
    {"id": "v05", "type": "vocab", "unit": 2, "title": "Время суток", "subtitle": "9 слов", "icon": "時",
     "words": ["ima", "kyou", "ashita", "kinou", "asa",
               "hiru", "yoru", "nanji", "jikan"],
     "intro": "«Сейчас», «сегодня/завтра/вчера» и части суток. С вопросом なんじ можно спросить время."},
    {"id": "v06", "type": "vocab", "unit": 2, "title": "Дни недели", "subtitle": "9 слов", "icon": "曜",
     "words": ["nichiyoubi", "getsuyoubi", "kayoubi", "suiyoubi", "mokuyoubi",
               "kinyoubi", "doyoubi", "mainichi", "shuumatsu"],
     "intro": "Семь дней недели оканчиваются на ようび. Первый слог — стихия: 月 луна, 火 огонь, 水 вода… "
              "пока учим на слух, кандзи придут позже."},

    # --- Юнит 3 — Еда и напитки ---
    {"id": "v07", "type": "vocab", "unit": 3, "title": "Еда", "subtitle": "9 слов", "icon": "食",
     "words": ["gohan", "pan", "niku", "sakana", "tamago",
               "yasai", "kudamono", "onigiri", "okashi"],
     "intro": "Базовая еда. パン — первое слово катаканой: заимствования всегда пишутся ей."},
    {"id": "v08", "type": "vocab", "unit": 3, "title": "Напитки", "subtitle": "8 слов", "icon": "飲",
     "words": ["mizu", "ocha", "koohii", "gyuunyuu", "juusu",
               "osake", "biiru", "nomimono"],
     "intro": "Что пьют в Японии. Половина — гайрайго катаканой: コーヒー, ジュース, ビール."},
    {"id": "v09", "type": "vocab", "unit": 3, "title": "За столом", "subtitle": "9 слов", "icon": "味",
     "words": ["taberu", "nomu", "oishii", "amai", "karai",
               "resutoran", "menyuu", "itadakimasu", "gochisousama"],
     "intro": "Глаголы «есть/пить», вкусы и две застольные фразы — いただきます перед едой и ごちそうさま после."},

    # --- Юнит 4 — Дом и быт ---
    {"id": "v10", "type": "vocab", "unit": 4, "title": "Дом", "subtitle": "9 слов", "icon": "家",
     "words": ["uchi", "heya", "daidokoro", "toire", "ofuro",
               "mado", "doa", "isu", "tsukue"],
     "intro": "Комнаты и обстановка. トイレ и ドア — гайрайго; おふろ — японская ванна для отмокания, не для мытья."},
    {"id": "v11", "type": "vocab", "unit": 4, "title": "Вещи", "subtitle": "9 слов", "icon": "物",
     "words": ["hon", "kaban", "tokei", "denwa", "terebi",
               "pasokon", "kasa", "kagi", "kami"],
     "intro": "Повседневные предметы. テレビ и パソコン — сокращённые заимствования, очень частотные."},
    {"id": "v12", "type": "vocab", "unit": 4, "title": "Каждый день", "subtitle": "9 слов", "icon": "動",
     "words": ["iku", "kuru", "miru", "kiku", "yomu",
               "kaku", "suru", "neru", "okiru"],
     "intro": "Первые глаголы действий в словарной форме. Дальше они спрягаются в ます-форму: たべる→たべます."},
]
