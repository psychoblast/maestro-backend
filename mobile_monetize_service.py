"""
PLMKR Mo — Monetization action service (mock-first).

Backs the mobile-monetize (Mo, Monetization) agent's tool_use loop in /api/chat_stream
(see MOBILE_MONETIZE_TOOLS in main.py). Mo does not just advise — these functions
let the agent take real action: search_monetization_programs, analyze_monetization, and enable_monetization (a real action on the
artist's connected platform monetization account).

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


class PlatformAccountNotConnected(Exception):
    """Raised when the artist has not connected a platform monetization account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class PlatformAccountAuthExpired(Exception):
    """Raised when a previously connected platform monetization account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_MOBILE_MONETIZE_CATALOG = [
    {'id': 'm-1', 'platform': 'youtube', 'tier': 'partner', 'name': 'YouTube Partner', 'note': 'Ad revenue share; needs 1k subs + watch hours.'},
    {'id': 'm-2', 'platform': 'tiktok', 'tier': 'creator', 'name': 'Creator Rewards', 'note': 'Payouts for qualifying 1-min+ videos.'},
    {'id': 'm-3', 'platform': 'instagram', 'tier': 'bonus', 'name': 'Reels Bonus', 'note': 'Invite-only performance bonuses.'},
    {'id': 'm-4', 'platform': 'youtube', 'tier': 'shorts', 'name': 'Shorts Fund', 'note': 'Shorts monetization via ad revenue.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_MOBILE_MONETIZE_HEUR = [
    ('under 1000 subs', 'Below subscriber threshold for monetization', 'high'),
    ('reused content', 'Reused/unoriginal content risks demonetization', 'high'),
    ('low watch time', 'Watch time below program requirement', 'medium'),
    ('copyright claims', 'Active copyright claims block payouts', 'high'),
    ('inconsistent posting', 'Irregular posting slows eligibility', 'low'),
]


async def search_monetization_programs(platform: str = "", tier: str = "") -> dict:
    """Search the reference catalog by platform and/or tier.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (platform or "").strip().lower()
    b = (tier or "").strip().lower()
    matches = [
        dict(c)
        for c in _MOBILE_MONETIZE_CATALOG
        if (not a or a in c["platform"]) and (not b or b in c["tier"])
    ]
    return {"items": matches, "count": len(matches)}


async def analyze_monetization(artist_id: str, metrics_text: str = "", context: str = "") -> dict:
    """Screen metrics_text against known indicators.

    Runs the pure ``_MOBILE_MONETIZE_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (metrics_text or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _MOBILE_MONETIZE_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "fix_eligibility" if has_high else ("grow_metrics" if findings else "ready_to_enable")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's platform monetization account.

    Driven purely by the ``MOBILE_MONETIZE_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise PlatformAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("MOBILE_MONETIZE_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise PlatformAccountAuthExpired("platform monetization account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def enable_monetization(artist_id: str, platform: str, program: str = "ads") -> dict:
    """Take the monetization enabled action on the artist's connected platform monetization account.

    Raises PlatformAccountNotConnected / PlatformAccountAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise PlatformAccountNotConnected("artist has not connected a platform monetization account")
    name = (platform or "").strip()
    opt = (program or "ads").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "MON-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "platform": name,
        "program": opt,
    }
