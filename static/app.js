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
  settingsModal.classList.add("open");
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
  $("#btn-review")?.addEventListener("click", startReview);
  $("#btn-lesson")?.addEventListener("click", () => startLesson(next.id));
}

/* ---------- Путь: регионы и сетка уроков ---------- */
const COURSE_OF = { l: "hiragana", k: "katakana", v: "n5", j: "kanji" };
const COURSE_LABEL = { all: "Все", hiragana: "Хирагана", katakana: "Катакана", n5: "Слова N5", kanji: "Кандзи" };
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
          <div class="lesson-card ${l.status}" data-id="${l.id}" data-status="${l.status}">
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

/* ---------- Упражнения ----------
   Каждый рендерер возвращает {correct, durationMs, usedHint}.
   afterAnswer — async-колбэк: вызывается после ответа, возвращает
   HTML (SRS-вердикт) для блока фидбека. */

/* Вердикт ответа в виде пилюли с галочкой/крестиком */
function verdict(ok, html) {
  return `<span class="verdict">${ok ? "✓ " : "✗ "}${html}</span>`;
}

async function runExercise(ex, afterAnswer) {
  if (ex.type === "kana_word_build" || ex.type === "vocab_build")
    return runWordBuild(ex, afterAnswer);
  if (ex.type === "kana_twins") return runTwins(ex, afterAnswer);
  if (ex.type === "kana_tracing" || ex.type === "kanji_tracing")
    return runTracing(ex, afterAnswer);
  return runChoice(ex, afterAnswer);
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
  const promptHtml = style === "audio"
    ? `<button class="audio-prompt" data-tts="${ex.prompt.tts}" title="Прослушать ещё раз">🔊</button>`
    : `<div class="prompt-text ${style === "jp" ? "jp" : ""}" ${ex.prompt.tts ? `data-tts="${ex.prompt.tts}"` : ""}>${ex.prompt.text}</div>` +
      (style !== "jp" && ex.prompt.tts ? ttsButton(ex.prompt.tts) : "");
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
    if (step.type === "intro_text") await showIntroText(step);
    else if (step.type === "intro_kana") await showIntroKana(step);
    else if (step.type === "intro_word") await showIntroWord(step);
    else if (step.type === "intro_kanji") await showIntroKanji(step);
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
  playerBody.innerHTML = `
    <div class="result">
      <div class="mark">完</div>
      <h2>${lesson.title} — пройден</h2>
      <p>Точность ${Math.round(score * 100)}% · ${correct} из ${total}<br>
      ${done.cards_created ? `В SRS добавлено карточек: ${done.cards_created}` : "Карточки уже в SRS"}</p>
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

async function renderStats() {
  view.innerHTML = `<div class="empty">Загрузка…</div>`;
  const s = await api.get("/api/stats");
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
      <p class="note">${s.settings.new_per_day} новых карточек и ${s.settings.reviews_per_day} повторений в день,
      целевое удержание ${Math.round(s.settings.desired_retention * 100)}%.</p>
    </div>`;
}

/* ---------- Старт ---------- */
show("today");
