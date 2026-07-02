"""
PLMKR Cal — Scheduling action service (mock-first).

Backs the schedule-keeper (Cal, Scheduling) agent's tool_use loop in /api/chat_stream
(see SCHEDULE_KEEPER_TOOLS in main.py). Cal does not just advise — these functions
let the agent take real action: search_schedule_templates, check_conflicts, and schedule_event (a real action on the
artist's connected calendar account).

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_connected``) driven by an env flag so tests can toggle
    connected / not-connected / expired deterministically — mirroring
    lex_cipher_service.RegistryNotConnected without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads.
"""
import hashlib
import os


class CalendarNotConnected(Exception):
    """Raised when the artist has not connected a calendar account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class CalendarAuthExpired(Exception):
    """Raised when a previously connected calendar account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_SCHEDULE_KEEPER_CATALOG = [
    {'id': 's-1', 'category': 'release', 'horizon': '8_weeks', 'name': 'Single Rollout', 'note': '8-week countdown checklist to release day.'},
    {'id': 's-2', 'category': 'tour', 'horizon': '12_weeks', 'name': 'Tour Advance', 'note': 'Advance milestones for a run of shows.'},
    {'id': 's-3', 'category': 'content', 'horizon': '4_weeks', 'name': 'Content Calendar', 'note': 'Monthly posting cadence template.'},
    {'id': 's-4', 'category': 'admin', 'horizon': 'quarterly', 'name': 'Royalty Review', 'note': 'Quarterly statement-review reminders.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_SCHEDULE_KEEPER_HEUR = [
    ('double booked', 'Two commitments overlap', 'high'),
    ('release on same day', 'Two releases clash on one date', 'high'),
    ('no travel time', 'No buffer for travel between events', 'medium'),
    ('back to back shows', 'No recovery day between shows', 'medium'),
    ('deadline overlap', 'Multiple deadlines land together', 'medium'),
]


async def search_schedule_templates(category: str = "", horizon: str = "") -> dict:
    """Search the reference catalog by category and/or horizon.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (category or "").strip().lower()
    b = (horizon or "").strip().lower()
    matches = [
        dict(c)
        for c in _SCHEDULE_KEEPER_CATALOG
        if (not a or a in c["category"]) and (not b or b in c["horizon"])
    ]
    return {"items": matches, "count": len(matches)}


async def check_conflicts(artist_id: str, schedule_text: str = "", context: str = "") -> dict:
    """Screen schedule_text against known indicators.

    Runs the pure ``_SCHEDULE_KEEPER_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (schedule_text or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _SCHEDULE_KEEPER_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "resolve_conflicts" if has_high else ("add_buffers" if findings else "clear")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's calendar account.

    Driven purely by the ``SCHEDULE_KEEPER_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise CalendarAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("SCHEDULE_KEEPER_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise CalendarAuthExpired("calendar account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def schedule_event(artist_id: str, event_title: str, calendar: str = "releases") -> dict:
    """Take the event scheduled action on the artist's connected calendar account.

    Raises CalendarNotConnected / CalendarAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise CalendarNotConnected("artist has not connected a calendar account")
    name = (event_title or "").strip()
    opt = (calendar or "releases").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "EVT-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "event_title": name,
        "calendar": opt,
    }
