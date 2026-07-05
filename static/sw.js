/* MICHI Service Worker — офлайн-оболочка и кэш статики (PWA, SRS.md «учат в метро»).
   Стратегии: навигация — network-first (свежий HTML, офлайн → оболочка из кэша);
   статика — stale-while-revalidate (мгновенно из кэша, обновляется в фоне);
   /api/tts — cache-first (озвучка иммутабельна по тексту+голосу); прочий /api —
   только сеть (динамика, cookie-сессия). Версия CACHE инвалидирует кэш на деплое. */
"use strict";

const VERSION = "a41f09d2c7e8";
const CACHE = `michi-${VERSION}`;
// Минимальная оболочка приложения (EN-оверлей контента и звуки кэшируются лениво
// по факту обращения через stale-while-revalidate — не раздуваем precache).
const SHELL = [
  "/", "/index.html", "/style.css", "/fonts.css", "/app.js", "/i18n.js",
  "/icons.js", "/tracing.js", "/art.js", "/manifest.webmanifest", "/icon.svg",
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;                   // POST/импорт и т.п. — мимо SW
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;         // внешнее (шрифты Google) — мимо

  // HTML-навигация: свежее из сети, офлайн → оболочка из кэша
  if (req.mode === "navigate") {
    e.respondWith(fetch(req).catch(() => caches.match("/index.html")));
    return;
  }

  // Озвучка иммутабельна (один файл на текст+голос) — cache-first
  if (url.pathname === "/api/tts") {
    e.respondWith(caches.open(CACHE).then(async c => {
      const hit = await c.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok) c.put(req, res.clone());
      return res;
    }));
    return;
  }

  if (url.pathname.startsWith("/api/")) return;        // прочий API — только сеть

  // Статика (css/js/svg/звуки/контент) — stale-while-revalidate
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(req);
    const net = fetch(req).then(res => {
      if (res.ok) c.put(req, res.clone());
      return res;
    }).catch(() => hit);
    return hit || net;
  }));
});
