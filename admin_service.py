"""
PLMKR Admin Service — Stats and deep health endpoints.

GET /api/admin/stats?artist_id=...&since=ISO_DATE
GET /api/admin/health/deep
"""

import os
import shutil
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

log = logging.getLogger("admin_service")

router = APIRouter()

_DB_PATH = Path(os.environ.get("DB_PATH", "/data/memory.db"))


def _conn():
    return sqlite3.connect(str(_DB_PATH))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _count(cur, table: str, where: str, params: tuple) -> int:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params)
        return cur.fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def _max_date(cur, table: str, col: str, where: str, params: tuple) -> Optional[str]:
    try:
        cur.execute(f"SELECT MAX({col}) FROM {table} WHERE {where}", params)
        row = cur.fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None


# ── Stats endpoint ────────────────────────────────────────────────────────────

@router.get("/api/admin/stats", tags=["admin"])
def admin_stats(artist_id: str, since: Optional[str] = None):
    """
    Return activity stats for an artist.
    since: ISO datetime string (optional). If omitted, returns all-time stats.
    """
    if not artist_id:
        raise HTTPException(status_code=400, detail="artist_id is required")

    since_val = since or "1970-01-01T00:00:00"

    conn = _conn()
    cur  = conn.cursor()

    pitches_sent    = _count(cur, "pitches",          "artist_id=? AND status!='draft' AND created_at>=?", (artist_id, since_val))
    pitches_replied = _count(cur, "pitches",          "artist_id=? AND status='replied' AND created_at>=?", (artist_id, since_val))

    pr_sent         = _count(cur, "pr_outreach",      "artist_id=? AND status!='draft' AND created_at>=?", (artist_id, since_val))
    pr_replied      = _count(cur, "pr_outreach",      "artist_id=? AND status='replied' AND created_at>=?", (artist_id, since_val))

    booking_sent    = _count(cur, "booking_inquiries", "artist_id=? AND status!='draft' AND created_at>=?", (artist_id, since_val))
    booking_replied = _count(cur, "booking_inquiries", "artist_id=? AND status='replied' AND created_at>=?", (artist_id, since_val))

    social_published = _count(cur, "social_posts",    "artist_id=? AND status='posted' AND created_at>=?", (artist_id, since_val))

    last_report_date = _max_date(cur, "weekly_reports", "generated_at", "artist_id=?", (artist_id,))

    conn.close()

    def _rate(replied: int, sent: int) -> float:
        return round(replied / sent, 2) if sent > 0 else 0.0

    return {
        "artist_id":             artist_id,
        "since":                 since_val,
        "pitches_sent":          pitches_sent,
        "pitches_replied":       pitches_replied,
        "reply_rate":            _rate(pitches_replied, pitches_sent),
        "pr_sent":               pr_sent,
        "pr_replied":            pr_replied,
        "pr_reply_rate":         _rate(pr_replied, pr_sent),
        "booking_sent":          booking_sent,
        "booking_replied":       booking_replied,
        "booking_reply_rate":    _rate(booking_replied, booking_sent),
        "social_posts_published": social_published,
        "last_report_date":      last_report_date,
    }


# ── Deep health endpoint ──────────────────────────────────────────────────────

def _check_db_connected() -> bool:
    try:
        conn = _conn()
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


def _check_scheduler_running() -> bool:
    try:
        from pitch_service import _scheduler
        return _scheduler is not None and _scheduler.running
    except Exception:
        return False


def _count_gmail_connected() -> int:
    """Count artists who have stored Gmail access tokens in their profile."""
    try:
        conn = _conn()
        cur  = conn.cursor()
        cur.execute("SELECT data FROM artists")
        rows = cur.fetchall()
        conn.close()
        import json
        count = 0
        for (data_str,) in rows:
            try:
                data = json.loads(data_str) if data_str else {}
                if data.get("gmail_tokens", {}).get("access_token"):
                    count += 1
            except Exception:
                pass
        return count
    except Exception:
        return 0


def _count_buffer_connected() -> int:
    """Count artists who have stored Buffer tokens."""
    try:
        conn = _conn()
        cur  = conn.cursor()
        cur.execute("SELECT data FROM artists")
        rows = cur.fetchall()
        conn.close()
        import json
        count = 0
        for (data_str,) in rows:
            try:
                data = json.loads(data_str) if data_str else {}
                if data.get("buffer_tokens", {}).get("access_token"):
                    count += 1
            except Exception:
                pass
        return count
    except Exception:
        return 0


def _disk_usage_pct() -> float:
    try:
        usage = shutil.disk_usage("/")
        return round(usage.used / usage.total * 100, 1)
    except Exception:
        return -1.0


def _security_posture() -> dict:
    """Snapshot of security-relevant env-var state at request time."""
    plmkr_key      = os.environ.get("PLMKR_API_KEY", "")
    anthropic_key  = os.environ.get("ANTHROPIC_API_KEY", "")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    dev_unsigned   = os.environ.get("STRIPE_DEV_ALLOW_UNSIGNED", "").lower() == "true"
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "")

    auth_enabled = bool(plmkr_key)
    return {
        "auth_enabled":                  auth_enabled,
        "auth_mode":                     "enforced" if auth_enabled else "dev-permissive",
        "anthropic_available":           bool(anthropic_key),
        "stripe_signed_webhooks_required": bool(webhook_secret) or not dev_unsigned,
        "stripe_dev_allow_unsigned":     dev_unsigned,
        "cors_origins":                  allowed_origins or "*",
    }


@router.get("/api/admin/health/deep", tags=["admin"])
def admin_health_deep():
    """
    Deep health check: DB, scheduler, OAuth token counts, disk usage, and
    security posture of the running deploy.
    """
    return {
        "timestamp":                     datetime.now(timezone.utc).isoformat(),
        "db_connected":                  _check_db_connected(),
        "scheduler_running":             _check_scheduler_running(),
        "gmail_token_valid_for_artists": _count_gmail_connected(),
        "buffer_token_valid_for_artists": _count_buffer_connected(),
        "disk_usage_pct":                _disk_usage_pct(),
        **_security_posture(),
    }
