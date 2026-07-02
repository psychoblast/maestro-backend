"""
PLMKR Coach — Performance Coach action service (mock-first).

Backs the live-coach (Coach, Performance Coach) agent's tool_use loop in /api/chat_stream
(see LIVE_COACH_TOOLS in main.py). Coach does not just advise — these functions
let the agent take real action: search_coaching_drills, assess_stage_presence, and schedule_coaching_session (a real action on the
artist's connected coaching calendar account).

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


class CoachingCalendarNotConnected(Exception):
    """Raised when the artist has not connected a coaching calendar account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class CoachingCalendarAuthExpired(Exception):
    """Raised when a previously connected coaching calendar account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_LIVE_COACH_CATALOG = [
    {'id': 'cd-1', 'focus': 'vocals', 'level': 'beginner', 'name': 'Lip Trills', 'note': 'Warm up the voice without strain.'},
    {'id': 'cd-2', 'focus': 'stage_presence', 'level': 'intermediate', 'name': 'Eye-Line Map', 'note': 'Distribute focus across the room.'},
    {'id': 'cd-3', 'focus': 'breath', 'level': 'beginner', 'name': 'Diaphragm Support', 'note': 'Sustain notes without pushing.'},
    {'id': 'cd-4', 'focus': 'endurance', 'level': 'advanced', 'name': 'Full-Set Runthrough', 'note': 'Simulate a 60-minute set for stamina.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_LIVE_COACH_HEUR = [
    ('stares at floor', 'Low eye contact with the audience', 'high'),
    ('no movement', 'Static staging — no use of the space', 'medium'),
    ('out of breath', 'Breath control failing mid-set', 'high'),
    ('no banter', 'No audience connection between songs', 'medium'),
    ('pitchy', 'Pitch drifting under performance pressure', 'medium'),
]


async def search_coaching_drills(focus: str = "", level: str = "") -> dict:
    """Search the reference catalog by focus and/or level.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (focus or "").strip().lower()
    b = (level or "").strip().lower()
    matches = [
        dict(c)
        for c in _LIVE_COACH_CATALOG
        if (not a or a in c["focus"]) and (not b or b in c["level"])
    ]
    return {"items": matches, "count": len(matches)}


async def assess_stage_presence(artist_id: str, performance_notes: str = "", context: str = "") -> dict:
    """Screen performance_notes against known indicators.

    Runs the pure ``_LIVE_COACH_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (performance_notes or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _LIVE_COACH_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "focused_coaching" if has_high else ("refine_stagecraft" if findings else "stage_ready")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's coaching calendar account.

    Driven purely by the ``LIVE_COACH_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise CoachingCalendarAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("LIVE_COACH_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise CoachingCalendarAuthExpired("coaching calendar account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def schedule_coaching_session(artist_id: str, focus: str, channel: str = "video") -> dict:
    """Take the session scheduled action on the artist's connected coaching calendar account.

    Raises CoachingCalendarNotConnected / CoachingCalendarAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise CoachingCalendarNotConnected("artist has not connected a coaching calendar account")
    name = (focus or "").strip()
    opt = (channel or "video").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "COACH-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "focus": name,
        "channel": opt,
    }
