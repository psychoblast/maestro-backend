"""
Report 3 (M2) fix — detect_replies() fetched each inbox message with its own
Gmail API round-trip (N+1: up to 50 sequential get().execute() calls). It now
fetches every message detail in ONE batched request (service.new_batch_http_request).

These tests use a fully SCRIPTED fake Gmail service (ZERO real API calls) to prove:
  1. exactly one batch.execute() is issued, and no per-message get().execute()
     ever runs (the N+1 is gone);
  2. output shape is preserved across multiple messages (scanned/matched/classified,
     pitch status transitions, interactions);
  3. a message whose batched fetch errors is skipped while the others still
     process (graceful per-message degradation).
"""
import base64
import importlib

import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    import pitch_service
    importlib.reload(pitch_service)
    pitch_service.init_pitch_db()
    yield


@pytest.fixture()
def ps():
    import pitch_service
    return pitch_service


# ── Scripted fake Gmail service (no MagicMock, no network) ───────────────────

def _gmail_message(thread_id, subject, body_text, from_addr="curator@example.com"):
    data = base64.urlsafe_b64encode(body_text.encode()).decode()
    return {
        "id": thread_id, "threadId": thread_id,
        "payload": {
            "headers": [
                {"name": "Subject", "value": f"Re: {subject}"},
                {"name": "From",    "value": from_addr},
            ],
            "body": {"data": data},
            "parts": [],
        },
    }


class _ListRequest:
    def __init__(self, inbox):
        self._inbox = inbox

    def execute(self):
        return self._inbox


class _GetRequest:
    def __init__(self, msg_id, counters):
        self.msg_id = msg_id
        self._counters = counters

    def execute(self):  # must never be called under the batch path
        self._counters["individual_get_execute"] += 1
        raise AssertionError("individual get().execute() must not run (N+1 regression)")


class _Messages:
    def __init__(self, inbox, counters):
        self._inbox = inbox
        self._counters = counters

    def list(self, **kwargs):
        return _ListRequest(self._inbox)

    def get(self, userId=None, id=None, format=None):
        return _GetRequest(id, self._counters)


class _Users:
    def __init__(self, messages):
        self._messages = messages

    def messages(self):
        return self._messages


class _Batch:
    def __init__(self, callback, id_to_msg, errors, counters):
        self._callback = callback
        self._id_to_msg = id_to_msg
        self._errors = errors
        self._counters = counters
        self._pending = []

    def add(self, request, request_id=None):
        self._pending.append(request_id)

    def execute(self):
        self._counters["batch_execute"] += 1
        for rid in self._pending:
            if rid in self._errors:
                self._callback(rid, None, self._errors[rid])
            else:
                self._callback(rid, self._id_to_msg.get(rid), None)


class _FakeGmailService:
    def __init__(self, inbox, id_to_msg, counters, errors=None):
        self._messages = _Messages(inbox, counters)
        self._id_to_msg = id_to_msg
        self._errors = errors or {}
        self._counters = counters

    def users(self):
        return _Users(self._messages)

    def new_batch_http_request(self, callback):
        return _Batch(callback, self._id_to_msg, self._errors, self._counters)


def _seed_curator(ps, curator_id="cur-1"):
    ps._db_upsert_curator({
        "id": curator_id, "name": "C", "outlet": "O", "genres": ["indie"],
        "tier": "B", "contact_email": "curator@example.com",
        "notes": "", "response_rate": 0.0,
    })


# ── Tests ────────────────────────────────────────────────────────────────────

def test_batch_used_no_n_plus_one(ps):
    """Two matching replies → one batch.execute(), zero individual get().execute()."""
    _seed_curator(ps)
    for pid, tid in (("p1", "thread-1"), ("p2", "thread-2")):
        ps._db_create_pitch({
            "id": pid, "artist_id": "artist-b", "curator_id": "cur-1",
            "status": "sent", "subject": f"subj {pid}", "body": "hi",
            "gmail_thread_id": tid,
        })

    inbox = {"messages": [
        {"id": "thread-1", "threadId": "thread-1"},
        {"id": "thread-2", "threadId": "thread-2"},
    ]}
    id_to_msg = {
        "thread-1": _gmail_message("thread-1", "subj p1", "Love it"),
        "thread-2": _gmail_message("thread-2", "subj p2", "Not for us"),
    }
    counters = {"batch_execute": 0, "individual_get_execute": 0}
    svc = _FakeGmailService(inbox, id_to_msg, counters)

    classify = AsyncMock(return_value={"sentiment": "positive", "summary": "ok"})
    with patch.object(ps, "_get_gmail_service", return_value=svc), \
         patch.object(ps, "_classify_reply", classify):
        import asyncio
        result = asyncio.run(ps.detect_replies("artist-b"))

    assert counters["batch_execute"] == 1, "must fetch via exactly one batch request"
    assert counters["individual_get_execute"] == 0, "no per-message round-trips (N+1 gone)"
    assert result["scanned"] == 2
    assert result["matched"] == 2
    assert len(result["classified"]) == 2
    assert ps._db_get_pitch("p1")["status"] == "replied"


def test_output_shape_matches_single_reply(ps):
    """Single matched reply: same result shape as before the batch refactor."""
    _seed_curator(ps)
    ps._db_create_pitch({
        "id": "p1", "artist_id": "artist-s", "curator_id": "cur-1",
        "status": "sent", "subject": "one", "body": "hi",
        "gmail_thread_id": "thread-1",
    })
    inbox = {"messages": [{"id": "thread-1", "threadId": "thread-1"}]}
    id_to_msg = {"thread-1": _gmail_message("thread-1", "one", "Yes!")}
    counters = {"batch_execute": 0, "individual_get_execute": 0}
    svc = _FakeGmailService(inbox, id_to_msg, counters)

    classify = AsyncMock(return_value={"sentiment": "positive", "summary": "keen"})
    with patch.object(ps, "_get_gmail_service", return_value=svc), \
         patch.object(ps, "_classify_reply", classify):
        import asyncio
        result = asyncio.run(ps.detect_replies("artist-s"))

    assert set(result) >= {"scanned", "matched", "classified"}
    assert result["scanned"] == 1
    assert result["matched"] == 1
    assert result["classified"][0]["from"] == "curator@example.com"
    assert result["classified"][0]["sentiment"] == "positive"


def test_errored_message_is_skipped_others_processed(ps):
    """A message whose batched fetch errors is skipped; the healthy one still matches."""
    _seed_curator(ps)
    for pid, tid in (("p1", "thread-1"), ("p2", "thread-2")):
        ps._db_create_pitch({
            "id": pid, "artist_id": "artist-e", "curator_id": "cur-1",
            "status": "sent", "subject": f"subj {pid}", "body": "hi",
            "gmail_thread_id": tid,
        })
    inbox = {"messages": [
        {"id": "thread-1", "threadId": "thread-1"},
        {"id": "thread-2", "threadId": "thread-2"},
    ]}
    id_to_msg = {"thread-2": _gmail_message("thread-2", "subj p2", "Yes!")}
    errors = {"thread-1": RuntimeError("fetch failed for this message")}
    counters = {"batch_execute": 0, "individual_get_execute": 0}
    svc = _FakeGmailService(inbox, id_to_msg, counters, errors=errors)

    classify = AsyncMock(return_value={"sentiment": "positive", "summary": "ok"})
    with patch.object(ps, "_get_gmail_service", return_value=svc), \
         patch.object(ps, "_classify_reply", classify):
        import asyncio
        result = asyncio.run(ps.detect_replies("artist-e"))

    assert counters["batch_execute"] == 1
    assert result["scanned"] == 2           # both were listed
    assert result["matched"] == 1           # only the healthy one processed
    assert ps._db_get_pitch("p2")["status"] == "replied"
    assert ps._db_get_pitch("p1")["status"] == "sent"   # errored one untouched
