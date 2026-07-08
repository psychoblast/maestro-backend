"""
PLMKR Design-Studio — brand-design consult service (data-only).

Backs the Design-Studio (Diego — Brand Designer) agent's tool_use loop in
/api/chat_stream (see DESIGN_STUDIO_TOOLS in main.py). Diego is consult-only: search
the brand-identity styles an artist can build in (each carrying the asset type it
targets and its production tier), and draft a structured brand brief from a concept
and target asset type so the artist has something ready to hand a designer or a
model. The mock produce_brand_asset terminal-action tool (and its
DESIGN_STUDIO_ACCOUNT_CONNECTED gate) was retired — Diego never actually produced a
brand asset, so the tool implied a real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live design/render APIs, no asset-store APIs, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""


# ── Brand-identity style library (in-memory reference data) ────────────────────
# A curated set of brand-identity styles / design directions an artist can build
# their brand in. Each style carries the asset type it targets, its production tier
# (A = flagship, B = mid, C = quick/social), and the aesthetic it leans on, plus a
# preset key used when an asset is actually produced. Keyed loosely on asset type +
# tier so the agent can surface the right directions for a branding push. No I/O.
_STYLES = [
    {
        "id": "brd-monogram-serif",
        "name": "Monogram Serif",
        "asset_type": "logo",
        "tier": "A",
        "aesthetic": "classic",
        "preset": "monogram-serif-v2",
    },
    {
        "id": "brd-geometric-mark",
        "name": "Geometric Mark",
        "asset_type": "logo",
        "tier": "A",
        "aesthetic": "modern",
        "preset": "geometric-mark",
    },
    {
        "id": "brd-bold-wordmark",
        "name": "Bold Wordmark",
        "asset_type": "wordmark",
        "tier": "A",
        "aesthetic": "editorial",
        "preset": "bold-wordmark",
    },
    {
        "id": "brd-signature-script",
        "name": "Signature Script",
        "asset_type": "wordmark",
        "tier": "B",
        "aesthetic": "handwritten",
        "preset": "signature-script",
    },
    {
        "id": "brd-duotone-palette",
        "name": "Duotone Palette",
        "asset_type": "color_palette",
        "tier": "B",
        "aesthetic": "high-contrast",
        "preset": "duotone-palette",
    },
    {
        "id": "brd-grotesk-type",
        "name": "Grotesk Type System",
        "asset_type": "typography",
        "tier": "B",
        "aesthetic": "minimalist",
        "preset": "grotesk-type",
    },
    {
        "id": "brd-social-kit",
        "name": "Social Starter Kit",
        "asset_type": "social_kit",
        "tier": "C",
        "aesthetic": "playful",
        "preset": "social-starter-kit",
    },
]


async def search_brand_styles(asset_type: str = "", tier: str = "") -> dict:
    """Search brand-identity styles by the asset type they target and/or tier.

    Both filters are optional and matched case-insensitively as substrings.
    ``asset_type`` matches the style's asset type (e.g. "logo", "wordmark"), and
    ``tier`` matches the production tier (e.g. "A", "B", "C").
    Returns {"styles": [...], "count": int}. Pure — no I/O.
    """
    at = (asset_type or "").strip().lower()
    tr = (tier or "").strip().lower()
    matches = [
        dict(s)
        for s in _STYLES
        if (not at or at in s["asset_type"].lower())
        and (not tr or tr in s["tier"].lower())
    ]
    return {"styles": matches, "count": len(matches)}


def _get_style(style_id: str) -> dict | None:
    sid = (style_id or "").strip()
    for s in _STYLES:
        if s["id"] == sid:
            return s
    return None


async def draft_brand_brief(
    artist_id: str,
    concept: str = "",
    asset_type: str = "",
    tone: str = "",
) -> dict:
    """Draft a structured brand brief from a concept and target asset type.

    Deterministic draft — never contacts a design API. Assembles a concept line
    built from the concept and target asset type, an optional tone/voice note, and a
    deliverables section, then reports gaps and a recommendation of
    "produce" / "revise" / "blocked".
    Returns the structured brief with sections and a word count.
    """
    cn = (concept or "").strip()
    at = (asset_type or "").strip()
    tn = (tone or "").strip()

    gaps = []
    if not cn:
        gaps.append("missing_concept")
    if not at:
        gaps.append("missing_asset_type")

    sections = []
    if cn or at:
        if cn and at:
            lede = f"{cn} for {at}"
        else:
            lede = cn or at
        lede = lede.strip()
        if lede:
            sections.append({"label": "concept", "text": lede})
        if tn:
            sections.append({"label": "tone", "text": f"Tone: {tn}"})
        sections.append({
            "label": "deliverables",
            "text": "Deliver a primary mark plus light and dark lockups.",
        })

    word_count = sum(len(s["text"].split()) for s in sections)

    if "missing_concept" in gaps:
        # Without a concept there is nothing to design — the brief is unusable.
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
        "asset_type": at,
        "tone": tn,
        "sections": sections,
        "word_count": word_count,
        "recommendation": recommendation,
    }
