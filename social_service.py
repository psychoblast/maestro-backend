"""
PLMKR Social Service — Phase 3
Handles social post scheduling (Buffer API), Riley persona post generation,
weekly report aggregation, and Claude Sonnet-powered weekly synthesis.

Same architecture as pr_service.py — self-contained, no circular imports.
Tables always live in SQLite. Buffer tokens stored in artist profile.
"""

import os
import re
import json
import uuid
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import anthropic

log = logging.getLogger("social_service")

# ── Config ────────────────────────────────────────────────────────────────────
_DB_PATH       = Path(os.environ.get("DB_PATH", "/data/memory.db"))
_DATABASE_URL  = os.environ.get("DATABASE_URL", "")
_ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
_MODEL_HAIKU   = "claude-haiku-4-5-20251001"
_MODEL_SONNET  = "claude-sonnet-4-6"           # used for weekly reports (synthesis quality)

_BUFFER_CLIENT_ID     = os.environ.get("BUFFER_CLIENT_ID", "")
_BUFFER_CLIENT_SECRET = os.environ.get("BUFFER_CLIENT_SECRET", "")
_BUFFER_REDIRECT_URI  = os.environ.get("BUFFER_REDIRECT_URI", "")
_BUFFER_AUTH_URL      = "https://bufferapp.com/oauth2/authorize"
_BUFFER_TOKEN_URL     = "https://api.bufferapp.com/1/oauth2/token.json"
_BUFFER_POST_URL      = "https://api.bufferapp.com/1/updates/create.json"

_SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "").lower() == "true"

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# DB: Social + Report tables (always SQLite)
# ═══════════════════════════════════════════════════════════════════════════════

def init_social_db():
    """Create social_posts and weekly_reports tables. Idempotent."""
    Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS social_posts (
            id               TEXT PRIMARY KEY,
            artist_id        TEXT NOT NULL,
            platform         TEXT NOT NULL,
            content          TEXT NOT NULL,
            media_url        TEXT DEFAULT '',
            status           TEXT DEFAULT 'draft',
            scheduled_at     TEXT,
            posted_at        TEXT,
            post_url         TEXT DEFAULT '',
            engagement_stats TEXT DEFAULT '{}',
            buffer_update_id TEXT DEFAULT '',
            created_at       TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_social_posts_artist "
        "ON social_posts (artist_id)"
    )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weekly_reports (
            id              TEXT PRIMARY KEY,
            artist_id       TEXT NOT NULL,
            week_start      TEXT NOT NULL,
            week_end        TEXT NOT NULL,
            summary         TEXT DEFAULT '{}',
            insights        TEXT DEFAULT '',
            recommendations TEXT DEFAULT '',
            momentum_score  INTEGER DEFAULT 5,
            headline        TEXT DEFAULT '',
            highlights      TEXT DEFAULT '[]',
            generated_at    TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_weekly_reports_artist "
        "ON weekly_reports (artist_id)"
    )
    # Schema migration for existing DBs
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(weekly_reports)").fetchall()}
    for col, ddl in [
        ("momentum_score", "INTEGER DEFAULT 5"),
        ("headline",       "TEXT DEFAULT ''"),
        ("highlights",     "TEXT DEFAULT '[]'"),
    ]:
        if col not in existing_cols:
            try:
                conn.execute(f"ALTER TABLE weekly_reports ADD COLUMN {col} {ddl}")
            except sqlite3.OperationalError:
                pass
    conn.commit()
    conn.close()
    print("[Social] SQLite social + report tables ready")


# ── Artist data helpers (same Postgres/SQLite routing pattern) ────────────────

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
    serialized = json.dumps(data)
    if _DATABASE_URL:
        try:
            import psycopg2
            with psycopg2.connect(_DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO artists (artist_id, data) VALUES (%s, %s) "
                        "ON CONFLICT (artist_id) DO UPDATE SET data = EXCLUDED.data",
                        (artist_id, json.dumps(data)),
                    )
            return
        except Exception:
            pass
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        "INSERT OR REPLACE INTO artists (artist_id, data) VALUES (?,?)",
        (artist_id, serialized),
    )
    conn.commit()
    conn.close()


# ── JSON parse helper ─────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text.strip())
    return json.loads(text)


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 3.1 — SocialPost CRUD
# ═══════════════════════════════════════════════════════════════════════════════

_SP_COLS = [
    "id", "artist_id", "platform", "content", "media_url", "status",
    "scheduled_at", "posted_at", "post_url", "engagement_stats",
    "buffer_update_id", "created_at",
]


def _sp_row_to_dict(row, cols) -> dict:
    d = dict(zip(cols, row))
    try:
        d["engagement_stats"] = json.loads(d["engagement_stats"]) if d["engagement_stats"] else {}
    except Exception:
        d["engagement_stats"] = {}
    return d


def _db_list_posts(
    artist_id: str, platform: str = "", status: str = ""
) -> list[dict]:
    conn   = sqlite3.connect(str(_DB_PATH))
    cur    = conn.cursor()
    q      = f"SELECT {','.join(_SP_COLS)} FROM social_posts WHERE artist_id=?"
    params: list = [artist_id]
    if platform:
        q += " AND platform=?"; params.append(platform)
    if status:
        q += " AND status=?"; params.append(status)
    q += " ORDER BY scheduled_at ASC, created_at DESC"
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return [_sp_row_to_dict(r, _SP_COLS) for r in rows]


def _db_get_post(post_id: str) -> dict:
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    cur.execute(
        f"SELECT {','.join(_SP_COLS)} FROM social_posts WHERE id=?", (post_id,)
    )
    row = cur.fetchone()
    conn.close()
    return _sp_row_to_dict(row, _SP_COLS) if row else {}


def _db_create_post(p: dict) -> dict:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        """INSERT INTO social_posts
           (id,artist_id,platform,content,media_url,status,scheduled_at,
            buffer_update_id)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            p["id"], p["artist_id"], p["platform"], p["content"],
            p.get("media_url", ""), p.get("status", "draft"),
            p.get("scheduled_at"), p.get("buffer_update_id", ""),
        ),
    )
    conn.commit()
    conn.close()
    return p


def _db_update_post(post_id: str, updates: dict):
    if "engagement_stats" in updates and isinstance(updates["engagement_stats"], dict):
        updates = {**updates, "engagement_stats": json.dumps(updates["engagement_stats"])}
    sets = ", ".join(f"{k}=?" for k in updates)
    vals = list(updates.values()) + [post_id]
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(f"UPDATE social_posts SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()


def _db_delete_post(post_id: str):
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("DELETE FROM social_posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()


# ── SocialPost endpoints ──────────────────────────────────────────────────────

class SocialPostIn(BaseModel):
    artist_id: str
    platform: str
    content: str
    media_url: str = ""
    scheduled_at: Optional[str] = None
    status: str = "draft"


class SocialPostPatch(BaseModel):
    content: Optional[str] = None
    media_url: Optional[str] = None
    status: Optional[str] = None
    scheduled_at: Optional[str] = None
    posted_at: Optional[str] = None
    post_url: Optional[str] = None
    engagement_stats: Optional[dict] = None


@router.get("/api/social/posts", tags=["social"])
def list_posts(artist_id: str, platform: str = "", status: str = ""):
    return {"posts": _db_list_posts(artist_id, platform=platform, status=status)}


@router.get("/api/social/posts/{post_id}", tags=["social"])
def get_post(post_id: str):
    p = _db_get_post(post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    return p


@router.post("/api/social/posts", status_code=201, tags=["social"])
def create_post(p: SocialPostIn):
    new_id = str(uuid.uuid4())
    row    = {**p.model_dump(), "id": new_id}
    _db_create_post(row)
    return row


@router.patch("/api/social/posts/{post_id}", tags=["social"])
def patch_post(post_id: str, patch: SocialPostPatch):
    existing = _db_get_post(post_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")
    updates = {k: v for k, v in patch.model_dump().items() if v is not None}
    if updates:
        _db_update_post(post_id, updates)
    return {**existing, **updates}


@router.delete("/api/social/posts/{post_id}", status_code=204, tags=["social"])
def delete_post(post_id: str):
    p = _db_get_post(post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    _db_delete_post(post_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 3.2 — Buffer API integration (mocked send, real OAuth flow stubs)
# ═══════════════════════════════════════════════════════════════════════════════

def _load_buffer_tokens(artist_id: str) -> dict:
    profile = _load_artist_data(artist_id)
    return profile.get("buffer_tokens", {})


def _save_buffer_tokens(artist_id: str, tokens: dict):
    profile = _load_artist_data(artist_id)
    profile["buffer_tokens"] = tokens
    _save_artist_data(artist_id, profile)


class BufferNotConnected(Exception):
    pass


@router.get("/api/buffer/auth", tags=["buffer"])
def buffer_auth(artist_id: str):
    """Redirect artist to Buffer OAuth consent screen."""
    if not _BUFFER_CLIENT_ID:
        raise HTTPException(status_code=503, detail="BUFFER_CLIENT_ID not configured")
    params = urlencode({
        "client_id":     _BUFFER_CLIENT_ID,
        "redirect_uri":  _BUFFER_REDIRECT_URI,
        "response_type": "code",
        "state":         artist_id,
    })
    return RedirectResponse(url=f"{_BUFFER_AUTH_URL}?{params}")


@router.get("/api/buffer/callback", tags=["buffer"])
async def buffer_callback(code: str, state: str):
    """Handle Buffer OAuth callback — exchange code for access token and store it."""
    if not _BUFFER_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Buffer OAuth not configured")
    artist_id = state
    try:
        import httpx
        resp = httpx.post(
            _BUFFER_TOKEN_URL,
            data={
                "client_id":     _BUFFER_CLIENT_ID,
                "client_secret": _BUFFER_CLIENT_SECRET,
                "redirect_uri":  _BUFFER_REDIRECT_URI,
                "code":          code,
                "grant_type":    "authorization_code",
            },
            timeout=15,
        )
        tokens = resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Buffer token exchange failed: {e}")

    _save_buffer_tokens(artist_id, {
        "access_token": tokens.get("access_token"),
        "stored_at":    datetime.now(timezone.utc).isoformat(),
    })
    return {"status": "connected", "artist_id": artist_id}


@router.get("/api/buffer/status", tags=["buffer"])
def buffer_status(artist_id: str):
    tokens = _load_buffer_tokens(artist_id)
    return {"connected": bool(tokens.get("access_token")), "artist_id": artist_id}


async def _buffer_schedule_post(
    artist_id: str,
    content: str,
    profile_ids: list[str],
    media_url: str = "",
    scheduled_at: Optional[str] = None,
) -> dict:
    """
    Schedule a post via Buffer API.
    MOCKED — real Buffer API call is structured but not executed to avoid
    accidental posts during dev. Enable by removing the mock guard below.
    """
    tokens = _load_buffer_tokens(artist_id)
    if not tokens.get("access_token"):
        raise BufferNotConnected(f"Artist {artist_id} has not connected Buffer")

    # ── MOCK: return simulated Buffer response ───────────────────────────────
    # To enable real posting: remove this block and uncomment the httpx call below.
    return {
        "id":        str(uuid.uuid4()),
        "status":    "buffer_queued",
        "mocked":    True,
        "text":      content[:60] + ("…" if len(content) > 60 else ""),
    }

    # ── Real Buffer API call (disabled during dev) ───────────────────────────
    # import httpx
    # payload = {
    #     "text":        content,
    #     "profile_ids[]": profile_ids,
    #     "access_token":  tokens["access_token"],
    # }
    # if scheduled_at:
    #     from datetime import datetime
    #     dt    = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
    #     payload["scheduled_at"] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    # if media_url:
    #     payload["media[link]"] = media_url
    # resp = httpx.post(_BUFFER_POST_URL, data=payload, timeout=15)
    # return resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 3.4 — generateSocialPost() — Riley persona
# ═══════════════════════════════════════════════════════════════════════════════

_PLATFORM_LIMITS = {
    "twitter":   280,
    "instagram": 2200,
    "tiktok":    2200,
    "facebook":  1000,
}

_PLATFORM_STYLE = {
    "twitter":   "punchy, direct, hook in first 8 words, no hashtag overload (max 2), conversational",
    "instagram": "warm and visual, lead with emotion, use 3-5 relevant hashtags at end, emojis ok",
    "tiktok":    "energetic, trend-aware, speak to Gen Z/Millennial, hook is everything, casual",
    "facebook":  "slightly longer form, storytelling tone, community-focused, less hashtags",
}

_RILEY_SYSTEM = (
    "You are Riley, Social Media Manager at Playmaker. You write platform-specific social posts "
    "for artists that sound authentic — not like marketing copy.\n\n"
    "Rules:\n"
    "- Match the platform's native voice exactly (Twitter = punchy, Instagram = visual + warm, "
    "TikTok = energetic + trend-aware, Facebook = community-focused)\n"
    "- Write IN the artist's voice — use their genre, personality, and bio as character reference\n"
    "- Never sound like a press release. Sound like the artist typed it themselves\n"
    "- optimal_posting_window: best day + time window as a string (e.g. 'Tuesday 6-9pm ET')\n"
    "- suggested_media_prompt: a one-sentence image/video description for AI generation or photographer brief\n\n"
    "Return ONLY valid JSON:\n"
    '{"content":"...","suggested_media_prompt":"...","optimal_posting_window":"..."}'
)


async def generate_social_post(
    artist_profile: dict,
    platform: str,
    context: dict,
    tone: str = "authentic",
) -> dict:
    """
    Draft one platform-specific social post for Riley.
    Returns {content, suggested_media_prompt, optimal_posting_window}.
    """
    platform   = platform.lower()
    char_limit = _PLATFORM_LIMITS.get(platform, 280)
    style_note = _PLATFORM_STYLE.get(platform, "")

    artist_name = artist_profile.get("artist_name", "The artist")
    genre       = artist_profile.get("genre", "")
    bio         = (artist_profile.get("bio", "") or "")[:200]

    release = context.get("release", "")
    show    = context.get("show", "")
    news    = context.get("news", "")
    custom  = context.get("custom", "")

    prompt = (
        f"Artist: {artist_name}\n"
        f"Genre: {genre}\n"
        f"Bio snippet: {bio}\n"
        f"Tone: {tone}\n"
        f"Platform: {platform} (character limit: {char_limit})\n"
        f"Platform style: {style_note}\n"
    )
    if release:
        prompt += f"Context — Release: {release}\n"
    if show:
        prompt += f"Context — Show: {show}\n"
    if news:
        prompt += f"Context — News: {news}\n"
    if custom:
        prompt += f"Context — Custom: {custom}\n"
    prompt += "\nWrite the post. Return JSON only."

    _client = anthropic.Anthropic(api_key=_ANTHROPIC_KEY)
    resp    = _client.messages.create(
        model=_MODEL_HAIKU,
        max_tokens=512,
        system=_RILEY_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )
    result = _parse_json(resp.content[0].text)
    # Enforce character limit on content
    content = result.get("content", "")
    if len(content) > char_limit:
        result["content"] = content[:char_limit - 1] + "…"
    return result


class GeneratePostRequest(BaseModel):
    artist_id: str
    platform: str
    context: dict = {}
    tone: str = "authentic"


@router.post("/api/social/posts/generate", tags=["social"])
async def api_generate_post(req: GeneratePostRequest):
    artist = _load_artist_data(req.artist_id)
    try:
        draft = await generate_social_post(artist, req.platform, req.context, req.tone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Post generation failed: {e}")
    return {**draft, "artist_id": req.artist_id, "platform": req.platform}


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 3.5 — schedulePosts() batch orchestration
# ═══════════════════════════════════════════════════════════════════════════════

class BatchPostRequest(BaseModel):
    artist_id: str
    platforms: list[str]
    context: dict = {}
    tone: str = "authentic"
    posts_per_platform: int = 3
    schedule_buffer: bool = False  # True = send to Buffer, False = save as draft
    buffer_profile_ids: list[str] = []  # Buffer profile IDs per platform (artist configures)
    start_date: Optional[str] = None    # ISO date string — first post date, defaults to tomorrow


@router.post("/api/social/posts/batch", tags=["social"])
async def schedule_posts(req: BatchPostRequest):
    """
    Generate req.posts_per_platform posts for each platform.
    Space them evenly across the week starting from start_date.
    Optionally schedule via Buffer (mocked).
    Returns {"generated": N, "scheduled_via_buffer": M, "errors": [...], "post_ids": [...]}.
    """
    artist  = _load_artist_data(req.artist_id)
    results: dict = {
        "generated": 0,
        "scheduled_via_buffer": 0,
        "errors": [],
        "post_ids": [],
    }

    start = (
        datetime.fromisoformat(req.start_date)
        if req.start_date
        else datetime.now(timezone.utc) + timedelta(days=1)
    )
    # Spread posts evenly across 7 days
    total_posts = len(req.platforms) * req.posts_per_platform
    if total_posts > 0:
        spacing = timedelta(days=7) / total_posts
    else:
        spacing = timedelta(days=1)

    post_index = 0
    for platform in req.platforms:
        for i in range(req.posts_per_platform):
            scheduled_at = (start + spacing * post_index).isoformat()
            post_index  += 1

            try:
                draft = await generate_social_post(
                    artist, platform, req.context, req.tone
                )
            except Exception as e:
                results["errors"].append(f"Generation failed for {platform} post {i+1}: {e}")
                continue

            post_id = str(uuid.uuid4())
            post    = {
                "id":           post_id,
                "artist_id":    req.artist_id,
                "platform":     platform,
                "content":      draft["content"],
                "media_url":    "",
                "status":       "draft",
                "scheduled_at": scheduled_at,
            }
            _db_create_post(post)
            results["generated"] += 1
            results["post_ids"].append(post_id)

            if req.schedule_buffer and req.buffer_profile_ids:
                try:
                    buf = await _buffer_schedule_post(
                        req.artist_id, draft["content"],
                        req.buffer_profile_ids, scheduled_at=scheduled_at,
                    )
                    _db_update_post(post_id, {
                        "status":           "scheduled",
                        "buffer_update_id": buf.get("id", ""),
                    })
                    results["scheduled_via_buffer"] += 1
                except BufferNotConnected:
                    results["errors"].append(
                        f"Buffer not connected — {platform} post saved as draft"
                    )
                except Exception as e:
                    results["errors"].append(f"Buffer scheduling failed for {platform}: {e}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 3.6 — WeeklyReport schema + endpoints
# ═══════════════════════════════════════════════════════════════════════════════

_WR_COLS = [
    "id", "artist_id", "week_start", "week_end",
    "summary", "insights", "recommendations",
    "momentum_score", "headline", "highlights", "generated_at",
]


def _wr_row_to_dict(row, cols) -> dict:
    d = dict(zip(cols, row))
    try:
        d["summary"] = json.loads(d["summary"]) if d["summary"] else {}
    except Exception:
        d["summary"] = {}
    try:
        d["highlights"] = json.loads(d["highlights"]) if d["highlights"] else []
    except Exception:
        d["highlights"] = []
    return d


def _db_list_reports(artist_id: str, limit: int = 12) -> list[dict]:
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    cur.execute(
        f"SELECT {','.join(_WR_COLS)} FROM weekly_reports "
        "WHERE artist_id=? ORDER BY week_start DESC LIMIT ?",
        (artist_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [_wr_row_to_dict(r, _WR_COLS) for r in rows]


def _db_get_report(report_id: str) -> dict:
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()
    cur.execute(
        f"SELECT {','.join(_WR_COLS)} FROM weekly_reports WHERE id=?", (report_id,)
    )
    row = cur.fetchone()
    conn.close()
    return _wr_row_to_dict(row, _WR_COLS) if row else {}


def _db_save_report(r: dict):
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        """INSERT OR REPLACE INTO weekly_reports
           (id,artist_id,week_start,week_end,summary,insights,recommendations,
            momentum_score,headline,highlights)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            r["id"], r["artist_id"], r["week_start"], r["week_end"],
            json.dumps(r.get("summary", {})),
            r.get("insights", ""), r.get("recommendations", ""),
            r.get("momentum_score", 5),
            r.get("headline", ""),
            json.dumps(r.get("highlights", [])),
        ),
    )
    conn.commit()
    conn.close()


@router.get("/api/reports/weekly", tags=["reports"])
def list_weekly_reports(artist_id: str, limit: int = 12):
    return {"reports": _db_list_reports(artist_id, limit=limit)}


@router.get("/api/reports/weekly/{report_id}", tags=["reports"])
def get_weekly_report(report_id: str):
    r = _db_get_report(report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r


class GenerateReportRequest(BaseModel):
    artist_id: str
    week_start: Optional[str] = None  # ISO date string, defaults to last Monday
    week_end: Optional[str] = None    # ISO date string, defaults to last Sunday


@router.post("/api/reports/weekly/generate", tags=["reports"])
async def api_generate_weekly_report(req: GenerateReportRequest):
    try:
        report = await generate_weekly_report(req.artist_id, req.week_start, req.week_end)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")
    return report


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 3.7 — generateWeeklyReport() — Claude Sonnet synthesis
# ═══════════════════════════════════════════════════════════════════════════════

_REPORT_SYSTEM = (
    "You are Marcus, Artist Manager at Playmaker. You write weekly management reports "
    "for artists — clear, actionable, no fluff.\n\n"
    "Structure your response as valid JSON:\n"
    "{\n"
    '  "headline": "one sentence summary of the week",\n'
    '  "highlights": ["bullet 1", "bullet 2", "bullet 3"],\n'
    '  "insights": "2-3 paragraph narrative analysis — what the data means for the artist\'s trajectory",\n'
    '  "recommendations": "3-5 concrete actions for next week, numbered, specific",\n'
    '  "momentum_score": 1-10\n'
    "}\n\n"
    "momentum_score: 1=stalled, 5=steady, 10=breakthrough week. "
    "Be honest — a 3/10 week needs honest feedback, not spin. "
    "Base analysis on the actual metrics provided."
)


def _aggregate_week_data(artist_id: str, week_start: str, week_end: str) -> dict:
    """Query all service tables for the given artist + week window."""
    conn = sqlite3.connect(str(_DB_PATH))
    cur  = conn.cursor()

    def count_where(table, extra_where="", params=None):
        base   = f"SELECT COUNT(*) FROM {table} WHERE artist_id=? AND created_at>=? AND created_at<=?"
        qparams = [artist_id, week_start, week_end]
        if extra_where:
            base   += f" AND {extra_where}"
            qparams += (params or [])
        cur.execute(base, qparams)
        row = cur.fetchone()
        return row[0] if row else 0

    def count_status(table, status):
        cur.execute(
            f"SELECT COUNT(*) FROM {table} WHERE artist_id=? AND status=? "
            f"AND created_at>=? AND created_at<=?",
            (artist_id, status, week_start, week_end),
        )
        row = cur.fetchone()
        return row[0] if row else 0

    # All queries wrapped — tables may not exist in test DBs or fresh deploys
    pitches_sent = pitches_replied = 0
    try:
        pitches_sent    = count_status("pitches", "sent")
        pitches_replied = count_status("pitches", "replied")
    except Exception:
        pass

    pr_sent = pr_replied = pr_featured = 0
    try:
        pr_sent     = count_status("pr_outreach", "sent")
        pr_replied  = count_status("pr_outreach", "replied")
        pr_featured = count_status("pr_outreach", "featured")
    except Exception:
        pass

    bk_sent = bk_replied = bk_booked = 0
    try:
        bk_sent    = count_status("booking_inquiries", "sent")
        bk_replied = count_status("booking_inquiries", "replied")
        bk_booked  = count_status("booking_inquiries", "booked")
    except Exception:
        pass

    social_posted = social_scheduled = 0
    try:
        social_posted    = count_status("social_posts", "posted")
        social_scheduled = count_status("social_posts", "scheduled")
    except Exception:
        pass

    conn.close()

    return {
        "week_start":   week_start,
        "week_end":     week_end,
        "pitches": {
            "sent":    pitches_sent,
            "replied": pitches_replied,
            "reply_rate": round(pitches_replied / pitches_sent, 2) if pitches_sent else 0.0,
        },
        "pr_outreach": {
            "sent":     pr_sent,
            "replied":  pr_replied,
            "featured": pr_featured,
        },
        "booking": {
            "sent":    bk_sent,
            "replied": bk_replied,
            "booked":  bk_booked,
        },
        "social": {
            "posted":    social_posted,
            "scheduled": social_scheduled,
        },
    }


async def generate_weekly_report(
    artist_id: str,
    week_start: Optional[str] = None,
    week_end: Optional[str] = None,
) -> dict:
    """
    Aggregate the artist's week data and synthesize with Claude Sonnet.
    Saves report to DB. Returns the full report dict.
    """
    now = datetime.now(timezone.utc)
    if not week_end:
        # Default to last Sunday
        days_since_sunday = (now.weekday() + 1) % 7
        week_end   = (now - timedelta(days=days_since_sunday)).strftime("%Y-%m-%dT23:59:59")
    if not week_start:
        # 7 days before week_end
        we_dt      = datetime.fromisoformat(week_end.replace("Z", "+00:00"))
        week_start = (we_dt - timedelta(days=6)).strftime("%Y-%m-%dT00:00:00")

    artist  = _load_artist_data(artist_id)
    metrics = _aggregate_week_data(artist_id, week_start, week_end)

    artist_name = artist.get("artist_name", "The artist")
    genre       = artist.get("genre", "")

    prompt = (
        f"Artist: {artist_name} | Genre: {genre}\n"
        f"Week: {week_start[:10]} → {week_end[:10]}\n\n"
        f"METRICS:\n{json.dumps(metrics, indent=2)}\n\n"
        "Write the weekly management report. Return JSON only."
    )

    _client = anthropic.Anthropic(api_key=_ANTHROPIC_KEY)
    resp    = _client.messages.create(
        model=_MODEL_SONNET,
        max_tokens=1200,
        system=_REPORT_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    analysis = _parse_json(resp.content[0].text)

    report_id = str(uuid.uuid4())
    report    = {
        "id":              report_id,
        "artist_id":       artist_id,
        "week_start":      week_start,
        "week_end":        week_end,
        "summary":         metrics,
        "insights":        analysis.get("insights", ""),
        "recommendations": analysis.get("recommendations", ""),
        "generated_at":    now.isoformat(),
        "headline":        analysis.get("headline", ""),
        "highlights":      analysis.get("highlights", []),
        "momentum_score":  analysis.get("momentum_score", 5),
    }
    _db_save_report(report)
    log.info("weekly_report_generated", extra={"artist_id": artist_id,
             "action": "weekly_report", "result": "ok",
             "momentum_score": report["momentum_score"]})
    return report


# ═══════════════════════════════════════════════════════════════════════════════
# Unit 3.8 — Scheduled report generation (extends pitch_service's APScheduler)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_artists_with_any_activity() -> list[str]:
    """Return all artist_ids that have at least one record in any service table."""
    conn    = sqlite3.connect(str(_DB_PATH))
    cur     = conn.cursor()
    ids: set = set()
    for table in ("pitches", "pr_outreach", "booking_inquiries", "social_posts"):
        try:
            cur.execute(f"SELECT DISTINCT artist_id FROM {table}")
            ids.update(r[0] for r in cur.fetchall())
        except Exception:
            pass
    conn.close()
    return list(ids)


async def _generate_all_weekly_reports():
    """Scheduler job: generate weekly report for every active artist (Sunday 18:00 UTC)."""
    artists = _get_artists_with_any_activity()
    print(f"[REPORT_SCHEDULER] Generating weekly reports for {len(artists)} artist(s)")
    for aid in artists:
        try:
            report = await generate_weekly_report(aid)
            score  = report.get("momentum_score", "?")
            print(f"[REPORT_SCHEDULER] {aid}: report generated — momentum {score}/10")
        except Exception as e:
            print(f"[REPORT_SCHEDULER] {aid}: report failed — {e}")


def init_report_scheduler():
    """
    Add weekly report job to the existing pitch_service APScheduler instance.
    Called from main.py after init_scheduler(). No-op unless SCHEDULER_ENABLED=true.
    """
    if not _SCHEDULER_ENABLED:
        print("[REPORT_SCHEDULER] Disabled — SCHEDULER_ENABLED not set")
        return
    try:
        from pitch_service import _scheduler
        if _scheduler is None:
            print("[REPORT_SCHEDULER] pitch_service scheduler not running — weekly reports disabled")
            return
        # Sundays at 18:00 UTC — document as TODO for per-artist timezone support
        _scheduler.add_job(
            _generate_all_weekly_reports,
            "cron",
            day_of_week="sun",
            hour=18,
            minute=0,
            id="weekly_reports",
            replace_existing=True,
        )
        print("[REPORT_SCHEDULER] Weekly reports scheduled — Sundays 18:00 UTC")
    except ImportError:
        print("[REPORT_SCHEDULER] pitch_service not importable — scheduler not registered")
    except Exception as e:
        print(f"[REPORT_SCHEDULER] Failed to register: {e}")
