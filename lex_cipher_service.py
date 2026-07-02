"""
PLMKR Lex-Cipher — legal action service (mock-first).

Backs the Lex-Cipher (Entertainment Lawyer) agent's tool_use loop in
/api/chat_stream (see LEX_CIPHER_TOOLS in main.py). Lex does not just advise —
these functions let the agent take real legal actions: look up standard clause
positions, screen an agreement for red-flags, and file an IP/copyright
registration for the artist's work.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live legal databases, no filing APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_registry_connected``) driven by an env flag so tests
    can toggle the connected / not-connected / expired states deterministically
    — mirroring pitch_service.GmailNotConnected without ever touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class RegistryNotConnected(Exception):
    """Raised when the artist has not connected an IP-registry filing account.

    Mirrors pitch_service.GmailNotConnected: the tool loop catches this and
    degrades gracefully into a structured 'connect your account first' result
    instead of crashing the stream.
    """


class RegistryAuthExpired(Exception):
    """Raised when a previously connected filing account's authorization expired."""


# ── Standard clause library (in-memory reference data — no I/O) ───────────────
# A curated set of entertainment-law clause positions. Keyed loosely on
# clause_type / deal_type so the agent can pull the house position for a term.
_CLAUSE_LIBRARY = [
    {
        "id": "cl-360",
        "clause_type": "revenue_share",
        "deal_type": "record_deal",
        "title": "360 Revenue Participation",
        "standard_position": (
            "Label participation in ancillary income (touring, merch, brand) capped "
            "at 15%, applies only to income generated during the term, sunset on expiry."
        ),
        "risk": "high",
    },
    {
        "id": "cl-recoup",
        "clause_type": "recoupment",
        "deal_type": "record_deal",
        "title": "Recoupment Basis",
        "standard_position": (
            "Advances recoupable from artist royalties only — never cross-collateralized "
            "against publishing or other agreements."
        ),
        "risk": "medium",
    },
    {
        "id": "cl-term",
        "clause_type": "term",
        "deal_type": "publishing",
        "title": "Term & Reversion",
        "standard_position": (
            "Initial term of one album cycle with defined option periods; full reversion "
            "of copyrights to writer 10 years after the end of the term."
        ),
        "risk": "medium",
    },
    {
        "id": "cl-ip-assign",
        "clause_type": "ip_assignment",
        "deal_type": "sync_license",
        "title": "Grant of Rights",
        "standard_position": (
            "License is non-exclusive and limited to the named production and media; no "
            "outright assignment of the master or the underlying composition."
        ),
        "risk": "high",
    },
    {
        "id": "cl-morality",
        "clause_type": "morality",
        "deal_type": "brand_deal",
        "title": "Morality / Conduct Clause",
        "standard_position": (
            "Termination trigger limited to conduct resulting in a criminal conviction; "
            "no subjective 'brings the brand into disrepute' standard."
        ),
        "risk": "medium",
    },
    {
        "id": "cl-commission",
        "clause_type": "commission",
        "deal_type": "management",
        "title": "Commission & Post-Term",
        "standard_position": (
            "Commission of 15–20% on net income; post-term commission sunsets on a "
            "declining scale over 24 months and excludes deals signed after termination."
        ),
        "risk": "medium",
    },
]


# ── Red-flag heuristics for agreement screening (pure string matching) ────────
# (phrase-to-match, human issue description, severity)
_RED_FLAGS = [
    ("in perpetuity",      "Perpetual term — rights never revert to the artist",        "high"),
    ("all rights",         "Blanket assignment of all rights",                          "high"),
    ("worldwide exclusive","Broad worldwide exclusive grant",                           "medium"),
    ("net profits",        "Net-profits accounting favors the counterparty",            "medium"),
    ("cross-collateral",   "Cross-collateralization across agreements",                 "high"),
    ("morality",           "Morality clause — subjective termination trigger",          "medium"),
    ("automatic renewal",  "Auto-renewal without an artist opt-out",                    "medium"),
    ("sole discretion",    "Counterparty decisions left to their sole discretion",      "medium"),
]


async def search_clause_library(clause_type: str = "", deal_type: str = "") -> dict:
    """Search the standard clause library by clause type and/or deal type.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"clauses": [...], "count": int}. Pure — no I/O.
    """
    ct = (clause_type or "").strip().lower()
    dt = (deal_type or "").strip().lower()
    matches = [
        dict(c)
        for c in _CLAUSE_LIBRARY
        if (not ct or ct in c["clause_type"]) and (not dt or dt in c["deal_type"])
    ]
    return {"clauses": matches, "count": len(matches)}


async def review_agreement(
    artist_id: str,
    agreement_type: str = "",
    agreement_text: str = "",
) -> dict:
    """Screen an agreement's text for known red-flag clauses.

    Runs the pure ``_RED_FLAGS`` heuristics over the supplied text and returns a
    structured risk assessment. Never contacts a wire; the "review" is a
    deterministic keyword screen, not an LLM call.
    """
    text = (agreement_text or "").lower()
    flags = [
        {"issue": issue, "severity": severity, "matched": phrase}
        for phrase, issue, severity in _RED_FLAGS
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in flags)
    recommendation = "do_not_sign" if has_high else ("negotiate" if flags else "acceptable")
    return {
        "agreement_type": agreement_type or "unspecified",
        "flags": flags,
        "flag_count": len(flags),
        "recommendation": recommendation,
    }


def _registry_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's IP-registry filing account.

    In production this would look up a stored filing-account link for the
    artist. Here it is driven purely by the ``IP_REGISTRY_CONNECTED`` env flag so
    tests can toggle connected / expired / not-connected with ZERO network calls
    and NO real secret. Values:
      - "expired"                → raise RegistryAuthExpired
      - "1"/"true"/"yes"/"connected" → connected
      - anything else / unset    → not connected
    """
    val = (os.environ.get("IP_REGISTRY_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise RegistryAuthExpired("filing account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def file_ip_registration(
    artist_id: str,
    work_title: str,
    work_type: str = "sound_recording",
) -> dict:
    """File an IP/copyright registration for a work on behalf of the artist.

    Raises RegistryNotConnected / RegistryAuthExpired when no filing account is
    linked so the caller can surface a 'connect your account' message instead of
    a hard failure. On success returns a deterministic mock filing reference —
    NO network call is ever made.
    """
    if not _registry_connected(artist_id):
        raise RegistryNotConnected("artist has not connected an IP-registry filing account")
    title = (work_title or "").strip()
    wtype = (work_type or "sound_recording").strip()
    digest = hashlib.sha1(f"{artist_id}:{title}:{wtype}".encode("utf-8")).hexdigest()
    reference = "IPR-" + digest[:10].upper()
    return {
        "status": "filed",
        "reference": reference,
        "work_title": title,
        "work_type": wtype,
    }
