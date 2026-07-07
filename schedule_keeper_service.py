"""
PLMKR Cal — Scheduling consult service (data-only).

Backs the schedule-keeper (Cal, Scheduling) agent's tool_use loop in /api/chat_stream
(see SCHEDULE_KEEPER_TOOLS in main.py). Cal is consult-only: search_schedule_templates
and check_conflicts. The mock schedule_event terminal-action tool (and its
SCHEDULE_KEEPER_CONNECTED gate) was retired — Cal never wrote to a real calendar,
so the tool implied a real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads.
"""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_SCHEDULE_KEEPER_CATALOG = [
    {'id': 's-1', 'category': 'release', 'horizon': '8_weeks', 'name': 'Single Rollout', 'note': '8-week countdown checklist to release day.'},
    {'id': 's-2', 'category': 'tour', 'horizon': '12_weeks', 'name': 'Tour Advance', 'note': 'Advance milestones for a run of shows.'},
    {'id': 's-3', 'category': 'content', 'horizon': '4_weeks', 'name': 'Content Calendar', 'note': 'Monthly posting cadence template.'},
    {'id': 's-4', 'category': 'admin', 'horizon': 'quarterly', 'name': 'Royalty Review', 'note': 'Quarterly statement-review reminders.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_SCHEDULE_KEEPER_HEUR = [
    ('double booked', 'Two commitments overlap', 'high'),
    ('release on same day', 'Two releases clash on one date', 'high'),
    ('no travel time', 'No buffer for travel between events', 'medium'),
    ('back to back shows', 'No recovery day between shows', 'medium'),
    ('deadline overlap', 'Multiple deadlines land together', 'medium'),
]


async def search_schedule_templates(category: str = "", horizon: str = "") -> dict:
    """Search the reference catalog by category and/or horizon.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (category or "").strip().lower()
    b = (horizon or "").strip().lower()
    matches = [
        dict(c)
        for c in _SCHEDULE_KEEPER_CATALOG
        if (not a or a in c["category"]) and (not b or b in c["horizon"])
    ]
    return {"items": matches, "count": len(matches)}


async def check_conflicts(artist_id: str, schedule_text: str = "", context: str = "") -> dict:
    """Screen schedule_text against known indicators.

    Runs the pure ``_SCHEDULE_KEEPER_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (schedule_text or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _SCHEDULE_KEEPER_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "resolve_conflicts" if has_high else ("add_buffers" if findings else "clear")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }
