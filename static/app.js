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

const api = {
  async get(url) {
    const r = await fetch(url);
    if (!r.ok) throw await apiError(r);
    return r.json();
  },
  async post(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    if (!r.ok) throw await apiError(r);
    return r.json();
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
  },
};
if ("speechSynthesis" in window) {
  speechSynthesis.onvoiceschanged = () => TTS.refreshBrowser();
}
TTS.init();

const speak = text => TTS.speak(text);
function ttsButton(text) {
  if (!TTS.available) return "";
  return `<button class="tts-btn" data-tts="${text}">🔊 послушать</button>`;
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
    tapSound: "drop_003",
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
      this.play(this.prefs.tapSound, 0.4);
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

function fillVoiceSelect() {
  const sel = $("#set-voice");
  const warn = $("#tts-warn");
  const vvHint = $("#vv-hint");
  warn.style.display = "none";
  vvHint.style.display = "none";
  if ($("#set-source").value === "neural") {
    if (!TTS.neuralVoices.length) {
      warn.textContent = "Нейроголос недоступен (нужен интернет). Используйте голос браузера.";
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
      warn.textContent = "В браузере нет японских голосов. Установите: Параметры Windows → Время и язык → Речь → Добавить голоса → «Японский».";
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
  $("#set-tap-sound").disabled = !Haptics.prefs.enabled;
  settingsModal.classList.add("open");
}

function fillTapSounds() {
  $("#set-tap-sound").innerHTML =
    Object.entries(Haptics.TAPS).map(([k, v]) =>
      `<option value="${k}" ${k === Haptics.prefs.tapSound ? "selected" : ""}>${v}</option>`).join("") +
    `<option value="off" ${Haptics.prefs.tapSound === "off" ? "selected" : ""}>Без звука</option>`;
}
$("#btn-settings").addEventListener("click", openSettings);
$("#set-close").addEventListener("click", () => settingsModal.classList.remove("open"));
settingsModal.addEventListener("click", e => {
  if (e.target === settingsModal) settingsModal.classList.remove("open");
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
  icons: { light: "☀", dark: "☾", auto: "◐" },
  isDark() {
    return this.pref === "dark" || (this.pref === "auto" && this.media.matches);
  },
  apply() {
    document.documentElement.dataset.theme = this.isDark() ? "dark" : "light";
    const btn = $("#btn-theme");
    btn.textContent = this.icons[this.pref];
    btn.title = `Тема: ${this.labels[this.pref]} (нажмите, чтобы сменить)`;
  },
  toggle() {
    // светлая -> тёмная -> авто -> ... (авто не теряется навсегда)
    const order = ["light", "dark", "auto"];
    this.pref = order[(order.indexOf(this.pref) + 1) % order.length];
    localStorage.setItem("michi_theme", this.pref);
    this.apply();
  },
};
Theme.media.addEventListener("change", () => {
  if (Theme.pref === "auto") Theme.apply();
});
$("#btn-theme").addEventListener("click", () => Theme.toggle());
Theme.apply();

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

/* ---------- Анимация появления экранов ---------- */
function animateIn(el) {
  el.classList.remove("anim-in");
  void el.offsetWidth; // перезапуск CSS-анимации
  el.classList.add("anim-in");
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

/* Enter/Space продолжают сессию, когда на экране есть кнопка «Дальше» */
document.addEventListener("keydown", e => {
  if (e.key !== "Enter" && e.key !== " ") return;
  if (!$("#player").classList.contains("open")) return;
  const btn = $("#player-body").querySelector("#next, #finish, #check");
  if (btn) { e.preventDefault(); btn.click(); }
});

/* ---------- Роутер вкладок ---------- */
const view = $("#view");
const renderers = { today: renderToday, lessons: renderLessons, review: renderReviewTab, stats: renderStats };

function show(name) {
  document.querySelectorAll("nav.tabs button").forEach(b =>
    b.classList.toggle("active", b.dataset.view === name));
  Promise.resolve(renderers[name]()).then(() => animateIn(view));
}
document.querySelectorAll("nav.tabs button").forEach(b =>
  b.addEventListener("click", () => show(b.dataset.view)));

function setStreakPill(streak) {
  const pill = $("#streak-pill");
  // Единственное место для серии — пилюля в шапке (видна на всех вкладках)
  pill.textContent = `🔥 ${streak} ${plural(streak, ["день", "дня", "дней"])}`;
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
  view.innerHTML = `<div class="empty">Загрузка…</div>`;
  const o = await api.get("/api/overview");
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
    ? `<p class="note">Хирагана пройдена — ромадзи скрыт, чтобы вы читали каной.
       Вернуть можно в ⚙ настройках.</p>`
    : "";
  if (romajiNote) localStorage.setItem("michi_romaji_note", "1");

  view.innerHTML = `
    <div class="hero">
      <div class="hero-top">
        <div>
          <div class="hero-jp jp" data-tts="${jp}">${jp}！</div>
          <div class="hero-ru">${ru}</div>
        </div>
      </div>
      <div class="hero-stats">
        <div class="hs"><b>${o.today.reviews}</b><span>повторено сегодня</span></div>
        <div class="hs"><b>${o.today.accuracy !== null ? o.today.accuracy + "%" : "—"}</b><span>точность сегодня</span></div>
      </div>
    </div>

    <div class="card gami">
      <div class="level-badge">
        <div class="lvl-num">${o.xp.level}</div>
        <div class="lvl-meta">
          <div class="lvl-title">Уровень ${o.xp.level}</div>
          <div class="lvl-bar"><div style="width:${o.xp.percent}%"></div></div>
          <div class="lvl-xp">${o.xp.into_level} / ${o.xp.level_span} XP · всего ${o.xp.total}</div>
        </div>
      </div>
      <div class="goal-ring ${goalMet ? "met" : ""}" style="--p:${goalPct}">
        <div class="goal-inner">
          <b>${goalMet ? "✓" : todayXp}</b>
          <span>${goalMet ? "цель!" : "/ " + goal + " XP"}</span>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>План на сегодня</h2>
      <div class="plan-item ${queueTotal ? "" : "done"}">
        <div class="pi-ico jp c3">復</div>
        <div class="pi-info">
          <div class="t">Повторение</div>
          <div class="s">${queueTotal
            ? `${o.srs.due ? `по расписанию: ${o.srs.due}` : ""}${o.srs.due && o.srs.new_available ? " · " : ""}${o.srs.new_available ? `новых: ${o.srs.new_available}` : ""} · ≈${estMin} мин`
            : "Очередь пуста — всё повторено"}</div>
        </div>
        ${queueTotal
          ? `<button class="mini-btn" id="btn-review">Начать</button>`
          : `<span class="pi-done">✓</span>`}
      </div>
      <div class="plan-item ${next ? "" : "done"}">
        <div class="pi-ico jp c0">道</div>
        <div class="pi-info">
          <div class="t">Новый урок</div>
          <div class="s">${next ? `${next.title} · ${next.subtitle}` : "Все доступные уроки пройдены"}</div>
        </div>
        ${next
          ? `<button class="mini-btn indigo" id="btn-lesson">Учить</button>`
          : `<span class="pi-done">✓</span>`}
      </div>
    </div>

    <div class="card">
      <h2>Прогресс курсов</h2>
      ${o.courses.map(c => `
      <div class="course-row">
        <span class="cr-title">${c.title}</span>
        <div class="progress"><div style="width:${Math.round(c.lessons_completed / c.lessons_total * 100)}%"></div></div>
        <span class="cr-num">${c.lessons_completed}/${c.lessons_total}</span>
      </div>`).join("")}
      <p class="note">Катакану можно учить параллельно с хираганой, слова N5 откроются после хираганы.</p>
    </div>
    ${romajiNote}`;
  // Цель дня достигнута впервые сегодня — поздравляем (раз в день)
  const todayKey = new Date().toISOString().slice(0, 10);
  if (goalMet && localStorage.getItem("michi_goal_day") !== todayKey) {
    localStorage.setItem("michi_goal_day", todayKey);
    confetti();
  }
  $("#btn-review")?.addEventListener("click", startReview);
  $("#btn-lesson")?.addEventListener("click", () => startLesson(next.id));
}

/* ---------- Путь: регионы и сетка уроков ---------- */
const COURSE_OF = { l: "hiragana", k: "katakana", v: "n5", j: "kanji", g: "grammar" };
const COURSE_LABEL = { all: "Все", hiragana: "Хирагана", katakana: "Катакана", n5: "Первые слова", kanji: "Кандзи", grammar: "Грамматика" };
let lessonFilter = localStorage.getItem("michi_lesson_filter") || "all";

async function renderLessons() {
  view.innerHTML = `<div class="empty">Загрузка…</div>`;
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
      `<button class="course-tab ${f === lessonFilter ? "active" : ""}" data-f="${f}">${COURSE_LABEL[f] || f}</button>`
    ).join("")}</div>`;

    view.innerHTML = tabs + groups.map(g => {
      const doneCount = g.lessons.filter(l => l.status === "completed").length;
      return `
      <div class="region-h">
        <span class="t">${g.title}</span>
        <span class="jp">${g.jp}</span>
        <span class="spacer"></span>
        <span class="region-progress ${doneCount === g.lessons.length ? "done" : ""}">
          ${doneCount === g.lessons.length ? "✓ " : ""}${doneCount} из ${g.lessons.length}</span>
      </div>
      <div class="lesson-grid">
        ${g.lessons.map(l => `
          <div class="lesson-card ${l.status} ${l.type === "gate_test" ? "gate" : ""}" data-id="${l.id}" data-status="${l.status}">
            <div class="circle jp c${lessons.indexOf(l) % 6}">${l.icon}</div>
            ${l.status === "completed"
              ? `<span class="state done">✓ ${l.score != null ? Math.round(l.score * 100) + "%" : ""}</span>`
              : l.status === "locked" ? `<span class="state lock">🔒</span>` : ""}
            <h3>${l.title}</h3>
            <div class="tag">${l.subtitle}${l.kana_count ? ` · ${l.kana_count} знаков` : ""}${l.locked_hint ? `<br>${l.locked_hint}` : ""}</div>
          </div>`).join("")}
      </div>`;
    }).join("");

    view.querySelectorAll(".course-tab").forEach(b =>
      b.addEventListener("click", () => {
        lessonFilter = b.dataset.f;
        localStorage.setItem("michi_lesson_filter", lessonFilter);
        paint();
        animateIn(view);
      }));
    view.querySelectorAll(".lesson-card").forEach(el =>
      el.addEventListener("click", () => {
        if (el.dataset.status !== "locked") startLesson(el.dataset.id);
      }));
  };

  paint();
}

/* ---------- Стилизованный диалог подтверждения (вместо confirm()) ---------- */
function confirmDialog(text, yesLabel = "Выйти") {
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

/* ---------- Плеер (общий для уроков и SRS) ---------- */
const player = $("#player");
const playerBody = $("#player-body");
let sessionToken = 0;
let playerMode = "lesson"; // lesson | review — для текста диалога выхода
// Снятие document-обработчиков текущего упражнения: без этого выход из
// сессии посреди вопроса оставляет слушатель клавиш 1–4 навсегда, и позднее
// нажатие цифры «отвечает» на брошенную карточку (фантомная озвучка + POST)
let exerciseCleanup = null;

function openPlayer(mode) {
  sessionToken++;
  playerMode = mode;
  player.classList.add("open");
  setProgress(0);
  $("#player-counter").textContent = "";
  return sessionToken;
}
function closePlayer() {
  sessionToken++;
  if (exerciseCleanup) exerciseCleanup();
  player.classList.remove("open");
  show("today");
}
async function askClosePlayer() {
  const msg = playerMode === "review"
    ? "Прервать повторение? Все ответы уже сохранены."
    : "Выйти из урока? Потом продолжите с этого же места.";
  if (await confirmDialog(msg)) closePlayer();
}
$("#player-close").addEventListener("click", askClosePlayer);
document.addEventListener("keydown", e => {
  if (e.key !== "Escape") return;
  if ($("#confirm").classList.contains("open")) return; // закроет свой onclick
  if (settingsModal.classList.contains("open")) settingsModal.classList.remove("open");
  else if (player.classList.contains("open")) askClosePlayer();
});
function setProgress(frac) {
  $("#player-progress").style.width = `${Math.round(frac * 100)}%`;
}
document.addEventListener("click", e => {
  const t = e.target.closest("[data-tts]");
  if (t) speak(t.dataset.tts);
});

function waitClick(el) {
  return new Promise(res => el.addEventListener("click", res, { once: true }));
}

/* Выбор варианта мышью или клавишами 1–N; обработчик клавиш снимается и при
   ответе, и при закрытии сессии (exerciseCleanup) */
function awaitChoice(buttons) {
  return new Promise(res => {
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
      <h2 class="intro-title">${step.title}</h2>
      ${step.subtitle ? `<div class="intro-sub">${step.subtitle}</div>` : ""}
      <p class="intro-text">${step.text}</p>
    </div>
    <div class="spacer"></div>
    <button class="primary" id="next">Начать</button>`;
  animateIn(playerBody);
  await waitClick($("#next", playerBody));
}

async function showIntroKana(step) {
  const lookalikes = (step.lookalikes || []).map(l =>
    `<span class="jp">${l.char}<small>${l.romaji}</small></span>`).join("");
  // Со штрихами — живая анимация порядка черт (2.1), иначе крупный знак
  const glyph = step.strokes
    ? `<div class="kana-anim" id="kana-anim" data-tts="${step.char}" title="Анимация порядка черт"></div>`
    : `<div class="big-kana ${step.char.length > 1 ? "small" : ""}" data-tts="${step.char}">${step.char}</div>`;
  playerBody.innerHTML = `
    ${glyph}
    <div class="romaji-big">${step.romaji}</div>
    ${ttsButton(step.tts)}
    ${step.derivation ? `<div class="derivation">${step.derivation}</div>` : ""}
    ${step.mnemonic ? `<div class="mnemonic">${step.mnemonic}</div>` : ""}
    ${step.note ? `<p class="note">${step.note}</p>` : ""}
    ${lookalikes ? `<p class="note center">не путайте с</p><div class="lookalikes">${lookalikes}</div>` : ""}
    <div class="spacer"></div>
    <button class="primary" id="next">Запомнил</button>`;
  if (step.strokes) Tracing.preview($("#kana-anim", playerBody), step.strokes, 176);
  animateIn(playerBody);
  speak(step.tts);
  await waitClick($("#next", playerBody));
}

async function showIntroWord(step) {
  playerBody.innerHTML = `
    <div class="big-kana small" data-tts="${step.tts}">${step.kana}</div>
    <div class="romaji-big">${step.romaji}</div>
    <div class="word-ru">${step.ru}</div>
    ${ttsButton(step.tts)}
    ${step.note ? `<p class="note center">${step.note}</p>` : ""}
    <div class="spacer"></div>
    <button class="primary" id="next">Запомнил</button>`;
  animateIn(playerBody);
  speak(step.tts);
  await waitClick($("#next", playerBody));
}

/* Знакомство с кандзи (6.2): порядок черт, значение, чтения он/кун, примеры */
async function showIntroKanji(step) {
  const glyph = step.strokes
    ? `<div class="kana-anim" id="kana-anim" data-tts="${step.tts}" title="Анимация порядка черт"></div>`
    : `<div class="big-kana" data-tts="${step.tts}">${step.char}</div>`;
  const on = (step.on || []).join("、");
  const kun = (step.kun || []).join("、");
  // Цветовое кодирование чтений (6.4): онъёми и кунъёми разными цветами
  const readings = `
    ${on ? `<span class="rd on"><small>он</small>${on}</span>` : ""}
    ${kun ? `<span class="rd kun"><small>кун</small>${kun}</span>` : ""}`;
  const examples = (step.examples || []).map(e =>
    `<button class="kanji-ex" data-tts="${e.r}">
       <span class="ex-w jp">${e.w}</span>
       <span class="ex-r jp">${e.r}</span>
       <span class="ex-ru">${e.ru}</span></button>`).join("");
  // Разбор на изученные компоненты (6.3): 木 + 木 = 林
  const parts = (step.components || []).map(c =>
    `<span class="part jp" data-tts="${c.char}">${c.char}<small>${c.meaning || ""}</small></span>`
  ).join(`<i class="op">+</i>`);
  const components = parts
    ? `<div class="kanji-parts">${parts}<i class="op">=</i><span class="part whole jp">${step.char}</span></div>`
    : "";
  playerBody.innerHTML = `
    ${glyph}
    <div class="kanji-meaning">${step.meaning}</div>
    <div class="kanji-readings">${readings}</div>
    ${components}
    ${ttsButton(step.tts)}
    ${step.mnemonic ? `<div class="mnemonic">${step.mnemonic}</div>` : ""}
    ${examples ? `<div class="kanji-examples">${examples}</div>` : ""}
    <div class="spacer"></div>
    <button class="primary" id="next">Запомнил</button>`;
  if (step.strokes) Tracing.preview($("#kana-anim", playerBody), step.strokes, 176);
  animateIn(playerBody);
  speak(step.tts);
  await waitClick($("#next", playerBody));
}

async function showIntroGrammar(step) {
  const reg = { neutral: "нейтр.", polite: "вежл.", casual: "разг.", formal: "формальн." };
  const explanation = (step.explanation || []).map(b =>
    `<p class="g-block">${b}</p>`).join("");
  const examples = (step.examples || []).map(e =>
    `<button class="kanji-ex" data-tts="${e.tts}">
       <span class="ex-w jp">${e.jp}</span>
       <span class="ex-ru">${e.ru}</span></button>`).join("");
  playerBody.innerHTML = `
    <div class="big-kana jp" data-tts="${step.tts || step.title}">${step.title}</div>
    <div class="grammar-structure jp">${step.structure}</div>
    <div class="kanji-meaning">${step.meaning}${step.register
      ? ` <span class="g-register">${reg[step.register] || step.register}</span>` : ""}</div>
    ${explanation}
    ${step.caution ? `<div class="mnemonic">⚠ ${step.caution}</div>` : ""}
    ${examples ? `<div class="kanji-examples">${examples}</div>` : ""}
    <div class="spacer"></div>
    <button class="primary" id="next">Понятно</button>`;
  animateIn(playerBody);
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
    <p class="question">${ex.question}</p>
    <div class="cloze-list">${ex.rows.map(rowHtml).join("")}</div>
    <div class="cloze-bank">${ex.bank.map(t =>
      `<button class="bank-tile" data-t="${t}">${t}</button>`).join("")}</div>
    <div class="feedback" id="fb"></div>
    <div class="spacer"></div>
    <button class="primary" id="check" disabled>Проверить</button>`;
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

  await waitClick(checkBtn);
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
  fb.innerHTML = verdict(allRight, allRight ? "Все пропуски верны!" : `Верно ${ok} из ${ex.rows.length}`);
  if (afterAnswer) fb.innerHTML += `<div class="srs-toast">${await afterAnswer(allRight, durationMs, false)}</div>`;

  checkBtn.remove();
  if (allRight) {
    await new Promise(r => setTimeout(r, 1100));
  } else {
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">Дальше</button>`);
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
    <p class="question">${ex.question}</p>
    <div class="match-board">
      <div class="match-col">${shuffle(ex.pairs).map(p => tile(p, p.jp, "jp")).join("")}</div>
      <div class="match-col">${shuffle(ex.pairs).map(p => tile(p, p.ru, "")).join("")}</div>
    </div>
    <div class="feedback" id="fb"></div>
    <div class="spacer"></div>`;
  animateIn(playerBody);

  const total = ex.pairs.length;
  const ttsOf = id => (ex.pairs.find(p => p.id === id) || {}).tts;
  let matched = 0, mistakes = 0, sel = null, busy = false;
  const t0 = performance.now();

  await new Promise(resolve => {
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
            mistakes === 0 ? "Все пары верны!" : "Доска собрана");
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
  let question = ex.question;
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
    ? `<button class="audio-prompt" data-tts="${ex.prompt.tts}" title="Прослушать ещё раз">🔊</button>`
    : `<div class="prompt-text ${jpClass}" ${ex.prompt.tts ? `data-tts="${ex.prompt.tts}"` : ""}>${ex.prompt.text}</div>` +
      (!jpish && ex.prompt.tts ? ttsButton(ex.prompt.tts) : "");
  playerBody.innerHTML = `
    <p class="question">${question}</p>
    ${promptHtml}
    <div class="options">
      ${ex.options.map((o, i) =>
        `<button data-i="${i}" class="${ex.options_are_kana ? "jp" : ""}"><span class="kbd">${i + 1}</span>${o}</button>`).join("")}
    </div>
    <div class="feedback" id="fb"></div>
    <div class="spacer"></div>`;
  animateIn(playerBody);
  if (speakOnStart) speak(ex.prompt.tts);

  const buttons = [...playerBody.querySelectorAll(".options button")];
  const t0 = performance.now();
  const choice = await awaitChoice(buttons);
  const durationMs = Math.round(performance.now() - t0);
  const correct = choice === ex.answer;
  buttons.forEach(b => (b.disabled = true));
  buttons[ex.answer].classList.add("correct");
  if (!correct) buttons[choice].classList.add("wrong");

  const fb = $("#fb", playerBody);
  fb.className = `feedback ${correct ? "ok" : "bad"}`;
  Haptics[correct ? "good" : "bad"]();
  fb.innerHTML = verdict(correct, correct ? "Верно" :
    `Правильно: <span class="jp">${ex.options[ex.answer]}</span>`);
  speak(ex.prompt.tts || ex.answer_tts);

  if (afterAnswer) fb.innerHTML += `<div class="srs-toast">${await afterAnswer(correct, durationMs, false)}</div>`;

  if (correct) {
    await new Promise(r => setTimeout(r, 900));
  } else {
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">Дальше</button>`);
    await waitClick($("#next", playerBody));
  }
  return { correct, durationMs, usedHint: false };
}

async function runWordBuild(ex, afterAnswer) {
  // speak_after: озвучка слова до ответа выдала бы его (тип vocab_build)
  const quiet = !!ex.speak_after;
  playerBody.innerHTML = `
    <p class="question">${ex.question}</p>
    <div class="prompt-text">${ex.prompt.text}</div>
    ${quiet ? "" : ttsButton(ex.prompt.tts)}
    <div class="build-slots" id="slots"></div>
    <div class="tiles" id="tiles">
      ${ex.tiles.map((t, i) => `<button data-i="${i}">${t}</button>`).join("")}
    </div>
    <div class="feedback" id="fb"></div>
    <div class="spacer"></div>
    <button class="primary" id="check" disabled>Проверить</button>`;
  animateIn(playerBody);
  if (!quiet) speak(ex.prompt.tts);

  const slots = $("#slots", playerBody);
  const checkBtn = $("#check", playerBody);
  const assembled = [];
  const t0 = performance.now();

  const renderSlots = () => {
    slots.innerHTML = assembled.map((a, i) =>
      `<span data-pos="${i}" title="Убрать">${a.tile}</span>`).join("");
    // Проверяем только по кнопке: автосабмит не давал исправить последнюю плитку
    checkBtn.disabled = assembled.length !== ex.answer_tokens.length;
  };

  const finished = new Promise(res => {
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
  await finished;

  const durationMs = Math.round(performance.now() - t0);
  const word = assembled.map(a => a.tile).join("");
  const correct = word === ex.answer_tokens.join("");

  const fb = $("#fb", playerBody);
  fb.className = `feedback ${correct ? "ok" : "bad"}`;
  Haptics[correct ? "good" : "bad"]();
  fb.innerHTML = verdict(correct, correct
    ? `<span class="jp">${word}</span>`
    : `Правильно: <span class="jp">${ex.answer_tokens.join("")}</span>`);
  speak(ex.prompt.tts);
  if (afterAnswer) fb.innerHTML += `<div class="srs-toast">${await afterAnswer(correct, durationMs, false)}</div>`;

  if (correct) {
    await new Promise(r => setTimeout(r, 1100));
  } else {
    $("#check", playerBody).remove();
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">Дальше</button>`);
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
    ? `<button class="audio-prompt" data-tts="${ex.prompt.tts}" title="Прослушать ещё раз">🔊</button>`
    : `<div class="prompt-text">${isAudio ? ex.prompt.fallback_text : ex.prompt.text}</div>`;
  const question = (isAudio && !audioMode) ? "Введите слово по-японски" : ex.question;
  playerBody.innerHTML = `
    <p class="question">${question}</p>
    ${top}
    <input class="text-answer" id="ans" type="text" inputmode="text"
      autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false"
      placeholder="каной или ромадзи">
    <div class="feedback" id="fb"></div>
    <div class="spacer"></div>
    <button class="primary" id="check" disabled>Проверить</button>`;
  animateIn(playerBody);
  if (audioMode) speak(ex.prompt.tts);

  const input = $("#ans", playerBody);
  const checkBtn = $("#check", playerBody);
  input.focus();
  input.addEventListener("input", () => { checkBtn.disabled = !input.value.trim(); });
  const t0 = performance.now();
  await new Promise(res => {
    const submit = () => { if (input.value.trim()) res(); };
    checkBtn.addEventListener("click", submit);
    input.addEventListener("keydown", e => { if (e.key === "Enter") submit(); });
  });

  const durationMs = Math.round(performance.now() - t0);
  const correct = ex.accept.includes(normInput(input.value));
  input.disabled = true;
  checkBtn.remove();

  const fb = $("#fb", playerBody);
  fb.className = `feedback ${correct ? "ok" : "bad"}`;
  Haptics[correct ? "good" : "bad"]();
  fb.innerHTML = verdict(correct, correct
    ? `<span class="jp">${ex.answer}</span>`
    : `Правильно: <span class="jp">${ex.answer}</span>`);
  speak(ex.answer_tts);
  if (afterAnswer) fb.innerHTML += `<div class="srs-toast">${await afterAnswer(correct, durationMs, false)}</div>`;

  if (correct) {
    await new Promise(r => setTimeout(r, 1100));
  } else {
    playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">Дальше</button>`);
    await waitClick($("#next", playerBody));
  }
  return { correct, durationMs, usedHint: false };
}

async function runTracing(ex, afterAnswer) {
  playerBody.innerHTML = `
    <p class="question">${ex.question}</p>
    <div class="prompt-text" ${ex.prompt.tts ? `data-tts="${ex.prompt.tts}"` : ""}>${ex.prompt.text}</div>
    ${ttsButton(ex.prompt.tts)}
    <div id="trace-host"></div>
    <div class="feedback" id="fb"></div>
    <div class="spacer"></div>`;
  animateIn(playerBody);
  speak(ex.prompt.tts);

  const t0 = performance.now();
  const result = await new Promise(res =>
    Tracing.create($("#trace-host", playerBody), {
      strokes: ex.strokes,
      mode: ex.mode,
      onComplete: res,
    }));
  const durationMs = Math.round(performance.now() - t0);
  // Трассировка прощает одну помарку, письмо по памяти — нет (6.7, режимы)
  const correct = ex.mode === "trace" ? result.errors <= 1 : result.errors === 0;

  const fb = $("#fb", playerBody);
  fb.className = `feedback ${correct ? "ok" : "bad"}`;
  Haptics[correct ? "good" : "bad"]();
  fb.innerHTML = verdict(correct, correct
    ? (result.errors === 0 ? "Написано чисто" : "Зачтено, была помарка")
    : `Помарок: ${result.errors} — посмотрите анимацию черт ещё раз`);
  if (afterAnswer) fb.innerHTML += `<div class="srs-toast">${await afterAnswer(correct, durationMs, result.usedHint)}</div>`;

  playerBody.insertAdjacentHTML("beforeend", `<button class="primary" id="next">Дальше</button>`);
  await waitClick($("#next", playerBody));
  return { correct, durationMs, usedHint: result.usedHint };
}

async function runTwins(ex, afterAnswer) {
  let errors = 0;
  const t0 = performance.now();
  for (let i = 0; i < ex.series.length; i++) {
    const round = ex.series[i];
    playerBody.innerHTML = `
      <p class="question">${ex.question}</p>
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
    `<div class="feedback ${correct ? "ok" : "bad"}">${correct ? "Серия без ошибок" : `Ошибок: ${errors} из ${ex.series.length}`}</div>`);
  await new Promise(r => setTimeout(r, 1000));
  return { correct, durationMs, usedHint: false };
}

/* ---------- Урок (с продолжением с места выхода) ---------- */
const RESUME_KEY = "michi_lesson_resume";

async function startLesson(lessonId) {
  let lesson, startIdx = 0, correct = 0, total = 0;
  // Если из этого урока выходили на середине — продолжаем с того же шага
  const saved = JSON.parse(localStorage.getItem(RESUME_KEY) || "null");
  if (saved && saved.lessonId === lessonId && Array.isArray(saved.steps)) {
    lesson = { title: saved.title, steps: saved.steps };
    startIdx = saved.i;
    correct = saved.correct;
    total = saved.total;
  } else {
    try {
      lesson = await api.get(`/api/lessons/${lessonId}`);
    } catch (e) {
      alert(e.message);
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
    }
    localStorage.setItem(RESUME_KEY, JSON.stringify({
      lessonId, title: lesson.title, steps, i: i + 1, correct, total,
    }));
  }
  if (token !== sessionToken) return;
  setProgress(1);
  localStorage.removeItem(RESUME_KEY);

  const score = total ? correct / total : 1;
  const done = await api.post(`/api/lessons/${lessonId}/complete`, { score });
  playerBody.classList.add("center-step");   // итог — по центру

  // Ворота юнита провалены: следующий юнит не открывается, предлагаем пересдать
  if (done.is_gate && !done.passed) {
    const need = Math.round((done.pass_mark || 0.8) * 100);
    playerBody.innerHTML = `
      <div class="result gate-fail">
        <div class="mark">⛩</div>
        <h2>Ворота не пройдены</h2>
        <p>Ваш результат ${Math.round(score * 100)}% · нужно ${need}%<br>
        Следующий юнит откроется после пересдачи.</p>
        <button class="primary" id="retry">Пересдать</button>
        <button class="ghost" id="finish">Выйти</button>
      </div>`;
    animateIn(playerBody);
    const choice = await Promise.race([
      waitClick($("#retry", playerBody)).then(() => "retry"),
      waitClick($("#finish", playerBody)).then(() => "finish"),
    ]);
    closePlayer();
    if (choice === "retry") startLesson(lessonId);
    return;
  }

  const isGate = done.is_gate;
  playerBody.innerHTML = `
    <div class="result">
      <div class="mark">${isGate ? "⛩" : "完"}</div>
      <h2>${isGate ? "Ворота пройдены!" : lesson.title + " — пройден"}</h2>
      <p>Точность ${Math.round(score * 100)}% · ${correct} из ${total}${
        isGate ? "" : "<br>" + (done.cards_created
          ? `В SRS добавлено карточек: ${done.cards_created}` : "Карточки уже в SRS")}</p>
      <button class="primary" id="finish">Дальше</button>
    </div>`;
  animateIn(playerBody);
  confetti();
  await waitClick($("#finish", playerBody));
  closePlayer();
}

/* ---------- SRS-сессия ---------- */
async function startReview() {
  const token = openPlayer("review");
  let done = 0, okCount = 0;

  while (token === sessionToken) {
    const data = await api.get("/api/srs/queue?limit=20");
    if (token !== sessionToken) return;
    if (!data.items.length) break;

    const remaining = data.counts.due + data.counts.new_available;
    for (let i = 0; i < data.items.length; i++) {
      if (token !== sessionToken) return;
      const item = data.items[i];
      setProgress(done / Math.max(done + remaining, 1));
      $("#player-counter").textContent = `${done} · осталось ~${Math.max(remaining - i, 1)}`;

      const res = await runExercise(item.exercise, async (correct, durationMs, usedHint) => {
        const verdict = await api.post("/api/srs/answer", {
          card_id: item.card_id,
          correct,
          duration_ms: durationMs,
          exercise_type: item.exercise.type,
          used_hint: usedHint,
        });
        let extra = `${verdict.rating_label} · следующий показ ${verdict.interval_human}`;
        if (!correct && item.info.hint)
          extra += `<br>${item.info.hint}`;
        if (verdict.is_leech)
          extra += `<br>Эта карточка даётся тяжело — присмотритесь к подсказке`;
        return extra;
      });
      if (token !== sessionToken) return;
      done++;
      if (res.correct) okCount++;
    }
  }
  if (token !== sessionToken) return;

  setProgress(1);
  playerBody.classList.add("center-step");   // итог — по центру
  playerBody.innerHTML = `
    <div class="result">
      <div class="mark">${done ? "完" : "休"}</div>
      <h2>${done ? "Очередь разобрана" : "Повторять пока нечего"}</h2>
      <p>${done ? `Карточек: ${done} · точность ${Math.round(okCount / done * 100)}%` :
        "Пройдите урок, чтобы добавить карточки в SRS."}</p>
      <button class="primary" id="finish">Готово</button>
    </div>`;
  animateIn(playerBody);
  if (done >= 10) confetti();
  await waitClick($("#finish", playerBody));
  closePlayer();
}

/* ---------- Вкладка «Повторение» ---------- */
async function renderReviewTab() {
  view.innerHTML = `<div class="empty">Загрузка…</div>`;
  const o = await api.get("/api/overview");
  setStreakPill(o.streak);
  Romaji.syncProgress(o.courses);
  const total = o.srs.due + o.srs.new_available;
  const estMin = Math.max(1, Math.round(total * 0.15));
  view.innerHTML = `
    <div class="card">
      <h2>Очередь на сегодня</h2>
      <div class="stat-trio">
        <div><b>${o.srs.due}</b><span>по расписанию</span></div>
        <div><b>${o.srs.new_available}</b><span>${plural(o.srs.new_available, ["новая", "новые", "новых"])}</span></div>
        <div><b>${o.srs.reviews_done_today}</b><span>повторено сегодня</span></div>
      </div>
      ${total
        ? `<button class="primary mt" id="btn-start">Начать сессию · ${total} · ≈${estMin} мин</button>`
        : `<p class="note center mt">Очередь пуста — всё повторено! Новые карточки появятся
           после уроков, повторения — по расписанию FSRS.</p>`}
    </div>`;
  $("#btn-start")?.addEventListener("click", startReview);
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
  view.innerHTML = `<div class="empty">Загрузка…</div>`;
  const [s, ach] = await Promise.all([
    api.get("/api/stats"), api.get("/api/achievements")]);
  const c = s.cards;
  const hasActivity = s.activity.some(d => d.reviews > 0);
  view.innerHTML = `
    <div class="card">
      <h2>Мои карточки</h2>
      <div class="stat-trio">
        <div><b>${c.review}</b><span>в долгой памяти</span></div>
        <div><b>${c.learning + c.relearning}</b><span>ещё учатся</span></div>
        <div><b>${s.retention.week ?? "—"}${s.retention.week != null ? "%" : ""}</b><span>помню при повторении</span></div>
      </div>
      <p class="note mt">«В долгой памяти» — карточки с интервалом от нескольких дней.
      Последняя цифра — доля верных ответов на повторениях за неделю (цель — ${Math.round(s.settings.desired_retention * 100)}%).</p>
    </div>

    <div class="card">
      <h2>Достижения · ${ach.unlocked}/${ach.total}</h2>
      <div class="ach-grid">
        ${ach.items.map(a => `
          <div class="ach ${a.unlocked ? "on " + a.tier : "off"}" title="${a.desc}">
            <div class="ach-ico">${a.unlocked ? a.icon : "🔒"}</div>
            <div class="ach-t">${a.title}</div>
          </div>`).join("")}
      </div>
    </div>
    <div class="card">
      <h2>Сколько я повторял · 14 дней</h2>
      ${hasActivity
        ? barChart(s.activity, "reviews", "date", "", d =>
            `${fmtDay(d.date)}: ${d.reviews}${d.accuracy != null ? ` · точность ${d.accuracy}%` : ""}`)
        : `<p class="note">Пока нет данных — пройдите первую SRS-сессию.</p>`}
    </div>
    <div class="card">
      <h2>Что меня ждёт · 14 дней</h2>
      ${barChart(s.forecast, "count", "date", "fc", (d, i) =>
        `${i === 0 ? "сегодня" : fmtDay(d.date)}: ${d.count}`)}
      <p class="note">Сколько карточек придёт на повторение в каждый день —
      если заниматься ежедневно, горка не вырастет.</p>
    </div>
    ${s.hardest.length ? `
    <div class="card">
      <h2>Трудные знаки</h2>
      <div class="hardest-list">
        ${s.hardest.map(h => `<span class="chip ${h.is_leech ? "leech" : ""}">${h.char}<small>${h.romaji} · ${h.lapses}</small></span>`).join("")}
      </div>
      <p class="note mt">Цифра — сколько раз знак забывался. Обведённые — «пиявки»:
      им в сессии показывается мнемоника.</p>
    </div>` : ""}
    <div class="card">
      <h2>Лимиты SRS</h2>
      <div class="srs-limits">
        <label>Новых карточек в день
          <select id="srs-new">${optionList([0, 4, 8, 12, 16, 20, 25, 30], s.settings.new_per_day, v => v)}</select>
        </label>
        <label>Повторений в день (макс.)
          <select id="srs-rev">${optionList([50, 100, 150, 250, 400, 600], s.settings.reviews_per_day, v => v)}</select>
        </label>
        <label>Целевое удержание
          <select id="srs-ret">${optionList([0.85, 0.9, 0.92, 0.95], s.settings.desired_retention, v => Math.round(v * 100) + "%")}</select>
        </label>
      </div>
      <p class="note mt">Выше удержание — крепче помните, но больше повторений в день.
      Меньше новых — спокойнее темп. Применяется со следующей сессии.</p>
      <p class="note" id="srs-saved" style="display:none">Сохранено ✓</p>
    </div>
    <div class="card">
      <h2>Резервная копия</h2>
      <p class="note" style="margin-top:0">Весь прогресс — карточки, журнал ответов,
      пройденные уроки и настройки — хранится локально в одном файле. Скачайте копию,
      чтобы перенести его на другой компьютер или вернуть после переустановки.</p>
      <div class="data-actions">
        <button class="ghost" id="data-export">Скачать копию</button>
        <button class="ghost" id="data-import">Восстановить из копии…</button>
      </div>
      <input type="file" id="data-file" accept=".db,application/octet-stream" hidden>
      <p class="note" id="data-msg" style="display:none"></p>
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
    try { await api.post("/api/settings", patch); srsHint("Сохранено ✓", true); }
    catch (e) { srsHint("Не удалось сохранить: " + e.message, false); }
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
      "Восстановление заменит весь текущий прогресс данными из копии. " +
      "Перед заменой рядом сохраняется страховочный michi.db.bak. Продолжить?",
      "Восстановить");
    if (!ok) return;
    const msg = $("#data-msg");
    msg.classList.remove("err");
    msg.style.display = "block";
    msg.textContent = "Восстановление…";
    try {
      const res = await fetch("/api/import", { method: "POST", body: file });
      if (!res.ok) throw await apiError(res);
      const r = await res.json();
      msg.textContent = `Готово: ${r.cards} карточек, ${r.reviews} ответов. Перезагрузка…`;
      setTimeout(() => location.reload(), 1000);
    } catch (e) {
      msg.classList.add("err");
      msg.textContent = "Не удалось восстановить: " + e.message;
    }
  });

  // Поздравляем с новыми достижениями (диф против ранее показанных)
  const seen = new Set(JSON.parse(localStorage.getItem("michi_ach_seen") || "[]"));
  const nowUnlocked = ach.items.filter(a => a.unlocked).map(a => a.id);
  const fresh = nowUnlocked.filter(id => !seen.has(id));
  localStorage.setItem("michi_ach_seen", JSON.stringify(nowUnlocked));
  if (fresh.length && seen.size) {  // не салютуем при самом первом заходе
    confetti();
    Haptics.good();
  }
}

/* ---------- Старт ---------- */
show("today");
