"""
PLMKR Knox — Booking Agent action service (mock-first).

Backs the live-wire (Knox, Booking Agent) agent's tool_use loop in /api/chat_stream
(see LIVE_WIRE_TOOLS in main.py). Knox does not just advise — these functions
let the agent take real action: search_venues, assess_show_offer, and submit_booking_hold (a real action on the
artist's connected booking account).

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


class BookingAccountNotConnected(Exception):
    """Raised when the artist has not connected a booking account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class BookingAccountAuthExpired(Exception):
    """Raised when a previously connected booking account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_LIVE_WIRE_CATALOG = [
    {'id': 'v-1', 'city': 'london', 'capacity_tier': 'club', 'name': 'The Lexington', 'note': '200-cap tastemaker room.'},
    {'id': 'v-2', 'city': 'berlin', 'capacity_tier': 'mid', 'name': 'Lido', 'note': '500-cap; strong for electronic and indie.'},
    {'id': 'v-3', 'city': 'austin', 'capacity_tier': 'club', 'name': 'Mohawk', 'note': 'Indoor/outdoor; SXSW staple.'},
    {'id': 'v-4', 'city': 'toronto', 'capacity_tier': 'theatre', 'name': 'The Danforth', 'note': '1500-cap step-up room.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_LIVE_WIRE_HEUR = [
    ('no guarantee', 'No guaranteed fee — door-deal risk', 'high'),
    ('pay to play', 'Pay-to-play structure — decline', 'high'),
    ('no radius clause relief', 'Restrictive radius clause', 'medium'),
    ('artist covers backline', 'Artist bears backline costs', 'medium'),
    ('no hospitality', 'No hospitality or accommodation', 'low'),
]


async def search_venues(city: str = "", capacity_tier: str = "") -> dict:
    """Search the reference catalog by city and/or capacity_tier.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (city or "").strip().lower()
    b = (capacity_tier or "").strip().lower()
    matches = [
        dict(c)
        for c in _LIVE_WIRE_CATALOG
        if (not a or a in c["city"]) and (not b or b in c["capacity_tier"])
    ]
    return {"items": matches, "count": len(matches)}


async def assess_show_offer(artist_id: str, offer_text: str = "", context: str = "") -> dict:
    """Screen offer_text against known indicators.

    Runs the pure ``_LIVE_WIRE_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (offer_text or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _LIVE_WIRE_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "renegotiate" if has_high else ("clarify_terms" if findings else "solid_offer")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's booking account.

    Driven purely by the ``LIVE_WIRE_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise BookingAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("LIVE_WIRE_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise BookingAccountAuthExpired("booking account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def submit_booking_hold(artist_id: str, venue_name: str, hold_type: str = "first") -> dict:
    """Take the hold submitted action on the artist's connected booking account.

    Raises BookingAccountNotConnected / BookingAccountAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise BookingAccountNotConnected("artist has not connected a booking account")
    name = (venue_name or "").strip()
    opt = (hold_type or "first").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "HOLD-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "venue_name": name,
        "hold_type": opt,
    }
