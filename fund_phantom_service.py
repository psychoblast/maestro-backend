"""
PLMKR Fund-Phantom — grants & funding action service (mock-first).

Backs the Fund-Phantom (Jade — Grants & Funding) agent's tool_use loop in
/api/chat_stream (see FUND_PHANTOM_TOOLS in main.py). Jade does not just advise —
these functions let the agent take real funding actions: search open grant
programs, screen a project for eligibility against a program's rules, and submit
a grant application on the artist's behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live grant portals, no submission APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_portal_connected``) driven by an env flag so tests can
    toggle the connected / not-connected / expired states deterministically —
    mirroring lex_cipher_service.RegistryNotConnected without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class FundingPortalNotConnected(Exception):
    """Raised when the artist has not connected a funding-portal submission account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first' result
    instead of crashing the stream.
    """


class FundingPortalAuthExpired(Exception):
    """Raised when a previously connected funding-portal account's auth expired."""


# ── Grant program library (in-memory reference data — no I/O) ─────────────────
# A curated set of arts-funding programs. Keyed loosely on genre / region so the
# agent can surface programs an artist could apply to.
_GRANT_PROGRAMS = [
    {
        "id": "gp-arts-council-recording",
        "name": "Arts Council Recording Grant",
        "funder": "National Arts Council",
        "genre": "any",
        "region": "national",
        "max_award": 15000,
        "focus": "recording",
        "deadline_window": "rolling",
    },
    {
        "id": "gp-touring-development",
        "name": "Emerging Artist Touring Fund",
        "funder": "National Arts Council",
        "genre": "any",
        "region": "national",
        "max_award": 25000,
        "focus": "touring",
        "deadline_window": "quarterly",
    },
    {
        "id": "gp-regional-hiphop",
        "name": "Regional Hip-Hop Creators Grant",
        "funder": "City Cultural Foundation",
        "genre": "hip-hop",
        "region": "regional",
        "max_award": 8000,
        "focus": "recording",
        "deadline_window": "annual",
    },
    {
        "id": "gp-electronic-innovation",
        "name": "Electronic Music Innovation Award",
        "funder": "Sound Futures Trust",
        "genre": "electronic",
        "region": "national",
        "max_award": 12000,
        "focus": "production",
        "deadline_window": "annual",
    },
    {
        "id": "gp-folk-heritage",
        "name": "Folk & Roots Heritage Bursary",
        "funder": "Heritage Music Foundation",
        "genre": "folk",
        "region": "regional",
        "max_award": 6000,
        "focus": "recording",
        "deadline_window": "annual",
    },
    {
        "id": "gp-video-production",
        "name": "Music Video Production Fund",
        "funder": "Screen & Sound Board",
        "genre": "any",
        "region": "national",
        "max_award": 10000,
        "focus": "video",
        "deadline_window": "quarterly",
    },
]


async def search_grant_programs(
    genre: str = "",
    region: str = "",
    max_award: int = 0,
) -> dict:
    """Search open grant programs by genre, region, and/or minimum award ceiling.

    All filters are optional. ``genre`` / ``region`` are matched
    case-insensitively as substrings (programs marked "any"/"national" always
    match a genre/region query). ``max_award`` filters to programs whose ceiling
    is at least that amount. Returns {"programs": [...], "count": int}. Pure — no
    I/O.
    """
    g = (genre or "").strip().lower()
    r = (region or "").strip().lower()
    try:
        floor = int(max_award or 0)
    except (TypeError, ValueError):
        floor = 0
    matches = []
    for p in _GRANT_PROGRAMS:
        if g and g not in p["genre"] and p["genre"] != "any":
            continue
        if r and r not in p["region"] and p["region"] != "national":
            continue
        if floor and p["max_award"] < floor:
            continue
        matches.append(dict(p))
    return {"programs": matches, "count": len(matches)}


def _get_program(program_id: str) -> dict | None:
    pid = (program_id or "").strip()
    for p in _GRANT_PROGRAMS:
        if p["id"] == pid:
            return p
    return None


async def check_eligibility(
    artist_id: str,
    program_id: str = "",
    requested_amount: int = 0,
    project_type: str = "",
) -> dict:
    """Screen a project against a grant program's rules and return an assessment.

    Deterministic keyword/threshold screen — never contacts a wire. Looks the
    program up by id and checks the requested amount against its ceiling and the
    project type against its focus. Returns a structured eligibility result with a
    recommendation of "apply" / "adjust" / "ineligible".
    """
    program = _get_program(program_id)
    if program is None:
        return {
            "eligible": False,
            "reasons": ["program_not_found"],
            "program_id": (program_id or "").strip(),
            "recommendation": "ineligible",
        }

    try:
        amount = int(requested_amount or 0)
    except (TypeError, ValueError):
        amount = 0
    ptype = (project_type or "").strip().lower()

    reasons = []
    over_cap = amount > program["max_award"]
    if over_cap:
        reasons.append(
            f"requested {amount} exceeds max award {program['max_award']}"
        )
    focus_mismatch = bool(ptype) and program["focus"] != "any" and ptype != program["focus"]
    if focus_mismatch:
        reasons.append(
            f"project type '{ptype}' does not match program focus '{program['focus']}'"
        )

    eligible = not (over_cap or focus_mismatch)
    if eligible:
        recommendation = "apply"
    elif over_cap and not focus_mismatch:
        recommendation = "adjust"
    else:
        recommendation = "ineligible"

    return {
        "eligible": eligible,
        "reasons": reasons,
        "program_id": program["id"],
        "program_name": program["name"],
        "max_award": program["max_award"],
        "focus": program["focus"],
        "recommendation": recommendation,
    }


def _portal_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's funding-portal submission account.

    In production this would look up a stored portal link for the artist. Here it
    is driven purely by the ``FUNDING_PORTAL_CONNECTED`` env flag so tests can
    toggle connected / expired / not-connected with ZERO network calls and NO
    real secret. Values:
      - "expired"                     → raise FundingPortalAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("FUNDING_PORTAL_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise FundingPortalAuthExpired("funding portal authorization expired")
    return val in ("1", "true", "yes", "connected")


async def submit_grant_application(
    artist_id: str,
    program_id: str,
    project_title: str,
    requested_amount: int = 0,
) -> dict:
    """Submit a grant application to a program on behalf of the artist.

    Raises FundingPortalNotConnected / FundingPortalAuthExpired when no submission
    account is linked so the caller can surface a 'connect your account' message
    instead of a hard failure. On success returns a deterministic mock submission
    reference — NO network call is ever made.
    """
    if not _portal_connected(artist_id):
        raise FundingPortalNotConnected(
            "artist has not connected a funding-portal submission account"
        )
    pid   = (program_id or "").strip()
    title = (project_title or "").strip()
    try:
        amount = int(requested_amount or 0)
    except (TypeError, ValueError):
        amount = 0
    digest = hashlib.sha1(f"{artist_id}:{pid}:{title}:{amount}".encode("utf-8")).hexdigest()
    reference = "GA-" + digest[:10].upper()
    return {
        "status": "submitted",
        "reference": reference,
        "program_id": pid,
        "project_title": title,
        "requested_amount": amount,
    }
