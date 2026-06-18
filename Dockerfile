# MICHI — публичный хостинг. Образ под uvicorn; данные пользователей — на томе.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Сначала зависимости — слой кэшируется, пока requirements.txt не менялся.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY static ./static

# Непривилегированный пользователь; /app пишем (data/, tts_cache/, ai_cache/).
RUN useradd --create-home michi && chown -R michi /app
USER michi

# Персистентные данные пользователей (per-user базы) + серверный секрет cookie.
VOLUME ["/app/data"]
EXPOSE 8000

# Слушаем 0.0.0.0 — наружу за reverse-proxy. В проде задайте MICHI_SECRET_KEY
# и MICHI_COOKIE_SECURE=1 (см. README → «Деплой»).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
