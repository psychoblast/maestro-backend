"""
PROOF tests — Victor (vault-keeper) Anthropic tool_use loop.

Mirrors tests/test_wire_mech_ledger.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Victor emits search_budget_templates → build_project_budget →
      schedule_expense_payment then a final message; all three mock-first
      vault_keeper_service functions are invoked with the correct args and the
      stream surfaces a populated `actions` event (actions_taken), with
      VAULT_KEEPER_TOOLS passed on every create() call;
  (b) a NON-vault agent (producer-connect) never receives VAULT_KEEPER_TOOLS — it takes
      the unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never VAULT_KEEPER_TOOLS;
  (d) the account-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries vault_account_not_connected=True);
  (e) expired account auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / banking calls —
the Anthropic client is faked and the vault_keeper_service boundary is exercised
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
    """Stand-in for async_client.messages.stream(...) — used by the non-vault path."""
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


# ── (a) Victor runs the tool loop and surfaces actions_taken ─────────────────

def test_vault_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected operating account so the payment succeeds (no network).
    monkeypatch.setenv("VAULT_KEEPER_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) vault_keeper_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, build_calls, pay_calls = [], [], []
    real_search = m.vault_keeper_service.search_budget_templates
    real_build  = m.vault_keeper_service.build_project_budget
    real_pay    = m.vault_keeper_service.schedule_expense_payment

    async def rec_search(project_type="", tier=""):
        search_calls.append({"project_type": project_type, "tier": tier})
        return await real_search(project_type=project_type, tier=tier)

    async def rec_build(artist_id, template_id="", project_name="", estimated_revenue=0):
        build_calls.append({"artist_id": artist_id, "template_id": template_id,
                            "project_name": project_name, "estimated_revenue": estimated_revenue})
        return await real_build(artist_id, template_id=template_id,
                                project_name=project_name, estimated_revenue=estimated_revenue)

    async def rec_pay(artist_id, payee, amount, category=""):
        pay_calls.append({"artist_id": artist_id, "payee": payee,
                          "amount": amount, "category": category})
        return await real_pay(artist_id, payee, amount, category)

    monkeypatch.setattr(m.vault_keeper_service, "search_budget_templates",   rec_search)
    monkeypatch.setattr(m.vault_keeper_service, "build_project_budget",      rec_build)
    monkeypatch.setattr(m.vault_keeper_service, "schedule_expense_payment",  rec_pay)

    # Scripted Anthropic responses: search → build → pay → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_budget_templates",
                      input={"project_type": "release", "tier": "starter"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_project_budget",
                      input={"template_id": "budget-single-release",
                             "project_name": "New Single", "estimated_revenue": 10000}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="schedule_expense_payment",
                      input={"payee": "Studio X", "amount": 3000,
                             "category": "production"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found a template, built your budget, and scheduled the payment.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Victor.
    def _no_stream(**kw):
        raise AssertionError("vault-keeper must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "vault-keeper",
        "message":   "budget my single and pay the studio",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"project_type": "release", "tier": "starter"}], search_calls
    assert build_calls == [{
        "artist_id": "artist-9", "template_id": "budget-single-release",
        "project_name": "New Single", "estimated_revenue": 10000,
    }], build_calls
    assert pay_calls == [{
        "artist_id": "artist-9", "payee": "Studio X",
        "amount": 3000, "category": "production",
    }], pay_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_budget_templates", "build_project_budget",
        "schedule_expense_payment",
    ], tools_used
    assert actions_evt["vault_account_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "template(s) found" in by_tool["search_budget_templates"]["result"]
    # name present, template known, positive revenue → viable / proceed.
    assert "viable=True" in by_tool["build_project_budget"]["result"]
    assert "proceed" in by_tool["build_project_budget"]["result"]
    assert by_tool["schedule_expense_payment"]["result"] == "payment scheduled"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, build, pay, final.
    assert len(create_calls) == 4
    # VAULT_KEEPER_TOOLS passed on every vault create call (never other toolsets).
    assert all(kw.get("tools") == m.VAULT_KEEPER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEX_CIPHER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.FUND_PHANTOM_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.RIGHTS_PULSE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.BORDER_ROYALTY_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MECH_LEDGER_TOOLS for kw in create_calls)


# ── (b) Non-vault agent never gets vault tools, takes the unchanged path ──────

def test_non_vault_agent_never_receives_vault_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT vault-keeper, NOT mech-ledger, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-vault agent must not invoke the tool_use create loop"
    # No actions event for non-vault agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not vault tools ─────

def test_marcus_still_uses_marcus_tools_not_vault(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the vault gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.VAULT_KEEPER_TOOLS


# ── (d) vault_account_not_connected (missing credential) handled gracefully ───

def test_vault_account_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No operating account connected → schedule raises VaultAccountNotConnected.
    monkeypatch.delenv("VAULT_KEEPER_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="schedule_expense_payment",
                      input={"payee": "Videographer", "amount": 1500,
                             "category": "visuals"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect an operating account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "vault-keeper",
        "message":   "pay my videographer",
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
    assert actions_evt["vault_account_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "vault_account_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_vault_account_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("VAULT_KEEPER_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="schedule_expense_payment",
                      input={"payee": "Tour Bus Co", "amount": 5000,
                             "category": "travel"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your operating-account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "vault-keeper",
        "message":   "pay the tour bus company",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["vault_account_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "vault_account_auth_expired"
