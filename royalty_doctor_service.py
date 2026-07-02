"""
PLMKR Doc — Royalty Recovery action service (mock-first).

Backs the royalty-doctor (Doc, Royalty Recovery) agent's tool_use loop in /api/chat_stream
(see ROYALTY_DOCTOR_TOOLS in main.py). Doc does not just advise — these functions
let the agent take real action: search_royalty_sources, assess_black_box, and file_royalty_claim (a real action on the
artist's connected collection society account).

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


class CollectionAccountNotConnected(Exception):
    """Raised when the artist has not connected a collection society account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class CollectionAccountAuthExpired(Exception):
    """Raised when a previously connected collection society account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_ROYALTY_DOCTOR_CATALOG = [
    {'id': 'r-1', 'source_type': 'neighbouring', 'territory': 'eu', 'name': 'Neighbouring Rights', 'note': 'Broadcast/public-performance master royalties.'},
    {'id': 'r-2', 'source_type': 'mechanical', 'territory': 'us', 'name': 'Black-Box Mechanicals', 'note': 'Unmatched mechanical royalties held by the MLC.'},
    {'id': 'r-3', 'source_type': 'performance', 'territory': 'global', 'name': 'Unregistered Works', 'note': 'PRO income lost to unregistered splits.'},
    {'id': 'r-4', 'source_type': 'digital', 'territory': 'global', 'name': 'DSP Underpayments', 'note': 'Misattributed streams and payout gaps.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_ROYALTY_DOCTOR_HEUR = [
    ('no pro', 'Not registered with a PRO — losing performance income', 'high'),
    ('no neighbouring', 'No neighbouring-rights registration', 'high'),
    ('unregistered splits', 'Splits never registered with societies', 'high'),
    ('old catalog', 'Legacy catalog never audited', 'medium'),
    ('cover songs', 'Cover royalties not being collected', 'medium'),
]


async def search_royalty_sources(source_type: str = "", territory: str = "") -> dict:
    """Search the reference catalog by source_type and/or territory.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (source_type or "").strip().lower()
    b = (territory or "").strip().lower()
    matches = [
        dict(c)
        for c in _ROYALTY_DOCTOR_CATALOG
        if (not a or a in c["source_type"]) and (not b or b in c["territory"])
    ]
    return {"items": matches, "count": len(matches)}


async def assess_black_box(artist_id: str, catalog_notes: str = "", context: str = "") -> dict:
    """Screen catalog_notes against known indicators.

    Runs the pure ``_ROYALTY_DOCTOR_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (catalog_notes or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _ROYALTY_DOCTOR_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "file_claims" if has_high else ("register_gaps" if findings else "fully_collected")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's collection society account.

    Driven purely by the ``ROYALTY_DOCTOR_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise CollectionAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("ROYALTY_DOCTOR_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise CollectionAccountAuthExpired("collection society account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def file_royalty_claim(artist_id: str, claim_subject: str, society: str = "pro") -> dict:
    """Take the claim filed action on the artist's connected collection society account.

    Raises CollectionAccountNotConnected / CollectionAccountAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise CollectionAccountNotConnected("artist has not connected a collection society account")
    name = (claim_subject or "").strip()
    opt = (society or "pro").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "CLAIM-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "claim_subject": name,
        "society": opt,
    }
