"""
PLMKR Reel — Music Video consult service (data-only).

Backs the video-director (Reel, Music Video) agent's tool_use loop in /api/chat_stream
(see VIDEO_DIRECTOR_TOOLS in main.py). Reel is consult-only: search_directors and
estimate_video_budget. The mock book_video_shoot terminal-action tool (and its
VIDEO_DIRECTOR_CONNECTED gate) was retired — Reel never booked a real shoot, so the
tool implied a real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads.
"""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_VIDEO_DIRECTOR_CATALOG = [
    {'id': 'dir-1', 'style': 'narrative', 'budget_tier': 'mid', 'name': 'J. Okafor', 'note': 'Story-driven videos with strong casting.'},
    {'id': 'dir-2', 'style': 'performance', 'budget_tier': 'low', 'name': 'Kite', 'note': 'One-take performance pieces on a budget.'},
    {'id': 'dir-3', 'style': 'animation', 'budget_tier': 'mid', 'name': 'Studio Vela', 'note': '2D/3D animated music videos.'},
    {'id': 'dir-4', 'style': 'experimental', 'budget_tier': 'high', 'name': 'Mara Voss', 'note': 'Award-circuit experimental visuals.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_VIDEO_DIRECTOR_HEUR = [
    ('multiple locations', 'Multiple locations drive up cost and days', 'high'),
    ('vfx heavy', 'Heavy VFX inflates post budget', 'high'),
    ('large cast', 'Large cast raises talent and catering costs', 'medium'),
    ('night shoot', 'Night shoots add overtime and lighting', 'medium'),
    ('animals', 'Animals on set require handlers and permits', 'low'),
]


async def search_directors(style: str = "", budget_tier: str = "") -> dict:
    """Search the reference catalog by style and/or budget_tier.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (style or "").strip().lower()
    b = (budget_tier or "").strip().lower()
    matches = [
        dict(c)
        for c in _VIDEO_DIRECTOR_CATALOG
        if (not a or a in c["style"]) and (not b or b in c["budget_tier"])
    ]
    return {"items": matches, "count": len(matches)}


async def estimate_video_budget(artist_id: str, treatment_notes: str = "", context: str = "") -> dict:
    """Screen treatment_notes against known indicators.

    Runs the pure ``_VIDEO_DIRECTOR_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (treatment_notes or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _VIDEO_DIRECTOR_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "scope_down" if has_high else ("budget_carefully" if findings else "budget_realistic")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }
