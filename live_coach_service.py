"""
PLMKR Coach — Performance Coach consult service (data-only).

Backs the live-coach (Coach, Performance Coach) agent's tool_use loop in /api/chat_stream
(see LIVE_COACH_TOOLS in main.py). Coach is consult-only: search_coaching_drills and
assess_stage_presence. The mock schedule_coaching_session terminal-action tool (and
its LIVE_COACH_CONNECTED gate) was retired — Coach never booked a real session, so
the tool implied a real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads.
"""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_LIVE_COACH_CATALOG = [
    {'id': 'cd-1', 'focus': 'vocals', 'level': 'beginner', 'name': 'Lip Trills', 'note': 'Warm up the voice without strain.'},
    {'id': 'cd-2', 'focus': 'stage_presence', 'level': 'intermediate', 'name': 'Eye-Line Map', 'note': 'Distribute focus across the room.'},
    {'id': 'cd-3', 'focus': 'breath', 'level': 'beginner', 'name': 'Diaphragm Support', 'note': 'Sustain notes without pushing.'},
    {'id': 'cd-4', 'focus': 'endurance', 'level': 'advanced', 'name': 'Full-Set Runthrough', 'note': 'Simulate a 60-minute set for stamina.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_LIVE_COACH_HEUR = [
    ('stares at floor', 'Low eye contact with the audience', 'high'),
    ('no movement', 'Static staging — no use of the space', 'medium'),
    ('out of breath', 'Breath control failing mid-set', 'high'),
    ('no banter', 'No audience connection between songs', 'medium'),
    ('pitchy', 'Pitch drifting under performance pressure', 'medium'),
]


async def search_coaching_drills(focus: str = "", level: str = "") -> dict:
    """Search the reference catalog by focus and/or level.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (focus or "").strip().lower()
    b = (level or "").strip().lower()
    matches = [
        dict(c)
        for c in _LIVE_COACH_CATALOG
        if (not a or a in c["focus"]) and (not b or b in c["level"])
    ]
    return {"items": matches, "count": len(matches)}


async def assess_stage_presence(artist_id: str, performance_notes: str = "", context: str = "") -> dict:
    """Screen performance_notes against known indicators.

    Runs the pure ``_LIVE_COACH_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (performance_notes or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _LIVE_COACH_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "focused_coaching" if has_high else ("refine_stagecraft" if findings else "stage_ready")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }
