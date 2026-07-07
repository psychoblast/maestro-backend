"""
PROOF tests — Data (data-oracle) Anthropic tool_use loop, DOC-WRITER Option B.

Proves that, in /api/chat_stream:

  (a) Data emits lookup_analytics_doctrine → build_analytics_doc_scaffold then a
      final message; both analytics data_oracle_service functions are invoked
      with the correct args and the stream surfaces a populated `actions`
      event, with DATA_ORACLE_TOOLS passed on every create() call and
      data_warehouse_not_connected ALWAYS False (the old data-warehouse gate
      is retired);
  (b) a NON-data agent never receives DATA_ORACLE_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool
      loop with MARCUS_TOOLS, never DATA_ORACLE_TOOLS;
  (d) a scaffold's standing doctrine (no_dollar_figures / never_fabricate_numbers)
      survives into the tool_result payload fed back to the model, and no
      computed numeric total ever leaks through (JSON-decode-then-assert,
      since raw string comparison breaks on non-ASCII escaping).

Everything is in-process and deterministic. NO network / LLM calls — the
Anthropic client is faked and the data_oracle_service boundary is exercised
through recording wrappers over the REAL functions. This file NEVER asserts
generated prose; the final assistant text is scripted.
"""
import importlib
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import analytics_data as ad


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


# ── (a) Data runs the tool loop and surfaces actions_taken ────────────────────

def test_data_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    lookup_calls, build_calls = [], []
    real_lookup = m.data_oracle_service.lookup_analytics_doctrine
    real_build  = m.data_oracle_service.build_analytics_doc_scaffold

    async def rec_lookup(metric_key="", band_key="", source_key="",
                          diagnosis_key="", quality_key="", stakeholder_key=""):
        lookup_calls.append({
            "metric_key": metric_key, "band_key": band_key, "source_key": source_key,
            "diagnosis_key": diagnosis_key, "quality_key": quality_key,
            "stakeholder_key": stakeholder_key,
        })
        return await real_lookup(metric_key=metric_key, band_key=band_key,
                                 source_key=source_key, diagnosis_key=diagnosis_key,
                                 quality_key=quality_key, stakeholder_key=stakeholder_key)

    async def rec_build(doc_type="", inputs=None):
        build_calls.append({"doc_type": doc_type, "inputs": inputs})
        return await real_build(doc_type=doc_type, inputs=inputs)

    monkeypatch.setattr(m.data_oracle_service, "lookup_analytics_doctrine", rec_lookup)
    monkeypatch.setattr(m.data_oracle_service, "build_analytics_doc_scaffold", rec_build)

    scaffold_input = {"stream": 12000, "saves": 400}
    responses = [
        _Resp([_Block("tool_use", name="lookup_analytics_doctrine",
                      input={"metric_key": "save_rate"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_analytics_doc_scaffold",
                      input={"doc_type": "metrics_readout", "inputs": scaffold_input},
                      id="t2")], "tool_use"),
        _Resp([_Block("text", text="Here is your metrics readout.")], "end_turn"),
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
        raise AssertionError("Data must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "data-oracle",
        "message":   "give me a metrics readout on my streams and saves",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert lookup_calls == [{
        "metric_key": "save_rate", "band_key": "", "source_key": "",
        "diagnosis_key": "", "quality_key": "", "stakeholder_key": "",
    }], lookup_calls
    assert build_calls == [{"doc_type": "metrics_readout", "inputs": scaffold_input}], build_calls

    assert "actions" in types and "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["lookup_analytics_doctrine", "build_analytics_doc_scaffold"], tools_used
    assert actions_evt["data_warehouse_not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "match(es)" in by_tool["lookup_analytics_doctrine"]["result"]
    assert "scaffold_ready" in by_tool["build_analytics_doc_scaffold"]["result"]

    # Three create() round-trips; DATA tools on every one (never MARCUS_TOOLS).
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.DATA_ORACLE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)

    # (d) Data's standing doctrine survives into the tool_result fed back to the
    # model, and no computed total ever leaks through. (json.dumps escapes
    # non-ASCII characters, so compare on the DECODED payload, not the raw string.)
    scaffold_payload = next(p for p in tool_result_payloads if "scaffold_ready" in p)
    decoded = json.loads(scaffold_payload)
    assert decoded["header"]["no_dollar_figures"] == ad.DATA_DOCTRINE["no_dollar_figures"]
    assert decoded["header"]["never_fabricate_numbers"] == ad.DATA_DOCTRINE["never_fabricate_numbers"]
    for banned_key in ('"growth_pct"', '"score"', '"percentage"', '"total"', '"sum"'):
        assert banned_key not in scaffold_payload.lower()


# ── (b) Non-data agent never gets data tools, takes the unchanged path ────────

def test_non_data_agent_never_receives_data_tools(monkeypatch, tmp_path):
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

    assert create_calls == [], "non-data agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not data tools ─────

def test_marcus_still_uses_marcus_tools_not_data(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.DATA_ORACLE_TOOLS


# ── (d) stakeholder stat sheet doctrine survives the loop, end to end ─────────

def test_stakeholder_stat_sheet_doctrine_survives_the_loop(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    stat_sheet_inputs = {
        "stakeholder": "venues_and_agents",
        "listeners_in_their_city": "1,200 monthly listeners in Chicago",
    }
    responses = [
        _Resp([_Block("tool_use", name="build_analytics_doc_scaffold",
                      input={"doc_type": "stakeholder_stat_sheet", "inputs": stat_sheet_inputs},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here is your stakeholder stat sheet.")], "end_turn"),
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
        "agent_id":  "data-oracle",
        "message":   "give me a stat sheet for the venue I'm pitching",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    scaffold_payload = next(p for p in tool_result_payloads if "scaffold_ready" in p)
    decoded = json.loads(scaffold_payload)
    assert decoded["header"]["insights_not_actions"] == ad.DATA_DOCTRINE["insights_not_actions"]
    wants_section = next(s for s in decoded["sections"] if s["key"] == "stakeholder_wants")
    by_want = {w["want"]: w["value"] for w in wants_section["wants"]}
    assert by_want["listeners_in_their_city"] == stat_sheet_inputs["listeners_in_their_city"]
    assert "[ARTIST-SUPPLIED:draw_evidence]" in decoded["missing"]
