"""
PLMKR Global-Scout — international-expansion consult service (data-only + pure math).

Backs the Global-Scout (Nova — International) agent's tool_use loop in
/api/chat_stream (see GLOBAL_SCOUT_TOOLS in main.py). Nova is consult-only: search
the world market directory for the territories where an artist's sound has real
traction (each carrying its region, market tier, streaming reach, the local
per-stream payout rate, and the local performing-rights org), and draft a concrete
market-entry plan by applying a market's economics to a genre and a marketing budget
so the artist has a numbers-backed expansion case. The mock
submit_distribution_registration terminal-action tool (and its
GLOBAL_SCOUT_ACCOUNT_CONNECTED gate) was retired — Nova never actually registered a
release, so the tool implied a real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live distribution/PRO APIs, no streaming rails, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""


# ── World market directory (in-memory reference data) ──────────────────────────
# A curated set of international markets an artist can pursue. Each market carries
# the region it sits in, its market tier (emerging / established / major), an
# addressable streaming-listener population, the average per-stream payout rate in
# that market (USD), the local performing-rights org an artist would register with,
# and the genres that have real traction there. The agent can surface the right
# territories for an expansion plan and apply a market's economics to a genre and
# budget to draft a real entry case. No I/O.
_MARKETS = [
    {
        "id": "mkt-mx",
        "name": "Mexico",
        "region": "Latin America",
        "market_tier": "emerging",
        "streaming_listeners": 40_000_000,
        "avg_stream_rate": 0.0021,
        "pro": "SACM",
        "genres": ["latin", "pop", "reggaeton", "indie"],
    },
    {
        "id": "mkt-br",
        "name": "Brazil",
        "region": "Latin America",
        "market_tier": "established",
        "streaming_listeners": 65_000_000,
        "avg_stream_rate": 0.0018,
        "pro": "ECAD",
        "genres": ["latin", "pop", "funk", "electronic"],
    },
    {
        "id": "mkt-de",
        "name": "Germany",
        "region": "Europe",
        "market_tier": "major",
        "streaming_listeners": 45_000_000,
        "avg_stream_rate": 0.0048,
        "pro": "GEMA",
        "genres": ["electronic", "techno", "pop", "indie", "rock"],
    },
    {
        "id": "mkt-uk",
        "name": "United Kingdom",
        "region": "Europe",
        "market_tier": "major",
        "streaming_listeners": 38_000_000,
        "avg_stream_rate": 0.0052,
        "pro": "PRS",
        "genres": ["indie", "pop", "rock", "electronic", "grime"],
    },
    {
        "id": "mkt-jp",
        "name": "Japan",
        "region": "Asia Pacific",
        "market_tier": "major",
        "streaming_listeners": 50_000_000,
        "avg_stream_rate": 0.0061,
        "pro": "JASRAC",
        "genres": ["pop", "city-pop", "rock", "electronic"],
    },
    {
        "id": "mkt-ng",
        "name": "Nigeria",
        "region": "Africa",
        "market_tier": "emerging",
        "streaming_listeners": 22_000_000,
        "avg_stream_rate": 0.0009,
        "pro": "MCSN",
        "genres": ["afrobeats", "pop", "hip-hop", "gospel"],
    },
]


async def search_markets(genre: str = "", region: str = "") -> dict:
    """Search the world market directory by genre traction and/or region.

    Both filters are optional and matched case-insensitively as substrings.
    ``genre`` matches any of a market's traction genres (e.g. "indie", "afrobeats"),
    and ``region`` matches the market's region (e.g. "Europe", "Latin America").
    Returns {"markets": [...], "count": int}. Pure — no I/O.
    """
    g  = (genre or "").strip().lower()
    rg = (region or "").strip().lower()
    matches = [
        dict(m)
        for m in _MARKETS
        if (not g or any(g in mg.lower() for mg in m["genres"]))
        and (not rg or rg in m["region"].lower())
    ]
    return {"markets": matches, "count": len(matches)}


def _get_market(market_id: str) -> dict | None:
    mid = (market_id or "").strip()
    for m in _MARKETS:
        if m["id"] == mid:
            return m
    return None


async def draft_market_entry_plan(
    artist_id: str,
    market_id: str = "",
    genre: str = "",
    marketing_budget: float = 0,
) -> dict:
    """Draft a concrete market-entry plan by applying a market's economics to a genre.

    Deterministic plan construction — never contacts a distributor or PRO API. Looks
    the market up by id, checks a target genre and a positive marketing budget are
    present, and estimates addressable reach (streaming listeners × an assumed 2%
    penetration), projected first-year streams (3 plays per reached listener) and the
    projected streaming revenue (streams × the market's per-stream rate). Returns a
    structured plan with line items, projected revenue, gaps, and a recommendation of
    "enter" / "revise" / "blocked".
    """
    market = _get_market(market_id)
    g = (genre or "").strip()

    try:
        budget = round(float(marketing_budget or 0), 2)
    except (TypeError, ValueError):
        budget = 0.0

    gaps = []
    if not (market_id or "").strip():
        gaps.append("missing_market")
    elif market is None:
        gaps.append("unknown_market")
    if not g:
        gaps.append("missing_genre")
    elif market is not None and not any(g.lower() in mg.lower() for mg in market["genres"]):
        gaps.append("genre_no_traction")
    if budget <= 0:
        gaps.append("non_positive_budget")

    line_items = []
    reachable_listeners = 0
    projected_streams = 0
    projected_revenue = 0.0
    if market is not None:
        reachable_listeners = int(market["streaming_listeners"] * 0.02)
        projected_streams = reachable_listeners * 3
        projected_revenue = round(projected_streams * market["avg_stream_rate"], 2)
        line_items.append({"label": "reachable_listeners", "amount": reachable_listeners})
        line_items.append({"label": "projected_streams", "amount": projected_streams})
        line_items.append({"label": "projected_revenue", "amount": projected_revenue})
        line_items.append({"label": "local_pro", "amount": market["pro"]})

    if "unknown_market" in gaps or "missing_market" in gaps:
        # Without a valid market target the plan cannot be built at all.
        recommendation = "blocked"
    elif gaps or projected_revenue <= 0:
        recommendation = "revise"
    else:
        recommendation = "enter"
    viable = recommendation == "enter"

    return {
        "viable": viable,
        "gaps": gaps,
        "market_id": market["id"] if market else (market_id or "").strip(),
        "market_name": market["name"] if market else None,
        "region": market["region"] if market else None,
        "market_tier": market["market_tier"] if market else None,
        "genre": g,
        "marketing_budget": budget,
        "reachable_listeners": reachable_listeners,
        "projected_streams": projected_streams,
        "projected_revenue": projected_revenue,
        "local_pro": market["pro"] if market else None,
        "line_items": line_items,
        "recommendation": recommendation,
    }
