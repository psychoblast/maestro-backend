"""
Report 3 (M5) fix — Marcus `search_curators` must not advertise filters it
never applies.

The curators table is keyed on genre/tier; there are no platform or follower
columns. The tool schema previously accepted `platform` and `min_followers` and
silently dropped them, so the model could pass constraints that were quietly
ignored (over-broad results, no signal). The honest fix REMOVES those two params
from the schema entirely — we never advertise a filter that isn't applied.

These tests lock:
  1. the schema no longer carries `platform` / `min_followers` (and the
     description no longer mentions them), so the footgun cannot silently return;
  2. the real genre/tier filtering at the service layer still works.
"""
import importlib
import json
import sqlite3
from unittest.mock import MagicMock, patch

import pytest


def _load_main(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY",      "sk-ant-test")
    monkeypatch.setenv("BANK_CONSULT_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",                str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",           "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",        str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",            str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",     "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
    return m


# ── 1. schema honesty: the two silently-dropped params are gone ──────────────

def _search_curators_schema(m):
    tools = {t["name"]: t for t in m.MARCUS_TOOLS}
    assert "search_curators" in tools, "search_curators must remain a Marcus tool"
    return tools["search_curators"]


def test_search_curators_schema_has_no_platform_param(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    props = _search_curators_schema(m)["input_schema"]["properties"]
    assert "platform" not in props, (
        "platform was a silently-dropped filter (no platform column) — it must "
        "not be advertised in the schema"
    )


def test_search_curators_schema_has_no_min_followers_param(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    props = _search_curators_schema(m)["input_schema"]["properties"]
    assert "min_followers" not in props, (
        "min_followers was a silently-dropped filter (no followers column) — it "
        "must not be advertised in the schema"
    )


def test_search_curators_schema_keeps_genre(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    props = _search_curators_schema(m)["input_schema"]["properties"]
    assert "genre" in props, "genre is the real, applied filter and must remain"


def test_search_curators_description_drops_dropped_axes(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    desc = _search_curators_schema(m)["description"].lower()
    assert "platform" not in desc, "description must not advertise platform filtering"
    assert "follower" not in desc, "description must not advertise follower filtering"


# ── 2. regression guard: genre/tier filtering at the service layer still works ──

def _seed_curators_db(path):
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE curators (id TEXT, name TEXT, outlet TEXT, genres TEXT, "
        "tier TEXT, contact_email TEXT, notes TEXT, last_pitched_at TEXT, "
        "response_rate REAL, created_at TEXT)"
    )
    rows = [
        ("c1", "Ada", "OutletA", json.dumps(["indie", "pop"]), "A", "a@x.com", "", "", 0.9, ""),
        ("c2", "Ben", "OutletB", json.dumps(["indie", "rock"]), "B", "b@x.com", "", "", 0.5, ""),
        ("c3", "Cal", "OutletC", json.dumps(["jazz"]),          "A", "c@x.com", "", "", 0.7, ""),
    ]
    conn.executemany("INSERT INTO curators VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


@pytest.fixture
def curators_db(tmp_path, monkeypatch):
    import pitch_service
    db = tmp_path / "curators.db"
    _seed_curators_db(db)
    monkeypatch.setattr(pitch_service, "_DB_PATH", db)
    return pitch_service


def test_db_list_curators_genre_filter(curators_db):
    ids = {r["id"] for r in curators_db._db_list_curators(genre="indie")}
    assert ids == {"c1", "c2"}, "genre filter must match indie curators only"


def test_db_list_curators_tier_filter(curators_db):
    ids = {r["id"] for r in curators_db._db_list_curators(tier="A")}
    assert ids == {"c1", "c3"}, "tier filter must match tier-A curators only"


def test_db_list_curators_genre_and_tier_combine(curators_db):
    ids = {r["id"] for r in curators_db._db_list_curators(genre="indie", tier="A")}
    assert ids == {"c1"}, "genre+tier must AND-combine"
