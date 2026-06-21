"""
PROOF tests for the shared knowledge bank.

Goal: show that an UNPAIRED agent (no home domain) can pull knowledge from a
domain it was never paired with, and that PAIRED agents get their home domain by
default and can reach across domains. Also exercises the mock /api/bank/consult
route end-to-end.

All in-process. NO network / LLM calls.
"""
import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from knowledge_bank.agent_home import consult_for_agent, home_domain
from entity_wall_terms import assert_no_forbidden_terms


# ── direct (no HTTP) proofs ──────────────────────────────────────────────────────

def test_homed_agent_reaches_beyond_its_home_domain():
    """
    THE PROOF: merch-empire is homed to bizdev yet a royalty/publishing query ALSO
    reaches finance_royalties and publishing — domains it was never paired with.
    Cross-domain retrieval works regardless of an agent's home.
    """
    result = consult_for_agent(
        "merch-empire",
        "how do mechanical royalties and publishing splits work on a track bundled with my merch",
    )
    assert result["home_domain"] == "bizdev"
    assert result["agent"] == "merch-empire"
    assert result["domains"][0] == "bizdev"          # home is always first
    assert "finance_royalties" in result["domains"]  # cross-domain match
    assert "publishing" in result["domains"]          # cross-domain match
    assert result["knowledge"].strip()


def test_homeless_slug_with_no_keyword_match_gets_nothing():
    """An unmapped slug + a query with no triggers → no domains, empty knowledge.

    Every agent in the roster now has a home, so this exercises the home=None path
    via a slug that is not in AGENT_HOME at all.
    """
    result = consult_for_agent("not-a-real-agent", "good morning, how are you today")
    assert result["home_domain"] is None
    assert result["domains"] == []
    assert result["knowledge"] == ""


def test_homed_agent_no_keyword_match_returns_home_only():
    """A homed agent + a query with no triggers → exactly its home domain."""
    result = consult_for_agent("storefront", "good morning, how are you today")
    assert result["home_domain"] == "bizdev"
    assert result["domains"] == ["bizdev"]
    assert result["knowledge"].strip()


def test_home_domain_lookup():
    assert home_domain("royalty-doctor") == "finance_royalties"
    assert home_domain("ar-scout") == "ar"
    assert home_domain("merch-empire") == "bizdev"
    assert home_domain("storefront") == "bizdev"
    assert home_domain("not-a-real-agent") is None


def test_paired_agent_gets_home_by_default():
    """ar-scout always includes its home domain (ar), even on a generic query."""
    result = consult_for_agent("ar-scout", "general question with no specific triggers")
    assert result["home_domain"] == "ar"
    assert "ar" in result["domains"]
    assert result["domains"][0] == "ar"


def test_paired_agent_cross_domain():
    """ar-scout asking about sync reaches BOTH its home (ar) and sync."""
    result = consult_for_agent("ar-scout", "what about the sync licensing angle")
    assert "ar" in result["domains"]
    assert "sync" in result["domains"]


def test_consult_for_agent_respects_max_domains():
    query = "contract clause, sync placement, royalty splits, tour booking, brand sponsor, mixing"
    result = consult_for_agent("merch-empire", query, max_domains=3)
    assert len(result["domains"]) <= 3


# ── HTTP route proof ─────────────────────────────────────────────────────────────

def _load_app(monkeypatch, tmp_path, *, mock_mode: str = "true"):
    monkeypatch.setenv("ANTHROPIC_API_KEY",      "sk-ant-test")
    monkeypatch.setenv("BANK_CONSULT_MOCK_MODE", mock_mode)
    monkeypatch.setenv("DB_PATH",                str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",           "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",        str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",            str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",     "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        return TestClient(m.app)


def test_route_homed_cross_domain_returns_200(monkeypatch, tmp_path):
    """POST /api/bank/consult for a homed agent + cross-domain query → 200."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/bank/consult", json={
        "agent": "merch-empire",
        "query": "mechanical royalties and publishing splits for a merch bundle",
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mock"] is True
    assert body["agent"] == "merch-empire"
    assert body["home_domain"] == "bizdev"
    assert "finance_royalties" in body["domains"]
    assert "publishing" in body["domains"]
    assert body["knowledge"].strip()


def test_route_paired_agent_includes_home(monkeypatch, tmp_path):
    """POST for a paired agent always returns its home domain first."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/bank/consult", json={
        "agent": "ar-scout",
        "query": "what about the sync licensing angle",
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["home_domain"] == "ar"
    assert body["domains"][0] == "ar"
    assert "sync" in body["domains"]


def test_route_no_match_no_home_empty(monkeypatch, tmp_path):
    """Unmapped slug + irrelevant query → 200, no domains, empty knowledge."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/bank/consult", json={
        "agent": "not-a-real-agent",
        "query": "the weather is lovely today",
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["home_domain"] is None
    assert body["domains"] == []
    assert body["knowledge"] == ""


# ── entity safety ────────────────────────────────────────────────────────────────

def test_proof_knowledge_has_no_forbidden_terms():
    """Knowledge assembled across the proof calls leaks no provenance markers."""
    calls = [
        ("merch-empire", "mechanical royalties and publishing splits for a merch bundle"),
        ("ar-scout",     "what about the sync licensing angle"),
        ("royalty-doctor", "statement analysis and recoup of the advance"),
        ("storefront",   "tour booking and venue rider for a pop-up show"),
    ]
    for agent, query in calls:
        result = consult_for_agent(agent, query)
        assert_no_forbidden_terms(result["knowledge"])
