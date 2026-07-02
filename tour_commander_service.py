"""
PLMKR Tour-Commander — tour-manager action service (mock-first).

Backs the Tour-Commander (Miles — Tour Manager) agent's tool_use loop in
/api/chat_stream (see TOUR_COMMANDER_TOOLS in main.py). Miles does not just advise
on routing, production, and crew — these functions let the agent take real
tour-manager actions: search the routing directory for the tour legs an artist can
run (each carrying the region it covers, its leg type, and its per-show operating
cost), draft a concrete tour budget by applying a leg's per-show cost to a run of
shows and a nightly guarantee so the artist has a numbers-backed P&L to sign off,
and confirm a crew call on a date for a leg through the artist's connected
tour-ops account so a production hold actually gets placed on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live routing/production APIs, no crewing rails, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_tour_ops_connected``) driven by an env flag so tests can
    toggle the connected / not-connected / expired states deterministically —
    mirroring venue_hawk_service._venue_booking_connected without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class TourOpsNotConnected(Exception):
    """Raised when the artist has not connected a tour-ops/crewing account.

    Mirrors venue_hawk_service.VenueBookingNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your tour-ops account first'
    result instead of crashing the stream.
    """


class TourOpsAuthExpired(Exception):
    """Raised when a previously connected tour-ops-account authorization expired."""


# ── Routing directory (in-memory reference data) ───────────────────────────────
# A curated set of tour legs an artist can run. Each leg carries the region it
# covers, its leg type (headline / support / festival), the number of markets on
# the run, a per-show operating cost (crew + transport + production, all-in), and a
# typical nightly guarantee for the leg's tier. The agent can surface the right
# legs for a routing plan and apply a leg's per-show cost to a run to draft a real
# budget. No I/O.
_LEGS = [
    {
        "id": "leg-us-west-club",
        "name": "US West Coast Club Run",
        "region": "US West",
        "leg_type": "headline",
        "markets": 8,
        "per_show_cost": 4200.0,
        "nightly_guarantee": 6000.0,
    },
    {
        "id": "leg-us-east-theatre",
        "name": "US East Coast Theatre Run",
        "region": "US East",
        "leg_type": "headline",
        "markets": 10,
        "per_show_cost": 6800.0,
        "nightly_guarantee": 11000.0,
    },
    {
        "id": "leg-eu-support",
        "name": "EU Arena Support Leg",
        "region": "Europe",
        "leg_type": "support",
        "markets": 14,
        "per_show_cost": 3500.0,
        "nightly_guarantee": 2500.0,
    },
    {
        "id": "leg-uk-club",
        "name": "UK Club Run",
        "region": "UK",
        "leg_type": "headline",
        "markets": 6,
        "per_show_cost": 3800.0,
        "nightly_guarantee": 5200.0,
    },
    {
        "id": "leg-au-festival",
        "name": "Australia Festival Run",
        "region": "Australia",
        "leg_type": "festival",
        "markets": 4,
        "per_show_cost": 5200.0,
        "nightly_guarantee": 18000.0,
    },
    {
        "id": "leg-jp-support",
        "name": "Japan Support Leg",
        "region": "Asia",
        "leg_type": "support",
        "markets": 5,
        "per_show_cost": 4600.0,
        "nightly_guarantee": 3000.0,
    },
]


async def search_routing_legs(region: str = "", leg_type: str = "") -> dict:
    """Search the routing directory by region and/or leg type.

    Both filters are optional and matched case-insensitively as substrings.
    ``region`` matches the leg's region (e.g. "US West", "Europe") and
    ``leg_type`` matches the type (e.g. "headline", "support", "festival").
    Returns {"legs": [...], "count": int}. Pure — no I/O.
    """
    rg = (region or "").strip().lower()
    lt = (leg_type or "").strip().lower()
    matches = [
        dict(leg)
        for leg in _LEGS
        if (not rg or rg in leg["region"].lower())
        and (not lt or lt in leg["leg_type"].lower())
    ]
    return {"legs": matches, "count": len(matches)}


def _get_leg(leg_id: str) -> dict | None:
    lid = (leg_id or "").strip()
    for leg in _LEGS:
        if leg["id"] == lid:
            return leg
    return None


async def draft_tour_budget(
    artist_id: str,
    leg_id: str = "",
    num_shows: int = 0,
    nightly_guarantee: float = 0,
) -> dict:
    """Draft a concrete tour budget by applying a leg's per-show cost to a run.

    Deterministic P&L construction — never contacts a production or crewing API.
    Looks the leg up by id, checks a positive show count and (falling back to the
    leg's typical guarantee when none is supplied) a nightly guarantee are present,
    then projects gross (shows × guarantee), operating cost (shows × per-show
    cost), and net. Returns a structured budget with line items, projected net, any
    gaps, and a recommendation of "run" / "revise" / "blocked".
    """
    leg = _get_leg(leg_id)

    try:
        shows = int(num_shows or 0)
    except (TypeError, ValueError):
        shows = 0

    # Fall back to the leg's typical nightly guarantee when the caller omits one.
    supplied_guarantee = nightly_guarantee not in (None, "", 0, 0.0)
    if supplied_guarantee:
        try:
            gtee = round(float(nightly_guarantee or 0), 2)
        except (TypeError, ValueError):
            gtee = 0.0
    elif leg is not None:
        gtee = round(float(leg["nightly_guarantee"]), 2)
    else:
        gtee = 0.0

    gaps = []
    if not (leg_id or "").strip():
        gaps.append("missing_leg")
    elif leg is None:
        gaps.append("unknown_leg")
    if shows <= 0:
        gaps.append("non_positive_shows")
    if gtee <= 0:
        gaps.append("non_positive_guarantee")

    line_items = []
    gross = 0.0
    operating_cost = 0.0
    projected_net = 0.0
    if leg is not None and shows > 0 and gtee > 0:
        gross = round(shows * gtee, 2)
        operating_cost = round(shows * leg["per_show_cost"], 2)
        projected_net = round(gross - operating_cost, 2)
        line_items.append({"label": "gross_guarantees", "amount": gross})
        line_items.append({"label": "operating_cost", "amount": -operating_cost})

    if "unknown_leg" in gaps or "missing_leg" in gaps:
        # Without a valid leg target the budget cannot be built at all.
        recommendation = "blocked"
    elif gaps or projected_net <= 0:
        recommendation = "revise"
    else:
        recommendation = "run"
    viable = recommendation == "run"

    return {
        "viable": viable,
        "gaps": gaps,
        "leg_id": leg["id"] if leg else (leg_id or "").strip(),
        "leg_name": leg["name"] if leg else None,
        "region": leg["region"] if leg else None,
        "num_shows": shows,
        "nightly_guarantee": gtee,
        "line_items": line_items,
        "gross_guarantees": gross,
        "operating_cost": operating_cost,
        "projected_net": projected_net,
        "recommendation": recommendation,
    }


def _tour_ops_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's tour-ops/crewing account.

    In production this would look up a stored tour-ops-account link for the artist.
    Here it is driven purely by the ``TOUR_COMMANDER_ACCOUNT_CONNECTED`` env flag so
    tests can toggle connected / expired / not-connected with ZERO network calls and
    NO real secret. Values:
      - "expired"                     → raise TourOpsAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("TOUR_COMMANDER_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise TourOpsAuthExpired("tour-ops-account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def book_crew_call(
    artist_id: str,
    leg_id: str,
    call_date: str,
    crew_size: int = 0,
) -> dict:
    """Confirm a crew call on a date for a leg via the artist's tour-ops account.

    Raises TourOpsNotConnected / TourOpsAuthExpired when no tour-ops account is
    linked so the caller can surface a 'connect your tour-ops account' message
    instead of a hard failure. When the leg id is unknown, returns a structured
    {"status": "unknown_leg"} result rather than raising. On success returns a
    deterministic mock crew-call reference — NO network call is ever made and no
    crew is actually booked.
    """
    if not _tour_ops_connected(artist_id):
        raise TourOpsNotConnected(
            "artist has not connected a tour-ops/crewing account"
        )
    leg = _get_leg(leg_id)
    if leg is None:
        return {"status": "unknown_leg", "leg_id": (leg_id or "").strip()}
    cd = (call_date or "").strip()
    try:
        size = int(crew_size or 0)
    except (TypeError, ValueError):
        size = 0
    digest = hashlib.sha1(
        f"{artist_id}:{leg['id']}:{cd}:{size}".encode("utf-8")
    ).hexdigest()
    reference = "CREW-" + digest[:10].upper()
    return {
        "status": "confirmed",
        "reference": reference,
        "leg_id": leg["id"],
        "leg_name": leg["name"],
        "call_date": cd,
        "crew_size": size,
    }
