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
    5: "Повседневные глаголы",
    6: "Прилагательные",
    7: "Время и календарь",
    8: "Места и город",
    9: "Транспорт и движение",
    10: "Семья",
    11: "Природа и погода",
    12: "Тело и здоровье",
    13: "Цвета",
    14: "Вопросы и наречия",
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

    # ======================= ЮНИТ 5 — Повседневные глаголы =======================
    # Стиль: словарная форма (じしょけい) каной — как у глаголов в v09/v12.
    # В речи спрягается в вежливую ます-форму: かう→かいます, はなす→はなします.
    # --- v13: действия и движение ---
    {"id": "kau",          "kana": "かう",          "romaji": "kau",           "ru": "покупать",
     "note": "Словарная форма. Вежливо: かいます."},
    {"id": "uru",          "kana": "うる",          "romaji": "uru",           "ru": "продавать",
     "note": "Словарная форма. Вежливо: うります."},
    {"id": "kaeru",        "kana": "かえる",         "romaji": "kaeru",         "ru": "возвращаться (домой)",
     "note": "Словарная форма. Вежливо: かえります."},
    {"id": "aruku",        "kana": "あるく",         "romaji": "aruku",         "ru": "идти пешком, гулять",
     "note": "Словарная форма. Вежливо: あるきます."},
    {"id": "hashiru",      "kana": "はしる",         "romaji": "hashiru",       "ru": "бежать, бегать",
     "note": "Словарная форма. Вежливо: はしります."},
    {"id": "tatsu",        "kana": "たつ",          "romaji": "tatsu",         "ru": "вставать, стоять",
     "note": "Словарная форма. Вежливо: たちます."},
    {"id": "suwaru",       "kana": "すわる",         "romaji": "suwaru",        "ru": "садиться, сидеть",
     "note": "Словарная форма. Вежливо: すわります."},
    {"id": "matsu",        "kana": "まつ",          "romaji": "matsu",         "ru": "ждать",
     "note": "Словарная форма. Вежливо: まちます."},
    {"id": "au",           "kana": "あう",          "romaji": "au",            "ru": "встречаться, видеться",
     "note": "Словарная форма. Вежливо: あいます. Управляет частицей に."},
    {"id": "asobu",        "kana": "あそぶ",         "romaji": "asobu",         "ru": "играть, развлекаться",
     "note": "Словарная форма. Вежливо: あそびます."},
    # --- v14: общение и быт ---
    {"id": "hanasu",       "kana": "はなす",         "romaji": "hanasu",        "ru": "говорить, разговаривать",
     "note": "Словарная форма. Вежливо: はなします."},
    {"id": "iu",           "kana": "いう",          "romaji": "iu",            "ru": "сказать, говорить",
     "note": "Словарная форма. Вежливо: いいます. Читается «иу»."},
    {"id": "narau",        "kana": "ならう",         "romaji": "narau",         "ru": "учиться (чему-л.), осваивать",
     "note": "Словарная форма. Вежливо: ならいます."},
    {"id": "oshieru",      "kana": "おしえる",       "romaji": "oshieru",       "ru": "учить, объяснять",
     "note": "Словарная форма. Вежливо: おしえます."},
    {"id": "tsukau",       "kana": "つかう",         "romaji": "tsukau",        "ru": "пользоваться, использовать",
     "note": "Словарная форма. Вежливо: つかいます."},
    {"id": "tsukuru",      "kana": "つくる",         "romaji": "tsukuru",       "ru": "делать, создавать, готовить",
     "note": "Словарная форма. Вежливо: つくります."},
    {"id": "wasureru",     "kana": "わすれる",       "romaji": "wasureru",      "ru": "забывать",
     "note": "Словарная форма. Вежливо: わすれます."},
    {"id": "oboeru",       "kana": "おぼえる",       "romaji": "oboeru",        "ru": "запоминать, помнить",
     "note": "Словарная форма. Вежливо: おぼえます."},
    {"id": "yasumu",       "kana": "やすむ",         "romaji": "yasumu",        "ru": "отдыхать; брать выходной",
     "note": "Словарная форма. Вежливо: やすみます."},
    {"id": "hataraku",     "kana": "はたらく",       "romaji": "hataraku",      "ru": "работать",
     "note": "Словарная форма. Вежливо: はたらきます."},

    # ======================= ЮНИТ 6 — Прилагательные =======================
    # Тип помечен в note: «い-прил.» меняет хвост (おおきい→おおきくない),
    # «な-прил.» присоединяется через な (きれいな はな) и работает как существительное.
    # --- v15: размер и оценка (い-прилагательные) ---
    {"id": "ookii",        "kana": "おおきい",       "romaji": "ookii",         "ru": "большой",
     "note": "い-прил. Отрицание: おおきくない."},
    {"id": "chiisai",      "kana": "ちいさい",       "romaji": "chiisai",       "ru": "маленький",
     "note": "い-прил."},
    {"id": "takai",        "kana": "たかい",         "romaji": "takai",         "ru": "высокий; дорогой",
     "note": "い-прил. Два значения: «высокий» и «дорогой»."},
    {"id": "yasui",        "kana": "やすい",         "romaji": "yasui",         "ru": "дешёвый",
     "note": "い-прил. Не путать с глаголом やすむ «отдыхать»."},
    {"id": "atarashii",    "kana": "あたらしい",      "romaji": "atarashii",     "ru": "новый",
     "note": "い-прил."},
    {"id": "furui",        "kana": "ふるい",         "romaji": "furui",         "ru": "старый (о вещах)",
     "note": "い-прил. О людях «старый» — としうえ/とし, не ふるい."},
    {"id": "nagai",        "kana": "ながい",         "romaji": "nagai",         "ru": "длинный, долгий",
     "note": "い-прил."},
    {"id": "mijikai",      "kana": "みじかい",       "romaji": "mijikai",       "ru": "короткий",
     "note": "い-прил."},
    {"id": "ii_adj",       "kana": "いい",          "romaji": "ii",            "ru": "хороший",
     "note": "い-прил. Отрицание нестандартное: よくない (от よい)."},
    {"id": "warui",        "kana": "わるい",         "romaji": "warui",         "ru": "плохой",
     "note": "い-прил."},
    # --- v16: ощущения и характер ---
    {"id": "atsui",        "kana": "あつい",         "romaji": "atsui",         "ru": "жаркий, горячий",
     "note": "い-прил."},
    {"id": "samui",        "kana": "さむい",         "romaji": "samui",         "ru": "холодный (о погоде)",
     "note": "い-прил. О предметах «холодный» — つめたい."},
    {"id": "tanoshii",     "kana": "たのしい",       "romaji": "tanoshii",      "ru": "весёлый, приятный",
     "note": "い-прил."},
    {"id": "muzukashii",   "kana": "むずかしい",      "romaji": "muzukashii",    "ru": "трудный, сложный",
     "note": "い-прил."},
    {"id": "yasashii",     "kana": "やさしい",       "romaji": "yasashii",      "ru": "лёгкий; добрый",
     "note": "い-прил. Два значения: «простой» и «добрый»."},
    {"id": "isogashii",    "kana": "いそがしい",      "romaji": "isogashii",     "ru": "занятой",
     "note": "い-прил."},
    {"id": "kirei",        "kana": "きれい",         "romaji": "kirei",         "ru": "красивый; чистый",
     "note": "な-прил. Перед существительным: きれいな はな. Несмотря на хвост -い, это な-тип."},
    {"id": "shizuka",      "kana": "しずか",         "romaji": "shizuka",       "ru": "тихий, спокойный",
     "note": "な-прил. Перед существительным: しずかな へや."},
    {"id": "yuumei",       "kana": "ゆうめい",       "romaji": "yuumei",        "ru": "известный, знаменитый",
     "note": "な-прил. Перед существительным: ゆうめいな ひと."},
    {"id": "benri",        "kana": "べんり",         "romaji": "benri",         "ru": "удобный",
     "note": "な-прил. Перед существительным: べんりな アプリ."},

    # ======================= ЮНИТ 7 — Время и календарь =======================
    # --- v17: месяцы и календарь ---
    {"id": "kotoshi",      "kana": "ことし",         "romaji": "kotoshi",       "ru": "этот год"},
    {"id": "raishuu",      "kana": "らいしゅう",      "romaji": "raishuu",       "ru": "следующая неделя"},
    {"id": "senshuu",      "kana": "せんしゅう",      "romaji": "senshuu",       "ru": "прошлая неделя"},
    {"id": "kongetsu",     "kana": "こんげつ",       "romaji": "kongetsu",      "ru": "этот месяц"},
    {"id": "raigetsu",     "kana": "らいげつ",       "romaji": "raigetsu",      "ru": "следующий месяц"},
    {"id": "gogo",         "kana": "ごご",          "romaji": "gogo",          "ru": "после полудня, p.m."},
    {"id": "gozen",        "kana": "ごぜん",         "romaji": "gozen",         "ru": "до полудня, a.m."},
    {"id": "han_time",     "kana": "はん",          "romaji": "han",           "ru": "половина (часа)",
     "note": "にじはん — «полтретьего», букв. «два часа с половиной»."},
    {"id": "fun_min",      "kana": "ふん",          "romaji": "fun",           "ru": "минута (счётный суффикс)",
     "note": "ごふん — пять минут; чередуется с ぷん: いっぷん, さんぷん."},
    {"id": "tanjoubi",     "kana": "たんじょうび",    "romaji": "tanjoubi",      "ru": "день рождения"},

    # ======================= ЮНИТ 8 — Места и город =======================
    # --- v18: места в городе ---
    {"id": "eki",          "kana": "えき",          "romaji": "eki",           "ru": "станция (вокзал)"},
    {"id": "mise",         "kana": "みせ",          "romaji": "mise",          "ru": "магазин, лавка"},
    {"id": "ginkou",       "kana": "ぎんこう",       "romaji": "ginkou",        "ru": "банк"},
    {"id": "byouin",       "kana": "びょういん",      "romaji": "byouin",        "ru": "больница"},
    {"id": "gakkou",       "kana": "がっこう",       "romaji": "gakkou",        "ru": "школа"},
    {"id": "kouen",        "kana": "こうえん",       "romaji": "kouen",         "ru": "парк"},
    {"id": "toshokan",     "kana": "としょかん",      "romaji": "toshokan",      "ru": "библиотека"},
    {"id": "yuubinkyoku",  "kana": "ゆうびんきょく",   "romaji": "yuubinkyoku",   "ru": "почта"},
    {"id": "depaato",      "kana": "デパート",       "romaji": "depaato",       "ru": "универмаг",
     "note": "Гайрайго от department store."},
    {"id": "machi",        "kana": "まち",          "romaji": "machi",         "ru": "город, городок; улица"},

    # ======================= ЮНИТ 9 — Транспорт и движение =======================
    # --- v19: транспорт ---
    {"id": "densha",       "kana": "でんしゃ",       "romaji": "densha",        "ru": "электричка, поезд"},
    {"id": "basu",         "kana": "バス",          "romaji": "basu",          "ru": "автобус",
     "note": "Гайрайго от bus."},
    {"id": "kuruma",       "kana": "くるま",         "romaji": "kuruma",        "ru": "машина, автомобиль"},
    {"id": "hikouki",      "kana": "ひこうき",       "romaji": "hikouki",       "ru": "самолёт"},
    {"id": "jitensha",     "kana": "じてんしゃ",      "romaji": "jitensha",      "ru": "велосипед"},
    {"id": "chikatetsu",   "kana": "ちかてつ",       "romaji": "chikatetsu",    "ru": "метро"},
    {"id": "takushii",     "kana": "タクシー",       "romaji": "takushii",      "ru": "такси",
     "note": "Гайрайго от taxi."},
    {"id": "michi",        "kana": "みち",          "romaji": "michi",         "ru": "дорога, путь"},
    {"id": "noru",         "kana": "のる",          "romaji": "noru",          "ru": "садиться (в транспорт), ехать",
     "note": "Словарная форма. Вежливо: のります. Управляет частицей に: バスに のる."},
    {"id": "oriru",        "kana": "おりる",         "romaji": "oriru",         "ru": "сходить, выходить (из транспорта)",
     "note": "Словарная форма. Вежливо: おります."},

    # ======================= ЮНИТ 10 — Семья =======================
    # --- v20: моя семья и чужая ---
    {"id": "kazoku",       "kana": "かぞく",         "romaji": "kazoku",        "ru": "семья"},
    {"id": "otousan",      "kana": "おとうさん",      "romaji": "otousan",       "ru": "отец (чужой/вежливо)",
     "note": "О своём отце говорят ちち."},
    {"id": "okaasan",      "kana": "おかあさん",      "romaji": "okaasan",       "ru": "мать (чужая/вежливо)",
     "note": "О своей матери говорят はは."},
    {"id": "ani",          "kana": "あに",          "romaji": "ani",           "ru": "старший брат (свой)",
     "note": "Чужой старший брат — おにいさん."},
    {"id": "ane",          "kana": "あね",          "romaji": "ane",           "ru": "старшая сестра (своя)",
     "note": "Чужая старшая сестра — おねえさん."},
    {"id": "otouto",       "kana": "おとうと",       "romaji": "otouto",        "ru": "младший брат"},
    {"id": "imouto",       "kana": "いもうと",       "romaji": "imouto",        "ru": "младшая сестра"},
    {"id": "kodomo",       "kana": "こども",         "romaji": "kodomo",        "ru": "ребёнок, дети"},
    {"id": "kyoudai",      "kana": "きょうだい",      "romaji": "kyoudai",       "ru": "братья и сёстры"},
    {"id": "otoko",        "kana": "おとこ",         "romaji": "otoko",         "ru": "мужчина",
     "note": "おんな — женщина. おとこのこ — мальчик."},

    # ======================= ЮНИТ 11 — Природа и погода =======================
    # --- v21: погода и природа ---
    {"id": "tenki",        "kana": "てんき",         "romaji": "tenki",         "ru": "погода",
     "note": "いいてんき — «хорошая погода»."},
    {"id": "ame",          "kana": "あめ",          "romaji": "ame",           "ru": "дождь"},
    {"id": "yuki",         "kana": "ゆき",          "romaji": "yuki",          "ru": "снег"},
    {"id": "kaze",         "kana": "かぜ",          "romaji": "kaze",          "ru": "ветер",
     "note": "Тем же словом かぜ называют простуду."},
    {"id": "yama",         "kana": "やま",          "romaji": "yama",          "ru": "гора"},
    {"id": "kawa",         "kana": "かわ",          "romaji": "kawa",          "ru": "река"},
    {"id": "umi",          "kana": "うみ",          "romaji": "umi",           "ru": "море"},
    {"id": "sora",         "kana": "そら",          "romaji": "sora",          "ru": "небо"},
    {"id": "ki_tree",      "kana": "き",            "romaji": "ki",            "ru": "дерево"},
    {"id": "hana",         "kana": "はな",          "romaji": "hana",          "ru": "цветок"},

    # ======================= ЮНИТ 12 — Тело и здоровье =======================
    # --- v22: тело и самочувствие ---
    {"id": "atama",        "kana": "あたま",         "romaji": "atama",         "ru": "голова"},
    {"id": "kao",          "kana": "かお",          "romaji": "kao",           "ru": "лицо"},
    {"id": "me_eye",       "kana": "め",            "romaji": "me",            "ru": "глаз"},
    {"id": "mimi",         "kana": "みみ",          "romaji": "mimi",          "ru": "ухо"},
    {"id": "kuchi",        "kana": "くち",          "romaji": "kuchi",         "ru": "рот"},
    {"id": "te_hand",      "kana": "て",            "romaji": "te",            "ru": "рука, кисть"},
    {"id": "ashi",         "kana": "あし",          "romaji": "ashi",          "ru": "нога; ступня"},
    {"id": "onaka",        "kana": "おなか",         "romaji": "onaka",         "ru": "живот",
     "note": "おなかが すいた — «проголодался»."},
    {"id": "byouki",       "kana": "びょうき",       "romaji": "byouki",        "ru": "болезнь, больной"},
    {"id": "kusuri",       "kana": "くすり",         "romaji": "kusuri",        "ru": "лекарство",
     "note": "くすりを のむ — «принимать лекарство» (букв. «пить»)."},

    # ======================= ЮНИТ 13 — Цвета =======================
    # --- v23: цвета ---
    {"id": "iro",          "kana": "いろ",          "romaji": "iro",           "ru": "цвет"},
    {"id": "akai",         "kana": "あかい",         "romaji": "akai",          "ru": "красный",
     "note": "い-прил. Существительное «красный (цвет)» — あか."},
    {"id": "aoi",          "kana": "あおい",         "romaji": "aoi",           "ru": "синий, голубой",
     "note": "い-прил. Иногда покрывает и «зелёный» (светофор, листва)."},
    {"id": "kiiroi",       "kana": "きいろい",       "romaji": "kiiroi",        "ru": "жёлтый",
     "note": "い-прил. Существительное — きいろ."},
    {"id": "shiroi",       "kana": "しろい",         "romaji": "shiroi",        "ru": "белый",
     "note": "い-прил. Существительное — しろ."},
    {"id": "kuroi",        "kana": "くろい",         "romaji": "kuroi",         "ru": "чёрный",
     "note": "い-прил. Существительное — くろ."},
    {"id": "chairoi",      "kana": "ちゃいろい",      "romaji": "chairoi",       "ru": "коричневый",
     "note": "Букв. «цвета чая» (ちゃ + いろ)."},
    {"id": "midori",       "kana": "みどり",         "romaji": "midori",        "ru": "зелёный (цвет)",
     "note": "Существительное, не い-прил.: みどりの き."},
    {"id": "murasaki",     "kana": "むらさき",       "romaji": "murasaki",      "ru": "фиолетовый"},
    {"id": "pinku",        "kana": "ピンク",         "romaji": "pinku",         "ru": "розовый",
     "note": "Гайрайго от pink."},

    # ======================= ЮНИТ 14 — Вопросы и наречия =======================
    # --- v24: вопросительные слова и частотные наречия ---
    {"id": "itsu",         "kana": "いつ",          "romaji": "itsu",          "ru": "когда"},
    {"id": "doko",         "kana": "どこ",          "romaji": "doko",          "ru": "где, куда"},
    {"id": "nani",         "kana": "なに",          "romaji": "nani",          "ru": "что",
     "note": "Перед некоторыми звуками читается なん: なんですか."},
    {"id": "naze",         "kana": "なぜ",          "romaji": "naze",          "ru": "почему",
     "note": "Разговорный вариант — どうして."},
    {"id": "dou",          "kana": "どう",          "romaji": "dou",           "ru": "как, каким образом"},
    {"id": "ikura",        "kana": "いくら",         "romaji": "ikura",         "ru": "сколько (стоит)",
     "note": "これは いくら ですか — «сколько это стоит?»"},
    {"id": "totemo",       "kana": "とても",         "romaji": "totemo",        "ru": "очень"},
    {"id": "sukoshi",      "kana": "すこし",         "romaji": "sukoshi",       "ru": "немного, чуть-чуть"},
    {"id": "takusan",      "kana": "たくさん",       "romaji": "takusan",       "ru": "много"},
    {"id": "amari",        "kana": "あまり",         "romaji": "amari",         "ru": "не очень (с отрицанием)",
     "note": "あまり… ません — «не очень / не особо»."},
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

    # --- Юнит 5 — Повседневные глаголы ---
    {"id": "v13", "type": "vocab", "unit": 5, "title": "Действия и движение", "subtitle": "10 слов", "icon": "歩",
     "words": ["kau", "uru", "kaeru", "aruku", "hashiru",
               "tatsu", "suwaru", "matsu", "au", "asobu"],
     "intro": "Глаголы движения и действий в словарной форме. В вежливой речи они становятся ます-формой: "
              "かう→かいます, まつ→まちます. Тип спряжения подсказан в заметке к каждому слову."},
    {"id": "v14", "type": "vocab", "unit": 5, "title": "Общение и дела", "subtitle": "10 слов", "icon": "話",
     "words": ["hanasu", "iu", "narau", "oshieru", "tsukau",
               "tsukuru", "wasureru", "oboeru", "yasumu", "hataraku"],
     "intro": "Глаголы общения, учёбы и работы. はなす «разговаривать» и いう «сказать» — основа любого диалога; "
              "ならう/おしえる — пара «учиться/учить»."},

    # --- Юнит 6 — Прилагательные ---
    {"id": "v15", "type": "vocab", "unit": 6, "title": "Размер и оценка", "subtitle": "10 слов", "icon": "大",
     "words": ["ookii", "chiisai", "takai", "yasui", "atarashii",
               "furui", "nagai", "mijikai", "ii_adj", "warui"],
     "intro": "Прилагательные-антонимы парами: большой/маленький, дорогой/дешёвый, новый/старый. "
              "Все здесь — い-типа: меняют хвост い (おおきい→おおきくない «не большой»)."},
    {"id": "v16", "type": "vocab", "unit": 6, "title": "Ощущения и характер", "subtitle": "10 слов", "icon": "暑",
     "words": ["atsui", "samui", "tanoshii", "muzukashii", "yasashii",
               "isogashii", "kirei", "shizuka", "yuumei", "benri"],
     "intro": "Ощущения и оценки. Первые шесть — い-прилагательные, а きれい, しずか, ゆうめい, べんり — "
              "な-типа: перед существительным присоединяются через な (きれいな はな «красивый цветок»)."},

    # --- Юнит 7 — Время и календарь ---
    {"id": "v17", "type": "vocab", "unit": 7, "title": "Календарь", "subtitle": "10 слов", "icon": "暦",
     "words": ["kotoshi", "raishuu", "senshuu", "kongetsu", "raigetsu",
               "gogo", "gozen", "han_time", "fun_min", "tanjoubi"],
     "intro": "«Этот/следующий/прошлый» для недель и месяцев, деление суток на ごぜん/ごご и счёт минут. "
              "С はん и ふん можно назвать любое время: にじはん, ごふん."},

    # --- Юнит 8 — Места и город ---
    {"id": "v18", "type": "vocab", "unit": 8, "title": "Места в городе", "subtitle": "10 слов", "icon": "町",
     "words": ["eki", "mise", "ginkou", "byouin", "gakkou",
               "kouen", "toshokan", "yuubinkyoku", "depaato", "machi"],
     "intro": "Куда ходят в городе: станция, магазин, банк, больница… С этими словами и глаголом いく "
              "получится сказать, куда вы направляетесь."},

    # --- Юнит 9 — Транспорт и движение ---
    {"id": "v19", "type": "vocab", "unit": 9, "title": "Транспорт", "subtitle": "10 слов", "icon": "車",
     "words": ["densha", "basu", "kuruma", "hikouki", "jitensha",
               "chikatetsu", "takushii", "michi", "noru", "oriru"],
     "intro": "На чём передвигаться и как «сесть/сойти». のる и おりる управляют частицей に: "
              "でんしゃに のる — «сесть на электричку»."},

    # --- Юнит 10 — Семья ---
    {"id": "v20", "type": "vocab", "unit": 10, "title": "Семья", "subtitle": "10 слов", "icon": "家",
     "words": ["kazoku", "otousan", "okaasan", "ani", "ane",
               "otouto", "imouto", "kodomo", "kyoudai", "otoko"],
     "intro": "Члены семьи. Важная тонкость: о своей семье и о чужой говорят по-разному — "
              "ちち/おとうさん, はは/おかあさん. В заметках указаны оба варианта."},

    # --- Юнит 11 — Природа и погода ---
    {"id": "v21", "type": "vocab", "unit": 11, "title": "Природа и погода", "subtitle": "10 слов", "icon": "天",
     "words": ["tenki", "ame", "yuki", "kaze", "yama",
               "kawa", "umi", "sora", "ki_tree", "hana"],
     "intro": "Погода и пейзаж. かぜ значит и «ветер», и «простуда» — различают по контексту."},

    # --- Юнит 12 — Тело и здоровье ---
    {"id": "v22", "type": "vocab", "unit": 12, "title": "Тело и здоровье", "subtitle": "10 слов", "icon": "体",
     "words": ["atama", "kao", "me_eye", "mimi", "kuchi",
               "te_hand", "ashi", "onaka", "byouki", "kusuri"],
     "intro": "Части тела и слова о самочувствии. У врача пригодятся びょうき «болезнь» и くすり «лекарство»."},

    # --- Юнит 13 — Цвета ---
    {"id": "v23", "type": "vocab", "unit": 13, "title": "Цвета", "subtitle": "10 слов", "icon": "色",
     "words": ["iro", "akai", "aoi", "kiiroi", "shiroi",
               "kuroi", "chairoi", "midori", "murasaki", "pinku"],
     "intro": "Основные цвета. Первые шесть — い-прилагательные (あかい «красный»), а みどり, むらさき, ピンク — "
              "существительные и соединяются через の: みどりの き."},

    # --- Юнит 14 — Вопросы и наречия ---
    {"id": "v24", "type": "vocab", "unit": 14, "title": "Вопросы и наречия", "subtitle": "10 слов", "icon": "問",
     "words": ["itsu", "doko", "nani", "naze", "dou",
               "ikura", "totemo", "sukoshi", "takusan", "amari"],
     "intro": "Вопросительные слова (いつ, どこ, なに…) и частотные наречия меры (とても, すこし, たくさん). "
              "あまり работает только с отрицанием: あまり わかりません — «не очень понимаю»."},
]
