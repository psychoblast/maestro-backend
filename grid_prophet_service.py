"""
PLMKR Grid-Prophet — digital-marketing action service (mock-first).

Backs the Grid-Prophet (Kai — Digital Marketing) agent's tool_use loop in
/api/chat_stream (see GRID_PROPHET_TOOLS in main.py). Kai does not just advise on
social media, digital growth, and algorithms — these functions let the agent take
real digital-marketing actions: search the growth channels an artist can run on
(each carrying the platform it lives on and its reach tier), draft a structured
content plan from a hook and target platform so the artist has something ready to
post, and schedule a post to a chosen channel through the artist's connected social
account so the post actually goes out on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live social APIs, no scheduler/ad APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_social_account_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring signal_blaster_service._press_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class SocialAccountNotConnected(Exception):
    """Raised when the artist has not connected a social/scheduler account.

    Mirrors signal_blaster_service.PressAccountNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class SocialAccountAuthExpired(Exception):
    """Raised when a previously connected social-account authorization expired."""


# ── Growth channel library (in-memory reference data) ──────────────────────────
# A curated set of growth channels an artist can run digital marketing on. Each
# channel carries the platform it lives on, its reach tier (A = major, B = mid,
# C = niche/community), and the content surface it uses (short_video, streaming
# algorithm, social feed, community), plus a handle used when a post is actually
# scheduled. Keyed loosely on platform + tier so the agent can surface the right
# channels for a growth push. No I/O.
_CHANNELS = [
    {
        "id": "ch-tiktok",
        "name": "TikTok",
        "platform": "tiktok",
        "tier": "A",
        "surface": "short_video",
        "handle": "@artist_tiktok",
    },
    {
        "id": "ch-reels",
        "name": "Instagram Reels",
        "platform": "instagram",
        "tier": "A",
        "surface": "short_video",
        "handle": "@artist_ig",
    },
    {
        "id": "ch-shorts",
        "name": "YouTube Shorts",
        "platform": "youtube",
        "tier": "A",
        "surface": "short_video",
        "handle": "@artist_yt",
    },
    {
        "id": "ch-spotify-algo",
        "name": "Spotify Algorithmic",
        "platform": "spotify",
        "tier": "A",
        "surface": "streaming_algo",
        "handle": "spotify:artist:demo",
    },
    {
        "id": "ch-x",
        "name": "X (Twitter)",
        "platform": "twitter",
        "tier": "B",
        "surface": "social_feed",
        "handle": "@artist_x",
    },
    {
        "id": "ch-threads",
        "name": "Threads",
        "platform": "instagram",
        "tier": "B",
        "surface": "social_feed",
        "handle": "@artist_threads",
    },
    {
        "id": "ch-discord",
        "name": "Discord Community",
        "platform": "discord",
        "tier": "C",
        "surface": "community",
        "handle": "artist-server",
    },
]


async def search_growth_channels(platform: str = "", tier: str = "") -> dict:
    """Search growth channels by platform and/or reach tier.

    Both filters are optional and matched case-insensitively as substrings.
    ``platform`` matches the channel's platform (e.g. "tiktok", "spotify"), and
    ``tier`` matches the reach tier (e.g. "A", "B", "C").
    Returns {"channels": [...], "count": int}. Pure — no I/O.
    """
    pf = (platform or "").strip().lower()
    tr = (tier or "").strip().lower()
    matches = [
        dict(c)
        for c in _CHANNELS
        if (not pf or pf in c["platform"].lower())
        and (not tr or tr in c["tier"].lower())
    ]
    return {"channels": matches, "count": len(matches)}


def _get_channel(channel_id: str) -> dict | None:
    cid = (channel_id or "").strip()
    for c in _CHANNELS:
        if c["id"] == cid:
            return c
    return None


async def draft_content_plan(
    artist_id: str,
    hook: str = "",
    platform: str = "",
    cadence: str = "",
) -> dict:
    """Draft a structured content plan from a hook and target platform.

    Deterministic draft — never contacts a social API. Assembles a hook line built
    from the hook and target platform, an optional posting cadence, and a
    call-to-action section, then reports gaps and a recommendation of
    "publish" / "revise" / "blocked".
    Returns the structured plan with sections and a word count.
    """
    hk = (hook or "").strip()
    pf = (platform or "").strip()
    cd = (cadence or "").strip()

    gaps = []
    if not hk:
        gaps.append("missing_hook")
    if not pf:
        gaps.append("missing_platform")

    sections = []
    if hk or pf:
        if hk and pf:
            lede = f"{hk} on {pf}"
        else:
            lede = hk or pf
        lede = lede.strip()
        if lede:
            sections.append({"label": "hook", "text": lede})
        if cd:
            sections.append({"label": "cadence", "text": f"Cadence: {cd}"})
        sections.append({
            "label": "cta",
            "text": "Follow for more and stream the latest release.",
        })

    word_count = sum(len(s["text"].split()) for s in sections)

    if "missing_hook" in gaps:
        # Without a hook there is nothing to open with — the plan is unusable.
        recommendation = "blocked"
    elif gaps:
        recommendation = "revise"
    else:
        recommendation = "publish"
    drafted = recommendation == "publish"

    return {
        "drafted": drafted,
        "gaps": gaps,
        "hook": hk,
        "platform": pf,
        "cadence": cd,
        "sections": sections,
        "word_count": word_count,
        "recommendation": recommendation,
    }


def _social_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's social/scheduler account.

    In production this would look up a stored social-account link for the artist.
    Here it is driven purely by the ``GRID_PROPHET_ACCOUNT_CONNECTED`` env flag so
    tests can toggle connected / expired / not-connected with ZERO network calls and
    NO real secret. Values:
      - "expired"                     → raise SocialAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("GRID_PROPHET_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise SocialAccountAuthExpired("social-account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def schedule_post(
    artist_id: str,
    channel_id: str,
    caption: str,
    body: str = "",
) -> dict:
    """Schedule a post to a growth channel via the artist's connected account.

    Raises SocialAccountNotConnected / SocialAccountAuthExpired when no social
    account is linked so the caller can surface a 'connect your account' message
    instead of a hard failure. When the channel id is unknown, returns a structured
    {"status": "unknown_channel"} result rather than raising. On success returns a
    deterministic mock schedule reference — NO network call is ever made and nothing
    is actually posted.
    """
    if not _social_account_connected(artist_id):
        raise SocialAccountNotConnected(
            "artist has not connected a social/scheduler account"
        )
    channel = _get_channel(channel_id)
    if channel is None:
        return {"status": "unknown_channel", "channel_id": (channel_id or "").strip()}
    cap = (caption or "").strip()
    digest = hashlib.sha1(
        f"{artist_id}:{channel['id']}:{cap}".encode("utf-8")
    ).hexdigest()
    reference = "POST-" + digest[:10].upper()
    return {
        "status": "scheduled",
        "reference": reference,
        "channel_id": channel["id"],
        "channel_name": channel["name"],
        "to": channel["handle"],
        "caption": cap,
    }
