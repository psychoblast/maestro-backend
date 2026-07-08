"""
M3 loop consolidation — unit tests for the shared `stream_tool_use_agent`
helper (main.py). These drive the helper DIRECTLY (not through the endpoint),
injecting a fake Anthropic client + fake executor, and assert the four
behaviours the consolidation contract depends on:

  1. generic-key path   — actions event ships the generic "not_connected" key.
  2. bespoke-key path   — actions event ships the exact per-agent key verbatim,
                          and reflects a True not-connected flag.
  3. cap enforcement    — a permanently tool-using model stops after exactly
                          `max_iters` create() round-trips (never unbounded).
  4. executor dispatch  — each tool_use block is routed to `execute_tool` with
                          (name, input, artist_id), and results feed back.

Also validates STREAM_AGENT_REGISTRY entry shape (callables + key strings).

No network / LLM / TTS / DB: the client is a scripted fake, do_tts=False, and
save_exchange is a fake seam.
"""
import asyncio
import importlib
import json
from unittest.mock import MagicMock, patch

import pytest


# ── Fake Anthropic SDK shapes ────────────────────────────────────────────────

class _Block:
    def __init__(self, type, text=None, name=None, input=None, id=None):
        self.type  = type
        self.text  = text
        self.name  = name
        self.input = input
        self.id    = id


class _Resp:
    def __init__(self, content, stop_reason):
        self.content     = content
        self.stop_reason = stop_reason


class _FakeMessages:
    """Scripted messages.create. If more create() calls happen than scripted
    responses, the LAST response repeats (used to prove cap enforcement)."""
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        idx = min(len(self.calls) - 1, len(self._responses) - 1)
        return self._responses[idx]


class _FakeClient:
    def __init__(self, responses):
        self.messages = _FakeMessages(responses)


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


def _drive(m, *, responses, execute_tool, not_connected_key,
           do_tts=False, message="hello", save_calls=None):
    """Run the helper to completion with a fake client; return parsed SSE events."""
    client = _FakeClient(responses)
    save_calls = save_calls if save_calls is not None else []

    async def _fake_save(*args):
        save_calls.append(args)

    async def _collect():
        gen = m.stream_tool_use_agent(
            tools=[{"name": "noop"}],
            execute_tool=execute_tool,
            max_iters=5,
            not_connected_key=not_connected_key,
            messages=[{"role": "user", "content": message}],
            model="claude-test",
            max_tokens=300,
            system_blocks=[{"type": "text", "text": "sys"}],
            voice="am_michael",
            do_tts=do_tts,
            artist_id="artist-9",
            agent_id="test-agent",
            message=message,
            experts_event=None,
            client=client,
            tts_fn=None,
            save_exchange_fn=_fake_save,
        )
        chunks = []
        async for chunk in gen:
            chunks.append(chunk)
        # Let the fire-and-forget _save_exchange task run before the loop closes.
        await asyncio.sleep(0)
        return chunks

    chunks = asyncio.run(_collect())
    events = []
    for chunk in chunks:
        for line in chunk.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:"):].strip()))
    return events, client, save_calls


# ── 1. generic-key path ──────────────────────────────────────────────────────

def test_generic_not_connected_key_and_stream(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    async def execute_tool(name, tool_input, artist_id):
        raise AssertionError("no tool_use in this scenario")

    responses = [_Resp([_Block("text", text="All set for you.")], "end_turn")]
    events, client, _ = _drive(
        m, responses=responses, execute_tool=execute_tool,
        not_connected_key="not_connected",
    )
    types = [e["type"] for e in events]

    assert "text" in types
    assert "actions" in types
    assert "done" in types
    assert types.index("actions") < types.index("done")

    actions = next(e for e in events if e["type"] == "actions")
    assert "not_connected" in actions
    assert actions["not_connected"] is False
    assert actions["actions_taken"] == []
    assert next(e for e in events if e["type"] == "done")["full_text"] == "All set for you."
    # Text-only turn = exactly one create() round-trip.
    assert len(client.messages.calls) == 1


# ── 2. bespoke-key path ──────────────────────────────────────────────────────

def test_bespoke_key_verbatim_and_not_connected_true(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    async def execute_tool(name, tool_input, artist_id):
        # Simulate a send blocked on missing auth → nc True.
        return ({"ok": False}, {"input": "x", "result": "blocked"}, True)

    responses = [
        _Resp([_Block("tool_use", name="send_thing", input={"a": 1}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Could not send — connect first.")], "end_turn"),
    ]
    events, _, _ = _drive(
        m, responses=responses, execute_tool=execute_tool,
        not_connected_key="gmail_not_connected",
    )
    actions = next(e for e in events if e["type"] == "actions")

    # The exact bespoke key is present; the generic key is NOT.
    assert "gmail_not_connected" in actions
    assert "not_connected" not in actions
    assert actions["gmail_not_connected"] is True
    assert [a["tool"] for a in actions["actions_taken"]] == ["send_thing"]


# ── 3. cap enforcement ───────────────────────────────────────────────────────

def test_iteration_cap_enforced(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    exec_calls = []

    async def execute_tool(name, tool_input, artist_id):
        exec_calls.append(name)
        return ({"ok": True}, {"input": "x", "result": "did"}, False)

    # Model NEVER stops tool-using — the last response repeats forever.
    responses = [
        _Resp([_Block("tool_use", name="loop_tool", input={}, id="t1")], "tool_use"),
    ]
    events, client, _ = _drive(
        m, responses=responses, execute_tool=execute_tool,
        not_connected_key="not_connected",
    )

    # Cap = 5 → exactly 5 create() round-trips and 5 executor dispatches, then
    # the fallback text is streamed. Never unbounded.
    assert len(client.messages.calls) == 5
    assert len(exec_calls) == 5
    done = next(e for e in events if e["type"] == "done")
    assert done["full_text"] == "I've taken the actions I can on that for now."


# ── 4. executor dispatch ─────────────────────────────────────────────────────

def test_executor_dispatch_args_and_feedback(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    seen = []

    async def execute_tool(name, tool_input, artist_id):
        seen.append((name, tool_input, artist_id))
        return ({"result_for": name}, {"input": f"in-{name}", "result": f"ok-{name}"}, False)

    responses = [
        _Resp([_Block("tool_use", name="search_x", input={"q": "hi"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Done.")], "end_turn"),
    ]
    events, client, save_calls = _drive(
        m, responses=responses, execute_tool=execute_tool,
        not_connected_key="not_connected",
    )

    # Executor called once, with the exact (name, input, artist_id).
    assert seen == [("search_x", {"q": "hi"}, "artist-9")]

    # Second create() got the tool_result fed back as a user turn.
    second = client.messages.calls[1]
    tool_results = [
        blk for msg in second["messages"]
        if msg["role"] == "user"
        for blk in (msg["content"] if isinstance(msg["content"], list) else [])
        if isinstance(blk, dict) and blk.get("type") == "tool_result"
    ]
    assert len(tool_results) == 1
    assert tool_results[0]["tool_use_id"] == "t1"
    assert json.loads(tool_results[0]["content"]) == {"result_for": "search_x"}

    # actions surfaced the summary, done fired, save_exchange invoked once.
    actions = next(e for e in events if e["type"] == "actions")
    assert actions["actions_taken"] == [{"tool": "search_x", "input": "in-search_x", "result": "ok-search_x"}]
    assert any(e["type"] == "done" for e in events)
    assert len(save_calls) == 1
    assert save_calls[0][0] == "artist-9"


# ── registry shape ───────────────────────────────────────────────────────────

def test_stream_agent_registry_shape(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    assert m.STREAM_AGENT_REGISTRY, "registry must carry per-agent params"
    for agent_id, entry in m.STREAM_AGENT_REGISTRY.items():
        assert isinstance(agent_id, str) and agent_id
        tools, execute_tool, max_iters, nck = entry
        assert isinstance(tools, list) and tools
        assert asyncio.iscoroutinefunction(execute_tool)
        assert isinstance(max_iters, int) and max_iters > 0
        assert isinstance(nck, str) and nck.endswith("not_connected")
