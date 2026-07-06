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

import radio_promo_data


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


# ── Unit-2 doctrine lookup + radio/DSP pitch send rail ─────────────────────────
# lookup_radio_promo_doctrine is a PURE read over radio_promo_data (no gate, no
# I/O); a curator-related topic returns an OUT_OF_SCOPE answer naming the
# management department (Marcus) — Solo runs radio + DSP editorial, never curator
# outreach. send_radio_pitch follows the Marcus send seam: the MODEL writes the
# pitch body in its turn and passes it in — the tool SENDS (deterministic mock
# sha1 reference, ZERO network), never generates/edits the body, and NEVER asserts
# or computes a MAPL status: the artist's DECLARED letters pass through verbatim,
# or a [NEEDS:mapl_declaration] gap is surfaced.

# The one-topic doctrine surface. Reference only — nothing mutates these objects.
_RADIO_TOPIC_SECTIONS = {
    "college_radio":        radio_promo_data.COLLEGE_RADIO,
    "cancon":               radio_promo_data.CANCON,
    "commercial_radio":     radio_promo_data.COMMERCIAL_RADIO,
    "dsp_editorial":        radio_promo_data.DSP_EDITORIAL,
    "servicing_platforms":  radio_promo_data.SERVICING_PLATFORMS,
    "delivery_vs_outreach": radio_promo_data.DELIVERY_VS_OUTREACH_DOCTRINE,
    "satellite_public":     radio_promo_data.SATELLITE_AND_PUBLIC,
}

RADIO_PROMO_TOPICS = ("college_radio", "cancon", "commercial_radio",
                      "dsp_editorial", "servicing_platforms",
                      "delivery_vs_outreach", "satellite_public")

# Missing-MAPL sentinel — a declaration is the artist's to make, never computed.
MAPL_DECLARATION_GAP = "[NEEDS:mapl_declaration]"


async def lookup_radio_promo_doctrine(topic: str = "") -> dict:
    """Look up the doctrine for ONE radio/DSP topic — pure corpus read, no gate.

    Returns the relevant radio_promo_data section plus the FULL honesty-rule set
    (never assert MAPL; a pitch is consideration, never a placement; costs and
    processes verify live). A CURATOR-related topic returns a structured
    ``out_of_scope`` answer naming the management department (Marcus) — playlist-
    curator outreach is not Solo's lane. Any other unknown topic returns a
    structured ``unknown_topic`` error. No I/O, no LLM, nothing invented.
    """
    t = (topic or "").strip().lower()
    if "curator" in t or t in ("playlist_curator", "playlist_curator_outreach",
                               "playlist_curators", "playlist"):
        oos = radio_promo_data.OUT_OF_SCOPE["playlist_curator_outreach"]
        return {
            "status": "out_of_scope",
            "topic": t,
            "owner": oos["owner"],
            "reason": oos["reason"],
            "message": ("Playlist-curator outreach is handled by the management "
                        "department (Marcus), not Solo. Solo covers radio + DSP "
                        "editorial only."),
        }
    honesty_rules = [dict(r) for r in radio_promo_data.HONESTY_RULES]
    if t in _RADIO_TOPIC_SECTIONS:
        return {
            "status": "ok",
            "topic": t,
            "data": _RADIO_TOPIC_SECTIONS[t],
            "honesty_rules": honesty_rules,
        }
    return {
        "status": "unknown_topic",
        "topic": t or "(missing)",
        "supported_topics": list(RADIO_PROMO_TOPICS),
        "message": ("Unsupported topic. Supported: "
                    + ", ".join(RADIO_PROMO_TOPICS) + "."),
    }


async def send_radio_pitch(artist_id: str, target_id: str, subject: str = "",
                           body: str = "", mapl_declaration=None) -> dict:
    """Send an artist's radio / DSP-editorial pitch — the MODEL wrote it; tool sends.

    The ``subject`` and ``body`` are written by the model in its turn and passed in
    verbatim; this function NEVER generates or edits them. It NEVER asserts or
    computes a CanCon / MAPL status: the artist's DECLARED letters
    (``mapl_declaration``) ride through byte-exact, and when none is supplied the
    result carries a ``[NEEDS:mapl_declaration]`` gap — a status is never invented.
    It follows submit_airplay_pitch's gate seam: raises AirwaveAccountNotConnected
    / AirwaveAuthExpired when no plugging account is linked, returns a structured
    {"status": "unknown_target"} for an unknown target, and on success returns a
    deterministic mock send reference — NO network call is ever made.
    """
    if not _airwave_account_connected(artist_id):
        raise AirwaveAccountNotConnected(
            "artist has not connected a radio-plugging/DSP-pitching account"
        )
    target = _get_target(target_id)
    if target is None:
        return {"status": "unknown_target", "target_id": (target_id or "").strip()}
    declared = mapl_declaration
    if not (isinstance(declared, str) and declared.strip()):
        declared = MAPL_DECLARATION_GAP        # never computed — a gap, not a status
    digest = hashlib.sha1(
        f"{artist_id}:{target['id']}:{subject}:{body}".encode("utf-8")
    ).hexdigest()
    reference = "RPITCH-" + digest[:10].upper()
    return {
        "status": "sent",
        "reference": reference,
        "target_id": target["id"],
        "target_name": target["name"],
        "subject": subject,                    # verbatim — never edited
        "body": body,                          # verbatim — never generated
        "mapl_declaration": declared,          # artist's declared letters or a gap
    }
