"""
PLMKR Maya — Wellness consult service (data-only).

Backs the artist-wellness (Maya, Wellness) agent's tool_use loop in /api/chat_stream
(see ARTIST_WELLNESS_TOOLS in main.py). Maya is consult-only: search_wellness_resources
and assess_burnout_risk. The mock schedule_wellness_checkin terminal-action tool
(and its ARTIST_WELLNESS_CONNECTED gate) was retired — Maya never actually booked a
check-in, so the tool implied a real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads.
"""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_ARTIST_WELLNESS_CATALOG = [
    {'id': 'w-breath', 'category': 'mindfulness', 'format': 'audio', 'name': 'Box-Breathing Reset', 'note': 'Five-minute pre-show breathing routine.'},
    {'id': 'w-sleep', 'category': 'recovery', 'format': 'guide', 'name': 'Tour Sleep Protocol', 'note': 'Circadian plan for cross-timezone touring.'},
    {'id': 'w-move', 'category': 'physical', 'format': 'video', 'name': 'Green-Room Mobility', 'note': 'Ten-minute movement to counter travel stiffness.'},
    {'id': 'w-noboundary', 'category': 'boundaries', 'format': 'guide', 'name': 'Say-No Scripts', 'note': 'Templates to decline overcommitment without guilt.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_ARTIST_WELLNESS_HEUR = [
    ('exhausted', 'Persistent exhaustion despite rest', 'high'),
    ('no days off', 'No recovery days scheduled', 'high'),
    ('dread', 'Dreading performances or sessions', 'high'),
    ('skipping meals', 'Basic self-care slipping', 'medium'),
    ('cynical', 'Growing cynicism about the work', 'medium'),
]


async def search_wellness_resources(category: str = "", format: str = "") -> dict:
    """Search the reference catalog by category and/or format.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (category or "").strip().lower()
    b = (format or "").strip().lower()
    matches = [
        dict(c)
        for c in _ARTIST_WELLNESS_CATALOG
        if (not a or a in c["category"]) and (not b or b in c["format"])
    ]
    return {"items": matches, "count": len(matches)}


async def assess_burnout_risk(artist_id: str, signals: str = "", context: str = "") -> dict:
    """Screen signals against known indicators.

    Runs the pure ``_ARTIST_WELLNESS_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (signals or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _ARTIST_WELLNESS_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "seek_support" if has_high else ("add_recovery" if findings else "sustainable")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }
