"""
PLMKR Collab — Networking consult service (data-only).

Backs the collab-connect (Collab, Networking) agent's tool_use loop in /api/chat_stream
(see COLLAB_CONNECT_TOOLS in main.py). Collab is consult-only: search_collaborators
and assess_collab_fit. The mock send_collab_invite terminal-action tool (and its
COLLAB_CONNECT_CONNECTED gate) was retired — Collab never sent a real invite, so the
tool implied a real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads.
"""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_COLLAB_CONNECT_CATALOG = [
    {'id': 'c-1', 'genre': 'pop', 'role': 'topliner', 'name': 'Ava Reed', 'note': 'Toplines with a strong hook sensibility.'},
    {'id': 'c-2', 'genre': 'hip_hop', 'role': 'producer', 'name': 'Marz', 'note': 'Boom-bap and trap hybrid production.'},
    {'id': 'c-3', 'genre': 'electronic', 'role': 'vocalist', 'name': 'Nyx', 'note': 'Ethereal vocals for dance records.'},
    {'id': 'c-4', 'genre': 'rnb', 'role': 'songwriter', 'name': 'Solae', 'note': 'Emotive R&B songwriting.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_COLLAB_CONNECT_HEUR = [
    ('no credits', 'No verifiable credits — vet before committing', 'high'),
    ('unclear splits', 'Split expectations unclear up front', 'high'),
    ('different genre', "Genre mismatch with the artist's lane", 'medium'),
    ('timezone', 'Timezone gap may slow the process', 'low'),
    ('no contract', 'No agreement in place yet', 'medium'),
]


async def search_collaborators(genre: str = "", role: str = "") -> dict:
    """Search the reference catalog by genre and/or role.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (genre or "").strip().lower()
    b = (role or "").strip().lower()
    matches = [
        dict(c)
        for c in _COLLAB_CONNECT_CATALOG
        if (not a or a in c["genre"]) and (not b or b in c["role"])
    ]
    return {"items": matches, "count": len(matches)}


async def assess_collab_fit(artist_id: str, collaborator_profile: str = "", context: str = "") -> dict:
    """Screen collaborator_profile against known indicators.

    Runs the pure ``_COLLAB_CONNECT_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (collaborator_profile or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _COLLAB_CONNECT_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "proceed_with_caution" if has_high else ("align_terms_first" if findings else "strong_fit")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }
