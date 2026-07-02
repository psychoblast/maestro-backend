"""
PROOF tests — Ray (rights-pulse) Anthropic tool_use loop.

Mirrors tests/test_marcus_tool_use.py / tests/test_wire_fund_phantom.py. Proves
that, in /api/chat_stream:

  (a) Ray emits search_pro_organizations → check_registration_status → register_work
      then a final message; all three mock-first rights_pulse_service functions are
      invoked with the correct args and the stream surfaces a populated `actions`
      event (actions_taken), with RIGHTS_PULSE_TOOLS passed on every create() call;
  (b) a NON-rights agent (producer-connect) never receives RIGHTS_PULSE_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never RIGHTS_PULSE_TOOLS;
  (d) the pro-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries pro_not_connected=True);
  (e) expired PRO auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / registration calls —
the Anthropic client is faked and the rights_pulse_service boundary is exercised
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
    """Stand-in for async_client.messages.stream(...) — used by the non-rights path."""
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


# ── (a) Ray runs the tool loop and surfaces actions_taken ────────────────────

def test_rights_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected PRO account so register_work succeeds (no network).
    monkeypatch.setenv("PRO_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) rights_pulse_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, check_calls, register_calls = [], [], []
    real_search   = m.rights_pulse_service.search_pro_organizations
    real_check    = m.rights_pulse_service.check_registration_status
    real_register = m.rights_pulse_service.register_work

    async def rec_search(territory="", org_type=""):
        search_calls.append({"territory": territory, "org_type": org_type})
        return await real_search(territory=territory, org_type=org_type)

    async def rec_check(artist_id, work_title="", pro_id="", writer_share=0):
        check_calls.append({"artist_id": artist_id, "work_title": work_title,
                            "pro_id": pro_id, "writer_share": writer_share})
        return await real_check(artist_id, work_title=work_title,
                                pro_id=pro_id, writer_share=writer_share)

    async def rec_register(artist_id, work_title, pro_id, writer_share=0):
        register_calls.append({"artist_id": artist_id, "work_title": work_title,
                               "pro_id": pro_id, "writer_share": writer_share})
        return await real_register(artist_id, work_title, pro_id, writer_share)

    monkeypatch.setattr(m.rights_pulse_service, "search_pro_organizations",   rec_search)
    monkeypatch.setattr(m.rights_pulse_service, "check_registration_status", rec_check)
    monkeypatch.setattr(m.rights_pulse_service, "register_work",             rec_register)

    # Scripted Anthropic responses: search → check → register → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_pro_organizations",
                      input={"territory": "US", "org_type": "performing_rights"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="check_registration_status",
                      input={"work_title": "Midnight Run", "pro_id": "pro-ascap",
                             "writer_share": 100}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="register_work",
                      input={"work_title": "Midnight Run", "pro_id": "pro-ascap",
                             "writer_share": 100}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found your PRO, confirmed the work is ready, and registered it.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Ray.
    def _no_stream(**kw):
        raise AssertionError("rights-pulse must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "rights-pulse",
        "message":   "get my song registered with the right PRO",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"territory": "US", "org_type": "performing_rights"}], search_calls
    assert check_calls == [{
        "artist_id": "artist-9", "work_title": "Midnight Run",
        "pro_id": "pro-ascap", "writer_share": 100,
    }], check_calls
    assert register_calls == [{
        "artist_id": "artist-9", "work_title": "Midnight Run",
        "pro_id": "pro-ascap", "writer_share": 100,
    }], register_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_pro_organizations", "check_registration_status", "register_work"], tools_used
    assert actions_evt["pro_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "PRO(s) found" in by_tool["search_pro_organizations"]["result"]
    # title present, ascap known, 100 is a valid share → ready / register.
    assert "ready=True" in by_tool["check_registration_status"]["result"]
    assert "register" in by_tool["check_registration_status"]["result"]
    assert by_tool["register_work"]["result"] == "work registered"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, check, register, final.
    assert len(create_calls) == 4
    # RIGHTS_PULSE_TOOLS passed on every rights create call (never other toolsets).
    assert all(kw.get("tools") == m.RIGHTS_PULSE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEX_CIPHER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.FUND_PHANTOM_TOOLS for kw in create_calls)


# ── (b) Non-rights agent never gets rights tools, takes the unchanged path ────

def test_non_rights_agent_never_receives_rights_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT rights-pulse, NOT fund-phantom, NOT lex-cipher, NOT puppet-master
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-rights agent must not invoke the tool_use create loop"
    # No actions event for non-rights agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not rights tools ───

def test_marcus_still_uses_marcus_tools_not_rights(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the rights gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.RIGHTS_PULSE_TOOLS


# ── (d) pro_not_connected (missing credential) handled gracefully ────────────

def test_rights_pro_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No PRO account connected → register_work raises ProAccountNotConnected.
    monkeypatch.delenv("PRO_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="register_work",
                      input={"work_title": "Skyline", "pro_id": "pro-bmi",
                             "writer_share": 50}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a PRO account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "rights-pulse",
        "message":   "register my new single",
        "artist_id": "artist-no-pro",
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
    assert actions_evt["pro_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "pro_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_rights_pro_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("PRO_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="register_work",
                      input={"work_title": "Afterglow", "pro_id": "pro-prs",
                             "writer_share": 75}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your PRO account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "rights-pulse",
        "message":   "register my track",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["pro_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "pro_auth_expired"
