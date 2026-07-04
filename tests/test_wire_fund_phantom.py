"""
PROOF tests — Jade (fund-phantom) Anthropic tool_use loop.

Mirrors tests/test_marcus_tool_use.py / tests/test_wire_lex_cipher.py. Proves
that, in /api/chat_stream:

  (a) Jade emits search_grant_programs → check_eligibility → submit_grant_application
      then a final message; all three mock-first fund_phantom_service functions are
      invoked with the correct args and the stream surfaces a populated `actions`
      event (actions_taken), with FUND_PHANTOM_TOOLS passed on every create() call;
  (b) a NON-fund agent (producer-connect) never receives FUND_PHANTOM_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never FUND_PHANTOM_TOOLS;
  (d) the portal-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries portal_not_connected=True);
  (e) expired portal auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / submission calls —
the Anthropic client is faked and the fund_phantom_service boundary is exercised
through recording wrappers over the REAL (pure, mock-first) functions.
"""
import asyncio
import importlib
import json
import re
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import fund_phantom_service as fps  # pure, mock-first — no network / LLM


def _run(coro):
    """Drive one pure async service call to completion without pytest-asyncio."""
    return asyncio.run(coro)


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
    """Stand-in for async_client.messages.stream(...) — used by the non-fund path."""
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


# ── (a) Jade runs the tool loop and surfaces actions_taken ───────────────────

def test_fund_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected portal so submit_grant_application succeeds (no network).
    monkeypatch.setenv("FUNDING_PORTAL_CONNECTED", "true")

    # Record calls into the REAL (pure) fund_phantom_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, elig_calls, submit_calls = [], [], []
    real_search = m.fund_phantom_service.search_grant_programs
    real_elig   = m.fund_phantom_service.check_eligibility
    real_submit = m.fund_phantom_service.submit_grant_application

    async def rec_search(genre="", region="", max_award=0, country="", track=""):
        search_calls.append({"genre": genre, "region": region, "max_award": max_award,
                             "country": country, "track": track})
        return await real_search(genre=genre, region=region, max_award=max_award,
                                 country=country, track=track)

    async def rec_elig(artist_id, program_id="", requested_amount=0, project_type=""):
        elig_calls.append({"artist_id": artist_id, "program_id": program_id,
                           "requested_amount": requested_amount, "project_type": project_type})
        return await real_elig(artist_id, program_id=program_id,
                               requested_amount=requested_amount, project_type=project_type)

    async def rec_submit(artist_id, program_id, project_title, requested_amount=0):
        submit_calls.append({"artist_id": artist_id, "program_id": program_id,
                             "project_title": project_title, "requested_amount": requested_amount})
        return await real_submit(artist_id, program_id, project_title, requested_amount)

    monkeypatch.setattr(m.fund_phantom_service, "search_grant_programs",    rec_search)
    monkeypatch.setattr(m.fund_phantom_service, "check_eligibility",        rec_elig)
    monkeypatch.setattr(m.fund_phantom_service, "submit_grant_application", rec_submit)

    # Scripted Anthropic responses: search → eligibility → submit → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_grant_programs",
                      input={"genre": "hip-hop", "region": "regional"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="check_eligibility",
                      input={"program_id": "factor-canada-music-fund",
                             "requested_amount": 5000, "project_type": "recording"},
                      id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="submit_grant_application",
                      input={"program_id": "factor-canada-music-fund",
                             "project_title": "Debut EP", "requested_amount": 5000},
                      id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found a program, confirmed you're eligible, and submitted.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Jade.
    def _no_stream(**kw):
        raise AssertionError("fund-phantom must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "fund-phantom",
        "message":   "find me a grant and apply for my EP",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"genre": "hip-hop", "region": "regional", "max_award": 0,
                             "country": "", "track": ""}], search_calls
    assert elig_calls == [{
        "artist_id": "artist-9", "program_id": "factor-canada-music-fund",
        "requested_amount": 5000, "project_type": "recording",
    }], elig_calls
    assert submit_calls == [{
        "artist_id": "artist-9", "program_id": "factor-canada-music-fund",
        "project_title": "Debut EP", "requested_amount": 5000,
    }], submit_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_grant_programs", "check_eligibility", "submit_grant_application"], tools_used
    assert actions_evt["portal_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "program(s) found" in by_tool["search_grant_programs"]["result"]
    # 5000 <= 75000 ceiling, recording in funds / focus "any" → eligible / apply.
    assert "eligible=True" in by_tool["check_eligibility"]["result"]
    assert "apply" in by_tool["check_eligibility"]["result"]
    assert by_tool["submit_grant_application"]["result"] == "application submitted"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, eligibility, submit, final.
    assert len(create_calls) == 4
    # FUND_PHANTOM_TOOLS passed on every fund create call (never other toolsets).
    assert all(kw.get("tools") == m.FUND_PHANTOM_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEX_CIPHER_TOOLS for kw in create_calls)


# ── (b) Non-fund agent never gets fund tools, takes the unchanged path ───────

def test_non_fund_agent_never_receives_fund_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT fund-phantom, NOT lex-cipher, NOT puppet-master
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-fund agent must not invoke the tool_use create loop"
    # No actions event for non-fund agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not fund tools ─────

def test_marcus_still_uses_marcus_tools_not_fund(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the fund gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.FUND_PHANTOM_TOOLS


# ── (d) portal_not_connected (missing credential) handled gracefully ─────────

def test_fund_portal_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No portal connected → submit_grant_application raises FundingPortalNotConnected.
    monkeypatch.delenv("FUNDING_PORTAL_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="submit_grant_application",
                      input={"program_id": "gp-touring-development",
                             "project_title": "Spring Tour"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a funding portal first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "fund-phantom",
        "message":   "submit my touring grant",
        "artist_id": "artist-no-portal",
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
    assert actions_evt["portal_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "portal_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_fund_portal_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("FUNDING_PORTAL_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="submit_grant_application",
                      input={"program_id": "gp-video-production",
                             "project_title": "Single Video"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your funding portal auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "fund-phantom",
        "message":   "submit my video grant",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["portal_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "portal_auth_expired"


# ═════════════════════════════════════════════════════════════════════════════
# Unit 2 — real logic over the structured grant_data axes.
# These exercise the pure fund_phantom_service functions directly (deterministic,
# no stream / LLM / network). They prove the lossy back-compat filters were
# replaced with country/track-aware search and funds-membership eligibility.
# ═════════════════════════════════════════════════════════════════════════════

# ── search: country filter excludes wrong-country funds ──────────────────────

def test_search_country_filter_excludes_wrong_country():
    # A UK-scoped query must NOT surface FACTOR (a Canadian fund).
    res = _run(fps.search_grant_programs(country="UK"))
    ids = [p["id"] for p in res["programs"]]
    assert "factor-canada-music-fund" not in ids
    assert res["count"] > 0, "UK should still have funds"
    assert all(p["country"] == "UK" for p in res["programs"]), ids
    # Case-insensitive code match still works.
    assert _run(fps.search_grant_programs(country="ca"))["count"] > 0


# ── search: crowdfunding excluded unless explicitly requested ────────────────

def test_search_excludes_crowdfunding_unless_requested():
    normal = _run(fps.search_grant_programs())
    assert normal["count"] > 0
    assert all(p["track"] != "crowdfunding" for p in normal["programs"]), \
        "crowdfunding must not appear in a normal grant search"
    # Even a country search must not leak crowdfunding.
    au = _run(fps.search_grant_programs(country="AU"))
    assert all(p["track"] != "crowdfunding" for p in au["programs"])
    # Explicit opt-in returns exactly the six crowdfunding records.
    cf = _run(fps.search_grant_programs(track="crowdfunding"))
    assert cf["count"] == 6
    assert all(p["track"] == "crowdfunding" for p in cf["programs"])


# ── search: track filter ─────────────────────────────────────────────────────

def test_search_track_filter_arts_council():
    res = _run(fps.search_grant_programs(track="arts_council"))
    assert res["count"] > 0
    assert all(p["track"] == "arts_council" for p in res["programs"])


# ── eligibility: project_type membership in funds (not scalar focus) ─────────

def test_eligibility_project_type_membership():
    # recording IS in FACTOR's funds → eligible / apply.
    ok = _run(fps.check_eligibility(
        "artist-1", program_id="factor-canada-music-fund",
        requested_amount=5000, project_type="recording"))
    assert ok["eligible"] is True
    assert ok["recommendation"] == "apply"
    assert "recording" in ok["funds"]
    assert ok["currency"] == "CAD"           # currency surfaced, no FX
    assert ok["country"] == "CA"
    assert ok["track"] == "industry"
    assert ok["amount_unlisted"] is False

    # production is NOT in FACTOR's funds → purpose mismatch → ineligible.
    bad = _run(fps.check_eligibility(
        "artist-1", program_id="factor-canada-music-fund",
        requested_amount=5000, project_type="production"))
    assert bad["eligible"] is False
    assert bad["recommendation"] == "ineligible"
    assert any("not in program funds" in r for r in bad["reasons"]), bad["reasons"]


# ── eligibility: stub with unknown ceiling is NOT rejected on amount ─────────

def test_eligibility_stub_amount_unlisted_non_blocking():
    # musicaction has amount_max=None → any requested amount is non-blocking.
    res = _run(fps.check_eligibility(
        "artist-1", program_id="musicaction",
        requested_amount=999_999, project_type="recording"))
    assert res["amount_unlisted"] is True
    assert res["amount_max"] is None
    assert res["eligible"] is True           # not rejected on an unknown cap
    assert res["recommendation"] == "apply"
    assert "amount_unlisted_verify_live" in res["reasons"]


# ── eligibility: over a KNOWN cap → adjust (not ineligible) ──────────────────

def test_eligibility_over_known_cap_recommends_adjust():
    res = _run(fps.check_eligibility(
        "artist-1", program_id="factor-canada-music-fund",
        requested_amount=999_999, project_type="recording"))
    assert res["eligible"] is False
    assert res["recommendation"] == "adjust"
    assert res["amount_unlisted"] is False


# ── suggest_crowdfunding: situational decision helper (pure) ─────────────────

def test_suggest_crowdfunding_raises_when_not_qualified():
    d = fps.suggest_crowdfunding(qualifies_for_grants=False)
    assert d["raise"] is True
    assert len(d["platforms"]) == 6
    assert all(p["track"] == "crowdfunding" for p in d["platforms"])


def test_suggest_crowdfunding_quiet_when_qualified():
    d = fps.suggest_crowdfunding(qualifies_for_grants=True, complements_grant=False)
    assert d["raise"] is False
    assert d["platforms"] == []


def test_suggest_crowdfunding_raises_when_complementary():
    d = fps.suggest_crowdfunding(qualifies_for_grants=True, complements_grant=True)
    assert d["raise"] is True
    assert len(d["platforms"]) == 6


# ══════════════════════════════════════════════════════════════════════════════
# Unit 3 — lookup_grant_deadline (mock-first; real fetch deferred behind the seam)
# ══════════════════════════════════════════════════════════════════════════════
# All deterministic, ZERO real network calls: _fetch_deadline_raw is gated on the
# DEADLINE_LOOKUP_CONNECTED env flag and returns canned data only. "factor-canada-
# music-fund" has a canned found=True deadline; every other enabled program is
# found=False ("round not announced").

# Matches a digit-bearing date: a 4-digit year, a numeric date, or month-name+day.
# Used to prove that no non-found path ever leaks a date the code invented.
_DATE_RE = re.compile(
    r"\b(?:19|20)\d{2}\b"
    r"|\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}\b",
    re.IGNORECASE,
)

_CANNED_PROGRAM = "factor-canada-music-fund"   # has a canned found=True deadline
_UNCANNED_PROGRAM = "musicaction"              # enabled → found=False


def test_deadline_found(monkeypatch):
    monkeypatch.setenv("DEADLINE_LOOKUP_CONNECTED", "true")
    res = _run(fps.lookup_grant_deadline("artist-1", _CANNED_PROGRAM))
    assert res["status"] == "deadline_found"
    assert res["program_id"] == _CANNED_PROGRAM
    assert res["deadline_text"]                       # a concrete date text is present
    assert res["source_url"] == res["official_url"]
    assert res["as_of"]
    # ALWAYS appends the official-page confirmation note (never asserts authority).
    assert "confirm on the official page" in res["message"].lower()
    assert res["official_url"] in res["message"]


def test_round_not_announced(monkeypatch):
    monkeypatch.setenv("DEADLINE_LOOKUP_CONNECTED", "true")
    res = _run(fps.lookup_grant_deadline("artist-1", _UNCANNED_PROGRAM))
    assert res["status"] == "round_not_announced"
    assert "deadline_text" not in res                 # no date field at all
    # No invented date leaks into the human-readable message.
    assert not _DATE_RE.search(res["message"]), res["message"]
    assert res["official_url"] in res["message"]


def test_lookup_unavailable_when_flag_unset(monkeypatch):
    monkeypatch.delenv("DEADLINE_LOOKUP_CONNECTED", raising=False)
    res = _run(fps.lookup_grant_deadline("artist-1", _CANNED_PROGRAM))
    assert res["status"] == "lookup_unavailable"
    assert res["official_url"] in res["message"]       # points to the official page
    assert not _DATE_RE.search(res["message"]), res["message"]


def test_program_not_found_does_not_fire_lookup(monkeypatch):
    # Spy on the seam: for a bogus id the lookup must NEVER be attempted.
    calls = []

    async def spy(program_id, official_url):
        calls.append((program_id, official_url))
        return {"found": False, "source_url": official_url}

    monkeypatch.setenv("DEADLINE_LOOKUP_CONNECTED", "true")
    monkeypatch.setattr(fps, "_fetch_deadline_raw", spy)
    res = _run(fps.lookup_grant_deadline("artist-1", "no-such-program-xyz"))
    assert res["status"] == "program_not_found"
    assert res["program_id"] == "no-such-program-xyz"
    assert calls == []                                 # seam never called
    assert not _DATE_RE.search(res["message"]), res["message"]


def test_no_official_source_when_url_missing(monkeypatch):
    # A program record with an empty URL → no lookup, no date.
    fake_program = {"id": "fund-x", "name": "Fund X", "funder": "Funder X", "url": ""}
    monkeypatch.setattr(fps, "_get_program", lambda pid: fake_program)

    called = []

    async def spy(program_id, official_url):
        called.append(program_id)
        return {"found": False, "source_url": official_url}

    monkeypatch.setenv("DEADLINE_LOOKUP_CONNECTED", "true")
    monkeypatch.setattr(fps, "_fetch_deadline_raw", spy)
    res = _run(fps.lookup_grant_deadline("artist-1", "fund-x"))
    assert res["status"] == "no_official_source"
    assert called == []                                # never attempted a lookup
    assert not _DATE_RE.search(res["message"]), res["message"]


def test_never_invents_a_date_across_no_date_paths(monkeypatch):
    """INVARIANT: not-found / unavailable / no-source paths never emit a date."""
    # round_not_announced (enabled, uncanned program)
    monkeypatch.setenv("DEADLINE_LOOKUP_CONNECTED", "true")
    r1 = _run(fps.lookup_grant_deadline("a", _UNCANNED_PROGRAM))
    # lookup_unavailable (flag unset)
    monkeypatch.delenv("DEADLINE_LOOKUP_CONNECTED", raising=False)
    r2 = _run(fps.lookup_grant_deadline("a", _CANNED_PROGRAM))
    # program_not_found
    r3 = _run(fps.lookup_grant_deadline("a", "bogus-id-123"))

    for r in (r1, r2, r3):
        assert r["status"] in ("round_not_announced", "lookup_unavailable", "program_not_found")
        assert "deadline_text" not in r
        assert not _DATE_RE.search(r["message"]), (r["status"], r["message"])
