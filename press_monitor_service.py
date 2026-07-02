"""
PLMKR Press — Media Monitor action service (mock-first).

Backs the press-monitor (Press, Media Monitor) agent's tool_use loop in /api/chat_stream
(see PRESS_MONITOR_TOOLS in main.py). Press does not just advise — these functions
let the agent take real action: search_media_outlets, analyze_sentiment, and create_media_alert (a real action on the
artist's connected media monitoring account).

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


class MonitoringNotConnected(Exception):
    """Raised when the artist has not connected a media monitoring account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class MonitoringAuthExpired(Exception):
    """Raised when a previously connected media monitoring account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_PRESS_MONITOR_CATALOG = [
    {'id': 'o-1', 'beat': 'indie', 'region': 'uk', 'name': 'The Line of Best Fit', 'note': 'Indie discovery coverage.'},
    {'id': 'o-2', 'beat': 'hip_hop', 'region': 'us', 'name': 'Pigeons & Planes', 'note': 'Emerging hip-hop features.'},
    {'id': 'o-3', 'beat': 'electronic', 'region': 'eu', 'name': 'Resident Advisor', 'note': 'Electronic scene coverage.'},
    {'id': 'o-4', 'beat': 'general', 'region': 'global', 'name': 'Hypebot', 'note': 'Music-industry trade coverage.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_PRESS_MONITOR_HEUR = [
    ('controversy', 'Coverage frames a controversy', 'high'),
    ('disappointing', 'Negative critical framing', 'high'),
    ('derivative', 'Criticised as derivative', 'medium'),
    ('mixed reviews', 'Mixed critical reception', 'medium'),
    ('overhyped', 'Backlash-to-hype narrative forming', 'medium'),
]


async def search_media_outlets(beat: str = "", region: str = "") -> dict:
    """Search the reference catalog by beat and/or region.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (beat or "").strip().lower()
    b = (region or "").strip().lower()
    matches = [
        dict(c)
        for c in _PRESS_MONITOR_CATALOG
        if (not a or a in c["beat"]) and (not b or b in c["region"])
    ]
    return {"items": matches, "count": len(matches)}


async def analyze_sentiment(artist_id: str, coverage_text: str = "", context: str = "") -> dict:
    """Screen coverage_text against known indicators.

    Runs the pure ``_PRESS_MONITOR_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (coverage_text or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _PRESS_MONITOR_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "respond_carefully" if has_high else ("monitor_closely" if findings else "positive")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's media monitoring account.

    Driven purely by the ``PRESS_MONITOR_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise MonitoringAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("PRESS_MONITOR_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise MonitoringAuthExpired("media monitoring account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def create_media_alert(artist_id: str, keyword: str, channel: str = "email") -> dict:
    """Take the alert created action on the artist's connected media monitoring account.

    Raises MonitoringNotConnected / MonitoringAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise MonitoringNotConnected("artist has not connected a media monitoring account")
    name = (keyword or "").strip()
    opt = (channel or "email").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "ALERT-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "keyword": name,
        "channel": opt,
    }
