"""
PLMKR Vision-Forge — AI-visuals action service (mock-first).

Backs the Vision-Forge (Luna — AI Visuals) agent's tool_use loop in
/api/chat_stream (see VISION_FORGE_TOOLS in main.py). Luna does not just advise on
artwork, visual identity, and art direction — these functions let the agent take
real visual-production actions: search the visual styles an artist can work in
(each carrying the medium it targets and its production tier), draft a structured
art brief from a concept and target medium so the artist has something ready to
hand a designer or a model, and generate artwork in a chosen style through the
artist's connected render/asset workspace so a piece actually gets produced on
their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live image/render APIs, no asset-store APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_render_workspace_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring grid_prophet_service._social_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class RenderWorkspaceNotConnected(Exception):
    """Raised when the artist has not connected a render/asset workspace.

    Mirrors grid_prophet_service.SocialAccountNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your workspace first'
    result instead of crashing the stream.
    """


class RenderWorkspaceAuthExpired(Exception):
    """Raised when a previously connected render-workspace authorization expired."""


# ── Visual style library (in-memory reference data) ────────────────────────────
# A curated set of visual styles / art directions an artist can produce work in.
# Each style carries the medium it targets, its production tier (A = flagship,
# B = mid, C = quick/social), and the aesthetic it leans on, plus a preset key used
# when a piece is actually generated. Keyed loosely on medium + tier so the agent
# can surface the right directions for a visual push. No I/O.
_STYLES = [
    {
        "id": "sty-neon-noir",
        "name": "Neon Noir",
        "medium": "cover_art",
        "tier": "A",
        "aesthetic": "cinematic",
        "preset": "neon-noir-v2",
    },
    {
        "id": "sty-analog-film",
        "name": "Analog Film",
        "medium": "cover_art",
        "tier": "A",
        "aesthetic": "vintage",
        "preset": "analog-film-35mm",
    },
    {
        "id": "sty-hyperpop-collage",
        "name": "Hyperpop Collage",
        "medium": "social",
        "tier": "A",
        "aesthetic": "maximalist",
        "preset": "hyperpop-collage",
    },
    {
        "id": "sty-minimal-type",
        "name": "Minimal Type",
        "medium": "poster",
        "tier": "B",
        "aesthetic": "minimalist",
        "preset": "minimal-type",
    },
    {
        "id": "sty-vapor-grid",
        "name": "Vaporwave Grid",
        "medium": "social",
        "tier": "B",
        "aesthetic": "retro",
        "preset": "vapor-grid",
    },
    {
        "id": "sty-hand-drawn",
        "name": "Hand-Drawn Ink",
        "medium": "merch",
        "tier": "B",
        "aesthetic": "illustrative",
        "preset": "hand-drawn-ink",
    },
    {
        "id": "sty-lofi-sketch",
        "name": "Lo-Fi Sketch",
        "medium": "lyric_video",
        "tier": "C",
        "aesthetic": "sketch",
        "preset": "lofi-sketch",
    },
]


async def search_visual_styles(medium: str = "", tier: str = "") -> dict:
    """Search visual styles by medium and/or production tier.

    Both filters are optional and matched case-insensitively as substrings.
    ``medium`` matches the style's medium (e.g. "cover_art", "poster"), and ``tier``
    matches the production tier (e.g. "A", "B", "C").
    Returns {"styles": [...], "count": int}. Pure — no I/O.
    """
    md = (medium or "").strip().lower()
    tr = (tier or "").strip().lower()
    matches = [
        dict(s)
        for s in _STYLES
        if (not md or md in s["medium"].lower())
        and (not tr or tr in s["tier"].lower())
    ]
    return {"styles": matches, "count": len(matches)}


def _get_style(style_id: str) -> dict | None:
    sid = (style_id or "").strip()
    for s in _STYLES:
        if s["id"] == sid:
            return s
    return None


async def draft_visual_brief(
    artist_id: str,
    concept: str = "",
    medium: str = "",
    palette: str = "",
) -> dict:
    """Draft a structured art brief from a concept and target medium.

    Deterministic draft — never contacts a render API. Assembles a concept line
    built from the concept and target medium, an optional colour palette, and a
    deliverables section, then reports gaps and a recommendation of
    "produce" / "revise" / "blocked".
    Returns the structured brief with sections and a word count.
    """
    cn = (concept or "").strip()
    md = (medium or "").strip()
    pl = (palette or "").strip()

    gaps = []
    if not cn:
        gaps.append("missing_concept")
    if not md:
        gaps.append("missing_medium")

    sections = []
    if cn or md:
        if cn and md:
            lede = f"{cn} for {md}"
        else:
            lede = cn or md
        lede = lede.strip()
        if lede:
            sections.append({"label": "concept", "text": lede})
        if pl:
            sections.append({"label": "palette", "text": f"Palette: {pl}"})
        sections.append({
            "label": "deliverables",
            "text": "Deliver a primary key art plus square and story crops.",
        })

    word_count = sum(len(s["text"].split()) for s in sections)

    if "missing_concept" in gaps:
        # Without a concept there is nothing to art-direct — the brief is unusable.
        recommendation = "blocked"
    elif gaps:
        recommendation = "revise"
    else:
        recommendation = "produce"
    drafted = recommendation == "produce"

    return {
        "drafted": drafted,
        "gaps": gaps,
        "concept": cn,
        "medium": md,
        "palette": pl,
        "sections": sections,
        "word_count": word_count,
        "recommendation": recommendation,
    }


def _render_workspace_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's render/asset workspace.

    In production this would look up a stored render/asset-workspace link for the
    artist. Here it is driven purely by the ``VISION_FORGE_ACCOUNT_CONNECTED`` env
    flag so tests can toggle connected / expired / not-connected with ZERO network
    calls and NO real secret. Values:
      - "expired"                     → raise RenderWorkspaceAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("VISION_FORGE_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise RenderWorkspaceAuthExpired("render-workspace authorization expired")
    return val in ("1", "true", "yes", "connected")


async def generate_artwork(
    artist_id: str,
    style_id: str,
    prompt: str,
    notes: str = "",
) -> dict:
    """Generate artwork in a chosen style via the artist's connected workspace.

    Raises RenderWorkspaceNotConnected / RenderWorkspaceAuthExpired when no
    render/asset workspace is linked so the caller can surface a 'connect your
    workspace' message instead of a hard failure. When the style id is unknown,
    returns a structured {"status": "unknown_style"} result rather than raising. On
    success returns a deterministic mock asset reference — NO network call is ever
    made and nothing is actually rendered or uploaded.
    """
    if not _render_workspace_connected(artist_id):
        raise RenderWorkspaceNotConnected(
            "artist has not connected a render/asset workspace"
        )
    style = _get_style(style_id)
    if style is None:
        return {"status": "unknown_style", "style_id": (style_id or "").strip()}
    pr = (prompt or "").strip()
    digest = hashlib.sha1(
        f"{artist_id}:{style['id']}:{pr}".encode("utf-8")
    ).hexdigest()
    reference = "ART-" + digest[:10].upper()
    return {
        "status": "generated",
        "reference": reference,
        "style_id": style["id"],
        "style_name": style["name"],
        "asset_ref": f"asset://vision-forge/{reference.lower()}.png",
        "prompt": pr,
    }
