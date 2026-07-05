/* MICHI — единая система интерфейсных иконок (inline-SVG, только свой origin).

   Зачем: системные эмодзи (⚙ ☾ 🔒 🔊 📜 🔨 …) на каждой ОС рисуются своим
   стилем — на Windows это жёлтые молотки с чёрной обводкой и синие квадраты,
   которые разрушают пастельный язык рядом с SVG-логотипом и артом достижений.

   Две семьи:
   * Icons.ui(name)  — «хром» приложения (шапка, плеер, замки, динамики):
     контурные 24×24, наследуют цвет и КЕГЛЬ текста (width/height = 1em через
     класс .ico) — оптически совпадают с текстом в обеих темах.
   * Icons.art(name) — плитки «Тренировки и игры»: кавай-стиль арта достижений
     (art.js): мягкие заливки палитры + чернильный контур #4A4458, свои цвета
     в обеих темах. viewBox 100×100, размер задаёт контейнер .pt-ico. */
"use strict";

const Icons = {
  ui(name) {
    const d = this._UI[name];
    if (!d) return "";
    // Заливочные иконки (flame) не обводятся; контурные — stroke=currentColor
    const attrs = d.fill
      ? `fill="currentColor" stroke="none"`
      : `fill="none" stroke="currentColor" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round"`;
    return `<svg class="ico ico-${name}" viewBox="0 0 24 24" ${attrs}
      aria-hidden="true">${d.svg || d}</svg>`;
  },

  art(name) {
    const inner = this._ART[name];
    return inner ? `<svg class="art-ico" viewBox="0 0 100 100"
      preserveAspectRatio="xMidYMid meet" aria-hidden="true">${inner}</svg>` : "";
  },

  /* ---------- Контурный «хром» (24×24, currentColor) ---------- */
  _UI: {
    // Тема: солнце / месяц / авто (полукруг) — состояния переключателя
    sun: `<circle cx="12" cy="12" r="4.1"/>
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.65 5.65l1.4 1.4M16.95 16.95l1.4 1.4M18.35 5.65l-1.4 1.4M7.05 16.95l-1.4 1.4"/>`,
    moon: `<path d="M19.5 13.5A7.8 7.8 0 0 1 10.5 4.5 7.9 7.9 0 1 0 19.5 13.5Z"/>`,
    themeAuto: `<circle cx="12" cy="12" r="8.2"/>
      <path d="M12 3.8a8.2 8.2 0 0 1 0 16.4Z" fill="currentColor" stroke="none"/>`,
    gear: `<circle cx="12" cy="12" r="3.1"/>
      <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.03 1.56V21a2 2 0 1 1-4 0v-.09a1.7 1.7 0 0 0-1.11-1.56 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.7 1.7 0 0 0 .34-1.87 1.7 1.7 0 0 0-1.56-1.03H3a2 2 0 1 1 0-4h.09a1.7 1.7 0 0 0 1.56-1.11 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34h.08a1.7 1.7 0 0 0 1.03-1.56V3a2 2 0 1 1 4 0v.09a1.7 1.7 0 0 0 1.03 1.56h.08a1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87v.08a1.7 1.7 0 0 0 1.56 1.03H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.56 1.03Z"/>`,
    close: `<path d="M6.2 6.2 17.8 17.8M17.8 6.2 6.2 17.8"/>`,
    lock: `<rect x="5.6" y="10.6" width="12.8" height="8.8" rx="2.6"/>
      <path d="M8.6 10.6V8.2a3.4 3.4 0 0 1 6.8 0v2.4"/>`,
    // Динамик с волнами — замена 🔊 в кнопках озвучки
    speaker: `<path d="M11.2 5.6 7.2 8.9H4.9A.9.9 0 0 0 4 9.8v4.4c0 .5.4.9.9.9h2.3l4 3.3Z"/>
      <path d="M14.6 9.6a3.4 3.4 0 0 1 0 4.8M17.2 7.2a6.9 6.9 0 0 1 0 9.6"/>`,
    // Искра — ИИ-разбор «Сэнсэй» (вместо 🧠)
    spark: `<path d="M12 4.4l1.7 4.7 4.7 1.7-4.7 1.7L12 17.2l-1.7-4.7-4.7-1.7 4.7-1.7Z"/>
      <path d="M18.6 15.6l.7 1.9 1.9.7-1.9.7-.7 1.9-.7-1.9-1.9-.7 1.9-.7Z"/>`,
    // Огонёк серии — фикс-палитра (тёплый в обеих темах), fill-иконка
    flame: {
      fill: true,
      svg: `<path d="M12 2.4c2 3.6 6.6 5.2 6.6 10.5a6.6 6.6 0 0 1-13.2 0c0-3.1 2.3-4.2 3.8-6.3.8 1.9 2 1.6 2.8-4.2Z" fill="#FF9E4F"/>
      <path d="M12 10.6c1.2 2 3.1 3.2 3.1 5.5a3.1 3.1 0 0 1-6.2 0c0-2.3 1.9-3.5 3.1-5.5Z" fill="#FFD24F"/>`,
    },
  },

  /* ---------- Кавай-плитки практик (100×100, палитра art.js) ---------- */
  _ART: {
    // Свиток 物語 — как арт достижения «Первый кандзи», без глифа
    story: `<rect x="31" y="21" width="38" height="8.5" rx="4.2"
        fill="#C68A5B" stroke="#4A4458" stroke-width="2.4"/>
      <rect x="34" y="28" width="32" height="44"
        fill="#FFF7E9" stroke="#4A4458" stroke-width="2.4"/>
      <rect x="31" y="70" width="38" height="8.5" rx="4.2"
        fill="#C68A5B" stroke="#4A4458" stroke-width="2.4"/>
      <g stroke="#C9A6CE" stroke-width="3.2" stroke-linecap="round">
        <path d="M42,39 H58"/><path d="M42,48 H58"/><path d="M42,57 H53"/></g>`,
    // Наушники — тренировка слуха
    listen: `<path d="M27,60 V50 a23,23 0 0 1 46,0 v10"
        fill="none" stroke="#8E7CC3" stroke-width="6.5" stroke-linecap="round"/>
      <rect x="21" y="55" width="13" height="21" rx="6.5"
        fill="#EF7FA8" stroke="#4A4458" stroke-width="2.4"/>
      <rect x="66" y="55" width="13" height="21" rx="6.5"
        fill="#EF7FA8" stroke="#4A4458" stroke-width="2.4"/>`,
    // Контур высотного ударения — дрилл «Тон»
    pitch: `<path d="M24,66 L40,42 H60 L76,66"
        fill="none" stroke="#B9A7E6" stroke-width="5" stroke-linecap="round"
        stroke-linejoin="round"/>
      <circle cx="24" cy="66" r="6.5" fill="#EF7FA8" stroke="#4A4458" stroke-width="2.2"/>
      <circle cx="50" cy="42" r="6.5" fill="#F4C84B" stroke="#4A4458" stroke-width="2.2"/>
      <circle cx="76" cy="66" r="6.5" fill="#7FD4E0" stroke="#4A4458" stroke-width="2.2"/>`,
    // Звенья цепочки слов — сиритори
    shiritori: `<rect x="20" y="36" width="34" height="22" rx="11"
        fill="none" stroke="#8E7CC3" stroke-width="6"/>
      <rect x="46" y="46" width="34" height="22" rx="11"
        fill="none" stroke="#EF7FA8" stroke-width="6"/>`,
    // Ханами-данго на шпажке — счётчики (一本、三個…)
    counters: `<path d="M50,24 V84" stroke="#C08A5B" stroke-width="5" stroke-linecap="round"/>
      <circle cx="50" cy="32" r="11" fill="#F7B8D0" stroke="#4A4458" stroke-width="2.4"/>
      <circle cx="50" cy="53" r="11" fill="#FFF7E9" stroke="#4A4458" stroke-width="2.4"/>
      <circle cx="50" cy="74" r="11" fill="#CDE9D4" stroke="#4A4458" stroke-width="2.4"/>`,
    // Молот с искрами — «Кузница кандзи»
    forge: `<path d="M50,46 V80" stroke="#C08A5B" stroke-width="8" stroke-linecap="round"/>
      <rect x="28" y="24" width="44" height="20" rx="7"
        fill="#8E7CC3" stroke="#4A4458" stroke-width="2.6"/>
      <rect x="44" y="24" width="12" height="20" fill="#B9A7E6"/>
      <rect x="28" y="24" width="44" height="20" rx="7"
        fill="none" stroke="#4A4458" stroke-width="2.6"/>
      <g stroke="#F4C84B" stroke-width="3.2" stroke-linecap="round">
        <path d="M22,18 l-4,-5"/><path d="M78,18 l4,-5"/><path d="M50,13 v-6"/></g>`,
    // Кисть-фудэ и штрих туши — каллиграфия 書道
    calligraphy: `<path d="M63,16 L47,42"
        stroke="#C08A5B" stroke-width="6" stroke-linecap="round"/>
      <path d="M47,42 C40,48 36,56 38,64 C46,62 53,56 55,48 Z"
        fill="#4A4458" stroke="#4A4458" stroke-width="2" stroke-linejoin="round"/>
      <path d="M24,80 Q48,66 76,74"
        fill="none" stroke="#8E7CC3" stroke-width="6.5" stroke-linecap="round"/>`,
  },
};
