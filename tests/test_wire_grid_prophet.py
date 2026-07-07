"""
PROOF tests — Kai (grid-prophet) Anthropic tool_use loop, DOC-WRITER Option B.

Proves that, in /api/chat_stream:

  (a) Kai emits lookup_digital_marketing_doctrine → build_marketing_doc_scaffold
      then a final message; both digital-marketing grid_prophet_service functions
      are invoked with the correct args and the stream surfaces a populated
      `actions` event, with GRID_PROPHET_TOOLS passed on every create() call and
      social_account_not_connected ALWAYS False (the old social-account gate is
      retired);
  (b) a NON-grid agent never receives GRID_PROPHET_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool
      loop with MARCUS_TOOLS, never GRID_PROPHET_TOOLS;
  (d) the scaffold tool_result fed back to the model carries Kai's standing
      doctrine (sequence_before_spend) and never a computed/echoed budget
      figure, even when one is supplied in inputs.

Everything is in-process and deterministic. NO network / LLM calls — the
Anthropic client is faked and the grid_prophet_service boundary is exercised
through recording wrappers over the REAL (pure) functions. This file NEVER
asserts generated prose; the final assistant text is scripted.
"""
import importlib
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import digital_marketing_data as dmd


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


# ── (a) Kai runs the tool loop and surfaces actions_taken ────────────────────

def test_grid_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    lookup_calls, build_calls = [], []
    real_lookup = m.grid_prophet_service.lookup_digital_marketing_doctrine
    real_build  = m.grid_prophet_service.build_marketing_doc_scaffold

    async def rec_lookup(sequence_key="", proof_key="", platform_key="",
                          budget_key="", measurement_key="", momentum_key=""):
        lookup_calls.append({
            "sequence_key": sequence_key, "proof_key": proof_key,
            "platform_key": platform_key, "budget_key": budget_key,
            "measurement_key": measurement_key, "momentum_key": momentum_key,
        })
        return await real_lookup(sequence_key=sequence_key, proof_key=proof_key,
                                 platform_key=platform_key, budget_key=budget_key,
                                 measurement_key=measurement_key, momentum_key=momentum_key)

    async def rec_build(doc_type="", inputs=None):
        build_calls.append({"doc_type": doc_type, "inputs": inputs})
        return await real_build(doc_type=doc_type, inputs=inputs)

    monkeypatch.setattr(m.grid_prophet_service, "lookup_digital_marketing_doctrine", rec_lookup)
    monkeypatch.setattr(m.grid_prophet_service, "build_marketing_doc_scaffold", rec_build)

    # A supplied budget figure — must NEVER be echoed as a number anywhere.
    scaffold_input = {
        "channels_in_place": ["streaming_platform_optimization", "organic_short_form_content"],
        "budget": 5000,
    }
    responses = [
        _Resp([_Block("tool_use", name="lookup_digital_marketing_doctrine",
                      input={"sequence_key": "sequencing_order"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_marketing_doc_scaffold",
                      input={"doc_type": "campaign_plan", "inputs": scaffold_input},
                      id="t2")], "tool_use"),
        _Resp([_Block("text", text="Here is your campaign plan prep.")], "end_turn"),
    ]
    create_calls = []
    tool_result_payloads = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        for msg in kwargs.get("messages", []):
            if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                for blk in msg["content"]:
                    if isinstance(blk, dict) and blk.get("type") == "tool_result":
                        tool_result_payloads.append(blk["content"])
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Kai must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "grid-prophet",
        "message":   "prep a campaign plan for the new single",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert lookup_calls == [{
        "sequence_key": "sequencing_order", "proof_key": "", "platform_key": "",
        "budget_key": "", "measurement_key": "", "momentum_key": "",
    }], lookup_calls
    assert build_calls == [{"doc_type": "campaign_plan", "inputs": scaffold_input}], build_calls

    assert "actions" in types and "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["lookup_digital_marketing_doctrine", "build_marketing_doc_scaffold"], tools_used
    assert actions_evt["social_account_not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "match(es)" in by_tool["lookup_digital_marketing_doctrine"]["result"]
    assert "scaffold_ready" in by_tool["build_marketing_doc_scaffold"]["result"]

    # Three create() round-trips; GRID tools on every one (never MARCUS_TOOLS).
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.GRID_PROPHET_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)

    # (d) Kai's standing doctrine survives into the tool_result fed back to
    # the model, and no computed/echoed budget figure ever leaks through. (json.dumps
    # escapes non-ASCII em-dashes, so compare on the DECODED payload, not the raw string.)
    scaffold_payload = next(p for p in tool_result_payloads if "scaffold_ready" in p)
    decoded = json.loads(scaffold_payload)
    assert decoded["header"]["sequence_before_spend"] == dmd.KAI_DOCTRINE["sequence_before_spend"]
    assert "5000" not in scaffold_payload
    for banned_key in ('"budget":5000', '"budget": 5000'):
        assert banned_key not in scaffold_payload


# ── (b) Non-grid agent never gets grid tools, takes the unchanged path ────────

def test_non_grid_agent_never_receives_grid_tools(monkeypatch, tmp_path):
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

    assert create_calls == [], "non-grid agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not grid ───────────

def test_marcus_still_uses_marcus_tools_not_grid(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.GRID_PROPHET_TOOLS


# ── (d) ad_test_brief budget figure never survives the loop, end to end ──────

def test_ad_test_brief_budget_figure_never_leaks_through_the_loop(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    ad_test_inputs = {"ad_spend": 12345, "budget": "10000 dollars a week"}
    responses = [
        _Resp([_Block("tool_use", name="build_marketing_doc_scaffold",
                      input={"doc_type": "ad_test_brief", "inputs": ad_test_inputs},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here is your ad test brief.")], "end_turn"),
    ]
    create_calls = []
    tool_result_payloads = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        for msg in kwargs.get("messages", []):
            if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                for blk in msg["content"]:
                    if isinstance(blk, dict) and blk.get("type") == "tool_result":
                        tool_result_payloads.append(blk["content"])
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "grid-prophet",
        "message":   "give me an ad test brief",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    scaffold_payload = next(p for p in tool_result_payloads if "scaffold_ready" in p)
    assert "12345" not in scaffold_payload
    assert "10000" not in scaffold_payload
    fields_section = json.loads(scaffold_payload)["sections"]
    assert all(s.get("key") != "ad_spend" for s in fields_section)
