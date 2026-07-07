"""
PLMKR Vision-Forge — AI-visuals consult service (data-only).

Backs the Vision-Forge (Luna — AI Visuals) agent's tool_use loop in
/api/chat_stream (see VISION_FORGE_TOOLS in main.py). Luna is consult-only: search
the visual styles an artist can work in (each carrying the medium it targets and its
production tier), and draft a structured art brief from a concept and target medium
so the artist has something ready to hand a designer or a model. The mock
generate_artwork terminal-action tool (and its VISION_FORGE_ACCOUNT_CONNECTED gate)
was retired — Luna never actually rendered artwork, so the tool implied a
real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live image/render APIs, no asset-store APIs, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""


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
