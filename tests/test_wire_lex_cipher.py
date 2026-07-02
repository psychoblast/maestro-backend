"""
Unit 1.8 PROOF tests — Lex (lex-cipher) Anthropic tool_use loop.

Mirrors tests/test_marcus_tool_use.py. Proves that, in /api/chat_stream:

  (a) Lex emits search_clause_library → review_agreement → file_ip_registration
      then a final message; all three mock-first lex_cipher_service functions are
      invoked with the correct args and the stream surfaces a populated `actions`
      event (actions_taken), with LEX_CIPHER_TOOLS passed on every create() call;
  (b) a NON-lex agent (producer-connect) never receives LEX_CIPHER_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never LEX_CIPHER_TOOLS;
  (d) the registry-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries registry_not_connected=True).

Everything is in-process and deterministic. NO network / LLM / filing calls — the
Anthropic client is faked and the lex_cipher_service boundary is exercised through
recording wrappers over the REAL (pure, mock-first) functions.
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
    """Stand-in for async_client.messages.stream(...) — used by the non-Lex path."""
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


# ── (a) Lex runs the tool loop and surfaces actions_taken ────────────────────

def test_lex_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected filing account so file_ip_registration succeeds (no network).
    monkeypatch.setenv("IP_REGISTRY_CONNECTED", "true")

    # Record calls into the REAL (pure) lex_cipher_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, review_calls, file_calls = [], [], []
    real_search = m.lex_cipher_service.search_clause_library
    real_review = m.lex_cipher_service.review_agreement
    real_file   = m.lex_cipher_service.file_ip_registration

    async def rec_search(clause_type="", deal_type=""):
        search_calls.append({"clause_type": clause_type, "deal_type": deal_type})
        return await real_search(clause_type=clause_type, deal_type=deal_type)

    async def rec_review(artist_id, agreement_type="", agreement_text=""):
        review_calls.append({"artist_id": artist_id, "agreement_type": agreement_type,
                             "agreement_text": agreement_text})
        return await real_review(artist_id, agreement_type=agreement_type,
                                 agreement_text=agreement_text)

    async def rec_file(artist_id, work_title, work_type="sound_recording"):
        file_calls.append({"artist_id": artist_id, "work_title": work_title,
                           "work_type": work_type})
        return await real_file(artist_id, work_title, work_type)

    monkeypatch.setattr(m.lex_cipher_service, "search_clause_library", rec_search)
    monkeypatch.setattr(m.lex_cipher_service, "review_agreement",      rec_review)
    monkeypatch.setattr(m.lex_cipher_service, "file_ip_registration",  rec_file)

    # Scripted Anthropic responses: search → review → file → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_clause_library",
                      input={"deal_type": "record_deal"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="review_agreement",
                      input={"agreement_type": "record_deal",
                             "agreement_text": "Label owns the masters in perpetuity."},
                      id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="file_ip_registration",
                      input={"work_title": "Midnight Drive", "work_type": "sound_recording"},
                      id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I reviewed the deal and filed your registration.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Lex.
    def _no_stream(**kw):
        raise AssertionError("Lex must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "lex-cipher",
        "message":   "review my record deal and register my single",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"clause_type": "", "deal_type": "record_deal"}], search_calls
    assert review_calls == [{
        "artist_id": "artist-9", "agreement_type": "record_deal",
        "agreement_text": "Label owns the masters in perpetuity.",
    }], review_calls
    assert file_calls == [{
        "artist_id": "artist-9", "work_title": "Midnight Drive",
        "work_type": "sound_recording",
    }], file_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_clause_library", "review_agreement", "file_ip_registration"], tools_used
    assert actions_evt["registry_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    # record_deal search returns the record_deal clauses from the real library.
    assert "clause(s) found" in by_tool["search_clause_library"]["result"]
    # "in perpetuity" is a HIGH red-flag → do_not_sign.
    assert "do_not_sign" in by_tool["review_agreement"]["result"]
    assert by_tool["file_ip_registration"]["result"] == "registration filed"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, review, file, final.
    assert len(create_calls) == 4
    # LEX_CIPHER_TOOLS passed on every Lex create call (never MARCUS_TOOLS).
    assert all(kw.get("tools") == m.LEX_CIPHER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


# ── (b) Non-Lex agent never gets Lex tools, takes the unchanged path ─────────

def test_non_lex_agent_never_receives_lex_tools(monkeypatch, tmp_path):
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
        "agent_id":  "collab-connect",   # NOT lex-cipher, NOT puppet-master
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-Lex agent must not invoke the tool_use create loop"
    # No actions event for non-Lex agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not LEX tools ──────

def test_marcus_still_uses_marcus_tools_not_lex(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — Lex's gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.LEX_CIPHER_TOOLS


# ── (d) registry_not_connected (missing credential) handled gracefully ───────

def test_lex_registry_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No filing account connected → file_ip_registration raises RegistryNotConnected.
    monkeypatch.delenv("IP_REGISTRY_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="file_ip_registration",
                      input={"work_title": "Unreleased Demo"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a filing account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "lex-cipher",
        "message":   "register my unreleased demo",
        "artist_id": "artist-no-registry",
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
    assert actions_evt["registry_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "registry_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_lex_registry_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("IP_REGISTRY_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="file_ip_registration",
                      input={"work_title": "Old Session"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your filing account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "lex-cipher",
        "message":   "file registration for old session",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["registry_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "registry_auth_expired"
