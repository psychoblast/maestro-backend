"""
PLMKR Reel — Music Video action service (mock-first).

Backs the video-director (Reel, Music Video) agent's tool_use loop in /api/chat_stream
(see VIDEO_DIRECTOR_TOOLS in main.py). Reel does not just advise — these functions
let the agent take real action: search_directors, estimate_video_budget, and book_video_shoot (a real action on the
artist's connected video production account).

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


class ProductionAccountNotConnected(Exception):
    """Raised when the artist has not connected a video production account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class ProductionAccountAuthExpired(Exception):
    """Raised when a previously connected video production account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_VIDEO_DIRECTOR_CATALOG = [
    {'id': 'dir-1', 'style': 'narrative', 'budget_tier': 'mid', 'name': 'J. Okafor', 'note': 'Story-driven videos with strong casting.'},
    {'id': 'dir-2', 'style': 'performance', 'budget_tier': 'low', 'name': 'Kite', 'note': 'One-take performance pieces on a budget.'},
    {'id': 'dir-3', 'style': 'animation', 'budget_tier': 'mid', 'name': 'Studio Vela', 'note': '2D/3D animated music videos.'},
    {'id': 'dir-4', 'style': 'experimental', 'budget_tier': 'high', 'name': 'Mara Voss', 'note': 'Award-circuit experimental visuals.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_VIDEO_DIRECTOR_HEUR = [
    ('multiple locations', 'Multiple locations drive up cost and days', 'high'),
    ('vfx heavy', 'Heavy VFX inflates post budget', 'high'),
    ('large cast', 'Large cast raises talent and catering costs', 'medium'),
    ('night shoot', 'Night shoots add overtime and lighting', 'medium'),
    ('animals', 'Animals on set require handlers and permits', 'low'),
]


async def search_directors(style: str = "", budget_tier: str = "") -> dict:
    """Search the reference catalog by style and/or budget_tier.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (style or "").strip().lower()
    b = (budget_tier or "").strip().lower()
    matches = [
        dict(c)
        for c in _VIDEO_DIRECTOR_CATALOG
        if (not a or a in c["style"]) and (not b or b in c["budget_tier"])
    ]
    return {"items": matches, "count": len(matches)}


async def estimate_video_budget(artist_id: str, treatment_notes: str = "", context: str = "") -> dict:
    """Screen treatment_notes against known indicators.

    Runs the pure ``_VIDEO_DIRECTOR_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (treatment_notes or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _VIDEO_DIRECTOR_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "scope_down" if has_high else ("budget_carefully" if findings else "budget_realistic")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's video production account.

    Driven purely by the ``VIDEO_DIRECTOR_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise ProductionAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("VIDEO_DIRECTOR_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise ProductionAccountAuthExpired("video production account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def book_video_shoot(artist_id: str, project_title: str, crew: str = "full") -> dict:
    """Take the shoot booked action on the artist's connected video production account.

    Raises ProductionAccountNotConnected / ProductionAccountAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise ProductionAccountNotConnected("artist has not connected a video production account")
    name = (project_title or "").strip()
    opt = (crew or "full").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "SHOOT-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "project_title": name,
        "crew": opt,
    }
