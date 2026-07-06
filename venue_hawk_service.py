"""
PLMKR Venue-Hawk — booking-agent action service (mock-first, OUTREACH pattern).

Backs the Venue-Hawk (Ray B — Booking Agent) agent's tool_use loop in
/api/chat_stream (see VENUE_HAWK_TOOLS in main.py). Ray B does not just advise on
venues, deals, and routing — these functions let the agent take real booking-agent
actions, honestly:

  - search_venues:          filter an ARTIST-SUPPLIED venue list on structured
                            fields (market/region, capacity tier, genre fit). It
                            NEVER invents venue names — with no real venue data it
                            returns a [NEEDS:venue_targets] gap.
  - submit_booking_hold:    build/record a hold-REQUEST state (venue, date(s), act,
                            deal-structure ask, hold_type/pencil order) with an
                            aggregated missing[]; it does NOT send and is NOT gated.
                            A hold is not a confirmed booking.
  - send_booking_inquiry:   the Marcus/Nia/Solo send seam — the MODEL writes the
                            inquiry body in its turn and passes it in; this tool
                            only SENDS (deterministic mock, ``BOOK-``+sha1) behind
                            the VENUE_HAWK_ACCOUNT_CONNECTED gate. It never writes
                            or edits prose and never invents a venue or a figure.
  - lookup_booking_doctrine: a PURE read over booking_data.py — no gate, no I/O.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live venue/promoter APIs, no ticketing rails, no LLM
    client and no model send call anywhere in this tool layer — the send seam is
    a deterministic sha1 mock only.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_venue_booking_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring vault_keeper_service._vault_account_connected.
  - Deterministic: no timestamps or random values leak into return payloads.
  - NEVER fabricate a venue name, promoter, guarantee, split, or commission — the
    booking_data.py HONESTY_RULES are the law of this module.
"""
import hashlib
import os

import booking_data


class VenueBookingNotConnected(Exception):
    """Raised when the artist has not connected a booking/ticketing account.

    The tool loop catches this and degrades gracefully into a structured 'connect
    your booking account first' result instead of crashing the stream.
    """


class VenueBookingAuthExpired(Exception):
    """Raised when a previously connected booking-account authorization expired."""


# ── search_venues — honest, artist-supplied only (never fabricates venues) ─────

def _venue_field(v: dict, *keys) -> str:
    """Return the first present, stringified value among ``keys`` on venue ``v``."""
    for k in keys:
        val = v.get(k)
        if val is not None:
            return str(val)
    return ""


def _match_venue(v: dict, market: str, capacity_tier: str, genre: str) -> bool:
    """Case-insensitive substring match on whichever structured fields exist.

    A filter that is empty matches everything; a filter with a value only matches
    when the venue carries the corresponding field and it contains the value.
    """
    if market:
        hay = " ".join((_venue_field(v, "market", "region", "city"),)).lower()
        if market.lower() not in hay:
            return False
    if capacity_tier:
        hay = _venue_field(v, "capacity_tier", "tier").lower()
        if capacity_tier.lower() not in hay:
            return False
    if genre:
        hay = _venue_field(v, "genre", "genres", "genre_fit").lower()
        if genre.lower() not in hay:
            return False
    return True


async def search_venues(market: str = "", capacity_tier: str = "",
                        genre: str = "", venue_list=None) -> dict:
    """Filter an ARTIST-SUPPLIED venue list on structured fields — never invents.

    ``venue_list`` is the artist's own list of venue dicts (each may carry name,
    market/region, capacity_tier, genre). When it is present and non-empty the
    function filters it by whichever of ``market`` / ``capacity_tier`` / ``genre``
    were supplied and returns the matches tagged ``[ARTIST-SUPPLIED:venue_list]``.
    When NO real venue data is supplied it returns a ``[NEEDS:venue_targets]`` gap
    — it NEVER conjures a venue name from a built-in directory. Pure — no I/O.
    """
    mk = (market or "").strip()
    ct = (capacity_tier or "").strip()
    g  = (genre or "").strip()
    criteria = {"market": mk, "capacity_tier": ct, "genre": g}

    supplied = [v for v in (venue_list or []) if isinstance(v, dict)]
    if not supplied:
        return {
            "status": "needs_targets",
            "source": "[NEEDS:venue_targets]",
            "criteria": criteria,
            "venues": [],
            "count": 0,
            "message": ("No venue directory is connected and no venue list was "
                        "supplied. Venue and promoter names are never invented — "
                        "supply a venue list or connect a real source."),
        }

    matches = [dict(v) for v in supplied if _match_venue(v, mk, ct, g)]
    return {
        "status": "artist_supplied",
        "source": "[ARTIST-SUPPLIED:venue_list]",
        "criteria": criteria,
        "venues": matches,
        "count": len(matches),
    }


# ── submit_booking_hold — build/record hold-REQUEST state (no send, no gate) ────

_KNOWN_HOLD_TYPES = booking_data.HOLD_SYSTEM["hold_order"]  # ("first","second","third")


def _clean_dates(show_dates) -> list:
    """Normalize show_dates (str or list) into a list of non-empty date strings."""
    if isinstance(show_dates, str):
        items = [show_dates]
    elif isinstance(show_dates, (list, tuple)):
        items = list(show_dates)
    else:
        items = []
    return [str(d).strip() for d in items if str(d).strip()]


async def submit_booking_hold(artist_id: str, venue: str = "", venue_id: str = "",
                              show_dates=None, act: str = "",
                              deal_structure: str = "", hold_type: str = "first") -> dict:
    """Build and record a hold-REQUEST — does NOT send and is NOT gated.

    Assembles the state a hold needs (venue, date(s), act, deal-structure ask,
    hold_type/pencil order) and aggregates a ``missing[]`` list of the gaps rather
    than fabricating any of them. ``hold_type`` follows HOLD_SYSTEM's pencil order
    (first / second / third); an unrecognized value is flagged, never silently
    accepted as standard. Deterministic; no network, no LLM. A hold is not a
    confirmed booking — that caveat rides out in the result.
    """
    vn  = (venue or "").strip()
    vid = (venue_id or "").strip()
    dates = _clean_dates(show_dates)
    ac  = (act or "").strip()
    ds  = (deal_structure or "").strip()
    ht  = (hold_type or "first").strip().lower() or "first"

    missing = []
    if not (vn or vid):
        missing.append("venue")
    if not dates:
        missing.append("show_dates")
    if not ac:
        missing.append("act")
    if not ds:
        missing.append("deal_structure")

    return {
        "status": "recorded" if not missing else "incomplete",
        "hold_request": {
            "venue": vn,
            "venue_id": vid,
            "show_dates": dates,
            "act": ac,
            "deal_structure": ds,
            "hold_type": ht,
        },
        "hold_type_recognized": ht in _KNOWN_HOLD_TYPES,
        "missing": missing,
        "note": ("A hold is a request, not a confirmed booking; hold and challenge "
                 "windows vary by venue — verify live."),
    }


# ── lookup_booking_doctrine — pure corpus read over booking_data.py ────────────

_BOOKING_TOPIC_SECTIONS = {
    "hold_system":     booking_data.HOLD_SYSTEM,
    "deal_mechanisms": booking_data.DEAL_MECHANISMS,
    "deal_memo":       booking_data.DEAL_MEMO_SPEC,
    "rider":           booking_data.RIDER_SPEC,
    "outreach":        booking_data.OUTREACH_DOCTRINE,
    "agent_economics": booking_data.AGENT_ECONOMICS,
    "boundaries":      booking_data.OUT_OF_SCOPE,
}

BOOKING_DOCTRINE_TOPICS = ("hold_system", "deal_mechanisms", "deal_memo", "rider",
                           "outreach", "agent_economics", "boundaries")


async def lookup_booking_doctrine(topic: str = "") -> dict:
    """Look up the doctrine for ONE booking topic — pure corpus read, no gate.

    Returns the relevant booking_data.py section plus the FULL honesty-rule set
    (venues/figures are never invented; deal evaluation is structural; a hold is
    not a confirmation). An unknown topic returns a structured ``unknown_topic``
    error listing the supported topics. No I/O, no LLM, nothing invented.
    """
    t = (topic or "").strip().lower()
    honesty_rules = [dict(r) for r in booking_data.HONESTY_RULES]
    if t in _BOOKING_TOPIC_SECTIONS:
        return {
            "status": "ok",
            "topic": t,
            "data": _BOOKING_TOPIC_SECTIONS[t],
            "honesty_rules": honesty_rules,
        }
    return {
        "status": "unknown_topic",
        "topic": t or "(missing)",
        "supported_topics": list(BOOKING_DOCTRINE_TOPICS),
        "message": ("Unsupported topic. Supported: "
                    + ", ".join(BOOKING_DOCTRINE_TOPICS) + "."),
    }


# ── send_booking_inquiry — the Marcus send seam (model writes body; tool sends) ─

def _venue_booking_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's booking/ticketing account.

    Driven purely by the ``VENUE_HAWK_ACCOUNT_CONNECTED`` env flag so tests can
    toggle connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise VenueBookingAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("VENUE_HAWK_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise VenueBookingAuthExpired("booking-account authorization expired")
    return val in ("1", "true", "yes", "connected")


def _submit_booking_inquiry(artist_id: str, venue_key: str, subject: str, body: str) -> str:
    """In-repo mock-send seam — deterministic ``BOOK-`` sha1 reference, ZERO network.

    This is the ONLY 'send' point and it is obviously a mock: no wire, no
    messages.create. The reference is a stable sha1 of the identity + the model's
    verbatim subject/body so a test can assert determinism.
    """
    digest = hashlib.sha1(
        f"{artist_id}:{venue_key}:{subject}:{body}".encode("utf-8")
    ).hexdigest()
    return "BOOK-" + digest[:10].upper()


async def send_booking_inquiry(artist_id: str, venue_id: str = "", venue: str = "",
                               subject: str = "", body: str = "") -> dict:
    """Send an artist's booking inquiry — the MODEL wrote the body; this tool sends.

    The ``subject`` and ``body`` are written by the model in its turn and passed in
    verbatim; this function NEVER generates or edits them and NEVER invents a venue
    or a figure. It follows the account-gate seam: raises VenueBookingNotConnected
    / VenueBookingAuthExpired when no booking account is linked, returns a
    structured {"status": "missing_venue"} when no venue is identified, and on
    success returns a deterministic mock send reference — NO network call is ever
    made and no inquiry is actually delivered. The supplied subject/body ride back
    out byte-exact so the caller can confirm what was sent.
    """
    if not _venue_booking_connected(artist_id):
        raise VenueBookingNotConnected(
            "artist has not connected a booking/ticketing account"
        )
    vid = (venue_id or "").strip()
    vn  = (venue or "").strip()
    venue_key = vid or vn
    if not venue_key:
        return {"status": "missing_venue", "venue_id": vid, "venue": vn}
    reference = _submit_booking_inquiry(artist_id, venue_key, subject, body)
    return {
        "status": "sent",
        "reference": reference,
        "venue_id": vid,
        "venue": vn,
        "subject": subject,   # verbatim — the tool never edits the model's inquiry
        "body": body,         # verbatim — never generated or modified here
    }
