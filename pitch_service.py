"""
PLMKR Pitch Service — Phase 1 Core Action Layer
Handles Gmail OAuth, email sending, curator DB, pitch generation + tracking, inbox scanning.

Self-contained module — reads env vars directly, no circular imports from main.py.
Pitch tables (curators, pitches, pitch_interactions) always live in SQLite.
Gmail tokens live inside the artist profile (follows main.py Postgres/SQLite routing).
"""

import os
import re
import json
import uuid
import base64
import sqlite3
import email.mime.text
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import anthropic

# ── Config ────────────────────────────────────────────────────────────────────
_DB_PATH        = Path(os.environ.get("DB_PATH", "/data/memory.db"))
_DATABASE_URL   = os.environ.get("DATABASE_URL", "")   # artist-profile reads only
_GMAIL_CLIENT_ID     = os.environ.get("GMAIL_OAUTH_CLIENT_ID", "")
_GMAIL_CLIENT_SECRET = os.environ.get("GMAIL_OAUTH_CLIENT_SECRET", "")
_GMAIL_REDIRECT_URI  = os.environ.get("GMAIL_OAUTH_REDIRECT_URI", "")
_GMAIL_SCOPES   = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]
_SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "").lower() == "true"
_REPLY_POLL_HOURS  = int(os.environ.get("REPLY_POLL_HOURS", "6"))
_ANTHROPIC_KEY     = os.environ.get("ANTHROPIC_API_KEY", "")

_MODEL_HAIKU  = "claude-haiku-4-5-20251001"

router = APIRouter()


# ── DB: pitch tables (always SQLite) ─────────────────────────────────────────

def init_pitch_db():
    """Create artists / curators / pitches / pitch_interactions tables. Idempotent."""
    Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            artist_id TEXT PRIMARY KEY,
            data      TEXT NOT NULL DEFAULT '{}'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS curators (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            outlet          TEXT DEFAULT '',
            genres          TEXT DEFAULT '[]',
            tier            TEXT DEFAULT 'C',
            contact_email   TEXT NOT NULL,
            notes           TEXT DEFAULT '',
            last_pitched_at TEXT,
            response_rate   REAL DEFAULT 0.0,
            created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pitches (
            id              TEXT PRIMARY KEY,
            artist_id       TEXT NOT NULL,
            curator_id      TEXT NOT NULL,
            status          TEXT DEFAULT 'draft',
            subject         TEXT NOT NULL,
            body            TEXT NOT NULL,
            sent_at         TEXT,
            replied_at      TEXT,
            gmail_msg_id    TEXT,
            gmail_thread_id TEXT,
            idempotency_key TEXT UNIQUE,
            created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pitches_artist ON pitches (artist_id)"
    )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pitch_interactions (
            id          TEXT PRIMARY KEY,
            pitch_id    TEXT NOT NULL,
            direction   TEXT NOT NULL,
            content     TEXT NOT NULL,
            sentiment   TEXT DEFAULT 'neutral',
            ts          TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_interactions_pitch ON pitch_interactions (pitch_id)"
    )
    existing_pitch_cols = {r[1] for r in conn.execute("PRAGMA table_info(pitches)").fetchall()}
    if "idempotency_key" not in existing_pitch_cols:
        try:
            conn.execute("ALTER TABLE pitches ADD COLUMN idempotency_key TEXT UNIQUE")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()
    print("[PITCH] SQLite pitch tables ready")


# ── Artist data helpers (routes to Postgres or SQLite matching main.py) ───────

def _load_artist_data(artist_id: str) -> dict:
    if _DATABASE_URL:
        try:
            import psycopg2
            with psycopg2.connect(_DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT data FROM artists WHERE artist_id = %s", (artist_id,)
                    )
                    row = cur.fetchone()
            return dict(row[0]) if row else {}
        except Exception:
            pass
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    cur.execute("SELECT data FROM artists WHERE artist_id=?", (artist_id,))
    row  = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}


def _save_artist_data(artist_id: str, data: dict):
    if _DATABASE_URL:
        try:
            import psycopg2, psycopg2.extras
            with psycopg2.connect(_DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO artists (artist_id, data) VALUES (%s, %s) "
                        "ON CONFLICT (artist_id) DO UPDATE SET data = EXCLUDED.data",
                        (artist_id, psycopg2.extras.Json(data)),
                    )
            return
        except Exception:
            pass
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        "INSERT OR REPLACE INTO artists (artist_id, data) VALUES (?, ?)",
        (artist_id, json.dumps(data)),
    )
    conn.commit()
    conn.close()


def _load_gmail_tokens(artist_id: str) -> dict:
    return _load_artist_data(artist_id).get("gmail_tokens", {})


def _save_gmail_tokens(artist_id: str, tokens: dict):
    data = _load_artist_data(artist_id) or {"artist_id": artist_id}
    data["gmail_tokens"] = tokens
    _save_artist_data(artist_id, data)


# ── Gmail error types ─────────────────────────────────────────────────────────

class GmailNotConnected(Exception):
    pass


class GmailAuthExpired(Exception):
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 1.1 — Gmail OAuth routes
# ═══════════════════════════════════════════════════════════════════════════════

def _build_flow():
    from google_auth_oauthlib.flow import Flow
    return Flow.from_client_config(
        {
            "web": {
                "client_id":     _GMAIL_CLIENT_ID,
                "client_secret": _GMAIL_CLIENT_SECRET,
                "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                "token_uri":     "https://oauth2.googleapis.com/token",
                "redirect_uris": [_GMAIL_REDIRECT_URI],
            }
        },
        scopes=_GMAIL_SCOPES,
    )


@router.get("/api/gmail/auth", tags=["gmail"])
def gmail_auth(artist_id: str):
    """Redirect artist to Google OAuth consent screen."""
    if not (_GMAIL_CLIENT_ID and _GMAIL_CLIENT_SECRET and _GMAIL_REDIRECT_URI):
        raise HTTPException(
            status_code=503,
            detail="Gmail OAuth not configured — set GMAIL_OAUTH_CLIENT_ID, "
                   "GMAIL_OAUTH_CLIENT_SECRET, GMAIL_OAUTH_REDIRECT_URI on Railway.",
        )
    try:
        flow = _build_flow()
        flow.redirect_uri = _GMAIL_REDIRECT_URI
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            state=artist_id,
        )
        return RedirectResponse(auth_url)
    except ImportError:
        raise HTTPException(status_code=503, detail="google-auth-oauthlib not installed")


@router.get("/api/gmail/callback", tags=["gmail"])
def gmail_callback(code: str, state: str):
    """Exchange OAuth code for tokens and persist in artist profile."""
    artist_id = state
    if not artist_id:
        raise HTTPException(status_code=400, detail="Missing artist_id in OAuth state")
    try:
        flow = _build_flow()
        flow.redirect_uri = _GMAIL_REDIRECT_URI
        flow.fetch_token(code=code)
        creds = flow.credentials
        tokens = {
            "access_token":  creds.token,
            "refresh_token": creds.refresh_token,
            "expires_at":    creds.expiry.isoformat() if creds.expiry else None,
            "token_uri":     creds.token_uri,
            "client_id":     creds.client_id,
            "client_secret": creds.client_secret,
            "scopes":        list(creds.scopes) if creds.scopes else _GMAIL_SCOPES,
        }
        _save_gmail_tokens(artist_id, tokens)
        print(f"[GMAIL] Tokens saved for artist {artist_id}")
        return {"status": "connected", "artist_id": artist_id}
    except ImportError:
        raise HTTPException(status_code=503, detail="google-auth-oauthlib not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {e}")


@router.get("/api/gmail/status", tags=["gmail"])
def gmail_status(artist_id: str):
    """Return whether artist has active Gmail tokens."""
    tokens = _load_gmail_tokens(artist_id)
    return {"connected": bool(tokens.get("access_token")), "artist_id": artist_id}


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 1.2 — sendEmail() with token refresh
# ═══════════════════════════════════════════════════════════════════════════════

def _get_gmail_service(artist_id: str):
    """
    Return an authenticated Gmail API service object.
    Refreshes access_token if expired. Raises GmailNotConnected / GmailAuthExpired.
    """
    tokens = _load_gmail_tokens(artist_id)
    if not tokens.get("access_token"):
        raise GmailNotConnected(f"No Gmail tokens for artist {artist_id}")

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        raise GmailNotConnected("google-api-python-client not installed")

    creds = Credentials(
        token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token"),
        token_uri=tokens.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=tokens.get("client_id", _GMAIL_CLIENT_ID),
        client_secret=tokens.get("client_secret", _GMAIL_CLIENT_SECRET),
        scopes=tokens.get("scopes", _GMAIL_SCOPES),
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            updated = {
                **tokens,
                "access_token": creds.token,
                "expires_at":   creds.expiry.isoformat() if creds.expiry else None,
            }
            _save_gmail_tokens(artist_id, updated)
            print(f"[GMAIL] Tokens refreshed for artist {artist_id}")
        except Exception as e:
            raise GmailAuthExpired(f"Token refresh failed: {e}")

    return build("gmail", "v1", credentials=creds)


def _gmail_execute_with_retry(request, max_retries: int = 3):
    """Execute a Gmail API request, retrying on HTTP 429 with exponential backoff."""
    import time
    delays = [1, 2, 4]
    for attempt in range(max_retries):
        try:
            return request.execute()
        except Exception as exc:
            status = getattr(getattr(exc, "resp", None), "status", None)
            if str(status) == "429" and attempt < max_retries - 1:
                wait = delays[attempt]
                print(f"[GMAIL] 429 rate-limit — retrying in {wait}s (attempt {attempt+1})")
                time.sleep(wait)
                continue
            raise


async def send_email(artist_id: str, to: str, subject: str, body: str) -> dict:
    """
    Send a plain-text email via Gmail API on behalf of the artist.
    Returns {"message_id": ..., "thread_id": ..., "status": "sent"}.
    Raises GmailNotConnected or GmailAuthExpired on auth failure.
    Retries up to 3 times on HTTP 429 with 1s/2s/4s backoff.
    """
    service = _get_gmail_service(artist_id)
    msg = email.mime.text.MIMEText(body, "plain", "utf-8")
    msg["to"]      = to
    msg["subject"] = subject
    raw    = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = _gmail_execute_with_retry(
        service.users().messages().send(userId="me", body={"raw": raw})
    )
    print(f"[GMAIL] Sent to {to} | msg_id={result.get('id')}")
    return {
        "message_id": result.get("id"),
        "thread_id":  result.get("threadId"),
        "status":     "sent",
    }


class SendEmailRequest(BaseModel):
    artist_id: str
    to: str
    subject: str
    body: str


@router.post("/api/gmail/send", tags=["gmail"])
async def api_send_email(req: SendEmailRequest):
    """Send a one-off email via artist's connected Gmail account."""
    try:
        return await send_email(req.artist_id, req.to, req.subject, req.body)
    except GmailNotConnected:
        raise HTTPException(
            status_code=403,
            detail="Gmail not connected. Visit /api/gmail/auth?artist_id=... to connect.",
        )
    except GmailAuthExpired:
        raise HTTPException(
            status_code=403,
            detail="Gmail auth expired. Re-connect at /api/gmail/auth?artist_id=...",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 1.3 — Curator + Pitch + PitchInteraction CRUD
# ═══════════════════════════════════════════════════════════════════════════════

# ── Curator helpers ───────────────────────────────────────────────────────────

def _curator_row_to_dict(row, cols) -> dict:
    d = dict(zip(cols, row))
    try:
        d["genres"] = json.loads(d["genres"]) if d["genres"] else []
    except Exception:
        d["genres"] = []
    return d


def _db_list_curators(genre: str = "", tier: str = "") -> list[dict]:
    cols  = ["id","name","outlet","genres","tier","contact_email",
             "notes","last_pitched_at","response_rate","created_at"]
    conn  = sqlite3.connect(str(_DB_PATH))
    cur   = conn.cursor()
    q     = f"SELECT {','.join(cols)} FROM curators WHERE 1=1"
    params: list = []
    if tier:
        q += " AND tier=?";  params.append(tier)
    if genre:
        q += " AND genres LIKE ?";  params.append(f"%{genre}%")
    q += " ORDER BY tier ASC, response_rate DESC"
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return [_curator_row_to_dict(r, cols) for r in rows]


def _db_get_curator(curator_id: str) -> dict:
    cols = ["id","name","outlet","genres","tier","contact_email",
            "notes","last_pitched_at","response_rate","created_at"]
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    cur.execute(f"SELECT {','.join(cols)} FROM curators WHERE id=?", (curator_id,))
    row  = cur.fetchone()
    conn.close()
    return _curator_row_to_dict(row, cols) if row else {}


def _db_upsert_curator(c: dict):
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        """INSERT OR REPLACE INTO curators
           (id, name, outlet, genres, tier, contact_email, notes, last_pitched_at, response_rate)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            c["id"], c["name"], c.get("outlet", ""),
            json.dumps(c.get("genres", [])), c.get("tier", "C"),
            c["contact_email"], c.get("notes", ""),
            c.get("last_pitched_at"), c.get("response_rate", 0.0),
        ),
    )
    conn.commit()
    conn.close()


# ── Pitch helpers ─────────────────────────────────────────────────────────────

_PITCH_COLS = ["id","artist_id","curator_id","status","subject","body",
               "sent_at","replied_at","gmail_msg_id","gmail_thread_id",
               "idempotency_key","created_at"]


def _db_create_pitch(p: dict) -> dict:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        """INSERT INTO pitches
           (id, artist_id, curator_id, status, subject, body,
            gmail_msg_id, gmail_thread_id, idempotency_key)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (p["id"], p["artist_id"], p["curator_id"], p.get("status","draft"),
         p["subject"], p["body"], p.get("gmail_msg_id"), p.get("gmail_thread_id"),
         p.get("idempotency_key", str(uuid.uuid4()))),
    )
    conn.commit()
    conn.close()
    return p


def _db_update_pitch(pitch_id: str, updates: dict):
    sets   = ", ".join(f"{k}=?" for k in updates)
    vals   = list(updates.values()) + [pitch_id]
    conn   = sqlite3.connect(str(_DB_PATH))
    conn.execute(f"UPDATE pitches SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()


def _db_list_pitches(artist_id: str) -> list[dict]:
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    cur.execute(
        f"SELECT {','.join(_PITCH_COLS)} FROM pitches WHERE artist_id=? ORDER BY created_at DESC",
        (artist_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(_PITCH_COLS, r)) for r in rows]


def _db_get_pitch(pitch_id: str) -> dict:
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    cur.execute(f"SELECT {','.join(_PITCH_COLS)} FROM pitches WHERE id=?", (pitch_id,))
    row  = cur.fetchone()
    conn.close()
    return dict(zip(_PITCH_COLS, row)) if row else {}


# ── PitchInteraction helpers ──────────────────────────────────────────────────

def _db_add_interaction(i: dict):
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        "INSERT INTO pitch_interactions (id, pitch_id, direction, content, sentiment) VALUES (?,?,?,?,?)",
        (i["id"], i["pitch_id"], i["direction"], i["content"], i.get("sentiment","neutral")),
    )
    conn.commit()
    conn.close()


def _db_list_interactions(pitch_id: str) -> list[dict]:
    cols = ["id","pitch_id","direction","content","sentiment","ts"]
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    cur.execute(f"SELECT {','.join(cols)} FROM pitch_interactions WHERE pitch_id=? ORDER BY ts", (pitch_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


# ── Curator endpoints ─────────────────────────────────────────────────────────

class CuratorIn(BaseModel):
    name: str
    outlet: str = ""
    genres: list[str] = []
    tier: str = "C"
    contact_email: str
    notes: str = ""
    response_rate: float = 0.0


class CuratorPatch(BaseModel):
    name: Optional[str] = None
    outlet: Optional[str] = None
    genres: Optional[list[str]] = None
    tier: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None
    response_rate: Optional[float] = None


@router.get("/api/curators", tags=["curators"])
def list_curators(genre: str = "", tier: str = ""):
    return {"curators": _db_list_curators(genre=genre, tier=tier)}


@router.get("/api/curators/{curator_id}", tags=["curators"])
def get_curator(curator_id: str):
    c = _db_get_curator(curator_id)
    if not c:
        raise HTTPException(status_code=404, detail="Curator not found")
    return c


@router.post("/api/curators", status_code=201, tags=["curators"])
def create_curator(c: CuratorIn):
    new_id = str(uuid.uuid4())
    row    = {**c.model_dump(), "id": new_id}
    _db_upsert_curator(row)
    return row


@router.patch("/api/curators/{curator_id}", tags=["curators"])
def patch_curator(curator_id: str, patch: CuratorPatch):
    existing = _db_get_curator(curator_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Curator not found")
    updates = {k: v for k, v in patch.model_dump().items() if v is not None}
    merged  = {**existing, **updates}
    _db_upsert_curator(merged)
    return merged


# ── Pitch endpoints ───────────────────────────────────────────────────────────

class PitchPatch(BaseModel):
    status: Optional[str] = None


@router.get("/api/pitches", tags=["pitches"])
def list_pitches(artist_id: str):
    return {"pitches": _db_list_pitches(artist_id)}


@router.get("/api/pitches/{pitch_id}", tags=["pitches"])
def get_pitch(pitch_id: str):
    p = _db_get_pitch(pitch_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pitch not found")
    p["interactions"] = _db_list_interactions(pitch_id)
    return p


@router.patch("/api/pitches/{pitch_id}", tags=["pitches"])
def patch_pitch(pitch_id: str, patch: PitchPatch):
    p = _db_get_pitch(pitch_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pitch not found")
    updates = {k: v for k, v in patch.model_dump().items() if v is not None}
    if updates:
        _db_update_pitch(pitch_id, updates)
    return {**p, **updates}


# ── Seed endpoint (admin, one-time) ──────────────────────────────────────────

@router.post("/api/curators/seed", tags=["curators"])
def seed_curators_endpoint():
    """Load curators from data/curators_seed.json. Idempotent."""
    seed_path = Path(__file__).parent / "data" / "curators_seed.json"
    if not seed_path.exists():
        raise HTTPException(status_code=404, detail="data/curators_seed.json not found")
    records = json.loads(seed_path.read_text())
    inserted = 0
    for c in records:
        existing = _db_get_curator(c["id"])
        if not existing:
            _db_upsert_curator(c)
            inserted += 1
    return {"seeded": inserted, "skipped": len(records) - inserted, "total": len(records)}


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 1.5 — generatePitchEmail()
# ═══════════════════════════════════════════════════════════════════════════════

_PITCH_SYSTEM = (
    "You are Marcus, Artist Manager at Playmaker. "
    "You write concise, professional pitch emails for music artists to curators.\n\n"
    "Rules:\n"
    "- Subject: under 8 words, specific to the curator's outlet\n"
    "- Body: 3 short paragraphs max\n"
    "  1. Who the artist is + one defining quality\n"
    "  2. The track being pitched + why it fits THIS curator's taste\n"
    "  3. Clear ask: a listen, a feature, or a playlist add\n"
    "- Sign off: Marcus | Playmaker, on behalf of [artist]\n"
    "- No filler, no flattery — curators get 100 pitches a day\n"
    "- suggested_followup_days: 3 for tier A, 5 for tier B, 7 for tier C\n\n"
    "Return ONLY valid JSON: "
    '{"subject":"...","body":"...","suggested_followup_days":5}'
)


def _parse_json_response(text: str) -> dict:
    """Strip markdown fences and parse JSON from Claude response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text.strip())
    return json.loads(text)


async def generate_pitch_email(
    artist_profile: dict, track_metadata: dict, curator: dict
) -> dict:
    """
    Use Claude (Haiku) to draft a curator pitch.
    Returns {"subject": str, "body": str, "suggested_followup_days": int}.
    Does NOT send — calling code handles send.
    """
    artist_name  = artist_profile.get("artist_name", "The artist")
    genre        = artist_profile.get("genre", "")
    bio          = (artist_profile.get("bio", "") or "")[:300]
    track_name   = track_metadata.get("name", "new release")
    track_link   = track_metadata.get("link", "")
    track_genre  = track_metadata.get("genre", genre)

    prompt = (
        f"Artist: {artist_name}\n"
        f"Genre: {track_genre or genre}\n"
        f"Bio: {bio}\n"
        f"Track: {track_name}"
        + (f"\nLink: {track_link}" if track_link else "")
        + f"\n\nCurator: {curator['name']}\n"
        f"Outlet: {curator.get('outlet','')}\n"
        f"Covers: {', '.join(curator.get('genres',[]))}\n"
        f"Tier: {curator.get('tier','C')}\n\n"
        "Write the pitch. Return JSON only."
    )

    _client = anthropic.Anthropic(api_key=_ANTHROPIC_KEY)
    resp = _client.messages.create(
        model=_MODEL_HAIKU,
        max_tokens=512,
        system=_PITCH_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )
    return _parse_json_response(resp.content[0].text)


class GeneratePitchRequest(BaseModel):
    artist_id: str
    curator_id: str
    track_metadata: dict = {}


@router.post("/api/pitches/generate", tags=["pitches"])
async def api_generate_pitch(req: GeneratePitchRequest):
    """Generate (but do not send) a pitch draft for one curator."""
    artist  = _load_artist_data(req.artist_id)
    curator = _db_get_curator(req.curator_id)
    if not curator:
        raise HTTPException(status_code=404, detail="Curator not found")
    try:
        draft = await generate_pitch_email(artist, req.track_metadata, curator)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pitch generation failed: {e}")
    return {**draft, "artist_id": req.artist_id, "curator_id": req.curator_id}


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 1.6 — sendPitchEmails() orchestration
# ═══════════════════════════════════════════════════════════════════════════════

class BatchPitchRequest(BaseModel):
    artist_id: str
    curator_ids: list[str]
    track_metadata: dict = {}


@router.post("/api/pitches/batch", tags=["pitches"])
async def send_pitch_emails(req: BatchPitchRequest):
    """
    For each curator_id:
      1. generate_pitch_email()  → draft
      2. _db_create_pitch()      → status=draft
      3. send_email()            → status=sent
    Returns {"sent": N, "failed": M, "errors": [...], "pitch_ids": [...]}.
    """
    artist  = _load_artist_data(req.artist_id)
    results: dict = {"sent": 0, "failed": 0, "errors": [], "pitch_ids": []}

    for curator_id in req.curator_ids:
        curator = _db_get_curator(curator_id)
        if not curator:
            results["failed"] += 1
            results["errors"].append(f"Curator {curator_id} not found")
            continue

        try:
            draft = await generate_pitch_email(artist, req.track_metadata, curator)
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Generation failed for {curator_id}: {e}")
            continue

        pitch_id = str(uuid.uuid4())
        pitch    = {
            "id":         pitch_id,
            "artist_id":  req.artist_id,
            "curator_id": curator_id,
            "status":     "draft",
            "subject":    draft["subject"],
            "body":       draft["body"],
        }
        _db_create_pitch(pitch)

        try:
            sent = await send_email(
                req.artist_id, curator["contact_email"], draft["subject"], draft["body"]
            )
            now = datetime.now(timezone.utc).isoformat()
            _db_update_pitch(pitch_id, {
                "status":         "sent",
                "sent_at":        now,
                "gmail_msg_id":   sent.get("message_id"),
                "gmail_thread_id":sent.get("thread_id"),
            })
            _db_upsert_curator({**curator, "last_pitched_at": now})
            _db_add_interaction({
                "id":        str(uuid.uuid4()),
                "pitch_id":  pitch_id,
                "direction": "outbound",
                "content":   f"Subject: {draft['subject']}\n\n{draft['body']}",
                "sentiment": "neutral",
            })
            results["sent"]      += 1
            results["pitch_ids"].append(pitch_id)

        except (GmailNotConnected, GmailAuthExpired) as e:
            _db_update_pitch(pitch_id, {"status": "failed"})
            results["failed"] += 1
            results["errors"].append(f"Gmail auth error for {curator_id}: {e}")
        except Exception as e:
            _db_update_pitch(pitch_id, {"status": "failed"})
            results["failed"] += 1
            results["errors"].append(f"Send failed for {curator_id}: {e}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 1.7 — detectReplies() inbox poller
# ═══════════════════════════════════════════════════════════════════════════════

_CLASSIFY_SYSTEM = (
    "Classify this curator reply to a music pitch. "
    "Return ONLY valid JSON: "
    '{"sentiment":"positive|negative|neutral|needs_human","summary":"one sentence"}\n'
    "positive=interested/playlist add confirmed, negative=pass/not a fit, "
    "neutral=auto-reply/ambiguous, needs_human=negotiation/complex question"
)


async def _classify_reply(text: str) -> dict:
    _client = anthropic.Anthropic(api_key=_ANTHROPIC_KEY)
    resp = _client.messages.create(
        model=_MODEL_HAIKU,
        max_tokens=100,
        system=_CLASSIFY_SYSTEM,
        messages=[{"role": "user", "content": text[:2000]}],
    )
    try:
        return _parse_json_response(resp.content[0].text)
    except Exception:
        return {"sentiment": "neutral", "summary": resp.content[0].text[:120]}


def _get_artists_with_sent_pitches() -> list[str]:
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT artist_id FROM pitches WHERE status='sent'")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def _get_sent_pitches(artist_id: str) -> list[dict]:
    cols = ["id","curator_id","gmail_thread_id","gmail_msg_id","subject"]
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    cur.execute(
        f"SELECT {','.join(cols)} FROM pitches WHERE artist_id=? AND status='sent'",
        (artist_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def _extract_body(msg: dict) -> str:
    """Pull plain-text body from a Gmail API message payload."""
    payload = msg.get("payload", {})
    data    = payload.get("body", {}).get("data", "")
    if not data:
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                break
    if not data:
        return "(no body)"
    return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")


async def detect_replies(artist_id: str) -> dict:
    """
    Scan Gmail inbox for replies to sent pitches.
    Matches by threadId first, falls back to subject.
    Classifies each reply with Claude, updates Pitch.status, appends PitchInteraction.
    """
    service = _get_gmail_service(artist_id)
    pitches = _get_sent_pitches(artist_id)
    results: dict = {"scanned": 0, "matched": 0, "classified": []}

    if not pitches:
        return {**results, "note": "No sent pitches to match"}

    thread_map  = {p["gmail_thread_id"]: p for p in pitches if p.get("gmail_thread_id")}
    subject_map = {p["subject"].lower(): p for p in pitches}

    inbox  = service.users().messages().list(
        userId="me", maxResults=50, q="in:inbox"
    ).execute()
    msgs   = inbox.get("messages", [])
    results["scanned"] = len(msgs)

    for ref in msgs:
        msg     = service.users().messages().get(
            userId="me", id=ref["id"], format="full"
        ).execute()
        headers = {h["name"].lower(): h["value"]
                   for h in msg.get("payload", {}).get("headers", [])}
        thread_id = msg.get("threadId")
        subject   = headers.get("subject", "").lower().lstrip("re:").strip()
        from_addr = headers.get("from", "")

        pitch = thread_map.get(thread_id) or subject_map.get(subject)
        if not pitch:
            continue

        body_text     = _extract_body(msg)
        classification = await _classify_reply(body_text)
        sentiment      = classification.get("sentiment", "neutral")
        summary        = classification.get("summary", "")

        now        = datetime.now(timezone.utc).isoformat()
        new_status = "replied" if sentiment in ("positive","needs_human") else (
                     "passed"  if sentiment == "negative" else "replied")
        _db_update_pitch(pitch["id"], {"status": new_status, "replied_at": now})

        curator = _db_get_curator(pitch["curator_id"])
        if curator:
            sent_count = len([p for p in pitches if p["curator_id"] == pitch["curator_id"]])
            new_rate   = min(1.0, curator.get("response_rate", 0.0) + 1.0 / max(sent_count, 1))
            _db_upsert_curator({**curator, "response_rate": round(new_rate, 2)})

        _db_add_interaction({
            "id":        str(uuid.uuid4()),
            "pitch_id":  pitch["id"],
            "direction": "inbound",
            "content":   f"From: {from_addr}\n\n{body_text[:1500]}",
            "sentiment": sentiment,
        })

        results["matched"] += 1
        results["classified"].append({
            "pitch_id":  pitch["id"],
            "from":      from_addr,
            "sentiment": sentiment,
            "summary":   summary,
        })

    return results


@router.post("/api/inbox/scan", tags=["pitches"])
async def api_scan_inbox(artist_id: str):
    """Manually trigger inbox scan for one artist."""
    try:
        return await detect_replies(artist_id)
    except GmailNotConnected:
        raise HTTPException(status_code=403, detail="Gmail not connected")
    except GmailAuthExpired:
        raise HTTPException(status_code=403, detail="Gmail auth expired — re-connect")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 1.8 — APScheduler (opt-in via SCHEDULER_ENABLED=true)
# ═══════════════════════════════════════════════════════════════════════════════

_scheduler = None


def init_scheduler():
    """Called from main.py after app startup. No-op unless SCHEDULER_ENABLED=true."""
    global _scheduler
    if not _SCHEDULER_ENABLED:
        print("[SCHEDULER] Disabled — set SCHEDULER_ENABLED=true to enable inbox polling")
        return
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
    except ImportError:
        print("[SCHEDULER] apscheduler not installed — polling disabled")
        return

    _scheduler = AsyncIOScheduler()

    async def _poll_all():
        artists = _get_artists_with_sent_pitches()
        print(f"[SCHEDULER] Polling {len(artists)} artist(s)")
        for aid in artists:
            try:
                result = await detect_replies(aid)
                print(f"[SCHEDULER] {aid}: {result.get('matched',0)} replies matched")
            except Exception as e:
                print(f"[SCHEDULER] Error polling {aid}: {e}")

    _scheduler.add_job(_poll_all, "interval", hours=_REPLY_POLL_HOURS, id="inbox_poll")
    _scheduler.start()
    print(f"[SCHEDULER] Inbox polling active — every {_REPLY_POLL_HOURS}h")


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 1.9 — Follow-up triggers (day 1 / 3 / 5 per tier)
# ═══════════════════════════════════════════════════════════════════════════════

_FOLLOWUP_SYSTEM = (
    "You are Marcus, Artist Manager at Playmaker. "
    "Write a brief follow-up email (2-3 sentences). "
    "Reference the original pitch. Be polite, direct, non-pushy. "
    "Return ONLY valid JSON: "
    '{"subject":"Re: ...","body":"..."}'
)

_TIER_FOLLOWUP_DAYS = {"A": [1, 3, 5], "B": [3, 5, 7], "C": [5, 7, 10]}


def _get_pitches_needing_followup(artist_id: str = "") -> list[dict]:
    """Return sent, unreplied pitches whose days-since-sent match tier threshold."""
    now  = datetime.now(timezone.utc)
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    q    = ("SELECT id, artist_id, curator_id, subject, sent_at, created_at "
            "FROM pitches WHERE status='sent' AND replied_at IS NULL")
    params: list = []
    if artist_id:
        q += " AND artist_id=?"; params.append(artist_id)
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()

    result = []
    for row in rows:
        pitch_id, a_id, c_id, subject, sent_at, created_at = row
        ref_str = sent_at or created_at
        if not ref_str:
            continue
        try:
            ref     = datetime.fromisoformat(ref_str.replace("Z", "+00:00"))
            days    = (now - ref).days
        except Exception:
            continue
        curator    = _db_get_curator(c_id)
        tier       = (curator.get("tier", "C") if curator else "C")
        thresholds = _TIER_FOLLOWUP_DAYS.get(tier, _TIER_FOLLOWUP_DAYS["C"])
        if days in thresholds:
            result.append({
                "id":            pitch_id,
                "artist_id":     a_id,
                "curator_id":    c_id,
                "subject":       subject,
                "days_since":    days,
                "followup_day":  days,
            })
    return result


async def _generate_followup(original: dict, curator: dict, artist: dict) -> dict:
    prompt = (
        f"Original pitch subject: {original['subject']}\n"
        f"Days since sent: {original.get('followup_day','?')}\n"
        f"Curator: {curator.get('name','')} at {curator.get('outlet','')}\n"
        f"Artist: {artist.get('artist_name','')}\n"
        "Write the follow-up. Return JSON only."
    )
    _client = anthropic.Anthropic(api_key=_ANTHROPIC_KEY)
    resp = _client.messages.create(
        model=_MODEL_HAIKU,
        max_tokens=256,
        system=_FOLLOWUP_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_json_response(resp.content[0].text)


@router.post("/api/pitches/followups/queue", tags=["pitches"])
async def queue_followups(artist_id: str = ""):
    """
    Find sent pitches that hit a follow-up threshold today,
    generate follow-up emails, and send them.
    Returns {"queued": N, "sent": M, "failed": K, "details": [...]}.
    """
    pitches = _get_pitches_needing_followup(artist_id)
    results: dict = {"queued": 0, "sent": 0, "failed": 0, "details": []}

    for p in pitches:
        curator = _db_get_curator(p["curator_id"])
        artist  = _load_artist_data(p["artist_id"])
        if not curator:
            continue

        try:
            followup = await _generate_followup(p, curator, artist)
        except Exception as e:
            results["failed"] += 1
            results["details"].append({"original_pitch_id": p["id"], "error": str(e)})
            continue

        fu_id = str(uuid.uuid4())
        _db_create_pitch({
            "id":         fu_id,
            "artist_id":  p["artist_id"],
            "curator_id": p["curator_id"],
            "status":     "draft",
            "subject":    followup["subject"],
            "body":       followup["body"],
        })
        results["queued"] += 1

        try:
            sent = await send_email(
                p["artist_id"], curator["contact_email"],
                followup["subject"], followup["body"],
            )
            now = datetime.now(timezone.utc).isoformat()
            _db_update_pitch(fu_id, {
                "status":          "sent",
                "sent_at":         now,
                "gmail_msg_id":    sent.get("message_id"),
                "gmail_thread_id": sent.get("thread_id"),
            })
            results["sent"] += 1
            results["details"].append({
                "original_pitch_id": p["id"],
                "followup_pitch_id": fu_id,
                "curator":           curator.get("name"),
                "followup_day":      p.get("followup_day"),
                "status":            "sent",
            })
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "original_pitch_id": p["id"],
                "followup_pitch_id": fu_id,
                "error":             str(e),
            })

    return results
