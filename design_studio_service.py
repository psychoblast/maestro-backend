"""
PLMKR Design-Studio — brand-design action service (mock-first).

Backs the Design-Studio (Diego — Brand Designer) agent's tool_use loop in
/api/chat_stream (see DESIGN_STUDIO_TOOLS in main.py). Diego does not just advise on
branding, logos, and visual assets — these functions let the agent take real
brand-design actions: search the brand-identity styles an artist can build in (each
carrying the asset type it targets and its production tier), draft a structured
brand brief from a concept and target asset type so the artist has something ready
to hand a designer or a model, and produce a brand asset (logo / wordmark / kit) in
a chosen style through the artist's connected design workspace so a deliverable
actually gets made on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live design/render APIs, no asset-store APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_design_workspace_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring vision_forge_service._render_workspace_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class DesignWorkspaceNotConnected(Exception):
    """Raised when the artist has not connected a design/asset workspace.

    Mirrors vision_forge_service.RenderWorkspaceNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your workspace first'
    result instead of crashing the stream.
    """


class DesignWorkspaceAuthExpired(Exception):
    """Raised when a previously connected design-workspace authorization expired."""


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


def _design_workspace_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's design/asset workspace.

    In production this would look up a stored design/asset-workspace link for the
    artist. Here it is driven purely by the ``DESIGN_STUDIO_ACCOUNT_CONNECTED`` env
    flag so tests can toggle connected / expired / not-connected with ZERO network
    calls and NO real secret. Values:
      - "expired"                     → raise DesignWorkspaceAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("DESIGN_STUDIO_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise DesignWorkspaceAuthExpired("design-workspace authorization expired")
    return val in ("1", "true", "yes", "connected")


async def produce_brand_asset(
    artist_id: str,
    style_id: str,
    prompt: str,
    notes: str = "",
) -> dict:
    """Produce a brand asset in a chosen style via the artist's connected workspace.

    Raises DesignWorkspaceNotConnected / DesignWorkspaceAuthExpired when no
    design/asset workspace is linked so the caller can surface a 'connect your
    workspace' message instead of a hard failure. When the style id is unknown,
    returns a structured {"status": "unknown_style"} result rather than raising. On
    success returns a deterministic mock asset reference — NO network call is ever
    made and nothing is actually rendered or uploaded.
    """
    if not _design_workspace_connected(artist_id):
        raise DesignWorkspaceNotConnected(
            "artist has not connected a design/asset workspace"
        )
    style = _get_style(style_id)
    if style is None:
        return {"status": "unknown_style", "style_id": (style_id or "").strip()}
    pr = (prompt or "").strip()
    digest = hashlib.sha1(
        f"{artist_id}:{style['id']}:{pr}".encode("utf-8")
    ).hexdigest()
    reference = "BRD-" + digest[:10].upper()
    return {
        "status": "produced",
        "reference": reference,
        "style_id": style["id"],
        "style_name": style["name"],
        "asset_ref": f"asset://design-studio/{reference.lower()}.svg",
        "prompt": pr,
    }
