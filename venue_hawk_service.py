"""
PLMKR Venue-Hawk — booking-agent action service (mock-first).

Backs the Venue-Hawk (Ray B — Booking Agent) agent's tool_use loop in
/api/chat_stream (see VENUE_HAWK_TOOLS in main.py). Ray B does not just advise on
venues, show deals, and routing — these functions let the agent take real
booking-agent actions: search the venue directory an artist can play (each carrying
the market it sits in and its capacity tier), draft a concrete show offer by
applying a venue's deal terms to a guarantee so the artist has a numbers-backed
proposal to send a promoter, and submit a booking hold on a date at a venue through
the artist's connected booking account so a date actually gets held on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live venue/promoter APIs, no ticketing rails, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_venue_booking_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring vault_keeper_service._vault_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class VenueBookingNotConnected(Exception):
    """Raised when the artist has not connected a booking/ticketing account.

    Mirrors vault_keeper_service.VaultAccountNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your booking account
    first' result instead of crashing the stream.
    """


class VenueBookingAuthExpired(Exception):
    """Raised when a previously connected booking-account authorization expired."""


# ── Venue directory (in-memory reference data) ─────────────────────────────────
# A curated set of venues an artist can pursue. Each venue carries the market it
# sits in, its capacity tier (club / theatre / amphitheatre), a hard capacity, an
# average ticket price, and the artist's typical door split (percent of gross the
# act keeps after the guarantee). The agent can surface the right rooms for a
# routing plan and apply a venue's terms to a guarantee to draft a real offer. No
# I/O.
_VENUES = [
    {
        "id": "ven-echo-club",
        "name": "The Echo Club",
        "market": "Los Angeles",
        "capacity_tier": "club",
        "capacity": 500,
        "avg_ticket": 25.0,
        "door_split_pct": 70,
    },
    {
        "id": "ven-canal-room",
        "name": "Canal Room",
        "market": "New York",
        "capacity_tier": "club",
        "capacity": 350,
        "avg_ticket": 20.0,
        "door_split_pct": 65,
    },
    {
        "id": "ven-mercury-hall",
        "name": "Mercury Hall",
        "market": "New York",
        "capacity_tier": "theatre",
        "capacity": 1200,
        "avg_ticket": 45.0,
        "door_split_pct": 75,
    },
    {
        "id": "ven-fillmore-west",
        "name": "Fillmore West",
        "market": "San Francisco",
        "capacity_tier": "theatre",
        "capacity": 1150,
        "avg_ticket": 40.0,
        "door_split_pct": 72,
    },
    {
        "id": "ven-corner-hotel",
        "name": "Corner Hotel",
        "market": "Melbourne",
        "capacity_tier": "club",
        "capacity": 800,
        "avg_ticket": 30.0,
        "door_split_pct": 68,
    },
    {
        "id": "ven-desert-amp",
        "name": "Desert Amphitheatre",
        "market": "Phoenix",
        "capacity_tier": "amphitheatre",
        "capacity": 5000,
        "avg_ticket": 60.0,
        "door_split_pct": 80,
    },
]


async def search_venues(market: str = "", capacity_tier: str = "") -> dict:
    """Search venues by the market they sit in and/or their capacity tier.

    Both filters are optional and matched case-insensitively as substrings.
    ``market`` matches the venue's market/city (e.g. "New York"), and
    ``capacity_tier`` matches the tier (e.g. "club", "theatre", "amphitheatre").
    Returns {"venues": [...], "count": int}. Pure — no I/O.
    """
    mk = (market or "").strip().lower()
    ct = (capacity_tier or "").strip().lower()
    matches = [
        dict(v)
        for v in _VENUES
        if (not mk or mk in v["market"].lower())
        and (not ct or ct in v["capacity_tier"].lower())
    ]
    return {"venues": matches, "count": len(matches)}


def _get_venue(venue_id: str) -> dict | None:
    vid = (venue_id or "").strip()
    for v in _VENUES:
        if v["id"] == vid:
            return v
    return None


async def draft_show_offer(
    artist_id: str,
    venue_id: str = "",
    show_date: str = "",
    guarantee: float = 0,
) -> dict:
    """Draft a concrete show offer by applying a venue's terms to a guarantee.

    Deterministic offer construction — never contacts a promoter or ticketing
    API. Looks the venue up by id, checks a show date and a positive guarantee are
    present, and estimates the artist's door potential (capacity × avg ticket ×
    door split) on top of the guarantee. Returns a structured offer with line
    items, projected payout, gaps, and a recommendation of
    "send" / "revise" / "blocked".
    """
    venue = _get_venue(venue_id)

    try:
        gtee = round(float(guarantee or 0), 2)
    except (TypeError, ValueError):
        gtee = 0.0

    gaps = []
    if not (show_date or "").strip():
        gaps.append("missing_show_date")
    if not (venue_id or "").strip():
        gaps.append("missing_venue")
    elif venue is None:
        gaps.append("unknown_venue")
    if gtee <= 0:
        gaps.append("non_positive_guarantee")

    line_items = []
    door_potential = 0.0
    projected_payout = 0.0
    if venue is not None and gtee > 0:
        door_potential = round(
            venue["capacity"] * venue["avg_ticket"] * venue["door_split_pct"] / 100.0,
            2,
        )
        line_items.append({"label": "guarantee", "amount": gtee})
        line_items.append({"label": "door_potential", "amount": door_potential})
        projected_payout = round(gtee + door_potential, 2)

    if "unknown_venue" in gaps or "missing_venue" in gaps:
        # Without a valid venue target the offer cannot be built at all.
        recommendation = "blocked"
    elif gaps or projected_payout <= 0:
        recommendation = "revise"
    else:
        recommendation = "send"
    viable = recommendation == "send"

    return {
        "viable": viable,
        "gaps": gaps,
        "venue_id": venue["id"] if venue else (venue_id or "").strip(),
        "venue_name": venue["name"] if venue else None,
        "market": venue["market"] if venue else None,
        "show_date": (show_date or "").strip(),
        "guarantee": gtee,
        "line_items": line_items,
        "door_potential": door_potential,
        "projected_payout": projected_payout,
        "recommendation": recommendation,
    }


def _venue_booking_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's booking/ticketing account.

    In production this would look up a stored booking-account link for the artist.
    Here it is driven purely by the ``VENUE_HAWK_ACCOUNT_CONNECTED`` env flag so
    tests can toggle connected / expired / not-connected with ZERO network calls
    and NO real secret. Values:
      - "expired"                     → raise VenueBookingAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("VENUE_HAWK_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise VenueBookingAuthExpired("booking-account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def submit_booking_hold(
    artist_id: str,
    venue_id: str,
    show_date: str,
    guarantee: float = 0,
) -> dict:
    """Submit a booking hold on a date at a venue via the artist's booking account.

    Raises VenueBookingNotConnected / VenueBookingAuthExpired when no booking
    account is linked so the caller can surface a 'connect your booking account'
    message instead of a hard failure. When the venue id is unknown, returns a
    structured {"status": "unknown_venue"} result rather than raising. On success
    returns a deterministic mock hold reference — NO network call is ever made and
    no date is actually held.
    """
    if not _venue_booking_connected(artist_id):
        raise VenueBookingNotConnected(
            "artist has not connected a booking/ticketing account"
        )
    venue = _get_venue(venue_id)
    if venue is None:
        return {"status": "unknown_venue", "venue_id": (venue_id or "").strip()}
    sd = (show_date or "").strip()
    try:
        gtee = round(float(guarantee or 0), 2)
    except (TypeError, ValueError):
        gtee = 0.0
    digest = hashlib.sha1(
        f"{artist_id}:{venue['id']}:{sd}:{gtee}".encode("utf-8")
    ).hexdigest()
    reference = "HOLD-" + digest[:10].upper()
    return {
        "status": "held",
        "reference": reference,
        "venue_id": venue["id"],
        "venue_name": venue["name"],
        "show_date": sd,
        "guarantee": gtee,
    }
