"""
PLMKR Rights-Pulse — performance-rights action service (mock-first).

Backs the Rights-Pulse (Ray — Performance Rights) agent's tool_use loop in
/api/chat_stream (see RIGHTS_PULSE_TOOLS in main.py). Ray does not just advise —
these functions let the agent take real performance-rights actions: look up the
right Performance Rights Organizations (PROs) to affiliate with, screen a work
for registration-readiness against a PRO's requirements, and register a work
with a PRO on the artist's behalf so it starts collecting performance royalties.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live PRO portals, no registration APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_pro_account_connected``) driven by an env flag so tests
    can toggle the connected / not-connected / expired states deterministically
    — mirroring fund_phantom_service._portal_connected without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class ProAccountNotConnected(Exception):
    """Raised when the artist has not connected a PRO registration account.

    Mirrors fund_phantom_service.FundingPortalNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class ProAccountAuthExpired(Exception):
    """Raised when a previously connected PRO account's authorization expired."""


# ── Performance Rights Organization library (in-memory reference data — no I/O) ─
# A curated set of PROs / digital-performance collectors. Keyed loosely on
# territory / type so the agent can surface which orgs an artist should affiliate
# with to collect the performance royalties they are owed.
_PRO_ORGANIZATIONS = [
    {
        "id": "pro-ascap",
        "name": "ASCAP",
        "territory": "US",
        "region": "north_america",
        "type": "performing_rights",
        "collects": ["public_performance", "digital_streaming"],
    },
    {
        "id": "pro-bmi",
        "name": "BMI",
        "territory": "US",
        "region": "north_america",
        "type": "performing_rights",
        "collects": ["public_performance", "digital_streaming"],
    },
    {
        "id": "pro-sesac",
        "name": "SESAC",
        "territory": "US",
        "region": "north_america",
        "type": "performing_rights",
        "collects": ["public_performance"],
    },
    {
        "id": "pro-soundexchange",
        "name": "SoundExchange",
        "territory": "US",
        "region": "north_america",
        "type": "digital_performance",
        "collects": ["digital_performance", "satellite_radio"],
    },
    {
        "id": "pro-prs",
        "name": "PRS for Music",
        "territory": "UK",
        "region": "europe",
        "type": "performing_rights",
        "collects": ["public_performance", "digital_streaming"],
    },
    {
        "id": "pro-socan",
        "name": "SOCAN",
        "territory": "CA",
        "region": "north_america",
        "type": "performing_rights",
        "collects": ["public_performance", "digital_streaming"],
    },
    {
        "id": "pro-gema",
        "name": "GEMA",
        "territory": "DE",
        "region": "europe",
        "type": "performing_rights",
        "collects": ["public_performance"],
    },
]


async def search_pro_organizations(territory: str = "", org_type: str = "") -> dict:
    """Search Performance Rights Organizations by territory and/or org type.

    Both filters are optional and matched case-insensitively as substrings.
    ``territory`` matches the two-letter territory code (e.g. "US", "UK"), and
    ``org_type`` matches the collection type (e.g. "performing_rights",
    "digital_performance"). Returns {"organizations": [...], "count": int}.
    Pure — no I/O.
    """
    t = (territory or "").strip().lower()
    ot = (org_type or "").strip().lower()
    matches = [
        dict(o)
        for o in _PRO_ORGANIZATIONS
        if (not t or t in o["territory"].lower()) and (not ot or ot in o["type"])
    ]
    return {"organizations": matches, "count": len(matches)}


def _get_org(pro_id: str) -> dict | None:
    pid = (pro_id or "").strip()
    for o in _PRO_ORGANIZATIONS:
        if o["id"] == pid:
            return o
    return None


async def check_registration_status(
    artist_id: str,
    work_title: str = "",
    pro_id: str = "",
    writer_share: int = 0,
) -> dict:
    """Screen a work against a PRO's registration requirements.

    Deterministic gap analysis — never contacts a wire. Looks the PRO up by id
    and checks that a work title is present, the PRO is known, and the writer
    share is a valid percentage (1–100). Returns a structured readiness result
    with a recommendation of "register" / "fix" / "blocked".
    """
    org = _get_org(pro_id)

    try:
        share = int(writer_share or 0)
    except (TypeError, ValueError):
        share = 0

    gaps = []
    if not (work_title or "").strip():
        gaps.append("missing_work_title")
    if pro_id and org is None:
        gaps.append("unknown_pro")
    if not pro_id:
        gaps.append("missing_pro")
    if share <= 0 or share > 100:
        gaps.append("invalid_writer_share")

    ready = not gaps
    if ready:
        recommendation = "register"
    elif "unknown_pro" in gaps or "missing_pro" in gaps:
        # Without a valid PRO target the registration cannot proceed at all.
        recommendation = "blocked"
    else:
        recommendation = "fix"

    return {
        "ready": ready,
        "gaps": gaps,
        "pro_id": org["id"] if org else (pro_id or "").strip(),
        "pro_name": org["name"] if org else None,
        "writer_share": share,
        "recommendation": recommendation,
    }


def _pro_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's PRO registration account.

    In production this would look up a stored PRO account link for the artist.
    Here it is driven purely by the ``PRO_ACCOUNT_CONNECTED`` env flag so tests
    can toggle connected / expired / not-connected with ZERO network calls and NO
    real secret. Values:
      - "expired"                     → raise ProAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("PRO_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise ProAccountAuthExpired("PRO account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def register_work(
    artist_id: str,
    work_title: str,
    pro_id: str,
    writer_share: int = 0,
) -> dict:
    """Register a work with a PRO on behalf of the artist.

    Raises ProAccountNotConnected / ProAccountAuthExpired when no PRO account is
    linked so the caller can surface a 'connect your account' message instead of
    a hard failure. On success returns a deterministic mock registration
    reference — NO network call is ever made.
    """
    if not _pro_account_connected(artist_id):
        raise ProAccountNotConnected(
            "artist has not connected a PRO registration account"
        )
    title = (work_title or "").strip()
    pid = (pro_id or "").strip()
    try:
        share = int(writer_share or 0)
    except (TypeError, ValueError):
        share = 0
    digest = hashlib.sha1(f"{artist_id}:{pid}:{title}:{share}".encode("utf-8")).hexdigest()
    reference = "PRO-" + digest[:10].upper()
    return {
        "status": "registered",
        "reference": reference,
        "work_title": title,
        "pro_id": pid,
        "writer_share": share,
    }
