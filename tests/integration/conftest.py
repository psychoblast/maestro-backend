"""
Shared fixtures for PLMKR integration tests.

Each test gets a fresh in-memory SQLite DB.  Modules are reloaded so the
module-level _DB_PATH constant picks up the temp path.  A minimal FastAPI
app exposes all four service routers — no main.py complexity needed.
"""

import os
import json
import base64
import sqlite3
import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ── DB bootstrap helpers ──────────────────────────────────────────────────────

def _ensure_artists_table(db_path: str):
    """artists table is normally created by main.py._ensure_db() — create it here."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            artist_id TEXT PRIMARY KEY,
            data      TEXT NOT NULL DEFAULT '{}'
        )
    """)
    conn.commit()
    conn.close()


def seed_artist(db_path: str, artist_id: str = "artist-int-001", **extra) -> dict:
    profile = {
        "artist_id":   artist_id,
        "artist_name": extra.get("artist_name", "Integration Artist"),
        "genre":       extra.get("genre", "indie pop"),
        "bio":         extra.get("bio", "Test artist for integration tests."),
        **extra,
    }
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO artists (artist_id, data) VALUES (?, ?)",
        (artist_id, json.dumps(profile)),
    )
    conn.commit()
    conn.close()
    return profile


def seed_gmail_tokens(db_path: str, artist_id: str):
    """Store fake Gmail tokens so send_email() / detect_replies() don't raise GmailNotConnected."""
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()
    cur.execute("SELECT data FROM artists WHERE artist_id=?", (artist_id,))
    row  = cur.fetchone()
    profile = json.loads(row[0]) if row else {"artist_id": artist_id}
    profile["gmail_tokens"] = {"access_token": "fake-access-token", "refresh_token": "fake-refresh"}
    conn.execute(
        "INSERT OR REPLACE INTO artists (artist_id, data) VALUES (?, ?)",
        (artist_id, json.dumps(profile)),
    )
    conn.commit()
    conn.close()


# ── Gmail mock builder helpers ────────────────────────────────────────────────

def make_gmail_message(thread_id: str, subject: str, body_text: str,
                       from_addr: str = "curator@example.com") -> dict:
    data = base64.urlsafe_b64encode(body_text.encode()).decode()
    return {
        "id":       "gmail-msg-001",
        "threadId": thread_id,
        "payload": {
            "headers": [
                {"name": "Subject", "value": f"Re: {subject}"},
                {"name": "From",    "value": from_addr},
            ],
            "body":  {"data": data},
            "parts": [],
        },
    }


class _FakeGmailBatch:
    """Scripted stand-in for a googleapiclient BatchHttpRequest.

    detect_replies now fetches message details via a single batch request. This
    fake records each added request's id and, on execute(), invokes the callback
    with the scripted message for that id — ZERO real API calls.
    """
    def __init__(self, callback, id_to_msg):
        self._callback  = callback
        self._id_to_msg = id_to_msg
        self._pending   = []

    def add(self, request, request_id=None):
        self._pending.append(request_id)

    def execute(self):
        for rid in self._pending:
            self._callback(rid, self._id_to_msg.get(rid), None)


def mock_gmail_service(thread_id: str, subject: str, body_text: str) -> object:
    """Return a mock Gmail API service that simulates one inbox message."""
    from unittest.mock import MagicMock
    svc     = MagicMock()
    msg     = make_gmail_message(thread_id, subject, body_text)
    inbox   = {"messages": [{"id": "gmail-msg-001", "threadId": thread_id}]}
    (svc.users.return_value.messages.return_value
        .list.return_value.execute.return_value) = inbox
    # pitch_service.detect_replies fetches via a batch request; pr_service and
    # booking_service still fetch each message with get().execute(). Script BOTH
    # so this shared fake serves every consumer.
    (svc.users.return_value.messages.return_value
        .get.return_value.execute.return_value)  = msg
    id_to_msg = {"gmail-msg-001": msg}
    svc.new_batch_http_request.side_effect = (
        lambda callback: _FakeGmailBatch(callback, id_to_msg)
    )
    return svc


# ── App factory ───────────────────────────────────────────────────────────────

def build_app(db_path: str) -> FastAPI:
    """
    Build a minimal FastAPI app with all 4 service routers.
    Reloads every service module so _DB_PATH picks up the temp path.
    """
    os.environ["DB_PATH"]             = db_path
    os.environ["DATABASE_URL"]        = ""
    os.environ["ANTHROPIC_API_KEY"]   = "sk-test"
    os.environ["GMAIL_OAUTH_CLIENT_ID"]     = "test-client-id"
    os.environ["GMAIL_OAUTH_CLIENT_SECRET"] = "test-secret"
    os.environ["GMAIL_OAUTH_REDIRECT_URI"]  = "http://localhost/callback"

    import pitch_service, pr_service, booking_service, social_service
    for mod in (pitch_service, pr_service, booking_service, social_service):
        importlib.reload(mod)

    _ensure_artists_table(db_path)
    pitch_service.init_pitch_db()
    pr_service.init_pr_db()
    booking_service.init_booking_db()
    social_service.init_social_db()

    app = FastAPI(title="PLMKR Integration Test App")
    app.include_router(pitch_service.router)
    app.include_router(pr_service.router)
    app.include_router(booking_service.router)
    app.include_router(social_service.router)
    return app


# ── Per-test fixtures ─────────────────────────────────────────────────────────

@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture()
def client(db_path):
    app = build_app(db_path)
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture()
def artist_id():
    return "artist-int-001"


@pytest.fixture()
def seeded_artist(db_path, artist_id):
    return seed_artist(db_path, artist_id)


@pytest.fixture()
def gmail_ready(db_path, artist_id, seeded_artist):
    """Artist exists + has Gmail tokens stored."""
    seed_gmail_tokens(db_path, artist_id)
    return artist_id


# ── Additional helpers added Unit 2 (May 15) ─────────────────────────────────

def make_claude_response(payload: dict) -> object:
    """Return a MagicMock that looks like an anthropic.Message with JSON content."""
    import json as _json
    from unittest.mock import MagicMock
    m = MagicMock()
    m.content = [MagicMock(text=_json.dumps(payload))]
    return m


def make_send_gmail_svc(thread_id: str, msg_id: str = "msg-001") -> object:
    """Return a MagicMock Gmail service that simulates a successful send.

    Mocks at the google-api-client boundary:
      service.users().messages().send(...).execute()  → {"id": ..., "threadId": ...}
    """
    from unittest.mock import MagicMock
    svc = MagicMock()
    (svc.users.return_value.messages.return_value
        .send.return_value.execute.return_value) = {"id": msg_id, "threadId": thread_id}
    return svc


def build_release_app(db_path: str) -> "FastAPI":
    """Build a test FastAPI app that includes all 5 service routers (pitch+pr+booking+social+release)."""
    import importlib
    os.environ["DB_PATH"]             = db_path
    os.environ["DATABASE_URL"]        = ""
    os.environ["ANTHROPIC_API_KEY"]   = "sk-test"
    os.environ["GMAIL_OAUTH_CLIENT_ID"]     = "test-client-id"
    os.environ["GMAIL_OAUTH_CLIENT_SECRET"] = "test-secret"
    os.environ["GMAIL_OAUTH_REDIRECT_URI"]  = "http://localhost/callback"

    import pitch_service, pr_service, booking_service, social_service, release_service
    for mod in (pitch_service, pr_service, booking_service, social_service, release_service):
        importlib.reload(mod)

    _ensure_artists_table(db_path)
    pitch_service.init_pitch_db()
    pr_service.init_pr_db()
    booking_service.init_booking_db()
    social_service.init_social_db()
    release_service.init_release_db()

    app = FastAPI(title="PLMKR Scheduler Test App")
    app.include_router(pitch_service.router)
    app.include_router(pr_service.router)
    app.include_router(booking_service.router)
    app.include_router(social_service.router)
    app.include_router(release_service.router)
    return app


@pytest.fixture()
def mock_anthropic():
    """Fixture: patch anthropic.Anthropic at the SDK boundary with a realistic pitch response.

    _anthropic_call_with_retry still executes, so observability counters increment.
    """
    from unittest.mock import patch, MagicMock
    _default = make_claude_response({
        "subject": "Pitch — Test Artist",
        "body":    "Hi! We'd love to be featured on your playlist.",
    })
    with patch("anthropic.Anthropic") as mc:
        mc.return_value.messages.create.return_value = _default
        yield mc
