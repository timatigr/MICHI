# -*- coding: utf-8 -*-
"""Тесты ИИ-разбора ошибок: деградация без ключа и кэш типовых объяснений.

Сеть не трогаем — реальный вызов Claude (_request_explanation) подменяется
заглушкой; проверяем, что повторный одинаковый промах берётся из кэша.
"""
import pytest

from app import ai_tutor, main

_AI_ENV = ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "MICHI_AI_PROVIDER",
           "MICHI_AI_ENABLED", "MICHI_AI_DAILY_LIMIT", "MICHI_AI_GLOBAL_DAILY_LIMIT",
           "MICHI_GEMINI_MODEL", "MICHI_CLAUDE_MODEL")


@pytest.fixture(autouse=True)
def _clean_ai_env(monkeypatch):
    """Каждый тест стартует без ИИ-переменных — независимо от окружения разработчика."""
    for k in _AI_ENV:
        monkeypatch.delenv(k, raising=False)


def _ctx(given="は"):
    return {
        "item_type": "grammar", "item_id": "g01", "exercise_type": "particle_choice",
        "prompt": "わたし＿がくせいです。", "correct_answer": "は",
        "given_answer": given, "choices": ["は", "を", "に"],
    }


def test_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert ai_tutor.available() is False
    assert ai_tutor.explain(_ctx()) == {"available": False, "error": "no_api_key"}


def test_cache_key_sensitive_to_answer():
    a = ai_tutor._cache_key(_ctx(given="を"))
    b = ai_tutor._cache_key(_ctx(given="に"))
    same = ai_tutor._cache_key(_ctx(given="を"))
    assert a == same          # детерминирован
    assert a != b             # разный промах — разный ключ


def test_explain_uses_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(ai_tutor, "CACHE_DIR", tmp_path)
    calls = {"n": 0}

    def fake(context):
        calls["n"] += 1
        return {"category": "particle", "explanation": "は — тема.",
                "rule": "Тема — は.", "counterexample": "これはペンです。"}

    monkeypatch.setattr(ai_tutor, "_request_explanation", fake)

    first = ai_tutor.explain(_ctx())
    assert first["available"] and first["cached"] is False
    assert first["category"] == "particle"

    second = ai_tutor.explain(_ctx())
    assert second["cached"] is True       # из кэша
    assert calls["n"] == 1                # сеть дёрнули один раз


def test_explain_degrades_on_error(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(ai_tutor, "CACHE_DIR", tmp_path)

    def boom(context):
        raise RuntimeError("network down")

    monkeypatch.setattr(ai_tutor, "_request_explanation", boom)
    out = ai_tutor.explain(_ctx())
    assert out["available"] is False and out["error"] == "RuntimeError"


def test_feature_flag_off(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("MICHI_AI_ENABLED", "0")
    assert ai_tutor.available() is False


def test_daily_limit(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("MICHI_AI_DAILY_LIMIT", "1")
    monkeypatch.setattr(ai_tutor, "CACHE_DIR", tmp_path)
    calls = {"n": 0}

    def fake(context):
        calls["n"] += 1
        return {"category": "particle", "explanation": "x", "rule": "y",
                "counterexample": "z"}

    monkeypatch.setattr(ai_tutor, "_request_explanation", fake)

    first = ai_tutor.explain(_ctx("を"))          # тратит 1 из 1
    assert first["available"] and first["cached"] is False

    again = ai_tutor.explain(_ctx("を"))          # кэш — квоту не трогает
    assert again["cached"] is True

    over = ai_tutor.explain(_ctx("に"))           # новый промах — лимит исчерпан
    assert over == {"available": False, "error": "daily_limit"}
    assert calls["n"] == 1                         # к сети ходили один раз
    assert ai_tutor.usage() == {"limit": 1, "used": 1, "remaining": 0}


def test_provider_autodetect(monkeypatch):
    assert ai_tutor._provider() == ""                       # ключей нет
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert ai_tutor._provider() == "claude"
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    assert ai_tutor._provider() == "gemini"                  # gemini приоритетнее при обоих
    monkeypatch.setenv("MICHI_AI_PROVIDER", "claude")
    assert ai_tutor._provider() == "claude"                  # явный выбор побеждает


def test_gemini_dispatch_and_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ai_tutor, "CACHE_DIR", tmp_path)
    assert ai_tutor._provider() == "gemini"
    assert ai_tutor.provider_label() == "Gemini (Flash)"
    calls = {"n": 0}

    def fake_gemini(context):
        calls["n"] += 1
        return {"category": "particle", "explanation": "は — тема.",
                "rule": "Тема — は.", "counterexample": "これはペンです。"}

    # мокаем именно gemini-ветку: диспетчер _request_explanation должен её выбрать
    monkeypatch.setattr(ai_tutor, "_request_gemini", fake_gemini)

    first = ai_tutor.explain(_ctx())
    assert first["available"] and first["cached"] is False
    assert ai_tutor.explain(_ctx())["cached"] is True        # кэш Gemini-разбора
    assert calls["n"] == 1


def test_cache_key_differs_by_provider(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    k_claude = ai_tutor._cache_key(_ctx())
    monkeypatch.setenv("MICHI_AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    assert ai_tutor._cache_key(_ctx()) != k_claude           # разный провайдер — разный кэш


def test_item_type_mapping():
    assert main._item_type_for("particle_choice", "") == "grammar"
    assert main._item_type_for("kanji_reading", "") == "kanji"
    assert main._item_type_for("vocab_choice", "") == "vocab"
    assert main._item_type_for("kana_recognition", "") == "kana"
    assert main._item_type_for("anything", "kanji") == "kanji"  # явный приоритетнее


def test_endpoint_status_and_guard(make_client):
    # Без ключа (env очищен автофикстурой): статус available=False, разбор → 503.
    c = make_client()
    assert c.get("/api/ai/status").json() == {"available": False}
    r = c.post("/api/ai/explain", json={"exercise_type": "particle_choice"})
    assert r.status_code == 503


def _fake_ai(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(ai_tutor, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ai_tutor, "_request_explanation", lambda ctx: {
        "category": "particle", "explanation": "x", "rule": "y", "counterexample": "z"})


def test_quota_is_per_user(monkeypatch, tmp_path):
    # Лимит на пользователя: один посетитель не сжигает квоту другого.
    monkeypatch.setenv("MICHI_AI_DAILY_LIMIT", "1")
    _fake_ai(monkeypatch, tmp_path)

    assert ai_tutor.explain(_ctx("を"), "userA")["cached"] is False   # A тратит свою 1
    assert ai_tutor.explain(_ctx("に"), "userA")["error"] == "daily_limit"
    assert ai_tutor.explain(_ctx("へ"), "userB")["cached"] is False   # B независим
    assert ai_tutor.usage("userA")["remaining"] == 0
    assert ai_tutor.usage("userB")["remaining"] == 0


def test_global_limit_caps_everyone(monkeypatch, tmp_path):
    # Общий потолок защищает бюджет владельца поверх пер-юзерных лимитов.
    monkeypatch.setenv("MICHI_AI_DAILY_LIMIT", "10")
    monkeypatch.setenv("MICHI_AI_GLOBAL_DAILY_LIMIT", "1")
    _fake_ai(monkeypatch, tmp_path)

    assert ai_tutor.explain(_ctx("を"), "a")["cached"] is False       # total=1
    assert ai_tutor.explain(_ctx("に"), "b")["error"] == "global_limit"
