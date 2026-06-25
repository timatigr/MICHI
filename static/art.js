/* MICHI — иллюстрации достижений: кавай-SVG под палитру проекта.

   SVG масштабируются без потерь и живут в тёмной теме (свои цвета, не зависят от
   темы — сидят на тировом градиенте плитки). Единый стиль на все достижения:
   незнакомый id тихо падает на эмодзи из поля icon, так что новые достижения не
   ломают сетку. (Маскот ниже поддерживает drop-in static/img/mascot.png.) */
"use strict";

const Art = {
  _uid: 0,   // счётчик уникальных id градиентов маскота (иначе дубли в одном DOM)
  // достижение -> вид иллюстрации. Несколько ачивок делят вид (тир красит рамку,
  // а каной/кандзи рисуется собственный глиф из поля icon). Незнакомый id даёт
  // фолбэк на эмодзи — новые достижения не ломают сетку.
  KIND: {
    first_lesson: "sprout", first_review: "loop", first_kanji: "scroll",
    gate_first: "torii",
    lessons_10: "book", lessons_30: "book", lessons_60: "grad",
    rev_100: "loop", rev_500: "loop", rev_1000: "target",
    streak_3: "flame", streak_7: "flame", streak_30: "flame", streak_100: "mountain",
    hiragana_done: "kana", katakana_done: "kana",
    kanji_10: "scroll", kanji_30: "scroll",
    words_50: "words", words_150: "words",
    memory_20: "brain", memory_50: "gem",
    accuracy_day: "medal", night_owl: "owl", level_5: "star",
  },

  kindFor(id) { return this.KIND[id] || null; },

  /* Полная плитка: кавай-SVG (или эмодзи для незнакомого id). Для закрытых —
     силуэт (CSS .locked обесцвечивает) с замочком. */
  tile(ach, big = false) {
    const kind = this.kindFor(ach.id);
    const art = kind ? this.svg(kind, ach)
      : `<span class="ach-emoji">${ach.icon || "🏆"}</span>`;
    const lock = ach.unlocked ? "" : `<span class="ach-lock">🔒</span>`;
    return `<span class="ach-art ${ach.unlocked ? "" : "locked"}${big ? " big" : ""}"
      data-kind="${kind || "emoji"}">${art}${lock}</span>`;
  },

  svg(kind, ach) {
    const f = this["_" + kind];
    return f ? this._wrap(f.call(this, ach)) : `<span class="ach-emoji">${ach.icon || ""}</span>`;
  },

  _wrap(inner) {
    return `<svg class="ach-svg" viewBox="0 0 100 100"
      preserveAspectRatio="xMidYMid meet" aria-hidden="true">${inner}</svg>`;
  },

  // Кавай-мордочка: глазки + улыбка + щёчки-румянец
  _face(x, y, s = 1) {
    return `<g fill="#4A4458">
        <circle cx="${x - 6 * s}" cy="${y}" r="${2.4 * s}"/>
        <circle cx="${x + 6 * s}" cy="${y}" r="${2.4 * s}"/></g>
      <path d="M${x - 4 * s},${y + 4 * s} Q${x},${y + 7.5 * s} ${x + 4 * s},${y + 4 * s}"
        fill="none" stroke="#4A4458" stroke-width="${1.8 * s}" stroke-linecap="round"/>
      <g fill="#F498BB" opacity=".75">
        <circle cx="${x - 9.5 * s}" cy="${y + 3.5 * s}" r="${2 * s}"/>
        <circle cx="${x + 9.5 * s}" cy="${y + 3.5 * s}" r="${2 * s}"/></g>`;
  },

  // --- Иллюстрации (viewBox 100×100, мотив ≈ 18..82) ---

  _sprout() {
    return `<ellipse cx="50" cy="84" rx="17" ry="4.5" fill="#4A4458" opacity=".10"/>
      <path d="M50,56 V40" stroke="#5CA37E" stroke-width="4.5" stroke-linecap="round"/>
      <path d="M50,48 C40,48 33,42 33,33 C44,32 50,40 50,48 Z"
        fill="#8FD0AE" stroke="#4A4458" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M50,44 C60,44 67,36 67,27 C56,26 50,35 50,44 Z"
        fill="#5CA37E" stroke="#4A4458" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M36,58 H64 L60,82 H40 Z"
        fill="#E2A36A" stroke="#4A4458" stroke-width="2.6" stroke-linejoin="round"/>
      <rect x="33" y="52" width="34" height="9" rx="3.5"
        fill="#EFB985" stroke="#4A4458" stroke-width="2.6"/>
      ${this._face(50, 70, .8)}`;
  },

  _loop() {
    return `<g fill="none" stroke-width="8" stroke-linecap="round">
        <path d="M27,42 A26,26 0 0,1 71,33" stroke="#8E7CC3"/>
        <path d="M73,58 A26,26 0 0,1 29,67" stroke="#EF7FA8"/></g>
      <path d="M74,24 l5,12 -13,1 Z" fill="#8E7CC3" stroke="#4A4458"
        stroke-width="1.6" stroke-linejoin="round"/>
      <path d="M26,76 l-5,-12 13,-1 Z" fill="#EF7FA8" stroke="#4A4458"
        stroke-width="1.6" stroke-linejoin="round"/>`;
  },

  _torii() {
    return `<g stroke="#4A4458" stroke-width="2.6" stroke-linejoin="round">
        <path d="M22,30 Q50,24 78,30 L74,38 Q50,33 26,38 Z" fill="#E36588"/>
        <rect x="29" y="43" width="42" height="7" fill="#E36588"/>
        <rect x="32" y="38" width="9" height="46" fill="#E36588"/>
        <rect x="59" y="38" width="9" height="46" fill="#E36588"/>
        <rect x="46.5" y="43" width="7" height="9" fill="#C94E72"/></g>`;
  },

  _book() {
    return `<path d="M50,33 C42,28 31,28 23,31 V69 C31,66 42,66 50,71 Z"
        fill="#FFF7E9" stroke="#4A4458" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M50,33 C58,28 69,28 77,31 V69 C69,66 58,66 50,71 Z"
        fill="#FBEFD8" stroke="#4A4458" stroke-width="2.4" stroke-linejoin="round"/>
      <g stroke="#C9A6CE" stroke-width="2.4" stroke-linecap="round">
        <path d="M30,41 H44"/><path d="M30,49 H44"/><path d="M30,57 H43"/>
        <path d="M56,41 H70"/><path d="M56,49 H70"/><path d="M57,57 H70"/></g>
      <circle cx="50" cy="26" r="3.2" fill="#F4C84B" stroke="#4A4458" stroke-width="1.4"/>`;
  },

  _grad() {
    return `<path d="M34,50 V62 C34,69 66,69 66,62 V50"
        fill="#8E7CC3" stroke="#4A4458" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M50,32 L82,44 L50,56 L18,44 Z"
        fill="#6E5DA8" stroke="#4A4458" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M82,44 V60" stroke="#F4C84B" stroke-width="2.4" stroke-linecap="round"/>
      <circle cx="82" cy="63" r="4" fill="#F4C84B" stroke="#4A4458" stroke-width="1.6"/>
      <circle cx="50" cy="44" r="3" fill="#FCE39A"/>`;
  },

  _target() {
    return `<circle cx="50" cy="50" r="27" fill="#fff" stroke="#4A4458" stroke-width="2.6"/>
      <circle cx="50" cy="50" r="19" fill="#F7B8D0"/>
      <circle cx="50" cy="50" r="11" fill="#fff"/>
      <circle cx="50" cy="50" r="4.5" fill="#EF7FA8"/>
      <path d="M74,26 L54,46" stroke="#4A4458" stroke-width="3.2" stroke-linecap="round"/>
      <path d="M52,48 l11,-3 l-3,11 Z" fill="#8E7CC3"
        stroke="#4A4458" stroke-width="1.6" stroke-linejoin="round"/>
      <path d="M74,26 l5,-1 -1,5 Z" fill="#8E7CC3"/>`;
  },

  _flame() {
    return `<ellipse cx="50" cy="84" rx="14" ry="3.6" fill="#4A4458" opacity=".10"/>
      <path d="M50,18 C58,32 72,38 72,55 C72,70 62,82 50,82
        C38,82 28,72 28,56 C28,46 36,45 41,38 C44,46 47,42 50,18 Z"
        fill="#FF9E4F" stroke="#4A4458" stroke-width="2.6" stroke-linejoin="round"/>
      <path d="M50,42 C55,50 61,55 61,64 C61,72 56,78 50,78
        C44,78 40,73 40,65 C40,57 47,55 50,42 Z" fill="#FFD24F"/>
      ${this._face(50, 62, .85)}`;
  },

  _mountain() {
    return `<path d="M20,76 L45,32 Q50,24 55,32 L80,76 Z"
        fill="#8E7CC3" stroke="#4A4458" stroke-width="2.6" stroke-linejoin="round"/>
      <path d="M39,47 L46,36 Q50,30 54,36 L61,47
        Q56,43 50,47 Q44,51 39,47 Z" fill="#FFFFFF"/>
      <path d="M50,30 V18" stroke="#4A4458" stroke-width="2.2" stroke-linecap="round"/>
      <path d="M50,18 L64,21.5 L50,25 Z"
        fill="#EF7FA8" stroke="#4A4458" stroke-width="1.6" stroke-linejoin="round"/>`;
  },

  _kana(ach) {
    const g = ach.icon || "あ";
    return `<circle cx="50" cy="50" r="29" fill="#FFFFFF" stroke="#EF7FA8" stroke-width="5"/>
      <circle cx="50" cy="50" r="29" fill="none" stroke="#4A4458" stroke-width="2" opacity=".22"/>
      <circle cx="50" cy="50" r="23" fill="none" stroke="#F7B8D0" stroke-width="1.6"/>
      <text x="50" y="52" text-anchor="middle" dominant-baseline="central"
        font-family="'Noto Sans JP',sans-serif" font-weight="700" font-size="34"
        fill="#8E7CC3">${g}</text>`;
  },

  _scroll(ach) {
    const g = ach.icon || "字";
    return `<rect x="31" y="21" width="38" height="8.5" rx="4.2"
        fill="#C68A5B" stroke="#4A4458" stroke-width="2.2"/>
      <rect x="34" y="28" width="32" height="44"
        fill="#FFF7E9" stroke="#4A4458" stroke-width="2.2"/>
      <rect x="31" y="70" width="38" height="8.5" rx="4.2"
        fill="#C68A5B" stroke="#4A4458" stroke-width="2.2"/>
      <text x="50" y="51" text-anchor="middle" dominant-baseline="central"
        font-family="'Noto Sans JP',sans-serif" font-weight="700" font-size="25"
        fill="#4A4458">${g}</text>`;
  },

  _words() {
    return `<path d="M22,30 H78 a7,7 0 0,1 7,7 V59 a7,7 0 0,1 -7,7 H45 L33,78 V66 H22
        a7,7 0 0,1 -7,-7 V37 a7,7 0 0,1 7,-7 Z"
        fill="#B9A7E6" stroke="#4A4458" stroke-width="2.4" stroke-linejoin="round"/>
      <g stroke="#FFFFFF" stroke-width="3.4" stroke-linecap="round">
        <path d="M27,43 H64"/><path d="M27,53 H55"/></g>`;
  },

  _brain() {
    return `<path d="M38,33 C27,33 23,46 30,52 C23,58 30,71 41,68
        C45,75 55,75 59,68 C70,71 77,58 70,52 C77,46 73,33 62,33
        C58,26 42,26 38,33 Z"
        fill="#F498BB" stroke="#4A4458" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M50,30 V70 M40,41 Q49,46 40,52 M60,41 Q51,46 60,52"
        fill="none" stroke="#D46E97" stroke-width="2.2" stroke-linecap="round"/>`;
  },

  _gem() {
    return `<path d="M34,38 H66 L78,50 L50,80 L22,50 Z" fill="#7FD4E0"/>
      <path d="M34,38 L42,50 H22 Z" fill="#B6E8F0"/>
      <path d="M66,38 L58,50 H78 Z" fill="#B6E8F0"/>
      <path d="M42,50 H58 L50,80 Z" fill="#57BECE"/>
      <path d="M34,38 L42,50 H58 L66,38 Z" fill="#D5F2F7"/>
      <path d="M34,38 H66 L78,50 L50,80 L22,50 Z"
        fill="none" stroke="#4A4458" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M22,50 H78 M42,50 L34,38 M58,50 L66,38"
        stroke="#4A4458" stroke-width="1.4" opacity=".5"/>`;
  },

  _medal() {
    return `<path d="M40,22 L49,46 H41 Z" fill="#8E7CC3" stroke="#4A4458"
        stroke-width="2" stroke-linejoin="round"/>
      <path d="M60,22 L51,46 H59 Z" fill="#EF7FA8" stroke="#4A4458"
        stroke-width="2" stroke-linejoin="round"/>
      <circle cx="50" cy="60" r="21" fill="#F4C84B" stroke="#4A4458" stroke-width="2.6"/>
      <circle cx="50" cy="60" r="14" fill="#FCE39A"/>
      <path d="M50,50 l2.8,5.7 6.3,.9 -4.6,4.4 1.1,6.2 -5.6,-2.9 -5.6,2.9 1.1,-6.2
        -4.6,-4.4 6.3,-.9 Z" fill="#EF7FA8" stroke="#4A4458"
        stroke-width="1.2" stroke-linejoin="round"/>`;
  },

  _owl() {
    return `<ellipse cx="50" cy="84" rx="17" ry="4" fill="#4A4458" opacity=".10"/>
      <path d="M33,30 L42,42 M67,30 L58,42" stroke="#8E7CC3"
        stroke-width="6.5" stroke-linecap="round"/>
      <ellipse cx="50" cy="56" rx="24" ry="26" fill="#8E7CC3"
        stroke="#4A4458" stroke-width="2.6"/>
      <path d="M50,38 C41,44 41,58 50,64 C59,58 59,44 50,38 Z" fill="#B9A7E6"/>
      <circle cx="40" cy="50" r="9.5" fill="#fff" stroke="#4A4458" stroke-width="2"/>
      <circle cx="60" cy="50" r="9.5" fill="#fff" stroke="#4A4458" stroke-width="2"/>
      <circle cx="40.5" cy="51" r="3.6" fill="#4A4458"/>
      <circle cx="59.5" cy="51" r="3.6" fill="#4A4458"/>
      <path d="M46,57 L50,63 L54,57 Z" fill="#F4C84B"
        stroke="#4A4458" stroke-width="1.6" stroke-linejoin="round"/>`;
  },

  _star() {
    return `<path d="M50,18 l9,18.5 20.4,3 -14.7,14.4 3.5,20.3 -18.2,-9.6 -18.2,9.6
        3.5,-20.3 -14.7,-14.4 20.4,-3 Z"
        fill="#FBD24E" stroke="#4A4458" stroke-width="2.6" stroke-linejoin="round"/>
      ${this._face(50, 47, .95)}`;
  },

  /* ---------- Сад памяти (Sprint 2): дерево сакуры из «силы памяти» FSRS ----------
     Кавай-SVG в едином стиле проекта. Цветущих бутонов = крепких знаков (R высок),
     бледных бутонов = тускнеющих, опадающих лепестков = рискующих забыться.
     Детерминированные слоты → стабильная картинка между перерисовками. */
  GARDEN_SLOTS: [
    [150, 38], [112, 48], [188, 50], [132, 60], [170, 60], [88, 70], [212, 70],
    [150, 72], [104, 88], [196, 88], [128, 92], [172, 92], [76, 86], [224, 86],
    [148, 50], [110, 66], [190, 66], [150, 100],
  ],

  garden(strong, fading, risk) {
    const slots = this.GARDEN_SLOTS;
    const s = Math.max(0, Math.min(strong, slots.length));
    const f = Math.max(0, Math.min(fading, slots.length - s));
    let blooms = "", buds = "";
    for (let i = 0; i < s; i++) blooms += this._sakuraMini(slots[i][0], slots[i][1], 1.15);
    for (let i = 0; i < f; i++) {
      const [x, y] = slots[s + i];
      buds += `<circle cx="${x}" cy="${y}" r="3.6" fill="#F3DCE7"
        stroke="#DCAEC5" stroke-width="1.1"/>`;
    }
    const RP = [[118, 120], [142, 134], [166, 124], [186, 140], [150, 150], [128, 146]];
    let fall = "";
    for (let i = 0; i < Math.min(risk, RP.length); i++) {
      const [x, y] = RP[i];
      fall += `<ellipse cx="${x}" cy="${y}" rx="3.2" ry="5" fill="#F3B6CE"
        stroke="#E78FB0" stroke-width=".8" transform="rotate(${i * 47 - 30} ${x} ${y})"/>`;
    }
    return `<svg class="garden-svg" viewBox="0 0 300 170"
        preserveAspectRatio="xMidYMid meet" aria-hidden="true">
      <ellipse cx="150" cy="159" rx="92" ry="8" fill="#4A4458" opacity=".08"/>
      <path d="M143,156 Q147,120 139,96 L161,96 Q153,120 157,156 Z"
        fill="#C08A5B" stroke="#4A4458" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M150,122 L126,104 M150,114 L174,98" stroke="#C08A5B"
        stroke-width="5" stroke-linecap="round"/>
      <g fill="#CDE9D4" stroke="#A6D2B0" stroke-width="2">
        <ellipse cx="150" cy="62" rx="76" ry="50"/>
        <ellipse cx="102" cy="78" rx="44" ry="33"/>
        <ellipse cx="198" cy="78" rx="44" ry="33"/>
      </g>
      ${buds}${blooms}${fall}
    </svg>`;
  },

  /* ---------- Маскот «Кицунэ-моти» (личность приложения) ----------
     Кавай-лисёнок под палитру. Drop-in: положи static/img/mascot.png —
     перекроет SVG (как у достижений). mood: wave (обычный) | cheer (радость). */
  mascotTile(mood = "wave", cls = "") {
    const p = "m" + (this._uid++) + "-";
    return `<span class="mascot-art ${cls}">${this._wrap(this._mascot(mood, p))}`
      + `<img class="mascot-photo" src="/img/mascot.png" alt="" loading="lazy"`
      + ` onload="this.classList.add('ok')" onerror="this.remove()"></span>`;
  },

  _sakuraMini(cx, cy, s = 1) {
    const petals = [0, 72, 144, 216, 288].map(a =>
      `<ellipse cx="0" cy="${-6 * s}" rx="${3.4 * s}" ry="${5 * s}" fill="#F8C0D6"`
      + ` stroke="#E78FB0" stroke-width="${0.9 * s}" transform="rotate(${a})"/>`).join("");
    return `<g transform="translate(${cx},${cy})">${petals}`
      + `<circle r="${2.3 * s}" fill="#F8CD6F"/></g>`;
  },

  _mascot(mood, p) {
    const happy = mood === "cheer";
    const eye = (cx) => happy
      ? `<path d="M${cx - 5},51 Q${cx},44 ${cx + 5},51" fill="none"
           stroke="#3A3550" stroke-width="3" stroke-linecap="round"/>`
      : `<ellipse cx="${cx}" cy="52" rx="4.7" ry="5.8" fill="#3A3550"/>
         <circle cx="${cx - 1.7}" cy="49.6" r="1.7" fill="#fff"/>`;
    return `<defs>
        <linearGradient id="${p}h" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#FFF8EE"/><stop offset="1" stop-color="#FBE7D2"/>
        </linearGradient></defs>
      <ellipse cx="50" cy="88" rx="21" ry="4.5" fill="#4A4458" opacity=".10"/>
      <path d="M26,42 L23,17 L45,33 Z" fill="url(#${p}h)" stroke="#4A4458"
        stroke-width="2.6" stroke-linejoin="round"/>
      <path d="M74,42 L77,17 L55,33 Z" fill="url(#${p}h)" stroke="#4A4458"
        stroke-width="2.6" stroke-linejoin="round"/>
      <path d="M30,35 L28.5,24 L39,32 Z" fill="#F4A0C0"/>
      <path d="M70,35 L71.5,24 L61,32 Z" fill="#F4A0C0"/>
      <path d="M50,27 C69,27 81,40 81,57 C81,75 67,86 50,86
        C33,86 19,75 19,57 C19,40 31,27 50,27 Z"
        fill="url(#${p}h)" stroke="#4A4458" stroke-width="2.8" stroke-linejoin="round"/>
      <path d="M50,72 C40,72 33,66 33,66 C40,63 60,63 67,66 C67,66 60,72 50,72 Z"
        fill="#FFFFFF" opacity=".55"/>
      <ellipse cx="29" cy="63" rx="6.2" ry="4.2" fill="#F58AB0" opacity=".7"/>
      <ellipse cx="71" cy="63" rx="6.2" ry="4.2" fill="#F58AB0" opacity=".7"/>
      ${eye(35)}${eye(65)}
      <circle cx="50" cy="60" r="2.1" fill="#3A3550"/>
      <path d="M50,62 L50,64 M44,66 Q50,70 56,66" fill="none"
        stroke="#3A3550" stroke-width="2" stroke-linecap="round"/>
      ${this._sakuraMini(72, 22, 1)}`;
  },
};
