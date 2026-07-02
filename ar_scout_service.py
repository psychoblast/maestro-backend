"""
PLMKR AR-Scout — A&R action service (mock-first).

Backs the AR-Scout (Scout — A&R) agent's tool_use loop in /api/chat_stream (see
AR_SCOUT_TOOLS in main.py). Scout does not just advise on sound development, demo
feedback, and career positioning — these functions let the agent take real A&R
actions: search a directory of emerging/unsigned artist prospects worth scouting
(each carrying the genre it sits in, its region, and its development stage), run a
structured demo/sound evaluation that scores a track across the five A&R pillars and
returns a develop / pass / sign-track recommendation, and log a scouting note and
rating on a prospect through the artist's connected A&R CRM so a real record gets
written on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live scouting/CRM APIs, no streaming data, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_ar_scout_crm_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring venue_hawk_service._venue_booking_connected
    without touching a wire.
  - Deterministic: scores are derived from a stable hash of the inputs and no
    timestamps or random values leak into return payloads, so tests can assert
    on exact structure.
"""
import hashlib
import os


class ArScoutCRMNotConnected(Exception):
    """Raised when the artist has not connected an A&R CRM / scouting account.

    Mirrors venue_hawk_service.VenueBookingNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your A&R CRM first'
    result instead of crashing the stream.
    """


class ArScoutCRMAuthExpired(Exception):
    """Raised when a previously connected A&R CRM authorization expired."""


# ── Prospect directory (in-memory reference data) ──────────────────────────────
# A curated set of emerging/unsigned artists worth scouting. Each prospect carries
# the genre it sits in, its region, a development stage (unsigned / emerging /
# buzzing), an approximate monthly-listener count, and a one-line standout note.
# The agent can surface the right prospects for a scouting brief and log notes
# against them. No I/O.
_PROSPECTS = [
    {
        "id": "pro-neon-hollow",
        "name": "Neon Hollow",
        "genre": "indie",
        "region": "Los Angeles",
        "stage": "buzzing",
        "monthly_listeners": 84000,
        "standout": "distinctive falsetto hook, strong TikTok pull-through",
    },
    {
        "id": "pro-cassette-kids",
        "name": "Cassette Kids",
        "genre": "indie pop",
        "region": "London",
        "stage": "emerging",
        "monthly_listeners": 21000,
        "standout": "tight songwriting, live show already selling out clubs",
    },
    {
        "id": "pro-velvet-signal",
        "name": "Velvet Signal",
        "genre": "r&b",
        "region": "Atlanta",
        "stage": "buzzing",
        "monthly_listeners": 132000,
        "standout": "vocal tone that cuts through a crowded lane",
    },
    {
        "id": "pro-paper-anthem",
        "name": "Paper Anthem",
        "genre": "pop",
        "region": "Nashville",
        "stage": "emerging",
        "monthly_listeners": 47000,
        "standout": "radio-ready choruses, needs production polish",
    },
    {
        "id": "pro-glass-district",
        "name": "Glass District",
        "genre": "electronic",
        "region": "Berlin",
        "stage": "unsigned",
        "monthly_listeners": 9000,
        "standout": "inventive sound design, no clear single yet",
    },
    {
        "id": "pro-southbound-echo",
        "name": "Southbound Echo",
        "genre": "americana",
        "region": "Austin",
        "stage": "emerging",
        "monthly_listeners": 33000,
        "standout": "authentic storytelling, loyal regional following",
    },
]

# The five A&R pillars a demo/sound evaluation scores against.
_PILLARS = ["hook", "production", "vocal", "originality", "market_fit"]


async def search_prospects(genre: str = "", region: str = "", stage: str = "") -> dict:
    """Search the prospect directory by genre, region, and/or development stage.

    All three filters are optional and matched case-insensitively as substrings.
    ``genre`` matches the prospect's genre (e.g. "indie"), ``region`` matches its
    region/city (e.g. "London"), and ``stage`` matches its stage (e.g. "emerging",
    "buzzing", "unsigned"). Returns {"prospects": [...], "count": int}. Pure — no I/O.
    """
    g = (genre or "").strip().lower()
    r = (region or "").strip().lower()
    s = (stage or "").strip().lower()
    matches = [
        dict(p)
        for p in _PROSPECTS
        if (not g or g in p["genre"].lower())
        and (not r or r in p["region"].lower())
        and (not s or s in p["stage"].lower())
    ]
    return {"prospects": matches, "count": len(matches)}


def _get_prospect(prospect_id: str) -> dict | None:
    pid = (prospect_id or "").strip()
    for p in _PROSPECTS:
        if p["id"] == pid:
            return p
    return None


def _pillar_scores(seed: str) -> dict:
    """Derive deterministic 1–10 pillar scores from a stable hash of the inputs.

    Same seed → same scores every time (no randomness, no I/O), so the agent's
    read on a demo is reproducible and tests can assert on exact structure. Each
    pillar takes one byte of a sha1 digest mapped into the 1–10 range.
    """
    digest = hashlib.sha1(seed.encode("utf-8")).digest()
    return {pillar: (digest[i] % 10) + 1 for i, pillar in enumerate(_PILLARS)}


async def evaluate_demo(
    artist_id: str,
    track_title: str = "",
    genre: str = "",
) -> dict:
    """Run a structured demo/sound evaluation and return an A&R scorecard.

    Deterministic evaluation — never calls an LLM or an audio-analysis API. Scores
    the track across the five A&R pillars (hook, production, vocal, originality,
    market_fit), averages them into a composite, and maps the composite to a
    recommendation of "sign_track" / "develop" / "pass". When no track title is
    provided there is nothing to assess, so it returns a structured
    {"recommendation": "insufficient_material"} with a gaps list instead of
    fabricating a score. Returns a plain JSON-serializable dict. Pure — no I/O.
    """
    title = (track_title or "").strip()
    gen   = (genre or "").strip()

    gaps = []
    if not title:
        gaps.append("missing_track_title")

    if gaps:
        return {
            "track_title": title,
            "genre": gen,
            "scores": {},
            "composite": 0.0,
            "gaps": gaps,
            "recommendation": "insufficient_material",
        }

    scores = _pillar_scores(f"{artist_id}:{title}:{gen}")
    composite = round(sum(scores.values()) / len(scores), 1)
    if composite >= 7.5:
        recommendation = "sign_track"
    elif composite >= 5.5:
        recommendation = "develop"
    else:
        recommendation = "pass"

    return {
        "track_title": title,
        "genre": gen,
        "scores": scores,
        "composite": composite,
        "gaps": gaps,
        "recommendation": recommendation,
    }


def _ar_scout_crm_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's A&R CRM / scouting account.

    In production this would look up a stored CRM link for the artist. Here it is
    driven purely by the ``AR_SCOUT_CRM_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise ArScoutCRMAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("AR_SCOUT_CRM_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise ArScoutCRMAuthExpired("A&R CRM authorization expired")
    return val in ("1", "true", "yes", "connected")


async def log_scouting_note(
    artist_id: str,
    prospect_id: str,
    note: str = "",
    rating: int = 0,
) -> dict:
    """Log a scouting note and rating on a prospect via the artist's A&R CRM.

    Raises ArScoutCRMNotConnected / ArScoutCRMAuthExpired when no CRM is linked so
    the caller can surface a 'connect your A&R CRM' message instead of a hard
    failure. When the prospect id is unknown, returns a structured
    {"status": "unknown_prospect"} result rather than raising. On success returns a
    deterministic mock note reference — NO network call is ever made and no record
    is actually written. The rating is clamped to the 0–10 range.
    """
    if not _ar_scout_crm_connected(artist_id):
        raise ArScoutCRMNotConnected(
            "artist has not connected an A&R CRM / scouting account"
        )
    prospect = _get_prospect(prospect_id)
    if prospect is None:
        return {"status": "unknown_prospect", "prospect_id": (prospect_id or "").strip()}
    txt = (note or "").strip()
    try:
        rt = int(rating or 0)
    except (TypeError, ValueError):
        rt = 0
    rt = max(0, min(10, rt))
    digest = hashlib.sha1(
        f"{artist_id}:{prospect['id']}:{txt}:{rt}".encode("utf-8")
    ).hexdigest()
    reference = "NOTE-" + digest[:10].upper()
    return {
        "status": "logged",
        "reference": reference,
        "prospect_id": prospect["id"],
        "prospect_name": prospect["name"],
        "note": txt,
        "rating": rt,
    }
