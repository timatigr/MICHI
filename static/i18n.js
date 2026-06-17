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
  "День засчитан в серию, когда набрана цель. XP: повторение +2, урок +20.":
    "A day counts toward your streak once the goal is met. XP: review +2, lesson +20.",
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
  "Не получилось разобрать. Попробуйте ещё раз.": "Couldn't analyze. Please try again.",
  "Правило": "Rule",
  "Пример": "Example",

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
  "Восстановление заменит весь текущий прогресс данными из копии. Перед заменой рядом сохраняется страховочный michi.db.bak. Продолжить?":
    "Restoring will replace all current progress with data from the backup. A safety michi.db.bak is saved alongside first. Continue?",
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
