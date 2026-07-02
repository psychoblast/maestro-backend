"""
PLMKR AI-Navigator — AI tooling action service (mock-first).

Backs the AI-Navigator (Neo, AI Tools) agent's tool_use loop in
/api/chat_stream (see AI_NAVIGATOR_TOOLS in main.py). Neo does not just advise —
these functions let the agent take real action: search a catalog of AI tools,
assess an artist's current tech stack for gaps, and provision an automation
workflow on the artist's connected automation account.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM, no automation platform calls.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_automation_connected``) driven by an env flag so tests
    can toggle the connected / not-connected / expired states deterministically
    — mirroring lex_cipher_service.RegistryNotConnected without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads.
"""
import hashlib
import os


class AutomationNotConnected(Exception):
    """Raised when the artist has not connected an automation account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class AutomationAuthExpired(Exception):
    """Raised when a previously connected automation account's auth expired."""


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


def _automation_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's automation account.

    Driven purely by the ``AI_NAVIGATOR_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise AutomationAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("AI_NAVIGATOR_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise AutomationAuthExpired("automation account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def provision_automation(
    artist_id: str,
    workflow_name: str,
    platform: str = "zapier",
) -> dict:
    """Provision an automation workflow on the artist's automation account.

    Raises AutomationNotConnected / AutomationAuthExpired when no account is
    linked so the caller can surface a 'connect your account' message instead of
    a hard failure. On success returns a deterministic mock reference — NO
    network call is ever made.
    """
    if not _automation_connected(artist_id):
        raise AutomationNotConnected("artist has not connected an automation account")
    name = (workflow_name or "").strip()
    plat = (platform or "zapier").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{plat}".encode("utf-8")).hexdigest()
    reference = "AUTO-" + digest[:10].upper()
    return {
        "status": "provisioned",
        "reference": reference,
        "workflow_name": name,
        "platform": plat,
    }
