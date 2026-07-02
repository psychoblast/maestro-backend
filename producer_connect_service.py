"""
PLMKR Producer-Connect — production action service (mock-first).

Backs the Producer-Connect (Beat — Production) agent's tool_use loop in
/api/chat_stream (see PRODUCER_CONNECT_TOOLS in main.py). Beat does not just advise
on producer connections, beat licensing, and co-writes — these functions let the
agent take real production actions: search a directory of producers/beatmakers worth
connecting with (each carrying the genre it works in, its region, a budget tier, and
a typical session rate), run a structured evaluation of a beat-licensing offer that
scores it across the five deal pillars and returns an accept / negotiate / pass
recommendation, and log a collaboration/co-write request to a producer through the
artist's connected production network so a real record gets written on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live producer/CRM APIs, no streaming data, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_producer_network_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring ar_scout_service._ar_scout_crm_connected
    without touching a wire.
  - Deterministic: scores are derived from a stable hash of the inputs and no
    timestamps or random values leak into return payloads, so tests can assert
    on exact structure.
"""
import hashlib
import os


class ProducerNetworkNotConnected(Exception):
    """Raised when the artist has not connected a production network / collab account.

    Mirrors ar_scout_service.ArScoutCRMNotConnected: the tool loop catches this and
    degrades gracefully into a structured 'connect your production network first'
    result instead of crashing the stream.
    """


class ProducerNetworkAuthExpired(Exception):
    """Raised when a previously connected production network authorization expired."""


# ── Producer directory (in-memory reference data) ──────────────────────────────
# A curated set of producers/beatmakers worth connecting with. Each producer carries
# the genre it works in, its region, a budget tier (budget / mid / premium), an
# approximate per-song session rate in USD, and a one-line standout credit. The agent
# can surface the right producers for a brief and log collab requests against them.
# No I/O.
_PRODUCERS = [
    {
        "id": "prd-midnight-oil",
        "name": "Midnight Oil",
        "genre": "pop",
        "region": "Los Angeles",
        "tier": "premium",
        "session_rate_usd": 3500,
        "standout": "two platinum singles, radio-ready top-line instincts",
    },
    {
        "id": "prd-low-end-lab",
        "name": "Low End Lab",
        "genre": "hip hop",
        "region": "Atlanta",
        "tier": "mid",
        "session_rate_usd": 1200,
        "standout": "808 sound designer, fast turnaround on demos",
    },
    {
        "id": "prd-glasshouse",
        "name": "Glasshouse",
        "genre": "r&b",
        "region": "Toronto",
        "tier": "premium",
        "session_rate_usd": 2800,
        "standout": "lush chord work, mixes in-house",
    },
    {
        "id": "prd-tape-room",
        "name": "Tape Room",
        "genre": "indie",
        "region": "London",
        "tier": "budget",
        "session_rate_usd": 450,
        "standout": "analog warmth, great with first-time collaborators",
    },
    {
        "id": "prd-pulse-dept",
        "name": "Pulse Dept",
        "genre": "electronic",
        "region": "Berlin",
        "tier": "mid",
        "session_rate_usd": 1500,
        "standout": "club-tested drops, strong on arrangement",
    },
    {
        "id": "prd-front-porch",
        "name": "Front Porch",
        "genre": "americana",
        "region": "Nashville",
        "tier": "budget",
        "session_rate_usd": 600,
        "standout": "live-band feel, deep session-musician rolodex",
    },
]

# The five pillars a beat-licensing offer is scored against.
_PILLARS = ["value", "rights", "flexibility", "production_fit", "market"]


async def search_producers(genre: str = "", region: str = "", tier: str = "") -> dict:
    """Search the producer directory by genre, region, and/or budget tier.

    All three filters are optional and matched case-insensitively as substrings.
    ``genre`` matches the producer's genre (e.g. "hip hop"), ``region`` matches its
    region/city (e.g. "London"), and ``tier`` matches its budget tier (e.g. "budget",
    "mid", "premium"). Returns {"producers": [...], "count": int}. Pure — no I/O.
    """
    g = (genre or "").strip().lower()
    r = (region or "").strip().lower()
    t = (tier or "").strip().lower()
    matches = [
        dict(p)
        for p in _PRODUCERS
        if (not g or g in p["genre"].lower())
        and (not r or r in p["region"].lower())
        and (not t or t in p["tier"].lower())
    ]
    return {"producers": matches, "count": len(matches)}


def _get_producer(producer_id: str) -> dict | None:
    pid = (producer_id or "").strip()
    for p in _PRODUCERS:
        if p["id"] == pid:
            return p
    return None


def _pillar_scores(seed: str) -> dict:
    """Derive deterministic 1–10 pillar scores from a stable hash of the inputs.

    Same seed → same scores every time (no randomness, no I/O), so the agent's read
    on a beat deal is reproducible and tests can assert on exact structure. Each
    pillar takes one byte of a sha1 digest mapped into the 1–10 range.
    """
    digest = hashlib.sha1(seed.encode("utf-8")).digest()
    return {pillar: (digest[i] % 10) + 1 for i, pillar in enumerate(_PILLARS)}


async def evaluate_beat_deal(
    artist_id: str,
    beat_title: str = "",
    license_type: str = "",
    price_usd: int = 0,
) -> dict:
    """Run a structured evaluation of a beat-licensing offer and return a scorecard.

    Deterministic evaluation — never calls an LLM or a marketplace API. Scores the
    offer across the five deal pillars (value, rights, flexibility, production_fit,
    market), averages them into a composite, and maps the composite to a
    recommendation of "accept" / "negotiate" / "pass". When no beat title is provided
    there is nothing to assess, so it returns a structured
    {"recommendation": "insufficient_material"} with a gaps list instead of
    fabricating a score. ``license_type`` is normalized to one of "lease" / "exclusive"
    (anything else is preserved verbatim) and ``price_usd`` is clamped to be
    non-negative. Returns a plain JSON-serializable dict. Pure — no I/O.
    """
    title = (beat_title or "").strip()
    ltype = (license_type or "").strip().lower()
    try:
        price = int(price_usd or 0)
    except (TypeError, ValueError):
        price = 0
    price = max(0, price)

    gaps = []
    if not title:
        gaps.append("missing_beat_title")

    if gaps:
        return {
            "beat_title": title,
            "license_type": ltype,
            "price_usd": price,
            "scores": {},
            "composite": 0.0,
            "gaps": gaps,
            "recommendation": "insufficient_material",
        }

    scores = _pillar_scores(f"{artist_id}:{title}:{ltype}:{price}")
    composite = round(sum(scores.values()) / len(scores), 1)
    if composite >= 7.5:
        recommendation = "accept"
    elif composite >= 5.5:
        recommendation = "negotiate"
    else:
        recommendation = "pass"

    return {
        "beat_title": title,
        "license_type": ltype,
        "price_usd": price,
        "scores": scores,
        "composite": composite,
        "gaps": gaps,
        "recommendation": recommendation,
    }


def _producer_network_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's production network / collab account.

    In production this would look up a stored network link for the artist. Here it is
    driven purely by the ``PRODUCER_NETWORK_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real secret.
    Values:
      - "expired"                     → raise ProducerNetworkAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("PRODUCER_NETWORK_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise ProducerNetworkAuthExpired("production network authorization expired")
    return val in ("1", "true", "yes", "connected")


async def log_collab_request(
    artist_id: str,
    producer_id: str,
    message: str = "",
    session_type: str = "",
) -> dict:
    """Log a collaboration/co-write request to a producer via the production network.

    Raises ProducerNetworkNotConnected / ProducerNetworkAuthExpired when no network is
    linked so the caller can surface a 'connect your production network' message
    instead of a hard failure. When the producer id is unknown, returns a structured
    {"status": "unknown_producer"} result rather than raising. On success returns a
    deterministic mock request reference — NO network call is ever made and no request
    is actually sent. ``session_type`` is preserved verbatim (e.g. "co-write",
    "beat lease", "full production").
    """
    if not _producer_network_connected(artist_id):
        raise ProducerNetworkNotConnected(
            "artist has not connected a production network / collab account"
        )
    producer = _get_producer(producer_id)
    if producer is None:
        return {"status": "unknown_producer", "producer_id": (producer_id or "").strip()}
    msg   = (message or "").strip()
    stype = (session_type or "").strip()
    digest = hashlib.sha1(
        f"{artist_id}:{producer['id']}:{msg}:{stype}".encode("utf-8")
    ).hexdigest()
    reference = "COLLAB-" + digest[:10].upper()
    return {
        "status": "sent",
        "reference": reference,
        "producer_id": producer["id"],
        "producer_name": producer["name"],
        "session_type": stype,
        "message": msg,
    }
