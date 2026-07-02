"""
PLMKR Signal-Blaster — publicist action service (mock-first).

Backs the Signal-Blaster (Zara — Publicist) agent's tool_use loop in
/api/chat_stream (see SIGNAL_BLASTER_TOOLS in main.py). Zara does not just advise on
press, media, and PR campaigns — these functions let the agent take real publicist
actions: search the media outlets / journalists an artist can pitch (each carrying
the beat it covers and its reach tier), draft a structured press release from a
headline and story angle so the artist has something ready to send, and send a
press pitch to a chosen outlet through the artist's connected press/email account
so the pitch actually goes out on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live media databases, no email/PR-wire APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_press_account_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring ledger_lock_service._ledger_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class PressAccountNotConnected(Exception):
    """Raised when the artist has not connected a press/email account.

    Mirrors ledger_lock_service.LedgerAccountNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class PressAccountAuthExpired(Exception):
    """Raised when a previously connected press/email-account authorization expired."""


# ── Media outlet library (in-memory reference data) ────────────────────────────
# A curated set of press outlets / journalists an artist can pitch. Each outlet
# carries the beat it covers (the kind of music/story it runs) and its reach tier
# (A = major, B = mid, C = local/niche), plus a contact address used when a pitch
# is actually sent. Keyed loosely on beat + tier so the agent can surface the right
# targets for a story. No I/O.
_OUTLETS = [
    {
        "id": "out-pitchfork",
        "name": "Pitchfork",
        "beat": "indie",
        "tier": "A",
        "region": "global",
        "contact_email": "tips@pitchfork.example",
    },
    {
        "id": "out-rolling-stone",
        "name": "Rolling Stone",
        "beat": "mainstream",
        "tier": "A",
        "region": "global",
        "contact_email": "music@rollingstone.example",
    },
    {
        "id": "out-the-fader",
        "name": "The FADER",
        "beat": "hiphop",
        "tier": "A",
        "region": "global",
        "contact_email": "editorial@thefader.example",
    },
    {
        "id": "out-stereogum",
        "name": "Stereogum",
        "beat": "indie",
        "tier": "B",
        "region": "global",
        "contact_email": "tips@stereogum.example",
    },
    {
        "id": "out-clash",
        "name": "Clash",
        "beat": "electronic",
        "tier": "B",
        "region": "uk",
        "contact_email": "news@clash.example",
    },
    {
        "id": "out-brooklyn-vegan",
        "name": "BrooklynVegan",
        "beat": "rock",
        "tier": "B",
        "region": "us",
        "contact_email": "tips@brooklynvegan.example",
    },
    {
        "id": "out-city-sound-zine",
        "name": "City Sound Zine",
        "beat": "local",
        "tier": "C",
        "region": "local",
        "contact_email": "hello@citysoundzine.example",
    },
]


async def search_media_outlets(beat: str = "", tier: str = "") -> dict:
    """Search media outlets by beat and/or reach tier.

    Both filters are optional and matched case-insensitively as substrings.
    ``beat`` matches the outlet's beat (e.g. "indie", "hiphop"), and ``tier``
    matches the reach tier (e.g. "A", "B", "C").
    Returns {"outlets": [...], "count": int}. Pure — no I/O.
    """
    bt = (beat or "").strip().lower()
    tr = (tier or "").strip().lower()
    matches = [
        dict(o)
        for o in _OUTLETS
        if (not bt or bt in o["beat"].lower())
        and (not tr or tr in o["tier"].lower())
    ]
    return {"outlets": matches, "count": len(matches)}


def _get_outlet(outlet_id: str) -> dict | None:
    oid = (outlet_id or "").strip()
    for o in _OUTLETS:
        if o["id"] == oid:
            return o
    return None


async def draft_press_release(
    artist_id: str,
    headline: str = "",
    angle: str = "",
    quote: str = "",
) -> dict:
    """Draft a structured press release from a headline and story angle.

    Deterministic draft — never contacts a wire. Assembles a headline, a lede built
    from the story angle, an optional artist quote, and a boilerplate section, then
    reports gaps and a recommendation of "publish" / "revise" / "blocked".
    Returns the structured draft with sections and a word count.
    """
    hl = (headline or "").strip()
    ag = (angle or "").strip()
    qt = (quote or "").strip()

    gaps = []
    if not hl:
        gaps.append("missing_headline")
    if not ag:
        gaps.append("missing_angle")

    sections = []
    if hl or ag:
        lede = f"{hl}. {ag}".strip(". ").strip()
        if lede:
            sections.append({"label": "lede", "text": lede})
        if qt:
            sections.append({"label": "quote", "text": f'"{qt}"'})
        sections.append({
            "label": "boilerplate",
            "text": "For press inquiries and interview requests, contact the artist's publicist.",
        })

    word_count = sum(len(s["text"].split()) for s in sections)

    if "missing_headline" in gaps:
        # Without a headline there is nothing to lead with — the draft is unusable.
        recommendation = "blocked"
    elif gaps:
        recommendation = "revise"
    else:
        recommendation = "publish"
    drafted = recommendation == "publish"

    return {
        "drafted": drafted,
        "gaps": gaps,
        "headline": hl,
        "angle": ag,
        "sections": sections,
        "word_count": word_count,
        "recommendation": recommendation,
    }


def _press_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's press/email account.

    In production this would look up a stored press/email-account link for the
    artist. Here it is driven purely by the ``SIGNAL_BLASTER_ACCOUNT_CONNECTED`` env
    flag so tests can toggle connected / expired / not-connected with ZERO network
    calls and NO real secret. Values:
      - "expired"                     → raise PressAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("SIGNAL_BLASTER_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise PressAccountAuthExpired("press-account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def send_press_pitch(
    artist_id: str,
    outlet_id: str,
    subject: str,
    body: str = "",
) -> dict:
    """Send a press pitch to a media outlet via the artist's connected account.

    Raises PressAccountNotConnected / PressAccountAuthExpired when no press/email
    account is linked so the caller can surface a 'connect your account' message
    instead of a hard failure. When the outlet id is unknown, returns a structured
    {"status": "unknown_outlet"} result rather than raising. On success returns a
    deterministic mock send reference — NO network call is ever made and nothing is
    actually sent.
    """
    if not _press_account_connected(artist_id):
        raise PressAccountNotConnected(
            "artist has not connected a press/email account"
        )
    outlet = _get_outlet(outlet_id)
    if outlet is None:
        return {"status": "unknown_outlet", "outlet_id": (outlet_id or "").strip()}
    subj = (subject or "").strip()
    digest = hashlib.sha1(
        f"{artist_id}:{outlet['id']}:{subj}".encode("utf-8")
    ).hexdigest()
    reference = "PITCH-" + digest[:10].upper()
    return {
        "status": "sent",
        "reference": reference,
        "outlet_id": outlet["id"],
        "outlet_name": outlet["name"],
        "to": outlet["contact_email"],
        "subject": subj,
    }
