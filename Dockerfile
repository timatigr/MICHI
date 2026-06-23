# MICHI — публичный хостинг. Образ под uvicorn; данные пользователей — на томе.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# gosu — чтобы стартовать под root (починить права тома) и сразу дропнуть
# привилегии до непривилегированного пользователя. См. docker-entrypoint.sh.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gosu \
 && rm -rf /var/lib/apt/lists/*

# Сначала зависимости — слой кэшируется, пока requirements.txt не менялся.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY static ./static

# Версия Service Worker = хэш оболочки: при деплое с изменённой статикой sw.js
# меняется сам собой, и браузеры подтягивают свежий JS (иначе залипал бы кэш).
COPY scripts/stamp_sw.py ./scripts/stamp_sw.py
RUN python scripts/stamp_sw.py

# Непривилегированный пользователь; /app пишем (data/, tts_cache/, ai_cache/).
RUN useradd --create-home michi && chown -R michi /app

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Персистентные данные пользователей (per-user базы) + серверный секрет cookie.
# Свежий том монтируется как root — entrypoint отдаёт его michi перед стартом.
VOLUME ["/app/data"]
EXPOSE 8000

# Контейнер стартует под root → entrypoint chown'ит том и через gosu запускает
# CMD уже под michi. В проде задайте MICHI_SECRET_KEY и MICHI_COOKIE_SECURE=1
# (см. README → «Деплой»). Слушаем 0.0.0.0 — наружу за reverse-proxy.
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
