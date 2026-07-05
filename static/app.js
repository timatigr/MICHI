/* MICHI — прототип core loop: уроки каны + SRS-повторения. */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);

/* Русские формы множественного числа: plural(3, ["день","дня","дней"]) */
function plural(n, [one, few, many]) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}

async function apiError(r) {
  let detail;
  try { detail = (await r.json()).detail; } catch { /* не-JSON ответ (500) */ }
  return new Error(detail || `${r.status} ${r.statusText}`);
}

// Смещение часового пояса браузера (минуты восточнее UTC). Бэкенд считает по нему
// «сегодня»/серию/дневные лимиты — иначе на общем хостинге у всех был бы UTC-день
// сервера (см. app/main.py _tz_offset_min). getTimezoneOffset = минуты к западу.
const TZ_OFFSET = String(-new Date().getTimezoneOffset());

const api = {
  async get(url) {
    const r = await fetch(url, { headers: { "X-TZ-Offset": TZ_OFFSET } });
    if (!r.ok) throw await apiError(r);
    return r.json();
  },
  async post(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-TZ-Offset": TZ_OFFSET },
      body: JSON.stringify(body || {}),
    });
    if (!r.ok) throw await apiError(r);
    return r.json();
  },
};

/* Кэш /api/overview: его тянут и «Сегодня», и «Повторение» — без кэша переключение
   вкладок = лишний round-trip. Короткий TTL + явная инвалидация после сессии
   (closePlayer), когда данные реально меняются. */
let _ov = { data: null, t: 0 };
async function getOverview() {
  if (_ov.data && Date.now() - _ov.t < 15000) return _ov.data;
  _ov.data = await api.get("/api/overview");
  _ov.t = Date.now();
  return _ov.data;
}
function invalidateOverview() { _ov = { data: null, t: 0 }; }

/* ---------- UI-настройки: зеркало в БД (перенос между устройствами + бэкап) ----------
   Источник истины на клиенте — localStorage (читается синхронно на старте всеми
   модулями). Сервер — durable-зеркало: сюда пишем при изменении настройки, а на
   старте подтягиваем (после импорта копии или на новом устройстве localStorage
   пуст/устарел). Значения — те же строки, что в localStorage. */
const Prefs = {
  KEYS: ["michi_theme", "michi_lang", "michi_tts", "michi_haptics",
         "michi_daily_goal", "michi_romaji", "michi_onboarded",
         "michi_mnemo_fav", "michi_mnemo_custom"],
  _pending: null,
  _timer: 0,

  // Отложенная запись — коалесцирует частые изменения (напр. ползунок громкости)
  push(key) {
    this._pending = this._pending || {};
    this._pending[key] = localStorage.getItem(key);
    clearTimeout(this._timer);
    this._timer = setTimeout(() => this.flush(), 600);
  },

  // Немедленно отправить накопленное (перед reload, чтобы запись не оборвалась)
  flush() {
    clearTimeout(this._timer);
    if (!this._pending) return Promise.resolve();
    const body = this._pending;
    this._pending = null;
    if (window.__noPrefWrite) return Promise.resolve();   // тестовый прогон не пишет в БД
    return api.post("/api/prefs", body).catch(() => {});
  },

  // Старт: сервер авторитетнее. При расхождении переписываем localStorage и один
  // раз перезагружаемся — модули переинициализируются из правильных значений.
  // Локальные ключи, которых нет на сервере, засеваем (чтобы бэкап их содержал).
  async sync() {
    let server;
    try { server = await api.get("/api/prefs"); } catch { return; }
    let changed = false;
    const seed = {};
    for (const k of this.KEYS) {
      const local = localStorage.getItem(k);
      const srv = Object.prototype.hasOwnProperty.call(server, k) ? server[k] : null;
      if (srv != null && srv !== local) { localStorage.setItem(k, srv); changed = true; }
      else if (srv == null && local != null) seed[k] = local;
    }
    if (window.__noPrefWrite) return;                     // тестовый прогон: без записи и reload
    if (Object.keys(seed).length) api.post("/api/prefs", seed).catch(() => {});
    if (changed) location.reload();
  },
};

/* ---------- Ассоциации: личный фаворит + своя мнемоника (6.6) ----------
   Хранится клиентски (зеркалится в БД через Prefs): michi_mnemo_fav —
   {знак: индекс пресета | "custom"}, michi_mnemo_custom — {знак: текст}. */
const Mnemo = {
  _get(key) { try { return JSON.parse(localStorage.getItem(key) || "{}"); } catch { return {}; } },
  _set(key, obj) { localStorage.setItem(key, JSON.stringify(obj)); Prefs.push(key); },

  custom(char) { return this._get("michi_mnemo_custom")[char] || ""; },
  setCustom(char, text) {
    const m = this._get("michi_mnemo_custom");
    text = (text || "").trim();
    if (text) m[char] = text; else delete m[char];
    this._set("michi_mnemo_custom", m);
  },
  fav(char) { const v = this._get("michi_mnemo_fav")[char]; return v == null ? 0 : v; },
  setFav(char, val) { const m = this._get("michi_mnemo_fav"); m[char] = val; this._set("michi_mnemo_fav", m); },

  // Все варианты знака: пресеты сервера + (если вписана) своя
  options(char, presets) {
    const opts = (presets || []).map(t => ({ text: t, custom: false }));
    const c = this.custom(char);
    if (c) opts.push({ text: c, custom: true });
    return opts;
  },
  // Выбранная пользователем ассоциация (текст) или null
  favText(char, presets) {
    const opts = this.options(char, presets);
    if (!opts.length) return null;
    const f = this.fav(char);
    if (f === "custom") { const c = opts.find(o => o.custom); if (c) return c.text; }
    const idx = (typeof f === "number" && f >= 0 && f < (presets || []).length) ? f : 0;
    return (presets && presets[idx]) || opts[0].text || null;
  },
};

/* ---------- Озвучка: нейроголос (Edge TTS на сервере) + фолбэк на браузер ---------- */
const TTS = {
  prefs: {
    source: "neural",                    // neural | browser
    neuralVoice: "nanami",
    voiceURI: null,                      // голос браузера
    volume: 0.9,
    rate: 0.85,
    ...JSON.parse(localStorage.getItem("michi_tts") || "{}"),
  },
  neuralVoices: [],   // [{id, label}] с сервера
  browserVoices: [],
  browserVoice: null,
  neuralOk: true,     // false после первой ошибки сети → фолбэк
  audio: new Audio(),

  async init() {
    try {
      this.neuralVoices = await api.get("/api/tts/voices");
    } catch {
      this.neuralVoices = [];
    }
    if (!this.neuralVoices.length) this.neuralOk = false;
    // Миграция старых id (ja-JP-NanamiNeural) и пропавших голосов VOICEVOX
    const legacy = { "ja-JP-NanamiNeural": "nanami", "ja-JP-KeitaNeural": "keita" };
    if (legacy[this.prefs.neuralVoice]) this.prefs.neuralVoice = legacy[this.prefs.neuralVoice];
    if (this.neuralVoices.length &&
        !this.neuralVoices.some(v => v.id === this.prefs.neuralVoice)) {
      this.prefs.neuralVoice = this.neuralVoices[0].id;
    }
    this.refreshBrowser();
  },

  refreshBrowser() {
    if (!("speechSynthesis" in window)) return;
    this.browserVoices = speechSynthesis.getVoices()
      .filter(v => v.lang.toLowerCase().startsWith("ja"));
    const saved = this.prefs.voiceURI &&
      this.browserVoices.find(v => v.voiceURI === this.prefs.voiceURI);
    this.browserVoice = saved || this.bestBrowser();
  },

  bestBrowser() {
    const score = v =>
      (/natural|neural/i.test(v.name) ? 4 : 0) +
      (/online/i.test(v.name) ? 2 : 0) +
      (/google/i.test(v.name) ? 3 : 0) +
      (/nanami|keita/i.test(v.name) ? 2 : 0) +
      (v.localService ? 0 : 1);
    return [...this.browserVoices].sort((a, b) => score(b) - score(a))[0] || null;
  },

  get available() {
    return (this.neuralOk && this.neuralVoices.length) || !!this.browserVoice;
  },

  speak(text) {
    if (!text || this.prefs.volume === 0) return;
    if (this.prefs.source === "neural" && this.neuralOk && this.neuralVoices.length) {
      this.speakNeural(text);
    } else {
      this.speakBrowser(text);
    }
  },

  speakNeural(text) {
    if (this.audio) this.audio.pause();
    // Новый элемент на каждое воспроизведение — без гонок при смене src
    const a = new Audio(`/api/tts?text=${encodeURIComponent(text)}&voice=${encodeURIComponent(this.prefs.neuralVoice)}`);
    this.audio = a;
    a.volume = this.prefs.volume;
    // Скорость — на клиенте (один файл в кэше на текст+голос)
    a.defaultPlaybackRate = this.prefs.rate;
    a.playbackRate = this.prefs.rate;
    if ("preservesPitch" in a) a.preservesPitch = true;
    a.onerror = () => { this.neuralOk = false; this.speakBrowser(text); };
    a.play().catch(() => {});
  },

  speakBrowser(text) {
    if (!this.browserVoice) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.voice = this.browserVoice;
    u.lang = "ja-JP";
    u.volume = this.prefs.volume;
    u.rate = this.prefs.rate;
    speechSynthesis.speak(u);
  },

  save() {
    localStorage.setItem("michi_tts", JSON.stringify(this.prefs));
    Prefs.push("michi_tts");
  },
};
if ("speechSynthesis" in window) {
  speechSynthesis.onvoiceschanged = () => TTS.refreshBrowser();
}
TTS.init();

/* ---------- ИИ-разбор ошибок «Сэнсэй» (SRS.md 7.2) ---------- */
const AI = {
  available: false,
  status: {},
  CAT: {
    particle: "Частица", conjugation: "Спряжение", vocabulary: "Лексика",
    word_order: "Порядок слов", kana_orthography: "Орфография каны",
    kanji: "Кандзи", other: "Разбор",
  },
  async init() {
    try {
      this.status = await api.get("/api/ai/status");
      this.available = !!this.status.available;
    } catch { this.status = {}; this.available = false; }
  },
};
AI.init();

// Кнопка «Разобрать ошибку» с ленивым запросом к Claude (только по клику).
// ctx: {exercise_type, item_id, prompt, correct_answer, given_answer, choices}
function mountExplain(host, ctx) {
  if (!AI.available || !host) return;
  const wrap = document.createElement("div");
  wrap.className = "ai-explain";
  wrap.innerHTML = `<button class="ghost ai-ask">${Icons.ui("spark")} ${tr("Разобрать ошибку")}</button>
    <div class="ai-body" hidden></div>`;
  host.appendChild(wrap);
  const btn = $(".ai-ask", wrap);
  const body = $(".ai-body", wrap);
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.textContent = tr("Думаю…");
    try {
      const r = await api.post("/api/ai/explain", ctx);
      const cat = tr(AI.CAT[r.category] || AI.CAT.other);
      body.innerHTML = `<span class="ai-cat">${cat}</span>
        <p class="ai-text">${escapeHtml(r.explanation)}</p>
        <p class="ai-rule"><b>${tr("Правило")}:</b> ${escapeHtml(r.rule)}</p>
        <p class="ai-ex"><b>${tr("Пример")}:</b> ${escapeHtml(r.counterexample)}</p>`;
      body.hidden = false;
      btn.remove();
    } catch {
      btn.disabled = false;
      btn.innerHTML = `${Icons.ui("spark")} ${tr("Разобрать ошибку")}`;
      body.innerHTML = `<p class="ai-text">${tr("Не получилось получить разбор. Попробуйте ещё раз.")}</p>`;
      body.hidden = false;
    }
  });
}

const escapeHtml = s => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/* Учебный мини-markdown: **жирный** в объяснениях грамматики. Контент курса
   пишет **は** — без конвертации звёздочки уходили в разметку как есть. */
const fmtBold = s => String(s == null ? "" : s)
  .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");

/* Локализация составного вопроса: шаблон и каждая подстановка переводятся
   отдельно (word_kanji / verb_conjugation). В RU вернёт исходную фразу. */
function qtr(qi) {
  const vars = {};
  for (const [k, v] of Object.entries(qi.vars || {})) vars[k] = tr(v);
  return tr(qi.key, vars);
}

/* Промпт упражнений-сборки. У kana_word_build это «ромадзи — перевод»:
   ромадзи не трогаем, переводим только перевод (после « — »); одиночную
   строку (vocab_build / sentence_scramble — это чистый русский) — целиком. */
function trBuildPrompt(s) {
  const i = s.indexOf(" — ");
  return i < 0 ? tr(s) : s.slice(0, i) + " — " + tr(s.slice(i + 3));
}

/* Интервал до следующего показа — считаем на клиенте из next_due (зеркало
   srs_engine._humanize), чтобы число и единицы переводились через tr. */
function humanizeInterval(secs) {
  secs = Math.max(secs, 0);
  if (secs < 90) return tr("через минуту");
  if (secs < 3600) return tr("через {n} мин", { n: Math.round(secs / 60) });
  if (secs < 86400 * 1.5) return tr("через {n} ч", { n: Math.round(secs / 3600) });
  return tr("через {n} дн", { n: Math.round(secs / 86400) });
}

const speak = text => TTS.speak(text);
function ttsButton(text) {
  if (!TTS.available) return "";
  return `<button class="tts-btn" data-tts="${text}">${Icons.ui("speaker")} ${tr("послушать")}</button>`;
}

/* ---------- Тактильный отклик интерфейса: звук нажатия + вибрация ----------
   Короткие сэмплы из набора Kenney «Interface Sounds» (CC0) через Web Audio —
   низкая задержка, мгновенный отклик. Звук нажатия выбирается в настройках,
   вердикт ответа — confirmation/error. Тумблер общий, по умолчанию включён;
   громкость не зависит от озвучки слов, вибрация уважает reduced-motion.
   Атрибуция — static/sounds/ui/CREDITS.txt. */
const Haptics = {
  prefs: {
    enabled: true,
    tapSound: "off",          // звук нажатия по умолчанию выключен (раздражает); вибрация и вердикт-звуки остаются. Можно включить в ⚙
    ...JSON.parse(localStorage.getItem("michi_haptics") || "{}"),
  },
  // имя файла -> подпись для селектора (порядок = порядок в списке)
  TAPS: {
    drop_003: "Капля",
    tick_002: "Тик",
    select_002: "Мягкий",
    click_002: "Клик",
    pluck_002: "Струна",
    glass_002: "Стекло",
    switch_002: "Щелчок",
  },
  ctx: null,
  raw: {},        // name -> Promise<ArrayBuffer|null> (скачанный файл)
  buffers: {},    // name -> AudioBuffer (декодированный)
  // заранее качаем все нужные файлы (декодируем позже — для decode нужен жест)
  prefetch() {
    const need = [...Object.keys(this.TAPS), "confirmation_001", "error_002"];
    for (const n of need) {
      if (!this.raw[n]) this.raw[n] = fetch(`/sounds/ui/${n}.wav`)
        .then(r => (r.ok ? r.arrayBuffer() : null)).catch(() => null);
    }
  },
  ensureCtx() {
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) this.ctx = new AC();
    }
    if (this.ctx && this.ctx.state === "suspended") this.ctx.resume();
    return this.ctx;
  },
  async buffer(name) {
    if (this.buffers[name]) return this.buffers[name];
    const ctx = this.ensureCtx();
    if (!ctx) return null;
    if (!this.raw[name]) this.raw[name] = fetch(`/sounds/ui/${name}.wav`)
      .then(r => (r.ok ? r.arrayBuffer() : null)).catch(() => null);
    const ab = await this.raw[name];
    if (!ab) return null;
    try {
      this.buffers[name] = await ctx.decodeAudioData(ab.slice(0));
      return this.buffers[name];
    } catch { return null; }
  },
  play(name, gain = 0.5) {
    this.buffer(name).then(buf => {
      const ctx = this.ctx;
      if (!buf || !ctx) return;
      const src = ctx.createBufferSource();
      src.buffer = buf;
      const g = ctx.createGain();
      g.gain.value = gain;
      src.connect(g).connect(ctx.destination);
      src.start();
    });
  },
  vibrate(pattern) {
    if (navigator.vibrate &&
        !matchMedia("(prefers-reduced-motion: reduce)").matches) {
      try { navigator.vibrate(pattern); } catch { /* не поддерживается */ }
    }
  },
  tap() {
    if (!this.prefs.enabled) return;
    if (this.prefs.tapSound && this.prefs.tapSound !== "off")
      this.play(this.prefs.tapSound, 0.28);   // мягче, чем было (0.4), если пользователь включил
    this.vibrate(8);
  },
  good() {                       // мягкий «подтверждающий» звук на верный ответ
    if (!this.prefs.enabled) return;
    this.play("confirmation_001", 0.45);
    this.vibrate(12);
  },
  bad() {                        // короткий звук ошибки
    if (!this.prefs.enabled) return;
    this.play("error_002", 0.4);
    this.vibrate([10, 50, 10]);
  },
  save() {
    localStorage.setItem("michi_haptics", JSON.stringify(this.prefs));
    Prefs.push("michi_haptics");
  },
};
Haptics.prefetch();

/* «Пик» в момент нажатия (pointerdown — мгновенно, не на отпускании) для всех
   кликабельных элементов; disabled-кнопки и заблокированные уроки молчат. */
document.addEventListener("pointerdown", e => {
  const el = e.target.closest(
    "button, .lesson-card:not(.locked), .course-tab, .kanji-ex, " +
    ".kanji-parts .part:not(.whole), .lookalikes span, .hardest-list .chip, " +
    ".build-slots span");
  if (el && !el.disabled) Haptics.tap();
}, { passive: true });

/* ---------- Настройки озвучки ---------- */
const settingsModal = $("#settings");
const aboutModal = $("#about");

function fillVoiceSelect() {
  const sel = $("#set-voice");
  const warn = $("#tts-warn");
  const vvHint = $("#vv-hint");
  warn.style.display = "none";
  vvHint.style.display = "none";
  if ($("#set-source").value === "neural") {
    if (!TTS.neuralVoices.length) {
      warn.textContent = tr("Нейроголос недоступен (нужен интернет). Используйте голос браузера.");
      warn.style.display = "block";
    } else if (!TTS.neuralVoices.some(v => v.id.startsWith("vv:"))) {
      vvHint.style.display = "block";
    }
    sel.innerHTML = TTS.neuralVoices.map(v =>
      `<option value="${v.id}" ${v.id === TTS.prefs.neuralVoice ? "selected" : ""}>${v.label}</option>`
    ).join("") || `<option>— недоступно —</option>`;
  } else {
    TTS.refreshBrowser();
    if (!TTS.browserVoices.length) {
      warn.textContent = tr("В браузере нет японских голосов. Установите: Параметры Windows → Время и язык → Речь → Добавить голоса → «Японский».");
      warn.style.display = "block";
    }
    sel.innerHTML = TTS.browserVoices.map(v =>
      `<option value="${v.voiceURI}" ${TTS.browserVoice && v.voiceURI === TTS.browserVoice.voiceURI ? "selected" : ""}>
        ${v.name}${v.localService ? "" : " (онлайн)"}</option>`
    ).join("") || `<option>— нет голосов —</option>`;
  }
}

function openSettings() {
  $("#set-source").value =
    (TTS.prefs.source === "neural" && TTS.neuralVoices.length) ? "neural" : "browser";
  fillVoiceSelect();
  $("#set-volume").value = Math.round(TTS.prefs.volume * 100);
  $("#set-rate").value = Math.round(TTS.prefs.rate * 100);
  $("#val-volume").textContent = `${Math.round(TTS.prefs.volume * 100)}%`;
  $("#val-rate").textContent = `${Math.round(TTS.prefs.rate * 100)}%`;
  $("#set-romaji").value = Romaji.pref;
  $("#set-goal").value = localStorage.getItem("michi_daily_goal") || "20";
  $("#set-haptics").checked = Haptics.prefs.enabled;
  fillTapSounds();
  fillLangSelect();
  $("#set-tap-sound").disabled = !Haptics.prefs.enabled;
  AI.init().then(refreshAiStatus);   // перепроверить (вдруг ключ задали после старта)
  refreshAiStatus();
  settingsModal.classList.add("open");
}

function refreshAiStatus() {
  const pill = $("#ai-pill"), hint = $("#ai-status-hint");
  if (!pill || !hint) return;
  if (AI.available) {
    pill.textContent = AI.status.provider || tr("включён");
    pill.className = "ai-pill on";
    const q = AI.status.limit != null
      ? " " + tr("Сегодня осталось {r} из {l} запросов (кэш-разборы не тратят квоту).",
          { r: AI.status.remaining, l: AI.status.limit })
      : "";
    hint.textContent = tr("После неверного ответа жмите «Разобрать ошибку» — модель " +
      "объяснит промах. Разборы кэшируются, чтобы не платить дважды.") + q;
  } else {
    pill.textContent = tr("нет ключа");
    pill.className = "ai-pill off";
    hint.textContent = tr("Чтобы включить, задайте ключ перед запуском и перезапустите " +
      "сервер. Бесплатно: GEMINI_API_KEY (ключ на aistudio.google.com/apikey) — " +
      "set GEMINI_API_KEY=… затем run.bat. Либо ANTHROPIC_API_KEY (Claude). " +
      "Без ключа курс работает как обычно.");
  }
}

function fillTapSounds() {
  $("#set-tap-sound").innerHTML =
    Object.entries(Haptics.TAPS).map(([k, v]) =>
      `<option value="${k}" ${k === Haptics.prefs.tapSound ? "selected" : ""}>${tr(v)}</option>`).join("") +
    `<option value="off" ${Haptics.prefs.tapSound === "off" ? "selected" : ""}>${tr("Без звука")}</option>`;
}

// Переключатель языка интерфейса: смена → reload (всё перерисуется на новом языке)
function fillLangSelect() {
  $("#set-lang").innerHTML = Object.entries(LANGS).map(([code, name]) =>
    `<option value="${code}" ${code === LANG ? "selected" : ""}>${name}</option>`).join("");
}
$("#set-lang").addEventListener("change", async e => {
  setLang(e.target.value);
  Prefs.push("michi_lang");
  await Prefs.flush();              // дождаться записи на сервер до перезагрузки
  location.reload();
});
$("#btn-settings").addEventListener("click", openSettings);
$("#player-settings").addEventListener("click", openSettings);   // настройки прямо из урока
$("#set-close").addEventListener("click", () => settingsModal.classList.remove("open"));
settingsModal.addEventListener("click", e => {
  if (e.target === settingsModal) settingsModal.classList.remove("open");
});
// «О проекте и приватность» — открывается поверх настроек
$("#open-about").addEventListener("click", () => aboutModal.classList.add("open"));
$("#about-close").addEventListener("click", () => aboutModal.classList.remove("open"));
aboutModal.addEventListener("click", e => {
  if (e.target === aboutModal) aboutModal.classList.remove("open");
});
$("#set-source").addEventListener("change", e => {
  TTS.prefs.source = e.target.value;
  if (e.target.value === "neural") TTS.neuralOk = true; // дать второй шанс сети
  TTS.save();
  fillVoiceSelect();
});
$("#set-voice").addEventListener("change", e => {
  if ($("#set-source").value === "neural") TTS.prefs.neuralVoice = e.target.value;
  else { TTS.prefs.voiceURI = e.target.value; TTS.refreshBrowser(); }
  TTS.save();
});
$("#set-volume").addEventListener("input", e => {
  TTS.prefs.volume = +e.target.value / 100;
  $("#val-volume").textContent = `${e.target.value}%`;
  TTS.save();
});
$("#set-rate").addEventListener("input", e => {
  TTS.prefs.rate = +e.target.value / 100;
  $("#val-rate").textContent = `${e.target.value}%`;
  TTS.save();
});
$("#set-test").addEventListener("click", () => speak("こんにちは。ミチへようこそ。"));
$("#set-romaji").addEventListener("change", e => Romaji.set(e.target.value));
$("#set-goal").addEventListener("change", e => {
  localStorage.setItem("michi_daily_goal", e.target.value);
  Prefs.push("michi_daily_goal");
  if (document.querySelector("nav.tabs button.active")?.dataset.view === "today")
    renderToday();
});
$("#set-haptics").addEventListener("change", e => {
  Haptics.prefs.enabled = e.target.checked;
  Haptics.save();
  $("#set-tap-sound").disabled = !e.target.checked;
  if (e.target.checked) Haptics.tap();   // сразу дать услышать/почувствовать
});
$("#set-tap-sound").addEventListener("change", e => {
  Haptics.prefs.tapSound = e.target.value;
  Haptics.save();
  if (e.target.value !== "off") Haptics.play(e.target.value, 0.4);  // прослушать
});

/* ---------- Тема оформления ---------- */
const Theme = {
  pref: localStorage.getItem("michi_theme") || "auto",
  media: matchMedia("(prefers-color-scheme: dark)"),
  labels: { light: "светлая", dark: "тёмная", auto: "как в системе" },
  icons: { light: "sun", dark: "moon", auto: "themeAuto" },
  isDark() {
    return this.pref === "dark" || (this.pref === "auto" && this.media.matches);
  },
  apply() {
    const dark = this.isDark();
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    const btn = $("#btn-theme");
    btn.innerHTML = Icons.ui(this.icons[this.pref]);
    btn.title = `Тема: ${this.labels[this.pref]} (нажмите, чтобы сменить)`;
    btn.setAttribute("aria-label", btn.title);     // имя для скринридера = подсказка
    // Кнопка в плеере: показывает «куда переключим» (месяц в светлой, солнце в тёмной)
    const pbtn = document.getElementById("player-theme");
    if (pbtn) {
      pbtn.innerHTML = Icons.ui(dark ? "sun" : "moon");
      pbtn.title = dark ? "Дневной режим" : "Ночной режим";
      pbtn.setAttribute("aria-label", pbtn.title);
    }
  },
  toggle() {
    // светлая -> тёмная -> авто -> ... (авто не теряется навсегда)
    const order = ["light", "dark", "auto"];
    this.pref = order[(order.indexOf(this.pref) + 1) % order.length];
    this._save();
  },
  // Прямое переключение свет<->тьма (кнопка в уроке): фиксируем явное
  // предпочтение от текущего вида, без «авто» — чтобы ночной режим был в один тап.
  flip() {
    this.pref = this.isDark() ? "light" : "dark";
    this._save();
  },
  _save() {
    localStorage.setItem("michi_theme", this.pref);
    Prefs.push("michi_theme");
    this.apply();
  },
};
Theme.media.addEventListener("change", () => {
  if (Theme.pref === "auto") Theme.apply();
});
$("#btn-theme").addEventListener("click", () => Theme.toggle());
$("#player-theme").addEventListener("click", () => Theme.flip());
Theme.apply();
// Статичные SVG-иконки «хрома»: index.html держит кнопки пустыми до JS,
// чтобы не мигать системным глифом до подмены (см. icons.js)
$("#btn-settings").innerHTML = Icons.ui("gear");
$("#player-settings").innerHTML = Icons.ui("gear");
$("#player-close").innerHTML = Icons.ui("close");

/* ---------- Ромадзи в интерфейсе курса (2.1: отключается после хираганы) ---------- */
const Romaji = {
  pref: localStorage.getItem("michi_romaji") || "auto",  // auto | on | off
  hiraganaDone: false,
  effectiveOn() {
    if (this.pref === "on") return true;
    if (this.pref === "off") return false;
    return !this.hiraganaDone;            // авто: показываем, пока хирагана не пройдена
  },
  apply() {
    document.documentElement.dataset.romaji = this.effectiveOn() ? "on" : "off";
  },
  set(pref) {
    this.pref = pref;
    localStorage.setItem("michi_romaji", pref);
    Prefs.push("michi_romaji");
    this.apply();
  },
  /* Вызывается, когда из /api/overview известен прогресс курсов */
  syncProgress(courses) {
    const hira = courses.find(c => c.id === "hiragana");
    this.hiraganaDone = !!hira && hira.lessons_completed >= hira.lessons_total;
    this.apply();
  },
};
Romaji.apply();

/* ---------- Анимация появления экранов ----------
   dir: 0 — подъём (по умолчанию, для перерисовок и плеера); +1/-1 — горизонтальный
   въезд под направление смены вкладки (как в нативных приложениях). */
function animateIn(el, dir = 0) {
  const cls = dir > 0 ? "anim-in-right" : dir < 0 ? "anim-in-left" : "anim-in";
  el.classList.remove("anim-in", "anim-in-left", "anim-in-right");
  void el.offsetWidth; // перезапуск CSS-анимации
  el.classList.add(cls);
}

/* Плавный счёт числа 0→to (ease-out cubic). Под reduced-motion — конечное сразу. */
function countUp(el, to, dur = 650) {
  if (!el) return;
  to = +to || 0;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) { el.textContent = to; return; }
  const t0 = performance.now();
  (function f(now) {
    const p = Math.min((now - t0) / dur, 1);
    el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3)));
    if (p < 1) requestAnimationFrame(f);
  })(t0);
}

/* ---------- Скелетоны загрузки ----------
   Мерцающие плейсхолдеры под геометрию экрана вместо текста «Загрузка…»:
   воспринимается быстрее и не даёт сдвига макета (контент приходит на готовый
   каркас). Мерцание само замирает при prefers-reduced-motion (глобальное правило). */
function skeleton(kind) {
  const card = h => `<div class="skel-card" style="height:${h}px"></div>`;
  if (kind === "lessons") {
    return `<div class="skel">
      <div class="skel-tabs">${"<span></span>".repeat(4)}</div>
      <div class="skel-grid">${'<div class="skel-tile"></div>'.repeat(6)}</div></div>`;
  }
  if (kind === "today") return `<div class="skel">${card(150)}${card(92)}${card(150)}${card(120)}</div>`;
  return `<div class="skel">${card(140)}${card(116)}${card(116)}</div>`;
}

/* ---------- Конфетти на вехах (≤2 с, уважает reduced-motion) ---------- */
function confetti() {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const c = document.createElement("canvas");
  c.className = "confetti";
  c.width = innerWidth;
  c.height = innerHeight;
  document.body.appendChild(c);
  const ctx = c.getContext("2d");
  const colors = ["#EF7FA8", "#8E7CC3", "#F2A2C4", "#5CA37E", "#B49DE4"];
  const parts = Array.from({ length: 80 }, () => ({
    x: Math.random() * c.width,
    y: -30 - Math.random() * c.height * 0.25,
    s: 6 + Math.random() * 6,
    vy: 2.2 + Math.random() * 3,
    vx: -1.5 + Math.random() * 3,
    r: Math.random() * Math.PI,
    vr: -0.1 + Math.random() * 0.2,
    color: colors[(Math.random() * colors.length) | 0],
  }));
  const t0 = performance.now();
  (function frame(now) {
    const t = now - t0;
    ctx.clearRect(0, 0, c.width, c.height);
    for (const p of parts) {
      p.x += p.vx; p.y += p.vy; p.r += p.vr;
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.r);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = Math.max(1 - t / 1800, 0);
      ctx.fillRect(-p.s / 2, -p.s / 2, p.s, p.s * 0.6);
      ctx.restore();
    }
    if (t < 1800) requestAnimationFrame(frame);
    else c.remove();
  })(t0);
}

/* ---------- Достижения: тихая сверка + оверлей «получено» ----------
   Источник правды — /api/achievements (вычисляется из журналов на сервере).
   michi_ach_seen хранит то, что игрок уже видел; диф = свежие. На старте сверяем
   молча (celebrate=false), чтобы засеять базу и не салютовать импортированную
   историю; после урока/сессии и в Статистике — с оверлеем. */
const TIER_LABEL = { bronze: "Бронза", silver: "Серебро", gold: "Золото", legend: "Легенда" };

async function checkAchievements(celebrate, ach) {
  if (!ach) {
    try { ach = await api.get("/api/achievements"); }
    catch { return null; }   // ИИ/сеть недоступны — курс работает как раньше
  }
  const prev = localStorage.getItem("michi_ach_seen");   // null => база ещё не засеяна
  const seen = new Set(JSON.parse(prev || "[]"));
  const unlocked = ach.items.filter(a => a.unlocked);
  const fresh = unlocked.filter(a => !seen.has(a.id));
  localStorage.setItem("michi_ach_seen", JSON.stringify(unlocked.map(a => a.id)));
  if (celebrate && prev !== null && fresh.length) await celebrateAchievements(fresh);
  return ach;
}

async function celebrateAchievements(list) {   // несколько сразу — показываем в очередь
  for (const a of list) await celebrateOne(a);
}

function celebrateOne(a) {
  return new Promise(resolve => {
    const el = document.createElement("div");
    el.className = `ach-pop ${a.tier}`;
    el.innerHTML = `
      <div class="ach-pop-card">
        <div class="ach-pop-art">
          <div class="ach-pop-rays"></div>
          <div class="ach-pop-disc">${Art.tile(a, true)}</div>
        </div>
        <div class="ach-pop-tier">${tr(TIER_LABEL[a.tier] || "")}</div>
        <div class="ach-pop-kicker">${tr("Достижение получено")}</div>
        <h3 class="ach-pop-title">${tr(a.title)}</h3>
        <p class="ach-pop-desc">${tr(a.desc)}</p>
        <button class="primary ach-pop-ok">${tr("Круто!")}</button>
      </div>`;
    document.body.appendChild(el);
    requestAnimationFrame(() => el.classList.add("show"));
    confetti();
    Haptics.good();
    const close = () => {
      el.classList.remove("show");
      setTimeout(() => { el.remove(); resolve(); }, 280);
    };
    el.querySelector(".ach-pop-ok").addEventListener("click", close, { once: true });
    el.addEventListener("click", e => { if (e.target === el) close(); });  // клик по фону
  });
}

/* ---------- Лепестки сакуры на фоне (тихая анимация, ~12 шт.) ----------
   Уважает prefers-reduced-motion; останавливается на скрытой вкладке. */
(function petals() {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const c = document.createElement("canvas");
  c.id = "petals";
  document.body.appendChild(c);
  const ctx = c.getContext("2d");
  let W, H;
  const resize = () => { W = c.width = innerWidth; H = c.height = innerHeight; };
  resize();
  addEventListener("resize", resize);

  const COUNT = Math.max(8, Math.min(14, Math.round(innerWidth / 90)));
  const mk = onTop => ({
    x: Math.random() * W,
    y: onTop ? -20 : Math.random() * H,
    s: 5 + Math.random() * 5,            // размер
    vy: 0.25 + Math.random() * 0.4,      // скорость падения
    drift: 0.4 + Math.random() * 0.9,    // амплитуда покачивания
    phase: Math.random() * Math.PI * 2,
    rot: Math.random() * Math.PI * 2,
    vrot: -0.012 + Math.random() * 0.024,
    hue: Math.random(),                  // розовый ↔ лавандовый
  });
  const parts = Array.from({ length: COUNT }, () => mk(false));

  function petalColor(p, dark) {
    const a = dark ? 0.22 : 0.4;
    return p.hue < 0.7
      ? `rgba(239, 127, 168, ${a})`     // сакура
      : `rgba(167, 143, 216, ${a * 0.9})`; // лаванда
  }

  function frame(now) {
    const dark = document.documentElement.dataset.theme === "dark";
    ctx.clearRect(0, 0, W, H);
    for (const p of parts) {
      p.phase += 0.008;
      p.y += p.vy;
      p.x += Math.sin(p.phase) * p.drift * 0.4 + 0.08;
      p.rot += p.vrot;
      if (p.y > H + 20 || p.x > W + 30) Object.assign(p, mk(true));
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot + Math.sin(p.phase) * 0.35);
      ctx.fillStyle = petalColor(p, dark);
      // лепесток: две дуги, сужающиеся к черенку
      ctx.beginPath();
      ctx.moveTo(0, -p.s);
      ctx.quadraticCurveTo(p.s * 0.9, -p.s * 0.3, 0, p.s);
      ctx.quadraticCurveTo(-p.s * 0.9, -p.s * 0.3, 0, -p.s);
      ctx.fill();
      ctx.restore();
    }
    if (!document.hidden) requestAnimationFrame(frame);
  }
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) requestAnimationFrame(frame);
  });
  requestAnimationFrame(frame);
})();

/* ---------- Доступность модальных оверлеев: focus-trap + изоляция фона ----------
   Оверлеи (#player/#settings/#confirm/#about/#onboarding) открываются классом
   .open в разных местах кода. Вместо правок каждого места — наблюдаем за классом
   через MutationObserver и на открытии: переносим фокус внутрь, запираем Tab в
   пределах ВЕРХНЕГО оверлея, делаем фон inert (и для клавиатуры, и для
   скринридера). На закрытии возвращаем фокус инициатору. Стек поддерживает
   вложенность (about поверх settings, confirm поверх player). */
const ModalA11y = {
  SEL: "a[href],button:not([disabled]),input:not([disabled]),select:not([disabled])," +
       'textarea:not([disabled]),[tabindex]:not([tabindex="-1"])',
  _stack: [],
  bg() { return [document.getElementById("app"), document.querySelector("nav.tabs")]; },

  watch(el) {
    if (!el) return;
    new MutationObserver(() => {
      const open = el.classList.contains("open");
      if (open === !!el._a11yOpen) return;
      el._a11yOpen = open;
      if (open) this._open(el); else this._close(el);
    }).observe(el, { attributes: true, attributeFilter: ["class"] });
  },

  _focusables(el) {
    return [...el.querySelectorAll(this.SEL)].filter(n => n.offsetParent !== null);
  },

  _top() { return this._stack.length ? this._stack[this._stack.length - 1].el : null; },

  _refresh() {
    const top = this._top();
    for (const b of this.bg()) if (b) b.inert = !!top;
    for (const s of this._stack) s.el.inert = (s.el !== top);   // нижние слои inert
  },

  _open(el) {
    this._stack.push({ el, opener: document.activeElement });
    el._trap = e => this._onKey(e, el);
    el.addEventListener("keydown", el._trap);
    this._refresh();
    // display:flex применяется тем же тиком — фокус переносим в следующем кадре
    requestAnimationFrame(() => {
      if (!el.classList.contains("open")) return;
      (this._focusables(el)[0] || el).focus();
    });
  },

  _close(el) {
    if (el._trap) { el.removeEventListener("keydown", el._trap); el._trap = null; }
    const i = this._stack.findIndex(s => s.el === el);
    const entry = i >= 0 ? this._stack.splice(i, 1)[0] : null;
    el.inert = false;
    this._refresh();
    const o = entry && entry.opener;     // вернуть фокус на элемент-инициатор
    if (o && o.isConnected && o.focus) o.focus();
  },

  _onKey(e, el) {
    if (e.key !== "Tab" || this._top() !== el) return;   // запирает только верхний
    const f = this._focusables(el);
    if (!f.length) { e.preventDefault(); return; }
    const first = f[0], last = f[f.length - 1], a = document.activeElement;
    if (e.shiftKey && (a === first || !el.contains(a))) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && (a === last || !el.contains(a))) { e.preventDefault(); first.focus(); }
  },
};
["#player", "#settings", "#confirm", "#about", "#onboarding"].forEach(
  sel => ModalA11y.watch($(sel)));

/* Enter/Space продолжают сессию, когда на экране есть кнопка «Дальше» */
document.addEventListener("keydown", e => {
  if (e.key !== "Enter" && e.key !== " ") return;
  if (!$("#player").classList.contains("open")) return;
  // Не перехватывать пробел/Enter, когда фокус в поле свободного ввода: иначе
  // пробел не печатается, а Enter дублировал бы собственный сабмит поля (N1).
  const a = document.activeElement;
  if (a && (a.tagName === "INPUT" || a.tagName === "TEXTAREA" || a.isContentEditable)) return;
  const btn = $("#player-body").querySelector("#next, #finish, #check");
  if (btn) { e.preventDefault(); btn.click(); }
});

/* ---------- Роутер вкладок ---------- */
const view = $("#view");
const renderers = { today: renderToday, lessons: renderLessons, review: renderReviewTab, stats: renderStats, dict: renderDict };
const TAB_ORDER = ["today", "lessons", "review", "stats", "dict"];
let _curTab = "today";

function show(name) {
  // Направление перехода между вкладками — для горизонтального въезда контента
  const dir = Math.sign(TAB_ORDER.indexOf(name) - TAB_ORDER.indexOf(_curTab));
  _curTab = name;
  document.querySelectorAll("nav.tabs button").forEach(b => {
    const on = b.dataset.view === name;
    b.classList.toggle("active", on);
    if (on) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
  });
  // Граница ошибки: упавший рендер (обрыв сети на /api/overview и т.п.) не должен
  // оставлять скелетон навсегда — показываем восстановимое состояние с «Повторить».
  Promise.resolve(renderers[name]())
    .then(() => animateIn(view, dir))
    .catch(err => {
      console.error(err);
      view.innerHTML = `
        <div class="card empty-state error-state" role="alert">
          <div class="empty-mascot">${Art.mascotTile("wave")}</div>
          <p class="note center">${tr("Не удалось загрузить. Проверьте соединение.")}</p>
          <button class="primary" id="retry-view">${tr("Повторить")}</button>
        </div>`;
      $("#retry-view")?.addEventListener("click", () => show(name));
      animateIn(view, 0);
    });
}
document.querySelectorAll("nav.tabs button").forEach(b =>
  b.addEventListener("click", () => show(b.dataset.view)));

function setStreakPill(streak) {
  const pill = $("#streak-pill");
  // Единственное место для серии — пилюля в шапке (видна на всех вкладках)
  const dayWord = LANG === "en"
    ? (streak === 1 ? "day" : "days")
    : plural(streak, ["день", "дня", "дней"]);
  pill.innerHTML = `${Icons.ui("flame")} ${streak} ${dayWord}`;
  pill.style.display = streak > 0 ? "" : "none";
}

/* ---------- Сегодня ---------- */
function greeting() {
  const h = new Date().getHours();
  if (h < 5) return ["こんばんは", "Доброй ночи"];
  if (h < 12) return ["おはよう", "Доброе утро"];
  if (h < 18) return ["こんにちは", "Добрый день"];
  return ["こんばんは", "Добрый вечер"];
}

async function renderToday() {
  view.innerHTML = skeleton("today");
  const o = await getOverview();
  setStreakPill(o.streak);
  Romaji.syncProgress(o.courses);
  const next = o.next_lesson;
  const queueTotal = o.srs.due + o.srs.new_available;
  const [jp, ru] = greeting();
  const estMin = Math.max(1, Math.round(queueTotal * 0.15));
  // Геймификация: уровень аккаунта + дневная цель (цель — клиентская настройка)
  const goal = +(localStorage.getItem("michi_daily_goal") || 20);
  const todayXp = o.xp.today;
  const goalPct = Math.min(100, Math.round(todayXp / goal * 100));
  const goalMet = todayXp >= goal;
  // Одноразовое пояснение в момент авто-скрытия ромадзи после хираганы
  const romajiNote = (Romaji.pref === "auto" && Romaji.hiraganaDone &&
    !localStorage.getItem("michi_romaji_note"))
    ? `<p class="note">${tr("Хирагана пройдена — ромадзи скрыт, чтобы вы читали каной.\n       Вернуть можно в ⚙ настройках.")}</p>`
    : "";
  if (romajiNote) localStorage.setItem("michi_romaji_note", "1");
  // «Правило 2 тапов» (SRS 11.2): одна главная кнопка дня прямо в герое —
  // очередь SRS, а когда она пуста — следующий урок. У новичка (ни XP, ни
  // серии) вместо мёртвых нулей статистики — только приглашение к первому уроку.
  const freshUser = o.xp.total === 0 && o.streak === 0;
  const heroAct = queueTotal
    ? { fn: startReview, label: tr("Начать сессию · {n} · ≈{m} мин", { n: queueTotal, m: estMin }) }
    : next
      ? { fn: () => startLesson(next.id), label: freshUser ? tr("Начать первый урок") : tr("Начать урок") }
      : null;

  view.innerHTML = `
    <div class="today stagger">
    <div class="hero">
      <div class="hero-top">
        <div>
          <div class="hero-jp jp" data-tts="${jp}">${jp}！</div>
          <div class="hero-ru">${tr(ru)}</div>
        </div>
        <div class="hero-mascot">${Art.mascotTile("wave")}</div>
      </div>
      ${freshUser ? "" : `<div class="hero-stats">
        ${o.streak > 0 ? `<div class="hs hs-streak"><b>${Icons.ui("flame")} ${o.streak}</b><span>${tr("серия дней")}</span></div>` : ""}
        <div class="hs"><b>${o.today.reviews}</b><span>${tr("повторено сегодня")}</span></div>
        <div class="hs"><b>${o.today.accuracy !== null ? o.today.accuracy + "%" : "—"}</b><span>${tr("точность сегодня")}</span></div>
      </div>`}
      ${heroAct ? `<button class="hero-cta" id="hero-cta">${heroAct.label}</button>` : ""}
    </div>
    ${o.streak > 0 && o.today.reviews === 0 ? `<div class="streak-nudge">${Icons.ui("flame")} ${tr("Серия {n} дн. — позанимайтесь сегодня, чтобы не прервать её", { n: o.streak })}</div>` : ""}

    <div class="card gami">
      <div class="level-badge">
        <div class="lvl-num">${o.xp.level}</div>
        <div class="lvl-meta">
          <div class="lvl-title">${tr("Уровень {n}", { n: o.xp.level })}</div>
          <div class="lvl-bar"><div style="width:${o.xp.percent}%"></div></div>
          <div class="lvl-xp">${tr("{a} / {b} XP · всего {c}", { a: o.xp.into_level, b: o.xp.level_span, c: o.xp.total })}</div>
        </div>
      </div>
      <div class="goal-ring ${goalMet ? "met" : ""}" style="--p:${goalPct}">
        <div class="goal-inner">
          <b>${goalMet ? "✓" : todayXp}</b>
          <span>${goalMet ? tr("цель!") : tr("/ {g} XP", { g: goal })}</span>
        </div>
      </div>
    </div>

    ${o.season ? `<div class="card season-card" data-tts="${o.season.reading}" title="${tr("Послушать")}">
      <span class="se-emoji" aria-hidden="true">${o.season.emoji}</span>
      <div class="se-text">
        <div class="se-head"><span class="se-kanji jp">${o.season.kanji}</span><span class="se-reading jp">${o.season.reading}</span></div>
        <div class="se-ru">${tr(o.season.ru)}</div>
      </div>
      <span class="se-tag jp">季節</span>
    </div>` : ""}

    <div class="card">
      <h2>${tr("План на сегодня")}</h2>
      <div class="plan-item ${queueTotal ? "" : "done"}">
        <div class="pi-ico jp c3">復</div>
        <div class="pi-info">
          <div class="t">${tr("Повторение")}</div>
          <div class="s">${queueTotal
            ? `${o.srs.due ? tr("по расписанию: {n}", { n: o.srs.due }) : ""}${o.srs.due && o.srs.new_available ? " · " : ""}${o.srs.new_available ? tr("новых: {n}", { n: o.srs.new_available }) : ""} · ${tr("≈{m} мин", { m: estMin })}`
            : tr("Очередь пуста — всё повторено")}</div>
        </div>
        ${queueTotal
          ? `<button class="mini-btn" id="btn-review">${tr("Начать")}</button>`
          : `<span class="pi-done">✓</span>`}
      </div>
      <div class="plan-item ${next ? "" : "done"}">
        <div class="pi-ico jp c0">道</div>
        <div class="pi-info">
          <div class="t">${tr("Новый урок")}</div>
          <div class="s">${next ? `${tr(next.title)} · ${tr(next.subtitle)}` : tr("Все доступные уроки пройдены")}</div>
        </div>
        ${next
          ? `<button class="mini-btn indigo" id="btn-lesson">${tr("Учить")}</button>`
          : `<span class="pi-done">✓</span>`}
      </div>
      ${(o.upcoming || 0) ? `
      <div class="plan-item">
        <div class="pi-ico jp c1">予</div>
        <div class="pi-info">
          <div class="t">${tr("Освежить заранее")}</div>
          <div class="s">${tr("{n} скоро потускнеют — повторите, пока легко", { n: o.upcoming })}</div>
        </div>
        <button class="mini-btn indigo" id="btn-freshen">${tr("Освежить")}</button>
      </div>` : ""}
    </div>

    <div class="card">
      <h2>${tr("Прогресс курсов")}</h2>
      ${o.courses.map(c => `
      <div class="course-row">
        <span class="cr-title">${tr(COURSE_LABEL[c.id] || c.title)}</span>
        <div class="progress"><div style="width:${Math.round(c.lessons_completed / c.lessons_total * 100)}%"></div></div>
        <span class="cr-num">${c.lessons_completed}/${c.lessons_total}</span>
      </div>`).join("")}
      <p class="note">${tr("Катакану можно учить параллельно с хираганой, слова N5 откроются после хираганы.")}</p>
    </div>
    ${romajiNote}
    </div>`;
  // Цель дня достигнута впервые сегодня — поздравляем (раз в день)
  const todayKey = new Date().toISOString().slice(0, 10);
  if (goalMet && localStorage.getItem("michi_goal_day") !== todayKey) {
    localStorage.setItem("michi_goal_day", todayKey);
    confetti();
  }
  // Награда-анимация: уровень-бар заливается, кольцо цели «свайпит», XP считается.
  // Запускаем на следующем кадре, выставив старт из 0 → CSS-переходы оживают.
  requestAnimationFrame(() => {
    const bar = view.querySelector(".lvl-bar > div");
    if (bar) { const w = bar.style.width; bar.style.width = "0%"; void bar.offsetWidth; bar.style.width = w; }
    const ring = view.querySelector(".goal-ring");
    if (ring && !goalMet) { ring.style.setProperty("--p", "0"); void ring.offsetWidth; ring.style.setProperty("--p", goalPct); }
    if (!goalMet) countUp(view.querySelector(".goal-inner b"), todayXp);
  });
  $("#btn-review")?.addEventListener("click", startReview);
  $("#btn-lesson")?.addEventListener("click", () => startLesson(next.id));
  $("#btn-freshen")?.addEventListener("click", startFreshen);
  if (heroAct) $("#hero-cta")?.addEventListener("click", heroAct.fn);
}

/* ---------- Путь: регионы и сетка уроков ---------- */
const COURSE_OF = { l: "hiragana", k: "katakana", v: "n5", j: "kanji", g: "grammar" };
const COURSE_LABEL = { all: "Все", hiragana: "Хирагана", katakana: "Катакана", n5: "Первые слова", kanji: "Кандзи", grammar: "Грамматика" };
let lessonFilter = localStorage.getItem("michi_lesson_filter") || "all";

async function renderLessons() {
  view.innerHTML = skeleton("lessons");
  const lessons = await api.get("/api/lessons");

  // Курсы в порядке появления — для переключателя
  const present = [];
  for (const l of lessons) {
    const c = COURSE_OF[l.id[0]] || "other";
    if (!present.includes(c)) present.push(c);
  }
  const filters = ["all", ...present];
  if (!filters.includes(lessonFilter)) lessonFilter = "all";

  const paint = () => {
    const shown = lessonFilter === "all"
      ? lessons
      : lessons.filter(l => (COURSE_OF[l.id[0]] || "other") === lessonFilter);

    // Группировка по «регионам» с сохранением порядка
    const groups = [];
    for (const l of shown) {
      let g = groups[groups.length - 1];
      if (!g || g.id !== l.group.id) {
        g = { ...l.group, lessons: [] };
        groups.push(g);
      }
      g.lessons.push(l);
    }

    const tabs = `<div class="course-tabs">${filters.map(f =>
      `<button class="course-tab ${f === lessonFilter ? "active" : ""}" data-f="${f}">${tr(COURSE_LABEL[f] || f)}</button>`
    ).join("")}</div>`;

    view.innerHTML = tabs + groups.map(g => {
      const doneCount = g.lessons.filter(l => l.status === "completed").length;
      return `
      <div class="region-h">
        <span class="t">${tr(g.title)}</span>
        <span class="jp">${g.jp}</span>
        <span class="spacer"></span>
        <span class="region-progress ${doneCount === g.lessons.length ? "done" : ""}">
          ${doneCount === g.lessons.length ? "✓ " : ""}${tr("{a} из {b}", { a: doneCount, b: g.lessons.length })}</span>
      </div>
      <div class="lesson-grid">
        ${g.lessons.map(l => {
          // Карточка урока доступна с клавиатуры (role=button + tabindex): без
          // этого экран «Путь» был недостижим без мыши (a11y). aria-label несёт
          // название и статус; декоративные иконка/замок скрыты от скринридера.
          const statusWord = l.status === "completed" ? tr("пройден")
            : l.status === "locked" ? tr("закрыто") : tr("доступен");
          return `
          <div class="lesson-card ${l.status} ${l.type === "gate_test" ? "gate" : ""}"
               role="button" tabindex="0" aria-disabled="${l.status === "locked"}"
               aria-label="${escAttr(`${tr(l.title)}. ${statusWord}`)}"
               data-id="${l.id}" data-status="${l.status}">
            <div class="circle jp c${lessons.indexOf(l) % 6}" aria-hidden="true">${l.icon}</div>
            ${l.status === "completed"
              ? `<span class="state done">✓ ${l.score != null ? Math.round(l.score * 100) + "%" : ""}</span>`
              : l.status === "locked" ? `<span class="state lock" aria-hidden="true">${Icons.ui("lock")}</span>` : ""}
            <h3>${tr(l.title)}</h3>
            <div class="tag">${tr(l.subtitle)}${l.kana_count ? ` · ${tr("{n} знаков", { n: l.kana_count })}` : ""}${l.locked_hint ? `<br>${tr(l.locked_hint)}` : ""}</div>
          </div>`;}).join("")}
      </div>`;
    }).join("");

    view.querySelectorAll(".course-tab").forEach(b =>
      b.addEventListener("click", () => {
        lessonFilter = b.dataset.f;
        localStorage.setItem("michi_lesson_filter", lessonFilter);
        paint();
        animateIn(view);
      }));
    view.querySelectorAll(".lesson-card").forEach(el => {
      const activate = () => {
        if (el.dataset.status !== "locked") startLesson(el.dataset.id);
      };
      el.addEventListener("click", activate);
      // Enter/Space активируют карточку (она role=button) — клавиатурный паритет
      el.addEventListener("keydown", e => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); activate(); }
      });
    });
  };

  paint();
}

/* ---------- Стилизованный диалог подтверждения (вместо confirm()) ---------- */
function confirmDialog(text, yesLabel = tr("Выйти")) {
  return new Promise(res => {
    const m = $("#confirm");
    $("#confirm-text").textContent = text;
    $("#confirm-yes").textContent = yesLabel;
    m.classList.add("open");
    const done = v => { m.classList.remove("open"); res(v); };
    $("#confirm-yes").onclick = () => done(true);
    $("#confirm-no").onclick = () => done(false);
    m.onclick = e => { if (e.target === m) done(false); };
  });
}

/* Краткое всплывающее уведомление (вместо нативного alert) — не ломает визуальный
   язык, объявляется скринридером (role=status). Сам исчезает через ~3 с. */
function toast(msg, isError = false) {
  const t = document.createElement("div");
  t.className = "toast" + (isError ? " err" : "");
  t.setAttribute("role", "status");
  t.setAttribute("aria-live", "polite");
  t.textContent = msg;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.classList.add("show"));
  setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 300); }, 3200);
}

/* ---------- Плеер (общий для уроков и SRS) ---------- */
const player = $("#player");
const playerBody = $("#player-body");
let sessionToken = 0;
let playerMode = "lesson"; // lesson | review — для текста диалога выхода
// Снятие document-обработчиков текущего упражнения: без этого выход из
// сессии посреди вопроса оставляет слушатель клавиш 1–4 навсегда, и позднее
// нажатие цифры «отвечает» на брошенную карточку (фантомная озвучка + POST)
let exerciseCleanup = null;

/* Прерываемое ожидание шага. Выход из сессии (closePlayer) должен ЗАВЕРШИТЬ
   ожидание текущего шага, а не оставить его «висеть»: иначе async-функция
   упражнения остаётся приостановленной навсегда, удерживая отсоединённый DOM
   (утечка), и позднее может дорисовать «фантомный» ответ. abortable(executor)
   ведёт себя как new Promise(executor), но дополнительно резолвится в ABORT,
   когда вызывается fireAbort(). Набор покрывает и одновременные ожидания
   (Promise.race в экране проваленных ворот). Каждое упражнение после await
   проверяет `=== ABORT` и тихо выходит — сессионный цикл затем видит смену
   токена и завершается. */
const ABORT = Symbol("abort");
const _abortWaiters = new Set();
function abortable(executor) {
  return new Promise(resolve => {
    const onAbort = () => resolve(ABORT);
    _abortWaiters.add(onAbort);
    executor(value => { _abortWaiters.delete(onAbort); resolve(value); });
  });
}
function fireAbort() {
  const waiters = [..._abortWaiters];
  _abortWaiters.clear();
  for (const w of waiters) w();
}

function openPlayer(mode) {
  sessionToken++;
  playerMode = mode;
  const labels = { review: "Повторение", practice: "Работа над ошибками",
                   freshen: "Упреждающее повторение", listen: "Тренировка слуха",
                   calligraphy: "Каллиграфия 書道", forge: "Кузница кандзи 鍛冶",
                   shiritori: "Сиритори しりとり", counters: "Счётные слова 助数詞",
                   pitch: "Высотное ударение 高低", story: "Свиток истории 物語",
                   confusion: "Радар путаницы", exam: "Пробный тест N5" };
  player.setAttribute("aria-label", tr(labels[mode] || "Урок"));
  player.classList.add("open");
  resetProgress();
  Combo.reset();
  $("#player-counter").textContent = "";
  return sessionToken;
}

/* Серия верных ответов внутри сессии — лёгкий мотиватор (огонёк N), сброс на ошибке. */
const Combo = {
  n: 0, el: null,
  _box() { return this.el || (this.el = document.getElementById("combo")); },
  reset() { this.n = 0; const el = this._box(); if (el) { el.hidden = true; el.className = "combo"; } },
  update(correct) {
    const el = this._box();
    if (!correct) return this.reset();
    this.n++;
    if (!el) return;
    if (this.n < 3) { el.hidden = true; return; }
    el.hidden = false;
    el.innerHTML = `${Icons.ui("flame")} ${this.n}`;
    el.classList.toggle("milestone", this.n % 5 === 0);   // вехи 5/10/15 — ярче
    el.classList.remove("bump"); void el.offsetWidth; el.classList.add("bump");
  },
};
function closePlayer() {
  sessionToken++;
  if (exerciseCleanup) exerciseCleanup();
  fireAbort();                 // завершить ожидание текущего шага (без зависших фреймов)
  player.classList.remove("open");
  invalidateOverview();        // за сессию изменились серия/XP/очередь — обновить
  show("today");
}
async function askClosePlayer() {
  const msg = playerMode === "lesson"
    ? tr("Выйти из урока? Потом продолжите с этого же места.")
    : playerMode === "practice"
      ? tr("Прервать разбор ошибок?")
      : playerMode === "listen"
        ? tr("Прервать тренировку слуха?")
        : playerMode === "calligraphy"
          ? tr("Закрыть каллиграфию? Несохранённый рисунок пропадёт.")
          : playerMode === "forge"
            ? tr("Прервать ковку кандзи?")
            : playerMode === "shiritori"
              ? tr("Прервать сиритори?")
              : playerMode === "story"
                ? tr("Закрыть свиток?")
                : playerMode === "pitch"
                  ? tr("Прервать тренировку тона?")
                : playerMode === "confusion"
                  ? tr("Прервать тренировку различения?")
                : playerMode === "counters"
                  ? tr("Прервать тренировку счётных слов?")
                : tr("Прервать повторение? Все ответы уже сохранены.");
  if (await confirmDialog(msg)) closePlayer();
}
$("#player-close").addEventListener("click", askClosePlayer);
document.addEventListener("keydown", e => {
  if (e.key !== "Escape") return;
  if ($("#confirm").classList.contains("open")) { $("#confirm-no").click(); return; } // отмена
  if (aboutModal.classList.contains("open")) aboutModal.classList.remove("open");
  else if (settingsModal.classList.contains("open")) settingsModal.classList.remove("open");
  else if (player.classList.contains("open")) askClosePlayer();
});
// Полоса прогресса не едет назад в пределах сессии: при дозагрузке очереди SRS
// знаменатель растёт и «сырая» доля может уменьшиться — это читалось бы как откат.
let _progress = 0;
function setProgress(frac) {
  _progress = Math.max(_progress, Math.min(1, Math.max(0, frac || 0)));
  $("#player-progress").style.width = `${Math.round(_progress * 100)}%`;
}
function resetProgress() {
  _progress = 0;
  $("#player-progress").style.width = "0%";
}
document.addEventListener("click", e => {
  const t = e.target.closest("[data-tts]");
  if (t) speak(t.dataset.tts);
});
/* Тач: у столбиков графиков нет hover-подсказки — показываем значение по тапу
   (на устройствах без курсора), на десктопе остаётся нативный title. */
document.addEventListener("click", e => {
  const el = e.target.closest(".bars .bar, .mm-cell");
  if (el && el.title && matchMedia("(hover: none)").matches) toast(el.title);
});

function waitClick(el) {
  return abortable(res => el.addEventListener("click", res, { once: true }));
}

/* Выбор варианта мышью или клавишами 1–N; обработчик клавиш снимается и при
   ответе, и при закрытии сессии (exerciseCleanup). На выходе из сессии ожидание
   резолвится в ABORT (см. abortable) — вызывающий тихо завершает упражнение. */
function awaitChoice(buttons) {
  return abortable(res => {
    const cleanup = () => {
      document.removeEventListener("keydown", onKey);
      exerciseCleanup = null;
    };
    const finish = i => { cleanup(); res(i); };
    const onKey = e => {
      const n = +e.key;
      if (n >= 1 && n <= buttons.length) finish(n - 1);
    };
    exerciseCleanup = cleanup;
    buttons.forEach(b => b.addEventListener("click", () => finish(+b.dataset.i)));
    document.addEventListener("keydown", onKey);
  });
}

/* ---------- Рендер шагов урока ---------- */
async function showIntroText(step) {
  playerBody.innerHTML = `
    <div class="intro-screen">
      ${step.icon ? `<div class="intro-ico jp c4">${step.icon}</div>` : ""}
      <h2 class="intro-title">${tr(step.title)}</h2>
      ${step.subtitle ? `<div class="intro-sub">${tr(step.subtitle)}</div>` : ""}
      <p class="intro-text">${tr(step.text)}</p>
    </div>
    <div class="spacer"></div>
    <button class="primary" id="next">${tr("Начать")}</button>`;
  animateIn(playerBody);
  await waitClick($("#next", playerBody));
}

// Экранирование текста в значение атрибута (своя мнемоника — ввод пользователя)
const escAttr = s => escapeHtml(s).replace(/"/g, "&quot;");

// Блок «выбери ассоциацию» в интро (только RU — мнемоники русскоязычные)
function mnemoChoiceHtml(char, presets) {
  presets = presets || [];
  const opts = Mnemo.options(char, presets);
  const fav = Mnemo.fav(char);
  const isFav = o => o.custom ? fav === "custom"
    : (typeof fav === "number" ? presets.indexOf(o.text) === fav : presets.indexOf(o.text) === 0);
  const row = o => {
    const val = o.custom ? "custom" : presets.indexOf(o.text);
    const on = isFav(o);
    return `<button type="button" class="mnemo-opt ${on ? "fav" : ""}" data-val="${val}">
       <span class="mnemo-star">${on ? "★" : "☆"}</span>
       <span class="mnemo-text">${escapeHtml(o.text)}</span></button>`;
  };
  return `<div class="mnemo-block" data-char="${escAttr(char)}">
    <p class="mnemo-head">${tr("Ассоциация — отметь, что лучше запомнится")}</p>
    <div class="mnemo-choices">${opts.map(row).join("")}</div>
    <input class="mnemo-custom" maxlength="120"
      placeholder="${tr("…или впиши свою")}" value="${escAttr(Mnemo.custom(char))}">
  </div>`;
}

// Кандзи: только «впиши свою» (пресетов-картинок у кандзи две — образ и чтение,
// их не ранжируем; своя заметка — отдельный личный крючок).
function customMnemoHtml(char) {
  const c = Mnemo.custom(char);
  return `<div class="mnemo-block mnemo-own" data-char="${escAttr(char)}">
    ${c ? `<p class="mnemo-head">✎ ${tr("Твоя ассоциация")}</p>` +
          `<div class="mnemo-own-text">${escapeHtml(c)}</div>` : ""}
    <input class="mnemo-custom" maxlength="140"
      placeholder="${tr("…впиши свою ассоциацию")}" value="${escAttr(c)}">
  </div>`;
}
function bindCustomMnemo(root) {
  const block = root.querySelector(".mnemo-own");
  if (!block) return;
  const char = block.dataset.char;
  const inp = block.querySelector(".mnemo-custom");
  inp.onchange = () => {
    Mnemo.setCustom(char, inp.value);
    block.outerHTML = customMnemoHtml(char);
    bindCustomMnemo(root);
  };
}

function bindMnemo(root) {
  const block = root.querySelector(".mnemo-block");
  if (!block) return;
  const char = block.dataset.char;
  const presets = block._presets || [];
  block.querySelectorAll(".mnemo-opt").forEach(btn => btn.onclick = () => {
    const val = btn.dataset.val === "custom" ? "custom" : Number(btn.dataset.val);
    Mnemo.setFav(char, val);
    Haptics.tap && Haptics.tap();
    block.querySelectorAll(".mnemo-opt").forEach(b => {
      const on = (b.dataset.val === "custom") ? (val === "custom") : (Number(b.dataset.val) === val);
      b.classList.toggle("fav", on);
      b.querySelector(".mnemo-star").textContent = on ? "★" : "☆";
    });
  });
  const inp = block.querySelector(".mnemo-custom");
  if (inp) inp.onchange = () => {
    const had = !!Mnemo.custom(char);
    Mnemo.setCustom(char, inp.value);
    if (inp.value.trim() && !had) Mnemo.setFav(char, "custom");  // вписал — сразу его в фавориты
    const fresh = mnemoChoiceHtml(char, presets);
    block.outerHTML = fresh;
    const nb = root.querySelector(".mnemo-block");
    if (nb) nb._presets = presets;
    bindMnemo(root);
  };
}

// Краткий отклик на ответ (сдержанно): подсветка края экрана + печать ✓ на верный
function answerFx(correct, glyphEl) {
  const fl = document.getElementById("fx-flash");
  if (fl) { fl.className = ""; void fl.offsetWidth; fl.className = correct ? "ok" : "bad"; }
  if (correct) {
    const s = document.createElement("div");
    s.className = "answer-stamp"; s.textContent = "✓";
    document.body.appendChild(s);
    setTimeout(() => s.remove(), 900);
  } else if (glyphEl) {
    glyphEl.classList.remove("fx-shake"); void glyphEl.offsetWidth; glyphEl.classList.add("fx-shake");
  }
}

// Напоминание ассоциации при ошибке (только RU): личный фаворит знака +
// «не путай» с похожим, если выбрали именно его (опирается на ex.confusables).
function mountMnemoReminder(host, ex, choice) {
  if (LANG !== "ru") return;
  let html = "";
  const fav = (ex.mnemonics && ex.mnemonics.length)
    ? Mnemo.favText(ex.item_id, ex.mnemonics) : null;
  if (fav)
    html += `<div class="mnemo-remind"><span class="mr-char jp">${escapeHtml(ex.item_id)}</span>` +
            `<span><b>${tr("Вспомни")}:</b> ${escapeHtml(fav)}</span></div>`;
  const own = Mnemo.custom(ex.item_id);
  if (own && own !== fav)
    html += `<div class="mnemo-remind own"><span class="mr-char">✎</span>` +
            `<span><b>${tr("Твоя заметка")}:</b> ${escapeHtml(own)}</span></div>`;
  const chosen = ex.options[choice];
  if (ex.confusables && ex.confusables[chosen])
    html += `<div class="mnemo-remind warn"><span class="mr-char jp">${escapeHtml(chosen)}</span>` +
            `<span><b>${tr("Не путай")}:</b> ${escapeHtml(ex.confusables[chosen])}</span></div>`;
  if (html) host.insertAdjacentHTML("beforeend", `<div class="mnemo-reminders">${html}</div>`);
}

async function showIntroKana(step) {
  const lookalikes = (step.lookalikes || []).map(l =>
    `<span class="jp">${l.char}<small>${l.romaji}</small></span>`).join("");
  // Со штрихами — живая анимация порядка черт (2.1), иначе крупный знак
  const glyph = step.strokes
    ? `<div class="kana-anim" id="kana-anim" data-tts="${step.char}" title="${tr("Анимация порядка черт")}"></div>`
    : `<div class="big-kana ${step.char.length > 1 ? "small" : ""}" data-tts="${step.char}">${step.char}</div>`;
  const presets = (step.mnemonics && step.mnemonics.length) ? step.mnemonics
    : (step.mnemonic ? [step.mnemonic] : []);
  playerBody.innerHTML = `
    ${glyph}
    <div class="romaji-big">${step.romaji}</div>
    ${ttsButton(step.tts)}
    ${step.derivation ? `<div class="derivation">${step.derivation}</div>` : ""}
    ${LANG === "ru" && presets.length ? mnemoChoiceHtml(step.char, presets) : ""}
    ${step.note ? `<p class="note">${tr(step.note)}</p>` : ""}
    ${lookalikes ? `<p class="note center">${tr("не путайте с")}</p><div class="lookalikes">${lookalikes}</div>` : ""}
    <div class="spacer"></div>
    <button class="primary" id="next">${tr("Запомнил")}</button>`;
  if (step.strokes) Tracing.preview($("#kana-anim", playerBody), step.strokes, 176);
  const mb = playerBody.querySelector(".mnemo-block");
  if (mb) { mb._presets = presets; bindMnemo(playerBody); }
  animateIn(playerBody);
  speak(step.tts);
  await waitClick($("#next", playerBody));
}

/* Контур высотного ударения 高低アクセント: моры с надчёркиванием высокого тона
   и «стенкой» на спаде + маркер тона следующей частицы (○) — он отличает 平板
   (частица высокая) от 尾高 (спад приходится на частицу). Чисто визуальная
   справка о произношении, не SRS-карточка. compact — мелкий вариант для словаря. */
const PITCH_JP = { heiban: "平板", atamadaka: "頭高", nakadaka: "中高", odaka: "尾高" };
const PITCH_DESC = { heiban: "ровный тон", atamadaka: "спад в начале",
                     nakadaka: "спад в середине", odaka: "спад в конце" };
function pitchHtml(p, compact) {
  if (!p) return "";
  const h = p.highs;
  const cells = p.moras.map((m, i) => {
    const hi = h[i];
    const nextHi = i + 1 < h.length ? h[i + 1] : p.particle_high;
    const cls = [hi ? "hi" : "lo"];
    if (hi && !nextHi) cls.push("drop");                 // спад справа от моры
    if (hi && i > 0 && !h[i - 1]) cls.push("rise");      // подъём слева
    return `<span class="pi-mora ${cls.join(" ")}">${escapeHtml(m)}</span>`;
  }).join("");
  const part = `<span class="pi-part ${p.particle_high ? "hi" : "lo"}" aria-hidden="true">○</span>`;
  const aria = tr("Высотное ударение: {d}", { d: tr(PITCH_DESC[p.pattern]) });
  return `<div class="pitch ${p.pattern}${compact ? " compact" : ""}" role="img" aria-label="${escAttr(aria)}">
    <span class="pi-line">${cells}${part}</span>
    <span class="pi-badge">${PITCH_JP[p.pattern]}</span>
    ${compact ? "" : `<span class="pi-desc">${tr(PITCH_DESC[p.pattern])}</span>`}
  </div>`;
}

async function showIntroWord(step) {
  playerBody.innerHTML = `
    <div class="big-kana small" data-tts="${step.tts}">${step.kana}</div>
    <div class="romaji-big">${step.romaji}</div>
    ${pitchHtml(step.pitch)}
    <div class="word-ru">${tr(step.ru)}</div>
    ${ttsButton(step.tts)}
    ${step.note ? `<p class="note center">${step.note}</p>` : ""}
    <div class="spacer"></div>
    <button class="primary" id="next">${tr("Запомнил")}</button>`;
  animateIn(playerBody);
  speak(step.tts);
  await waitClick($("#next", playerBody));
}

/* Знакомство с кандзи (6.2): порядок черт, значение, чтения он/кун, примеры */
async function showIntroKanji(step) {
  const glyph = step.strokes
    ? `<div class="kana-anim" id="kana-anim" data-tts="${step.tts}" title="${tr("Анимация порядка черт")}"></div>`
    : `<div class="big-kana" data-tts="${step.tts}">${step.char}</div>`;
  const on = (step.on || []).join("、");
  const kun = (step.kun || []).join("、");
  // Цветовое кодирование чтений (6.4): онъёми и кунъёми разными цветами
  const readings = `
    ${on ? `<span class="rd on"><small>${tr("он")}</small>${on}</span>` : ""}
    ${kun ? `<span class="rd kun"><small>${tr("кун")}</small>${kun}</span>` : ""}`;
  const examples = (step.examples || []).map(e =>
    `<button class="kanji-ex" data-tts="${e.r}">
       <span class="ex-w jp">${e.w}</span>
       <span class="ex-r jp">${e.r}</span>
       <span class="ex-ru">${tr(e.ru)}</span></button>`).join("");
  // Разбор на изученные компоненты (6.3): 木 + 木 = 林
  const parts = (step.components || []).map(c =>
    `<span class="part jp" data-tts="${c.char}">${c.char}<small>${c.meaning ? tr(c.meaning) : ""}</small></span>`
  ).join(`<i class="op">+</i>`);
  const components = parts
    ? `<div class="kanji-parts">${parts}<i class="op">=</i><span class="part whole jp">${step.char}</span></div>`
    : "";
  playerBody.innerHTML = `
    ${glyph}
    <div class="kanji-meaning">${tr(step.meaning)}</div>
    <div class="kanji-readings">${readings}</div>
    ${components}
    ${ttsButton(step.tts)}
    ${step.mnemonic && LANG === "ru" ? `<div class="mnemonic">${step.mnemonic}</div>` : ""}
    ${step.mnemonic_reading && LANG === "ru" ? `<div class="mnemonic mnemonic-reading"><b>${Icons.ui("speaker")} Чтение:</b> ${step.mnemonic_reading}</div>` : ""}
    ${LANG === "ru" ? customMnemoHtml(step.char) : ""}
    ${examples ? `<div class="kanji-examples">${examples}</div>` : ""}
    <div class="spacer"></div>
    <button class="primary" id="next">${tr("Запомнил")}</button>`;
  if (step.strokes) Tracing.preview($("#kana-anim", playerBody), step.strokes, 176);
  bindCustomMnemo(playerBody);
  animateIn(playerBody);
  speak(step.tts);
  await waitClick($("#next", playerBody));
}

async function showIntroGrammar(step) {
  const reg = { neutral: "нейтр.", polite: "вежл.", casual: "разг.", formal: "формальн." };
  const explanation = (step.explanation || []).map(b =>
    `<p class="g-block">${fmtBold(tr(b))}</p>`).join("");
  const examples = (step.examples || []).map(e =>
    `<button class="kanji-ex" data-tts="${e.tts}">
       <span class="ex-w jp">${e.jp}</span>
       <span class="ex-ru">${tr(e.ru)}</span></button>`).join("");
  // «Объяснить по-другому» (SRS 7): ленивый запрос к Сэнсэю по клику. Кнопка
  // только при доступном ИИ и в RU (модель объясняет по-русски).
  const aiBtn = AI.available && LANG === "ru" && step.id
    ? `<div class="ai-explain g-ai">
         <button class="ghost ai-ask" id="g-ai">${Icons.ui("spark")} ${tr("Объяснить по-другому")}</button>
         <div class="ai-body ai-grammar" hidden></div></div>`
    : "";
  playerBody.innerHTML = `
    <div class="big-kana jp" data-tts="${step.tts || step.title}">${tr(step.title)}</div>
    <div class="grammar-structure jp">${step.structure}</div>
    <div class="kanji-meaning">${tr(step.meaning)}${step.register
      ? ` <span class="g-register">${tr(reg[step.register] || step.register)}</span>` : ""}</div>
    ${explanation}
    ${step.caution ? `<div class="mnemonic">⚠ ${tr(step.caution)}</div>` : ""}
    ${examples ? `<div class="kanji-examples">${examples}</div>` : ""}
    ${aiBtn}
    <div class="spacer"></div>
    <button class="primary" id="next">${tr("Понятно")}</button>`;
  animateIn(playerBody);
  const gAi = $("#g-ai", playerBody);
  if (gAi) gAi.addEventListener("click", async () => {
    const body = playerBody.querySelector(".ai-grammar");
    gAi.disabled = true;
    gAi.textContent = tr("Думаю…");
    try {
      const r = await api.post("/api/ai/explain_grammar", { point_id: step.id });
      body.innerHTML = `
        <p class="ai-text">${fmtBold(escapeHtml(r.explanation))}</p>
        ${(r.examples || []).map(e => `<p class="ai-ex jp-ex">
          <span class="jp" data-tts="${escAttr(e.jp)}">${escapeHtml(e.jp)}</span>
          — ${escapeHtml(e.ru)}</p>`).join("")}
        ${r.tip ? `<p class="ai-rule"><b>${tr("Подсказка")}:</b> ${escapeHtml(r.tip)}</p>` : ""}`;
      body.hidden = false;
      gAi.remove();
    } catch {
      gAi.disabled = false;
      gAi.innerHTML = `${Icons.ui("spark")} ${tr("Объяснить по-другому")}`;
      body.innerHTML = `<p class="ai-text">${tr("Не получилось получить разбор. Попробуйте ещё раз.")}</p>`;
      body.hidden = false;
    }
  });
  await waitClick($("#next", playerBody));
}

/* ---------- Упражнения ----------
   Каждый рендерер возвращает {correct, durationMs, usedHint}.
   afterAnswer — async-колбэк: вызывается после ответа, возвращает
   HTML (SRS-вердикт) для блока фидбека. */

/* Вердикт ответа в виде пилюли с галочкой/крестиком */
function verdict(ok, html) {
  return `<span class="verdict">${ok ? "✓ " : "✗ "}${html}</span>`;
}

async function runExercise(ex, afterAnswer) {
  playerBody.classList.remove("center-step");   // упражнение — верхнее выравнивание
  if (ex.type === "kana_word_build" || ex.type === "vocab_build"
      || ex.type === "sentence_scramble")
    return runWordBuild(ex, afterAnswer);
  if (ex.type === "kana_twins") return runTwins(ex, afterAnswer);
  if (ex.type === "kana_tracing" || ex.type === "kanji_tracing")
    return runTracing(ex, afterAnswer);
  if (ex.type === "vocab_input" || ex.type === "dictation")
    return runInput(ex, afterAnswer);
  if (ex.type === "vocab_match") return runMatch(ex, afterAnswer);
  if (ex.type === "grammar_cloze") return runGrammarCloze(ex, afterAnswer);
  return runChoice(ex, afterAnswer);
}

// Мульти-пропуск с общим банком (тип 34 grammar_cloze).
async function runGrammarCloze(ex, afterAnswer) {
  const rowHtml = (r, i) => {
    const sent = r.tokens.map((t, j) => j === r.key
      ? `<button class="cloze-blank" data-row="${i}"></button>`
      : `<span>${t}</span>`).join("");
    return `<div class="cloze-row"><div class="cloze-jp">${sent}</div>` +
           `<div class="cloze-ru">${r.ru}</div></div>`;
  };
  playerBody.innerHTML = `
    <p class="question">${tr(ex.question)}</p>
    <div class="cloze-list">${ex.rows.map(rowHtml).join("")}</div>
    <div class="cloze-bank">${ex.bank.map(t =>
      `<button class="bank-tile" data-t="${t}">${t}</button>`).join("")}</div>
    <div class="feedback" id="fb" aria-live="polite"></div>
    <div class="spacer"></div>
    <button class="primary" id="check" disabled>${tr("Проверить")}</button>`;
  animateIn(playerBody);

  const blanks = [...playerBody.querySelectorAll(".cloze-blank")];
  const fills = new Array(ex.rows.length).fill(null);
  const checkBtn = $("#check", playerBody);
  let selRow = 0;
  const selectRow = i => { selRow = i; blanks.forEach((b, j) => b.classList.toggle("sel", j === i)); };
  const refresh = () => { checkBtn.disabled = fills.includes(null); };
  selectRow(0);
  const t0 = performance.now();

  playerBody.querySelector(".cloze-list").addEventListener("click", e => {
    const b = e.target.closest(".cloze-blank");
    if (!b) return;
    const i = +b.dataset.row;
    if (fills[i]) { fills[i] = null; b.textContent = ""; b.classList.remove("filled"); }
    selectRow(i); refresh();
  });
  playerBody.querySelector(".cloze-bank").addEventListener("click", e => {
    const t = e.target.closest(".bank-tile");
    if (!t) return;
    let i = (selRow != null && !fills[selRow]) ? selRow : fills.indexOf(null);
    if (i < 0) return;
    fills[i] = t.dataset.t;
    blanks[i].textContent = t.dataset.t; blanks[i].classList.add("filled");
    const next = fills.indexOf(null);
    selectRow(next < 0 ? i : next);
    refresh();
  });

  if (await waitClick(checkBtn) === ABORT) return { correct: false, durationMs: 0, usedHint: false };
  const durationMs = Math.round(performance.now() - t0);
  playerBody.querySelector(".cloze-bank").style.pointerEvents = "none";
  blanks.forEach(b => (b.disabled = true));
  let ok = 0;
  ex.rows.forEach((r, i) => {
    const good = fills[i] === r.answer;
    if (good) ok++;
    blanks[i].classList.remove("sel");
    blanks[i].classList.add(good ? "right" : "bad-fill");
    if (!good) blanks[i].textContent = r.answer;
  });
  const allRight = ok === ex.rows.length;
  const fb = $("#fb", playerBody);
  fb.className = `feedback ${allRight ? "ok" : "bad"}`;
  Haptics[allRight ? "good" : "bad"]();
  fb.innerHTML = verdict(allRight, allRight ? tr("Все пропуски верны!") : tr("Верно {ok} из {n}", { ok, n: ex.rows.length }));
  if (afterAnswer) fb.innerHTML += `<div class="srs-toast">${await afterAnswer(allRight, durationMs, false)}</div>`;

  checkBtn.remove();
  if (allRight) {
    await new Promise(r => setTimeout(r, 1100));
  } else {
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
    await waitClick($("#next", playerBody));
  }
  return { correct: allRight, durationMs, usedHint: false };
}

// Сопоставление пар (тип 11): две колонки, тап слева + тап справа.
async function runMatch(ex, afterAnswer) {
  const shuffle = a => {
    a = a.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  };
  const tile = (p, label, cls) =>
    `<button class="match-tile ${cls}" data-id="${p.id}">${label}</button>`;
  playerBody.innerHTML = `
    <p class="question">${tr(ex.question)}</p>
    <div class="match-board">
      <div class="match-col">${shuffle(ex.pairs).map(p => tile(p, p.jp, "jp")).join("")}</div>
      <div class="match-col">${shuffle(ex.pairs).map(p => tile(p, p.ru, "")).join("")}</div>
    </div>
    <div class="feedback" id="fb" aria-live="polite"></div>
    <div class="spacer"></div>`;
  animateIn(playerBody);

  const total = ex.pairs.length;
  const ttsOf = id => (ex.pairs.find(p => p.id === id) || {}).tts;
  let matched = 0, mistakes = 0, sel = null, busy = false;
  const t0 = performance.now();

  const done = await abortable(resolve => {
    playerBody.querySelector(".match-board").addEventListener("click", e => {
      const b = e.target.closest(".match-tile");
      if (!b || busy || b.classList.contains("matched")) return;
      const col = b.parentElement;
      if (b === sel) { b.classList.remove("sel"); sel = null; return; }
      if (!sel || sel.parentElement === col) {        // выбор/перевыбор в колонке
        if (sel) sel.classList.remove("sel");
        sel = b; b.classList.add("sel"); return;
      }
      const a = sel; sel = null; a.classList.remove("sel");   // пара из двух колонок
      if (a.dataset.id === b.dataset.id) {
        a.classList.add("matched"); b.classList.add("matched");
        Haptics.good(); speak(ttsOf(b.dataset.id));
        if (++matched === total) {
          const fb = $("#fb", playerBody);
          fb.className = "feedback ok";
          fb.innerHTML = verdict(mistakes === 0,
            mistakes === 0 ? tr("Все пары верны!") : tr("Доска собрана"));
          setTimeout(resolve, 750);
        }
      } else {
        mistakes++; Haptics.bad(); busy = true;
        a.classList.add("bad"); b.classList.add("bad");
        setTimeout(() => {
          a.classList.remove("bad"); b.classList.remove("bad"); busy = false;
        }, 480);
      }
    });
  });

  if (done === ABORT) return { correct: false, durationMs: 0, usedHint: false };
  const durationMs = Math.round(performance.now() - t0);
  const correct = mistakes === 0;
  if (afterAnswer)
    $("#fb", playerBody).innerHTML += `<div class="srs-toast">${await afterAnswer(correct, durationMs, false)}</div>`;
  await new Promise(r => setTimeout(r, 600));
  return { correct, durationMs, usedHint: false };
}

async function runChoice(ex, afterAnswer) {
  let style = ex.prompt.style ||
    (ex.type === "kana_recognition" ? "jp" : "text");
  let question = ex.question_i18n ? qtr(ex.question_i18n) : ex.question;
  // Аудио-вопрос без доступной озвучки: показываем ромадзи вместо кнопки
  if (style === "audio" && !TTS.available && ex.prompt.fallback) {
    style = "text";
    ex.prompt.text = ex.prompt.fallback;
    question = "Прочитайте и выберите перевод";
  }
  // Звук подсказал бы ответ: у распознавания знака — молчим до ответа
  const speakOnStart = ex.type !== "kana_recognition" && ex.prompt.tts;
  // jp — крупный одиночный глиф; jp-sentence — целое предложение (мельче)
  const jpish = style === "jp" || style === "jp-sentence";
  const jpClass = style === "jp" ? "jp" : style === "jp-sentence" ? "jp jp-sentence" : "";
  const promptHtml = style === "audio"
    ? `<button class="audio-prompt" data-tts="${ex.prompt.tts}" title="${tr("Прослушать ещё раз")}">${Icons.ui("speaker")}</button>`
    : `<div class="prompt-text ${jpClass}" ${ex.prompt.tts ? `data-tts="${ex.prompt.tts}"` : ""}>${tr(ex.prompt.text)}</div>` +
      (!jpish && ex.prompt.tts ? ttsButton(ex.prompt.tts) : "");
  playerBody.innerHTML = `
    <p class="question">${tr(question)}</p>
    ${promptHtml}
    <div class="options">
      ${ex.options.map((o, i) =>
        `<button data-i="${i}" class="${ex.options_are_kana ? "jp" : ""}"><span class="kbd">${i + 1}</span>${tr(o)}</button>`).join("")}
    </div>
    <div class="feedback" id="fb" aria-live="polite"></div>
    <div class="spacer"></div>`;
  animateIn(playerBody);
  if (speakOnStart) speak(ex.prompt.tts);

  const buttons = [...playerBody.querySelectorAll(".options button")];
  const t0 = performance.now();
  const choice = await awaitChoice(buttons);
  if (choice === ABORT) return { correct: false, durationMs: 0, usedHint: false };
  const durationMs = Math.round(performance.now() - t0);
  const correct = choice === ex.answer;
  buttons.forEach(b => (b.disabled = true));
  buttons[ex.answer].classList.add("correct");
  if (!correct) buttons[choice].classList.add("wrong");

  const fb = $("#fb", playerBody);
  fb.className = `feedback ${correct ? "ok" : "bad"}`;
  Haptics[correct ? "good" : "bad"]();
  answerFx(correct, playerBody.querySelector(".prompt-text, .audio-prompt"));
  fb.innerHTML = verdict(correct, correct ? tr("Верно") :
    tr("Правильно: {x}", { x: `<span class="jp">${tr(ex.options[ex.answer])}</span>` }));
  speak(ex.prompt.tts || ex.answer_tts);

  if (afterAnswer) {
    // Радар путаницы: при ошибке в выборе из кана-вариантов передаём выбранный
    // неверный знак — сервер копит пары «путаю X с Y» для точечных дриллов.
    const confusedWith = (!correct && ex.options_are_kana) ? ex.options[choice] : null;
    fb.innerHTML += `<div class="srs-toast">${await afterAnswer(correct, durationMs, false, confusedWith)}</div>`;
  }

  if (correct) {
    await new Promise(r => setTimeout(r, 900));
  } else {
    mountMnemoReminder(playerBody, ex, choice);
    mountExplain(playerBody, {
      exercise_type: ex.type, item_id: ex.item_id || "",
      prompt: ex.prompt.text || question || "",
      correct_answer: ex.options[ex.answer], given_answer: ex.options[choice],
      choices: ex.options,
    });
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
    await waitClick($("#next", playerBody));
  }
  return { correct, durationMs, usedHint: false };
}

async function runWordBuild(ex, afterAnswer) {
  // speak_after: озвучка слова до ответа выдала бы его (тип vocab_build)
  const quiet = !!ex.speak_after;
  playerBody.innerHTML = `
    <p class="question">${tr(ex.question)}</p>
    <div class="prompt-text">${trBuildPrompt(ex.prompt.text)}</div>
    ${quiet ? "" : ttsButton(ex.prompt.tts)}
    <div class="build-slots" id="slots"></div>
    <div class="tiles" id="tiles">
      ${ex.tiles.map((t, i) => `<button data-i="${i}">${t}</button>`).join("")}
    </div>
    <div class="feedback" id="fb" aria-live="polite"></div>
    <div class="spacer"></div>
    <button class="primary" id="check" disabled>${tr("Проверить")}</button>`;
  animateIn(playerBody);
  if (!quiet) speak(ex.prompt.tts);

  const slots = $("#slots", playerBody);
  const checkBtn = $("#check", playerBody);
  const assembled = [];
  const t0 = performance.now();

  const renderSlots = () => {
    slots.innerHTML = assembled.map((a, i) =>
      `<span data-pos="${i}" title="${tr("Убрать")}">${a.tile}</span>`).join("");
    // Проверяем только по кнопке: автосабмит не давал исправить последнюю плитку
    checkBtn.disabled = assembled.length !== ex.answer_tokens.length;
  };

  const finished = abortable(res => {
    $("#tiles", playerBody).addEventListener("click", e => {
      const b = e.target.closest("button");
      if (!b || b.disabled) return;
      b.disabled = true;
      assembled.push({ tile: b.textContent, btn: b });
      renderSlots();
    });
    slots.addEventListener("click", e => {
      const s = e.target.closest("span");
      if (!s) return;
      const [removed] = assembled.splice(+s.dataset.pos, 1);
      removed.btn.disabled = false;
      renderSlots();
    });
    checkBtn.addEventListener("click", () => {
      if (assembled.length === ex.answer_tokens.length) res();
    });
  });
  if (await finished === ABORT) return { correct: false, durationMs: 0, usedHint: false };

  const durationMs = Math.round(performance.now() - t0);
  const word = assembled.map(a => a.tile).join("");
  const correct = word === ex.answer_tokens.join("");

  const fb = $("#fb", playerBody);
  fb.className = `feedback ${correct ? "ok" : "bad"}`;
  Haptics[correct ? "good" : "bad"]();
  answerFx(correct, $("#slots", playerBody));
  fb.innerHTML = verdict(correct, correct
    ? `<span class="jp">${word}</span>`
    : tr("Правильно: {x}", { x: `<span class="jp">${ex.answer_tokens.join("")}</span>` }));
  speak(ex.prompt.tts);
  if (afterAnswer) fb.innerHTML += `<div class="srs-toast">${await afterAnswer(correct, durationMs, false)}</div>`;

  if (correct) {
    await new Promise(r => setTimeout(r, 1100));
  } else {
    $("#check", playerBody).remove();
    mountExplain(playerBody, {
      exercise_type: ex.type, item_id: ex.item_id || "",
      prompt: ex.question || (ex.prompt && ex.prompt.text) || "",
      correct_answer: ex.answer_tokens.join(""), given_answer: word, choices: [],
    });
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
    await waitClick($("#next", playerBody));
  }
  return { correct, durationMs, usedHint: false };
}

// Свободный ввод ответа (тип 10 vocab_input, тип 37 dictation).
// Принимаем кану и ромадзи: нормализация должна совпадать с серверной (accept).
const normInput = s => s.trim().toLowerCase().replace(/\s+/g, "");

async function runInput(ex, afterAnswer) {
  const isAudio = ex.prompt.style === "audio";
  // Диктант без озвучки (офлайн) деградирует к показу перевода — иначе никак
  const audioMode = isAudio && TTS.available;
  const top = audioMode
    ? `<button class="audio-prompt" data-tts="${ex.prompt.tts}" title="${tr("Прослушать ещё раз")}">${Icons.ui("speaker")}</button>`
    : `<div class="prompt-text">${tr(isAudio ? ex.prompt.fallback_text : ex.prompt.text)}</div>`;
  const question = (isAudio && !audioMode) ? "Введите слово по-японски" : ex.question;
  playerBody.innerHTML = `
    <p class="question">${tr(question)}</p>
    ${top}
    <input class="text-answer" id="ans" type="text" inputmode="text"
      autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false"
      placeholder="${tr("каной или ромадзи")}">
    <div class="feedback" id="fb" aria-live="polite"></div>
    <div class="spacer"></div>
    <button class="primary" id="check" disabled>${tr("Проверить")}</button>`;
  animateIn(playerBody);
  if (audioMode) speak(ex.prompt.tts);

  const input = $("#ans", playerBody);
  const checkBtn = $("#check", playerBody);
  input.focus();
  input.addEventListener("input", () => { checkBtn.disabled = !input.value.trim(); });
  const t0 = performance.now();
  const aborted = await abortable(res => {
    const submit = () => { if (input.value.trim()) res(); };
    checkBtn.addEventListener("click", submit);
    input.addEventListener("keydown", e => { if (e.key === "Enter") submit(); });
  });
  if (aborted === ABORT) return { correct: false, durationMs: 0, usedHint: false };

  const durationMs = Math.round(performance.now() - t0);
  const correct = ex.accept.includes(normInput(input.value));
  input.disabled = true;
  checkBtn.remove();

  const fb = $("#fb", playerBody);
  fb.className = `feedback ${correct ? "ok" : "bad"}`;
  Haptics[correct ? "good" : "bad"]();
  answerFx(correct, input);
  fb.innerHTML = verdict(correct, correct
    ? `<span class="jp">${ex.answer}</span>`
    : tr("Правильно: {x}", { x: `<span class="jp">${ex.answer}</span>` }));
  speak(ex.answer_tts);
  if (afterAnswer) fb.innerHTML += `<div class="srs-toast">${await afterAnswer(correct, durationMs, false)}</div>`;

  if (correct) {
    await new Promise(r => setTimeout(r, 1100));
  } else {
    mountExplain(playerBody, {
      exercise_type: ex.type, item_id: ex.item_id || "",
      prompt: (isAudio ? ex.prompt.fallback_text : ex.prompt.text) || ex.question || "",
      correct_answer: ex.answer, given_answer: input.value, choices: [],
    });
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
    await waitClick($("#next", playerBody));
  }
  return { correct, durationMs, usedHint: false };
}

async function runTracing(ex, afterAnswer) {
  playerBody.innerHTML = `
    <p class="question">${tr(ex.question)}</p>
    <div class="prompt-text" ${ex.prompt.tts ? `data-tts="${ex.prompt.tts}"` : ""}>${tr(ex.prompt.text)}</div>
    ${ttsButton(ex.prompt.tts)}
    <div id="trace-host"></div>
    <div class="feedback" id="fb" aria-live="polite"></div>
    <div class="spacer"></div>`;
  animateIn(playerBody);
  speak(ex.prompt.tts);

  const t0 = performance.now();
  const result = await abortable(res =>
    Tracing.create($("#trace-host", playerBody), {
      strokes: ex.strokes,
      mode: ex.mode,
      onComplete: res,
    }));
  if (result === ABORT) return { correct: false, durationMs: 0, usedHint: false };
  const durationMs = Math.round(performance.now() - t0);
  // Трассировка прощает одну помарку, письмо по памяти — нет (6.7, режимы)
  const correct = ex.mode === "trace" ? result.errors <= 1 : result.errors === 0;

  const fb = $("#fb", playerBody);
  fb.className = `feedback ${correct ? "ok" : "bad"}`;
  Haptics[correct ? "good" : "bad"]();
  fb.innerHTML = verdict(correct, correct
    ? (result.errors === 0 ? tr("Написано чисто") : tr("Зачтено, была помарка"))
    : tr("Помарок: {n} — посмотрите анимацию черт ещё раз", { n: result.errors }));
  if (afterAnswer) fb.innerHTML += `<div class="srs-toast">${await afterAnswer(correct, durationMs, result.usedHint)}</div>`;

  playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
  await waitClick($("#next", playerBody));
  return { correct, durationMs, usedHint: result.usedHint };
}

async function runTwins(ex, afterAnswer) {
  let errors = 0;
  const t0 = performance.now();
  for (let i = 0; i < ex.series.length; i++) {
    const round = ex.series[i];
    playerBody.innerHTML = `
      <p class="question">${tr(ex.question)}</p>
      <div class="prompt-text">${round.prompt}</div>
      <div class="options">
        ${round.options.map((o, j) =>
          `<button data-i="${j}" class="jp"><span class="kbd">${j + 1}</span>${o}</button>`).join("")}
      </div>
      <div class="twins-progress">${i + 1} / ${ex.series.length}</div>
      <div class="spacer"></div>`;
    speak(round.tts);
    const buttons = [...playerBody.querySelectorAll(".options button")];
    const choice = await awaitChoice(buttons);
    if (choice === ABORT) return { correct: false, durationMs: 0, usedHint: false };
    const ok = choice === round.answer;
    if (!ok) errors++;
    buttons.forEach(b => (b.disabled = true));
    buttons[round.answer].classList.add("correct");
    if (!ok) buttons[choice].classList.add("wrong");
    await new Promise(r => setTimeout(r, ok ? 350 : 1200));
  }
  const durationMs = Math.round(performance.now() - t0);
  const correct = errors === 0;
  Haptics[correct ? "good" : "bad"]();
  if (afterAnswer) await afterAnswer(correct, durationMs, false);
  playerBody.insertAdjacentHTML("beforeend",
    `<div class="feedback ${correct ? "ok" : "bad"}" role="status" aria-live="polite">${correct ? tr("Серия без ошибок") : tr("Ошибок: {n} из {m}", { n: errors, m: ex.series.length })}</div>`);
  await new Promise(r => setTimeout(r, 1000));
  return { correct, durationMs, usedHint: false };
}

/* ---------- Урок (с продолжением с места выхода) ----------
   Ключ resume — по lessonId: иначе старт другого урока затирал сохранённый
   прогресс первого (один общий ключ терял место выхода). Храним сам сценарий
   (steps сгенерированы со случайностью — так продолжаем ту же сессию). */
const RESUME_PREFIX = "michi_lesson_resume_";
const resumeKey = id => RESUME_PREFIX + id;

async function startLesson(lessonId) {
  let lesson, startIdx = 0, correct = 0, total = 0;
  localStorage.removeItem("michi_lesson_resume");   // миграция: убрать старый общий ключ
  // Если из этого урока выходили на середине — продолжаем с того же шага
  const saved = JSON.parse(localStorage.getItem(resumeKey(lessonId)) || "null");
  if (saved && saved.lessonId === lessonId && Array.isArray(saved.steps)) {
    lesson = { title: saved.title, steps: saved.steps };
    startIdx = saved.i;
    correct = saved.correct;
    total = saved.total;
  } else {
    try {
      lesson = await api.get(`/api/lessons/${lessonId}`);
    } catch (e) {
      toast(e.message, true);
      return;
    }
  }
  const token = openPlayer("lesson");
  const steps = lesson.steps;

  for (let i = startIdx; i < steps.length; i++) {
    if (token !== sessionToken) return; // сессию закрыли — прогресс уже сохранён
    setProgress(i / steps.length);
    $("#player-counter").textContent = `${i + 1} / ${steps.length}`;
    const step = steps[i];
    // Вступления центрируем, упражнения — верхнее выравнивание (без «прыжка»)
    playerBody.classList.toggle("center-step", step.type !== "exercise");
    if (step.type === "intro_text") await showIntroText(step);
    else if (step.type === "intro_kana") await showIntroKana(step);
    else if (step.type === "intro_word") await showIntroWord(step);
    else if (step.type === "intro_kanji") await showIntroKanji(step);
    else if (step.type === "intro_grammar") await showIntroGrammar(step);
    else if (step.type === "exercise") {
      const res = await runExercise(step.exercise);
      if (token !== sessionToken) return;
      total++;
      if (res.correct) correct++;
      Combo.update(res.correct);
    }
    localStorage.setItem(resumeKey(lessonId), JSON.stringify({
      lessonId, title: lesson.title, steps, i: i + 1, correct, total,
    }));
  }
  if (token !== sessionToken) return;
  setProgress(1);

  // Сначала пишем результат на сервер и только при успехе снимаем точку
  // возобновления. Иначе обрыв сети на финише терял бы весь урок: прогресс не
  // дошёл бы до сервера, а resume-ключ был бы уже удалён. /complete идемпотентен
  // (ON CONFLICT) — повторный заход в урок (resume на i == steps.length) досдаёт.
  const score = total ? correct / total : 1;
  let done;
  try {
    done = await api.post(`/api/lessons/${lessonId}/complete`, { score });
  } catch {
    if (token !== sessionToken) return;
    toast(tr("Нет сети — урок не засчитан. Зайдите снова, прогресс сохранён."), true);
    closePlayer();
    return;
  }
  if (token !== sessionToken) return;
  localStorage.removeItem(resumeKey(lessonId));   // успех — точка возобновления больше не нужна
  playerBody.classList.add("center-step");   // итог — по центру

  // Ворота юнита провалены: следующий юнит не открывается, предлагаем пересдать
  if (done.is_gate && !done.passed) {
    const need = Math.round((done.pass_mark || 0.8) * 100);
    playerBody.innerHTML = `
      <div class="result gate-fail">
        <div class="mark">門</div>
        <h2>${tr("Ворота не пройдены")}</h2>
        <p>${tr("Ваш результат {p}% · нужно {need}%", { p: Math.round(score * 100), need })}<br>
        ${tr("Следующий юнит откроется после пересдачи.")}</p>
        <button class="primary" id="retry">${tr("Пересдать")}</button>
        <button class="ghost" id="finish">${tr("Выйти")}</button>
      </div>`;
    animateIn(playerBody);
    const choice = await Promise.race([
      waitClick($("#retry", playerBody)).then(v => v === ABORT ? ABORT : "retry"),
      waitClick($("#finish", playerBody)).then(v => v === ABORT ? ABORT : "finish"),
    ]);
    if (choice === ABORT) return;        // вышли из плеера — closePlayer уже отработал
    closePlayer();
    if (choice === "retry") startLesson(lessonId);
    return;
  }

  const isGate = done.is_gate;
  playerBody.innerHTML = `
    <div class="result">
      <div class="result-mascot">${Art.mascotTile("cheer")}</div>
      <h2>${isGate ? tr("Ворота пройдены!") : tr("{title} — пройден", { title: tr(lesson.title) })}</h2>
      <p>${tr("Точность {p}% · {a} из {b}", { p: Math.round(score * 100), a: correct, b: total })}${
        isGate ? "" : "<br>" + (done.cards_created
          ? tr("В SRS добавлено карточек: {n}", { n: done.cards_created }) : tr("Карточки уже в SRS"))}</p>
      <button class="primary" id="finish">${tr("Дальше")}</button>
    </div>`;
  animateIn(playerBody);
  confetti();
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
  await checkAchievements(true);   // мог открыться кандзи/ворота/веха — салютуем
}

/* ---------- SRS-сессия ---------- */
async function startReview() {
  const token = openPlayer("review");
  let done = 0, okCount = 0;

  while (token === sessionToken) {
    let data;
    try {
      data = await api.get("/api/srs/queue?limit=20");
    } catch {
      if (token !== sessionToken) return;
      toast(tr("Нет сети — попробуйте позже. Ответы сохранены."), true);
      closePlayer();
      return;
    }
    if (token !== sessionToken) return;
    if (!data.items.length) break;

    const remaining = data.counts.due + data.counts.new_available;
    for (let i = 0; i < data.items.length; i++) {
      if (token !== sessionToken) return;
      const item = data.items[i];
      setProgress(done / Math.max(done + remaining, 1));
      $("#player-counter").textContent = tr("{n} · осталось ~{m}", { n: done, m: Math.max(remaining - i, 1) });

      const res = await runExercise(item.exercise, async (correct, durationMs, usedHint, confusedWith) => {
        let verdict;
        try {
          verdict = await api.post("/api/srs/answer", {
            card_id: item.card_id,
            correct,
            duration_ms: durationMs,
            exercise_type: item.exercise.type,
            used_hint: usedHint,
            confused_with: confusedWith || null,
          });
        } catch {
          // Сеть отпала: ответ не записан, карточка остаётся due и вернётся
          // в следующей сессии. Сессию не роняем — сообщаем в области вердикта.
          return tr("Нет сети — ответ не сохранён, карточка вернётся позже.");
        }
        let extra = `${tr(verdict.rating_label)} · ${tr("следующий показ")} ${humanizeInterval((new Date(verdict.next_due) - Date.now()) / 1000)}`;
        // hint приходит с сервера по-русски (item_info); для не-RU не показываем —
        // как и мнемо-напоминание (см. mountMnemoReminder), чтобы не было русских вкраплений
        if (!correct && item.info.hint && LANG === "ru")
          extra += `<br>${item.info.hint}`;
        if (verdict.is_leech)
          extra += `<br>${tr("Эта карточка даётся тяжело — присмотритесь к подсказке")}`;
        return extra;
      });
      if (token !== sessionToken) return;
      done++;
      if (res.correct) okCount++;
      Combo.update(res.correct);
    }
  }
  if (token !== sessionToken) return;

  setProgress(1);
  playerBody.classList.add("center-step");   // итог — по центру
  playerBody.innerHTML = `
    <div class="result">
      ${done ? `<div class="result-mascot">${Art.mascotTile("cheer")}</div>`
             : `<div class="mark">休</div>`}
      <h2>${done ? tr("Очередь разобрана") : tr("Повторять пока нечего")}</h2>
      <p>${done ? tr("Карточек: {n} · точность {p}%", { n: done, p: Math.round(okCount / done * 100) }) :
        tr("Пройдите урок, чтобы добавить карточки в SRS.")}</p>
      <button class="primary" id="finish">${tr("Готово")}</button>
    </div>`;
  animateIn(playerBody);
  if (done >= 10) confetti();
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
  await checkAchievements(true);   // повторения могли открыть веху памяти/серии
}

/* ---------- Упреждающее повторение: освежить то, что скоро потускнеет ----------
   Ранний повтор карточек, входящих в «зону забывания» (/api/srs/upcoming).
   В отличие от «разбора ошибок» ответы идут в обычный /api/srs/answer — это
   настоящий повтор: FSRS учтёт ранний показ, и карточка не успеет сорваться. */
async function startFreshen() {
  const token = openPlayer("freshen");
  let data;
  try { data = await api.get("/api/srs/upcoming?limit=20"); }
  catch { toast(tr("Нет сети — попробуйте позже. Ответы сохранены."), true); closePlayer(); return; }
  if (token !== sessionToken) return;
  const items = data.items;
  let done = 0, okCount = 0;
  for (let i = 0; i < items.length; i++) {
    if (token !== sessionToken) return;
    const item = items[i];
    setProgress(done / Math.max(items.length, 1));
    $("#player-counter").textContent = tr("{n} · осталось ~{m}", { n: done, m: Math.max(items.length - i, 1) });
    const res = await runExercise(item.exercise, async (correct, durationMs, usedHint) => {
      let verdict;
      try {
        verdict = await api.post("/api/srs/answer", {
          card_id: item.card_id, correct, duration_ms: durationMs,
          exercise_type: item.exercise.type, used_hint: usedHint,
        });
      } catch {
        return tr("Нет сети — ответ не сохранён, карточка вернётся позже.");
      }
      let extra = `${tr(verdict.rating_label)} · ${tr("следующий показ")} ${humanizeInterval((new Date(verdict.next_due) - Date.now()) / 1000)}`;
      if (!correct && item.info.hint && LANG === "ru") extra += `<br>${item.info.hint}`;
      return extra;
    });
    if (token !== sessionToken) return;
    done++;
    if (res.correct) okCount++;
    Combo.update(res.correct);
  }
  if (token !== sessionToken) return;
  setProgress(1);
  playerBody.classList.add("center-step");
  playerBody.innerHTML = `
    <div class="result">
      ${done ? `<div class="result-mascot">${Art.mascotTile("cheer")}</div>` : `<div class="mark">予</div>`}
      <h2>${done ? tr("Освежили вовремя!") : tr("Пока нечего освежать")}</h2>
      <p>${done ? tr("Повторено: {n} · точность {p}%", { n: done, p: Math.round(okCount / done * 100) })
                : tr("Загляните позже — подскажем, когда что-то начнёт тускнеть.")}</p>
      <button class="primary" id="finish">${tr("Готово")}</button>
    </div>`;
  animateIn(playerBody);
  if (done >= 10) confetti();
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
  await checkAchievements(true);   // ранние повторения тоже двигают вехи памяти/серии
}

/* ---------- Вкладка «Повторение» ---------- */
async function renderReviewTab() {
  view.innerHTML = skeleton("review");
  const o = await getOverview();
  const conf = await api.get("/api/confusions?limit=6").catch(() => ({ pairs: [] }));
  setStreakPill(o.streak);
  Romaji.syncProgress(o.courses);
  const total = o.srs.due + o.srs.new_available;
  const estMin = Math.max(1, Math.round(total * 0.15));
  // Новичок без единой карточки: вместо трёх нулей — маскот и приглашение
  const freshSrs = !total && !o.srs.reviews_done_today;
  view.innerHTML = `
    <div class="review-wrap stagger">
    <div class="card">
      <h2>${tr("Очередь на сегодня")}</h2>
      ${freshSrs ? `
      <div class="empty-mascot">${Art.mascotTile("wave")}</div>
      <p class="note center">${tr("Пока нечего повторять — пройдите первый урок, и карточки появятся здесь.")}</p>`
      : `
      <div class="stat-trio">
        <div><b>${o.srs.due}</b><span>${tr("по расписанию")}</span></div>
        <div><b>${o.srs.new_available}</b><span>${tr(plural(o.srs.new_available, ["новая", "новые", "новых"]))}</span></div>
        <div><b>${o.srs.reviews_done_today}</b><span>${tr("повторено сегодня")}</span></div>
      </div>
      ${total
        ? `<button class="primary mt cta-glow" id="btn-start">${tr("Начать сессию · {n} · ≈{m} мин", { n: total, m: estMin })}</button>`
        : `<p class="note center mt">${tr("Очередь пуста — всё повторено! Новые карточки появятся\n           после уроков, повторения — по расписанию FSRS.")}</p>`}`}
    </div>
    ${o.mistakes_today ? `<div class="card">
      <h2>${tr("Работа над ошибками")}</h2>
      <p class="note" style="margin-top:0">${tr("Быстрый разбор того, в чём вы сегодня ошиблись. Это практика — на расписание SRS не влияет.")}</p>
      <button class="ghost mt" id="btn-mistakes">${tr("Разобрать ошибки дня · {n}", { n: o.mistakes_today })}</button>
    </div>` : ""}
    <div class="card">
      <h2>${tr("Пробный тест")}</h2>
      <p class="note" style="margin-top:0">${tr("Мини-срез уровня по всей программе N5: кана, слова, кандзи, грамматика — 10 минут. Практика, на расписание SRS не влияет.")}</p>
      <button class="ghost mt" id="btn-exam">${tr("Пройти пробный тест N5")}</button>
    </div>
    ${conf.pairs.length ? `<div class="card radar-card">
      <h2>${tr("Радар путаницы")}</h2>
      <p class="note" style="margin-top:0">${tr("Знаки, которые вы чаще путаете на повторениях. Точечная отработка — на расписание SRS не влияет.")}</p>
      <div class="radar-pairs">${conf.pairs.map(p => `
        <span class="radar-pair"><b class="jp">${escapeHtml(p.a)}</b><i>↔</i><b class="jp">${escapeHtml(p.b)}</b><em>×${p.count}</em></span>`).join("")}</div>
      <button class="ghost mt" id="btn-confusion">${tr("Отработать различение")}</button>
    </div>` : ""}
    <div class="card practice-card">
      <h2>${tr("Тренировки и игры")}</h2>
      <p class="note" style="margin-top:0">${tr("Практика и мини-игры — на расписание SRS не влияют.")}</p>
      <div class="practice-grid">
        <button class="practice-tile story-tile" data-practice="story"><span class="pt-ico">${Icons.art("story")}</span><span class="pt-label">${tr("Свиток")}</span><span class="pt-jp jp">物語</span></button>
        ${TTS.available ? `<button class="practice-tile" data-practice="listen"><span class="pt-ico">${Icons.art("listen")}</span><span class="pt-label">${tr("Слух")}</span><span class="pt-jp jp">耳</span></button>` : ""}
        <button class="practice-tile" data-practice="pitch"><span class="pt-ico">${Icons.art("pitch")}</span><span class="pt-label">${tr("Тон")}</span><span class="pt-jp jp">高低</span></button>
        <button class="practice-tile" data-practice="shiritori"><span class="pt-ico">${Icons.art("shiritori")}</span><span class="pt-label">${tr("Сиритори")}</span><span class="pt-jp jp">しりとり</span></button>
        <button class="practice-tile" data-practice="counters"><span class="pt-ico">${Icons.art("counters")}</span><span class="pt-label">${tr("Счётчики")}</span><span class="pt-jp jp">助数詞</span></button>
        <button class="practice-tile" data-practice="forge"><span class="pt-ico">${Icons.art("forge")}</span><span class="pt-label">${tr("Кузница")}</span><span class="pt-jp jp">鍛冶</span></button>
        <button class="practice-tile" data-practice="calligraphy"><span class="pt-ico">${Icons.art("calligraphy")}</span><span class="pt-label">${tr("Каллиграфия")}</span><span class="pt-jp jp">書道</span></button>
      </div>
      ${!TTS.available ? `<p class="note mt" style="color:var(--warning)">${tr("Тренировка слуха требует голос — включите озвучку в ⚙.")}</p>` : ""}
    </div>
    </div>`;
  const PRACTICE = { story: startStory, listen: startListening, shiritori: startShiritori,
                     counters: startCounters, forge: startForge, calligraphy: startCalligraphy,
                     pitch: startPitch };
  $("#btn-start")?.addEventListener("click", startReview);
  $("#btn-mistakes")?.addEventListener("click", startMistakes);
  $("#btn-exam")?.addEventListener("click", startExam);
  $("#btn-confusion")?.addEventListener("click", startConfusionDrill);
  view.querySelector(".practice-grid")?.addEventListener("click", e => {
    const b = e.target.closest(".practice-tile");
    if (b) PRACTICE[b.dataset.practice]?.();
  });
}

/* ---------- «Разбор ошибок дня»: практика по сегодняшним промахам ----------
   Read-only: ответы НЕ уходят в SRS (runExercise без afterAnswer), поэтому
   расписание/статистика не меняются — это эффект тестирования и «остывание». */
async function startMistakes() {
  const token = openPlayer("practice");
  let data;
  try { data = await api.get("/api/review/mistakes?limit=30"); }
  catch { closePlayer(); return; }
  if (token !== sessionToken) return;
  const items = data.items;
  let done = 0, okCount = 0;
  for (let i = 0; i < items.length; i++) {
    if (token !== sessionToken) return;
    setProgress(done / Math.max(items.length, 1));
    $("#player-counter").textContent = tr("{n} · осталось ~{m}", { n: done, m: Math.max(items.length - i, 1) });
    const res = await runExercise(items[i].exercise);   // без afterAnswer → не пишем в SRS
    if (token !== sessionToken) return;
    done++;
    if (res.correct) okCount++;
    Combo.update(res.correct);
  }
  if (token !== sessionToken) return;
  setProgress(1);
  playerBody.classList.add("center-step");
  playerBody.innerHTML = `
    <div class="result">
      <div class="mark">復</div>
      <h2>${tr("Разбор ошибок завершён")}</h2>
      <p>${done ? tr("Повторено: {n} · сейчас верно {p}%", { n: done, p: Math.round(okCount / done * 100) })
                : tr("Сегодня ошибок нет — отлично!")}</p>
      <button class="primary" id="finish">${tr("Готово")}</button>
    </div>`;
  animateIn(playerBody);
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
}

/* ---------- Пробный мини-тест N5 (SRS.md 11.1 «Пробный экзамен») ----------
   Оценка по всей программе — i+1 сознательно не действует (это срез уровня,
   не обучение). Read-only: runExercise без afterAnswer, в SRS ничего не уходит.
   Таймер в шапке; по истечении времени оставшиеся вопросы идут в ошибки. */
async function startExam() {
  const token = openPlayer("exam");
  let paper;
  try { paper = await api.get("/api/exam?listening=" + (TTS.available ? 1 : 0)); }
  catch { toast(tr("Нет сети — попробуйте позже."), true); closePlayer(); return; }
  if (token !== sessionToken) return;
  const sections = paper.sections;
  const totalN = sections.reduce((n, s) => n + s.exercises.length, 0);
  const totalMin = Math.round(paper.time_limit_sec / 60);

  // Вступление: правила теста (таймер стартует после «Начать»)
  playerBody.classList.add("center-step");
  playerBody.innerHTML = `
    <div class="intro-screen">
      <div class="intro-ico jp c4">験</div>
      <h2 class="intro-title">${tr("Пробный тест N5")}</h2>
      <div class="intro-sub jp">${sections.map(s => s.jp).join("・")}</div>
      <p class="intro-text">${tr("{n} вопросов · {m} минут. Вопросы — по всей программе N5, в том числе ещё не пройденной. Результат не влияет на расписание повторений.", { n: totalN, m: totalMin })}</p>
      <div class="spacer"></div>
      <button class="primary" id="next">${tr("Начать")}</button>
    </div>`;
  animateIn(playerBody);
  if (await waitClick($("#next", playerBody)) === ABORT) return;

  const deadline = Date.now() + paper.time_limit_sec * 1000;
  let answeredN = 0;
  const counter = $("#player-counter");
  const tick = () => {
    const left = Math.max(0, deadline - Date.now());
    const m = Math.floor(left / 60000), s = Math.floor(left / 1000) % 60;
    counter.textContent = `${m}:${String(s).padStart(2, "0")} · ${answeredN}/${totalN}`;
  };
  tick();
  const timer = setInterval(() => {
    if (token !== sessionToken) { clearInterval(timer); return; }
    tick();
  }, 500);

  const results = [];
  let timeUp = false;
  try {
    for (const sec of sections) {
      const r = { title: sec.title, jp: sec.jp, ok: 0, total: sec.exercises.length };
      results.push(r);
      if (timeUp || !sec.exercises.length) continue;
      // Перебивка секции: что сейчас проверяем
      playerBody.classList.add("center-step");
      playerBody.innerHTML = `
        <div class="intro-screen">
          <div class="intro-ico jp c${results.length % 6}">${sec.jp.slice(0, 1)}</div>
          <h2 class="intro-title">${tr(sec.title)}</h2>
          <div class="intro-sub jp">${sec.jp}</div>
          <div class="spacer"></div>
          <button class="primary" id="next">${tr("Дальше")}</button>
        </div>`;
      animateIn(playerBody);
      if (await waitClick($("#next", playerBody)) === ABORT) return;
      for (const ex of sec.exercises) {
        if (Date.now() >= deadline) { timeUp = true; break; }
        setProgress(answeredN / totalN);
        const res = await runExercise(ex);          // без afterAnswer → read-only
        if (token !== sessionToken) return;
        answeredN++;
        if (res.correct) r.ok++;
        Combo.update(res.correct);
      }
    }
  } finally {
    clearInterval(timer);
  }

  setProgress(1);
  counter.textContent = "";
  const okTotal = results.reduce((n, r) => n + r.ok, 0);
  const pct = totalN ? Math.round(okTotal / totalN * 100) : 0;
  const passed = pct >= 80;                          // планка ворот юнита (раздел 3)
  const verdictText = passed
    ? tr("Отличная готовность! Такой результат — уверенный проходной.")
    : pct >= 60
      ? tr("Уже близко: подтяните слабые секции и попробуйте ещё раз.")
      : tr("Пока рано — продолжайте путь. Тест можно повторять в любой момент.");
  playerBody.classList.add("center-step");
  playerBody.innerHTML = `
    <div class="result">
      ${passed ? `<div class="result-mascot">${Art.mascotTile("cheer")}</div>` : `<div class="mark">験</div>`}
      <h2>${tr("Результат: {p}%", { p: pct })}</h2>
      <p>${verdictText}${timeUp ? `<br>${tr("Время вышло — оставшиеся вопросы засчитаны как ошибки.")}` : ""}</p>
      <div class="exam-breakdown">
        ${results.map(r => `
        <div class="exam-row">
          <span class="er-jp jp">${r.jp}</span>
          <span class="er-t">${tr(r.title)}</span>
          <div class="er-bar"><div style="width:${r.total ? Math.round(r.ok / r.total * 100) : 0}%"></div></div>
          <b class="er-n">${r.ok}/${r.total}</b>
        </div>`).join("")}
      </div>
      <button class="primary" id="finish">${tr("Готово")}</button>
    </div>`;
  animateIn(playerBody);
  if (passed) confetti();
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
}

/* ---------- Тренировка слуха: минимальные пары (5.5) ----------
   Read-only практика: проигрываем одно слово пары — выбери, что услышал.
   Тренирует фонематический слух (долгота гласного, удвоение «っ»). Озвучка
   обязательна — карточка скрыта без голоса (см. renderReviewTab). */
async function startListening() {
  const token = openPlayer("listen");
  let data;
  try { data = await api.get("/api/listen/pairs?limit=8"); }
  catch { toast(tr("Нет сети — попробуйте позже."), true); closePlayer(); return; }
  if (token !== sessionToken) return;
  const rounds = data.rounds;
  let done = 0, okCount = 0;
  for (let i = 0; i < rounds.length; i++) {
    if (token !== sessionToken) return;
    const r = rounds[i];
    setProgress(done / Math.max(rounds.length, 1));
    $("#player-counter").textContent = tr("{n} · осталось ~{m}", { n: done, m: Math.max(rounds.length - i, 1) });
    playerBody.classList.remove("center-step");
    playerBody.innerHTML = `
      <p class="question">${tr("Что вы услышали?")}</p>
      <button class="audio-prompt" id="lp-play" title="${tr("Прослушать ещё раз")}">${Icons.ui("speaker")}</button>
      <div class="options">
        ${r.options.map((o, j) =>
          `<button data-i="${j}" class="jp"><span class="kbd">${j + 1}</span>${o}</button>`).join("")}
      </div>
      <div class="feedback" id="fb" aria-live="polite"></div>
      <div class="spacer"></div>`;
    animateIn(playerBody);
    $("#lp-play", playerBody).addEventListener("click", () => speak(r.tts));
    speak(r.tts);

    const buttons = [...playerBody.querySelectorAll(".options button")];
    const choice = await awaitChoice(buttons);
    if (choice === ABORT) return;
    const correct = choice === r.answer;
    buttons.forEach(b => (b.disabled = true));
    buttons[r.answer].classList.add("correct");
    if (!correct) buttons[choice].classList.add("wrong");
    const fb = $("#fb", playerBody);
    fb.className = `feedback ${correct ? "ok" : "bad"}`;
    Haptics[correct ? "good" : "bad"]();
    answerFx(correct, $("#lp-play", playerBody));
    // Раскрываем ОБА слова с переводом — пара осмысленна только вместе
    fb.innerHTML = verdict(correct, correct ? tr("Верно") : tr("Вы выбрали не то слово")) +
      `<div class="lp-reveal">${r.options.map((o, j) =>
        `<div class="lp-word ${j === r.answer ? "right" : ""}">
           <span class="jp">${o}</span><small>${r.romaji[j]} · ${tr(r.meanings[j])}</small></div>`).join("")}</div>`;
    speak(r.tts);
    done++;
    if (correct) okCount++;
    Combo.update(correct);
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
    if (await waitClick($("#next", playerBody)) === ABORT) return;
  }
  if (token !== sessionToken) return;
  setProgress(1);
  playerBody.classList.add("center-step");
  playerBody.innerHTML = `
    <div class="result">
      ${done ? `<div class="result-mascot">${Art.mascotTile("cheer")}</div>` : `<div class="mark">耳</div>`}
      <h2>${tr("Слух натренирован")}</h2>
      <p>${tr("Пар на слух: {n} · точность {p}%", { n: done, p: Math.round(okCount / Math.max(done, 1) * 100) })}</p>
      <button class="primary" id="finish">${tr("Готово")}</button>
    </div>`;
  animateIn(playerBody);
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
}

/* ---------- Кузница кандзи 鍛冶 (Sprint: Кузница) ----------
   Собрать выученный иероглиф из компонентов-радикалов (木 + 木 = 林) — обратная
   сторона разбора кандзи (6.3). Read-only практика: в SRS не пишет. Учитывает
   повторы компонентов (мультимножество). */
async function startForge() {
  const token = openPlayer("forge");
  let data;
  try { data = await api.get("/api/forge/rounds?limit=8"); }
  catch { toast(tr("Нет сети — попробуйте позже."), true); closePlayer(); return; }
  if (token !== sessionToken) return;
  const rounds = data.rounds;
  if (!rounds.length) {
    playerBody.classList.add("center-step");
    playerBody.innerHTML = `<div class="result"><div class="mark">鍛</div>
      <h2>${tr("Пока нечего ковать")}</h2>
      <p>${tr("Выучите кандзи с разбором на части (林, 明, 男…) — и соберёте их здесь.")}</p>
      <button class="primary" id="finish">${tr("Готово")}</button></div>`;
    animateIn(playerBody);
    if (await waitClick($("#finish", playerBody)) === ABORT) return;
    closePlayer();
    return;
  }
  let done = 0, okCount = 0;
  for (let i = 0; i < rounds.length; i++) {
    if (token !== sessionToken) return;
    setProgress(done / rounds.length);
    $("#player-counter").textContent = tr("{n} · осталось ~{m}", { n: done, m: Math.max(rounds.length - i, 1) });
    const res = await forgeRound(rounds[i]);
    if (res === ABORT || token !== sessionToken) return;
    done++;
    if (res) okCount++;
    Combo.update(res);
  }
  if (token !== sessionToken) return;
  setProgress(1);
  playerBody.classList.add("center-step");
  playerBody.innerHTML = `<div class="result">
      <div class="result-mascot">${Art.mascotTile("cheer")}</div>
      <h2>${tr("Кузница остыла")}</h2>
      <p>${tr("Сковано: {n} · точность {p}%", { n: done, p: Math.round(okCount / Math.max(done, 1) * 100) })}</p>
      <button class="primary" id="finish">${tr("Готово")}</button>
    </div>`;
  animateIn(playerBody);
  if (done >= 5) confetti();
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
}

async function forgeRound(r) {
  playerBody.classList.remove("center-step");
  if (window.__noPrefWrite) window.__forgeRound = r;   // тест-хук для headless-проверки
  const need = r.components.length;
  playerBody.innerHTML = `
    <p class="question">${tr("Соберите кандзи из частей")}</p>
    <div class="forge-clue">
      <div class="forge-meaning">${tr(r.meaning)}</div>
      <button class="forge-reading jp" data-tts="${r.tts}">${Icons.ui("speaker")} ${r.reading}</button>
    </div>
    <div class="build-slots forge-slots" id="fslots"></div>
    <div class="tiles forge-tiles" id="ftiles">
      ${r.tiles.map((t, i) => `<button class="forge-tile" data-i="${i}">
        <span class="ft-char jp">${t.char}</span><small>${tr(t.meaning)}</small></button>`).join("")}
    </div>
    <div class="feedback" id="fb" aria-live="polite"></div>
    <button class="primary" id="forge" disabled>${tr("Сковать")}</button>`;
  animateIn(playerBody);
  speak(r.tts);

  const slots = $("#fslots", playerBody);
  const forgeBtn = $("#forge", playerBody);
  const assembled = [];                       // [{char, btn}]
  const renderSlots = () => {
    slots.innerHTML = assembled.map((a, i) =>
      `<span data-pos="${i}" class="jp" title="${tr("Убрать")}">${a.char}</span>`).join("");
    forgeBtn.disabled = assembled.length !== need;
  };

  const finished = abortable(res => {
    $("#ftiles", playerBody).addEventListener("click", e => {
      const b = e.target.closest(".forge-tile");
      if (!b || b.disabled || assembled.length >= need) return;
      b.disabled = true;
      assembled.push({ char: b.querySelector(".ft-char").textContent, btn: b });
      renderSlots();
    });
    slots.addEventListener("click", e => {
      const s = e.target.closest("span");
      if (!s) return;
      const [rm] = assembled.splice(+s.dataset.pos, 1);
      rm.btn.disabled = false;
      renderSlots();
    });
    forgeBtn.addEventListener("click", () => { if (assembled.length === need) res(); });
  });
  if (await finished === ABORT) return ABORT;

  // Сверка по мультимножеству (учёт повторов: 林 = 木 + 木)
  const got = assembled.map(a => a.char).sort();
  const want = r.components.map(c => c.char).sort();
  const correct = got.length === want.length && got.every((c, i) => c === want[i]);

  $("#ftiles", playerBody).style.pointerEvents = "none";
  slots.style.pointerEvents = "none";
  const fb = $("#fb", playerBody);
  fb.className = `feedback ${correct ? "ok" : "bad"}`;
  Haptics[correct ? "good" : "bad"]();
  answerFx(correct, slots);
  const parts = r.components.map(c =>
    `<span class="part jp">${c.char}<small>${tr(c.meaning)}</small></span>`).join(`<i class="op">+</i>`);
  fb.innerHTML = verdict(correct, correct ? tr("Сковано!") : tr("Не сошлось — вот верный разбор"))
    + `<div class="kanji-parts forge-assembled">${parts}<i class="op">=</i>`
    + `<span class="part whole jp">${r.char}</span></div>`;
  speak(r.tts);

  forgeBtn.remove();
  playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
  if (await waitClick($("#next", playerBody)) === ABORT) return ABORT;
  return correct;
}

/* ---------- Сиритори しりとり (Sprint: словесная цепочка) ----------
   Японская игра: каждое слово начинается с последней каны предыдущего. Реальная
   цепочка из изученных слов приходит с сервера (/api/shiritori). Read-only. */
async function startShiritori() {
  const token = openPlayer("shiritori");
  let data;
  try { data = await api.get("/api/shiritori/rounds?limit=8"); }
  catch { toast(tr("Нет сети — попробуйте позже."), true); closePlayer(); return; }
  if (token !== sessionToken) return;
  const rounds = data.rounds;
  if (!rounds.length) {
    playerBody.classList.add("center-step");
    playerBody.innerHTML = `<div class="result"><div class="mark">語</div>
      <h2>${tr("Пока некого ставить в цепочку")}</h2>
      <p>${tr("Выучите больше слов — и сможете играть в цепочку каны.")}</p>
      <button class="primary" id="finish">${tr("Готово")}</button></div>`;
    animateIn(playerBody);
    if (await waitClick($("#finish", playerBody)) === ABORT) return;
    closePlayer();
    return;
  }
  const chain = [rounds[0].current.kana];           // растущая видимая цепочка
  const ribbon = () => `<div class="shiri-chain">${chain.map((k, i) =>
    `<span class="shiri-link${i === chain.length - 1 ? " last" : ""} jp">${escapeHtml(k)}</span>`
  ).join('<i class="shiri-arrow">→</i>')}</div>`;
  let done = 0, okCount = 0;
  for (let i = 0; i < rounds.length; i++) {
    if (token !== sessionToken) return;
    const r = rounds[i];
    setProgress(done / rounds.length);
    $("#player-counter").textContent = tr("{n} · осталось ~{m}", { n: done, m: Math.max(rounds.length - i, 1) });
    playerBody.classList.remove("center-step");
    playerBody.innerHTML = `
      ${ribbon()}
      <p class="question">${tr("Слово на 「{k}」 — продолжите цепочку", { k: r.need })}</p>
      <button class="shiri-current jp" data-tts="${r.current.tts}">
        <span class="sc-kana">${escapeHtml(r.current.kana)}</span>
        <small>${escapeHtml(tr(r.current.ru))} ${Icons.ui("speaker")}</small></button>
      <div class="options shiri-options">
        ${r.options.map((o, j) => `<button data-i="${j}" class="shiri-opt">
          <span class="kbd">${j + 1}</span><span class="so-kana jp">${escapeHtml(o.kana)}</span>
          <small>${escapeHtml(tr(o.ru))}</small></button>`).join("")}
      </div>
      <div class="feedback" id="fb" aria-live="polite"></div>`;
    animateIn(playerBody);
    speak(r.current.tts);
    const buttons = [...playerBody.querySelectorAll(".shiri-options button")];
    const choice = await awaitChoice(buttons);
    if (choice === ABORT) return;
    const correct = choice === r.answer;
    buttons.forEach(b => (b.disabled = true));
    buttons[r.answer].classList.add("correct");
    if (!correct) buttons[choice].classList.add("wrong");
    const picked = r.options[r.answer];             // в цепочку идёт верное продолжение
    chain.push(picked.kana);
    const fb = $("#fb", playerBody);
    fb.className = `feedback ${correct ? "ok" : "bad"}`;
    Haptics[correct ? "good" : "bad"]();
    answerFx(correct, playerBody.querySelector(".shiri-current"));
    fb.innerHTML = verdict(correct, correct ? tr("Верно")
      : tr("Цепочку продолжает: {x}", { x: `<span class="jp">${escapeHtml(picked.kana)}</span>` }));
    speak(picked.tts);
    done++;
    if (correct) okCount++;
    Combo.update(correct);
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
    if (await waitClick($("#next", playerBody)) === ABORT) return;
  }
  if (token !== sessionToken) return;
  setProgress(1);
  playerBody.classList.add("center-step");
  playerBody.innerHTML = `<div class="result">
      <div class="result-mascot">${Art.mascotTile("cheer")}</div>
      <h2>${tr("Цепочка собрана!")}</h2>
      <p>${tr("Слов в цепочке: {n} · точность {p}%", { n: chain.length, p: Math.round(okCount / Math.max(done, 1) * 100) })}</p>
      ${ribbon()}
      <button class="primary" id="finish">${tr("Готово")}</button>
    </div>`;
  animateIn(playerBody);
  if (done >= 5) confetti();
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
}

/* ---------- Счётные суффиксы 助数詞 (Sprint: счётные слова) ----------
   Японский считает разные предметы разными словами (3匹 / 3冊 / 3台). Дано
   N предметов — выбрать верное счётное слово. Чистая практика, в SRS не пишет. */
async function startCounters() {
  const token = openPlayer("counters");
  let data;
  try { data = await api.get("/api/counters/rounds?limit=8"); }
  catch { toast(tr("Нет сети — попробуйте позже."), true); closePlayer(); return; }
  if (token !== sessionToken) return;
  const rounds = data.rounds;
  let done = 0, okCount = 0;
  for (let i = 0; i < rounds.length; i++) {
    if (token !== sessionToken) return;
    const r = rounds[i];
    setProgress(done / Math.max(rounds.length, 1));
    $("#player-counter").textContent = tr("{n} · осталось ~{m}", { n: done, m: Math.max(rounds.length - i, 1) });
    playerBody.classList.remove("center-step");
    playerBody.innerHTML = `
      <div class="cnt-objects" aria-hidden="true">${(r.noun.emoji + " ").repeat(r.count).trim()}</div>
      <button class="cnt-noun jp" data-tts="${r.noun.tts}">
        <span class="cn-kana">${escapeHtml(r.noun.kana)}</span>
        <small>${escapeHtml(tr(r.noun.ru))} × ${r.count} ${Icons.ui("speaker")}</small></button>
      <p class="question">${tr("Каким счётным словом их сосчитать?")}</p>
      <div class="options cnt-options">
        ${r.options.map((o, j) => `<button data-i="${j}" class="cnt-opt">
          <span class="kbd">${j + 1}</span><span class="co-char jp">${o.counter}</span>
          <small>${o.reading}</small></button>`).join("")}
      </div>
      <div class="feedback" id="fb" aria-live="polite"></div>`;
    animateIn(playerBody);
    speak(r.noun.tts);
    const buttons = [...playerBody.querySelectorAll(".cnt-options button")];
    const choice = await awaitChoice(buttons);
    if (choice === ABORT) return;
    const correct = choice === r.answer;
    buttons.forEach(b => (b.disabled = true));
    buttons[r.answer].classList.add("correct");
    if (!correct) buttons[choice].classList.add("wrong");
    const right = r.options[r.answer];
    const fb = $("#fb", playerBody);
    fb.className = `feedback ${correct ? "ok" : "bad"}`;
    Haptics[correct ? "good" : "bad"]();
    answerFx(correct, playerBody.querySelector(".cnt-noun"));
    fb.innerHTML = verdict(correct, correct ? tr("Верно")
      : tr("Правильно: {x}", { x: `<span class="jp">${right.counter}</span>` }))
      + `<div class="cnt-why"><span class="jp">${right.counter}</span> <b>${right.reading}</b> — ${tr(right.meaning)}</div>`;
    done++;
    if (correct) okCount++;
    Combo.update(correct);
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
    if (await waitClick($("#next", playerBody)) === ABORT) return;
  }
  if (token !== sessionToken) return;
  setProgress(1);
  playerBody.classList.add("center-step");
  playerBody.innerHTML = `<div class="result">
      ${done ? `<div class="result-mascot">${Art.mascotTile("cheer")}</div>` : `<div class="mark">数</div>`}
      <h2>${tr("Счётчики освоены")}</h2>
      <p>${tr("Предметов сосчитано: {n} · точность {p}%", { n: done, p: Math.round(okCount / Math.max(done, 1) * 100) })}</p>
      <button class="primary" id="finish">${tr("Готово")}</button>
    </div>`;
  animateIn(playerBody);
  if (done >= 5) confetti();
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
}

/* ---------- Дрилл высотного ударения 高低 (USP: произношение) ----------
   Дано слово (кана + озвучка) — выбрать тип акцента из 4 (平板/頭高/中高/尾高).
   Контур показывается ПОСЛЕ ответа (активное распознавание, не подсказка).
   Практика — в SRS ничего не пишет. */
async function startPitch() {
  const token = openPlayer("pitch");
  let data;
  try { data = await api.get("/api/pitch/rounds?limit=8"); }
  catch { toast(tr("Нет сети — попробуйте позже."), true); closePlayer(); return; }
  if (token !== sessionToken) return;
  const rounds = data.rounds;
  let done = 0, okCount = 0;
  for (let i = 0; i < rounds.length; i++) {
    if (token !== sessionToken) return;
    const r = rounds[i];
    setProgress(done / Math.max(rounds.length, 1));
    $("#player-counter").textContent = tr("{n} · осталось ~{m}", { n: done, m: Math.max(rounds.length - i, 1) });
    playerBody.classList.remove("center-step");
    playerBody.innerHTML = `
      <div class="big-kana small" data-tts="${escAttr(r.tts)}">${escapeHtml(r.kana)}</div>
      <div class="word-ru">${tr(r.ru)}</div>
      ${ttsButton(r.tts)}
      <p class="question">${tr("Какой у слова тон?")}</p>
      <div class="options pitch-options">
        ${r.options.map((o, j) => `<button data-i="${j}" class="cnt-opt pi-opt">
          <span class="kbd">${j + 1}</span><span class="co-char jp">${PITCH_JP[o]}</span>
          <small>${tr(PITCH_DESC[o])}</small></button>`).join("")}
      </div>
      <div class="feedback" id="fb" aria-live="polite"></div>`;
    animateIn(playerBody);
    speak(r.tts);
    const buttons = [...playerBody.querySelectorAll(".pitch-options button")];
    const choice = await awaitChoice(buttons);
    if (choice === ABORT) return;
    const correct = choice === r.answer;
    buttons.forEach(b => (b.disabled = true));
    buttons[r.answer].classList.add("correct");
    if (!correct) buttons[choice].classList.add("wrong");
    const fb = $("#fb", playerBody);
    fb.className = `feedback ${correct ? "ok" : "bad"}`;
    Haptics[correct ? "good" : "bad"]();
    answerFx(correct, playerBody.querySelector(".big-kana"));
    // Раскрываем контур слова — главное обучающее звено: связать тип со звучанием
    fb.innerHTML = verdict(correct, correct ? tr("Верно")
      : tr("Правильно: {x}", { x: PITCH_JP[r.options[r.answer]] }))
      + pitchHtml(r.pitch);
    done++;
    if (correct) okCount++;
    Combo.update(correct);
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
    if (await waitClick($("#next", playerBody)) === ABORT) return;
  }
  if (token !== sessionToken) return;
  setProgress(1);
  playerBody.classList.add("center-step");
  playerBody.innerHTML = `<div class="result">
      ${done ? `<div class="result-mascot">${Art.mascotTile("cheer")}</div>` : `<div class="mark">高</div>`}
      <h2>${tr("Тон освоен")}</h2>
      <p>${tr("Слов разобрано: {n} · точность {p}%", { n: done, p: Math.round(okCount / Math.max(done, 1) * 100) })}</p>
      <button class="primary" id="finish">${tr("Готово")}</button>
    </div>`;
  animateIn(playerBody);
  if (done >= 5) confetti();
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
}

/* ---------- Радар путаницы: дрилл-различение по личным ошибкам ----------
   Берём пары, которые ученик реально путал на повторениях (db.confusions), и
   гоняем различение: дано чтение — выбрать верный знак из двух спутанных.
   Практика — в SRS не пишет. */
async function startConfusionDrill() {
  const token = openPlayer("confusion");
  let data;
  try { data = await api.get("/api/confusions/rounds?limit=10"); }
  catch { toast(tr("Нет сети — попробуйте позже."), true); closePlayer(); return; }
  if (token !== sessionToken) return;
  const rounds = data.rounds;
  if (!rounds.length) {
    playerBody.classList.add("center-step");
    playerBody.innerHTML = `<div class="result"><div class="mark">的</div>
      <h2>${tr("Путаниц пока нет")}</h2>
      <p>${tr("Здесь появятся знаки, которые вы путаете на повторениях.")}</p>
      <button class="primary" id="finish">${tr("Готово")}</button></div>`;
    animateIn(playerBody);
    waitClick($("#finish", playerBody)).then(v => { if (v !== ABORT) closePlayer(); });
    return;
  }
  let done = 0, okCount = 0;
  for (let i = 0; i < rounds.length; i++) {
    if (token !== sessionToken) return;
    const r = rounds[i];
    setProgress(done / Math.max(rounds.length, 1));
    $("#player-counter").textContent = tr("{n} · осталось ~{m}", { n: done, m: Math.max(rounds.length - i, 1) });
    playerBody.classList.remove("center-step");
    playerBody.innerHTML = `
      <p class="question">${tr("Какой знак читается так?")}</p>
      <div class="romaji-big">${escapeHtml(r.prompt)}</div>
      ${ttsButton(r.tts)}
      <div class="options">
        ${r.options.map((o, j) => `<button data-i="${j}" class="jp"><span class="kbd">${j + 1}</span>${escapeHtml(o)}</button>`).join("")}
      </div>
      <div class="feedback" id="fb" aria-live="polite"></div>`;
    animateIn(playerBody);
    speak(r.tts);
    const buttons = [...playerBody.querySelectorAll(".options button")];
    const choice = await awaitChoice(buttons);
    if (choice === ABORT) return;
    const correct = choice === r.answer;
    buttons.forEach(b => (b.disabled = true));
    buttons[r.answer].classList.add("correct");
    if (!correct) buttons[choice].classList.add("wrong");
    const fb = $("#fb", playerBody);
    fb.className = `feedback ${correct ? "ok" : "bad"}`;
    Haptics[correct ? "good" : "bad"]();
    answerFx(correct, playerBody.querySelector(".romaji-big"));
    fb.innerHTML = verdict(correct, correct ? tr("Верно")
      : tr("Правильно: {x}", { x: `<span class="jp">${escapeHtml(r.options[r.answer])}</span>` }));
    speak(r.tts);
    done++;
    if (correct) okCount++;
    Combo.update(correct);
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">${tr("Дальше")}</button>`);
    if (await waitClick($("#next", playerBody)) === ABORT) return;
  }
  if (token !== sessionToken) return;
  setProgress(1);
  playerBody.classList.add("center-step");
  playerBody.innerHTML = `<div class="result">
      ${done ? `<div class="result-mascot">${Art.mascotTile("cheer")}</div>` : `<div class="mark">的</div>`}
      <h2>${tr("Различение отработано")}</h2>
      <p>${tr("Разобрано: {n} · точность {p}%", { n: done, p: Math.round(okCount / Math.max(done, 1) * 100) })}</p>
      <button class="primary" id="finish">${tr("Готово")}</button>
    </div>`;
  animateIn(playerBody);
  if (done >= 5) confetti();
  if (await waitClick($("#finish", playerBody)) === ABORT) return;
  closePlayer();
}

/* ---------- Каллиграфия 書道 (Sprint: Каллиграфия-арт) ----------
   Выразительное письмо кистью поверх готового движка прописей. Не тест: ничего
   не пишет в SRS. Выбираем выученный знак (кана/кандзи) → пишем кистью → можно
   сохранить свою работу картинкой (Tracing.calligraphy). */
async function startCalligraphy() {
  const token = openPlayer("calligraphy");
  let data;
  try { data = await api.get("/api/learned"); }
  catch { toast(tr("Нет сети — попробуйте позже."), true); closePlayer(); return; }
  if (token !== sessionToken) return;
  const chars = [];
  const seen = new Set();
  for (const c of data.courses) {
    if (!["hiragana", "katakana", "kanji"].includes(c.id)) continue;
    for (const it of c.items) {
      if ([...it.title].length === 1 && !seen.has(it.title)) {
        seen.add(it.title);
        chars.push({ char: it.title, reading: it.tts || "", sub: it.sub });
      }
    }
  }
  const pick = () => {
    playerBody.classList.add("center-step");
    if (!chars.length) {
      playerBody.innerHTML = `<div class="result"><div class="mark">書</div>
        <h2>${tr("Пока нечего писать")}</h2>
        <p>${tr("Выучите кану или кандзи — и сможете написать их кистью.")}</p></div>`;
      animateIn(playerBody);
      return;
    }
    playerBody.innerHTML = `
      <p class="question">${tr("Выберите знак для каллиграфии")}</p>
      <div class="cal-pick">${chars.map((c, i) =>
        `<button class="cal-pick-item jp" data-i="${i}">${escapeHtml(c.char)}</button>`).join("")}</div>`;
    animateIn(playerBody);
    playerBody.querySelectorAll(".cal-pick-item").forEach(b =>
      b.addEventListener("click", () => draw(chars[+b.dataset.i])));
  };
  const draw = (c) => {
    playerBody.classList.remove("center-step");
    playerBody.innerHTML = `
      <p class="question">${tr("Напишите красиво — кистью")}</p>
      <div id="cal-host"></div>
      <button class="ghost mt" id="cal-back">← ${tr("Выбрать другой знак")}</button>`;
    animateIn(playerBody);
    Tracing.calligraphy($("#cal-host", playerBody), { char: c.char, reading: c.reading });
    speak(c.reading || c.char);
    $("#cal-back", playerBody).addEventListener("click", pick);
  };
  pick();
}

/* ---------- «Свиток истории» 物語 (обучение через контекст) ----------
   Растущая история: главы открываются по мере прохождения уроков и собраны
   только из изученных слов (i+1, проверяется на сервере). Это чтение, не тест —
   в SRS ничего не пишется. Picker глав → ридер сцен (тап по строке = озвучка). */
async function startStory() {
  const token = openPlayer("story");
  let data;
  try { data = await api.get("/api/story"); }
  catch { toast(tr("Нет сети — попробуйте позже."), true); closePlayer(); return; }
  if (token !== sessionToken) return;
  const chapters = data.chapters;
  const unlockedCount = chapters.filter(c => c.unlocked).length;

  const pick = () => {
    if (!unlockedCount) {
      playerBody.classList.add("center-step");
      playerBody.innerHTML = `<div class="result"><div class="mark">巻</div>
        <h2>${tr("Свиток ещё закрыт")}</h2>
        <p>${tr("Пройдите первые уроки лексики — и откроется первая глава истории.")}</p>
        <button class="primary" id="finish">${tr("Готово")}</button></div>`;
      animateIn(playerBody);
      waitClick($("#finish", playerBody)).then(v => { if (v !== ABORT) closePlayer(); });
      return;
    }
    playerBody.classList.remove("center-step");
    playerBody.innerHTML = `
      <p class="question">${tr("Свиток истории")} 物語</p>
      <div class="story-chapters">${chapters.map((c, i) => `
        <button class="story-chapter ${c.unlocked ? "" : "locked"}" data-i="${i}" ${c.unlocked ? "" : "disabled"}>
          <span class="sc-num jp">${i + 1}</span>
          <span class="sc-meta"><span class="sc-jp jp">${escapeHtml(c.jp)}</span><span class="sc-title">${escapeHtml(tr(c.title))}</span></span>
          <span class="sc-state">${c.unlocked ? "›" : Icons.ui("lock")}</span>
        </button>`).join("")}</div>`;
    animateIn(playerBody);
    playerBody.querySelectorAll(".story-chapter:not(.locked)").forEach(b =>
      b.addEventListener("click", () => read(chapters[+b.dataset.i])));
  };

  const read = (ch) => {
    playerBody.classList.remove("center-step");
    playerBody.innerHTML = `
      <div class="story-read">
        <div class="story-head"><span class="sh-jp jp">${escapeHtml(ch.jp)}</span><h2>${escapeHtml(tr(ch.title))}</h2></div>
        <div class="story-scenes">${ch.scenes.map(s => `
          <div class="story-scene">
            <button class="story-jp jp" data-tts="${escAttr(s.tts)}">${escapeHtml(s.jp)} <span class="sj-spk">${Icons.ui("speaker")}</span></button>
            <div class="story-ru">${escapeHtml(tr(s.ru))}</div>
          </div>`).join("")}</div>
        <button class="ghost mt" id="story-back">← ${tr("К главам")}</button>
      </div>`;
    animateIn(playerBody);
    $("#story-back", playerBody).addEventListener("click", pick);
  };

  pick();
}

/* ---------- Словарь: справочник изученного ----------
   Всё, что попало в SRS (введено на уроках), сгруппировано по курсам. Клик по
   элементу с озвучкой — проигрывает (глобальный [data-tts]-обработчик). */
// Галерея личных ассоциаций (только RU): свои заметки + выбранные не-дефолтные
// пресеты по уже изученным знакам. Опирается на it.mn (пресеты из /api/learned).
function mnemoGalleryHtml(courses) {
  const seen = new Set();
  const entries = [];
  for (const c of courses) for (const it of c.items) {
    const g = it.title;
    if (seen.has(g)) continue;
    let text = null, tag = "";
    const custom = Mnemo.custom(g);
    if (custom) { text = custom; tag = tr("своя"); }
    else if (it.mn && it.mn.length) {
      const f = Mnemo.fav(g);
      if (typeof f === "number" && f > 0 && f < it.mn.length) { text = it.mn[f]; tag = tr("выбрана"); }
    }
    if (!text) continue;
    seen.add(g);
    entries.push(`<button class="mg-item"${it.tts ? ` data-tts="${escapeHtml(it.tts)}"` : ""}>
      <span class="mg-char jp">${escapeHtml(g)}</span>
      <span class="mg-text">${escapeHtml(text)}</span>
      <span class="mg-tag">${tag}</span></button>`);
  }
  if (!entries.length) return "";
  return `<div class="card mnemo-gallery">
    <h2>${tr("Мои ассоциации")} · ${entries.length}</h2>
    <p class="note">${tr("Твои собственные и выбранные образы. Нажми — послушать знак.")}</p>
    <div class="mg-grid">${entries.join("")}</div>
  </div>`;
}

/* Карта памяти: каждый выученный знак — клетка, цвет = «сила памяти» (FSRS-R,
   поле strength из /api/learned). Даёт здоровье знаний одним взглядом; тусклые
   клетки — кандидаты на «Освежить заранее» на «Сегодня». Тап — послушать. */
function memoryMapHtml(courses) {
  const items = [];
  for (const c of courses) for (const it of c.items)
    if (it.strength != null) items.push(it);
  if (items.length < 6) return "";          // мало данных — карта неинформативна
  items.sort((a, b) => a.strength - b.strength);   // слабые вперёд — взгляд цепляется за риск
  const strong = items.filter(i => i.strength >= 85).length;
  const fading = items.filter(i => i.strength >= 60 && i.strength < 85).length;
  const risk = items.filter(i => i.strength < 60).length;
  // Сад (8/USP): дерево сакуры — цветущих бутонов = крепких знаков, бледных =
  // тускнеющих, опадающих лепестков = рискующих. Эмоциональный «снимок» здоровья
  // знаний; тепловая решётка ниже даёт ту же картину детально, поэлементно.
  const caption = risk > 0
    ? tr("Несколько знаков вянут — освежите их на «Сегодня»")
    : (fading <= strong * 0.3
        ? tr("Сад в полном цвету 🌸")
        : tr("Сад растёт — так держать!"));
  const cells = items.map(it => {
    const mem = tr("Память {p}%", { p: it.strength });
    return `<button class="mm-cell" style="--s:${it.strength}"${
      it.tts ? ` data-tts="${escapeHtml(it.tts)}"` : ""}
      title="${escapeHtml(it.title)} · ${mem}" aria-label="${escapeHtml(it.title)} ${mem}"></button>`;
  }).join("");
  return `<div class="card mem-map">
    <h2>${tr("Сад памяти")} · ${items.length}</h2>
    <div class="mem-garden">${Art.garden(strong, fading, risk)}</div>
    <p class="garden-caption">${caption}</p>
    <p class="note" style="margin-top:0">${tr("Каждая клетка — выученный знак, цвет = насколько он свеж в памяти. Тусклые освежите на «Сегодня».")}</p>
    <div class="mm-grid">${cells}</div>
    <div class="mm-legend">
      <span class="mm-leg strong">${tr("крепко")} · ${strong}</span>
      <span class="mm-leg fading">${tr("тускнеет")} · ${fading}</span>
      <span class="mm-leg risk">${tr("рискует")} · ${risk}</span>
    </div>
  </div>`;
}

async function renderDict() {
  view.innerHTML = skeleton("dict");
  const data = await api.get("/api/learned");
  if (!data.courses.length) {
    view.innerHTML = `<div class="dict-wrap"><div class="card empty-state">
      <div class="empty-mascot">${Art.mascotTile("wave")}</div>
      <p class="note center">${tr("Пока пусто — пройдите урок, и выученное появится здесь для повторения.")}</p>
    </div></div>`;
    return;
  }
  const label = { new: tr("новое"), learning: tr("учится"), review: tr("в памяти") };
  const memMap = memoryMapHtml(data.courses);
  const gallery = LANG === "ru" ? mnemoGalleryHtml(data.courses) : "";

  // Поиск + фильтр по состоянию (B1): словарь может быть 700+ элементов — найти
  // нужный знак прокруткой тяжело. data-s — строка поиска (знак/перевод/чтение).
  const STATES = [["all", "Все"], ["learning", "Учится"],
                  ["review", "В памяти"], ["leech", "Трудные"]];
  const controls = `
    <div class="dict-search">
      <input id="dict-q" type="search" inputmode="search" autocomplete="off"
        spellcheck="false" placeholder="${tr("Поиск: знак, чтение или перевод")}"
        aria-label="${tr("Поиск по словарю")}">
    </div>
    <div class="course-tabs dict-filters">${STATES.map(([k, v], i) =>
      `<button class="course-tab ${i === 0 ? "active" : ""}" data-st="${k}">${tr(v)}</button>`).join("")}</div>`;

  const itemHtml = it => {
    const s = [it.title, it.sub ? tr(it.sub) : "", it.extra || ""].join(" ").toLowerCase();
    return `<button class="dict-item st-${it.state}${it.leech ? " leech" : ""}" data-s="${escAttr(s)}"${
      it.tts ? ` data-tts="${escapeHtml(it.tts)}"` : ""}>
      <span class="di-title jp">${escapeHtml(it.title)}</span>
      ${it.extra ? `<span class="di-extra jp">${escapeHtml(it.extra)}</span>` : ""}
      ${it.pitch ? pitchHtml(it.pitch, true) : ""}
      <span class="di-sub">${escapeHtml(it.sub ? tr(it.sub) : "")}</span>
      <span class="di-state">${label[it.state]}</span>
      ${it.strength != null ? `<span class="di-strength" style="--s:${it.strength}" title="${tr("Память {p}%", { p: it.strength })}" aria-label="${tr("Память {p}%", { p: it.strength })}"></span>` : ""}
    </button>`;
  };

  view.innerHTML = `<div class="dict-wrap stagger">`
    + controls
    + `<div class="dict-aggregate">` + memMap + gallery + `</div>`
    + `<p class="dict-empty note center" hidden>${tr("Ничего не найдено")}</p>`
    + data.courses.map(c => `
      <div class="card dict-course">
        <h2>${tr(COURSE_LABEL[c.id] || c.title)} · <span class="dc-count">${c.count}</span></h2>
        <div class="dict-grid">${c.items.map(itemHtml).join("")}</div>
      </div>`).join("")
    + `</div>`;

  // Фильтрация по месту (без перерисовки): прячем не подходящие элементы и пустые
  // карточки; агрегаты (Сад/галерея) скрываем, пока активен поиск/фильтр.
  const qInput = $("#dict-q", view);
  let stFilter = "all";
  const apply = () => {
    const query = qInput.value.trim().toLowerCase();
    let found = 0;
    view.querySelectorAll(".dict-course").forEach(card => {
      let shown = 0;
      card.querySelectorAll(".dict-item").forEach(el => {
        const okQ = !query || el.dataset.s.includes(query);
        const okSt = stFilter === "all"
          || (stFilter === "leech" ? el.classList.contains("leech")
              : el.classList.contains("st-" + stFilter));
        const show = okQ && okSt;
        el.classList.toggle("hide", !show);
        if (show) shown++;
      });
      const cnt = card.querySelector(".dc-count");
      if (cnt) cnt.textContent = shown;
      card.classList.toggle("hide", shown === 0);
      found += shown;
    });
    const filtering = !!query || stFilter !== "all";
    view.querySelector(".dict-aggregate")?.classList.toggle("hide", filtering);
    view.querySelector(".dict-empty").hidden = found > 0;
  };
  qInput.addEventListener("input", apply);
  view.querySelectorAll(".dict-filters .course-tab").forEach(b =>
    b.addEventListener("click", () => {
      stFilter = b.dataset.st;
      view.querySelectorAll(".dict-filters .course-tab").forEach(
        x => x.classList.toggle("active", x === b));
      apply();
    }));
}

/* ---------- Статистика ---------- */
const fmtDay = iso => `${iso.slice(8, 10)}.${iso.slice(5, 7)}`;

function barChart(data, valueKey, dateKey, cls = "", titleFn = null) {
  const max = Math.max(...data.map(d => d[valueKey]), 1);
  return `<div class="bars">${data.map((d, i) => `
    <div class="bar ${cls}" title="${titleFn ? titleFn(d, i) : `${fmtDay(d[dateKey])}: ${d[valueKey]}`}">
      <div style="height:${Math.round(d[valueKey] / max * 100)}%"></div>
      <small>${i % 2 ? "" : fmtDay(d[dateKey])}</small>
    </div>`).join("")}</div>`;
}

/* Список <option> с выбранным текущим значением; если текущего нет среди
   пресетов — добавляем его, чтобы нестандартное значение не пропало. */
function optionList(values, current, label) {
  const set = values.includes(current) ? values : [current, ...values].sort((a, b) => a - b);
  return set.map(v =>
    `<option value="${v}" ${v === current ? "selected" : ""}>${label(v)}</option>`).join("");
}

async function renderStats() {
  view.innerHTML = skeleton("stats");
  const [s, ach] = await Promise.all([
    api.get("/api/stats"), api.get("/api/achievements")]);
  const c = s.cards;
  const hasActivity = s.activity.some(d => d.reviews > 0);
  view.innerHTML = `
    <div class="stats-wrap stagger">
    <div class="card">
      <h2>${tr("Мои карточки")}</h2>
      <div class="stat-trio">
        <div><b>${c.review}</b><span>${tr("в долгой памяти")}</span></div>
        <div><b>${c.learning + c.relearning}</b><span>${tr("ещё учатся")}</span></div>
        <div><b>${s.retention.week ?? "—"}${s.retention.week != null ? "%" : ""}</b><span>${tr("помню при повторении")}</span></div>
      </div>
      <p class="note mt">${tr("«В долгой памяти» — карточки с интервалом от нескольких дней.\n      Последняя цифра — доля верных ответов на повторениях за неделю (цель — {p}%).", { p: Math.round(s.settings.desired_retention * 100) })}</p>
    </div>

    <div class="card">
      <h2>${tr("Достижения · {a}/{b}", { a: ach.unlocked, b: ach.total })}</h2>
      <div class="ach-grid">
        ${ach.items.map(a => `
          <div class="ach ${a.unlocked ? "on " + a.tier : "off"}" title="${tr(a.desc)}">
            <div class="ach-ico">${Art.tile(a)}</div>
            <div class="ach-t">${tr(a.title)}</div>
          </div>`).join("")}
      </div>
    </div>
    <div class="card">
      <h2>${tr("Сколько я повторял · 14 дней")}</h2>
      ${hasActivity
        ? barChart(s.activity, "reviews", "date", "", d =>
            `${fmtDay(d.date)}: ${d.reviews}${d.accuracy != null ? ` · ${tr("точность {p}%", { p: d.accuracy })}` : ""}`)
        : `<p class="note">${tr("Пока нет данных — пройдите первую SRS-сессию.")}</p>`}
    </div>
    <div class="card">
      <h2>${tr("Что меня ждёт · 14 дней")}</h2>
      ${barChart(s.forecast, "count", "date", "fc", (d, i) =>
        `${i === 0 ? tr("сегодня") : fmtDay(d.date)}: ${d.count}`)}
      <p class="note">${tr("Сколько карточек придёт на повторение в каждый день —\n      если заниматься ежедневно, горка не вырастет.")}</p>
    </div>
    ${s.hardest.length ? `
    <div class="card">
      <h2>${tr("Трудные знаки")}</h2>
      <div class="hardest-list">
        ${s.hardest.map(h => `<span class="chip ${h.is_leech ? "leech" : ""}">${h.char}<small>${h.romaji} · ${h.lapses}</small></span>`).join("")}
      </div>
      <p class="note mt">${tr("Цифра — сколько раз знак забывался. Обведённые — «пиявки»:\n      им в сессии показывается мнемоника.")}</p>
    </div>` : ""}
    <div class="card">
      <h2>${tr("Лимиты SRS")}</h2>
      <div class="srs-limits">
        <label>${tr("Новых карточек в день")}
          <select id="srs-new">${optionList([0, 4, 8, 12, 16, 20, 25, 30], s.settings.new_per_day, v => v)}</select>
        </label>
        <label>${tr("Повторений в день (макс.)")}
          <select id="srs-rev">${optionList([50, 100, 150, 250, 400, 600], s.settings.reviews_per_day, v => v)}</select>
        </label>
        <label>${tr("Целевое удержание")}
          <select id="srs-ret">${optionList([0.85, 0.9, 0.92, 0.95], s.settings.desired_retention, v => Math.round(v * 100) + "%")}</select>
        </label>
      </div>
      <p class="note mt">${tr("Выше удержание — крепче помните, но больше повторений в день.\n      Меньше новых — спокойнее темп. Применяется со следующей сессии.")}</p>
      <p class="note" id="srs-saved" style="display:none">${tr("Сохранено ✓")}</p>
    </div>
    <div class="card">
      <h2>${tr("Резервная копия")}</h2>
      <p class="note" style="margin-top:0">${tr("Весь прогресс — карточки, журнал ответов,\n      пройденные уроки и настройки — хранится локально в одном файле. Скачайте копию,\n      чтобы перенести его на другой компьютер или вернуть после переустановки.")}</p>
      <div class="data-actions">
        <button class="ghost" id="data-export">${tr("Скачать копию")}</button>
        <button class="ghost" id="data-import">${tr("Восстановить из копии…")}</button>
      </div>
      <input type="file" id="data-file" accept=".db,application/octet-stream" hidden>
      <p class="note" id="data-msg" style="display:none"></p>
      <div class="danger-zone">
        <button class="danger-link" id="data-delete">${tr("Удалить мои данные")}</button>
        <p class="note" style="margin-top:6px">${tr("Сотрёт весь прогресс с сервера и начнёт чистую сессию. Необратимо — сначала скачайте копию, если хотите сохранить.")}</p>
      </div>
    </div>
    </div>`;
  // Лимиты SRS — серверные настройки: меняем по месту, сохраняем сразу
  const srsHint = (msg, ok) => {
    const h = $("#srs-saved");
    h.textContent = msg;
    h.classList.toggle("err", !ok);
    h.style.display = "block";
    clearTimeout(srsHint._t);
    if (ok) srsHint._t = setTimeout(() => { h.style.display = "none"; }, 1600);
  };
  const saveSrs = async patch => {
    try { await api.post("/api/settings", patch); srsHint(tr("Сохранено ✓"), true); }
    catch (e) { srsHint(tr("Не удалось сохранить: {e}", { e: e.message }), false); }
  };
  $("#srs-new").addEventListener("change", e => saveSrs({ new_per_day: +e.target.value }));
  $("#srs-rev").addEventListener("change", e => saveSrs({ reviews_per_day: +e.target.value }));
  $("#srs-ret").addEventListener("change", e => saveSrs({ desired_retention: +e.target.value }));

  // Резервная копия: скачать снимок / восстановить из файла (перезапись прогресса!)
  $("#data-export").addEventListener("click", () => { location.href = "/api/export"; });
  const dataFile = $("#data-file");
  $("#data-import").addEventListener("click", () => dataFile.click());
  dataFile.addEventListener("change", async () => {
    const file = dataFile.files[0];
    dataFile.value = "";                       // позволить повторный выбор того же файла
    if (!file) return;
    const ok = await confirmDialog(
      tr("Восстановление заменит весь текущий прогресс данными из копии. " +
      "Перед заменой рядом сохраняется страховочный michi.db.bak. Продолжить?"),
      tr("Восстановить"));
    if (!ok) return;
    const msg = $("#data-msg");
    msg.classList.remove("err");
    msg.style.display = "block";
    msg.textContent = tr("Восстановление…");
    try {
      const res = await fetch("/api/import", { method: "POST", body: file });
      if (!res.ok) throw await apiError(res);
      const r = await res.json();
      msg.textContent = tr("Готово: {c} карточек, {r} ответов. Перезагрузка…", { c: r.cards, r: r.reviews });
      setTimeout(() => location.reload(), 1000);
    } catch (e) {
      msg.classList.add("err");
      msg.textContent = tr("Не удалось восстановить: {e}", { e: e.message });
    }
  });

  // Удаление своих данных: двойное подтверждение → стереть на сервере → чистый старт
  $("#data-delete").addEventListener("click", async () => {
    const ok = await confirmDialog(
      tr("Удалить весь ваш прогресс с сервера? Карточки, ответы, уроки и настройки " +
      "будут стёрты безвозвратно — это нельзя отменить."),
      tr("Удалить"));
    if (!ok) return;
    const msg = $("#data-msg");
    msg.classList.remove("err");
    msg.style.display = "block";
    msg.textContent = tr("Удаление…");
    try {
      await api.post("/api/account/delete", {});
      try { localStorage.clear(); } catch { /* приватный режим — не критично */ }
      location.reload();                       // чистая сессия: новый uid, онбординг
    } catch (e) {
      msg.classList.add("err");
      msg.textContent = tr("Не удалось удалить: {e}", { e: e.message });
    }
  });

  // Поздравляем с новыми достижениями оверлеем (общий путь — checkAchievements)
  checkAchievements(true, ach);
}

/* ---------- Онбординг первого запуска ---------- */
// Показывается один раз (флаг michi_onboarded): приветствие, выбор языка
// интерфейса и дневной цели, краткая карта курса. Рендерится на JS (все строки
// через tr(), так что EN/RU работают без перезагрузки), оверлеем поверх дашборда.
const Onboarding = {
  box: null,
  step: 0,
  goal: +(localStorage.getItem("michi_daily_goal") || 20),

  maybeShow() {
    if (localStorage.getItem("michi_onboarded")) return;
    this.box = $("#onboarding");
    if (!this.box) return;
    this.step = 0;
    this.render();
    this.box.classList.add("open");
  },

  render() {
    const steps = [this.stepWelcome, this.stepGoal, this.stepStart];
    this.box.innerHTML = `
      <div class="ob-card">
        <button class="ob-skip" id="ob-skip">${tr("Пропустить")}</button>
        <div class="ob-step">${steps[this.step].call(this)}</div>
        <div class="ob-dots">${[0, 1, 2].map(i =>
          `<span class="ob-dot ${i === this.step ? "on" : ""}"></span>`).join("")}</div>
        <div class="ob-nav">
          ${this.step > 0 ? `<button class="ghost" id="ob-back">${tr("Назад")}</button>` : ""}
          ${this.step < 2 ? `<button class="primary" id="ob-next">${tr("Далее")}</button>` : ""}
        </div>
      </div>`;
    this.wire();
  },

  wire() {
    const b = this.box;
    b.querySelector("#ob-skip").onclick = () => this.finish();
    const next = b.querySelector("#ob-next");
    if (next) next.onclick = () => { this.step++; this.render(); };
    const back = b.querySelector("#ob-back");
    if (back) back.onclick = () => { this.step--; this.render(); };
    b.querySelectorAll(".ob-lang").forEach(el => (el.onclick = () => {
      setLang(el.dataset.lang);
      Prefs.push("michi_lang");
      applyI18n();            // перевести статику (навигацию/настройки) под низом
      this.render();
    }));
    b.querySelectorAll(".ob-goal").forEach(el => (el.onclick = () => {
      this.goal = +el.dataset.goal;
      localStorage.setItem("michi_daily_goal", this.goal);
      Prefs.push("michi_daily_goal");
      this.render();
    }));
    const hear = b.querySelector("#ob-hear");
    if (hear) hear.onclick = () => speak("こんにちは。ミチへようこそ。");
    const start = b.querySelector("#ob-start");
    if (start) start.onclick = () => this.startFirst();
    const look = b.querySelector("#ob-look");
    if (look) look.onclick = () => { this.finish(); show("today"); };
  },

  stepWelcome() {
    return `
      <div class="ob-mascot">${Art.mascotTile("cheer")}</div>
      <div class="ob-kicker">${tr("Добро пожаловать")}</div>
      <h2 class="ob-title">MICHI（道）</h2>
      <p class="ob-sub">${tr("Японский с нуля — и в удовольствие")}</p>
      <p class="ob-body">${tr("Кана, слова, кандзи и грамматика N5 — маленькими уроками. Умное повторение само напомнит, что пора освежить выученное.")}</p>
      <div class="ob-field">
        <span class="ob-label">${tr("Язык интерфейса")}</span>
        <div class="ob-langs">
          ${Object.entries(LANGS).map(([code, name]) =>
            `<button class="ob-lang ${code === LANG ? "active" : ""}" data-lang="${code}">${name}</button>`).join("")}
        </div>
      </div>`;
  },

  stepGoal() {
    const opts = [[10, "Лёгкая"], [20, "Обычная"], [40, "Серьёзная"]];
    return `
      <h2 class="ob-title sm">${tr("Выберите дневную цель")}</h2>
      <p class="ob-body">${tr("Дневная цель в XP — личный ориентир на день. Серию 🔥 держит любое занятие. Повторение +2 XP, урок +20 XP. Поменять можно в ⚙ в любой момент.")}</p>
      <div class="ob-goals">
        ${opts.map(([xp, label]) =>
          `<button class="ob-goal ${xp === this.goal ? "sel" : ""}" data-goal="${xp}">
             <b>${xp}</b><span>XP</span><em>${tr(label)}</em></button>`).join("")}
      </div>
      <button class="ghost ob-hear" id="ob-hear">${Icons.ui("speaker")} ${tr("Послушать голос")}</button>`;
  },

  stepStart() {
    const chips = ["ひらがな", "カタカナ", "単語", "漢字", "文法"];
    return `
      <div class="ob-mascot sm">${Art.mascotTile("cheer")}</div>
      <h2 class="ob-title sm">${tr("С чего начнём")}</h2>
      <p class="ob-body">${tr("Старт — хирагана, японская азбука. Дальше курсы открываются сами: катакана параллельно, слова N5 после хираганы, затем кандзи и грамматика.")}</p>
      <div class="ob-path">${chips.map((c, i) =>
        `<span class="ob-chip">${c}</span>` +
        (i < chips.length - 1 ? `<span class="ob-arrow">→</span>` : "")).join("")}</div>
      <div class="ob-final">
        <button class="primary" id="ob-start">${tr("Начать первый урок")}</button>
        <button class="ghost" id="ob-look">${tr("Осмотреться самому")}</button>
      </div>`;
  },

  finish() {
    localStorage.setItem("michi_onboarded", "1");
    Prefs.push("michi_onboarded");
    this.box.classList.remove("open");
    this.box.innerHTML = "";
  },

  async startFirst() {
    this.finish();
    show("today");            // обновить дашборд (вдруг сменили язык) под плеером
    if (LANG === "en") await loadEnContent();   // EN-контент урока до его рендера
    try {
      const lessons = await api.get("/api/lessons");
      const first = lessons.find(l => l.status === "available");
      if (first) startLesson(first.id);
    } catch { /* нет сети — просто останемся на дашборде */ }
  },
};

/* Последняя линия защиты: непойманное отклонение промиса (необёрнутый await в
   обработчике, фоновая операция) не должно тихо проваливаться — мягко уведомляем.
   ABORT-выходы из сессии резолвятся, а не реджектятся, поэтому сюда не попадают. */
addEventListener("unhandledrejection", e => {
  console.error("unhandledrejection:", e.reason);
  toast(tr("Что-то пошло не так. Попробуйте ещё раз."), true);
});

/* ---------- Старт ---------- */
function boot() {
  applyI18n();              // перевод статической разметки (навигация, настройки)
  checkAchievements(false); // тихо засеять базу «увиденных» — без салюта на старте
  show("today");
  Onboarding.maybeShow();   // первый запуск — приветствие, выбор языка и цели
  Prefs.sync();             // подтянуть UI-настройки из БД (после импорта/нов. устройства)
}
// В английском дожидаемся EN-оверлея контента до первого рендера (иначе мелькнул
// бы русский); русскому большинству оверлей не грузится вовсе.
if (LANG === "en") loadEnContent().then(boot); else boot();

/* PWA: офлайн-оболочка через Service Worker (мягко — без него всё работает) */
if ("serviceWorker" in navigator) {
  addEventListener("load", () =>
    navigator.serviceWorker.register("/sw.js").catch(() => {}));
}
