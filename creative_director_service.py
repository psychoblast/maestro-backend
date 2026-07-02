"""
PLMKR Creative-Director — creative-direction action service (mock-first).

Backs the Creative-Director (Cree — Creative Director) agent's tool_use loop in
/api/chat_stream (see CREATIVE_DIRECTOR_TOOLS in main.py). Cree does not just
advise on aesthetics — these functions let the agent take real creative-direction
actions: search the library of proven release-rollout campaign templates (single,
EP, album) by release type and creative goal, assess how ready a specific creative
concept is against a chosen template's aesthetic, timing, and asset requirements,
and schedule that rollout on the artist's behalf through their connected creative
studio / content-calendar account.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live content calendars, no publishing tools, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_creative_studio_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring sync_agent_service._sync_catalogue_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class CreativeStudioNotConnected(Exception):
    """Raised when the artist has not connected a creative studio / content account.

    Mirrors sync_agent_service.SyncCatalogueNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your studio first'
    result instead of crashing the stream.
    """


class CreativeStudioAuthExpired(Exception):
    """Raised when a previously connected creative-studio authorization expired."""


# ── Rollout template library (in-memory reference data) ─────────────────────────
# A curated set of proven release-rollout campaign templates a creative director
# might reach for. Each template carries the release type (single / ep / album),
# the primary creative goal it serves, the aesthetic themes it suits, a
# recommended lead-time window (weeks before release), whether finished visual
# assets are required up front, and a headline phase count. The agent surfaces the
# right starting point for a project, then assesses a specific concept against a
# chosen template. No I/O.
_TEMPLATES = [
    {
        "id": "tpl-single-slow-burn",
        "title": "Single — Slow-Burn Teaser Rollout",
        "release_type": "single",
        "goal": "awareness",
        "themes": ["nostalgic", "intimate", "moody"],
        "lead_min": 3,
        "lead_max": 8,
        "visual_assets_required": False,
        "phases": 3,
    },
    {
        "id": "tpl-single-viral-hook",
        "title": "Single — Short-Form Viral Hook Push",
        "release_type": "single",
        "goal": "streams",
        "themes": ["bold", "playful", "energetic"],
        "lead_min": 2,
        "lead_max": 5,
        "visual_assets_required": True,
        "phases": 4,
    },
    {
        "id": "tpl-ep-story-arc",
        "title": "EP — Serialized Story-Arc Rollout",
        "release_type": "ep",
        "goal": "superfans",
        "themes": ["cinematic", "conceptual", "moody"],
        "lead_min": 6,
        "lead_max": 12,
        "visual_assets_required": True,
        "phases": 5,
    },
    {
        "id": "tpl-album-era-launch",
        "title": "Album — Full Era Launch Campaign",
        "release_type": "album",
        "goal": "press",
        "themes": ["bold", "cinematic", "conceptual"],
        "lead_min": 8,
        "lead_max": 16,
        "visual_assets_required": True,
        "phases": 6,
    },
    {
        "id": "tpl-album-intimate-reveal",
        "title": "Album — Intimate Direct-to-Fan Reveal",
        "release_type": "album",
        "goal": "superfans",
        "themes": ["intimate", "nostalgic", "acoustic"],
        "lead_min": 5,
        "lead_max": 10,
        "visual_assets_required": False,
        "phases": 4,
    },
    {
        "id": "tpl-single-brand-moment",
        "title": "Single — Brand / Cultural Moment Tie-In",
        "release_type": "single",
        "goal": "press",
        "themes": ["bold", "playful", "cinematic"],
        "lead_min": 4,
        "lead_max": 9,
        "visual_assets_required": True,
        "phases": 4,
    },
]


async def search_rollout_templates(release_type: str = "", goal: str = "") -> dict:
    """Search proven release-rollout templates by release type and/or creative goal.

    Both filters are optional and matched case-insensitively. ``release_type``
    matches the template's release type (e.g. "single", "ep", "album") as a
    substring; ``goal`` matches the template's primary creative goal (e.g.
    "awareness", "streams", "superfans", "press").
    Returns {"templates": [...], "count": int}. Pure — no I/O.
    """
    rt = (release_type or "").strip().lower()
    gl = (goal or "").strip().lower()
    matches = [
        dict(t)
        for t in _TEMPLATES
        if (not rt or rt in t["release_type"].lower())
        and (not gl or gl in t["goal"].lower())
    ]
    return {"templates": matches, "count": len(matches)}


def _get_template(template_id: str) -> dict | None:
    tid = (template_id or "").strip()
    for t in _TEMPLATES:
        if t["id"] == tid:
            return t
    return None


async def assess_creative_concept(
    artist_id: str,
    template_id: str = "",
    release_title: str = "",
    theme: str = "",
    weeks_to_release: float = 0,
    has_visual_assets: bool = False,
) -> dict:
    """Assess how ready a specific creative concept is against a chosen template.

    Deterministic readiness assessment — never contacts a wire. Looks the template
    up by id, then scores the concept against the template's aesthetic themes,
    recommended lead-time window, and visual-asset requirement. Each satisfied
    criterion adds to a readiness score out of 100. Returns a structured
    assessment with matched/missing criteria, the score, and a recommendation of
    "proceed" / "adjust" / "blocked".
    """
    template = _get_template(template_id)

    try:
        weeks = round(float(weeks_to_release or 0), 1)
    except (TypeError, ValueError):
        weeks = 0.0

    gaps = []
    if not (release_title or "").strip():
        gaps.append("missing_release_title")
    if not (template_id or "").strip():
        gaps.append("missing_template")
    elif template is None:
        gaps.append("unknown_template")

    matched = []
    missing = []
    score = 0
    if template is not None:
        th = (theme or "").strip().lower()
        if th and any(th in t.lower() or t.lower() in th for t in template["themes"]):
            matched.append("theme")
            score += 40
        else:
            missing.append("theme")

        if weeks > 0 and template["lead_min"] <= weeks <= template["lead_max"]:
            matched.append("timing")
            score += 35
        else:
            missing.append("timing")

        if not template["visual_assets_required"] or has_visual_assets:
            matched.append("visual_assets")
            score += 25
        else:
            missing.append("visual_assets")

    if "unknown_template" in gaps or "missing_template" in gaps:
        # Without a valid template target the concept cannot be assessed at all.
        recommendation = "blocked"
    elif gaps or score < 60:
        recommendation = "adjust"
    else:
        recommendation = "proceed"
    ready = recommendation == "proceed"

    return {
        "ready": ready,
        "gaps": gaps,
        "template_id": template["id"] if template else (template_id or "").strip(),
        "template_title": template["title"] if template else None,
        "release_title": (release_title or "").strip(),
        "score": score,
        "matched": matched,
        "missing": missing,
        "recommendation": recommendation,
    }


def _creative_studio_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's creative studio / content account.

    In production this would look up a stored creative-studio / content-calendar
    link for the artist. Here it is driven purely by the
    ``CREATIVE_DIRECTOR_STUDIO_CONNECTED`` env flag so tests can toggle connected /
    expired / not-connected with ZERO network calls and NO real secret. Values:
      - "expired"                     → raise CreativeStudioAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("CREATIVE_DIRECTOR_STUDIO_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise CreativeStudioAuthExpired("creative-studio authorization expired")
    return val in ("1", "true", "yes", "connected")


async def schedule_rollout(
    artist_id: str,
    template_id: str,
    release_title: str,
    kickoff: str = "",
) -> dict:
    """Schedule a release rollout for the artist against a chosen template.

    Raises CreativeStudioNotConnected / CreativeStudioAuthExpired when no creative
    studio is linked so the caller can surface a 'connect your studio' message
    instead of a hard failure. On success returns a deterministic mock rollout
    reference — NO network call is ever made and nothing is actually scheduled.
    """
    if not _creative_studio_connected(artist_id):
        raise CreativeStudioNotConnected(
            "artist has not connected a creative studio / content account"
        )
    tid   = (template_id or "").strip()
    title = (release_title or "").strip()
    kick  = (kickoff or "").strip()
    digest = hashlib.sha1(f"{artist_id}:{tid}:{title}".encode("utf-8")).hexdigest()
    reference = "ROLLOUT-" + digest[:10].upper()
    return {
        "status": "scheduled",
        "reference": reference,
        "template_id": tid,
        "release_title": title,
        "kickoff": kick,
    }
