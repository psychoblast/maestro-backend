"""
PROOF tests — Nadia (ledger-lock) Anthropic tool_use loop.

Mirrors tests/test_wire_vault_keeper.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Nadia emits search_royalty_sources → reconcile_royalty_statement →
      file_tax_document then a final message; all three mock-first
      ledger_lock_service functions are invoked with the correct args and the
      stream surfaces a populated `actions` event (actions_taken), with
      LEDGER_LOCK_TOOLS passed on every create() call;
  (b) a NON-ledger agent (producer-connect) never receives LEDGER_LOCK_TOOLS — it takes
      the unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never LEDGER_LOCK_TOOLS;
  (d) the account-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries ledger_account_not_connected=True);
  (e) expired account auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / tax-filing calls —
the Anthropic client is faked and the ledger_lock_service boundary is exercised
through recording wrappers over the REAL (pure, mock-first) functions.
"""
import importlib
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── Fake Anthropic SDK shapes ────────────────────────────────────────────────

class _Block:
    """Stand-in for an Anthropic content block (text or tool_use)."""
    def __init__(self, type, text=None, name=None, input=None, id=None):
        self.type  = type
        self.text  = text
        self.name  = name
        self.input = input
        self.id    = id


class _Resp:
    """Stand-in for a messages.create(...) response."""
    def __init__(self, content, stop_reason):
        self.content     = content
        self.stop_reason = stop_reason


class _FakeStream:
    """Stand-in for async_client.messages.stream(...) — used by the non-ledger path."""
    def __init__(self, text):
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @property
    def text_stream(self):
        async def _gen():
            yield self._text
        return _gen()


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


def _parse_sse(body: str) -> list:
    events = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:"):].strip()))
    return events


# ── (a) Nadia runs the tool loop and surfaces actions_taken ──────────────────

def test_ledger_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected bookkeeping account so the filing succeeds (no network).
    monkeypatch.setenv("LEDGER_LOCK_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) ledger_lock_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, recon_calls, file_calls = [], [], []
    real_search = m.ledger_lock_service.search_royalty_sources
    real_recon  = m.ledger_lock_service.reconcile_royalty_statement
    real_file   = m.ledger_lock_service.file_tax_document

    async def rec_search(source_type="", region=""):
        search_calls.append({"source_type": source_type, "region": region})
        return await real_search(source_type=source_type, region=region)

    async def rec_recon(artist_id, source_id="", statement_period="", gross_amount=0):
        recon_calls.append({"artist_id": artist_id, "source_id": source_id,
                            "statement_period": statement_period, "gross_amount": gross_amount})
        return await real_recon(artist_id, source_id=source_id,
                                statement_period=statement_period, gross_amount=gross_amount)

    async def rec_file(artist_id, filing_type, period, amount=0):
        file_calls.append({"artist_id": artist_id, "filing_type": filing_type,
                           "period": period, "amount": amount})
        return await real_file(artist_id, filing_type, period, amount)

    monkeypatch.setattr(m.ledger_lock_service, "search_royalty_sources",      rec_search)
    monkeypatch.setattr(m.ledger_lock_service, "reconcile_royalty_statement", rec_recon)
    monkeypatch.setattr(m.ledger_lock_service, "file_tax_document",           rec_file)

    # Scripted Anthropic responses: search → reconcile → file → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_royalty_sources",
                      input={"source_type": "streaming", "region": "foreign"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="reconcile_royalty_statement",
                      input={"source_id": "src-streaming-foreign",
                             "statement_period": "2026-Q1", "gross_amount": 10000}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="file_tax_document",
                      input={"filing_type": "quarterly_estimate", "period": "2026-Q1",
                             "amount": 2100}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the source, reconciled your statement, and filed the estimate.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Nadia.
    def _no_stream(**kw):
        raise AssertionError("ledger-lock must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ledger-lock",
        "message":   "reconcile my foreign streaming statement and file the estimate",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"source_type": "streaming", "region": "foreign"}], search_calls
    assert recon_calls == [{
        "artist_id": "artist-9", "source_id": "src-streaming-foreign",
        "statement_period": "2026-Q1", "gross_amount": 10000,
    }], recon_calls
    assert file_calls == [{
        "artist_id": "artist-9", "filing_type": "quarterly_estimate",
        "period": "2026-Q1", "amount": 2100,
    }], file_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_royalty_sources", "reconcile_royalty_statement",
        "file_tax_document",
    ], tools_used
    assert actions_evt["ledger_account_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "source(s) found" in by_tool["search_royalty_sources"]["result"]
    # period present, source known, positive gross → reconciled / record.
    assert "reconciled=True" in by_tool["reconcile_royalty_statement"]["result"]
    assert "record" in by_tool["reconcile_royalty_statement"]["result"]
    assert by_tool["file_tax_document"]["result"] == "tax document filed"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, reconcile, file, final.
    assert len(create_calls) == 4
    # LEDGER_LOCK_TOOLS passed on every ledger create call (never other toolsets).
    assert all(kw.get("tools") == m.LEDGER_LOCK_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEX_CIPHER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.FUND_PHANTOM_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.RIGHTS_PULSE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.BORDER_ROYALTY_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MECH_LEDGER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VAULT_KEEPER_TOOLS for kw in create_calls)


# ── (b) Non-ledger agent never gets ledger tools, takes the unchanged path ────

def test_non_ledger_agent_never_receives_ledger_tools(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return _Resp([_Block("text", text="x")], "end_turn")

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    monkeypatch.setattr(m.async_client.messages, "stream",
                        lambda **kw: _FakeStream("Here is some general guidance for you."))

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "music-edu",   # NOT ledger-lock, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-ledger agent must not invoke the tool_use create loop"
    # No actions event for non-ledger agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not ledger tools ────

def test_marcus_still_uses_marcus_tools_not_ledger(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return _Resp([_Block("text", text="On it.")], "end_turn")

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    monkeypatch.setattr(m.async_client.messages, "stream",
                        lambda **kw: (_ for _ in ()).throw(
                            AssertionError("Marcus must not use messages.stream")))

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "puppet-master",
        "message":   "what's my next move",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200

    assert len(create_calls) == 1
    # Marcus keeps its own toolset — the ledger gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.LEDGER_LOCK_TOOLS


# ── (d) ledger_account_not_connected (missing credential) handled gracefully ──

def test_ledger_account_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No bookkeeping account connected → file raises LedgerAccountNotConnected.
    monkeypatch.delenv("LEDGER_LOCK_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="file_tax_document",
                      input={"filing_type": "annual_return", "period": "2025",
                             "amount": 4200}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a bookkeeping account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ledger-lock",
        "message":   "file my annual return",
        "artist_id": "artist-no-account",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Stream completes without crashing.
    assert "done" in types
    assert "error" not in types, types
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["ledger_account_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "ledger_account_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_ledger_account_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("LEDGER_LOCK_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="file_tax_document",
                      input={"filing_type": "1099", "period": "2025",
                             "amount": 800}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your bookkeeping-account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ledger-lock",
        "message":   "file my 1099",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["ledger_account_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "ledger_account_auth_expired"
