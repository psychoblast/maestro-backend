"""
PLMKR Airwave — radio & playlist action service (mock-first).

Backs the Airwave (Solo — Radio & Playlist) agent's tool_use loop in
/api/chat_stream (see AIRWAVE_TOOLS in main.py). Solo does not just advise on radio
plugging and playlist pitching — these functions let the agent take real
radio/playlist actions: search the directory of radio stations and playlist outlets
an artist can target (each carrying the format it programs, the market it serves,
and its weekly reach), draft a concrete airplay/playlist pitch by applying a
target's reach and placement odds to a specific track so the artist has a
numbers-backed pitch to send a programmer or curator, and submit that pitch through
the artist's connected radio-plugging / DSP-pitching account so a track actually
gets pitched on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live radio/DSP/plugging APIs, no submission rails, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_airwave_account_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring venue_hawk_service._venue_booking_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class AirwaveAccountNotConnected(Exception):
    """Raised when the artist has not connected a radio-plugging / DSP-pitching account.

    Mirrors venue_hawk_service.VenueBookingNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your plugging account first'
    result instead of crashing the stream.
    """


class AirwaveAuthExpired(Exception):
    """Raised when a previously connected plugging-account authorization expired."""


# ── Airplay directory (in-memory reference data) ───────────────────────────────
# A curated set of radio stations and playlist outlets an artist can pursue. Each
# target carries its type (radio / playlist), the format it programs, the market it
# serves, its weekly reach (listeners or followers), how many add slots it opens per
# week, and the artist's realistic placement rate (percent chance of landing an add
# / spin). The agent can surface the right targets for a campaign and apply a
# target's numbers to a track to draft a real pitch. No I/O.
_TARGETS = [
    {
        "id": "tgt-kexp-drive",
        "name": "KEXP Drive Time",
        "type": "radio",
        "format": "indie",
        "market": "Seattle",
        "reach": 180000,
        "add_slots": 6,
        "placement_rate_pct": 20,
    },
    {
        "id": "tgt-bbc-6music",
        "name": "BBC 6 Music Rotation",
        "type": "radio",
        "format": "indie",
        "market": "United Kingdom",
        "reach": 2500000,
        "add_slots": 4,
        "placement_rate_pct": 8,
    },
    {
        "id": "tgt-triple-j",
        "name": "Triple J Unearthed",
        "type": "radio",
        "format": "rock",
        "market": "Australia",
        "reach": 1400000,
        "add_slots": 5,
        "placement_rate_pct": 12,
    },
    {
        "id": "tgt-fresh-finds",
        "name": "Fresh Finds",
        "type": "playlist",
        "format": "pop",
        "market": "Global",
        "reach": 900000,
        "add_slots": 20,
        "placement_rate_pct": 15,
    },
    {
        "id": "tgt-indie-pop-list",
        "name": "Indie Pop Rising",
        "type": "playlist",
        "format": "indie",
        "market": "Global",
        "reach": 320000,
        "add_slots": 12,
        "placement_rate_pct": 25,
    },
    {
        "id": "tgt-electronic-heat",
        "name": "Electronic Heat",
        "type": "playlist",
        "format": "electronic",
        "market": "Global",
        "reach": 540000,
        "add_slots": 10,
        "placement_rate_pct": 18,
    },
]


async def search_airplay_targets(format: str = "", market: str = "") -> dict:
    """Search airplay targets by the format they program and/or the market they serve.

    Both filters are optional and matched case-insensitively as substrings.
    ``format`` matches the target's programmed format (e.g. "indie", "pop",
    "rock", "electronic"), and ``market`` matches the market/region it serves
    (e.g. "United Kingdom", "Global"). Returns {"targets": [...], "count": int}.
    Pure — no I/O.
    """
    fmt = (format or "").strip().lower()
    mk = (market or "").strip().lower()
    matches = [
        dict(t)
        for t in _TARGETS
        if (not fmt or fmt in t["format"].lower())
        and (not mk or mk in t["market"].lower())
    ]
    return {"targets": matches, "count": len(matches)}


def _get_target(target_id: str) -> dict | None:
    tid = (target_id or "").strip()
    for t in _TARGETS:
        if t["id"] == tid:
            return t
    return None


async def draft_airplay_pitch(
    artist_id: str,
    target_id: str = "",
    track_title: str = "",
    release_date: str = "",
) -> dict:
    """Draft a concrete airplay/playlist pitch by applying a target's numbers to a track.

    Deterministic pitch construction — never contacts a programmer, curator, or DSP
    API. Looks the target up by id, checks a track title and release date are
    present, and estimates the audience the artist could reach (target reach ×
    placement rate) plus how many add slots that realistically converts to. Returns
    a structured pitch with line items, projected reach, gaps, and a recommendation
    of "send" / "revise" / "blocked".
    """
    target = _get_target(target_id)

    gaps = []
    if not (track_title or "").strip():
        gaps.append("missing_track_title")
    if not (release_date or "").strip():
        gaps.append("missing_release_date")
    if not (target_id or "").strip():
        gaps.append("missing_target")
    elif target is None:
        gaps.append("unknown_target")

    line_items = []
    audience_potential = 0
    projected_adds = 0
    if target is not None:
        audience_potential = int(
            round(target["reach"] * target["placement_rate_pct"] / 100.0)
        )
        projected_adds = int(
            round(target["add_slots"] * target["placement_rate_pct"] / 100.0)
        )
        line_items.append({"label": "reach", "amount": target["reach"]})
        line_items.append({"label": "audience_potential", "amount": audience_potential})

    if "unknown_target" in gaps or "missing_target" in gaps:
        # Without a valid target the pitch cannot be built at all.
        recommendation = "blocked"
    elif gaps or audience_potential <= 0:
        recommendation = "revise"
    else:
        recommendation = "send"
    viable = recommendation == "send"

    return {
        "viable": viable,
        "gaps": gaps,
        "target_id": target["id"] if target else (target_id or "").strip(),
        "target_name": target["name"] if target else None,
        "target_type": target["type"] if target else None,
        "format": target["format"] if target else None,
        "market": target["market"] if target else None,
        "track_title": (track_title or "").strip(),
        "release_date": (release_date or "").strip(),
        "line_items": line_items,
        "audience_potential": audience_potential,
        "projected_adds": projected_adds,
        "recommendation": recommendation,
    }


def _airwave_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's radio-plugging / DSP-pitching account.

    In production this would look up a stored plugging-account link for the artist.
    Here it is driven purely by the ``AIRWAVE_ACCOUNT_CONNECTED`` env flag so tests
    can toggle connected / expired / not-connected with ZERO network calls and NO
    real secret. Values:
      - "expired"                     → raise AirwaveAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("AIRWAVE_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise AirwaveAuthExpired("plugging-account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def submit_airplay_pitch(
    artist_id: str,
    target_id: str,
    track_title: str,
    release_date: str = "",
) -> dict:
    """Submit an airplay/playlist pitch for a track via the artist's plugging account.

    Raises AirwaveAccountNotConnected / AirwaveAuthExpired when no plugging account
    is linked so the caller can surface a 'connect your plugging account' message
    instead of a hard failure. When the target id is unknown, returns a structured
    {"status": "unknown_target"} result rather than raising. On success returns a
    deterministic mock pitch reference — NO network call is ever made and no pitch is
    actually delivered.
    """
    if not _airwave_account_connected(artist_id):
        raise AirwaveAccountNotConnected(
            "artist has not connected a radio-plugging/DSP-pitching account"
        )
    target = _get_target(target_id)
    if target is None:
        return {"status": "unknown_target", "target_id": (target_id or "").strip()}
    tt = (track_title or "").strip()
    rd = (release_date or "").strip()
    digest = hashlib.sha1(
        f"{artist_id}:{target['id']}:{tt}:{rd}".encode("utf-8")
    ).hexdigest()
    reference = "PITCH-" + digest[:10].upper()
    return {
        "status": "pitched",
        "reference": reference,
        "target_id": target["id"],
        "target_name": target["name"],
        "track_title": tt,
        "release_date": rd,
    }
