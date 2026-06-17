/* MICHI — английский overlay КОНТЕНТА, часть 2 (фаза 3 локализации).

   Добивает оставшийся фактический контент: значения и примеры кандзи,
   грамматику (значения, объяснения, предостережения, примеры), интро уроков,
   заметки каны, ярлыки форм/регистров, вердикт SRS и составные вопросы.

   НЕ переведено осознанно: мнемоники кандзи/каны — это русскоязычная
   фонетическая игра слов («ХИТ собирает толпу ЛЮДЕЙ» цепляет чтение ひと через
   русские звуки); для англоязычного она бессмысленна, поэтому в EN-режиме
   мнемоники просто скрываются (а не переводятся). Подсказка SRS-вердикта (hint)
   и деривация каны — составные серверные строки, остаются на RU-фолбэке. */
"use strict";

Object.assign(EN, {
  // --- Ярлыки и служебные строки ---
  "он": "on", "кун": "kun",
  "не путайте с": "don't confuse with",
  "нейтр.": "neutral", "вежл.": "polite", "разг.": "casual", "формальн.": "formal",
  "следующий показ": "next review",
  "Эта карточка даётся тяжело — присмотритесь к подсказке":
    "This card is giving you trouble — take a look at the hint",
  // авто-оценка FSRS (вердикт повторения)
  "Снова": "Again", "Трудно": "Hard", "Хорошо": "Good", "Легко": "Easy",
  // интервал до следующего показа (считается на клиенте из next_due)
  "через минуту": "in a minute",
  "через {n} мин": "in {n} min",
  "через {n} ч": "in {n} h",
  "через {n} дн": "in {n} d",
  // составные вопросы упражнений (шаблон + переведённые подстановки)
  "«{x}» — запишите кандзи": "«{x}» — write it in kanji",
  "«{v}» → {f}": "«{v}» → {f}",
  // ярлыки форм глагола (verb_conjugation)
  "ます-форма": "ます form", "ました (прош.)": "ました (past)",
  "ません (отриц.)": "ません (negative)", "て-форма": "て form",
  // ru глаголов из verbs.py, которых нет в словаре N5
  "смотреть": "to watch, to look", "вставать": "to get up", "писать": "to write",
  "говорить": "to speak", "встречаться": "to meet",
  "слушать, спрашивать": "to listen, to ask",

  // --- Значения кандзи (показ в интро и «Словаре») ---
  "один": "one", "два": "two", "три": "three", "четыре": "four", "пять": "five",
  "шесть": "six", "семь": "seven", "восемь": "eight", "девять": "nine", "десять": "ten",
  "солнце; день": "sun; day", "луна; месяц": "moon; month", "огонь": "fire",
  "золото; деньги": "gold; money", "земля; почва": "earth; soil", "роща": "grove",
  "лес": "forest", "светлый; ясный": "bright; clear", "книга; основа": "book; origin",
  "середина; внутри": "middle; inside", "верх; над": "top; above", "низ; под": "bottom; below",
  "год": "year", "время; час": "time; hour", "минута; часть": "minute; part",
  "сейчас": "now", "что; сколько": "what; how many", "учиться; наука": "to study; learning",
  "школа (здание)": "school (building)", "раньше; впереди": "before; ahead",
  "жизнь; рождаться": "life; to be born", "отец": "father", "мать": "mother",
  "ребёнок": "child", "идти": "to go", "приходить": "to come",
  "смотреть; видеть": "to look; to see", "слушать; спрашивать": "to listen; to ask",
  "говорить; рассказ": "to speak; story", "есть; еда": "to eat; food",
  "высокий; дорогой": "tall; expensive", "дешёвый; спокойный": "cheap; calm",
  "много": "many", "длинный; глава": "long; chief", "восток": "east", "запад": "west",
  "юг": "south", "север": "north", "небо": "sky", "дух; воздух": "spirit; air",
  // компоненты кандзи
  "луна": "moon", "солнце": "sun", "глаз": "eye", "рот": "mouth", "женщина": "woman",

  // --- Слова-примеры кандзи (интро / word_kanji) ---
  "один (число)": "one (number)", "одна штука": "one item", "две штуки": "two items",
  "три штуки": "three items", "четыре штуки": "four items", "пять штук": "five items",
  "шесть штук": "six items", "семь штук": "seven items", "восемь штук": "eight items",
  "девять штук": "nine items", "солнце, день": "sun, day", "Япония": "Japan",
  "январь": "January", "вторник": "Tuesday", "среда": "Wednesday", "четверг": "Thursday",
  "золото": "gold", "деньги": "money", "земля, почва": "earth, soil", "суббота": "Saturday",
  "светлый, ясный": "bright, clear", "японец": "a Japanese person",
  "большой; крупный": "big; large", "начальная школа": "elementary school",
  "середина, внутри": "middle, inside", "Китай": "China", "верх, наверху": "top, above",
  "умелый, искусный": "skilled, good at", "низ, внизу": "bottom, below",
  "неумелый": "unskilled, bad at", "население": "population", "цель": "goal, purpose",
  "год; возраст": "year; age", "время; момент": "time; moment", "час (время)": "one o'clock",
  "минута (счётный)": "minute (counter)", "разделять": "to divide", "половина": "half",
  "половина, пополам": "half, in two", "который час": "what time", "учиться": "to study",
  "школа (в словах)": "school (in compounds)", "впереди; ранее": "ahead; earlier",
  "жить": "to live", "учащийся, студент": "student", "отец (свой)": "father (one's own)",
  "папа (вежливо)": "dad (polite)", "мать (своя)": "mother (one's own)",
  "мама (вежливо)": "mom (polite)", "мальчик": "boy", "девочка": "girl",
  "друг, приятель": "friend, buddy", "путешествие": "trip, travel",
  "следующий год": "next year", "смотреть, видеть": "to look, to see",
  "экскурсия (с осмотром)": "field trip", "газета": "newspaper",
  "говорить, беседовать": "to speak, to converse", "чтение книг": "reading books",
  "каллиграфия": "calligraphy", "столовая": "cafeteria", "старшая школа": "high school",
  "спокойствие": "peace of mind", "бывший в употреблении": "used, second-hand",
  "многочисленный": "numerous", "наверное": "probably", "директор фирмы": "company president",
  "Токио": "Tokyo", "западный выход": "west exit", "южный выход": "south exit",
  "северный выход": "north exit", "гора Фудзи": "Mt. Fuji", "ручей": "stream, brook",
  "дух, настроение": "spirit, mood", "бодрость, здоровье": "energy, health",
  "ливень": "downpour, heavy rain",

  // --- Грамматика: заголовки точек с русскими словами ---
  "из чего собран знак": "what a character is built from",
  "от (исходная точка)": "from (starting point)",
  "и-прилагательное": "い-adjective",
  "い-прилагательное": "い-adjective",
  "い-прил. прошедшее (～かった)": "い-adj. past (～かった)",
  "な-прилагательное": "な-adjective",
  "から (причина)": "から (reason)",

  // --- Грамматика: значения (gloss) ---
  "выделяет тему: «что касается A — …»": "marks the topic: “as for A …”",
  "вежливая связка «есть, является» в конце фразы": "polite copula “is / am / are” at the end of a sentence",
  "превращает фразу в вопрос": "turns a statement into a question",
  "принадлежность/связь: «B, относящееся к A»": "possession / link: “B that belongs to A”",
  "«тоже, также» — вместо は": "“too, also” — replaces は",
  "маркер прямого дополнения (что делают с N)": "direct-object marker (what the action is done to)",
  "место, где происходит действие": "the place where an action happens",
  "направление движения и точка времени": "direction of motion and a point in time",
  "признак в настоящем времени: «N — какое-то»": "a quality in the present: “N is such-and-such”",
  "признак в прошлом: «было каким-то»": "a quality in the past: “it was such-and-such”",
  "な-прилагательное перед существительным требует な": "a な-adjective takes な before a noun",
  "вежливое настоящее-будущее: «делаю / буду делать»": "polite present-future: “I do / will do”",
  "вежливое прошедшее: «сделал»": "polite past: “did”",
  "вежливое отрицание: «не делаю» / «не делал»": "polite negative: “don't do” / “didn't do”",
  "направление движения «в, к» (читается «э»)": "direction of motion “to, toward” (read “e”)",
  "«и» (соединяет существительные) и «с кем» (совместное действие)":
    "“and” (joins nouns) and “with whom” (doing something together)",
  "«это / то / вон то» — предмет-местоимение": "“this / that / that over there” — a stand-alone pronoun",
  "«этот / тот / вон тот» перед существительным": "“this / that / that over there” before a noun",
  "«здесь / там / вон там» — место": "“here / there / over there” — a place",
  "маркер подлежащего (вводит новое, отвечает «что/кто»)":
    "subject marker (introduces something new, answers “what / who”)",
  "«есть, имеется» — о неодушевлённых предметах": "“there is / exists” — for inanimate things",
  "«есть, находится» — о людях и животных": "“there is / exists” — for people and animals",
  "«хочу (сделать)» — желание говорящего": "“want to (do)” — the speaker's wish",
  "«давай(те) сделаем» — приглашение к совместному действию":
    "“let's do it” — an invitation to do something together",
  "«не сделать ли нам…?» — вежливое приглашение": "“shall we …?” — a polite invitation",
  "«потому что, так как» — причина": "“because, since” — a reason",
  "«чем» — вторая часть сравнения": "“than” — the second part of a comparison",
  "«A более …, чем B» — выделяет, что́ превосходит":
    "“A is more … than B” — highlights what comes out on top",
  "«самый …» — превосходная степень": "“the most …” — the superlative",
  "объект симпатии или умения берёт が": "the thing you like or are good at takes が",
  "вежливая просьба «сделайте, пожалуйста»": "a polite request “please do …”",
  "длящееся действие «делаю (прямо сейчас)»": "an ongoing action “I am doing (right now)”",
  "разрешение «можно (сделать)»": "permission “you may (do)”",
  "запрет «нельзя (делать)»": "prohibition “you must not (do)”",
  "простое (casual) отрицание «не делаю»": "plain (casual) negative “don't do”",
  "простое (casual) прошедшее «сделал»": "plain (casual) past “did”",
  "предположение «наверное, вероятно»": "a guess “probably, likely”",
  "«…ведь, не правда ли?» — ищет согласия": "“…right? isn't it?” — seeks agreement",
  "«…же! вот!» — сообщает новое, подчёркивает": "“…you know! look!” — gives new info, emphasizes",
  "«и (среди прочего)» — неполное перечисление": "“and (among others)” — an incomplete list",

  // --- Грамматика: предостережения (caution) ---
  "は читается «ва», но никогда не пишется как わ.": "は is read “wa”, but is never written as わ.",
  "です ставится в самом конце; перед ним — существительное или な-прилагательное.":
    "です goes at the very end; before it comes a noun or a な-adjective.",
  "か ставится после です/ます, в самом конце.": "か goes after です/ます, at the very end.",
  "Порядок обратный русскому: владелец идёт перед の, предмет — после.":
    "The order is owner-first: the owner comes before の, the thing after it.",
  "も ставится вместо は, а не вместе с ней.": "も replaces は, it is not used together with it.",
  "を пишется отдельным знаком を, но читается как お «о».":
    "を is written with its own character を, but read like お “o”.",
  "Не путать で (место действия) и に (направление/нахождение).":
    "Don't confuse で (place of action) with に (direction / location).",
  "С действием на месте (есть, пить) нужна で, а не に.":
    "For an action done in place (eat, drink) you need で, not に.",
  "い-прилагательное уже само вежливо; です не меняет его окончание — い не убирают.":
    "An い-adjective is already polite on its own; です doesn't change its ending — the い stays.",
  "Не «おいしいでした» — у い-прилагательных прошлое в самом слове: ～かった, а です остаётся в настоящей форме.":
    "Not “おいしいでした” — an い-adjective carries its past in the word itself (～かった), while です stays in its present form.",
  "な ставится между な-прилагательным и существительным, но не перед です.":
    "な goes between a な-adjective and a noun, but not before です.",
  "ます ставится в самом конце вместо словарного окончания; перед ним идёт основа на -i.":
    "ます goes at the very end instead of the dictionary ending; before it comes the -i stem.",
  "Прошедшее берётся из ます-формы (たべました), а не из словарной (не «たべるでした»).":
    "The past comes from the ます form (たべました), not from the dictionary form (not “たべるでした”).",
  "ません — настоящее «не делаю»; для прошлого «не делал» нужно ませんでした.":
    "ません is the present “don't do”; for the past “didn't do” you need ませんでした.",
  "Частица へ читается «э»; пишется знаком へ, но не へ→え.":
    "The particle へ is read “e”; it is written with へ, not changed to え.",
  "と перечисляет полный список; для «и так далее / выбор» нужны другие частицы.":
    "と lists a complete set; for “and so on / choice” you need other particles.",
  "これ/それ/あれ заменяют сам предмет и стоят отдельно; перед существительным нужны この/その/あの.":
    "これ/それ/あれ stand in for the thing itself and stand alone; before a noun you need この/その/あの.",
  "Нельзя сказать «これほん»: перед существительным — только この, а これ стоит само по себе.":
    "You can't say “これほん”: before a noun use only この, while これ stands on its own.",
  "Вопрос «где?» — どこ из той же серии こ・そ・あ・ど.": "“Where?” is どこ, from the same こ・そ・あ・ど series.",
  "С глаголами существования ある/いる действующее лицо берёт が, а не を.":
    "With the existence verbs ある/いる the subject takes が, not を.",
  "あります — только для предметов; для людей и животных нужен глагол います.":
    "あります is for objects only; for people and animals you need the verb います.",
  "Для людей — います, не あります: «せんせいがあります» — ошибка.":
    "For people use います, not あります: “せんせいがあります” is wrong.",
  "たい присоединяется к основе на -i (のみたい), а не к словарной форме (не «のむたい»).":
    "たい attaches to the -i stem (のみたい), not to the dictionary form (not “のむたい”).",
  "ましょう — призыв «давай», а не простое будущее; для «буду делать» нужна форма ます.":
    "ましょう is the call “let's”, not a plain future; for “I will do” you need the ます form.",
  "Это приглашение, а не обычный вопрос-отрицание: интонация и смысл — «давайте вместе?».":
    "This is an invitation, not an ordinary negative question: the intonation and meaning are “shall we, together?”.",
  "Причинная から идёт после целого сказуемого; не путать с から «от/из» (исходная точка).":
    "The causal から goes after the whole predicate; don't confuse it with から “from” (a starting point).",
  "より стоит сразу после слова-эталона (B より), а не в конце фразы.":
    "より comes right after the benchmark word (B より), not at the end of the sentence.",
  "のほうが навешивается на превосходящий предмет; эталон сравнения берёт より.":
    "のほうが is attached to the item that wins; the thing it's compared against takes より.",
  "いちばん стоит перед прилагательным, а не после него.": "いちばん goes before the adjective, not after it.",
  "«Люблю японский» — にほんごがすき, через が, не を.":
    "“I like Japanese” is にほんごがすき, with が, not を.",
  "Перед ください нужна именно て-форма (みて), а не словарная (не «みるください»).":
    "Before ください you need the て form specifically (みて), not the dictionary form (not “みるください”).",
  "Это процесс «делаю сейчас»; простое ます — обычное/будущее действие.":
    "This is the ongoing “doing now”; plain ます is a habitual / future action.",
  "Нужна て-форма + もいい; «たべるもいい» — ошибка.": "You need the て form + もいい; “たべるもいい” is wrong.",
  "Запрет строится от て-формы + はいけません; словарная форма тут не годится.":
    "The prohibition is built from the て form + はいけません; the dictionary form doesn't work here.",
  "ない — простая форма; в вежливой речи ей соответствует ません.":
    "ない is the plain form; in polite speech it corresponds to ません.",
  "た-форма — простое прошлое; вежливый эквивалент — ました.":
    "The た form is the plain past; the polite equivalent is ました.",
  "でしょう — догадка «наверное», а です — утверждение факта.":
    "でしょう is a guess “probably”, while です states a fact.",
  "ね рассчитывает на согласие; よ — наоборот, сообщает новое собеседнику.":
    "ね expects agreement; よ, on the contrary, tells the listener something new.",
  "よ сообщает новое; ね — ищет согласия о том, что оба и так знают.":
    "よ delivers new info; ね seeks agreement about something both already know.",
  "と — закрытый список «ровно эти»; や — открытый «эти и другие».":
    "と is a closed list “exactly these”; や is open “these and others”.",

  // --- Грамматика: объяснения (explanation; **жирный** и японский сохранены) ---
  "Частица **は** ставится после темы предложения — того, о чём идёт речь. Читается как «ва», хотя пишется знаком は.":
    "The particle **は** goes after the topic of the sentence — what is being talked about. It is read “wa”, though written with the character は.",
  "Схема **A は B です** — «A есть B»: わたし**は**がくせいです — «Я (что касается меня) — студент».":
    "The pattern **A は B です** means “A is B”: わたし**は**がくせいです — “I (as for me) am a student”.",
  "**です** — вежливая связка в конце предложения, аналог «есть/является». Делает высказывание нейтрально-вежливым.":
    "**です** is the polite copula at the end of a sentence, like “is / am / are”. It makes the statement neutrally polite.",
  "Прошедшее время — **でした** («был»). Простая (грубоватая) форма — **だ**.":
    "The past tense is **でした** (“was”). The plain (blunt) form is **だ**.",
  "Частица **か** в конце предложения делает его вопросом — знак вопроса не нужен.":
    "The particle **か** at the end of a sentence turns it into a question — no question mark is needed.",
  "がくせいです → がくせいです**か** — «(Вы) студент?».": "がくせいです → がくせいです**か** — “Are (you) a student?”.",
  "**の** соединяет два существительных: **A の B** — «B, принадлежащее A» или «A-ское B».":
    "**の** joins two nouns: **A の B** — “B belonging to A” or “A's B”.",
  "わたし**の**ともだち — «мой друг»; せんせい**の**なまえ — «имя учителя».":
    "わたし**の**ともだち — “my friend”; せんせい**の**なまえ — “the teacher's name”.",
  "**も** заменяет は и значит «тоже»: わたし**も**がくせいです — «Я тоже студент».":
    "**も** replaces は and means “too”: わたし**も**がくせいです — “I am a student too”.",
  "も вытесняет は: нельзя сказать はも — только も.": "も pushes out は: you can't say はも — only も.",
  "**を** (читается «о») отмечает прямое дополнение — то, на что направлено действие: ごはん**を**たべる — «есть рис».":
    "**を** (read “o”) marks the direct object — what the action is aimed at: ごはん**を**たべる — “to eat rice”.",
  "を используется почти только с этой частицей; собственного слова «о» нет.":
    "を is used almost only as this particle; there is no separate word “o”.",
  "**で** указывает место действия: レストラン**で**たべる — «есть в ресторане».":
    "**で** marks the place of an action: レストラン**で**たべる — “to eat at a restaurant”.",
  "Сравните с に: で — где что-то *делают*, に — куда *направлены* или где *находятся*.":
    "Compare with に: で is where something is *done*, に is where you are *headed* or where you *are*.",
  "**に** показывает направление с глаголами движения: うち**に**いく — «идти домой».":
    "**に** shows direction with motion verbs: うち**に**いく — “to go home”.",
  "Та же に отмечает точку во времени: あさ**に**おきる — «вставать утром».":
    "The same に marks a point in time: あさ**に**おきる — “to get up in the morning”.",
  "**い-прилагательные** оканчиваются на い и сами по себе значат «такой-то»: おいし**い** — «вкусный», あま**い** — «сладкий».":
    "**い-adjectives** end in い and mean “such-and-such” on their own: おいし**い** — “tasty”, あま**い** — “sweet”.",
  "В сказуемом い-прилагательное ставят **перед です**, и い при этом сохраняется: ごはん**は**おいし**い**です — «Рис вкусный».":
    "As a predicate, the い-adjective goes **before です**, and the い is kept: ごはん**は**おいし**い**です — “The rice is tasty”.",
  "Прошедшее время い-прилагательного: убираем い и добавляем **かった**. おいし**い** → おいし**かった** — «был вкусным».":
    "Past tense of an い-adjective: drop the い and add **かった**. おいし**い** → おいし**かった** — “was tasty”.",
  "Вежливость добавляет です **после** かった: ごはん**は**おいし**かった**です — «Рис был вкусным».":
    "Politeness adds です **after** かった: ごはん**は**おいし**かった**です — “The rice was tasty”.",
  "**な-прилагательные** (げんき, すき, だいじょうぶ) перед существительным присоединяют **な**: げんき**な**ひと — «бодрый человек».":
    "**な-adjectives** (げんき, すき, だいじょうぶ) take **な** before a noun: げんき**な**ひと — “an energetic person”.",
  "В сказуемом な не нужна — там просто です: ひと**は**げんきです. な появляется только когда прилагательное стоит **перед существительным**.":
    "As a predicate な is not needed — just です: ひと**は**げんきです. な appears only when the adjective stands **before a noun**.",
  "**ます** — вежливая форма глагола в настоящем-будущем времени. たべる → たべ**ます**, のむ → のみ**ます**, いく → いき**ます**.":
    "**ます** is the polite verb form for the present-future. たべる → たべ**ます**, のむ → のみ**ます**, いく → いき**ます**.",
  "Одна форма покрывает и «ем сейчас», и «буду есть»: ごはんをたべ**ます** — «ем / буду есть рис».":
    "One form covers both “I eat now” and “I will eat”: ごはんをたべ**ます** — “I eat / will eat rice”.",
  "Прошедшее время ます-формы — **ました**. たべ**ます** → たべ**ました** («поел»), のみ**ます** → のみ**ました** («попил»).":
    "The past of the ます form is **ました**. たべ**ます** → たべ**ました** (“ate”), のみ**ます** → のみ**ました** (“drank”).",
  "Меняется только окончание ます → ました, основа глагола та же: ほんをよみ**ました** — «прочитал книгу».":
    "Only the ending changes, ます → ました; the verb stem stays the same: ほんをよみ**ました** — “read a book”.",
  "Отрицание ます-формы — **ません**: たべ**ます** → たべ**ません** «не ем». Это настоящее-будущее.":
    "The negative of the ます form is **ません**: たべ**ます** → たべ**ません** “don't eat”. This is present-future.",
  "Прошедшее отрицание — **ませんでした**: たべ**ませんでした** «не ел». Просто добавляем でした к ません.":
    "The past negative is **ませんでした**: たべ**ませんでした** “didn't eat”. Just add でした to ません.",
  "**へ** отмечает направление движения — «в сторону, к»: うち**へ**いきます — «иду домой». В роли частицы читается «э», не «хэ».":
    "**へ** marks direction of motion — “toward, to”: うち**へ**いきます — “I'm going home”. As a particle it is read “e”, not “he”.",
  "С глаголами движения へ и に близки; へ подчёркивает направление как таковое, に — конечную точку.":
    "With motion verbs へ and に are close; へ stresses the direction itself, に the destination.",
  "**と** соединяет существительные в закрытый список «и»: にく**と**さかな — «мясо и рыба».":
    "**と** joins nouns into a closed “and” list: にく**と**さかな — “meat and fish”.",
  "С людьми と значит «вместе с»: ともだち**と**たべます — «ем вместе с другом».":
    "With people と means “together with”: ともだち**と**たべます — “I eat with a friend”.",
  "**これ** — «это» (рядом со мной), **それ** — «то» (рядом с собеседником), **あれ** — «вон то» (далеко от обоих).":
    "**これ** — “this” (near me), **それ** — “that” (near the listener), **あれ** — “that over there” (far from both).",
  "Это самостоятельные слова-предметы, после них идёт は: **これ**はほんです — «Это книга».":
    "These are stand-alone pronouns, followed by は: **これ**はほんです — “This is a book”.",
  "**この/その/あの** ставятся **перед существительным**: **この**ほん — «эта книга», **その**かばん — «та сумка».":
    "**この/その/あの** go **before a noun**: **この**ほん — “this book”, **その**かばん — “that bag”.",
  "Различие по расстоянию то же, что у これ/それ/あれ: こ — рядом со мной, そ — рядом с тобой, あ — далеко.":
    "The distance distinction is the same as これ/それ/あれ: こ — near me, そ — near you, あ — far away.",
  "**ここ** — «здесь», **そこ** — «там (у тебя)», **あそこ** — «вон там (далеко)».":
    "**ここ** — “here”, **そこ** — “there (by you)”, **あそこ** — “over there (far)”.",
  "Это слова-места: **ここ**はだいどころです — «Здесь — кухня».":
    "These are place words: **ここ**はだいどころです — “Here is the kitchen”.",
  "**が** отмечает подлежащее, когда вводят что-то новое или отвечают на вопрос «что есть? кто?»: ほん**が**あります — «есть книга».":
    "**が** marks the subject when introducing something new or answering “what is there? who?”: ほん**が**あります — “there is a book”.",
  "は выделяет тему (уже известное), が — само подлежащее (новое в фокусе).":
    "は highlights the topic (already known), が the subject itself (the new thing in focus).",
  "**あります** — «есть, имеется» о **неодушевлённых** предметах (вещи, растения): つくえ**が**あります — «есть стол».":
    "**あります** — “there is / exists” for **inanimate** things (objects, plants): つくえ**が**あります — “there is a desk”.",
  "Отрицание — **ありません** «нет, не имеется».": "The negative is **ありません** “there isn't / none”.",
  "**います** — «есть, находится» о **одушевлённых** (люди, животные): せんせい**が**います — «учитель здесь».":
    "**います** — “there is / exists” for **animate** beings (people, animals): せんせい**が**います — “the teacher is here”.",
  "Отрицание — **いません** «нет, отсутствует».": "The negative is **いません** “isn't here / absent”.",
  "**～たい** выражает желание «хочу сделать». Берём ます-основу и добавляем たい: たべ**ます** → たべ**たい** — «хочу есть».":
    "**～たい** expresses the wish “want to do”. Take the ます stem and add たい: たべ**ます** → たべ**たい** — “want to eat”.",
  "Вежливо добавляют です: みず**を**のみ**たい**です — «Хочу выпить воды».":
    "To be polite add です: みず**を**のみ**たい**です — “I want to drink water”.",
  "**～ましょう** — «давайте сделаем вместе». Заменяет ます на ましょう: たべ**ます** → たべ**ましょう** — «давайте поедим».":
    "**～ましょう** — “let's do it together”. Replaces ます with ましょう: たべ**ます** → たべ**ましょう** — “let's eat”.",
  "Часто отвечает на приглашение или предлагает что-то сделать сообща.":
    "It often answers an invitation or proposes doing something together.",
  "**～ませんか** — вежливое приглашение «не сделаете ли? давайте?». Форма ません + か: のみ**ませんか** — «не выпьете ли?».":
    "**～ませんか** is a polite invitation “won't you? shall we?”. The ません form + か: のみ**ませんか** — “won't you have a drink?”.",
  "Мягче, чем ましょう: оставляет собеседнику выбор отказаться.":
    "Softer than ましょう: it leaves the listener room to decline.",
  "**から** после сказуемого значит «потому что»: причина идёт **перед** から, следствие — после.":
    "**から** after a predicate means “because”: the reason comes **before** から, the result after it.",
  "やすい**から**かいます — «Куплю, потому что дёшево».": "やすい**から**かいます — “I'll buy it because it's cheap”.",
  "**より** значит «чем» и ставится после того, с чем сравнивают: A は B **より** たかい — «A дороже, чем B».":
    "**より** means “than” and goes after what is being compared: A は B **より** たかい — “A is more expensive than B”.",
  "Конструкция: тема は + предмет-эталон より + прилагательное.":
    "Pattern: topic は + benchmark item より + adjective.",
  "**のほうが** подчёркивает предмет, который «больше/лучше»: にく**のほうが**たかいです — «Мясо-то дороже».":
    "**のほうが** highlights the item that is “more / better”: にく**のほうが**たかいです — “Meat is the more expensive one”.",
  "Часто в паре с より: にくのほうがさかな**より**たかいです.": "Often paired with より: にくのほうがさかな**より**たかいです.",
  "**いちばん** перед прилагательным значит «самый»: これ**が**いちばんたかいです — «Это самое дорогое».":
    "**いちばん** before an adjective means “the most”: これ**が**いちばんたかいです — “This is the most expensive”.",
  "Буквально «номер один»; ставится прямо перед признаком.":
    "Literally “number one”; it goes right before the quality.",
  "С すき «нравится» и じょうず «умелый» объект отмечается **が**, а не を: にほんご**が**すきです — «Нравится японский».":
    "With すき “like” and じょうず “good at”, the object is marked with **が**, not を: にほんご**が**すきです — “I like Japanese”.",
  "По-русски это «прямое дополнение», но в японском — が.":
    "In English this feels like an object, but in Japanese it is が.",
  "**～てください** — вежливая просьба. Берём て-форму глагола и добавляем ください: み**て**ください — «посмотрите, пожалуйста».":
    "**～てください** is a polite request. Take the て form and add ください: み**て**ください — “please look”.",
  "て-форма: たべる→たべて, よむ→よんで, みる→みて.": "The て form: たべる→たべて, よむ→よんで, みる→みて.",
  "**～ています** — действие в процессе: ほんをよ**んでいます** — «читаю книгу (сейчас)».":
    "**～ています** — an action in progress: ほんをよ**んでいます** — “I'm reading a book (now)”.",
  "Образуется: て-форма + います. Отрицание — ～ていません.":
    "Formed as: て form + います. The negative is ～ていません.",
  "**～てもいいです** — разрешение «можно»: たべ**てもいいです** — «можно есть».":
    "**～てもいいです** — permission “you may”: たべ**てもいいです** — “you may eat”.",
  "Часто как вопрос-просьба о разрешении: たべてもいいですか — «Можно поесть?».":
    "Often as a question asking permission: たべてもいいですか — “May I eat?”.",
  "**～てはいけません** — запрет «нельзя»: ここでたべ**てはいけません** — «здесь нельзя есть».":
    "**～てはいけません** — prohibition “you must not”: ここでたべ**てはいけません** — “you must not eat here”.",
  "Образуется: て-форма + はいけません. Противоположно разрешению ～てもいい.":
    "Formed as: て form + はいけません. The opposite of the permission ～てもいい.",
  "**～ない** — простое отрицание глагола: のむ→の**まない** «не пью», たべる→たべ**ない** «не ем».":
    "**～ない** — the plain negative of a verb: のむ→の**まない** “don't drink”, たべる→たべ**ない** “don't eat”.",
  "Это casual-форма, аналог вежливого ません. Для друзей и заметок.":
    "This is the casual form, equivalent to polite ません. For friends and notes.",
  "**～た** — простое прошедшее: たべる→たべ**た** «поел», よむ→よ**んだ** «прочитал».":
    "**～た** — the plain past: たべる→たべ**た** “ate”, よむ→よ**んだ** “read”.",
  "Casual-аналог вежливого ました. Образуется как て-форма, но с -た/-だ.":
    "The casual counterpart of polite ました. Formed like the て form, but with -た/-だ.",
  "**でしょう** выражает предположение «наверное»: あした**は**さむい**でしょう** — «Завтра, наверное, будет холодно».":
    "**でしょう** expresses a guess “probably”: あした**は**さむい**でしょう** — “Tomorrow will probably be cold”.",
  "Мягче и менее категорично, чем です.": "Softer and less categorical than です.",
  "**ね** в конце фразы ищет согласия собеседника, «ведь, да?»: おいしい**です**ね — «Вкусно, правда?».":
    "**ね** at the end of a sentence seeks the listener's agreement, “right?”: おいしい**です**ね — “Tasty, isn't it?”.",
  "Смягчает речь и показывает, что вы разделяете чувство.":
    "It softens speech and shows that you share the feeling.",
  "**よ** в конце фразы подаёт информацию как новость для собеседника, с нажимом: この**ほん**はおもしろいです**よ** — «Эта книга интересная, правда (говорю тебе)!».":
    "**よ** at the end presents information as news to the listener, with emphasis: この**ほん**はおもしろいです**よ** — “This book is interesting, I'm telling you!”.",
  "Сообщает то, чего собеседник, возможно, не знал.": "It conveys something the listener may not have known.",
  "**や** перечисляет примеры неполно, «и…, и… (и так далее)»: にく**や**さかな — «мясо, рыба и тому подобное».":
    "**や** lists examples incompletely, “… and … (and so on)”: にく**や**さかな — “meat, fish and the like”.",
  "В отличие от と (полный список), や намекает, что есть и другое.":
    "Unlike と (a complete list), や hints that there is more.",

  // --- Грамматика: переводы примеров (ex.ru) ---
  "Друг — учитель.": "My friend is a teacher.",
  "Я в порядке (бодр).": "I'm fine (energetic).",
  "Я студент.": "I'm a student.",
  "Сегодня воскресенье.": "Today is Sunday.",
  "Я учитель.": "I'm a teacher.",
  "Вы студент?": "Are you a student?",
  "Как ты? (бодр?)": "How are you? (doing well?)",
  "Это учитель?": "Is this the teacher?",
  "имя учителя": "the teacher's name",
  "мой друг": "my friend",
  "моё имя": "my name",
  "Друг тоже в порядке.": "My friend is fine too.",
  "Я тоже студент.": "I'm a student too.",
  "Я тоже учитель.": "I'm a teacher too.",
  "есть рис (еду)": "to eat rice (food)",
  "пить воду": "to drink water",
  "читать книгу": "to read a book",
  "есть в ресторане": "to eat at a restaurant",
  "пить дома": "to drink at home",
  "спать в комнате": "to sleep in the room",
  "вставать утром": "to get up in the morning",
  "идти в ресторан": "to go to a restaurant",
  "идти домой": "to go home",
  "Мясо острое.": "The meat is spicy.",
  "Овощи сладкие.": "The vegetables are sweet.",
  "Рис вкусный.": "The rice is tasty.",
  "Рис был вкусным.": "The rice was tasty.",
  "Рыба была сладковатой.": "The fish was a bit sweet.",
  "бодрый человек": "an energetic person",
  "любимый напиток": "a favorite drink",
  "Ем рис.": "I eat rice.",
  "Пью воду.": "I drink water.",
  "Читаю книгу.": "I read a book.",
  "Поел рис.": "I ate the rice.",
  "Попил воды.": "I drank some water.",
  "Не ем мясо.": "I don't eat meat.",
  "Не пил сакэ.": "I didn't drink sake.",
  "Иду в комнату.": "I'm going to the room.",
  "Иду в ресторан.": "I'm going to the restaurant.",
  "Иду домой.": "I'm going home.",
  "Ем вместе с другом.": "I eat with a friend.",
  "Иду вместе с учителем.": "I'm going with the teacher.",
  "мясо и рыба": "meat and fish",
  "Вон то — часы.": "That over there is a clock.",
  "То — зонт.": "That is an umbrella.",
  "Это книга.": "This is a book.",
  "Вон тот человек — учитель.": "That person over there is a teacher.",
  "Та сумка — учителя.": "That bag is the teacher's.",
  "Эта книга моя.": "This book is mine.",
  "Вон там ресторан.": "Over there is a restaurant.",
  "Здесь кухня.": "Here is the kitchen.",
  "Там туалет.": "The toilet is there.",
  "Есть вода.": "There is water.",
  "Есть друг.": "There is a friend.",
  "Есть книга.": "There is a book.",
  "Есть стол.": "There is a desk.",
  "Компьютера нет.": "There is no computer.",
  "Друга нет.": "The friend isn't here.",
  "Учитель здесь.": "The teacher is here.",
  "Хочу вернуться домой.": "I want to go back home.",
  "Хочу выпить воды.": "I want to drink some water.",
  "Хочу поесть.": "I want to eat.",
  "Давайте поедим.": "Let's eat.",
  "Давайте пойдём в ресторан.": "Let's go to a restaurant.",
  "Не выпьете ли чаю?": "Won't you have some tea?",
  "Не посмотреть ли телевизор?": "Shall we watch some TV?",
  "Куплю, потому что дёшево.": "I'll buy it because it's cheap.",
  "Отдохну, потому что занят.": "I'll rest because I'm busy.",
  "Мясо дороже рыбы.": "Meat is more expensive than fish.",
  "Сегодня жарче, чем вчера.": "Today is hotter than yesterday.",
  "Маленькая комната тише.": "A small room is quieter.",
  "Мясо дороже.": "Meat is the more expensive one.",
  "Эта книга самая дешёвая.": "This book is the cheapest.",
  "Это самое дорогое.": "This is the most expensive.",
  "Нравится рыба.": "I like fish.",
  "Нравится японский.": "I like Japanese.",
  "Подойдите сюда, пожалуйста.": "Please come here.",
  "Прочитайте книгу, пожалуйста.": "Please read the book.",
  "Ем (сейчас).": "I'm eating (now).",
  "Смотрю телевизор.": "I'm watching TV.",
  "Здесь можно отдохнуть.": "You may rest here.",
  "Можно пить воду.": "You may drink water.",
  "Здесь нельзя пить.": "You must not drink here.",
  "Эту книгу нельзя читать.": "You must not read this book.",
  "Поел.": "I ate.",
  "Прочитал книгу.": "I read the book.",
  "Завтра, наверное, холодно.": "Tomorrow will probably be cold.",
  "Тот человек, наверное, учитель.": "That person is probably a teacher.",
  "Вкусно, правда?": "Tasty, isn't it?",
  "Сегодня жарко, да?": "It's hot today, isn't it?",
  "Вон то дёшево, имей в виду!": "That one is cheap, just so you know!",
  "Эта вода вкусная, между прочим!": "This water is tasty, by the way!",
  "книги, сумки и прочее": "books, bags and so on",
  "мясо, рыба и тому подобное": "meat, fish and the like",

  // --- Заметки каны ---
  "Редкий знак: тот же звук, что じ. Встречается в はなぢ (кровь из носа).":
    "A rare character: same sound as じ. Appears in はなぢ (nosebleed).",
  "Редкий знак: тот же звук, что ず. Встречается в つづく (продолжаться).":
    "A rare character: same sound as ず. Appears in つづく (to continue).",
  "В современных текстах частица を пишется хираганой; ヲ встречается в основном в старых играх и вывесках.":
    "In modern text the particle を is written in hiragana; ヲ mostly shows up in old games and signs.",
  "Редкий знак: тот же звук, что ジ.": "A rare character: same sound as ジ.",
  "Редкий знак: тот же звук, что ズ.": "A rare character: same sound as ズ.",
});

// --- Вступительные тексты уроков (intro) ---
Object.assign(EN, {
  "Первые пять знаков хираганы — пять гласных японского языка. Всё остальное строится на них.":
    "The first five hiragana — the five vowels of Japanese. Everything else is built on them.",
  "Согласная К + гласные. С этого урока вы уже читаете настоящие слова!":
    "The consonant K + vowels. From this lesson on you can already read real words!",
  "Внимание на исключение: し читается «ши» (shi), а не «si».":
    "Watch the exception: し is read “shi”, not “si”.",
  "Два исключения: ち = «чи» (chi), つ = «цу» (tsu).":
    "Two exceptions: ち = “chi”, つ = “tsu”.",
  "Ряд Н. Здесь живут коварные близнецы ぬ и ね — приглядитесь к ним.":
    "The N row. The tricky twins ぬ and ね live here — look at them closely.",
  "ふ — лёгкое «фу» (между «фу» и «ху»). Знак は как частица читается «ва».":
    "ふ is a soft “fu” (between “fu” and “hu”). The character は, used as a particle, is read “wa”.",
  "Ряд М. Сравните め с ぬ из ряда な — частая путаница.":
    "The M row. Compare め with ぬ from the な row — a common mix-up.",
  "Только три знака. Позже их маленькие версии (ゃゅょ) образуют комбинации вроде きょ.":
    "Only three characters. Later their small versions (ゃゅょ) form combinations like きょ.",
  "Японский «Р» — один удар языка, между русскими «р» и «л».":
    "The Japanese “R” is a single tap of the tongue, between an English “r” and “l”.",
  "Последние знаки годзюон! を используется только как частица. ん — единственный одиночный согласный. Базовая хирагана пройдена!":
    "The last gojūon characters! を is used only as a particle. ん is the only standalone consonant. Basic hiragana is done!",
  "Две чёрточки (゛дакутэн) озвончают согласный: か(ka) → が(ga), さ(sa) → ざ(za). Новых форм учить не надо — только правило!":
    "Two strokes (゛ dakuten) voice the consonant: か(ka) → が(ga), さ(sa) → ざ(za). No new shapes to learn — just the rule!",
  "た → だ (da), は → ば (ba). Знаки ぢ и づ редкие — звучат как じ и ず.":
    "た → だ (da), は → ば (ba). The characters ぢ and づ are rare — they sound like じ and ず.",
  "Кружок (゜хандакутэн) превращает Х в П: は(ha) → ぱ(pa). Различайте триаду は/ば/ぱ!":
    "A small circle (゜ handakuten) turns H into P: は(ha) → ぱ(pa). Tell the trio は/ば/ぱ apart!",
  "Знак ряда И + маленькие ゃゅょ = один слог: き+ゃ = きゃ (кя). Важно: きや (кия, 2 слога) ≠ きゃ (кя, 1 слог) — смотрите на размер!":
    "An i-row character + small ゃゅょ = one syllable: き+ゃ = きゃ (kya). Important: きや (kiya, 2 syllables) ≠ きゃ (kya, 1 syllable) — watch the size!",
  "Оставшиеся базовые комбинации ёон. りょ встречается очень часто: りょこう (путешествие), りょうり (кухня).":
    "The remaining basic yōon combinations. りょ is very common: りょこう (travel), りょうり (cooking).",
  "Озвонченные комбинации. じゃ/じゅ/じょ — самые частые: じゃあね (пока!), じゅう (десять).":
    "Voiced combinations. じゃ/じゅ/じょ are the most common: じゃあね (bye!), じゅう (ten).",
  "Маленькое っ удваивает следующий согласный: きって (kitte) — пауза-толчок перед «т». Долгие гласные: あ+あ, い+い, う+う, え+い (ええ), お+う (おお) — гласная тянется в два раза дольше. Это меняет смысл: おばさん (тётя) ≠ おばあさん (бабушка)!":
    "A small っ doubles the next consonant: きって (kitte) — a held pause before the “t”. Long vowels: あ+あ, い+い, う+う, え+い (ええ), お+う (おお) — the vowel is held twice as long. It changes meaning: おばさん (aunt) ≠ おばあさん (grandmother)!",
  "Катакана — вторая азбука: ей пишут заимствования (コーヒー — кофе), иностранные имена и названия. Звуки те же, что в хирагане, — учим только новые формы. Сразу правило долготы: чёрточка ー тянет гласную: カー (kā) — машина.":
    "Katakana is the second syllabary: it writes loanwords (コーヒー — coffee), foreign names and titles. The sounds are the same as hiragana — only the shapes are new. The length rule right away: the bar ー stretches a vowel: カー (kā) — car.",
  "カ — почти хирагана か, а キ — верх от き. С этого урока вы читаете настоящие гайрайго: ケーキ — торт!":
    "カ is almost hiragana か, and キ is the top of き. From this lesson you can read real loanwords: ケーキ — cake!",
  "Здесь живёт первая пара «катакана-ада»: シ (черты лежат) и ソ (черта стоит). Запомните направление взмаха!":
    "The first “katakana hell” pair lives here: シ (strokes lie flat) and ソ (the stroke stands up). Remember the stroke direction!",
  "Вторая пара ада: ツ (черты стоят, взмах сверху вниз) против シ (черты лежат, взмах снизу вверх).":
    "The second hell pair: ツ (strokes stand, brushed top-down) versus シ (strokes lie flat, brushed bottom-up).",
  "ニ — буквально кандзи 二 «два». ノ — одна косая черта.":
    "ニ is literally the kanji 二 “two”. ノ is a single diagonal stroke.",
  "ヘ почти не отличается от хираганы へ. Награда урока — слово コーヒー (кофе)!":
    "ヘ is almost the same as hiragana へ. The lesson's reward is the word コーヒー (coffee)!",
  "ミ — три штриха. Сравнивайте マ с ア — частая путаница новичков.":
    "ミ is three strokes. Compare マ with ア — a common beginner mix-up.",
  "ヤ — копия хираганы や. ヨ — грабли зубьями влево (не путайте с ユ).":
    "ヤ is a copy of hiragana や. ヨ is a rake with teeth to the left (don't confuse it with ユ).",
  "リ — копия хираганы り. После этого урока вам откроются ホテル, ミルク и カメラ.":
    "リ is a copy of hiragana り. After this lesson you'll unlock ホテル, ミルク and カメラ.",
  "Финал базовой катаканы! Третья пара ада: ン (взмах снизу вверх) против ソ (сверху вниз). ヲ почти не используется — но узнавать его нужно.":
    "The end of basic katakana! The third hell pair: ン (brushed bottom-up) versus ソ (top-down). ヲ is almost never used — but you should recognize it.",
  "Те же две чёрточки ゛, что в хирагане: カ → ガ, サ → ザ. Новых форм нет — только правило.":
    "The same two strokes ゛ as in hiragana: カ → ガ, サ → ザ. No new shapes — just the rule.",
  "タ → ダ, ハ → バ. Знаки ヂ и ヅ так же редки, как их родственники в хирагане.":
    "タ → ダ, ハ → バ. The characters ヂ and ヅ are as rare as their hiragana relatives.",
  "Кружок ゜: ハ → パ. В гайрайго звук «п» очень частый: パン, パスタ, パンダ.":
    "The circle ゜: ハ → パ. The “p” sound is very common in loanwords: パン, パスタ, パンダ.",
  "Знак ряда И + маленькие ャュョ — один слог, как в хирагане: ニュース — новости.":
    "An i-row character + small ャュョ — one syllable, as in hiragana: ニュース — news.",
  "Оставшиеся базовые комбинации. В гайрайго встречаются реже, но リュック (рюкзак) без リュ не написать.":
    "The remaining basic combinations. Rarer in loanwords, but you can't write リュック (backpack) without リュ.",
  "Озвонченные комбинации: ジュース (сок), ジャズ (джаз). ジャ/ジュ/ジョ — самые частые.":
    "Voiced combinations: ジュース (juice), ジャズ (jazz). ジャ/ジュ/ジョ are the most common.",
  "Маленькое ッ удваивает согласный, как っ в хирагане: カップ (kappu) — чашка. Долгота в катакане всегда пишется чертой ー: コーヒー, ケーキ. Вместе они дают целый пласт слов: サッカー — футбол, クッキー — печенье.":
    "A small ッ doubles the consonant, like っ in hiragana: カップ (kappu) — cup. Length in katakana is always written with the bar ー: コーヒー, ケーキ. Together they give a whole layer of words: サッカー — soccer, クッキー — cookie.",
  "Финальный экзамен на различение близнецов (раздел 2.2 методики): シ/ツ, ソ/ン, ク/ワ/フ. Помните правило: у シ и ン черты/взмах идут СНИЗУ ВВЕРХ, у ツ и ソ — СВЕРХУ ВНИЗ. Серии быстрых выборов — цель ≥ 95% точности!":
    "A final exam on telling the twins apart: シ/ツ, ソ/ン, ク/ワ/フ. Remember the rule: for シ and ン the strokes go BOTTOM-UP, for ツ and ソ — TOP-DOWN. Series of quick choices — aim for ≥ 95% accuracy!",
  "Первые настоящие слова! Все они записаны хираганой, которую вы уже знаете. Каждое слово станет двумя SRS-карточками: «узнать перевод» и «вспомнить японский».":
    "Your first real words! All of them are written in the hiragana you already know. Each word becomes two SRS cards: “recognize the meaning” and “recall the Japanese”.",
  "Слова про себя и окружающих. Многие вы уже встречали в уроках каны — теперь они войдут в ваш активный словарь.":
    "Words about yourself and the people around you. You've met many of them in the kana lessons — now they enter your active vocabulary.",
  "Связка です, «понимаю/не понимаю» и вежливые слова — этого уже хватит на первый мини-диалог.":
    "The copula です, “I understand / don't understand” and polite words — enough for your first mini-dialogue.",
  "Основа счёта. У 4, 7 и 9 по два чтения — сначала запомните основное (よん, なな, きゅう), второе встретите в датах и времени.":
    "The basics of counting. 4, 7 and 9 have two readings each — first learn the main one (よん, なな, きゅう); you'll meet the other in dates and times.",
  "«Сейчас», «сегодня/завтра/вчера» и части суток. С вопросом なんじ можно спросить время.":
    "“Now”, “today / tomorrow / yesterday” and the parts of the day. With the question なんじ you can ask the time.",
  "Семь дней недели оканчиваются на ようび. Первый слог — стихия: 月 луна, 火 огонь, 水 вода… пока учим на слух, кандзи придут позже.":
    "The seven days of the week all end in ようび. The first syllable is an element: 月 moon, 火 fire, 水 water… for now learn them by ear, the kanji come later.",
  "Базовая еда. パン — первое слово катаканой: заимствования всегда пишутся ей.":
    "Basic food. パン is your first katakana word: loanwords are always written in it.",
  "Что пьют в Японии. Половина — гайрайго катаканой: コーヒー, ジュース, ビール.":
    "What people drink in Japan. Half are katakana loanwords: コーヒー, ジュース, ビール.",
  "Глаголы «есть/пить», вкусы и две застольные фразы — いただきます перед едой и ごちそうさま после.":
    "The verbs “eat / drink”, tastes, and two mealtime phrases — いただきます before eating and ごちそうさま after.",
  "Комнаты и обстановка. トイレ и ドア — гайрайго; おふろ — японская ванна для отмокания, не для мытья.":
    "Rooms and furnishings. トイレ and ドア are loanwords; おふろ is a Japanese bath for soaking, not for washing.",
  "Повседневные предметы. テレビ и パソコン — сокращённые заимствования, очень частотные.":
    "Everyday objects. テレビ and パソコン are shortened loanwords, very frequent.",
  "Первые глаголы действий в словарной форме. Дальше они спрягаются в ます-форму: たべる→たべます.":
    "Your first action verbs in dictionary form. Next they conjugate into the ます form: たべる→たべます.",
  "Глаголы движения и действий в словарной форме. В вежливой речи они становятся ます-формой: かう→かいます, まつ→まちます. Тип спряжения подсказан в заметке к каждому слову.":
    "Verbs of motion and action in dictionary form. In polite speech they become the ます form: かう→かいます, まつ→まちます. The conjugation type is noted with each word.",
  "Глаголы общения, учёбы и работы. はなす «разговаривать» и いう «сказать» — основа любого диалога; ならう/おしえる — пара «учиться/учить».":
    "Verbs of communication, study and work. はなす “to talk” and いう “to say” are the basis of any dialogue; ならう/おしえる are the pair “learn / teach”.",
  "Прилагательные-антонимы парами: большой/маленький, дорогой/дешёвый, новый/старый. Все здесь — и-типа: меняют хвост и (おおきい→おおきくない «не большой»).":
    "Antonym adjectives in pairs: big/small, expensive/cheap, new/old. All of these are the い-type: they change the い ending (おおきい→おおきくない “not big”).",
  "Прилагательные-антонимы парами: большой/маленький, дорогой/дешёвый, новый/старый. Все здесь — い-типа: меняют хвост い (おおきい→おおきくない «не большой»).":
    "Antonym adjectives in pairs: big/small, expensive/cheap, new/old. All of these are the い-type: they change the い ending (おおきい→おおきくない “not big”).",
  "Ощущения и оценки. Первые шесть — и-прилагательные, а きれい, しずか, ゆうめい, べんり — な-типа: перед существительным присоединяются через な (きれいな はな «красивый цветок»).":
    "Feelings and judgments. The first six are い-adjectives, while きれい, しずか, ゆうめい, べんり are the な-type: before a noun they attach with な (きれいな はな “a beautiful flower”).",
  "Ощущения и оценки. Первые шесть — い-прилагательные, а きれい, しずか, ゆうめい, べんり — な-типа: перед существительным присоединяются через な (きれいな はな «красивый цветок»).":
    "Feelings and judgments. The first six are い-adjectives, while きれい, しずか, ゆうめい, べんり are the な-type: before a noun they attach with な (きれいな はな “a beautiful flower”).",
  "«Этот/следующий/прошлый» для недель и месяцев, деление суток на ごぜん/ごご и счёт минут. С はん и ふん можно назвать любое время: にじはん, ごふん.":
    "“This / next / last” for weeks and months, the split of the day into ごぜん/ごご, and counting minutes. With はん and ふん you can tell any time: にじはん, ごふん.",
  "Куда ходят в городе: станция, магазин, банк, больница… С этими словами и глаголом いく получится сказать, куда вы направляетесь.":
    "Where people go in town: station, shop, bank, hospital… With these words and the verb いく you can say where you're headed.",
  "На чём передвигаться и как «сесть/сойти». のる и おりる управляют частицей に: でんしゃに のる — «сесть на электричку».":
    "How to get around and how to “board / get off”. のる and おりる take the particle に: でんしゃに のる — “to board a train”.",
  "Члены семьи. Важная тонкость: о своей семье и о чужой говорят по-разному — ちち/おとうさん, はは/おかあさん. В заметках указаны оба варианта.":
    "Family members. An important subtlety: you speak about your own family and someone else's differently — ちち/おとうさん, はは/おかあさん. Both forms are given in the notes.",
  "Погода и пейзаж. かぜ значит и «ветер», и «простуда» — различают по контексту.":
    "Weather and scenery. かぜ means both “wind” and “a cold” — told apart by context.",
  "Части тела и слова о самочувствии. У врача пригодятся びょうき «болезнь» и くすり «лекарство».":
    "Body parts and words about how you feel. At the doctor's, びょうき “illness” and くすり “medicine” come in handy.",
  "Основные цвета. Первые шесть — и-прилагательные (あかい «красный»), а みどり, むらさき, ピンク — существительные и соединяются через の: みどりの き.":
    "The basic colors. The first six are い-adjectives (あかい “red”), while みどり, むらさき, ピンク are nouns and connect with の: みどりの き.",
  "Основные цвета. Первые шесть — い-прилагательные (あかい «красный»), а みどり, むらさき, ピンク — существительные и соединяются через の: みどりの き.":
    "The basic colors. The first six are い-adjectives (あかい “red”), while みどり, むらさき, ピンク are nouns and connect with の: みどりの き.",
  "Вопросительные слова (いつ, どこ, なに…) и частотные наречия меры (とても, すこし, たくさん). あまり работает только с отрицанием: あまり わかりません — «не очень понимаю».":
    "Question words (いつ, どこ, なに…) and common adverbs of degree (とても, すこし, たくさん). あまり works only with a negative: あまり わかりません — “I don't understand it very well”.",
  "Первые кандзи — числа. У каждого знака есть значение, чтение и строгий порядок черт. Сначала смотрим анимацию написания, затем обводим знак и проверяем значение и чтение.":
    "The first kanji are numbers. Each one has a meaning, a reading and a strict stroke order. First watch the writing animation, then trace the character and check its meaning and reading.",
  "Вторая половина чисел. Теми же шагами: порядок черт → написание → значение → чтение. С 一〜十 вы уже сможете читать даты и цены.":
    "The second half of the numbers. Same steps: stroke order → writing → meaning → reading. With 一〜十 you can already read dates and prices.",
  "Стихии и дни недели. Эти знаки — пиктограммы: за каждым стоит образ. 日 и 月 ещё станут компонентами других кандзи.":
    "Elements and days of the week. These characters are pictographs: each one holds an image. 日 and 月 will also become components of other kanji.",
  "Остальные стихии недели. 木 «дерево» — очень частый компонент: из него собираются 林, 森 и 本 в следующем уроке.":
    "The rest of the week's elements. 木 “tree” is a very common component: 林, 森 and 本 are built from it in the next lesson.",
  "Кандзи редко учат как картинку целиком — их собирают из компонентов. Здесь все четыре знака складываются из уже изученных 木, 日 и 月.":
    "Kanji are rarely learned as one whole picture — they're assembled from components. Here all four characters are built from the already-learned 木, 日 and 月.",
  "Самые частые кандзи о человеке и величине. 人 «человек» лежит в основе 大 «большой» (человек с раскинутыми руками), а 小 и 中 задают противоположности: маленькое и среднее.":
    "The most common kanji about people and size. 人 “person” underlies 大 “big” (a person with arms spread wide), while 小 and 中 set the opposites: small and middle.",
  "Направления и части тела. 上 и 下 — зеркальные знаки «верх» и «низ». 口 «рот» — простой квадрат, а 目 «глаз» — тот же квадрат, поставленный вертикально и с чёрточками-зрачками.":
    "Directions and body parts. 上 and 下 are mirror characters, “top” and “bottom”. 口 “mouth” is a plain square, and 目 “eye” is the same square stood upright with pupil strokes.",
  "Слова о времени. 時 «время» собирается из уже знакомого солнца 日, а 分 и 半 пригодятся, чтобы называть минуты и «полчаса».":
    "Words about time. 時 “time” is built from the familiar sun 日, while 分 and 半 will help you name minutes and “half past”.",
  "Завершаем время: 半 «половина» (часто «полчаса»), 今 «сейчас» и вопрос 何 «что? сколько?», в котором прячется знакомый 口.":
    "Finishing time: 半 “half” (often “half an hour”), 今 “now”, and the question 何 “what? how many?”, which hides the familiar 口.",
  "Школьные кандзи. 校 «школа» собрана из дерева 木, а 先生 «учитель» и 学生 «студент» — слова, которые встретятся на каждом шагу.":
    "School kanji. 校 “school” is built from the tree 木, while 先生 “teacher” and 学生 “student” are words you'll meet at every turn.",
  "Ядро семьи. 父 «отец», 母 «мать» и 子 «ребёнок» — частые знаки. 子 ещё станет компонентом других кандзи.":
    "The core of the family. 父 “father”, 母 “mother” and 子 “child” are common characters. 子 will also become a component of other kanji.",
  "Люди вокруг. 男 «мужчина» и 女 «женщина» задают пару, а 友 «друг» — две руки, протянутые навстречу.":
    "The people around you. 男 “man” and 女 “woman” form a pair, while 友 “friend” is two hands reaching toward each other.",
  "Кандзи-глаголы движения и восприятия. 見 «видеть» вырастает из глаза 目, а 来 «приходить» прячет дерево 木.":
    "Verb kanji of motion and perception. 見 “to see” grows out of the eye 目, while 来 “to come” hides the tree 木.",
  "Глаголы речи и быта. 話 «говорить» и 読 «читать» опираются на рот 口, 書 «писать» — на солнце 日, а 飲 «пить» — на знак еды 食.":
    "Verbs of speech and daily life. 話 “to speak” and 読 “to read” rest on the mouth 口, 書 “to write” on the sun 日, and 飲 “to drink” on the food sign 食.",
  "Прилагательные-противоположности. 高い «дорогой/высокий» против 安い «дешёвый», 新しい «новый» против 古い «старый».":
    "Opposite adjectives. 高い “expensive / tall” versus 安い “cheap”, 新しい “new” versus 古い “old”.",
  "Ещё две меры: 多い «многочисленный» и 長い «длинный, долгий». В словах 長 даёт и «старшего» — 社長 «директор».":
    "Two more measures: 多い “numerous” and 長い “long”. In compounds 長 also gives “senior” — 社長 “company president”.",
  "Стороны света. 東 «восток» — солнце 日 за деревом 木. Эти знаки стоят в названиях городов и выходов со станций (西口, 南口).":
    "The cardinal directions. 東 “east” is the sun 日 behind a tree 木. These characters appear in city names and station exits (西口, 南口).",
  "Природа в пиктограммах: 山 «гора» — три пика, 川 «река» — три струи, 天 «небо» — человек 大 под чертой-небосводом.":
    "Nature in pictographs: 山 “mountain” is three peaks, 川 “river” three streams, 天 “sky” a person 大 under the line of the firmament.",
  "Погода и настроение. 気 «дух, воздух» и 雨 «дождь» вместе дают 天気 «погода» и 元気 «бодрость».":
    "Weather and mood. 気 “spirit, air” and 雨 “rain” together give 天気 “weather” and 元気 “energy”.",
  "Три кирпичика японской фразы: тема (は), связка (です) и вопрос (か). С ними вы строите «Я — студент» и «Вы студент?».":
    "The three building blocks of a Japanese sentence: the topic (は), the copula (です) and the question (か). With them you build “I am a student” and “Are you a student?”.",
  "の связывает слова в «мой друг», «имя учителя»; も добавляет значение «тоже». Обе частицы очень частотны.":
    "の links words into “my friend”, “the teacher's name”; も adds the meaning “too”. Both particles are very frequent.",
  "Частицы действия: を (что делают), で (где делают), に (куда идут и когда). Здесь появляется классическая пара で / に.":
    "Action particles: を (what is acted on), で (where it's done), に (where you go and when). The classic で / に pair appears here.",
  "Два класса прилагательных. и-прилагательные (おいしい) меняют окончание: ～かった в прошлом. な-прилагательные (げんき) присоединяют な перед существительным.":
    "Two classes of adjectives. い-adjectives (おいしい) change their ending: ～かった in the past. な-adjectives (げんき) attach な before a noun.",
  "Два класса прилагательных. い-прилагательные (おいしい) меняют окончание: ～かった в прошлом. な-прилагательные (げんき) присоединяют な перед существительным.":
    "Two classes of adjectives. い-adjectives (おいしい) change their ending: ～かった in the past. な-adjectives (げんき) attach な before a noun.",
  "Вежливая ます-форма глаголов: настоящее ます, прошлое ました, отрицание ません/ませんでした. Плюс частицы へ (направление «в») и と (с кем / и).":
    "The polite ます verb form: present ます, past ました, negative ません/ませんでした. Plus the particles へ (direction “to”) and と (with whom / and).",
  "Серия указателей こ (рядом со мной) / そ (рядом с тобой) / あ (далеко): これ — «это», この — «этот» (перед словом), ここ — «здесь».":
    "The series of demonstratives こ (near me) / そ (near you) / あ (far): これ — “this”, この — “this” (before a word), ここ — “here”.",
  "Подлежащее с が и два глагола существования: あります для вещей, います для людей и животных.":
    "The subject with が and two existence verbs: あります for things, います for people and animals.",
  "Выражаем желание (～たい «хочу») и приглашаем: ましょう «давайте» и ませんか «не сделать ли?».":
    "Expressing a wish (～たい “want”) and inviting: ましょう “let's” and ませんか “shall we?”.",
  "Причина с から «потому что» и сравнения: より «чем», のほうが «более», いちばん «самый», а также ～が好き «нравится».":
    "Cause with から “because” and comparisons: より “than”, のほうが “more”, いちばん “the most”, plus ～が好き “to like”.",
  "Связующая て-форма открывает много конструкций: ～てください (просьба), ～ています (сейчас делаю), ～てもいい (можно), ～てはいけない (нельзя).":
    "The connective て form opens up many constructions: ～てください (request), ～ています (doing now), ～てもいい (may), ～てはいけない (must not).",
  "Простые (casual) формы для речи с друзьями и заметок: ～ない «не делаю», ～た «сделал». Вежливые эквиваленты — ません и ました.":
    "Plain (casual) forms for talking with friends and for notes: ～ない “don't do”, ～た “did”. Their polite equivalents are ません and ました.",
  "でしょう «наверное» смягчает утверждение; финальные ね (ищет согласия) и よ (сообщает новое); や — неполное перечисление «и прочее».":
    "でしょう “probably” softens a statement; the final ね (seeks agreement) and よ (delivers news); や — an incomplete list “and so on”.",
});

