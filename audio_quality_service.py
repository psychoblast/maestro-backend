"""
PLMKR Audio — Quality Control consult service (data-only).

Backs the audio-quality (Audio, Quality Control) agent's tool_use loop in /api/chat_stream
(see AUDIO_QUALITY_TOOLS in main.py). Audio is consult-only: search_quality_standards
and analyze_mix. The mock submit_master_qc terminal-action tool (and its
AUDIO_QUALITY_CONNECTED gate) was retired — Audio never submitted a real master, so
the tool implied a real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads.
"""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_AUDIO_QUALITY_CATALOG = [
    {'id': 'q-spot', 'platform': 'spotify', 'stage': 'master', 'name': 'Spotify Loudness', 'note': 'Target -14 LUFS integrated; -1 dBTP ceiling.'},
    {'id': 'q-apple', 'platform': 'apple_music', 'stage': 'master', 'name': 'Apple Sound Check', 'note': 'Target -16 LUFS; preserve dynamics.'},
    {'id': 'q-yt', 'platform': 'youtube', 'stage': 'master', 'name': 'YouTube Normalization', 'note': 'Normalizes to ~-14 LUFS; avoid over-limiting.'},
    {'id': 'q-mix', 'platform': 'spotify', 'stage': 'mix', 'name': 'Pre-Master Headroom', 'note': 'Leave -6 dB headroom before mastering.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_AUDIO_QUALITY_HEUR = [
    ('clipping', 'Digital clipping — reduce gain before the ceiling', 'high'),
    ('muddy', 'Low-mid buildup masking clarity', 'high'),
    ('harsh', 'Harsh high-mids — tame 2-5 kHz', 'medium'),
    ('no low end', 'Thin low end — check sub balance', 'medium'),
    ('mono', 'Narrow image — check stereo width', 'low'),
]


async def search_quality_standards(platform: str = "", stage: str = "") -> dict:
    """Search the reference catalog by platform and/or stage.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (platform or "").strip().lower()
    b = (stage or "").strip().lower()
    matches = [
        dict(c)
        for c in _AUDIO_QUALITY_CATALOG
        if (not a or a in c["platform"]) and (not b or b in c["stage"])
    ]
    return {"items": matches, "count": len(matches)}


async def analyze_mix(artist_id: str, mix_notes: str = "", context: str = "") -> dict:
    """Screen mix_notes against known indicators.

    Runs the pure ``_AUDIO_QUALITY_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (mix_notes or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _AUDIO_QUALITY_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "remix_required" if has_high else ("targeted_fixes" if findings else "master_ready")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }
