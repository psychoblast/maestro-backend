"""
PLMKR Fan-Builder — fan-engagement action service (mock-first).

Backs the Fan-Builder (Aria — Fan Engagement) agent's tool_use loop in
/api/chat_stream (see FAN_BUILDER_TOOLS in main.py). Aria does not just advise on
community building — these functions let the agent take real fan-engagement
actions: look up a fan segment appropriate to the artist's goal (superfans,
engaged listeners, casual fans, lapsed fans, brand-new followers), build a
concrete multi-channel engagement campaign by applying that segment's recommended
channel mix to a target reach, and schedule a broadcast message to a segment of
fans out of the artist's connected fan-club / CRM account so the outreach
actually goes out on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live fan-CRM APIs, no email/SMS/Discord rails, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_fan_platform_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring vault_keeper_service._vault_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class FanPlatformNotConnected(Exception):
    """Raised when the artist has not connected a fan-club / CRM platform.

    Mirrors vault_keeper_service.VaultAccountNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your fan platform
    first' result instead of crashing the stream.
    """


class FanPlatformAuthExpired(Exception):
    """Raised when a previously connected fan-platform authorization expired."""


# ── Fan segment library (in-memory reference data) ─────────────────────────────
# A curated set of fan-engagement segments. Each segment carries a recommended
# channel mix with percentage-of-reach allocations that sum to 100, so the agent
# can build a concrete engagement campaign by applying the mix to a target reach.
# Keyed loosely on segment type / tier so the agent can surface the right starting
# point for an artist's community plan. No I/O.
_SEGMENTS = [
    {
        "id": "seg-superfans",
        "name": "Superfans",
        "segment_type": "superfans",
        "tier": "core",
        "channels": [
            {"name": "fan_club", "pct": 40},
            {"name": "sms", "pct": 30},
            {"name": "email", "pct": 20},
            {"name": "community_post", "pct": 10},
        ],
    },
    {
        "id": "seg-engaged",
        "name": "Engaged Listeners",
        "segment_type": "engaged",
        "tier": "core",
        "channels": [
            {"name": "email", "pct": 40},
            {"name": "community_post", "pct": 30},
            {"name": "sms", "pct": 20},
            {"name": "fan_club", "pct": 10},
        ],
    },
    {
        "id": "seg-casual",
        "name": "Casual Fans",
        "segment_type": "casual",
        "tier": "growth",
        "channels": [
            {"name": "email", "pct": 45},
            {"name": "social_dm", "pct": 35},
            {"name": "community_post", "pct": 20},
        ],
    },
    {
        "id": "seg-lapsed",
        "name": "Lapsed Fans",
        "segment_type": "lapsed",
        "tier": "winback",
        "channels": [
            {"name": "email", "pct": 55},
            {"name": "sms", "pct": 30},
            {"name": "social_dm", "pct": 15},
        ],
    },
    {
        "id": "seg-new-followers",
        "name": "New Followers",
        "segment_type": "new",
        "tier": "growth",
        "channels": [
            {"name": "welcome_email", "pct": 50},
            {"name": "community_post", "pct": 30},
            {"name": "social_dm", "pct": 20},
        ],
    },
]

# Broadcast channels the platform recognises on a scheduled fan broadcast.
_VALID_CHANNELS = (
    "fan_club", "sms", "email", "welcome_email", "community_post",
    "social_dm", "push", "other",
)


async def search_fan_segments(segment_type: str = "", tier: str = "") -> dict:
    """Search fan segments by segment type and/or tier.

    Both filters are optional and matched case-insensitively as substrings.
    ``segment_type`` matches the segment's type (e.g. "superfans", "lapsed"),
    and ``tier`` matches the segment tier (e.g. "core", "growth", "winback").
    Returns {"segments": [...], "count": int}. Pure — no I/O.
    """
    st = (segment_type or "").strip().lower()
    tr = (tier or "").strip().lower()
    matches = [
        dict(s)
        for s in _SEGMENTS
        if (not st or st in s["segment_type"].lower())
        and (not tr or tr in s["tier"].lower())
    ]
    return {"segments": matches, "count": len(matches)}


def _get_segment(segment_id: str) -> dict | None:
    sid = (segment_id or "").strip()
    for s in _SEGMENTS:
        if s["id"] == sid:
            return s
    return None


async def build_engagement_campaign(
    artist_id: str,
    segment_id: str = "",
    campaign_name: str = "",
    target_reach: int = 0,
) -> dict:
    """Build a concrete fan-engagement campaign by applying a segment's channel mix.

    Deterministic campaign construction — never contacts a wire. Looks the segment
    up by id, checks a campaign name and a positive target reach are present, and
    allocates the reach across the segment's channels per their percentages.
    Returns a structured campaign with channel touchpoints, total reach, and a
    recommendation of "launch" / "adjust" / "blocked".
    """
    segment = _get_segment(segment_id)

    try:
        reach = int(target_reach or 0)
    except (TypeError, ValueError):
        reach = 0

    gaps = []
    if not (campaign_name or "").strip():
        gaps.append("missing_campaign_name")
    if not (segment_id or "").strip():
        gaps.append("missing_segment")
    elif segment is None:
        gaps.append("unknown_segment")
    if reach <= 0:
        gaps.append("non_positive_reach")

    touchpoints = []
    total_reach = 0
    if segment is not None and reach > 0:
        for ch in segment["channels"]:
            count = int(reach * ch["pct"] / 100.0)
            touchpoints.append({
                "channel": ch["name"],
                "pct": ch["pct"],
                "reach": count,
            })
            total_reach += count

    if "unknown_segment" in gaps or "missing_segment" in gaps:
        # Without a valid segment target the campaign cannot be built at all.
        recommendation = "blocked"
    elif gaps:
        recommendation = "adjust"
    else:
        recommendation = "launch"
    viable = recommendation == "launch"

    return {
        "viable": viable,
        "gaps": gaps,
        "segment_id": segment["id"] if segment else (segment_id or "").strip(),
        "segment_name": segment["name"] if segment else None,
        "campaign_name": (campaign_name or "").strip(),
        "target_reach": reach,
        "touchpoints": touchpoints,
        "total_reach": total_reach,
        "recommendation": recommendation,
    }


def _fan_platform_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's fan-club / CRM platform.

    In production this would look up a stored fan-platform link for the artist.
    Here it is driven purely by the ``FAN_BUILDER_ACCOUNT_CONNECTED`` env flag so
    tests can toggle connected / expired / not-connected with ZERO network calls
    and NO real secret. Values:
      - "expired"                     → raise FanPlatformAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("FAN_BUILDER_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise FanPlatformAuthExpired("fan-platform authorization expired")
    return val in ("1", "true", "yes", "connected")


async def schedule_fan_broadcast(
    artist_id: str,
    channel: str,
    message: str,
    segment: str = "",
) -> dict:
    """Schedule a broadcast message to fans out of the artist's fan-club / CRM account.

    Raises FanPlatformNotConnected / FanPlatformAuthExpired when no fan platform is
    linked so the caller can surface a 'connect your fan platform' message instead
    of a hard failure. On success returns a deterministic mock broadcast reference
    — NO network call is ever made and no message actually goes out.
    """
    if not _fan_platform_connected(artist_id):
        raise FanPlatformNotConnected(
            "artist has not connected a fan-club / CRM platform"
        )
    ch = (channel or "").strip().lower()
    seg = (segment or "").strip().lower()
    msg = message or ""
    digest = hashlib.sha1(
        f"{artist_id}:{ch}:{seg}:{msg}".encode("utf-8")
    ).hexdigest()
    reference = "BCAST-" + digest[:10].upper()
    return {
        "status": "scheduled",
        "reference": reference,
        "channel": ch,
        "segment": seg,
    }
