"""
PLMKR AI-Navigator — AI tooling consult service (data-only).

Backs the AI-Navigator (Neo, AI Tools) agent's tool_use loop in
/api/chat_stream (see AI_NAVIGATOR_TOOLS in main.py). Neo is consult-only: search a
catalog of AI tools and assess an artist's current tech stack for gaps. The mock
provision_automation terminal-action tool (and its AI_NAVIGATOR_CONNECTED gate) was
retired — Neo never actually provisioned an automation, so the tool implied a
real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM, no automation platform calls.
  - Deterministic: no timestamps or random values leak into return payloads.
"""


# ── AI tool catalog (in-memory reference data — no I/O) ───────────────────────
_TOOL_CATALOG = [
    {"id": "t-mastering", "category": "audio",     "use_case": "mastering",
     "name": "Auto-Master", "note": "One-click AI mastering for reference-loud masters."},
    {"id": "t-stems",     "category": "audio",     "use_case": "stem_separation",
     "name": "StemSplit", "note": "Isolate vocals/drums/bass from a stereo mix."},
    {"id": "t-art",       "category": "visual",    "use_case": "cover_art",
     "name": "CoverForge", "note": "Generate release artwork from a text brief."},
    {"id": "t-video",     "category": "visual",    "use_case": "music_video",
     "name": "ClipGen", "note": "Draft lyric/visualizer videos from audio."},
    {"id": "t-caption",   "category": "content",   "use_case": "social_copy",
     "name": "CaptionAI", "note": "Draft platform-specific captions and hooks."},
    {"id": "t-schedule",  "category": "workflow",  "use_case": "automation",
     "name": "FlowPilot", "note": "Automate posting, DMs, and release checklists."},
]


# ── Tech-stack gap heuristics (pure keyword screen) ───────────────────────────
# (capability keyword, human gap description, priority)
_STACK_CAPABILITIES = [
    ("mastering",  "No mastering pipeline — masters may be under-loud vs peers", "high"),
    ("analytics",  "No analytics tooling — flying blind on audience data",       "high"),
    ("automation", "Manual posting/admin — automate to reclaim studio time",     "medium"),
    ("artwork",    "No repeatable artwork workflow — inconsistent visual brand", "medium"),
    ("captions",   "Captions written ad hoc — no content system",                "low"),
]


async def search_ai_tools(category: str = "", use_case: str = "") -> dict:
    """Search the AI-tool catalog by category and/or use case.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"tools": [...], "count": int}. Pure — no I/O.
    """
    cat = (category or "").strip().lower()
    uc = (use_case or "").strip().lower()
    matches = [
        dict(t)
        for t in _TOOL_CATALOG
        if (not cat or cat in t["category"]) and (not uc or uc in t["use_case"])
    ]
    return {"tools": matches, "count": len(matches)}


async def assess_tech_stack(
    artist_id: str,
    current_tools: str = "",
    goal: str = "",
) -> dict:
    """Assess an artist's current tooling for gaps against common capabilities.

    Runs the pure ``_STACK_CAPABILITIES`` heuristics over the supplied
    description of what the artist already uses. A capability is a "gap" when its
    keyword is NOT present in ``current_tools``. Never contacts a wire.
    """
    have = (current_tools or "").lower()
    gaps = [
        {"gap": desc, "priority": priority, "capability": keyword}
        for keyword, desc, priority in _STACK_CAPABILITIES
        if keyword not in have
    ]
    has_high = any(g["priority"] == "high" for g in gaps)
    recommendation = "prioritize_high_gaps" if has_high else ("close_gaps" if gaps else "stack_healthy")
    return {
        "goal": goal or "unspecified",
        "gaps": gaps,
        "gap_count": len(gaps),
        "recommendation": recommendation,
    }
