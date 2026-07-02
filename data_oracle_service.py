"""
PLMKR Data-Oracle — analytics action service (mock-first).

Backs the Data-Oracle (Data — Analytics) agent's tool_use loop in
/api/chat_stream (see DATA_ORACLE_TOOLS in main.py). Data does not just describe
the numbers — these functions let the agent take real analytics actions: search
the catalogue of available streaming / audience datasets across the DSPs by
platform and metric, analyze how a specific streaming metric is trending against
its prior window, and schedule a recurring data export / digest to the artist's
connected data warehouse (or dashboard) on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live DSP APIs, no analytics warehouse, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_data_warehouse_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring creative_director_service._creative_studio_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class DataWarehouseNotConnected(Exception):
    """Raised when the artist has not connected a data warehouse / dashboard.

    Mirrors creative_director_service.CreativeStudioNotConnected: the tool loop
    catches this and degrades gracefully into a structured 'connect your
    warehouse first' result instead of crashing the stream.
    """


class DataWarehouseAuthExpired(Exception):
    """Raised when a previously connected data-warehouse authorization expired."""


# ── Dataset catalogue (in-memory reference data) ────────────────────────────────
# A curated set of streaming / audience-analytics datasets a data oracle might
# reach for across the major DSPs. Each dataset carries the platform it comes
# from, the primary metric it exposes, its reporting granularity, and the typical
# reporting latency in hours. The agent surfaces the right dataset for a question,
# then analyzes a specific metric's movement against its prior window. No I/O.
_DATASETS = [
    {
        "id": "ds-spotify-streams-daily",
        "title": "Spotify — Daily Streams",
        "platform": "spotify",
        "metric": "streams",
        "granularity": "daily",
        "latency_hours": 24,
    },
    {
        "id": "ds-spotify-listeners-monthly",
        "title": "Spotify — Monthly Listeners",
        "platform": "spotify",
        "metric": "listeners",
        "granularity": "monthly",
        "latency_hours": 48,
    },
    {
        "id": "ds-spotify-saves-daily",
        "title": "Spotify — Save Rate",
        "platform": "spotify",
        "metric": "saves",
        "granularity": "daily",
        "latency_hours": 24,
    },
    {
        "id": "ds-apple-plays-daily",
        "title": "Apple Music — Daily Plays",
        "platform": "apple_music",
        "metric": "streams",
        "granularity": "daily",
        "latency_hours": 36,
    },
    {
        "id": "ds-apple-shazams-daily",
        "title": "Apple Music — Shazam Discovery",
        "platform": "apple_music",
        "metric": "discovery",
        "granularity": "daily",
        "latency_hours": 24,
    },
    {
        "id": "ds-youtube-watchtime-daily",
        "title": "YouTube — Watch Time",
        "platform": "youtube",
        "metric": "watch_time",
        "granularity": "daily",
        "latency_hours": 24,
    },
    {
        "id": "ds-tiktok-sound-views-daily",
        "title": "TikTok — Sound Video Views",
        "platform": "tiktok",
        "metric": "video_views",
        "granularity": "daily",
        "latency_hours": 12,
    },
]


async def search_streaming_datasets(platform: str = "", metric: str = "") -> dict:
    """Search available streaming / audience datasets by platform and/or metric.

    Both filters are optional and matched case-insensitively. ``platform`` matches
    the dataset's DSP (e.g. "spotify", "apple_music", "youtube", "tiktok") as a
    substring; ``metric`` matches the dataset's primary metric (e.g. "streams",
    "listeners", "saves", "watch_time") as a substring.
    Returns {"datasets": [...], "count": int}. Pure — no I/O.
    """
    pf = (platform or "").strip().lower()
    mt = (metric or "").strip().lower()
    matches = [
        dict(d)
        for d in _DATASETS
        if (not pf or pf in d["platform"].lower())
        and (not mt or mt in d["metric"].lower())
    ]
    return {"datasets": matches, "count": len(matches)}


def _get_dataset(dataset_id: str) -> dict | None:
    did = (dataset_id or "").strip()
    for d in _DATASETS:
        if d["id"] == did:
            return d
    return None


async def analyze_streaming_metric(
    artist_id: str,
    dataset_id: str = "",
    current_value: float = 0,
    prior_value: float = 0,
    window_days: float = 0,
) -> dict:
    """Analyze how a specific streaming metric is trending vs. its prior window.

    Deterministic analysis — never contacts a wire. Looks the dataset up by id,
    then compares ``current_value`` against ``prior_value`` to derive a
    period-over-period growth percentage, classify the trend (up / flat / down /
    new), score momentum out of 100, and produce a recommendation of
    "scale" / "monitor" / "investigate" / "blocked".
    """
    dataset = _get_dataset(dataset_id)

    try:
        current = round(float(current_value or 0), 2)
    except (TypeError, ValueError):
        current = 0.0
    try:
        prior = round(float(prior_value or 0), 2)
    except (TypeError, ValueError):
        prior = 0.0
    try:
        window = round(float(window_days or 0), 1)
    except (TypeError, ValueError):
        window = 0.0

    gaps = []
    if not (dataset_id or "").strip():
        gaps.append("missing_dataset")
    elif dataset is None:
        gaps.append("unknown_dataset")

    growth_pct = None
    trend = "unknown"
    score = 0
    if dataset is not None:
        if prior > 0:
            growth_pct = round((current - prior) / prior * 100, 1)
            if growth_pct > 5:
                trend = "up"
                score = min(100, 60 + int(growth_pct))
            elif growth_pct < -5:
                trend = "down"
                score = max(0, 40 + int(growth_pct))
            else:
                trend = "flat"
                score = 50
        elif current > 0:
            trend = "new"
            score = 55
        else:
            trend = "flat"
            score = 50

    if "unknown_dataset" in gaps or "missing_dataset" in gaps:
        # Without a valid dataset target the metric cannot be analyzed at all.
        recommendation = "blocked"
    elif trend == "down":
        recommendation = "investigate"
    elif trend in ("up", "new"):
        recommendation = "scale"
    else:
        recommendation = "monitor"

    return {
        "gaps": gaps,
        "dataset_id": dataset["id"] if dataset else (dataset_id or "").strip(),
        "dataset_title": dataset["title"] if dataset else None,
        "current_value": current,
        "prior_value": prior,
        "window_days": window,
        "growth_pct": growth_pct,
        "trend": trend,
        "score": score,
        "recommendation": recommendation,
    }


def _data_warehouse_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's data warehouse / dashboard.

    In production this would look up a stored analytics-warehouse / dashboard link
    for the artist. Here it is driven purely by the
    ``DATA_ORACLE_WAREHOUSE_CONNECTED`` env flag so tests can toggle connected /
    expired / not-connected with ZERO network calls and NO real secret. Values:
      - "expired"                     → raise DataWarehouseAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("DATA_ORACLE_WAREHOUSE_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise DataWarehouseAuthExpired("data-warehouse authorization expired")
    return val in ("1", "true", "yes", "connected")


async def schedule_data_export(
    artist_id: str,
    dataset_id: str,
    destination: str = "",
    cadence: str = "",
) -> dict:
    """Schedule a recurring data export / digest for the artist against a dataset.

    Raises DataWarehouseNotConnected / DataWarehouseAuthExpired when no warehouse
    is linked so the caller can surface a 'connect your warehouse' message instead
    of a hard failure. On success returns a deterministic mock export reference —
    NO network call is ever made and nothing is actually exported.
    """
    if not _data_warehouse_connected(artist_id):
        raise DataWarehouseNotConnected(
            "artist has not connected a data warehouse / dashboard"
        )
    did  = (dataset_id or "").strip()
    dest = (destination or "").strip() or "dashboard"
    cad  = (cadence or "").strip() or "weekly"
    digest = hashlib.sha1(f"{artist_id}:{did}:{dest}:{cad}".encode("utf-8")).hexdigest()
    reference = "EXPORT-" + digest[:10].upper()
    return {
        "status": "scheduled",
        "reference": reference,
        "dataset_id": did,
        "destination": dest,
        "cadence": cad,
    }
