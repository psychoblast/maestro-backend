"""
PROOF tests — Nia Unit 2: lookup_brand_deal_doctrine + send_brand_pitch (+ wiring).

lookup_brand_deal_doctrine is a PURE read over brand_partnerships_data (Nia Unit 1)
— each topic returns its section plus the full honesty-rule set; unknown topic ->
structured error; NOT portal-gated. send_brand_pitch follows the Marcus send seam:
the MODEL writes the pitch subject/body in its turn and passes them in — the tool
SENDS (deterministic mock sha1 reference, ZERO network), it NEVER generates or
edits the body, and it NEVER invents a rate. It sits behind the same
BRAND_CONNECT_ACCOUNT_CONNECTED gate as submit_partnership_proposal: connected ->
mock send; not-connected / expired -> raises so the loop degrades to an honest
partnerships_not_connected. Wiring: both schemas in BRAND_CONNECT_TOOLS, dispatch
through Nia's execute path in the real /api/chat_stream loop; the doctrine lookup
is not gated.
"""
import asyncio
import importlib
import json
import re
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import brand_partnerships_data
import brand_connect_service as svc


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


_HONESTY_RULE_IDS = ["no_market_rates_ever", "deal_evaluation_is_structural",
                     "disclosure_not_legal_advice", "facts_supplied_or_marked"]

_BRAND_ID = "brand-v612-apparel"
_PITCH_SUBJECT = "V612 x your Q3 launch — an aligned collab"
_PITCH_BODY = ("Hi V612 team,\n\nMy audience skews exactly into your athleisure "
               "core and I've organically worn the line twice this year. I'd love "
               "to structure a launch collab — happy to share my EPK.\n\n— the artist")


# ── lookup_brand_deal_doctrine (pure read, not gated) ──────────────────────────

def test_lookup_returns_section_and_honesty_for_each_topic(monkeypatch):
    monkeypatch.delenv("BRAND_CONNECT_ACCOUNT_CONNECTED", raising=False)  # not gated
    for topic in svc.BRAND_DOCTRINE_TOPICS:
        res = _run(svc.lookup_brand_deal_doctrine(topic))
        assert res["status"] == "ok", topic
        assert res["topic"] == topic
        assert res["data"] is not None, topic
        assert [r["id"] for r in res["honesty_rules"]] == _HONESTY_RULE_IDS, topic


def test_lookup_deal_term_topic_resolves_to_its_record():
    res = _run(svc.lookup_brand_deal_doctrine("compensation"))
    assert res["data"]["id"] == "compensation"
    assert res["data"]["amounts"] is None  # rate never quoted


def test_lookup_unknown_topic_structured_error():
    res = _run(svc.lookup_brand_deal_doctrine("pricing"))
    assert res["status"] == "unknown_topic"
    assert res["supported_topics"] == list(svc.BRAND_DOCTRINE_TOPICS)
    assert "data" not in res


def test_lookup_topic_normalized_case_and_whitespace():
    res = _run(svc.lookup_brand_deal_doctrine("  Exclusivity "))
    assert res["status"] == "ok"
    assert res["topic"] == "exclusivity"


def test_lookup_results_json_serializable():
    for topic in list(svc.BRAND_DOCTRINE_TOPICS) + ["nope"]:
        json.dumps(_run(svc.lookup_brand_deal_doctrine(topic)))


# ── send_brand_pitch (Marcus send seam; gated; body verbatim; no rates) ────────

def test_send_connected_returns_mock_reference_and_body_verbatim(monkeypatch):
    monkeypatch.setenv("BRAND_CONNECT_ACCOUNT_CONNECTED", "true")
    res = _run(svc.send_brand_pitch("artist-9", _BRAND_ID, _PITCH_SUBJECT, _PITCH_BODY))
    assert res["status"] == "sent"
    assert res["reference"].startswith("BPITCH-")
    assert res["brand_id"] == _BRAND_ID
    # REQUIRED: the tool never edits the model's pitch — subject/body ride byte-exact.
    assert res["subject"] == _PITCH_SUBJECT
    assert res["body"] == _PITCH_BODY


def test_send_never_generates_body_when_model_passes_it(monkeypatch):
    monkeypatch.setenv("BRAND_CONNECT_ACCOUNT_CONNECTED", "connected")
    # An empty body is NOT back-filled by the tool — it sends exactly what it got.
    res = _run(svc.send_brand_pitch("artist-9", _BRAND_ID, "subj", ""))
    assert res["status"] == "sent"
    assert res["body"] == ""


def test_send_not_connected_raises(monkeypatch):
    monkeypatch.delenv("BRAND_CONNECT_ACCOUNT_CONNECTED", raising=False)
    try:
        _run(svc.send_brand_pitch("artist-9", _BRAND_ID, "s", "b"))
        assert False, "expected BrandConnectAccountNotConnected"
    except svc.BrandConnectAccountNotConnected:
        pass


def test_send_expired_raises(monkeypatch):
    monkeypatch.setenv("BRAND_CONNECT_ACCOUNT_CONNECTED", "expired")
    try:
        _run(svc.send_brand_pitch("artist-9", _BRAND_ID, "s", "b"))
        assert False, "expected BrandConnectAuthExpired"
    except svc.BrandConnectAuthExpired:
        pass


def test_send_unknown_brand_is_structured(monkeypatch):
    monkeypatch.setenv("BRAND_CONNECT_ACCOUNT_CONNECTED", "true")
    res = _run(svc.send_brand_pitch("artist-9", "brand-does-not-exist", "s", "b"))
    assert res["status"] == "unknown_brand"


def test_send_result_contains_no_invented_rates(monkeypatch):
    # REQUIRED: the tool adds no fee/rate/amount and no currency figure of its own.
    monkeypatch.setenv("BRAND_CONNECT_ACCOUNT_CONNECTED", "true")
    res = _run(svc.send_brand_pitch("artist-9", _BRAND_ID, "subject with no rate",
                                    "body with no rate"))
    for bad_key in ("fee", "rate", "amount", "price", "proposed_fee"):
        assert bad_key not in res, bad_key
    # no currency symbol anywhere in the tool-produced fields (body/subject here
    # carry none either) and no market figure minted by the tool.
    assert "$" not in json.dumps(res)


# ── wiring through the real /api/chat_stream loop ──────────────────────────────

def test_lookup_dispatch_not_portal_gated(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("BRAND_CONNECT_ACCOUNT_CONNECTED", raising=False)

    lookup_calls = []
    real_lookup = m.brand_connect_service.lookup_brand_deal_doctrine

    async def rec_lookup(topic=""):
        lookup_calls.append({"topic": topic})
        return await real_lookup(topic)

    monkeypatch.setattr(m.brand_connect_service, "lookup_brand_deal_doctrine", rec_lookup)

    responses = [
        _Resp([_Block("tool_use", name="lookup_brand_deal_doctrine",
                      input={"topic": "exclusivity"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here is the exclusivity doctrine to work from.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "brand-connect",
        "message":   "how does exclusivity work?",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    assert lookup_calls == [{"topic": "exclusivity"}]
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["actions_taken"][0]["tool"] == "lookup_brand_deal_doctrine"
    assert "honesty rule(s)" in actions_evt["actions_taken"][0]["result"]
    assert actions_evt["partnerships_not_connected"] is False, \
        "the doctrine lookup must not trip the account gate"
    assert all(kw.get("tools") == m.BRAND_CONNECT_TOOLS for kw in create_calls)


def test_send_brand_pitch_connected_through_loop(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("BRAND_CONNECT_ACCOUNT_CONNECTED", "true")

    responses = [
        _Resp([_Block("tool_use", name="send_brand_pitch",
                      input={"brand_id": _BRAND_ID, "subject": _PITCH_SUBJECT,
                             "body": _PITCH_BODY}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Sent your pitch to V612.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "brand-connect",
        "message":   "send my pitch to V612",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["actions_taken"][0]["tool"] == "send_brand_pitch"
    assert actions_evt["actions_taken"][0]["result"] == "brand pitch sent"
    assert actions_evt["partnerships_not_connected"] is False
    assert "Sent your pitch" in next(e for e in events if e["type"] == "done")["full_text"]


def test_send_brand_pitch_not_connected_through_loop(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("BRAND_CONNECT_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="send_brand_pitch",
                      input={"brand_id": _BRAND_ID, "subject": "s", "body": "b"},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a brand account first.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "brand-connect",
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
    assert actions_evt["partnerships_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "partnerships_not_connected"


def test_dispatch_send_and_unknown_topic_through_execute_path(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("BRAND_CONNECT_ACCOUNT_CONNECTED", "true")
    res, summary, nc = asyncio.run(m._execute_brand_connect_tool(
        "send_brand_pitch",
        {"brand_id": _BRAND_ID, "subject": "s", "body": "b"},
        "artist-9"))
    assert res["status"] == "sent"
    assert summary["result"] == "brand pitch sent"
    assert nc is False

    res2, summary2, nc2 = asyncio.run(m._execute_brand_connect_tool(
        "lookup_brand_deal_doctrine", {"topic": "nope"}, "artist-9"))
    assert res2["status"] == "unknown_topic"
    assert summary2["result"] == "unknown_topic"
    assert nc2 is False
