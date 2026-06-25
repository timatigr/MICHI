/* MICHI — локализация интерфейса (i18n).

   Принцип: ключ перевода — это сам русский текст. Английский лежит overlay-ом
   в EN; чего там нет — тихо показывается по-русски (мягкий откат, можно
   переводить инкрементально). Контент уроков/слов локализуется на бэкенде
   (он строит упражнения); фронт шлёт выбранный язык параметром ?lang.

   Использование:
     tr("Готово")                       -> "Done" (в EN) / "Готово" (в RU)
     tr("Уровень {n}", {n: 3})          -> "Level 3"
   Статика в index.html — атрибут data-i18n="<русский текст>" (или
   data-i18n-html для разметки внутри), применяется applyI18n() при загрузке. */
"use strict";

const LANGS = { ru: "Русский", en: "English" };
let LANG = localStorage.getItem("michi_lang") || "ru";

const EN = {
  // --- Шапка / навигация / общее ---
  "Светлая/тёмная тема": "Light / dark theme",
  "Настройки": "Settings",
  "Сегодня": "Today",
  "Путь": "Path",
  "Повторение": "Review",
  "Статистика": "Stats",
  "Словарь": "Dictionary",
  "новое": "new",
  "учится": "learning",
  "в памяти": "memorized",
  "Пока пусто — пройдите урок, и выученное появится здесь для повторения.":
    "Empty for now — finish a lesson and what you learn will show up here to review.",
  "Загрузка…": "Loading…",
  "Выйти": "Exit",
  "Готово": "Done",
  "Начать": "Start",
  "Дальше": "Next",
  "Проверить": "Check",
  "Запомнил": "Got it",
  "Понятно": "Got it",
  "Круто!": "Cool!",
  "послушать": "listen",
  "Достижение получено": "Achievement unlocked",
  "Бронза": "Bronze", "Серебро": "Silver", "Золото": "Gold", "Легенда": "Legend",
  "каной или ромадзи": "kana or romaji",
  "Прослушать ещё раз": "Listen again",
  "Убрать": "Remove",
  "Анимация порядка черт": "Stroke-order animation",
  "Нейроголос недоступен (нужен интернет). Используйте голос браузера.":
    "Neural voice unavailable (needs internet). Use the browser voice.",
  "В браузере нет японских голосов. Установите: Параметры Windows → Время и язык → Речь → Добавить голоса → «Японский».":
    "The browser has no Japanese voices. Install: Windows Settings → Time & language → Speech → Add voices → “Japanese”.",
  "Учить": "Learn",
  "Пересдать": "Retry",
  "Остаться": "Stay",
  "Прослушать": "Play sample",
  "Верно": "Correct",
  "Правильно: {x}": "Correct: {x}",
  "пройден": "completed",
  "закрыто": "locked",
  "доступен": "available",
  "Урок": "Lesson",
  // --- Тренажёр письма (tracing.js) ---
  "Стереть": "Clear",
  "Подсказка": "Hint",
  "черта {a} из {b}": "stroke {a} of {b}",
  "Направление: эта черта пишется с другого конца": "Direction: this stroke goes the other way",
  "Отлично написано!": "Beautifully written!",
  "Смотрите, как пишется эта черта": "Watch how this stroke is written",
  "Не похоже — попробуйте ещё раз": "Doesn't match — try again",
  "Память {p}%": "Memory {p}%",
  // --- Карта памяти (Словарь) ---
  "Карта памяти": "Memory map",
  "Каждая клетка — выученный знак, цвет = насколько он свеж в памяти. Тусклые освежите на «Сегодня».":
    "Each cell is a learned character; color shows how fresh it is in memory. Freshen the dim ones on «Today».",
  "крепко": "strong", "тускнеет": "fading", "рискует": "at risk",
  // --- Разбор ошибок дня ---
  "Работа над ошибками": "Mistake review",
  "Быстрый разбор того, в чём вы сегодня ошиблись. Это практика — на расписание SRS не влияет.":
    "A quick run through what you got wrong today. It's practice — it doesn't affect the SRS schedule.",
  "Разобрать ошибки дня · {n}": "Review today's mistakes · {n}",
  "Разбор ошибок завершён": "Mistake review complete",
  "Повторено: {n} · сейчас верно {p}%": "Reviewed: {n} · now correct {p}%",
  "Сегодня ошибок нет — отлично!": "No mistakes today — great!",
  "Прервать разбор ошибок?": "Stop the mistake review?",

  // --- Тренировка слуха (минимальные пары) ---
  "Тренировка слуха": "Listening practice",
  "Минимальные пары: おばさん／おばあさん, きて／きって. Услышьте разницу в долготе и удвоении — это практика, на SRS не влияет.":
    "Minimal pairs: おばさん／おばあさん, きて／きって. Hear the difference in length and gemination — it's practice, doesn't affect SRS.",
  "Нужен голос — включите озвучку в ⚙ (нейроголос или японский голос системы).":
    "Audio needed — turn on a voice in ⚙ (neural voice or a system Japanese voice).",
  "Различать на слух": "Tell them apart by ear",
  "Что вы услышали?": "What did you hear?",
  "Вы выбрали не то слово": "You picked the wrong word",
  "Слух натренирован": "Ear trained",
  "Пар на слух: {n} · точность {p}%": "Pairs by ear: {n} · accuracy {p}%",
  "Прервать тренировку слуха?": "Stop the listening practice?",
  "Нет сети — попробуйте позже.": "No connection — try again later.",

  // --- Настройки (⚙) ---
  "Озвучка": "Audio",
  "Источник": "Source",
  "Нейроголос Microsoft (онлайн, лучший звук)": "Microsoft neural voice (online, best sound)",
  "Голос браузера / системы": "Browser / system voice",
  "Голос": "Voice",
  "Громкость": "Volume",
  "Скорость речи": "Speech rate",
  "Ромадзи (латинская транскрипция)": "Romaji (Latin transcription)",
  "Авто — скрыть после хираганы": "Auto — hide after hiragana",
  "Всегда показывать": "Always show",
  "Никогда не показывать": "Never show",
  "Дневная цель": "Daily goal",
  "Лёгкая — 10 XP": "Light — 10 XP",
  "Обычная — 20 XP": "Normal — 20 XP",
  "Серьёзная — 40 XP": "Serious — 40 XP",
  "Серия 🔥 растёт за любой день с занятием. Цель — личный дневной ориентир. XP: повторение +2, урок +20.":
    "Your 🔥 streak grows on any day you study. The goal is a personal daily target. XP: review +2, lesson +20.",
  "Звук и вибрация при нажатиях": "Sound & vibration on taps",
  "Звук нажатия": "Tap sound",
  "Выберите звук — он сразу проиграется. Звуки Kenney (CC0), не зависят от громкости озвучки слов.":
    "Pick a sound — it plays instantly. Kenney sounds (CC0), independent of word audio volume.",
  "ИИ-разбор ошибок «Сэнсэй»": "AI mistake analysis «Sensei»",
  "Язык": "Language",
  "Язык интерфейса. Контент уроков переводится постепенно; непереведённое показывается по-русски.":
    "Interface language. Lesson content is translated gradually; untranslated parts show in Russian.",
  "Без звука": "No sound",

  // --- Голоса нажатий (Haptics.TAPS) ---
  "Капля": "Drop", "Тик": "Tick", "Мягкий": "Soft", "Клик": "Click",
  "Струна": "Pluck", "Стекло": "Glass", "Щелчок": "Switch",

  // --- Сегодня ---
  "Доброй ночи": "Good night",
  "Доброе утро": "Good morning",
  "Добрый день": "Good afternoon",
  "Добрый вечер": "Good evening",
  "повторено сегодня": "reviewed today",
  "точность сегодня": "accuracy today",
  "Уровень {n}": "Level {n}",
  "{a} / {b} XP · всего {c}": "{a} / {b} XP · {c} total",
  "цель!": "goal!",
  "/ {g} XP": "/ {g} XP",
  "План на сегодня": "Today's plan",
  "по расписанию: {n}": "scheduled: {n}",
  "новых: {n}": "new: {n}",
  "Очередь пуста — всё повторено": "Queue empty — all reviewed",
  "Новый урок": "New lesson",
  "Все доступные уроки пройдены": "All available lessons completed",
  "Прогресс курсов": "Course progress",
  "Катакану можно учить параллельно с хираганой, слова N5 откроются после хираганы.":
    "You can learn katakana alongside hiragana; N5 words unlock after hiragana.",
  "Хирагана пройдена — ромадзи скрыт, чтобы вы читали каной.\n       Вернуть можно в ⚙ настройках.":
    "Hiragana complete — romaji is hidden so you read kana.\n       You can bring it back in ⚙ settings.",

  // --- Путь (уроки) ---
  "Все": "All", "Хирагана": "Hiragana", "Катакана": "Katakana",
  "Первые слова": "First words", "Кандзи": "Kanji", "Грамматика": "Grammar",
  "ворота": "gate", "Открыто": "Open", "Пройдено": "Done", "Закрыто": "Locked",

  // --- Повторение (вкладка) ---
  "Очередь на сегодня": "Today's queue",
  "по расписанию": "scheduled",
  "новая": "new", "новые": "new", "новых": "new",
  "повторено сегодня ": "reviewed today",
  "Начать сессию · {n} · ≈{m} мин": "Start session · {n} · ≈{m} min",
  "Очередь пуста — всё повторено! Новые карточки появятся\n           после уроков, повторения — по расписанию FSRS.":
    "Queue empty — all reviewed! New cards appear after lessons; reviews follow the FSRS schedule.",

  // --- Результат урока / сессии ---
  "{title} — пройден": "{title} — done",
  "Ворота пройдены!": "Gate passed!",
  "Ворота не пройдены": "Gate not passed",
  "Очередь разобрана": "Queue cleared",
  "Повторять пока нечего": "Nothing to review yet",
  "Точность {p}% · {a} из {b}": "Accuracy {p}% · {a} of {b}",
  "В SRS добавлено карточек: {n}": "Cards added to SRS: {n}",
  "Карточки уже в SRS": "Cards already in SRS",
  "Карточек: {n} · точность {p}%": "Cards: {n} · accuracy {p}%",
  "Пройдите урок, чтобы добавить карточки в SRS.": "Complete a lesson to add cards to SRS.",
  "Ваш результат {p}% · нужно {need}%": "Your score {p}% · need {need}%",
  "Следующий юнит откроется после пересдачи.": "The next unit opens after you retake it.",

  // --- Статистика ---
  "Мои карточки": "My cards",
  "в долгой памяти": "in long-term memory",
  "ещё учатся": "still learning",
  "помню при повторении": "recalled on review",
  "Достижения · {a}/{b}": "Achievements · {a}/{b}",
  "Сколько я повторял · 14 дней": "Reviews · 14 days",
  "Что меня ждёт · 14 дней": "What's coming · 14 days",
  "Трудные знаки": "Tricky characters",
  "Лимиты SRS": "SRS limits",
  "Новых карточек в день": "New cards per day",
  "Повторений в день (макс.)": "Reviews per day (max)",
  "Целевое удержание": "Target retention",
  "Резервная копия": "Backup",
  "Скачать копию": "Download backup",
  "Восстановить из копии…": "Restore from backup…",
  "Сохранено ✓": "Saved ✓",

  // --- Плеер / упражнение / счётчики ---
  "≈{m} мин": "≈{m} min",
  "{n} · осталось ~{m}": "{n} · ~{m} left",
  "Прервать повторение? Все ответы уже сохранены.":
    "Stop the review? All answers are already saved.",
  "Выйти из урока? Потом продолжите с этого же места.":
    "Leave the lesson? You'll continue from this spot later.",
  // --- Сетевые сбои в сессии (мягкая деградация) ---
  "Нет сети — урок не засчитан. Зайдите снова, прогресс сохранён.":
    "No connection — the lesson wasn't recorded. Come back and your progress is saved.",
  "Нет сети — попробуйте позже. Ответы сохранены.":
    "No connection — try again later. Your answers are saved.",
  "Нет сети — ответ не сохранён, карточка вернётся позже.":
    "No connection — answer not saved; the card will come back later.",
  "следующий показ": "next in",
  // --- Упреждающее повторение «Освежить заранее» ---
  "Освежить заранее": "Freshen up early",
  "Освежить": "Freshen up",
  "{n} скоро потускнеют — повторите, пока легко":
    "{n} will fade soon — review while it's still easy",
  "Освежили вовремя!": "Freshened in time!",
  "Пока нечего освежать": "Nothing to freshen yet",
  "Повторено: {n} · точность {p}%": "Reviewed: {n} · accuracy {p}%",
  "Загляните позже — подскажем, когда что-то начнёт тускнеть.":
    "Check back later — we'll nudge you when something starts to fade.",

  // --- ИИ-статус (⚙) ---
  "включён": "enabled",
  "нет ключа": "no key",
  "Сегодня осталось {r} из {l} запросов (кэш-разборы не тратят квоту).":
    "{r} of {l} requests left today (cached analyses don't use quota).",
  "После неверного ответа жмите «🧠 Разобрать ошибку» — модель объяснит промах. Разборы кэшируются, чтобы не платить дважды.":
    "After a wrong answer, tap «🧠 Analyze mistake» — the model will explain it. Analyses are cached so you don't pay twice.",
  "Чтобы включить, задайте ключ перед запуском и перезапустите сервер. Бесплатно: GEMINI_API_KEY (ключ на aistudio.google.com/apikey) — set GEMINI_API_KEY=… затем run.bat. Либо ANTHROPIC_API_KEY (Claude). Без ключа курс работает как обычно.":
    "To enable it, set a key before launch and restart the server. Free: GEMINI_API_KEY (get one at aistudio.google.com/apikey) — set GEMINI_API_KEY=… then run.bat. Or ANTHROPIC_API_KEY (Claude). Without a key the course works as usual.",

  // --- Разбор ошибок «Сэнсэй» (кнопка/панель) ---
  "🧠 Разобрать ошибку": "🧠 Analyze mistake",
  "Думаю…": "Thinking…",
  "Не получилось получить разбор. Попробуйте ещё раз.": "Couldn't get an analysis. Please try again.",
  "Правило": "Rule",
  "Пример": "Example",
  // Категории ошибки «Сэнсэя» (AI.CAT); «Кандзи» уже переведён выше
  "Частица": "Particle", "Спряжение": "Conjugation", "Лексика": "Vocabulary",
  "Порядок слов": "Word order", "Орфография каны": "Kana orthography", "Разбор": "Analysis",

  // --- Статистика: длинные заметки и графики ---
  "«В долгой памяти» — карточки с интервалом от нескольких дней. Последняя цифра — доля верных ответов на повторениях за неделю (цель — {p}%).":
    "«Long-term memory» — cards with intervals of several days or more. The last number is the share of correct answers on reviews over the week (target — {p}%).",
  "Пока нет данных — пройдите первую SRS-сессию.": "No data yet — do your first SRS session.",
  "Сколько карточек придёт на повторение в каждый день — если заниматься ежедневно, горка не вырастет.":
    "How many cards come due each day — if you study daily, the pile won't grow.",
  "Цифра — сколько раз знак забывался. Обведённые — «пиявки»: им в сессии показывается мнемоника.":
    "The number is how many times the character was forgotten. Outlined ones are «leeches»: a mnemonic is shown for them during sessions.",
  "Выше удержание — крепче помните, но больше повторений в день. Меньше новых — спокойнее темп. Применяется со следующей сессии.":
    "Higher retention — stronger memory but more reviews per day. Fewer new — calmer pace. Applies from the next session.",
  "Весь прогресс — карточки, журнал ответов, пройденные уроки и настройки — хранится локально в одном файле. Скачайте копию, чтобы перенести его на другой компьютер или вернуть после переустановки.":
    "All your progress — cards, answer log, completed lessons and settings — is stored locally in a single file. Download a backup to move it to another computer or restore after a reinstall.",
  "точность {p}%": "accuracy {p}%",
  "сегодня": "today",

  // --- Резервная копия (диалоги/сообщения) ---
  "Восстановить прогресс из этого файла? Текущие карточки, ответы и настройки будут заменены.":
    "Restore progress from this file? Your current cards, answers and settings will be replaced.",
  "Восстановить": "Restore",
  "Отмена": "Cancel",
  "Готово: {c} карточек, {r} ответов. Перезагрузка…": "Done: {c} cards, {r} answers. Reloading…",
  "Не удалось восстановить: {e}": "Restore failed: {e}",
  "Не удалось сохранить: {e}": "Couldn't save: {e}",
  "{a} из {b}": "{a} of {b}",
  "{n} знаков": "{n} characters",
  "Восстановление…": "Restoring…",
  "Удалить мои данные": "Delete my data",
  "Сотрёт весь прогресс с сервера и начнёт чистую сессию. Необратимо — сначала скачайте копию, если хотите сохранить.":
    "Erases all progress on the server and starts a clean session. Irreversible — download a backup first if you want to keep it.",
  "Удалить весь ваш прогресс с сервера? Карточки, ответы, уроки и настройки будут стёрты безвозвратно — это нельзя отменить.":
    "Delete all your progress on the server? Cards, answers, lessons and settings will be erased permanently — this can't be undone.",
  "Удалить": "Delete",
  "Удаление…": "Deleting…",
  "Не удалось удалить: {e}": "Couldn't delete: {e}",
  "Восстановление заменит весь текущий прогресс данными из копии. Перед заменой рядом сохраняется страховочный michi.db.bak. Продолжить?":
    "Restoring will replace all current progress with data from the backup. A safety michi.db.bak is saved alongside first. Continue?",

  // --- Онбординг первого запуска ---
  "Пропустить": "Skip",
  "Назад": "Back",
  "Далее": "Next",
  "Добро пожаловать": "Welcome",
  "Японский с нуля — и в удовольствие": "Japanese from zero — and a joy",
  "Кана, слова, кандзи и грамматика N5 — маленькими уроками. Умное повторение само напомнит, что пора освежить выученное.":
    "Kana, words, kanji and N5 grammar — in bite-sized lessons. Smart spaced repetition reminds you when it's time to refresh.",
  "Язык интерфейса": "Interface language",
  "Выберите дневную цель": "Choose a daily goal",
  "Дневная цель в XP — личный ориентир на день. Серию 🔥 держит любое занятие. Повторение +2 XP, урок +20 XP. Поменять можно в ⚙ в любой момент.":
    "A daily XP goal is your personal target for the day. Any study keeps your 🔥 streak. Review +2 XP, lesson +20 XP. Change it anytime in ⚙.",
  "Лёгкая": "Light", "Обычная": "Normal", "Серьёзная": "Serious",
  "Послушать голос": "Hear the voice",
  "С чего начнём": "Where we'll start",
  "Старт — хирагана, японская азбука. Дальше курсы открываются сами: катакана параллельно, слова N5 после хираганы, затем кандзи и грамматика.":
    "We start with hiragana, the Japanese syllabary. Then courses unlock on their own: katakana in parallel, N5 words after hiragana, then kanji and grammar.",
  "Начать первый урок": "Start the first lesson",
  "Осмотреться самому": "Look around first",

  // --- О проекте / приватность ---
  "О проекте и приватности": "About & privacy",
  "О проекте": "About",
  "MICHI（道, «путь») — бесплатный тренажёр японского с нуля: кана, лексика, кандзи и грамматика уровня JLPT N5. Материал даётся маленькими уроками, а умное интервальное повторение (алгоритм FSRS) само напоминает, что пора освежить выученное.":
    "MICHI (道, “the path”) is a free beginner's Japanese trainer: kana, vocabulary, kanji and JLPT N5 grammar. Material comes in small lessons, and smart spaced repetition (the FSRS algorithm) reminds you when it's time to refresh what you've learned.",
  "Приватность": "Privacy",
  "Без регистрации: ни почты, ни пароля. При первом заходе браузеру выдаётся анонимный идентификатор, он хранится в подписанной cookie и привязывает прогресс к этому браузеру. Никакой аналитики и трекеров третьих сторон.":
    "No sign-up: no email, no password. On your first visit the browser is given an anonymous identifier, stored in a signed cookie, which ties your progress to this browser. No analytics and no third-party trackers.",
  "Что хранится на сервере: ваши карточки, журнал ответов, пройденные уроки и настройки — в отдельной базе, привязанной к анонимному идентификатору. Данные не передаются третьим лицам и не используются для рекламы. Весь прогресс можно скачать одним файлом (⚙ → «Скачать копию») и восстановить на другом устройстве.":
    "What's stored on the server: your cards, answer log, completed lessons and settings — in a separate database tied to the anonymous identifier. The data is not shared with third parties or used for ads. You can download all your progress as a single file (⚙ → “Download backup”) and restore it on another device.",
  "Сторонние запросы: интерфейс, шрифты и звуки отдаются с этого же сайта — никаких сторонних шрифтов, CDN или аналитики. ИИ-разбор ошибок «Сэнсэй» по умолчанию выключен; если владелец сайта его включил, то при нажатии кнопки разбора текст конкретного задания и ваш ответ отправляются провайдеру ИИ (Anthropic или Google) только ради объяснения ошибки. Без ключа ИИ ничего никуда не отправляется.":
    "Third-party requests: the interface, fonts and sounds are all served from this site — no third-party fonts, CDNs or analytics. The «Sensei» AI mistake analysis is off by default; if the site owner enabled it, pressing the analyze button sends the specific exercise text and your answer to the AI provider (Anthropic or Google) solely to explain the mistake. Without a key, AI sends nothing anywhere.",
  "Удалить данные: на вкладке «Статистика» → «Резервная копия» есть кнопка «Удалить мои данные» — она безвозвратно стирает весь прогресс с сервера и начинает чистую сессию. Можно и просто очистить cookie сайта. Заброшенные пустые сессии сервер удаляет сам.":
    "Deleting your data: on the «Stats» tab → «Backup» there's a «Delete my data» button — it permanently erases all progress on the server and starts a clean session. You can also just clear the site's cookie. Abandoned empty sessions are removed by the server automatically.",
  "Лицензия и благодарности": "License & credits",
  'Код — под лицензией MIT. Данные порядка черт — <a href="https://kanjivg.tagaini.net/" target="_blank" rel="noopener">KanjiVG</a> (© Ulrich Apel, CC BY-SA 3.0). Звуки интерфейса — <a href="https://kenney.nl/assets/interface-sounds" target="_blank" rel="noopener">Kenney</a> (CC0). Шрифты — Inter и Noto Sans JP.':
    'Code is licensed under MIT. Stroke-order data — <a href="https://kanjivg.tagaini.net/" target="_blank" rel="noopener">KanjiVG</a> (© Ulrich Apel, CC BY-SA 3.0). Interface sounds — <a href="https://kenney.nl/assets/interface-sounds" target="_blank" rel="noopener">Kenney</a> (CC0). Fonts — Inter and Noto Sans JP.',
  "Учебный проект, предоставляется «как есть», без гарантий.":
    "An educational project, provided «as is», without any warranty.",
};

// Индекс по «схлопнутым» пробелам: ключи в словаре можно писать одной строкой,
// а в коде строка может быть многострочной с отступами — всё равно совпадёт.
const _norm = s => s.replace(/\s+/g, " ").trim();
const EN_NORM = {};
for (const k in EN) EN_NORM[_norm(k)] = EN[k];

function tr(s, vars) {
  let out = s;
  if (LANG === "en") {
    const hit = EN[s] != null ? EN[s] : EN_NORM[_norm(s)];
    if (hit != null) out = hit;
  }
  if (vars) for (const k in vars) out = out.split("{" + k + "}").join(vars[k]);
  return out;
}

function setLang(l) {
  LANG = l;
  localStorage.setItem("michi_lang", l);
  if (l === "en") loadEnContent();   // подгрузить EN-оверлей контента при переключении
}

/* EN-оверлей контента (content_en*.js, ~158КБ переводов слов/упражнений/уроков)
   грузим лениво и только в английском — русскому большинству он мёртвый груз.
   Скрипты выполняют Object.assign(EN, {...}); async=false + порядок вставки
   сохраняют порядок применения оверлеев. Идемпотентно; ошибка загрузки —
   мягкий откат на русские строки (tr вернёт исходный ключ). */
let _enContentPromise = null;
function loadEnContent() {
  if (_enContentPromise) return _enContentPromise;
  const files = ["content_en.js", "content_en_2.js", "content_en_3.js"];
  _enContentPromise = Promise.all(files.map(src => new Promise(resolve => {
    const s = document.createElement("script");
    s.src = src;
    s.async = false;
    s.onload = resolve;
    s.onerror = () => resolve();
    document.head.appendChild(s);
  })));
  return _enContentPromise;
}

/* Перевод статической разметки index.html: data-i18n (textContent) и
   data-i18n-html (innerHTML, если внутри ссылка/разметка). */
function applyI18n() {
  document.documentElement.lang = LANG;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.textContent = tr(el.getAttribute("data-i18n"));
  });
  document.querySelectorAll("[data-i18n-html]").forEach(el => {
    el.innerHTML = tr(el.getAttribute("data-i18n-html"));
  });
}
