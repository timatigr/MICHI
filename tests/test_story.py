# -*- coding: utf-8 -*-
"""«Свиток истории» 物語: инвариант i+1 — глава собрана только из изученного.

Зеркало проверки уроков лексики (registry.requires): каждое содержательное слово
главы должно быть введено к моменту её открытия, а «клей» — только из
ALLOWED_LITERALS. Опечатка в id слова тоже ловится здесь (до фронта)."""
from app.content import story, vocab_n5


def _known_word_ids_through(requires):
    """Слова, изученные к открытию главы: уроки лексики разблокируются
    последовательно, поэтому известно всё до последнего из requires включительно."""
    order = [l["id"] for l in vocab_n5.LESSONS]
    last = max(order.index(r) for r in requires)
    known = set()
    for l in vocab_n5.LESSONS[: last + 1]:
        known.update(l["words"])
    return known


def test_requires_reference_real_lessons():
    ids = {l["id"] for l in vocab_n5.LESSONS}
    for ch in story.CHAPTERS:
        assert ch["requires"], f"{ch['id']}: пустой requires"
        for r in ch["requires"]:
            assert r in ids, f"{ch['id']}: requires ссылается на несуществующий урок {r}"


def test_chapters_use_only_learned_words():
    for ch in story.CHAPTERS:
        known = _known_word_ids_through(ch["requires"])
        for wid in story.content_word_ids(ch):
            assert wid in vocab_n5.WORD_BY_ID, f"{ch['id']}: неизвестное слово {wid!r}"
            assert wid in known, f"{ch['id']}: слово {wid!r} не изучено к моменту главы (i+1)"


def test_literals_are_allowed():
    """Каждый токен — либо id изученного слова, либо литерал из белого списка."""
    for ch in story.CHAPTERS:
        for scene in ch["scenes"]:
            for t in scene["t"]:
                assert t in vocab_n5.WORD_BY_ID or t in story.ALLOWED_LITERALS, (
                    f"{ch['id']}: токен {t!r} — не слово и не разрешённый литерал")


def test_render_scene_builds_kana():
    for ch in story.CHAPTERS:
        for scene in ch["scenes"]:
            r = story.render_scene(scene)
            assert r["jp"] and r["reading"] == r["jp"] and r["tts"] == r["jp"]
            assert r["ru"]


def test_chapters_for_unlocks_and_renders():
    """Открытие главы и сборка сцен (chapters_for — чистая логика эндпоинта)."""
    assert all(not c["unlocked"] for c in story.chapters_for(set()))
    ch1 = story.CHAPTER_BY_ID["ch1"]
    by = {c["id"]: c for c in story.chapters_for(set(ch1["requires"]))}
    assert by["ch1"]["unlocked"] and by["ch1"]["scenes"]
    jp = by["ch1"]["scenes"][0]["jp"]
    assert jp and not any("a" <= c.lower() <= "z" for c in jp)  # без латиницы-id
    assert by["ch2"]["unlocked"] is False                       # его уроки не пройдены


def test_story_endpoint_locks_for_fresh_user(client):
    r = client.get("/api/story")
    assert r.status_code == 200
    chapters = r.json()["chapters"]
    assert len(chapters) == len(story.CHAPTERS)
    # У нового пользователя прогресса нет → все главы закрыты, сцены не раскрыты.
    assert all(not c["unlocked"] and c["scenes"] == [] for c in chapters)
