/* Рукописный ввод каны с проверкой черт (SRS.md 6.7, данные KanjiVG).
   Онлайн-распознавание по траекториям: число черт -> порядок ->
   направление -> форма (среднее расстояние ресемплированных траекторий). */
"use strict";

const Tracing = (() => {
  const VIEW = 109; // viewBox KanjiVG
  const N = 24;     // точек на черту при ресемплинге

  /* Цвета берутся из CSS-переменных — канва следует за темой оформления */
  function themeColors() {
    const css = getComputedStyle(document.documentElement);
    const get = (name, fallback) => (css.getPropertyValue(name) || fallback).trim();
    return {
      grid: get("--trace-grid", "#EAE5F4"),
      guide: get("--trace-guide", "#DCD4EC"),
      done: get("--trace-done", "#4A4458"),
      live: get("--trace-live", "#7B68B5"),
      error: get("--error", "#C9536B"),
      hint: get("--pink", "#EF7FA8"),
      marker: get("--pink", "#EF7FA8"),
    };
  }

  /* SVG-черты -> полилинии в координатах 0..109 (через getPointAtLength) */
  function sampleStrokes(strokeDs) {
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", `0 0 ${VIEW} ${VIEW}`);
    svg.style.cssText = "position:fixed;left:-300px;top:0;width:109px;height:109px;visibility:hidden";
    document.body.appendChild(svg);
    const polys = strokeDs.map(d => {
      const p = document.createElementNS(ns, "path");
      p.setAttribute("d", d);
      svg.appendChild(p);
      const L = p.getTotalLength();
      const pts = [];
      for (let i = 0; i < N; i++) {
        const pt = p.getPointAtLength((L * i) / (N - 1));
        pts.push([pt.x, pt.y]);
      }
      return pts;
    });
    svg.remove();
    return polys;
  }

  /* Ресемплинг произвольной траектории по длине дуги */
  function resample(points, n = N) {
    if (points.length < 2) return null;
    const dist = [0];
    let total = 0;
    for (let i = 1; i < points.length; i++) {
      total += Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]);
      dist.push(total);
    }
    if (total < 1e-6) return null;
    const out = [];
    let j = 0;
    for (let i = 0; i < n; i++) {
      const target = (total * i) / (n - 1);
      while (j < dist.length - 2 && dist[j + 1] < target) j++;
      const seg = dist[j + 1] - dist[j] || 1;
      const t = (target - dist[j]) / seg;
      out.push([
        points[j][0] + (points[j + 1][0] - points[j][0]) * t,
        points[j][1] + (points[j + 1][1] - points[j][1]) * t,
      ]);
    }
    return out;
  }

  function meanDist(a, b) {
    let s = 0;
    for (let i = 0; i < a.length; i++) s += Math.hypot(a[i][0] - b[i][0], a[i][1] - b[i][1]);
    return s / a.length;
  }

  function strokeLen(pts) {
    let s = 0;
    for (let i = 1; i < pts.length; i++) s += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    return s;
  }

  /* create(host, {strokes, mode, onComplete, onStatus})
     mode: trace | memory; onComplete({errors, usedHint}) */
  function create(host, opts) {
    const size = Math.min(300, Math.max(220, window.innerWidth - 72));
    const dpr = window.devicePixelRatio || 1;
    const scale = size / VIEW;

    host.innerHTML = `
      <div class="trace-wrap">
        <canvas width="${size * dpr}" height="${size * dpr}"
                style="width:${size}px;height:${size}px"></canvas>
        <div class="trace-tools">
          <button class="ghost small" data-act="clear">Стереть</button>
          ${opts.mode === "memory" ? `<button class="ghost small" data-act="hint">Подсказка</button>` : ""}
          <span class="trace-counter"></span>
        </div>
        <div class="trace-msg"></div>
      </div>`;

    const canvas = host.querySelector("canvas");
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.lineCap = ctx.lineJoin = "round";
    const COLORS = themeColors();
    const msg = host.querySelector(".trace-msg");
    const counter = host.querySelector(".trace-counter");

    const refs = sampleStrokes(opts.strokes)
      .map(poly => poly.map(([x, y]) => [x * scale, y * scale]));
    const total = refs.length;

    let idx = 0;
    let errors = 0;
    let failsOnCurrent = 0;
    let usedHint = false;
    let livePoints = null;
    let hintVisible = false;
    let flashStroke = null; // [{pts, color}] временная подсветка
    let finished = false;

    const threshold = size * (opts.mode === "trace" ? 0.13 : 0.18);
    const endThreshold = size * 0.28;

    function drawPoly(pts, color, width) {
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
      ctx.stroke();
    }

    function drawGrid() {
      ctx.strokeStyle = COLORS.grid;
      ctx.lineWidth = 1;
      ctx.strokeRect(0.5, 0.5, size - 1, size - 1);
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(size / 2, 0); ctx.lineTo(size / 2, size);
      ctx.moveTo(0, size / 2); ctx.lineTo(size, size / 2);
      ctx.moveTo(0, 0); ctx.lineTo(size, size);
      ctx.moveTo(size, 0); ctx.lineTo(0, size);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    function redraw(partialHint) {
      ctx.clearRect(0, 0, size, size);
      drawGrid();
      const inkW = Math.max(7, size * 0.035);
      // Контур-образец: в трассировке всегда, в памяти — при подсказке
      if (opts.mode === "trace" || hintVisible) {
        refs.forEach(p => drawPoly(p, COLORS.guide, inkW));
      }
      // Завершённые черты
      for (let i = 0; i < idx; i++) drawPoly(refs[i], COLORS.done, inkW);
      // Анимация подсказки текущей черты
      if (partialHint && partialHint.length > 1) drawPoly(partialHint, COLORS.hint, inkW);
      // Вспышка ошибки
      if (flashStroke) drawPoly(flashStroke, COLORS.error, inkW * 0.8);
      // Текущий ввод
      if (livePoints && livePoints.length > 1) drawPoly(livePoints, COLORS.live, inkW * 0.8);
      // Маркер начала текущей черты (режим трассировки)
      if (opts.mode === "trace" && idx < total && !partialHint) {
        const [x, y] = refs[idx][0];
        ctx.fillStyle = COLORS.marker;
        ctx.beginPath();
        ctx.arc(x, y, 9, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.font = "bold 11px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(idx + 1), x, y);
      }
      counter.textContent = `черта ${Math.min(idx + 1, total)} из ${total}`;
    }

    function setMsg(text, kind) {
      msg.textContent = text || "";
      msg.className = `trace-msg ${kind || ""}`;
    }

    function animateHint(strokeIdx, cb) {
      const pts = refs[strokeIdx];
      const t0 = performance.now();
      const dur = 700;
      (function frame(now) {
        const t = Math.min((now - t0) / dur, 1);
        const upto = Math.max(2, Math.round(pts.length * t));
        redraw(pts.slice(0, upto));
        if (t < 1) requestAnimationFrame(frame);
        else setTimeout(() => { redraw(); cb && cb(); }, 250);
      })(t0);
    }

    function validate(userPts) {
      const ref = refs[idx];
      if (strokeLen(userPts) < 6) return; // случайный тап
      const user = resample(userPts);
      if (!user) return;

      const fwd = meanDist(user, ref);
      const bwd = meanDist([...user].reverse(), ref);

      if (bwd < fwd && bwd <= threshold) {
        // Форма верна, направление обратное (6.7: направление каждой черты)
        if (opts.mode === "memory") errors++;
        setMsg("Направление: эта черта пишется с другого конца", "warn");
        return;
      }
      const endsOk =
        Math.hypot(user[0][0] - ref[0][0], user[0][1] - ref[0][1]) <= endThreshold &&
        Math.hypot(user[N - 1][0] - ref[N - 1][0], user[N - 1][1] - ref[N - 1][1]) <= endThreshold;

      if (fwd <= threshold && endsOk) {
        idx++;
        failsOnCurrent = 0;
        setMsg("");
        redraw();
        if (idx === total) {
          finished = true;
          setMsg(errors === 0 ? "Отлично написано!" : "Готово", "ok");
          opts.onComplete({ errors, usedHint });
        }
        return;
      }

      // Неверная форма
      errors++;
      failsOnCurrent++;
      flashStroke = userPts;
      redraw();
      setTimeout(() => { flashStroke = null; redraw(); }, 450);
      if (failsOnCurrent >= 2) {
        if (opts.mode === "memory") usedHint = true;
        setMsg("Смотрите, как пишется эта черта", "warn");
        animateHint(idx);
      } else {
        setMsg("Не похоже — попробуйте ещё раз", "warn");
      }
    }

    /* Ввод */
    canvas.style.touchAction = "none";
    canvas.addEventListener("pointerdown", e => {
      if (finished || idx >= total) return;
      canvas.setPointerCapture(e.pointerId);
      const r = canvas.getBoundingClientRect();
      livePoints = [[e.clientX - r.left, e.clientY - r.top]];
    });
    canvas.addEventListener("pointermove", e => {
      if (!livePoints) return;
      const r = canvas.getBoundingClientRect();
      livePoints.push([e.clientX - r.left, e.clientY - r.top]);
      redraw();
    });
    const finishStroke = () => {
      if (!livePoints) return;
      const pts = livePoints;
      livePoints = null;
      redraw();
      validate(pts);
    };
    canvas.addEventListener("pointerup", finishStroke);
    canvas.addEventListener("pointercancel", () => { livePoints = null; redraw(); });

    host.querySelector('[data-act="clear"]').addEventListener("click", () => {
      if (finished) return;
      idx = 0;
      failsOnCurrent = 0;
      setMsg("");
      redraw();
    });
    const hintBtn = host.querySelector('[data-act="hint"]');
    if (hintBtn) hintBtn.addEventListener("click", () => {
      if (finished) return;
      usedHint = true;
      hintVisible = true;
      redraw();
      setTimeout(() => { hintVisible = false; redraw(); }, 1600);
    });

    redraw();
  }

  /* preview(host, strokes, size) — зацикленная анимация порядка черт
     (раздел 2.1: знакомство со знаком). Останавливается сама, когда
     канва исчезает из DOM. */
  function preview(host, strokeDs, size = 176) {
    const dpr = window.devicePixelRatio || 1;
    host.innerHTML = `<canvas class="kana-preview" width="${size * dpr}" height="${size * dpr}"
      style="width:${size}px;height:${size}px"></canvas>`;
    const canvas = host.querySelector("canvas");
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.lineCap = ctx.lineJoin = "round";
    const C = themeColors();
    const scale = size / VIEW;
    const refs = sampleStrokes(strokeDs)
      .map(poly => poly.map(([x, y]) => [x * scale, y * scale]));
    const inkW = Math.max(6, size * 0.05);
    const STROKE_MS = 460, PAUSE_MS = 140, HOLD_MS = 1400;
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

    function drawPoly(pts, color, upto = pts.length) {
      if (upto < 2) return;
      ctx.strokeStyle = color;
      ctx.lineWidth = inkW;
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < upto; i++) ctx.lineTo(pts[i][0], pts[i][1]);
      ctx.stroke();
    }

    function drawFrame(strokeIdx, frac) {
      ctx.clearRect(0, 0, size, size);
      refs.forEach(p => drawPoly(p, C.grid));          // лёгкий контур-призрак
      for (let i = 0; i < strokeIdx; i++) drawPoly(refs[i], C.done);
      if (frac > 0 && strokeIdx < refs.length) {
        const pts = refs[strokeIdx];
        drawPoly(pts, C.live, Math.max(2, Math.round(pts.length * frac)));
      }
    }

    if (reduced) { drawFrame(refs.length, 0); return; }

    let start = performance.now();
    (function frame(now) {
      if (!canvas.isConnected) return;                 // экран сменился
      const cycle = refs.length * (STROKE_MS + PAUSE_MS) + HOLD_MS;
      const t = (now - start) % cycle;
      const per = STROKE_MS + PAUSE_MS;
      const idx = Math.floor(t / per);
      if (idx >= refs.length) drawFrame(refs.length, 0);  // удержание
      else drawFrame(idx, Math.min((t - idx * per) / STROKE_MS, 1));
      requestAnimationFrame(frame);
    })(start);
  }

  return { create, preview };
})();
