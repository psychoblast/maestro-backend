"""
PROOF tests — Solo Unit 2: lookup_radio_promo_doctrine + send_radio_pitch (+ wiring).

lookup_radio_promo_doctrine is a PURE read over radio_promo_data (Solo Unit 1) —
each topic returns its section plus the full honesty-rule set; a CURATOR-related
topic returns a structured out_of_scope answer naming the management department
(Marcus); unknown topic -> structured error; NOT gated. send_radio_pitch follows
the Marcus send seam: the MODEL writes the pitch subject/body and passes them in —
the tool SENDS (deterministic mock sha1 reference, ZERO network), it NEVER
generates/edits the body, and it NEVER asserts or computes a MAPL status (declared
letters ride through verbatim, else a [NEEDS:mapl_declaration] gap). Same
AIRWAVE_ACCOUNT_CONNECTED gate as submit_airplay_pitch: connected -> mock send;
not-connected/expired -> raises so the loop degrades to plugging_not_connected.
Wiring: both schemas in AIRWAVE_TOOLS, dispatch through Solo's execute path in the
real /api/chat_stream loop; the doctrine lookup is not gated.
"""
import asyncio
import importlib
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import radio_promo_data
import airwave_service as svc


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


def _run(coro):
    return asyncio.run(coro)


_HONESTY_RULE_IDS = ["never_assert_mapl", "no_placement_guarantees",
                     "costs_and_panel_sizes_verify_live",
                     "platform_costs_and_processes_verify_live",
                     "facts_supplied_or_marked"]

_TARGET_ID = "tgt-kexp-drive"
_SUBJECT = "New single for your Drive show — MAL-declared"
_BODY = ("Hi music director,\n\nSending my new single ahead of its release for "
         "your consideration on the Drive show. Full servicing to follow via the "
         "usual delivery platform.\n\n— the artist")


# ── lookup_radio_promo_doctrine (pure read, not gated) ─────────────────────────

def test_lookup_returns_section_and_honesty_for_each_topic(monkeypatch):
    monkeypatch.delenv("AIRWAVE_ACCOUNT_CONNECTED", raising=False)  # not gated
    for topic in svc.RADIO_PROMO_TOPICS:
        res = _run(svc.lookup_radio_promo_doctrine(topic))
        assert res["status"] == "ok", topic
        assert res["topic"] == topic
        assert res["data"] is not None, topic
        assert [r["id"] for r in res["honesty_rules"]] == _HONESTY_RULE_IDS, topic


def test_lookup_cancon_resolves_to_its_section():
    res = _run(svc.lookup_radio_promo_doctrine("cancon"))
    assert "35%" in res["data"]["rule"]["commercial_popular_music"]


def test_lookup_unknown_topic_structured_error():
    res = _run(svc.lookup_radio_promo_doctrine("terrestrial"))
    assert res["status"] == "unknown_topic"
    assert res["supported_topics"] == list(svc.RADIO_PROMO_TOPICS)
    assert "data" not in res


def test_lookup_topic_normalized_case_and_whitespace():
    res = _run(svc.lookup_radio_promo_doctrine("  College_Radio "))
    assert res["status"] == "ok"
    assert res["topic"] == "college_radio"


def test_lookup_results_json_serializable():
    for topic in list(svc.RADIO_PROMO_TOPICS) + ["nope", "playlist_curators"]:
        json.dumps(_run(svc.lookup_radio_promo_doctrine(topic)))


def test_curator_topic_returns_out_of_scope_naming_marcus():
    # REQUIRED: a curator-related topic returns the out-of-scope boundary, naming
    # the management department (Marcus). Solo defines no curator tools.
    for topic in ("playlist_curator_outreach", "curators", "playlist curator"):
        res = _run(svc.lookup_radio_promo_doctrine(topic))
        assert res["status"] == "out_of_scope", topic
        assert "marcus" in res["owner"].lower()
        assert "management" in res["owner"].lower()
        assert "marcus" in res["message"].lower()
        assert "data" not in res


# ── send_radio_pitch (Marcus send seam; gated; body verbatim; never asserts MAPL)

def test_send_connected_returns_mock_reference_and_body_verbatim(monkeypatch):
    monkeypatch.setenv("AIRWAVE_ACCOUNT_CONNECTED", "true")
    res = _run(svc.send_radio_pitch("artist-9", _TARGET_ID, _SUBJECT, _BODY,
                                    mapl_declaration="MAL"))
    assert res["status"] == "sent"
    assert res["reference"].startswith("RPITCH-")
    assert res["target_id"] == _TARGET_ID
    assert res["subject"] == _SUBJECT
    assert res["body"] == _BODY
    assert res["mapl_declaration"] == "MAL"  # declared letters ride verbatim


def test_send_never_asserts_mapl_when_undeclared(monkeypatch):
    # REQUIRED: with no declaration, the result carries a [NEEDS:] gap — never an
    # invented / computed CanCon or MAPL status.
    monkeypatch.setenv("AIRWAVE_ACCOUNT_CONNECTED", "true")
    res = _run(svc.send_radio_pitch("artist-9", _TARGET_ID, "s", "b"))
    assert res["mapl_declaration"] == "[NEEDS:mapl_declaration]"
    blob = json.dumps(res).lower()
    # nothing that reads as a computed CanCon status was minted by the tool
    assert "cancon" not in blob
    assert "is_cancon" not in res and "cancon_status" not in res


def test_send_empty_string_mapl_is_a_gap_not_asserted(monkeypatch):
    monkeypatch.setenv("AIRWAVE_ACCOUNT_CONNECTED", "connected")
    res = _run(svc.send_radio_pitch("artist-9", _TARGET_ID, "s", "b",
                                    mapl_declaration="   "))
    assert res["mapl_declaration"] == "[NEEDS:mapl_declaration]"


def test_send_not_connected_raises(monkeypatch):
    monkeypatch.delenv("AIRWAVE_ACCOUNT_CONNECTED", raising=False)
    try:
        _run(svc.send_radio_pitch("artist-9", _TARGET_ID, "s", "b"))
        assert False, "expected AirwaveAccountNotConnected"
    except svc.AirwaveAccountNotConnected:
        pass


def test_send_expired_raises(monkeypatch):
    monkeypatch.setenv("AIRWAVE_ACCOUNT_CONNECTED", "expired")
    try:
        _run(svc.send_radio_pitch("artist-9", _TARGET_ID, "s", "b"))
        assert False, "expected AirwaveAuthExpired"
    except svc.AirwaveAuthExpired:
        pass


def test_send_unknown_target_is_structured(monkeypatch):
    monkeypatch.setenv("AIRWAVE_ACCOUNT_CONNECTED", "true")
    res = _run(svc.send_radio_pitch("artist-9", "tgt-nope", "s", "b"))
    assert res["status"] == "unknown_target"


# ── wiring through the real /api/chat_stream loop ──────────────────────────────

def test_lookup_dispatch_not_portal_gated(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("AIRWAVE_ACCOUNT_CONNECTED", raising=False)

    lookup_calls = []
    real_lookup = m.airwave_service.lookup_radio_promo_doctrine

    async def rec_lookup(topic=""):
        lookup_calls.append({"topic": topic})
        return await real_lookup(topic)

    monkeypatch.setattr(m.airwave_service, "lookup_radio_promo_doctrine", rec_lookup)

    responses = [
        _Resp([_Block("tool_use", name="lookup_radio_promo_doctrine",
                      input={"topic": "cancon"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here is the CanCon doctrine to work from.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "airwave",
        "message":   "how does CanCon work?",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    assert lookup_calls == [{"topic": "cancon"}]
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["actions_taken"][0]["tool"] == "lookup_radio_promo_doctrine"
    assert "honesty rule(s)" in actions_evt["actions_taken"][0]["result"]
    assert actions_evt["plugging_not_connected"] is False, \
        "the doctrine lookup must not trip the plugging gate"
    assert all(kw.get("tools") == m.AIRWAVE_TOOLS for kw in create_calls)


def test_send_radio_pitch_connected_through_loop(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("AIRWAVE_ACCOUNT_CONNECTED", "true")

    responses = [
        _Resp([_Block("tool_use", name="send_radio_pitch",
                      input={"target_id": _TARGET_ID, "subject": _SUBJECT,
                             "body": _BODY, "mapl_declaration": "MAL"}, id="t1")],
              "tool_use"),
        _Resp([_Block("text", text="Sent your pitch to KEXP.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "airwave",
        "message":   "send my pitch to KEXP",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["actions_taken"][0]["tool"] == "send_radio_pitch"
    assert actions_evt["actions_taken"][0]["result"] == "radio pitch sent"
    assert actions_evt["plugging_not_connected"] is False
    assert "Sent your pitch" in next(e for e in events if e["type"] == "done")["full_text"]


def test_send_radio_pitch_not_connected_through_loop(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("AIRWAVE_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="send_radio_pitch",
                      input={"target_id": _TARGET_ID, "subject": "s", "body": "b"},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a plugging account first.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "airwave",
        "message":   "send my pitch",
        "artist_id": "artist-no-account",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types = [e["type"] for e in events]
    assert "error" not in types
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["plugging_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "plugging_not_connected"


def test_dispatch_send_and_curator_topic_through_execute_path(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("AIRWAVE_ACCOUNT_CONNECTED", "true")
    res, summary, nc = asyncio.run(m._execute_airwave_tool(
        "send_radio_pitch",
        {"target_id": _TARGET_ID, "subject": "s", "body": "b"},
        "artist-9"))
    assert res["status"] == "sent"
    assert summary["result"] == "radio pitch sent"
    assert nc is False

    # a curator-related doctrine topic surfaces the out-of-scope boundary
    res2, summary2, nc2 = asyncio.run(m._execute_airwave_tool(
        "lookup_radio_promo_doctrine", {"topic": "playlist_curators"}, "artist-9"))
    assert res2["status"] == "out_of_scope"
    assert summary2["result"] == "out_of_scope"
    assert "marcus" in res2["owner"].lower()
    assert nc2 is False
