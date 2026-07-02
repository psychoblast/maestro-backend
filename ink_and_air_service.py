"""
PLMKR Reed — Music Publisher action service (mock-first).

Backs the ink-and-air (Reed, Music Publisher) agent's tool_use loop in /api/chat_stream
(see INK_AND_AIR_TOOLS in main.py). Reed does not just advise — these functions
let the agent take real action: search_publishing_deals, review_split_sheet, and register_composition (a real action on the
artist's connected publishing administration account).

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


class PublishingAdminNotConnected(Exception):
    """Raised when the artist has not connected a publishing administration account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class PublishingAdminAuthExpired(Exception):
    """Raised when a previously connected publishing administration account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_INK_AND_AIR_CATALOG = [
    {'id': 'p-admin', 'deal_type': 'administration', 'territory': 'worldwide', 'name': 'Admin Deal', 'note': 'Writer keeps copyright; admin takes 10-15% for collection.'},
    {'id': 'p-copub', 'deal_type': 'co_publishing', 'territory': 'worldwide', 'name': 'Co-Pub Deal', 'note': "Publisher takes 50% of publisher's share; writer keeps writer's share."},
    {'id': 'p-sub', 'deal_type': 'sub_publishing', 'territory': 'eu', 'name': 'EU Sub-Pub', 'note': 'Local collection in-territory; short term.'},
    {'id': 'p-full', 'deal_type': 'full_publishing', 'territory': 'worldwide', 'name': 'Full Publishing', 'note': 'Assign copyright — highest advance, least ownership.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_INK_AND_AIR_HEUR = [
    ('does not total 100', 'Splits do not sum to 100%', 'high'),
    ('no signature', 'Unsigned split sheet — not enforceable', 'high'),
    ('verbal', 'Splits only agreed verbally', 'high'),
    ('tbd', 'Undecided splits left as TBD', 'medium'),
    ('no publisher', 'Publisher shares not documented', 'medium'),
]


async def search_publishing_deals(deal_type: str = "", territory: str = "") -> dict:
    """Search the reference catalog by deal_type and/or territory.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (deal_type or "").strip().lower()
    b = (territory or "").strip().lower()
    matches = [
        dict(c)
        for c in _INK_AND_AIR_CATALOG
        if (not a or a in c["deal_type"]) and (not b or b in c["territory"])
    ]
    return {"items": matches, "count": len(matches)}


async def review_split_sheet(artist_id: str, split_text: str = "", context: str = "") -> dict:
    """Screen split_text against known indicators.

    Runs the pure ``_INK_AND_AIR_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (split_text or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _INK_AND_AIR_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "resolve_before_release" if has_high else ("confirm_shares" if findings else "clean")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's publishing administration account.

    Driven purely by the ``INK_AND_AIR_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise PublishingAdminAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("INK_AND_AIR_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise PublishingAdminAuthExpired("publishing administration account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def register_composition(artist_id: str, work_title: str, work_type: str = "song") -> dict:
    """Take the composition registered action on the artist's connected publishing administration account.

    Raises PublishingAdminNotConnected / PublishingAdminAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise PublishingAdminNotConnected("artist has not connected a publishing administration account")
    name = (work_title or "").strip()
    opt = (work_type or "song").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "PUB-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "work_title": name,
        "work_type": opt,
    }
