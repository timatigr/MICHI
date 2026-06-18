"""ИИ-разбор ошибок «Сэнсэй» (SRS.md 7.2 п.2).

Опциональная подсистема: без ключа провайдера (или его библиотеки) приложение
работает как раньше — фронтенд скрывает кнопку разбора (деградация по 7.3).
Стабильный системный промпт переиспользуется, а готовые разборы складываются на
диск в ai_cache/ по ключу «провайдер/модель × тип ошибки × упражнение» (7.1:
кэширование типовых объяснений), чтобы один и тот же промах не оплачивался дважды.

Абстракция провайдера (SRS.md 7.1 «interface LlmProvider»): поддержаны Claude
(Anthropic, модель Haiku) и Gemini (Google, модель Flash — бесплатный тариф).
Выбор провайдера:
  MICHI_AI_PROVIDER=claude|gemini  — явный выбор; иначе автоопределение по ключу
  (GEMINI_API_KEY → gemini, ANTHROPIC_API_KEY → claude).
  MICHI_GEMINI_MODEL / MICHI_CLAUDE_MODEL — переопределить модель.

Страховка по бюджету (задел под раздел 7.1/16.1 «фича-флаг, квоты» на масштабе):
  MICHI_AI_ENABLED=0            — выключить ИИ даже при наличии ключа (фича-флаг);
  MICHI_AI_DAILY_LIMIT=N        — лимит обращений к ИИ на пользователя в сутки
                                  (по умолчанию 200); на публичном хостинге
                                  защищает от того, что один посетитель сожжёт
                                  весь бюджет;
  MICHI_AI_GLOBAL_DAILY_LIMIT=N — общий потолок на всех пользователей в сутки
                                  (по умолчанию без потолка) — страховка владельца.
Кэш-хиты лимит не тратят (они бесплатны) — считаются только реальные запросы.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import threading

CACHE_DIR = pathlib.Path(__file__).resolve().parent.parent / "ai_cache"
DEFAULT_DAILY_LIMIT = 200
_USAGE_FILE = "_usage.json"
# Учёт квоты — read-modify-write одного файла; блокировка спасает от гонки между
# одновременными запросами в пределах процесса (на нескольких воркерах счёт может
# слегка недосчитываться — это лишь страховочный потолок, не биллинг).
_USAGE_LOCK = threading.Lock()

# Реестр провайдеров (7.1). key — env с ключом; model_env — переопределение модели.
_PROVIDERS = {
    "claude": {"key": "ANTHROPIC_API_KEY", "model_env": "MICHI_CLAUDE_MODEL",
               "default_model": "claude-haiku-4-5"},
    "gemini": {"key": "GEMINI_API_KEY", "model_env": "MICHI_GEMINI_MODEL",
               "default_model": "gemini-2.5-flash"},
}

# Классификация ошибки (7.2 п.2). Значения — машинные, ярлыки для UI — на фронте.
CATEGORIES = (
    "particle",          # частица (は/が/を/に/で…)
    "conjugation",       # спряжение глагола/прилагательного
    "vocabulary",        # лексика: не то слово/значение
    "word_order",        # порядок слов
    "kana_orthography",  # орфография каны (длгота, дакутэн, похожие знаки)
    "kanji",             # чтение/значение/запись кандзи
    "other",
)

SYSTEM_PROMPT = (
    "Ты — Сэнсэй, доброжелательный преподаватель японского языка для "
    "русскоязычного новичка уровня JLPT N5. Тебе дают одно задание из приложения, "
    "верный ответ и ошибочный ответ ученика. Объясни ошибку коротко и по делу.\n"
    "Правила:\n"
    "1. Отвечай ТОЛЬКО на русском языке (японские слова можно приводить).\n"
    "2. Никаких приветствий и воды — сразу суть.\n"
    "3. Говори только об этой ошибке в японском; не уходи в другие темы.\n"
    "4. explanation — 2–3 коротких предложения: почему ответ ученика неверен и "
    "почему верный вариант правильный.\n"
    "5. rule — одно мини-правило, которое поможет не ошибиться впредь.\n"
    "6. counterexample — короткий контрпример (фраза с переводом), "
    "по возможности из уже знакомой ученику лексики.\n"
    "7. category — тип ошибки из заданного списка."
)

# Claude: строгий JSON-Schema (additionalProperties запрещены).
_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": list(CATEGORIES)},
        "explanation": {"type": "string"},
        "rule": {"type": "string"},
        "counterexample": {"type": "string"},
    },
    "required": ["category", "explanation", "rule", "counterexample"],
    "additionalProperties": False,
}

# Gemini: подмножество OpenAPI-схемы (без additionalProperties).
_GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": list(CATEGORIES)},
        "explanation": {"type": "string"},
        "rule": {"type": "string"},
        "counterexample": {"type": "string"},
    },
    "required": ["category", "explanation", "rule", "counterexample"],
}


def _provider() -> str:
    """Какой LLM-провайдер активен: явный MICHI_AI_PROVIDER или автоопределение."""
    explicit = os.environ.get("MICHI_AI_PROVIDER", "").strip().lower()
    if explicit in _PROVIDERS:
        return explicit
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    return ""


def _model(provider: str) -> str:
    cfg = _PROVIDERS[provider]
    return os.environ.get(cfg["model_env"]) or cfg["default_model"]


def _have_library(provider: str) -> bool:
    try:
        if provider == "claude":
            import anthropic  # noqa: F401
        elif provider == "gemini":
            from google import genai  # noqa: F401
        else:
            return False
        return True
    except Exception:
        return False


def _enabled() -> bool:
    """Фича-флаг: MICHI_AI_ENABLED=0 выключает ИИ даже при наличии ключа."""
    return os.environ.get("MICHI_AI_ENABLED", "1") != "0"


def _daily_limit() -> int:
    """Лимит на одного пользователя в сутки."""
    try:
        return max(0, int(os.environ.get("MICHI_AI_DAILY_LIMIT", DEFAULT_DAILY_LIMIT)))
    except ValueError:
        return DEFAULT_DAILY_LIMIT


def _global_limit() -> int | None:
    """Общий суточный потолок на всех (None — без потолка)."""
    raw = os.environ.get("MICHI_AI_GLOBAL_DAILY_LIMIT")
    if raw is None:
        return None
    try:
        return max(0, int(raw))
    except ValueError:
        return None


def available() -> bool:
    """Доступен ли ИИ-разбор прямо сейчас (флаг, провайдер, ключ и библиотека)."""
    if not _enabled():
        return False
    provider = _provider()
    if not provider:
        return False
    return bool(os.environ.get(_PROVIDERS[provider]["key"])) and _have_library(provider)


def provider_label() -> str:
    """Человекочитаемое имя активного провайдера — для статуса в настройках."""
    return {"claude": "Claude (Haiku)", "gemini": "Gemini (Flash)"}.get(_provider(), "")


def _today() -> str:
    return datetime.date.today().isoformat()


def _bucket(user_id) -> str:
    """Ключ пользователя в счётчике; None → общий бакет (локальный однопользователь)."""
    return user_id or "_"


def _read_usage() -> dict:
    """Счётчик обращений за сегодня: {date, users:{uid:n}, total:n} (сброс по дате)."""
    try:
        data = json.loads((CACHE_DIR / _USAGE_FILE).read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if data.get("date") != _today():
        return {"date": _today(), "users": {}, "total": 0}
    users = data.get("users") if isinstance(data.get("users"), dict) else {}
    return {"date": _today(), "users": dict(users), "total": int(data.get("total", 0))}


def _bump_usage(user_id=None) -> None:
    with _USAGE_LOCK:
        u = _read_usage()
        key = _bucket(user_id)
        u["users"][key] = int(u["users"].get(key, 0)) + 1
        u["total"] = int(u.get("total", 0)) + 1
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            (CACHE_DIR / _USAGE_FILE).write_text(json.dumps(u), encoding="utf-8")
        except Exception:
            pass


def usage(user_id=None) -> dict:
    """Сводка по дневной квоте пользователя — для статуса в настройках."""
    limit = _daily_limit()
    used = int(_read_usage()["users"].get(_bucket(user_id), 0))
    return {"limit": limit, "used": used, "remaining": max(0, limit - used)}


def _cache_key(context: dict) -> str:
    """Стабильный ключ «тип ошибки × упражнение» для дискового кэша."""
    prov = _provider()
    payload = json.dumps(
        {
            "model": f"{prov}:{_model(prov)}" if prov else "",
            "item_type": context.get("item_type", ""),
            "item_id": context.get("item_id", ""),
            "exercise_type": context.get("exercise_type", ""),
            "prompt": context.get("prompt", ""),
            "correct": context.get("correct_answer", ""),
            "given": context.get("given_answer", ""),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache_path(key: str) -> pathlib.Path:
    return CACHE_DIR / f"{key}.json"


def _read_cache(key: str) -> dict | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_cache(key: str, data: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path(key).write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def _user_message(context: dict) -> str:
    """Компактное описание промаха для модели (i+1: только эта карточка)."""
    lines = []
    title = context.get("title")
    sub = context.get("sub")
    if title:
        lines.append(f"Изучаемый элемент: {title}" + (f" — {sub}" if sub else ""))
    hint = context.get("hint")
    if hint:
        lines.append(f"Справка: {hint}")
    lines.append(f"Тип упражнения: {context.get('exercise_type', '—')}")
    if context.get("prompt"):
        lines.append(f"Задание (стимул): {context['prompt']}")
    choices = context.get("choices") or []
    if choices:
        lines.append("Варианты: " + " / ".join(str(c) for c in choices))
    lines.append(f"Верный ответ: {context.get('correct_answer', '—')}")
    lines.append(f"Ответ ученика (неверный): {context.get('given_answer', '—')}")
    return "\n".join(lines)


def _request_claude(context: dict) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=_model("claude"),
        max_tokens=600,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": _user_message(context)}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
    )
    text = next((b.text for b in resp.content if b.type == "text"), "")
    return json.loads(text)


def _request_gemini(context: dict) -> dict:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model=_model("gemini"),
        contents=_user_message(context),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=_GEMINI_SCHEMA,
            max_output_tokens=800,
            # Flash по умолчанию «думает» и съедает выходной бюджет — для короткого
            # разбора это лишний расход; отключаем, ответ остаётся качественным.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    return json.loads(resp.text)


def _request_explanation(context: dict) -> dict:
    """Сетевой вызов активного провайдера. Вынесен отдельно, чтобы мокать в тестах."""
    if _provider() == "gemini":
        return _request_gemini(context)
    return _request_claude(context)


def explain(context: dict, user_id=None) -> dict:
    """Вернуть разбор ошибки. Сначала кэш, затем сеть.

    Формат ответа: {available, cached, category, explanation, rule, counterexample}.
    При недоступности/сбое — {available: False, error: ...}. Квота считается по
    пользователю (user_id); на масштабе ещё и общий потолок MICHI_AI_GLOBAL_DAILY_LIMIT.
    """
    if not available():
        return {"available": False, "error": "no_api_key"}

    key = _cache_key(context)
    cached = _read_cache(key)
    if cached is not None:
        return {"available": True, "cached": True, **cached}  # бесплатно, лимит не трогаем

    u = _read_usage()
    if int(u["users"].get(_bucket(user_id), 0)) >= _daily_limit():
        return {"available": False, "error": "daily_limit"}
    glimit = _global_limit()
    if glimit is not None and int(u.get("total", 0)) >= glimit:
        return {"available": False, "error": "global_limit"}

    try:
        data = _request_explanation(context)
    except Exception as exc:  # сеть/ключ/сбой — деградируем мягко (попытку не считаем)
        return {"available": False, "error": type(exc).__name__}

    _bump_usage(user_id)  # успешный запрос к ИИ — расходуем единицу квоты пользователя
    result = {
        "category": data.get("category", "other"),
        "explanation": data.get("explanation", ""),
        "rule": data.get("rule", ""),
        "counterexample": data.get("counterexample", ""),
    }
    _write_cache(key, result)
    return {"available": True, "cached": False, **result}
