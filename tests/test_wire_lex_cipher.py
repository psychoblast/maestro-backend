"""
PROOF tests — Lex (lex-cipher) Anthropic tool_use loop, DOC-WRITER Option B.

Proves that, in /api/chat_stream:

  (a) Lex emits lookup_legal_concepts → build_legal_doc_scaffold then a final
      message; both legal-education lex_cipher_service functions are invoked with
      the correct args and the stream surfaces a populated `actions` event, with
      LEX_CIPHER_TOOLS passed on every create() call and registry_not_connected
      ALWAYS False (the old IP-registry gate is retired);
  (b) a NON-lex agent never receives LEX_CIPHER_TOOLS — it takes the unchanged
      streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never LEX_CIPHER_TOOLS;
  (d) THE ONE RULE survives the loop: the scaffold tool_result fed back to the
      model carries the FOR YOUR LAWYER framing and no signable-assurance language.

Everything is in-process and deterministic. NO network / LLM calls — the Anthropic
client is faked and the lex_cipher_service boundary is exercised through recording
wrappers over the REAL (pure) functions. This file NEVER asserts generated prose;
the final assistant text is scripted.
"""
import importlib
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import legal_data as ld

FYL = ld.FOR_YOUR_LAWYER


class _Block:
    def __init__(self, type, text=None, name=None, input=None, id=None):
        self.type = type
        self.text = text
        self.name = name
        self.input = input
        self.id = id


class _Resp:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class _FakeStream:
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

    lookup_calls, build_calls = [], []
    real_lookup = m.lex_cipher_service.lookup_legal_concepts
    real_build  = m.lex_cipher_service.build_legal_doc_scaffold

    async def rec_lookup(agreement_type="", clause_term="", flag_key="", jurisdiction_key=""):
        lookup_calls.append({"agreement_type": agreement_type, "clause_term": clause_term,
                             "flag_key": flag_key, "jurisdiction_key": jurisdiction_key})
        return await real_lookup(agreement_type=agreement_type, clause_term=clause_term,
                                 flag_key=flag_key, jurisdiction_key=jurisdiction_key)

    async def rec_build(doc_type="", inputs=None):
        build_calls.append({"doc_type": doc_type, "inputs": inputs})
        return await real_build(doc_type=doc_type, inputs=inputs)

    monkeypatch.setattr(m.lex_cipher_service, "lookup_legal_concepts", rec_lookup)
    monkeypatch.setattr(m.lex_cipher_service, "build_legal_doc_scaffold", rec_build)

    scaffold_input = {
        "agreement_type": "recording_contract",
        "jurisdiction": "United States",
        "deal_points": "One album, 360 on merch.",
        "contract_text": "ARTIST CONTRACT TEXT",
    }
    responses = [
        _Resp([_Block("tool_use", name="lookup_legal_concepts",
                      input={"agreement_type": "recording_contract"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_legal_doc_scaffold",
                      input={"doc_type": "contract_review_brief", "inputs": scaffold_input},
                      id="t2")], "tool_use"),
        _Resp([_Block("text", text="Here is a brief to take to your lawyer.")], "end_turn"),
    ]
    create_calls = []
    tool_result_payloads = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        # Capture the tool_result content fed back on the 2nd/3rd round-trips.
        for msg in kwargs.get("messages", []):
            if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                for blk in msg["content"]:
                    if isinstance(blk, dict) and blk.get("type") == "tool_result":
                        tool_result_payloads.append(blk["content"])
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Lex must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "lex-cipher",
        "message":   "prep a review brief for my record deal",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert lookup_calls == [{"agreement_type": "recording_contract", "clause_term": "",
                             "flag_key": "", "jurisdiction_key": ""}], lookup_calls
    assert build_calls == [{"doc_type": "contract_review_brief", "inputs": scaffold_input}], build_calls

    assert "actions" in types and "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["lookup_legal_concepts", "build_legal_doc_scaffold"], tools_used
    assert actions_evt["registry_not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "match(es)" in by_tool["lookup_legal_concepts"]["result"]
    assert "scaffold_ready" in by_tool["build_legal_doc_scaffold"]["result"]

    # Three create() round-trips; LEX tools on every one (never MARCUS_TOOLS).
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.LEX_CIPHER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)

    # (d) THE ONE RULE survives into the tool_result fed back to the model.
    scaffold_payload = next(p for p in tool_result_payloads if "scaffold_ready" in p)
    assert FYL in scaffold_payload  # FOR YOUR LAWYER framing rode through
    for banned in ("safe to sign", "this contract is fine", "standard to sign"):
        assert banned not in scaffold_payload.lower()


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
        "agent_id":  "music-edu",
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert create_calls == [], "non-Lex agent must not invoke the tool_use create loop"
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
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.LEX_CIPHER_TOOLS
