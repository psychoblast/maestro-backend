"""
PLMKR Sync-Agent — sync-licensing action service (mock-first).

Backs the Sync-Agent (Sync — Sync Licensing) agent's tool_use loop in
/api/chat_stream (see SYNC_AGENT_TOOLS in main.py). Sync does not just advise on
placements — these functions let the agent take real sync-licensing actions:
search the open sync-opportunity briefs (TV, film, advertising, video games) that
music supervisors have posted, assess how well a specific track fits a brief's
creative and technical requirements, and submit a pitch of that track to the
supervisor on the artist's behalf out of their connected sync catalogue.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live sync marketplaces, no supervisor inboxes, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_sync_catalogue_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring vault_keeper_service._vault_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class SyncCatalogueNotConnected(Exception):
    """Raised when the artist has not connected a sync catalogue / rights account.

    Mirrors vault_keeper_service.VaultAccountNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your catalogue first'
    result instead of crashing the stream.
    """


class SyncCatalogueAuthExpired(Exception):
    """Raised when a previously connected sync-catalogue authorization expired."""


# ── Sync brief library (in-memory reference data) ──────────────────────────────
# A curated set of open sync-opportunity briefs a music supervisor might post.
# Each brief carries the placement medium (tv / film / ad / game), the genres the
# supervisor is hunting for, a target tempo window, whether an instrumental
# version is required, and a headline fee range. The agent surfaces the right
# starting point for an artist's catalogue, then assesses a specific track
# against a chosen brief. No I/O.
_BRIEFS = [
    {
        "id": "brief-tv-drama-indie",
        "title": "Prestige TV Drama — Emotional Montage",
        "medium": "tv",
        "genres": ["indie", "folk", "singer-songwriter"],
        "tempo_min": 60,
        "tempo_max": 100,
        "instrumental_required": False,
        "fee_low": 3000,
        "fee_high": 12000,
    },
    {
        "id": "brief-film-trailer-epic",
        "title": "Feature Film Trailer — Epic Build",
        "medium": "film",
        "genres": ["cinematic", "electronic", "rock"],
        "tempo_min": 90,
        "tempo_max": 140,
        "instrumental_required": True,
        "fee_low": 8000,
        "fee_high": 40000,
    },
    {
        "id": "brief-ad-national-pop",
        "title": "National Ad Campaign — Upbeat Pop Bed",
        "medium": "ad",
        "genres": ["pop", "electronic", "indie"],
        "tempo_min": 100,
        "tempo_max": 128,
        "instrumental_required": False,
        "fee_low": 15000,
        "fee_high": 75000,
    },
    {
        "id": "brief-ad-lifestyle-acoustic",
        "title": "Lifestyle Brand Ad — Warm Acoustic",
        "medium": "ad",
        "genres": ["folk", "acoustic", "singer-songwriter"],
        "tempo_min": 70,
        "tempo_max": 110,
        "instrumental_required": False,
        "fee_low": 5000,
        "fee_high": 25000,
    },
    {
        "id": "brief-game-action-electronic",
        "title": "AAA Game — Action Set-Piece",
        "medium": "game",
        "genres": ["electronic", "cinematic", "rock"],
        "tempo_min": 120,
        "tempo_max": 160,
        "instrumental_required": True,
        "fee_low": 4000,
        "fee_high": 20000,
    },
    {
        "id": "brief-tv-reality-pop",
        "title": "Reality TV — High-Energy Reveal",
        "medium": "tv",
        "genres": ["pop", "hip-hop", "electronic"],
        "tempo_min": 100,
        "tempo_max": 140,
        "instrumental_required": False,
        "fee_low": 1500,
        "fee_high": 6000,
    },
]


async def search_sync_briefs(medium: str = "", genre: str = "") -> dict:
    """Search open sync briefs by placement medium and/or genre.

    Both filters are optional and matched case-insensitively. ``medium`` matches
    the brief's placement medium (e.g. "tv", "film", "ad", "game") as a substring;
    ``genre`` matches when it appears in the brief's target genre list.
    Returns {"briefs": [...], "count": int}. Pure — no I/O.
    """
    md = (medium or "").strip().lower()
    gn = (genre or "").strip().lower()
    matches = [
        dict(b)
        for b in _BRIEFS
        if (not md or md in b["medium"].lower())
        and (not gn or any(gn in g.lower() for g in b["genres"]))
    ]
    return {"briefs": matches, "count": len(matches)}


def _get_brief(brief_id: str) -> dict | None:
    bid = (brief_id or "").strip()
    for b in _BRIEFS:
        if b["id"] == bid:
            return b
    return None


async def assess_track_sync_fit(
    artist_id: str,
    brief_id: str = "",
    track_title: str = "",
    genre: str = "",
    tempo_bpm: float = 0,
    has_instrumental: bool = False,
) -> dict:
    """Assess how well a specific track fits a chosen sync brief.

    Deterministic fit assessment — never contacts a wire. Looks the brief up by
    id, then scores the track against the brief's genre list, tempo window, and
    instrumental requirement. Each satisfied criterion adds to a fit score out of
    100. Returns a structured assessment with matched/missing criteria, the score,
    and a recommendation of "proceed" / "adjust" / "blocked".
    """
    brief = _get_brief(brief_id)

    try:
        tempo = round(float(tempo_bpm or 0), 1)
    except (TypeError, ValueError):
        tempo = 0.0

    gaps = []
    if not (track_title or "").strip():
        gaps.append("missing_track_title")
    if not (brief_id or "").strip():
        gaps.append("missing_brief")
    elif brief is None:
        gaps.append("unknown_brief")

    matched = []
    missing = []
    score = 0
    if brief is not None:
        gn = (genre or "").strip().lower()
        if gn and any(gn in g.lower() or g.lower() in gn for g in brief["genres"]):
            matched.append("genre")
            score += 40
        else:
            missing.append("genre")

        if tempo > 0 and brief["tempo_min"] <= tempo <= brief["tempo_max"]:
            matched.append("tempo")
            score += 35
        else:
            missing.append("tempo")

        if not brief["instrumental_required"] or has_instrumental:
            matched.append("instrumental")
            score += 25
        else:
            missing.append("instrumental")

    if "unknown_brief" in gaps or "missing_brief" in gaps:
        # Without a valid brief target the track cannot be assessed at all.
        recommendation = "blocked"
    elif gaps or score < 60:
        recommendation = "adjust"
    else:
        recommendation = "proceed"
    fit = recommendation == "proceed"

    return {
        "fit": fit,
        "gaps": gaps,
        "brief_id": brief["id"] if brief else (brief_id or "").strip(),
        "brief_title": brief["title"] if brief else None,
        "track_title": (track_title or "").strip(),
        "score": score,
        "matched": matched,
        "missing": missing,
        "recommendation": recommendation,
    }


def _sync_catalogue_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's sync catalogue / rights account.

    In production this would look up a stored sync-catalogue / rights link for the
    artist. Here it is driven purely by the ``SYNC_AGENT_CATALOGUE_CONNECTED`` env
    flag so tests can toggle connected / expired / not-connected with ZERO network
    calls and NO real secret. Values:
      - "expired"                     → raise SyncCatalogueAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("SYNC_AGENT_CATALOGUE_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise SyncCatalogueAuthExpired("sync-catalogue authorization expired")
    return val in ("1", "true", "yes", "connected")


async def submit_sync_pitch(
    artist_id: str,
    brief_id: str,
    track_title: str,
    note: str = "",
) -> dict:
    """Submit a pitch of a track to the music supervisor on a sync brief.

    Raises SyncCatalogueNotConnected / SyncCatalogueAuthExpired when no sync
    catalogue is linked so the caller can surface a 'connect your catalogue'
    message instead of a hard failure. On success returns a deterministic mock
    pitch reference — NO network call is ever made and no pitch actually leaves.
    """
    if not _sync_catalogue_connected(artist_id):
        raise SyncCatalogueNotConnected(
            "artist has not connected a sync catalogue / rights account"
        )
    bid   = (brief_id or "").strip()
    track = (track_title or "").strip()
    nte   = (note or "").strip()
    digest = hashlib.sha1(f"{artist_id}:{bid}:{track}".encode("utf-8")).hexdigest()
    reference = "SYNC-" + digest[:10].upper()
    return {
        "status": "submitted",
        "reference": reference,
        "brief_id": bid,
        "track_title": track,
        "note": nte,
    }
