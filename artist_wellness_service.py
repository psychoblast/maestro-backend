"""
PLMKR Maya — Wellness action service (mock-first).

Backs the artist-wellness (Maya, Wellness) agent's tool_use loop in /api/chat_stream
(see ARTIST_WELLNESS_TOOLS in main.py). Maya does not just advise — these functions
let the agent take real action: search_wellness_resources, assess_burnout_risk, and schedule_wellness_checkin (a real action on the
artist's connected wellness scheduling account).

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


class WellnessAccountNotConnected(Exception):
    """Raised when the artist has not connected a wellness scheduling account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class WellnessAccountAuthExpired(Exception):
    """Raised when a previously connected wellness scheduling account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_ARTIST_WELLNESS_CATALOG = [
    {'id': 'w-breath', 'category': 'mindfulness', 'format': 'audio', 'name': 'Box-Breathing Reset', 'note': 'Five-minute pre-show breathing routine.'},
    {'id': 'w-sleep', 'category': 'recovery', 'format': 'guide', 'name': 'Tour Sleep Protocol', 'note': 'Circadian plan for cross-timezone touring.'},
    {'id': 'w-move', 'category': 'physical', 'format': 'video', 'name': 'Green-Room Mobility', 'note': 'Ten-minute movement to counter travel stiffness.'},
    {'id': 'w-noboundary', 'category': 'boundaries', 'format': 'guide', 'name': 'Say-No Scripts', 'note': 'Templates to decline overcommitment without guilt.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_ARTIST_WELLNESS_HEUR = [
    ('exhausted', 'Persistent exhaustion despite rest', 'high'),
    ('no days off', 'No recovery days scheduled', 'high'),
    ('dread', 'Dreading performances or sessions', 'high'),
    ('skipping meals', 'Basic self-care slipping', 'medium'),
    ('cynical', 'Growing cynicism about the work', 'medium'),
]


async def search_wellness_resources(category: str = "", format: str = "") -> dict:
    """Search the reference catalog by category and/or format.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (category or "").strip().lower()
    b = (format or "").strip().lower()
    matches = [
        dict(c)
        for c in _ARTIST_WELLNESS_CATALOG
        if (not a or a in c["category"]) and (not b or b in c["format"])
    ]
    return {"items": matches, "count": len(matches)}


async def assess_burnout_risk(artist_id: str, signals: str = "", context: str = "") -> dict:
    """Screen signals against known indicators.

    Runs the pure ``_ARTIST_WELLNESS_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (signals or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _ARTIST_WELLNESS_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "seek_support" if has_high else ("add_recovery" if findings else "sustainable")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's wellness scheduling account.

    Driven purely by the ``ARTIST_WELLNESS_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise WellnessAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("ARTIST_WELLNESS_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise WellnessAccountAuthExpired("wellness scheduling account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def schedule_wellness_checkin(artist_id: str, topic: str, channel: str = "video") -> dict:
    """Take the check-in scheduled action on the artist's connected wellness scheduling account.

    Raises WellnessAccountNotConnected / WellnessAccountAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise WellnessAccountNotConnected("artist has not connected a wellness scheduling account")
    name = (topic or "").strip()
    opt = (channel or "video").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "WELL-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "topic": name,
        "channel": opt,
    }
