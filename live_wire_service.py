"""
PLMKR Knox — Booking Agent action service (mock-first).

Backs the live-wire (Knox, Booking Agent) agent's tool_use loop in /api/chat_stream
(see LIVE_WIRE_TOOLS in main.py). Knox screens show offers for unfavourable terms.

NOTE (RAY-B build, July 2026): Knox's ``search_venues`` and ``submit_booking_hold``
were DUPLICATES of the venue-hawk (Ray B) booking tools. Per the Tommy-decided
step-0 resolution, Ray B OWNS booking — those two tools (and their fabricated
``_LIVE_WIRE_CATALOG``, the ``LIVE_WIRE_CONNECTED`` gate, and the
BookingAccount* exception classes) were REMOVED here. Knox keeps only its own,
non-duplicate ``assess_show_offer`` screen. See _audit/rayb_step0_collision_report.md.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads.
"""


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_LIVE_WIRE_HEUR = [
    ('no guarantee', 'No guaranteed fee — door-deal risk', 'high'),
    ('pay to play', 'Pay-to-play structure — decline', 'high'),
    ('no radius clause relief', 'Restrictive radius clause', 'medium'),
    ('artist covers backline', 'Artist bears backline costs', 'medium'),
    ('no hospitality', 'No hospitality or accommodation', 'low'),
]


async def assess_show_offer(artist_id: str, offer_text: str = "", context: str = "") -> dict:
    """Screen offer_text against known indicators.

    Runs the pure ``_LIVE_WIRE_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (offer_text or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _LIVE_WIRE_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "renegotiate" if has_high else ("clarify_terms" if findings else "solid_offer")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }
