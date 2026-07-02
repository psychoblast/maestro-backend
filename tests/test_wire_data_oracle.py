"""
PROOF tests — Data (data-oracle) Anthropic tool_use loop.

Mirrors tests/test_wire_creative_director.py / tests/test_marcus_tool_use.py.
Proves that, in /api/chat_stream:

  (a) Data emits search_streaming_datasets → analyze_streaming_metric →
      schedule_data_export then a final message; all three mock-first
      data_oracle_service functions are invoked with the correct args and the
      stream surfaces a populated `actions` event (actions_taken), with
      DATA_ORACLE_TOOLS passed on every create() call;
  (b) a NON-data-oracle agent (producer-connect) never receives DATA_ORACLE_TOOLS — it
      takes the unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never DATA_ORACLE_TOOLS;
  (d) the warehouse-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries data_warehouse_not_connected=True);
  (e) expired warehouse auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM calls — the
Anthropic client is faked and the data_oracle_service boundary is exercised
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
    """Stand-in for async_client.messages.stream(...) — used by the non-Data path."""
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


# ── (a) Data runs the tool loop and surfaces actions_taken ───────────────────

def test_data_oracle_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected warehouse so the export succeeds (no network).
    monkeypatch.setenv("DATA_ORACLE_WAREHOUSE_CONNECTED", "true")

    # Record calls into the REAL (pure) data_oracle_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, analyze_calls, export_calls = [], [], []
    real_search  = m.data_oracle_service.search_streaming_datasets
    real_analyze = m.data_oracle_service.analyze_streaming_metric
    real_export  = m.data_oracle_service.schedule_data_export

    async def rec_search(platform="", metric=""):
        search_calls.append({"platform": platform, "metric": metric})
        return await real_search(platform=platform, metric=metric)

    async def rec_analyze(artist_id, dataset_id="", current_value=0, prior_value=0, window_days=0):
        analyze_calls.append({"artist_id": artist_id, "dataset_id": dataset_id,
                              "current_value": current_value, "prior_value": prior_value,
                              "window_days": window_days})
        return await real_analyze(artist_id, dataset_id=dataset_id,
                                  current_value=current_value, prior_value=prior_value,
                                  window_days=window_days)

    async def rec_export(artist_id, dataset_id, destination="", cadence=""):
        export_calls.append({"artist_id": artist_id, "dataset_id": dataset_id,
                             "destination": destination, "cadence": cadence})
        return await real_export(artist_id, dataset_id, destination, cadence)

    monkeypatch.setattr(m.data_oracle_service, "search_streaming_datasets", rec_search)
    monkeypatch.setattr(m.data_oracle_service, "analyze_streaming_metric",  rec_analyze)
    monkeypatch.setattr(m.data_oracle_service, "schedule_data_export",      rec_export)

    # Scripted Anthropic responses: search → analyze → export → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_streaming_datasets",
                      input={"platform": "spotify", "metric": "streams"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="analyze_streaming_metric",
                      input={"dataset_id": "ds-spotify-streams-daily",
                             "current_value": 12000, "prior_value": 10000,
                             "window_days": 7}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="schedule_data_export",
                      input={"dataset_id": "ds-spotify-streams-daily",
                             "destination": "email", "cadence": "weekly"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the dataset, analyzed the trend, and scheduled the export.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Data.
    def _no_stream(**kw):
        raise AssertionError("data-oracle must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "data-oracle",
        "message":   "analyze my spotify streams and set up a weekly export",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"platform": "spotify", "metric": "streams"}], search_calls
    assert analyze_calls == [{
        "artist_id": "artist-9", "dataset_id": "ds-spotify-streams-daily",
        "current_value": 12000, "prior_value": 10000, "window_days": 7,
    }], analyze_calls
    assert export_calls == [{
        "artist_id": "artist-9", "dataset_id": "ds-spotify-streams-daily",
        "destination": "email", "cadence": "weekly",
    }], export_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_streaming_datasets", "analyze_streaming_metric", "schedule_data_export",
    ], tools_used
    assert actions_evt["data_warehouse_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "dataset(s) found" in by_tool["search_streaming_datasets"]["result"]
    # 12000 vs 10000 = +20% → trend up, recommend scale.
    assert "trend=up" in by_tool["analyze_streaming_metric"]["result"]
    assert "scale" in by_tool["analyze_streaming_metric"]["result"]
    assert by_tool["schedule_data_export"]["result"] == "export scheduled"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, analyze, export, final.
    assert len(create_calls) == 4
    # DATA_ORACLE_TOOLS passed on every Data create call (never other toolsets).
    assert all(kw.get("tools") == m.DATA_ORACLE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.CREATIVE_DIRECTOR_TOOLS for kw in create_calls)


# ── (b) Non-Data agent never gets Data tools, takes the unchanged path ────────

def test_non_data_oracle_agent_never_receives_data_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT data-oracle, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-Data agent must not invoke the tool_use create loop"
    # No actions event for non-Data agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not Data tools ──────

def test_marcus_still_uses_marcus_tools_not_data_oracle(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the Data gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.DATA_ORACLE_TOOLS


# ── (d) data_warehouse_not_connected (missing credential) handled gracefully ──

def test_data_warehouse_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No warehouse connected → export raises DataWarehouseNotConnected.
    monkeypatch.delenv("DATA_ORACLE_WAREHOUSE_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="schedule_data_export",
                      input={"dataset_id": "ds-youtube-watchtime-daily",
                             "destination": "dashboard"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a data warehouse first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "data-oracle",
        "message":   "schedule my youtube export",
        "artist_id": "artist-no-warehouse",
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
    assert actions_evt["data_warehouse_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "data_warehouse_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_data_warehouse_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("DATA_ORACLE_WAREHOUSE_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="schedule_data_export",
                      input={"dataset_id": "ds-tiktok-sound-views-daily",
                             "destination": "warehouse"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your data-warehouse auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "data-oracle",
        "message":   "schedule my tiktok export",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["data_warehouse_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "data_warehouse_auth_expired"
