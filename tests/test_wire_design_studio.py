"""
PROOF tests — Diego (design-studio) Anthropic tool_use loop.

Mirrors tests/test_wire_vision_forge.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Diego emits search_brand_styles -> draft_brand_brief then a final message;
      both mock-first design_studio_service functions are invoked with the correct
      args and the stream surfaces a populated `actions` event (actions_taken),
      with DESIGN_STUDIO_TOOLS passed on every create() call;
  (b) a NON-design agent (producer-connect) never receives DESIGN_STUDIO_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never DESIGN_STUDIO_TOOLS;
  (d) Diego is consult-only — the retired produce_brand_asset mock-action tool (and
      its DESIGN_STUDIO_ACCOUNT_CONNECTED gate) is gone from both the schema and the
      dispatch: it is neither offered to the model nor executable by name, and
      not_connected is structurally always False.

Everything is in-process and deterministic. NO network / LLM / render calls — the
Anthropic client is faked and the design_studio_service boundary is exercised through
recording wrappers over the REAL (pure, mock-first) functions.
"""
import importlib
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


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
    """Stand-in for async_client.messages.stream(...) — used by the non-design path."""
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


# ── (a) Diego runs the tool loop and surfaces actions_taken ──────────────────

def test_design_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    search_calls, draft_calls = [], []
    real_search = m.design_studio_service.search_brand_styles
    real_draft  = m.design_studio_service.draft_brand_brief

    async def rec_search(asset_type="", tier=""):
        search_calls.append({"asset_type": asset_type, "tier": tier})
        return await real_search(asset_type=asset_type, tier=tier)

    async def rec_draft(artist_id, concept="", asset_type="", tone=""):
        draft_calls.append({"artist_id": artist_id, "concept": concept,
                            "asset_type": asset_type, "tone": tone})
        return await real_draft(artist_id, concept=concept, asset_type=asset_type, tone=tone)

    monkeypatch.setattr(m.design_studio_service, "search_brand_styles", rec_search)
    monkeypatch.setattr(m.design_studio_service, "draft_brand_brief",   rec_draft)

    responses = [
        _Resp([_Block("tool_use", name="search_brand_styles",
                      input={"asset_type": "logo", "tier": "A"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_brand_brief",
                      input={"concept": "Bold monogram for a rising artist",
                             "asset_type": "logo",
                             "tone": "confident and timeless"}, id="t2")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the style and drafted the brief.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("design-studio must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "design-studio",
        "message":   "find a logo style and draft a brief",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert search_calls == [{"asset_type": "logo", "tier": "A"}], search_calls
    assert draft_calls == [{
        "artist_id": "artist-9", "concept": "Bold monogram for a rising artist",
        "asset_type": "logo",
        "tone": "confident and timeless",
    }], draft_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_brand_styles", "draft_brand_brief"], tools_used
    assert actions_evt["design_workspace_not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "style(s) found" in by_tool["search_brand_styles"]["result"]
    assert "drafted=True" in by_tool["draft_brand_brief"]["result"]
    assert "produce" in by_tool["draft_brand_brief"]["result"]

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.DESIGN_STUDIO_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEX_CIPHER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VISION_FORGE_TOOLS for kw in create_calls)


# ── (b) Non-design agent never gets design tools, takes the unchanged path ────

def test_non_design_agent_never_receives_design_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT design-studio, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert create_calls == [], "non-design agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not design tools ────

def test_marcus_still_uses_marcus_tools_not_design(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.DESIGN_STUDIO_TOOLS


# ── (d) Diego's tool roster is consult-only; the retired mock tool cannot reappear ──

def test_design_studio_tool_roster_is_consult_only(monkeypatch, tmp_path):
    """This unit owns Diego's exact tool roster: exactly the two consult tools,
    nothing more. The retired produce_brand_asset mock-action tool must not
    reappear."""
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.DESIGN_STUDIO_TOOLS]
    assert names == ["search_brand_styles", "draft_brand_brief"], names
    assert "produce_brand_asset" not in names
    assert not hasattr(m.design_studio_service, "produce_brand_asset")
    assert not hasattr(m.design_studio_service, "DesignWorkspaceNotConnected")
    assert not hasattr(m.design_studio_service, "DesignWorkspaceAuthExpired")


def test_design_studio_unknown_tool_name_is_handled_gracefully(monkeypatch, tmp_path):
    """A retired/unknown tool name must degrade to the unknown_tool branch, not crash."""
    m = _load_main(monkeypatch, tmp_path)
    import asyncio
    result, summary, not_connected = asyncio.run(
        m._execute_design_studio_tool("produce_brand_asset",
                                       {"style_id": "brd-monogram-serif", "prompt": "x"}, "artist-9")
    )
    assert result == {"error": "unknown_tool", "tool": "produce_brand_asset"}
    assert not_connected is False
