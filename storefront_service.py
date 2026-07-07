"""
PLMKR Store — Fan Store consult service (data-only).

Backs the storefront (Store, Fan Store) agent's tool_use loop in /api/chat_stream
(see STOREFRONT_TOOLS in main.py). Store is consult-only: search_product_types and
assess_pricing. The mock publish_store_product terminal-action tool (and its
STOREFRONT_CONNECTED gate) was retired — Store never actually published a product,
so the tool implied a real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads.
"""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_STOREFRONT_CATALOG = [
    {'id': 'sp-1', 'category': 'music', 'format': 'digital', 'name': 'Deluxe Bundle', 'note': 'Album + stems + demos as a paid download.'},
    {'id': 'sp-2', 'category': 'merch', 'format': 'physical', 'name': 'Signed Vinyl', 'note': 'Limited signed pressing, numbered.'},
    {'id': 'sp-3', 'category': 'membership', 'format': 'subscription', 'name': 'Inner Circle', 'note': 'Monthly membership with exclusive drops.'},
    {'id': 'sp-4', 'category': 'experience', 'format': 'ticketed', 'name': 'Livestream Show', 'note': 'Ticketed streaming performance.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_STOREFRONT_HEUR = [
    ('below cost', 'Priced below unit cost — negative margin', 'high'),
    ('no shipping', 'Shipping not factored into price', 'high'),
    ('too cheap', 'Underpriced vs perceived value', 'medium'),
    ('no tiers', 'No pricing tiers to capture superfans', 'medium'),
    ('no scarcity', 'No limited edition to drive urgency', 'low'),
]


async def search_product_types(category: str = "", format: str = "") -> dict:
    """Search the reference catalog by category and/or format.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (category or "").strip().lower()
    b = (format or "").strip().lower()
    matches = [
        dict(c)
        for c in _STOREFRONT_CATALOG
        if (not a or a in c["category"]) and (not b or b in c["format"])
    ]
    return {"items": matches, "count": len(matches)}


async def assess_pricing(artist_id: str, pricing_notes: str = "", context: str = "") -> dict:
    """Screen pricing_notes against known indicators.

    Runs the pure ``_STOREFRONT_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (pricing_notes or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _STOREFRONT_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "reprice" if has_high else ("adjust_tiers" if findings else "priced_well")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }
