"""
PLMKR Mech-Ledger — mechanical-royalties action service (mock-first).

Backs the Mech-Ledger (Finn — Mechanical Royalties) agent's tool_use loop in
/api/chat_stream (see MECH_LEDGER_TOOLS in main.py). Finn does not just advise —
these functions let the agent take real mechanical-royalties actions: look up the
right mechanical-rights collection agency / administrator to register with per
territory (e.g. the MLC in the US, MCPS in the UK), screen a musical work
(composition) for registration-readiness against an agency's requirements, and
register a work with an agency on the artist's behalf so it starts collecting the
mechanical royalties they are owed on reproductions/streams of that composition.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live agency portals, no registration APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_mech_account_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring border_royalty_service._society_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class MechAccountNotConnected(Exception):
    """Raised when the artist has not connected a mechanical-rights agency account.

    Mirrors border_royalty_service.SocietyAccountNotConnected: the tool loop
    catches this and degrades gracefully into a structured 'connect your account
    first' result instead of crashing the stream.
    """


class MechAccountAuthExpired(Exception):
    """Raised when a previously connected mechanical-rights account's authorization expired."""


# ── Mechanical-rights collection agency library (in-memory reference data) ─────
# A curated set of mechanical-rights orgs / administrators that collect mechanical
# royalties (songwriter and/or publisher share) on reproductions of musical works.
# Keyed loosely on territory / type so the agent can surface which agency an artist
# should register with to collect the mechanical royalties they are owed. No I/O.
_AGENCIES = [
    {
        "id": "mech-mlc",
        "name": "The MLC",
        "territory": "US",
        "region": "north_america",
        "type": "combined",
        "collects": ["songwriter", "publisher"],
    },
    {
        "id": "mech-hfa",
        "name": "Harry Fox Agency",
        "territory": "US",
        "region": "north_america",
        "type": "publisher",
        "collects": ["publisher"],
    },
    {
        "id": "mech-mcps",
        "name": "MCPS",
        "territory": "UK",
        "region": "europe",
        "type": "combined",
        "collects": ["songwriter", "publisher"],
    },
    {
        "id": "mech-cmrra",
        "name": "CMRRA",
        "territory": "CA",
        "region": "north_america",
        "type": "combined",
        "collects": ["songwriter", "publisher"],
    },
    {
        "id": "mech-gema",
        "name": "GEMA",
        "territory": "DE",
        "region": "europe",
        "type": "combined",
        "collects": ["songwriter", "publisher"],
    },
    {
        "id": "mech-sacem",
        "name": "SACEM",
        "territory": "FR",
        "region": "europe",
        "type": "combined",
        "collects": ["songwriter", "publisher"],
    },
]

# Writer/publisher roles the platform recognises on a mechanical-work registration.
_VALID_ROLES = ("writer", "co_writer", "publisher")


async def search_mechanical_agencies(territory: str = "", right_type: str = "") -> dict:
    """Search mechanical-rights collection agencies by territory and/or role type.

    Both filters are optional and matched case-insensitively as substrings.
    ``territory`` matches the two-letter territory code (e.g. "US", "UK"), and
    ``right_type`` matches the collected right (e.g. "songwriter", "publisher").
    Returns {"agencies": [...], "count": int}. Pure — no I/O.
    """
    t  = (territory or "").strip().lower()
    rt = (right_type or "").strip().lower()
    matches = [
        dict(a)
        for a in _AGENCIES
        if (not t or t in a["territory"].lower())
        and (not rt or any(rt in c for c in a["collects"]))
    ]
    return {"agencies": matches, "count": len(matches)}


def _get_agency(agency_id: str) -> dict | None:
    aid = (agency_id or "").strip()
    for a in _AGENCIES:
        if a["id"] == aid:
            return a
    return None


async def check_registration_readiness(
    artist_id: str,
    work_title: str = "",
    agency_id: str = "",
    writer_role: str = "",
) -> dict:
    """Screen a musical work against an agency's mechanical-registration requirements.

    Deterministic gap analysis — never contacts a wire. Looks the agency up by id
    and checks that a work title is present, the agency is known, and the writer
    role is one of the recognised roles. Returns a structured readiness result
    with a recommendation of "register" / "fix" / "blocked".
    """
    agency = _get_agency(agency_id)

    role = (writer_role or "").strip().lower()

    gaps = []
    if not (work_title or "").strip():
        gaps.append("missing_work_title")
    if agency_id and agency is None:
        gaps.append("unknown_agency")
    if not agency_id:
        gaps.append("missing_agency")
    if role not in _VALID_ROLES:
        gaps.append("invalid_writer_role")

    ready = not gaps
    if ready:
        recommendation = "register"
    elif "unknown_agency" in gaps or "missing_agency" in gaps:
        # Without a valid agency target the registration cannot proceed at all.
        recommendation = "blocked"
    else:
        recommendation = "fix"

    return {
        "ready": ready,
        "gaps": gaps,
        "agency_id": agency["id"] if agency else (agency_id or "").strip(),
        "agency_name": agency["name"] if agency else None,
        "writer_role": role,
        "recommendation": recommendation,
    }


def _mech_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's mechanical-rights agency account.

    In production this would look up a stored agency account link for the artist.
    Here it is driven purely by the ``MECH_LEDGER_ACCOUNT_CONNECTED`` env flag so
    tests can toggle connected / expired / not-connected with ZERO network calls
    and NO real secret. Values:
      - "expired"                     → raise MechAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("MECH_LEDGER_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise MechAccountAuthExpired("mechanical-rights account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def register_mechanical_work(
    artist_id: str,
    work_title: str,
    agency_id: str,
    writer_role: str = "",
) -> dict:
    """Register a musical work with a mechanical-rights agency on behalf of the artist.

    Raises MechAccountNotConnected / MechAccountAuthExpired when no agency account
    is linked so the caller can surface a 'connect your account' message instead of
    a hard failure. On success returns a deterministic mock work reference — NO
    network call is ever made.
    """
    if not _mech_account_connected(artist_id):
        raise MechAccountNotConnected(
            "artist has not connected a mechanical-rights agency account"
        )
    title = (work_title or "").strip()
    aid   = (agency_id or "").strip()
    role  = (writer_role or "").strip().lower()
    digest = hashlib.sha1(f"{artist_id}:{aid}:{title}:{role}".encode("utf-8")).hexdigest()
    reference = "MW-" + digest[:10].upper()
    return {
        "status": "registered",
        "reference": reference,
        "work_title": title,
        "agency_id": aid,
        "writer_role": role,
    }
