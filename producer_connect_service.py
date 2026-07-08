"""
PLMKR Producer-Connect — production consult service (data-only + pure evaluation).

Backs the Producer-Connect (Beat — Production) agent's tool_use loop in
/api/chat_stream (see PRODUCER_CONNECT_TOOLS in main.py). Beat is consult-only:
search a directory of producers/beatmakers worth connecting with (each carrying the
genre it works in, its region, a budget tier, and a typical session rate), and run a
structured evaluation of a beat-licensing offer that scores it across the five deal
pillars and returns an accept / negotiate / pass recommendation. The mock
log_collab_request terminal-action tool (and its PRODUCER_NETWORK_CONNECTED gate)
was retired — Beat never actually sent a collab request, so the tool implied a
real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live producer/CRM APIs, no streaming data, no LLM.
  - Deterministic: scores are derived from a stable hash of the inputs and no
    timestamps or random values leak into return payloads, so tests can assert
    on exact structure.
"""
import hashlib


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
