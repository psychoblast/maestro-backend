"""
Report 4 fix — Jade's `suggest_crowdfunding` was built and unit-tested in
fund_phantom_service but NEVER DISPATCHED: it was absent from FUND_PHANTOM_TOOLS
and from the _execute_fund_phantom_tool dispatch, so Jade could never call it.

This unit adds the schema entry + dispatch branch (following Jade's read/consult
pattern: return contract (result, summary, portal_not_connected); NOT portal-gated).

These tests lock:
  1. the tool appears in the schema Jade receives (by name);
  2. the EXACT Jade tool roster (names + count) — this unit owns that invariant;
  3. dispatch reaches the REAL fund_phantom_service.suggest_crowdfunding and
     returns its result verbatim with portal_not_connected=False.
"""
import asyncio
import importlib
from unittest.mock import MagicMock, patch

import fund_phantom_service as fps


def _run(coro):
    return asyncio.run(coro)


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


# ── 1. tool is in the schema Jade receives ───────────────────────────────────

def test_suggest_crowdfunding_in_tool_list(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.FUND_PHANTOM_TOOLS]
    assert "suggest_crowdfunding" in names, "suggest_crowdfunding must be dispatchable"


def test_suggest_crowdfunding_schema_shape(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    tool = next(t for t in m.FUND_PHANTOM_TOOLS if t["name"] == "suggest_crowdfunding")
    props = tool["input_schema"]["properties"]
    assert "qualifies_for_grants" in props
    assert "complements_grant" in props
    assert tool["input_schema"].get("required") == ["qualifies_for_grants"]


# ── 2. EXACT Jade roster — this unit owns the tool count/name invariant ───────

def test_fund_phantom_exact_tool_roster(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.FUND_PHANTOM_TOOLS]
    assert names == [
        "search_grant_programs",
        "check_eligibility",
        "submit_grant_application",
        "lookup_grant_deadline",
        "build_grant_application_scaffold",
        "suggest_crowdfunding",
    ], names
    assert len(m.FUND_PHANTOM_TOOLS) == 6


# ── 3. dispatch reaches the REAL function and returns its result verbatim ─────

def test_dispatch_reaches_real_function_raise_case(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    result, summary, portal_not_connected = _run(
        m._execute_fund_phantom_tool(
            "suggest_crowdfunding",
            {"qualifies_for_grants": False},
            "artist-1",
        )
    )
    # Identical to calling the real service directly → dispatch really wired to it.
    expected = fps.suggest_crowdfunding(qualifies_for_grants=False)
    assert result == expected
    assert result["raise"] is True
    assert len(result["platforms"]) == 6         # six crowdfunding records surfaced
    assert portal_not_connected is False         # read/consult, never portal-gated
    assert summary["result"].startswith("raise=True")


def test_dispatch_reaches_real_function_quiet_case(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    result, summary, portal_not_connected = _run(
        m._execute_fund_phantom_tool(
            "suggest_crowdfunding",
            {"qualifies_for_grants": True, "complements_grant": False},
            "artist-1",
        )
    )
    expected = fps.suggest_crowdfunding(qualifies_for_grants=True, complements_grant=False)
    assert result == expected
    assert result["raise"] is False
    assert result["platforms"] == []
    assert portal_not_connected is False


def test_dispatch_complements_case(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    result, _summary, portal_not_connected = _run(
        m._execute_fund_phantom_tool(
            "suggest_crowdfunding",
            {"qualifies_for_grants": True, "complements_grant": True},
            "artist-1",
        )
    )
    assert result["raise"] is True
    assert len(result["platforms"]) == 6
    assert portal_not_connected is False
