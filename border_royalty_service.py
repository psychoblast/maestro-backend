"""
PLMKR Border-Royalty — neighbouring-rights action service (mock-first).

Backs the Border-Royalty (Cleo — Neighbouring Rights) agent's tool_use loop in
/api/chat_stream (see BORDER_ROYALTY_TOOLS in main.py). Cleo does not just advise —
these functions let the agent take real neighbouring-rights actions: look up the
right neighbouring-rights collection societies (CMOs) to affiliate with per
territory, screen a sound recording for claim-readiness against a society's
requirements, and file a performer/producer neighbouring-rights claim with a
society on the artist's behalf so it starts collecting the international royalties
they are owed on plays of their masters.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live society portals, no registration APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_society_account_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring rights_pulse_service._pro_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class SocietyAccountNotConnected(Exception):
    """Raised when the artist has not connected a neighbouring-rights society account.

    Mirrors rights_pulse_service.ProAccountNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class SocietyAccountAuthExpired(Exception):
    """Raised when a previously connected society account's authorization expired."""


# ── Neighbouring-rights collection society library (in-memory reference data) ──
# A curated set of neighbouring-rights CMOs (collective management orgs) that
# collect performer and/or producer royalties on plays of sound recordings.
# Keyed loosely on territory / type so the agent can surface which societies an
# artist should affiliate with to collect the international royalties they are
# owed. No I/O.
_SOCIETIES = [
    {
        "id": "soc-ppl",
        "name": "PPL",
        "territory": "UK",
        "region": "europe",
        "type": "combined",
        "collects": ["performer", "producer"],
    },
    {
        "id": "soc-soundexchange",
        "name": "SoundExchange",
        "territory": "US",
        "region": "north_america",
        "type": "combined",
        "collects": ["performer", "producer"],
    },
    {
        "id": "soc-gvl",
        "name": "GVL",
        "territory": "DE",
        "region": "europe",
        "type": "combined",
        "collects": ["performer", "producer"],
    },
    {
        "id": "soc-sena",
        "name": "SENA",
        "territory": "NL",
        "region": "europe",
        "type": "combined",
        "collects": ["performer", "producer"],
    },
    {
        "id": "soc-adami",
        "name": "ADAMI",
        "territory": "FR",
        "region": "europe",
        "type": "performer",
        "collects": ["performer"],
    },
    {
        "id": "soc-spedidam",
        "name": "SPEDIDAM",
        "territory": "FR",
        "region": "europe",
        "type": "performer",
        "collects": ["performer"],
    },
    {
        "id": "soc-re-sound",
        "name": "Re:Sound",
        "territory": "CA",
        "region": "north_america",
        "type": "combined",
        "collects": ["performer", "producer"],
    },
]

# Performer/producer roles the platform recognises on a neighbouring-rights claim.
_VALID_ROLES = ("featured", "non_featured", "producer")


async def search_collection_societies(territory: str = "", right_type: str = "") -> dict:
    """Search neighbouring-rights collection societies by territory and/or role type.

    Both filters are optional and matched case-insensitively as substrings.
    ``territory`` matches the two-letter territory code (e.g. "UK", "US"), and
    ``right_type`` matches the collected right (e.g. "performer", "producer").
    Returns {"societies": [...], "count": int}. Pure — no I/O.
    """
    t  = (territory or "").strip().lower()
    rt = (right_type or "").strip().lower()
    matches = [
        dict(s)
        for s in _SOCIETIES
        if (not t or t in s["territory"].lower())
        and (not rt or any(rt in c for c in s["collects"]))
    ]
    return {"societies": matches, "count": len(matches)}


def _get_society(society_id: str) -> dict | None:
    sid = (society_id or "").strip()
    for s in _SOCIETIES:
        if s["id"] == sid:
            return s
    return None


async def check_claim_readiness(
    artist_id: str,
    recording_title: str = "",
    society_id: str = "",
    performer_role: str = "",
) -> dict:
    """Screen a sound recording against a society's neighbouring-rights requirements.

    Deterministic gap analysis — never contacts a wire. Looks the society up by id
    and checks that a recording title is present, the society is known, and the
    performer role is one of the recognised roles. Returns a structured readiness
    result with a recommendation of "file" / "fix" / "blocked".
    """
    soc = _get_society(society_id)

    role = (performer_role or "").strip().lower()

    gaps = []
    if not (recording_title or "").strip():
        gaps.append("missing_recording_title")
    if society_id and soc is None:
        gaps.append("unknown_society")
    if not society_id:
        gaps.append("missing_society")
    if role not in _VALID_ROLES:
        gaps.append("invalid_performer_role")

    ready = not gaps
    if ready:
        recommendation = "file"
    elif "unknown_society" in gaps or "missing_society" in gaps:
        # Without a valid society target the claim cannot proceed at all.
        recommendation = "blocked"
    else:
        recommendation = "fix"

    return {
        "ready": ready,
        "gaps": gaps,
        "society_id": soc["id"] if soc else (society_id or "").strip(),
        "society_name": soc["name"] if soc else None,
        "performer_role": role,
        "recommendation": recommendation,
    }


def _society_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's neighbouring-rights society account.

    In production this would look up a stored society account link for the artist.
    Here it is driven purely by the ``NEIGHBOURING_RIGHTS_ACCOUNT_CONNECTED`` env
    flag so tests can toggle connected / expired / not-connected with ZERO network
    calls and NO real secret. Values:
      - "expired"                     → raise SocietyAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("NEIGHBOURING_RIGHTS_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise SocietyAccountAuthExpired("society account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def register_neighbouring_rights_claim(
    artist_id: str,
    recording_title: str,
    society_id: str,
    performer_role: str = "",
) -> dict:
    """File a neighbouring-rights claim with a society on behalf of the artist.

    Raises SocietyAccountNotConnected / SocietyAccountAuthExpired when no society
    account is linked so the caller can surface a 'connect your account' message
    instead of a hard failure. On success returns a deterministic mock claim
    reference — NO network call is ever made.
    """
    if not _society_account_connected(artist_id):
        raise SocietyAccountNotConnected(
            "artist has not connected a neighbouring-rights society account"
        )
    title = (recording_title or "").strip()
    sid   = (society_id or "").strip()
    role  = (performer_role or "").strip().lower()
    digest = hashlib.sha1(f"{artist_id}:{sid}:{title}:{role}".encode("utf-8")).hexdigest()
    reference = "NR-" + digest[:10].upper()
    return {
        "status": "filed",
        "reference": reference,
        "recording_title": title,
        "society_id": sid,
        "performer_role": role,
    }
