# MICHI — гайд по выкладке в общий доступ

Пошаговый запуск публичного сайта с нуля до «работает, застраховано, наблюдаемо».
Технически всё уже в репозитории ([Dockerfile](Dockerfile), [fly.toml](fly.toml),
заголовки безопасности, рейт-лимит, бэкапы, чистка баз) — этот файл только
о том, **что нажать и в каком порядке**. Обзор возможностей и переменных
окружения — в [README](README.md#публичный-хостинг-анонимные-сессии).

Ориентир по времени: шаги 1–3 — около часа; шаги 4–5 — ещё ~30 минут.
Стоимость: Fly-машина `shared-cpu-1x` с auto-stop при малом трафике —
порядка $1–3/мес; Cloudflare R2 и мониторинг — бесплатные тарифы.

---

## Шаг 0. Что должно быть готово локально

- Тесты зелёные: `.venv\Scripts\python -m pytest -q`
- UI-прогон чистый: `.venv\Scripts\python scripts\ui_check.py`
- Если правилась статика — Service Worker перештампован:
  `.venv\Scripts\python scripts\stamp_sw.py` (иначе тест `test_sw_version` упадёт).

## Шаг 1. Код: закоммитить и завести remote

Сейчас репозиторий существует **только на этой машине** — это главный риск.

1. Закоммитить рабочую копию (незакоммиченные фичи + новые файлы):

   ```bash
   git add -A
   git commit -m "Публичный запуск: щиты стрика, кэш вкладок, иконки PWA, валидация API"
   git checkout main && git merge public-hosting
   ```

2. Создать репозиторий на GitHub — <https://github.com/new> (код под MIT,
   можно публичный: пользовательские данные в git не попадают — `data/`,
   `michi.db`, кэши в [.gitignore](.gitignore)). Затем:

   ```bash
   git remote add origin https://github.com/<ваш-логин>/michi.git
   git push -u origin main public-hosting
   ```

   Либо одной командой через [GitHub CLI](https://cli.github.com/):
   `gh repo create michi --public --source . --push`

3. CI заработает сам: [.github/workflows/ci.yml](.github/workflows/ci.yml)
   гоняет pytest на Python 3.10/3.12 при каждом push
  (о GitHub Actions: <https://docs.github.com/actions>).

## Шаг 2. Fly.io: первый деплой

Почему Fly: [fly.toml](fly.toml) уже написан, HTTPS автоматический, том для
данных рядом с приложением. Альтернативы (Render/Railway/свой VPS) — в конце.

1. **Аккаунт и CLI**
   - Регистрация: <https://fly.io/app/sign-up>
   - flyctl на Windows (PowerShell): команда из
     <https://fly.io/docs/flyctl/install/> —
     `pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"`
   - Войти: `fly auth login`

2. **Имя приложения** — в [fly.toml](fly.toml) поменять `app = "michi-jp"`
   на своё (имя уникально на весь Fly), затем создать приложение:

   ```bash
   fly apps create <ваше-имя>
   ```

3. **Том для данных** (per-user базы + секрет cookie живут тут;
   документация: <https://fly.io/docs/volumes/>):

   ```bash
   fly volumes create michi_data --region fra --size 1
   ```

   1 ГБ хватит на тысячи пользователей (личная база — десятки–сотни КБ).

4. **Секрет подписи cookie — ДО первого деплоя**
   (секреты Fly: <https://fly.io/docs/apps/secrets/>):

   ```bash
   fly secrets set MICHI_SECRET_KEY=$(openssl rand -hex 32)
   ```

   В PowerShell без openssl:
   `fly secrets set MICHI_SECRET_KEY=$(python -c "import secrets;print(secrets.token_hex(32))")`

   Без секрета сервер в прод-режиме **не стартует** (fail-fast): при потере
   тома или смене ключа все посетители разом теряют доступ к прогрессу.
   Сохраните значение в менеджере паролей.

5. **Деплой — строго одна машина.** Данные лежат на локальном томе, поэтому
   двух инстансов быть не должно. По умолчанию `fly deploy` создаёт ДВЕ
   машины (и второй том!) ради HA — глушим флагом:

   ```bash
   fly deploy --ha=false
   fly scale count 1        # страховка: убедиться, что машина ровно одна
   fly status               # state=started, 1 machine
   ```

6. **Проверка**: открыть `https://<ваше-имя>.fly.dev` — онбординг, первый
   урок; `https://<ваше-имя>.fly.dev/api/health` → `{"ok":true}`.
   Логи: `fly logs` (<https://fly.io/docs/monitoring/logging/>).

`auto_stop_machines` в fly.toml гасит машину без трафика (данные на томе
целы) и будит на первый запрос — на бесплатно-малом трафике счёт близок к
нулю. Цены: <https://fly.io/docs/about/pricing/>.

## Шаг 3. Offsite-бэкапы (не откладывать: том — единственная копия всех данных)

Сервер уже сам снимает суточные архивы в `data/backups/` на томе, но потерю
тома они не переживут. Выгрузка в S3-совместимое хранилище встроена
([app/backup.py](app/backup.py)) — нужно только хранилище.

**Cloudflare R2** (10 ГБ бесплатно, egress бесплатный;
<https://developers.cloudflare.com/r2/>):

1. Аккаунт Cloudflare → R2 Object Storage → **Create bucket** → `michi-backups`
   (включение R2 может попросить привязать карту; в пределах бесплатной
   квоты списаний нет: <https://developers.cloudflare.com/r2/pricing/>).
2. **API-токен**: R2 → Manage API tokens → Create — права **Object Read & Write**,
   область — только этот бакет (<https://developers.cloudflare.com/r2/api/tokens/>).
   Получите Access Key ID, Secret Access Key и endpoint вида
   `https://<account-id>.r2.cloudflarestorage.com`.
3. Прокинуть в приложение:

   ```bash
   fly secrets set \
     MICHI_BACKUP_S3_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com \
     MICHI_BACKUP_S3_BUCKET=michi-backups \
     MICHI_BACKUP_S3_ACCESS_KEY=... \
     MICHI_BACKUP_S3_SECRET_KEY=...
   ```

   (`MICHI_BACKUP_S3_REGION` по умолчанию `auto` — для R2 верно; для AWS S3
   укажите регион явно.)
4. Проверить: `fly logs` → строка `Серверный бэкап: … → выгружен offsite`,
   в бакете появился `michi/michi-data-*.tar.gz`.
5. **Ротация удалённых копий — lifecycle-правилом бакета** (например, хранить
   30 дней): <https://developers.cloudflare.com/r2/buckets/object-lifecycles/>.
   Ключу с сервера прав на удаление не давать — взлом сервера не сотрёт бэкапы.

Альтернатива без карты: Backblaze B2, тоже S3-совместимый и 10 ГБ бесплатно —
<https://www.backblaze.com/cloud-storage>.

Дополнительный слой: Fly сам делает ежедневные снапшоты тома (хранятся 5 дней) —
<https://fly.io/docs/volumes/snapshots/>. Это удобно, но не замена offsite.

**Восстановление после аварии**: новый том → скачать последний архив из R2 →
`tar -xzf michi-data-*.tar.gz -C data` на томе (через `fly ssh console` /
`fly ssh sftp`) → перезапуск. Архив содержит и `secret.key`, но при заданном
`MICHI_SECRET_KEY` (наш случай) cookie переживут восстановление сами.

## Шаг 4. Аптайм-мониторинг (5 минут)

Направить бесплатный монитор на `https://<ваше-имя>.fly.dev/api/health`
(эндпоинт дешёвый: не трогает диск и не плодит сессий):

- UptimeRobot — <https://uptimerobot.com/> (бесплатно: HTTP-монитор,
  интервал 5 мин, алерты на почту), или
- Better Stack — <https://betterstack.com/uptime>.

Бонус: регулярный пинг не даёт машине с `auto_stop` засыпать — если хотите
«всегда тёплый» сайт, это самый дешёвый способ (или поставьте
`min_machines_running = 1` в fly.toml).

## Шаг 5. Опции продукта (можно после запуска)

**Озвучка.** В fly.toml серверный TTS выключен (`MICHI_TTS_ENABLED=0`):
Edge TTS под потоком посетителей троттлит. Посетители получают голос браузера —
работает везде. Хотите аниме-голоса (Дзундамон и др.) для всех:

- поднять рядом контейнер `voicevox/voicevox_engine`
  (<https://hub.docker.com/r/voicevox/voicevox_engine>, движок:
  <https://voicevox.hiroshiba.jp/>) — на Fly это второе приложение в приватной
  сети (<https://fly.io/docs/networking/private-networking/>), адрес прокинуть:
  `fly secrets set MICHI_VOICEVOX_URL=http://<vv-app>.internal:50021`;
- на VPS то же самое даёт готовый [docker-compose.yml](docker-compose.yml).
- Учтите условия использования голосов персонажей VOICEVOX (кредит вида
  «VOICEVOX:ずんだもん»): <https://voicevox.hiroshiba.jp/term/>.

**ИИ-Сэнсэй** (разбор ошибок; по умолчанию выключен, курс работает без него):

```bash
fly secrets set GEMINI_API_KEY=...            # бесплатный ключ: https://aistudio.google.com/apikey
# или Claude: fly secrets set ANTHROPIC_API_KEY=...   # https://console.anthropic.com/settings/keys
fly secrets set MICHI_AI_GLOBAL_DAILY_LIMIT=500       # общий потолок в сутки — страховка бюджета
```

Персональный лимит уже есть (200/сутки на пользователя, кэш-разборы квоту
не тратят). Провайдер определяется по ключу автоматически.

## Шаг 6. Домен и внешний вид ссылок

- Из коробки сайт живёт на `https://<ваше-имя>.fly.dev` — этого достаточно.
- Свой домен: купить (например, <https://porkbun.com/> или
  <https://www.cloudflare.com/products/registrar/>), затем
  `fly certs add michi.example.com` + CNAME на `<ваше-имя>.fly.dev` —
  инструкция: <https://fly.io/docs/networking/custom-domain/>.
- Превью ссылок (Open Graph) уже настроено с относительным `og.png` —
  заработает на любом домене без правок. Проверить:
  <https://www.opengraph.xyz/> или валидаторы соцсетей.
- `robots.txt` уже закрывает `/api/` от индексации, интерфейс индексировать можно.

## Шаг 7. Жизнь после запуска

- **Обновления**: правки → `pytest` + `scripts/ui_check.py` + при правке статики
  `scripts/stamp_sw.py` → `git push` → `fly deploy --ha=false`. Пользователи
  получат новую версию при следующем заходе (SW сам сбросит кэш по версии).
- **Логи**: `fly logs` — фоновые задачи (бэкап, чистка) пишут WARNING/ERROR туда.
- **Метрики владельца без трекеров**: раз в неделю
  `python scripts/owner_stats.py --days 7` по скачанной копии данных
  (или в `fly ssh console`) — DAU, retention D1/D7/D30, воронка уроков.
- **Право пользователя на данные** уже встроено: экспорт/импорт одним файлом
  и «Удалить мои данные» в ⚙ → Статистика; заброшенные пустые базы сервер
  чистит сам раз в сутки.

## Альтернатива: свой VPS вместо Fly

Любой VPS с Docker (Hetzner <https://www.hetzner.com/cloud> ~€4/мес,
DigitalOcean <https://www.digitalocean.com/> и т.п.):

```bash
echo "MICHI_SECRET_KEY=$(openssl rand -hex 32)" > .env
docker compose up -d        # приложение + VOICEVOX из docker-compose.yml
```

TLS и лимиты — на reverse-proxy, проще всего Caddy с автоматическим HTTPS
(<https://caddyserver.com/docs/>): две строки конфига есть в
[README](README.md#деплой-docker). Бэкапы/мониторинг — те же шаги 3–4
(переменные окружения вместо `fly secrets`).

---

## Чек-лист запуска

- [ ] Тесты + ui_check зелёные, sw.js заштампован
- [ ] Код закоммичен и запушен на GitHub (CI зелёный)
- [ ] `fly apps create` + том `michi_data` + `MICHI_SECRET_KEY` задан
- [ ] `fly deploy --ha=false`, машина ровно одна, `/api/health` отвечает
- [ ] R2-бакет + `MICHI_BACKUP_S3_*`, в логах «выгружен offsite», lifecycle-правило
- [ ] Монитор на `/api/health` шлёт алерты на почту
- [ ] (опция) VOICEVOX / ИИ-ключ с глобальным лимитом
- [ ] (опция) Свой домен + проверка OG-превью
