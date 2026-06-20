# -*- coding: utf-8 -*-
"""Контент курса хираганы (SRS.md, раздел 2.1).

104 графемы/комбинации: 46 базовых + 25 дакутэн/хандакутэн + 33 ёон.
17 микроуроков: по рядам годзюон, затем дакутэн, ёон и урок-правило
(сокуон/долгие гласные). Ловушки — парные тренировки похожих знаков.
"""

# kind: basic | dakuten | handakuten | yoon
# lookalikes: визуально похожие знаки для дистракторов (тип 2 kana_reverse)
KANA = [
    # --- あ行 ---
    {"char": "あ", "romaji": "a",   "kind": "basic", "row": "a",  "mnemonic": "Антенна на крыше дома — «А-а, ловит!»", "mnemonics": ["Аист расправил крылья — «А-а!»"], "lookalikes": ["お", "め", "ぬ"]},
    {"char": "い", "romaji": "i",   "kind": "basic", "row": "a",  "mnemonic": "Две сосульки рядом — «И-и, холодно!»", "mnemonics": ["Два прыгающих дельфина — «И-и!»"], "lookalikes": ["り", "こ"]},
    {"char": "う", "romaji": "u",   "kind": "basic", "row": "a",  "mnemonic": "Утка нырнула клювом вперёд — «У!»", "mnemonics": ["Человек согнулся в поклоне — «У-у, устал»"], "lookalikes": ["つ", "ら"]},
    {"char": "え", "romaji": "e",   "kind": "basic", "row": "a",  "mnemonic": "Экзотическая птица на ветке — «Э!»", "mnemonics": ["Энот тянет лапку вверх — «Э!»"], "lookalikes": ["そ", "ん"]},
    {"char": "お", "romaji": "o",   "kind": "basic", "row": "a",  "mnemonic": "Облако с хвостиком — «О!»", "mnemonics": ["Почти как あ, но с бантиком — «О, родня!»"], "lookalikes": ["あ", "む"]},
    # --- か行 ---
    {"char": "か", "romaji": "ka",  "kind": "basic", "row": "ka", "mnemonic": "КАтана, рассекающая воздух", "mnemonics": ["Каратист в стойке, нога отставлена — «КА!»"], "lookalikes": ["や", "せ"]},
    {"char": "き", "romaji": "ki",  "kind": "basic", "row": "ka", "mnemonic": "КЛЮЧ (key) с двумя зубцами", "mnemonics": ["Колосок пшеницы клонится — «КИ»"], "lookalikes": ["さ", "ち"]},
    {"char": "く", "romaji": "ku",  "kind": "basic", "row": "ka", "mnemonic": "КЛЮв птицы, раскрытый — «ку-ку»", "mnemonics": ["Уголок «меньше» (<) — КУ-да острие?"], "lookalikes": ["へ", "し"]},
    {"char": "け", "romaji": "ke",  "kind": "basic", "row": "ka", "mnemonic": "КЕгля у стены", "mnemonics": ["Кенгуру в прыжке, лапка отставлена — «КЕ!»"], "lookalikes": ["は", "ほ"]},
    {"char": "こ", "romaji": "ko",  "kind": "basic", "row": "ka", "mnemonic": "Две КОроткие полки", "mnemonics": ["Два КОврика друг над другом"], "lookalikes": ["に", "い"]},
    # --- さ行 ---
    {"char": "さ", "romaji": "sa",  "kind": "basic", "row": "sa", "mnemonic": "САмолётик с одним крылом", "mnemonics": ["САдовый цветок на стебле клонится"], "lookalikes": ["き", "ち"]},
    {"char": "し", "romaji": "shi", "kind": "basic", "row": "sa", "mnemonic": "Леска с крючком — «ШИкарный улов»", "mnemonics": ["Улыбка-крючок снизу вверх — «ШИ-ши»"], "lookalikes": ["く", "つ"]},
    {"char": "す", "romaji": "su",  "kind": "basic", "row": "sa", "mnemonic": "Петля на верёвке — «СУ-узел»", "mnemonics": ["Леденец на палочке с завитком — «СУ-сладко»"], "lookalikes": ["む", "お"]},
    {"char": "せ", "romaji": "se",  "kind": "basic", "row": "sa", "mnemonic": "СЕть, натянутая на шест", "mnemonics": ["СЕно на вилах"], "lookalikes": ["さ", "か"]},
    {"char": "そ", "romaji": "so",  "kind": "basic", "row": "sa", "mnemonic": "Зигзаг молнии — «СОрвалась с неба»", "mnemonics": ["Нитка зашивает зигзагом — «СО-шью»"], "lookalikes": ["え", "ろ"]},
    # --- た行 ---
    {"char": "た", "romaji": "ta",  "kind": "basic", "row": "ta", "mnemonic": "Латинские «t» и «a» рядом — ТА!", "mnemonics": ["ТАнк с пушкой и гусеницей"], "lookalikes": ["な", "に"]},
    {"char": "ち", "romaji": "chi", "kind": "basic", "row": "ta", "mnemonic": "Пятёрка наоборот — «ЧИсло 5»", "mnemonics": ["Гимнаст прогнулся назад — «ЧИ»"], "lookalikes": ["さ", "き", "ら"]},
    {"char": "つ", "romaji": "tsu", "kind": "basic", "row": "ta", "mnemonic": "Волна ЦУнами", "mnemonics": ["Крючок-улыбка набок — «ЦУ»"], "lookalikes": ["う", "し", "ら"]},
    {"char": "て", "romaji": "te",  "kind": "basic", "row": "ta", "mnemonic": "Изогнутая рука (te = рука)", "mnemonics": ["Клюшка для гольфа — «ТЭ»"], "lookalikes": ["で", "そ"]},
    {"char": "と", "romaji": "to",  "kind": "basic", "row": "ta", "mnemonic": "Палец ноги с занозой (toe)", "mnemonics": ["Гвоздь с капелькой — «ТО-чка»"], "lookalikes": ["し", "ど"]},
    # --- な行 ---
    {"char": "な", "romaji": "na",  "kind": "basic", "row": "na", "mnemonic": "Крест с НАвесом и петелькой", "mnemonics": ["Монах НАгнулся в молитве"], "lookalikes": ["た", "は"]},
    {"char": "に", "romaji": "ni",  "kind": "basic", "row": "na", "mnemonic": "НИша с двумя полками", "mnemonics": ["Иголка с ниткой — «НИ-точка»"], "lookalikes": ["こ", "た"]},
    {"char": "ぬ", "romaji": "nu",  "kind": "basic", "row": "na", "mnemonic": "Лапша (НУдлы) на вилке с петлёй", "mnemonics": ["Узелок-петля — «НУ, завяжи»"], "lookalikes": ["め", "ね", "あ"]},
    {"char": "ね", "romaji": "ne",  "kind": "basic", "row": "na", "mnemonic": "Кошка (НЭко) с хвостом-петлёй", "mnemonics": ["Змейка свернулась колечком — «НЭ»"], "lookalikes": ["わ", "れ", "ぬ"]},
    {"char": "の", "romaji": "no",  "kind": "basic", "row": "na", "mnemonic": "Вихрь-завиток — «НОль с хвостом»", "mnemonics": ["Улитка закрутилась — «НО»"], "lookalikes": ["め", "ぬ"]},
    # --- は行 ---
    {"char": "は", "romaji": "ha",  "kind": "basic", "row": "ha", "mnemonic": "Стена и буква «а» — ХАта", "mnemonics": ["Человечек машет рукой — «ХА-привет»"], "lookalikes": ["ほ", "け", "ま"]},
    {"char": "ひ", "romaji": "hi",  "kind": "basic", "row": "ha", "mnemonic": "Улыбка — «ХИ-хи»", "mnemonics": ["Нос профиля — «ХИ-хихикает»"], "lookalikes": ["び", "ぴ"]},
    {"char": "ふ", "romaji": "fu",  "kind": "basic", "row": "ha", "mnemonic": "Гора ФУдзи с облачками", "mnemonics": ["Танцор с раскинутыми руками — «ФУ-х»"], "lookalikes": ["ぶ", "う"]},
    {"char": "へ", "romaji": "he",  "kind": "basic", "row": "ha", "mnemonic": "Холмик: поднялся и спустился — «ХЭй!»", "mnemonics": ["Стрелка-галочка вверх — «ХЭ»"], "lookalikes": ["く", "べ"]},
    {"char": "ほ", "romaji": "ho",  "kind": "basic", "row": "ha", "mnemonic": "Как は, но с крышей — ХОзяин достроил", "mnemonics": ["Почтовый ящик с флажком — «ХО»"], "lookalikes": ["は", "け", "ま"]},
    # --- ま行 ---
    {"char": "ま", "romaji": "ma",  "kind": "basic", "row": "ma", "mnemonic": "Клубок с хвостиком — МАма вяжет", "mnemonics": ["Леденец на палочке с двумя петлями — «МА»"], "lookalikes": ["は", "ほ", "も"]},
    {"char": "み", "romaji": "mi",  "kind": "basic", "row": "ma", "mnemonic": "Число 21 с петлёй — «МИ»", "mnemonics": ["Узел с двумя хвостиками — «МИ»"], "lookalikes": ["ふ", "ん"]},
    {"char": "む", "romaji": "mu",  "kind": "basic", "row": "ma", "mnemonic": "Корова с рогом и хвостом — «МУ-у!»", "mnemonics": ["Узелок с задорным хвостиком — «МУ-дрёный»"], "lookalikes": ["す", "お"]},
    {"char": "め", "romaji": "me",  "kind": "basic", "row": "ma", "mnemonic": "Глаз (мэ = глаз): петля с пересечением", "mnemonics": ["Моток ниток крест-накрест — «МЭ»"], "lookalikes": ["ぬ", "の", "あ"]},
    {"char": "も", "romaji": "mo",  "kind": "basic", "row": "ma", "mnemonic": "Червяк на крючке — МОрмышка", "mnemonics": ["Рыболовный крючок с двумя наживками — «МО»"], "lookalikes": ["ま", "し"]},
    # --- や行 ---
    {"char": "や", "romaji": "ya",  "kind": "basic", "row": "ya", "mnemonic": "Рогатка с натянутой резинкой — «Я!»", "mnemonics": ["Як с большими рогами — «Я»"], "lookalikes": ["か", "ゆ"]},
    {"char": "ゆ", "romaji": "yu",  "kind": "basic", "row": "ya", "mnemonic": "ЮРкая рыбка с плавником", "mnemonics": ["Петля лассо — «Ю-у, поймал»"], "lookalikes": ["や", "よ"]},
    {"char": "よ", "romaji": "yo",  "kind": "basic", "row": "ya", "mnemonic": "ЙО-йо, повисшее на пальце", "mnemonics": ["Крючок с узелком на леске — «ЙО»"], "lookalikes": ["ま", "ゆ"]},
    # --- ら行 ---
    {"char": "ら", "romaji": "ra",  "kind": "basic", "row": "ra", "mnemonic": "КобРА подняла голову", "mnemonics": ["Человек бежит с флажком — «РА»"], "lookalikes": ["ち", "う", "ろ"]},
    {"char": "り", "romaji": "ri",  "kind": "basic", "row": "ra", "mnemonic": "Две травинки — РИс растёт", "mnemonics": ["Две капли дождя падают — «РИ»"], "lookalikes": ["い", "け"]},
    {"char": "る", "romaji": "ru",  "kind": "basic", "row": "ra", "mnemonic": "Дорога с петлёй на конце — маршРУт", "mnemonics": ["Леденец-завиток на палочке — «РУ»"], "lookalikes": ["ろ", "そ"]},
    {"char": "れ", "romaji": "re",  "kind": "basic", "row": "ra", "mnemonic": "Человек делает РЕверанс, отставив ногу", "mnemonics": ["Бегун рванул с низкого старта — «РЭ»"], "lookalikes": ["わ", "ね", "ぬ"]},
    {"char": "ろ", "romaji": "ro",  "kind": "basic", "row": "ra", "mnemonic": "Как る, но без петли — доРОга прямая", "mnemonics": ["Цифра 3 угловатая — «РО»"], "lookalikes": ["る", "そ"]},
    # --- わ行 + ん ---
    {"char": "わ", "romaji": "wa",  "kind": "basic", "row": "wa", "mnemonic": "Как れ, но с круглым боком — ВАтрушка", "mnemonics": ["Человек машет платком — «ВА-пока»"], "lookalikes": ["ね", "れ"]},
    {"char": "を", "romaji": "wo",  "kind": "basic", "row": "wa", "mnemonic": "Человек замахнулся копьём — «ВО!»", "mnemonics": ["Танцор в выпаде с лентой — «О» (частица)"], "lookalikes": ["お", "と"]},
    {"char": "ん", "romaji": "n",   "kind": "basic", "row": "wa", "mnemonic": "Английская «n» курсивом — росчерк", "mnemonics": ["Завиток-подпись в конце слова — «Н»"], "lookalikes": ["え", "そ"]},
    # --- дакутэн: が行 ---
    {"char": "が", "romaji": "ga", "kind": "dakuten", "row": "ga", "base": "か", "lookalikes": ["か", "ば"]},
    {"char": "ぎ", "romaji": "gi", "kind": "dakuten", "row": "ga", "base": "き", "lookalikes": ["き", "さ"]},
    {"char": "ぐ", "romaji": "gu", "kind": "dakuten", "row": "ga", "base": "く", "lookalikes": ["く", "ぶ"]},
    {"char": "げ", "romaji": "ge", "kind": "dakuten", "row": "ga", "base": "け", "lookalikes": ["け", "ば"]},
    {"char": "ご", "romaji": "go", "kind": "dakuten", "row": "ga", "base": "こ", "lookalikes": ["こ", "ざ"]},
    # --- дакутэн: ざ行 ---
    {"char": "ざ", "romaji": "za", "kind": "dakuten", "row": "za", "base": "さ", "lookalikes": ["さ", "ぎ"]},
    {"char": "じ", "romaji": "ji", "kind": "dakuten", "row": "za", "base": "し", "lookalikes": ["し", "ち"]},
    {"char": "ず", "romaji": "zu", "kind": "dakuten", "row": "za", "base": "す", "lookalikes": ["す", "づ"]},
    {"char": "ぜ", "romaji": "ze", "kind": "dakuten", "row": "za", "base": "せ", "lookalikes": ["せ", "ぱ"]},
    {"char": "ぞ", "romaji": "zo", "kind": "dakuten", "row": "za", "base": "そ", "lookalikes": ["そ", "ど"]},
    # --- дакутэн: だ行 ---
    {"char": "だ", "romaji": "da", "kind": "dakuten", "row": "da", "base": "た", "lookalikes": ["た", "な"]},
    {"char": "ぢ", "romaji": "ji (di)", "kind": "dakuten", "row": "da", "base": "ち", "lookalikes": ["ち", "じ"], "note": "Редкий знак: тот же звук, что じ. Встречается в はなぢ (кровь из носа)."},
    {"char": "づ", "romaji": "zu (du)", "kind": "dakuten", "row": "da", "base": "つ", "lookalikes": ["つ", "ず"], "note": "Редкий знак: тот же звук, что ず. Встречается в つづく (продолжаться)."},
    {"char": "で", "romaji": "de", "kind": "dakuten", "row": "da", "base": "て", "lookalikes": ["て", "ぜ"]},
    {"char": "ど", "romaji": "do", "kind": "dakuten", "row": "da", "base": "と", "lookalikes": ["と", "ぞ"]},
    # --- дакутэн: ば行 ---
    {"char": "ば", "romaji": "ba", "kind": "dakuten", "row": "ba", "base": "は", "lookalikes": ["は", "ぱ", "ほ"]},
    {"char": "び", "romaji": "bi", "kind": "dakuten", "row": "ba", "base": "ひ", "lookalikes": ["ひ", "ぴ"]},
    {"char": "ぶ", "romaji": "bu", "kind": "dakuten", "row": "ba", "base": "ふ", "lookalikes": ["ふ", "ぷ"]},
    {"char": "べ", "romaji": "be", "kind": "dakuten", "row": "ba", "base": "へ", "lookalikes": ["へ", "ぺ"]},
    {"char": "ぼ", "romaji": "bo", "kind": "dakuten", "row": "ba", "base": "ほ", "lookalikes": ["ほ", "ぽ", "ば"]},
    # --- хандакутэн: ぱ行 ---
    {"char": "ぱ", "romaji": "pa", "kind": "handakuten", "row": "pa", "base": "は", "lookalikes": ["は", "ば"]},
    {"char": "ぴ", "romaji": "pi", "kind": "handakuten", "row": "pa", "base": "ひ", "lookalikes": ["ひ", "び"]},
    {"char": "ぷ", "romaji": "pu", "kind": "handakuten", "row": "pa", "base": "ふ", "lookalikes": ["ふ", "ぶ"]},
    {"char": "ぺ", "romaji": "pe", "kind": "handakuten", "row": "pa", "base": "へ", "lookalikes": ["へ", "べ"]},
    {"char": "ぽ", "romaji": "po", "kind": "handakuten", "row": "pa", "base": "ほ", "lookalikes": ["ほ", "ぼ"]},
    # --- ёон: базовые ---
    {"char": "きゃ", "romaji": "kya", "kind": "yoon", "row": "yoon1", "base": "き", "lookalikes": ["きゅ", "きょ", "ちゃ"]},
    {"char": "きゅ", "romaji": "kyu", "kind": "yoon", "row": "yoon1", "base": "き", "lookalikes": ["きゃ", "きょ", "ちゅ"]},
    {"char": "きょ", "romaji": "kyo", "kind": "yoon", "row": "yoon1", "base": "き", "lookalikes": ["きゃ", "きゅ", "ちょ"]},
    {"char": "しゃ", "romaji": "sha", "kind": "yoon", "row": "yoon1", "base": "し", "lookalikes": ["しゅ", "しょ", "ちゃ"]},
    {"char": "しゅ", "romaji": "shu", "kind": "yoon", "row": "yoon1", "base": "し", "lookalikes": ["しゃ", "しょ", "ちゅ"]},
    {"char": "しょ", "romaji": "sho", "kind": "yoon", "row": "yoon1", "base": "し", "lookalikes": ["しゃ", "しゅ", "ちょ"]},
    {"char": "ちゃ", "romaji": "cha", "kind": "yoon", "row": "yoon1", "base": "ち", "lookalikes": ["ちゅ", "ちょ", "しゃ"]},
    {"char": "ちゅ", "romaji": "chu", "kind": "yoon", "row": "yoon1", "base": "ち", "lookalikes": ["ちゃ", "ちょ", "しゅ"]},
    {"char": "ちょ", "romaji": "cho", "kind": "yoon", "row": "yoon1", "base": "ち", "lookalikes": ["ちゃ", "ちゅ", "しょ"]},
    {"char": "にゃ", "romaji": "nya", "kind": "yoon", "row": "yoon1", "base": "に", "lookalikes": ["にゅ", "にょ", "みゃ"]},
    {"char": "にゅ", "romaji": "nyu", "kind": "yoon", "row": "yoon1", "base": "に", "lookalikes": ["にゃ", "にょ", "みゅ"]},
    {"char": "にょ", "romaji": "nyo", "kind": "yoon", "row": "yoon1", "base": "に", "lookalikes": ["にゃ", "にゅ", "みょ"]},
    {"char": "ひゃ", "romaji": "hya", "kind": "yoon", "row": "yoon2", "base": "ひ", "lookalikes": ["ひゅ", "ひょ", "びゃ"]},
    {"char": "ひゅ", "romaji": "hyu", "kind": "yoon", "row": "yoon2", "base": "ひ", "lookalikes": ["ひゃ", "ひょ", "びゅ"]},
    {"char": "ひょ", "romaji": "hyo", "kind": "yoon", "row": "yoon2", "base": "ひ", "lookalikes": ["ひゃ", "ひゅ", "びょ"]},
    {"char": "みゃ", "romaji": "mya", "kind": "yoon", "row": "yoon2", "base": "み", "lookalikes": ["みゅ", "みょ", "にゃ"]},
    {"char": "みゅ", "romaji": "myu", "kind": "yoon", "row": "yoon2", "base": "み", "lookalikes": ["みゃ", "みょ", "にゅ"]},
    {"char": "みょ", "romaji": "myo", "kind": "yoon", "row": "yoon2", "base": "み", "lookalikes": ["みゃ", "みゅ", "にょ"]},
    {"char": "りゃ", "romaji": "rya", "kind": "yoon", "row": "yoon2", "base": "り", "lookalikes": ["りゅ", "りょ", "きゃ"]},
    {"char": "りゅ", "romaji": "ryu", "kind": "yoon", "row": "yoon2", "base": "り", "lookalikes": ["りゃ", "りょ", "きゅ"]},
    {"char": "りょ", "romaji": "ryo", "kind": "yoon", "row": "yoon2", "base": "り", "lookalikes": ["りゃ", "りゅ", "きょ"]},
    # --- ёон: дакутэн ---
    {"char": "ぎゃ", "romaji": "gya", "kind": "yoon", "row": "yoon3", "base": "ぎ", "lookalikes": ["ぎゅ", "ぎょ", "きゃ"]},
    {"char": "ぎゅ", "romaji": "gyu", "kind": "yoon", "row": "yoon3", "base": "ぎ", "lookalikes": ["ぎゃ", "ぎょ", "きゅ"]},
    {"char": "ぎょ", "romaji": "gyo", "kind": "yoon", "row": "yoon3", "base": "ぎ", "lookalikes": ["ぎゃ", "ぎゅ", "きょ"]},
    {"char": "じゃ", "romaji": "ja",  "kind": "yoon", "row": "yoon3", "base": "じ", "lookalikes": ["じゅ", "じょ", "しゃ"]},
    {"char": "じゅ", "romaji": "ju",  "kind": "yoon", "row": "yoon3", "base": "じ", "lookalikes": ["じゃ", "じょ", "しゅ"]},
    {"char": "じょ", "romaji": "jo",  "kind": "yoon", "row": "yoon3", "base": "じ", "lookalikes": ["じゃ", "じゅ", "しょ"]},
    {"char": "びゃ", "romaji": "bya", "kind": "yoon", "row": "yoon3", "base": "び", "lookalikes": ["びゅ", "びょ", "ぴゃ"]},
    {"char": "びゅ", "romaji": "byu", "kind": "yoon", "row": "yoon3", "base": "び", "lookalikes": ["びゃ", "びょ", "ぴゅ"]},
    {"char": "びょ", "romaji": "byo", "kind": "yoon", "row": "yoon3", "base": "び", "lookalikes": ["びゃ", "びゅ", "ぴょ"]},
    {"char": "ぴゃ", "romaji": "pya", "kind": "yoon", "row": "yoon3", "base": "ぴ", "lookalikes": ["ぴゅ", "ぴょ", "びゃ"]},
    {"char": "ぴゅ", "romaji": "pyu", "kind": "yoon", "row": "yoon3", "base": "ぴ", "lookalikes": ["ぴゃ", "ぴょ", "びゅ"]},
    {"char": "ぴょ", "romaji": "pyo", "kind": "yoon", "row": "yoon3", "base": "ぴ", "lookalikes": ["ぴゃ", "ぴゅ", "びょ"]},
]

KANA_BY_CHAR = {k["char"]: k for k in KANA}

# Группы «ловушек» (раздел 2.1: парные тренировки визуально похожих знаков)
TRAP_GROUPS = [
    ["あ", "お"],
    ["き", "さ"],
    ["さ", "ち"],
    ["う", "つ"],
    ["こ", "に"],
    ["ぬ", "め"],
    ["は", "ほ"],
    ["く", "へ"],
    ["わ", "れ", "ね"],
    ["る", "ろ"],
]

# Слова для kana_word_build: только из каны, изученной к данному уроку (принцип i+1)
WORDS = {
    "l01": [
        {"kana": "あい", "romaji": "ai",  "ru": "любовь"},
        {"kana": "いえ", "romaji": "ie",  "ru": "дом"},
        {"kana": "うえ", "romaji": "ue",  "ru": "верх"},
        {"kana": "あお", "romaji": "ao",  "ru": "синий"},
    ],
    "l02": [
        {"kana": "あか", "romaji": "aka",  "ru": "красный"},
        {"kana": "かお", "romaji": "kao",  "ru": "лицо"},
        {"kana": "いけ", "romaji": "ike",  "ru": "пруд"},
        {"kana": "こえ", "romaji": "koe",  "ru": "голос"},
        {"kana": "えき", "romaji": "eki",  "ru": "станция"},
        {"kana": "きく", "romaji": "kiku", "ru": "слушать"},
    ],
    "l03": [
        {"kana": "あさ",  "romaji": "asa",   "ru": "утро"},
        {"kana": "すし",  "romaji": "sushi", "ru": "суши"},
        {"kana": "いす",  "romaji": "isu",   "ru": "стул"},
        {"kana": "しお",  "romaji": "shio",  "ru": "соль"},
        {"kana": "さけ",  "romaji": "sake",  "ru": "сакэ"},
        {"kana": "せかい", "romaji": "sekai", "ru": "мир"},
    ],
    "l04": [
        {"kana": "した",  "romaji": "shita",  "ru": "низ"},
        {"kana": "くつ",  "romaji": "kutsu",  "ru": "обувь"},
        {"kana": "つくえ", "romaji": "tsukue", "ru": "стол"},
        {"kana": "たかい", "romaji": "takai",  "ru": "высокий"},
        {"kana": "ちかい", "romaji": "chikai", "ru": "близкий"},
        {"kana": "とけい", "romaji": "tokei",  "ru": "часы"},
    ],
    "l05": [
        {"kana": "なつ",  "romaji": "natsu", "ru": "лето"},
        {"kana": "いぬ",  "romaji": "inu",   "ru": "собака"},
        {"kana": "ねこ",  "romaji": "neko",  "ru": "кошка"},
        {"kana": "にく",  "romaji": "niku",  "ru": "мясо"},
        {"kana": "なに",  "romaji": "nani",  "ru": "что"},
        {"kana": "おかね", "romaji": "okane", "ru": "деньги"},
    ],
    "l06": [
        {"kana": "はな", "romaji": "hana", "ru": "цветок"},
        {"kana": "ひと", "romaji": "hito", "ru": "человек"},
        {"kana": "ふね", "romaji": "fune", "ru": "корабль"},
        {"kana": "ほし", "romaji": "hoshi", "ru": "звезда"},
        {"kana": "はは", "romaji": "haha", "ru": "мама"},
        {"kana": "へた", "romaji": "heta", "ru": "неумелый"},
    ],
    "l07": [
        {"kana": "まち",  "romaji": "machi",  "ru": "город"},
        {"kana": "みみ",  "romaji": "mimi",   "ru": "ухо"},
        {"kana": "むし",  "romaji": "mushi",  "ru": "насекомое"},
        {"kana": "め",   "romaji": "me",     "ru": "глаз"},
        {"kana": "もも",  "romaji": "momo",   "ru": "персик"},
        {"kana": "なまえ", "romaji": "namae",  "ru": "имя"},
    ],
    "l08": [
        {"kana": "やま",  "romaji": "yama",   "ru": "гора"},
        {"kana": "ゆき",  "romaji": "yuki",   "ru": "снег"},
        {"kana": "よこ",  "romaji": "yoko",   "ru": "бок, сторона"},
        {"kana": "ふゆ",  "romaji": "fuyu",   "ru": "зима"},
        {"kana": "やすみ", "romaji": "yasumi", "ru": "отдых, выходной"},
        {"kana": "やさい", "romaji": "yasai",  "ru": "овощи"},
    ],
    "l09": [
        {"kana": "そら",  "romaji": "sora",   "ru": "небо"},
        {"kana": "とり",  "romaji": "tori",   "ru": "птица"},
        {"kana": "はる",  "romaji": "haru",   "ru": "весна"},
        {"kana": "しろ",  "romaji": "shiro",  "ru": "белый"},
        {"kana": "さくら", "romaji": "sakura", "ru": "сакура"},
        {"kana": "くるま", "romaji": "kuruma", "ru": "машина"},
    ],
    "l10": [
        {"kana": "わたし",  "romaji": "watashi", "ru": "я"},
        {"kana": "ほん",   "romaji": "hon",     "ru": "книга"},
        {"kana": "みかん",  "romaji": "mikan",   "ru": "мандарин"},
        {"kana": "かわ",   "romaji": "kawa",    "ru": "река"},
        {"kana": "にわ",   "romaji": "niwa",    "ru": "сад"},
        {"kana": "にほん",  "romaji": "nihon",   "ru": "Япония"},
        {"kana": "せんせい", "romaji": "sensei",  "ru": "учитель"},
    ],
    "l11": [
        {"kana": "みず",   "romaji": "mizu",    "ru": "вода"},
        {"kana": "かぜ",   "romaji": "kaze",    "ru": "ветер"},
        {"kana": "ひざ",   "romaji": "hiza",    "ru": "колено"},
        {"kana": "かがみ",  "romaji": "kagami",  "ru": "зеркало"},
        {"kana": "ぎんこう", "romaji": "ginkou",  "ru": "банк"},
        {"kana": "かぞく",  "romaji": "kazoku",  "ru": "семья"},
    ],
    "l12": [
        {"kana": "だれ",   "romaji": "dare",     "ru": "кто"},
        {"kana": "どこ",   "romaji": "doko",     "ru": "где"},
        {"kana": "ばら",   "romaji": "bara",     "ru": "роза"},
        {"kana": "たべる",  "romaji": "taberu",   "ru": "есть, кушать"},
        {"kana": "ともだち", "romaji": "tomodachi", "ru": "друг"},
        {"kana": "くだもの", "romaji": "kudamono", "ru": "фрукты"},
    ],
    "l13": [
        {"kana": "さんぽ",   "romaji": "sanpo",    "ru": "прогулка"},
        {"kana": "えんぴつ",  "romaji": "enpitsu",  "ru": "карандаш"},
        {"kana": "かんぱい",  "romaji": "kanpai",   "ru": "тост («до дна!»)"},
        {"kana": "ぴかぴか",  "romaji": "pikapika", "ru": "блестящий (ономатопея)"},
        {"kana": "ぺこぺこ",  "romaji": "pekopeko", "ru": "голодный (ономатопея)"},
    ],
    "l14": [
        {"kana": "おちゃ",   "romaji": "ocha",     "ru": "чай"},
        {"kana": "きょう",   "romaji": "kyou",     "ru": "сегодня"},
        {"kana": "しゃしん",  "romaji": "shashin",  "ru": "фотография"},
        {"kana": "でんしゃ",  "romaji": "densha",   "ru": "электричка"},
        {"kana": "きょねん",  "romaji": "kyonen",   "ru": "прошлый год"},
        {"kana": "おにいちゃん", "romaji": "oniichan", "ru": "старший брат"},
    ],
    "l15": [
        {"kana": "ひゃく",  "romaji": "hyaku",  "ru": "сто"},
        {"kana": "りょこう", "romaji": "ryokou", "ru": "путешествие"},
        {"kana": "りょうり", "romaji": "ryouri", "ru": "готовка, кухня"},
        {"kana": "みょうじ", "romaji": "myouji", "ru": "фамилия"},
    ],
    "l16": [
        {"kana": "じしょ",    "romaji": "jisho",     "ru": "словарь"},
        {"kana": "じゃがいも",  "romaji": "jagaimo",   "ru": "картофель"},
        {"kana": "ぎゅうにゅう", "romaji": "gyuunyuu",  "ru": "молоко"},
        {"kana": "びょういん",  "romaji": "byouin",    "ru": "больница"},
        {"kana": "じゅぎょう",  "romaji": "jugyou",    "ru": "занятие, урок"},
    ],
    "l17": [
        {"kana": "きって",   "romaji": "kitte",    "ru": "почтовая марка"},
        {"kana": "がっこう",  "romaji": "gakkou",   "ru": "школа"},
        {"kana": "ざっし",   "romaji": "zasshi",   "ru": "журнал"},
        {"kana": "にっき",   "romaji": "nikki",    "ru": "дневник"},
        {"kana": "いっしょ",  "romaji": "issho",    "ru": "вместе"},
        {"kana": "せっけん",  "romaji": "sekken",   "ru": "мыло"},
        {"kana": "おかあさん", "romaji": "okaasan",  "ru": "мама (вежливо)"},
        {"kana": "おとうさん", "romaji": "otousan",  "ru": "папа (вежливо)"},
    ],
}

# 17 микроуроков (раздел 2.1: 1 ряд = 1 микроурок, 5–7 мин)
LESSONS = [
    {"id": "l01", "title": "Ряд あ", "subtitle": "a · i · u · e · o", "kana": ["あ", "い", "う", "え", "お"],
     "intro": "Первые пять знаков хираганы — пять гласных японского языка. Всё остальное строится на них."},
    {"id": "l02", "title": "Ряд か", "subtitle": "ka · ki · ku · ke · ko", "kana": ["か", "き", "く", "け", "こ"],
     "intro": "Согласная К + гласные. С этого урока вы уже читаете настоящие слова!"},
    {"id": "l03", "title": "Ряд さ", "subtitle": "sa · shi · su · se · so", "kana": ["さ", "し", "す", "せ", "そ"],
     "intro": "Внимание на исключение: し читается «ши» (shi), а не «si»."},
    {"id": "l04", "title": "Ряд た", "subtitle": "ta · chi · tsu · te · to", "kana": ["た", "ち", "つ", "て", "と"],
     "intro": "Два исключения: ち = «чи» (chi), つ = «цу» (tsu)."},
    {"id": "l05", "title": "Ряд な", "subtitle": "na · ni · nu · ne · no", "kana": ["な", "に", "ぬ", "ね", "の"],
     "intro": "Ряд Н. Здесь живут коварные близнецы ぬ и ね — приглядитесь к ним."},
    {"id": "l06", "title": "Ряд は", "subtitle": "ha · hi · fu · he · ho", "kana": ["は", "ひ", "ふ", "へ", "ほ"],
     "intro": "ふ — лёгкое «фу» (между «фу» и «ху»). Знак は как частица читается «ва»."},
    {"id": "l07", "title": "Ряд ま", "subtitle": "ma · mi · mu · me · mo", "kana": ["ま", "み", "む", "め", "も"],
     "intro": "Ряд М. Сравните め с ぬ из ряда な — частая путаница."},
    {"id": "l08", "title": "Ряд や", "subtitle": "ya · yu · yo", "kana": ["や", "ゆ", "よ"],
     "intro": "Только три знака. Позже их маленькие версии (ゃゅょ) образуют комбинации вроде きょ."},
    {"id": "l09", "title": "Ряд ら", "subtitle": "ra · ri · ru · re · ro", "kana": ["ら", "り", "る", "れ", "ろ"],
     "intro": "Японский «Р» — один удар языка, между русскими «р» и «л»."},
    {"id": "l10", "title": "Ряд わ и ん", "subtitle": "wa · wo · n", "kana": ["わ", "を", "ん"],
     "intro": "Последние знаки годзюон! を используется только как частица. ん — единственный одиночный согласный. Базовая хирагана пройдена!"},
    {"id": "l11", "title": "Дакутэн: が и ざ", "subtitle": "ga–go · za–zo", "kana": ["が", "ぎ", "ぐ", "げ", "ご", "ざ", "じ", "ず", "ぜ", "ぞ"],
     "intro": "Две чёрточки (゛дакутэн) озвончают согласный: か(ka) → が(ga), さ(sa) → ざ(za). Новых форм учить не надо — только правило!"},
    {"id": "l12", "title": "Дакутэн: だ и ば", "subtitle": "da–do · ba–bo", "kana": ["だ", "ぢ", "づ", "で", "ど", "ば", "び", "ぶ", "べ", "ぼ"],
     "intro": "た → だ (da), は → ば (ba). Знаки ぢ и づ редкие — звучат как じ и ず."},
    {"id": "l13", "title": "Хандакутэн: ぱ", "subtitle": "pa · pi · pu · pe · po", "kana": ["ぱ", "ぴ", "ぷ", "ぺ", "ぽ"],
     "intro": "Кружок (゜хандакутэн) превращает Х в П: は(ha) → ぱ(pa). Различайте триаду は/ば/ぱ!"},
    {"id": "l14", "title": "Ёон: きゃ・しゃ・ちゃ・にゃ", "subtitle": "kya · sha · cha · nya", "kana": ["きゃ", "きゅ", "きょ", "しゃ", "しゅ", "しょ", "ちゃ", "ちゅ", "ちょ", "にゃ", "にゅ", "にょ"],
     "intro": "Знак ряда И + маленькие ゃゅょ = один слог: き+ゃ = きゃ (кя). Важно: きや (кия, 2 слога) ≠ きゃ (кя, 1 слог) — смотрите на размер!"},
    {"id": "l15", "title": "Ёон: ひゃ・みゃ・りゃ", "subtitle": "hya · mya · rya", "kana": ["ひゃ", "ひゅ", "ひょ", "みゃ", "みゅ", "みょ", "りゃ", "りゅ", "りょ"],
     "intro": "Оставшиеся базовые комбинации ёон. りょ встречается очень часто: りょこう (путешествие), りょうり (кухня)."},
    {"id": "l16", "title": "Ёон с дакутэн", "subtitle": "gya · ja · bya · pya", "kana": ["ぎゃ", "ぎゅ", "ぎょ", "じゃ", "じゅ", "じょ", "びゃ", "びゅ", "びょ", "ぴゃ", "ぴゅ", "ぴょ"],
     "intro": "Озвонченные комбинации. じゃ/じゅ/じょ — самые частые: じゃあね (пока!), じゅう (десять)."},
    {"id": "l17", "title": "Сокуон и долгие гласные", "subtitle": "っ · ー", "kana": [],
     "intro": "Маленькое っ удваивает следующий согласный: きって (kitte) — пауза-толчок перед «т». "
              "Долгие гласные: あ+あ, い+い, う+う, え+い (ええ), お+う (おお) — гласная тянется в два раза дольше. "
              "Это меняет смысл: おばさん (тётя) ≠ おばあさん (бабушка)!",
     "rule_lesson": True},
]

LESSON_BY_ID = {l["id"]: l for l in LESSONS}
LESSON_ORDER = [l["id"] for l in LESSONS]

# Ловушки, доступные в уроке: обе каны группы уже введены к концу этого урока
def _kana_known_by(lesson_id):
    known = []
    for l in LESSONS:
        known.extend(l["kana"])
        if l["id"] == lesson_id:
            break
    return set(known)

def traps_for_lesson(lesson_id):
    """Группы-ловушки, в которых участвует кана этого урока (и все знаки уже знакомы)."""
    lesson = LESSON_BY_ID[lesson_id]
    known = _kana_known_by(lesson_id)
    new_kana = set(lesson["kana"])
    return [g for g in TRAP_GROUPS if set(g) <= known and set(g) & new_kana]

def kana_known_by(lesson_id):
    return _kana_known_by(lesson_id)
