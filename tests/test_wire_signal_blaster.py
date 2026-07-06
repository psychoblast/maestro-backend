"""
PROOF tests — Zara (signal-blaster) Anthropic tool_use loop (U2 OUTREACH rework).

Mirrors tests/test_wire_brand_connect.py / test_wire_venue_hawk.py. Proves that, in
/api/chat_stream:

  (a) Zara emits search_media_outlets → build_pitch_plan → lookup_publicity_doctrine
      → send_press_pitch then a final message; all four mock-first
      signal_blaster_service functions are invoked with the correct args and the
      stream surfaces a populated `actions` event, with SIGNAL_BLASTER_TOOLS passed
      on every create() call. search_media_outlets NEVER fabricates an outlet (it
      filters the artist-supplied list); build_pitch_plan returns compact
      ingredients; send_press_pitch is the gated mock send with the model-written
      body;
  (b) a NON-signal agent (music-edu) never receives SIGNAL_BLASTER_TOOLS — unchanged
      streaming path, NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still uses MARCUS_TOOLS;
  (d) the account-not-connected (missing-credential) path on send_press_pitch is
      handled gracefully (actions carries press_account_not_connected=True);
  (e) expired account auth also degrades to the not-connected path;
  (f) an EMBARGO pitch with no zoned lift is HELD with a [NEEDS:embargo_lift_datetime]
      gap (no send);
  (g) this (newest) unit OWNS the exact signal-blaster tool roster and the drafting
      tool is gone; and
  (h) the service tool layer contains NO LLM send seam (AST-enforced).

Everything is in-process and deterministic. NO network / LLM / press-wire calls —
the Anthropic client is faked and the signal_blaster_service boundary is exercised
through recording wrappers over the REAL (pure, mock-first) functions.
"""
import ast
import importlib
import json
import pathlib
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


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


# Artist-supplied media list — the ONLY source of outlet names Zara ever sees.
_ARTIST_MEDIA = [
    {"name": "The Weekly Zine", "beat": "indie", "level": "mid"},
    {"name": "City Beat Blog",  "beat": "indie", "level": "local"},
]


# ── (a) Zara runs the full tool loop and surfaces actions_taken ──────────────

def test_signal_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected press account so the pitch send succeeds (no network).
    monkeypatch.setenv("PRESS_OUTREACH_CONNECTED", "true")

    search_calls, plan_calls, doctrine_calls, send_calls = [], [], [], []
    real_search   = m.signal_blaster_service.search_media_outlets
    real_plan     = m.signal_blaster_service.build_pitch_plan
    real_doctrine = m.signal_blaster_service.lookup_publicity_doctrine
    real_send     = m.signal_blaster_service.send_press_pitch

    async def rec_search(beat="", level="", media_list=None):
        search_calls.append({"beat": beat, "level": level, "media_list": media_list})
        return await real_search(beat=beat, level=level, media_list=media_list)

    async def rec_plan(artist_id, release_date="", weeks_to_release=None, goal="", package=None):
        plan_calls.append({"artist_id": artist_id, "release_date": release_date,
                           "weeks_to_release": weeks_to_release, "goal": goal,
                           "package": package})
        return await real_plan(artist_id, release_date=release_date,
                               weeks_to_release=weeks_to_release, goal=goal, package=package)

    async def rec_doctrine(topic=""):
        doctrine_calls.append({"topic": topic})
        return await real_doctrine(topic)

    async def rec_send(artist_id, outlet_id="", outlet="", subject="", body="",
                       pitch_mode="standard", embargo_lift_datetime=None):
        send_calls.append({"artist_id": artist_id, "outlet_id": outlet_id, "outlet": outlet,
                           "subject": subject, "body": body, "pitch_mode": pitch_mode,
                           "embargo_lift_datetime": embargo_lift_datetime})
        return await real_send(artist_id, outlet_id=outlet_id, outlet=outlet,
                               subject=subject, body=body, pitch_mode=pitch_mode,
                               embargo_lift_datetime=embargo_lift_datetime)

    monkeypatch.setattr(m.signal_blaster_service, "search_media_outlets",     rec_search)
    monkeypatch.setattr(m.signal_blaster_service, "build_pitch_plan",         rec_plan)
    monkeypatch.setattr(m.signal_blaster_service, "lookup_publicity_doctrine", rec_doctrine)
    monkeypatch.setattr(m.signal_blaster_service, "send_press_pitch",         rec_send)

    responses = [
        _Resp([_Block("tool_use", name="search_media_outlets",
                      input={"beat": "indie", "media_list": _ARTIST_MEDIA}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_pitch_plan",
                      input={"release_date": "2026-10-01", "weeks_to_release": 10,
                             "goal": "max impressions",
                             "package": {"bio": "b", "story_angle": "a"}}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="lookup_publicity_doctrine",
                      input={"topic": "embargo"}, id="t3")], "tool_use"),
        _Resp([_Block("tool_use", name="send_press_pitch",
                      input={"outlet": "The Weekly Zine", "subject": "New single",
                             "body": "Hi — new single out Oct, angle attached.",
                             "pitch_mode": "standard"}, id="t4")], "tool_use"),
        _Resp([_Block("text", text="Done — filtered the list, built the plan, and sent the pitch.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("signal-blaster must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "signal-blaster",
        "message":   "pitch my single to my indie list",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # search filtered the ARTIST-supplied list (never fabricated).
    assert len(search_calls) == 1
    assert search_calls[0]["beat"] == "indie"
    assert search_calls[0]["media_list"] == _ARTIST_MEDIA
    assert plan_calls == [{
        "artist_id": "artist-9", "release_date": "2026-10-01", "weeks_to_release": 10,
        "goal": "max impressions", "package": {"bio": "b", "story_angle": "a"},
    }], plan_calls
    assert doctrine_calls == [{"topic": "embargo"}], doctrine_calls
    # send carried the MODEL-written body verbatim.
    assert send_calls == [{
        "artist_id": "artist-9", "outlet_id": "", "outlet": "The Weekly Zine",
        "subject": "New single", "body": "Hi — new single out Oct, angle attached.",
        "pitch_mode": "standard", "embargo_lift_datetime": None,
    }], send_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_media_outlets", "build_pitch_plan", "lookup_publicity_doctrine",
        "send_press_pitch",
    ], tools_used
    assert actions_evt["press_account_not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "artist-supplied outlet(s) matched" in by_tool["search_media_outlets"]["result"]
    assert "mode=standard" in by_tool["build_pitch_plan"]["result"]
    assert "honesty rule(s)" in by_tool["lookup_publicity_doctrine"]["result"]
    assert by_tool["send_press_pitch"]["result"] == "press pitch sent"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 5
    assert all(kw.get("tools") == m.SIGNAL_BLASTER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


# ── (b) Non-signal agent never gets signal tools, unchanged path ─────────────

def test_non_signal_agent_never_receives_signal_tools(monkeypatch, tmp_path):
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

    assert create_calls == [], "non-signal agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS ─────────────────────

def test_marcus_still_uses_marcus_tools_not_signal(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.SIGNAL_BLASTER_TOOLS


# ── (d) press_account_not_connected (missing credential) handled gracefully ───

def test_press_account_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.delenv("PRESS_OUTREACH_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="send_press_pitch",
                      input={"outlet": "The Weekly Zine", "subject": "Hi",
                             "body": "New single."}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a press account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "signal-blaster",
        "message":   "send the pitch",
        "artist_id": "artist-no-account",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert "done" in types
    assert "error" not in types, types
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["press_account_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "press_account_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_press_account_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("PRESS_OUTREACH_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="send_press_pitch",
                      input={"outlet": "City Beat Blog", "subject": "Hi",
                             "body": "New single."}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your press-account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "signal-blaster",
        "message":   "send the pitch",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["press_account_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "press_account_auth_expired"


# ── (f) embargo with no zoned lift is HELD (no send) ─────────────────────────

def test_embargo_without_lift_is_held(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("PRESS_OUTREACH_CONNECTED", "true")

    responses = [
        _Resp([_Block("tool_use", name="send_press_pitch",
                      input={"outlet": "The Weekly Zine", "subject": "Embargoed news",
                             "body": "Under embargo.", "pitch_mode": "embargo"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="I need a lift date/time with time zone before I send that.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "signal-blaster",
        "message":   "send the embargoed pitch",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["press_account_not_connected"] is False
    assert actions_evt["actions_taken"][0]["result"] == "needs embargo lift datetime"


# ── (g) newest unit OWNS the exact signal-blaster tool roster ────────────────

def test_signal_blaster_tool_roster_is_exact(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.SIGNAL_BLASTER_TOOLS]
    assert names == ["search_media_outlets", "build_pitch_plan",
                     "lookup_publicity_doctrine", "send_press_pitch"], names
    # drafting was removed — it belongs to creative-director's build_copy_scaffold.
    assert "draft_press_release" not in names
    assert not hasattr(m.signal_blaster_service, "draft_press_release")


# ── (h) the service tool layer carries NO LLM send seam (AST-enforced) ───────

def test_service_layer_has_no_llm_send_seam():
    import signal_blaster_service as sbs
    source = pathlib.Path(sbs.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert "anthropic" not in a.name.lower(), a.name
        if isinstance(node, ast.ImportFrom):
            assert "anthropic" not in (node.module or "").lower(), node.module
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "create" and isinstance(node.func.value, ast.Attribute):
                assert node.func.value.attr != "messages", "no messages.create in the tool layer"
