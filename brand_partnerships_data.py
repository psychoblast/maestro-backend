"""
PLMKR Nia — brand-partnerships doctrine corpus (data only).

A data-only sibling of grant_data.py / royalties_data.py / copy_data.py: the
structural anatomy of a brand / endorsement / sponsorship deal, the categories
brand deals come from, the outreach doctrine, and the section-honesty rules Nia
works under. It carries NO market rates, NO fee figures, and NO legal verdicts.

MOCK-FIRST / CORPUS CONTRACT (hard rules for this module):
  - Data only: no def / class / import / call anywhere. Pure literals.
  - JSON-serializable throughout; ``None`` for an unknown, paired with a
    "verify live" note — never a guessed value.
  - Free text is a NOTE (a convention to convey), never a hard rule the code
    branches on.
  - Compensation ``amounts`` are always ``None``: a rate is only ever the
    artist's own supplied figure, never invented or quoted here. This is
    enforced by a numeric scan in the tests (no currency amounts in source).
  - Deal evaluation is STRUCTURAL — it flags terms present/missing, never
    good/bad. Concrete agreements route to legal framing as a draft-for-review.
"""

# ── DEAL_TERMS — the structural anatomy of a brand deal (doctrine records, ─────
# stable ids). Each record names one term and what MUST be pinned down; none of
# them carries a rate. "typical" framing marks a common shape, never a rule.
DEAL_TERMS = (
    {
        "id": "deliverables",
        "note": ("Pin down EXACT counts, formats, platforms, and dates — e.g. "
                 "'three in-feed Reels plus two Stories on one platform, posted the "
                 "week of launch', never 'a few posts'. Vagueness here is where "
                 "disputes begin."),
        "must_be_explicit": ("count", "format", "platform", "date"),
    },
    {
        "id": "compensation",
        "models": ("flat", "per_post", "performance_hybrid"),
        "amounts": None,
        "amounts_note": ("market rates vary by reach, category, and usage and are "
                         "NEVER quoted here; only the artist's own supplied figures "
                         "are ever used."),
        "payment_trigger_and_timeline": ("must be explicit — what triggers payment "
                                         "(on post, on approval, net terms) and by "
                                         "when."),
    },
    {
        "id": "usage_rights",
        "baseline_note": ("a roughly one-year content license is a common baseline; "
                          "broader scope, longer term, or paid-media / whitelisting "
                          "usage pushes the fee up — a typical shape, not a rule."),
        "ownership_vs_license": ("who OWNS the content versus what LICENSE the brand "
                                 "gets must be explicit — they are different "
                                 "questions."),
    },
    {
        "id": "exclusivity",
        "dimensions": ("category_defined_narrowly", "duration", "geography", "platform"),
        "duration_note": ("a 30-90 day post-campaign exclusivity window is typical — "
                          "verify against the specific deal."),
        "pricing_note": ("broader exclusivity (wider category, longer term, more "
                         "territories) costs more."),
    },
    {
        "id": "approval_workflow",
        "revision_rounds_limited": True,
        "review_windows": ("48-72h review turnarounds are typical; cap the number of "
                           "revision rounds so approvals do not run forever."),
    },
    {
        "id": "disclosure",
        "mechanism": ("a paid-partnership label / #ad per the FTC (US) and the local "
                      "equivalent — Ad Standards and the Competition Bureau (CA), and "
                      "others by market."),
        "rule": ("per-country specifics = verify live; surfaced as the current "
                 "convention, never stated as legal advice."),
    },
    {
        "id": "termination_morals",
        "note": ("morality / termination clauses cut BOTH directions — the brand may "
                 "exit on artist conduct and the artist may exit on brand conduct. "
                 "Flag whether the clause is present and whether it is mutual; never "
                 "rewrite it."),
    },
)


# ── BRAND_CATEGORIES — a STRUCTURAL map of where brand deals come from. Not ────
# facts about any brand; just the category surface, with gated categories noted.
BRAND_CATEGORIES = (
    {"id": "fashion_apparel", "note": None},
    {"id": "beauty", "note": None},
    {"id": "food_beverage", "note": None},
    {"id": "alcohol",
     "note": "age-gated — audience-age and platform rules apply; verify live."},
    {"id": "tech_audio_gear", "note": None},
    {"id": "gaming", "note": None},
    {"id": "lifestyle_wellness", "note": None},
    {"id": "automotive", "note": None},
    {"id": "finance_fintech",
     "note": ("regulated category — financial-promotion rules may apply; verify "
              "live, never advise.")},
    {"id": "travel", "note": None},
    {"id": "local_business", "note": None},
)


# ── OUTREACH_DOCTRINE — how Nia reaches out. Personalized, evidence-led, and ────
# never inventing a rate. Materials live with the creative department.
OUTREACH_DOCTRINE = {
    "personalized_pitch_only": ("every pitch is personalized to the specific brand — "
                                "no blast templates."),
    "alignment_evidence": ("artist-brand fit is SHOWN with evidence (audience "
                           "overlap, prior organic mentions, shared values), not "
                           "merely asserted."),
    "materials_ref": ("EPK / one-sheet / media kit are produced by the creative "
                      "department — cross-reference those tools; Nia references "
                      "them, never regenerates them here."),
    "rates_never_invented": ("compensation is discussed ONLY from the artist's own "
                             "supplied figures — no market rate is ever invented or "
                             "quoted."),
    "follow_up_cadence_note": ("a light, spaced follow-up cadence is normal — "
                               "persistence without pestering; exact timing is a "
                               "judgment call, not a fixed rule."),
}


# ── HONESTY_RULES — the guardrails, with stable ids (id / statement / allowed / ─
# forbidden), mirroring the sibling corpora.
HONESTY_RULES = (
    {
        "id": "no_market_rates_ever",
        "statement": ("No market rate, fee range, or currency figure is ever invented "
                      "or quoted. Compensation is only ever the artist's own supplied "
                      "number."),
        "allowed": "Structuring a deal around a fee the artist supplied.",
        "forbidden": "Producing, estimating, or 'ballparking' any rate the artist did not supply.",
    },
    {
        "id": "deal_evaluation_is_structural",
        "statement": ("Deal evaluation flags which terms are present or missing and "
                      "whether each is explicit — it never renders a good/bad verdict. "
                      "A concrete agreement goes to the legal framing as a "
                      "draft-for-review."),
        "allowed": "Flagging that usage rights or exclusivity are undefined.",
        "forbidden": "Declaring a deal 'good', 'fair', or 'bad', or approving it as final.",
    },
    {
        "id": "disclosure_not_legal_advice",
        "statement": ("Disclosure mechanics (paid-partnership labels, #ad) are surfaced "
                      "as the current convention with a verify-live reminder — never as "
                      "legal advice; per-country specifics are always verify live."),
        "allowed": "Noting that a paid partnership must be disclosed per FTC / local rules.",
        "forbidden": "Stating a specific jurisdiction's legal requirement as settled advice.",
    },
    {
        "id": "facts_supplied_or_marked",
        "statement": ("Any fact a deal depends on — deliverables, dates, fees, rights — "
                      "is either the artist's supplied input or an explicit gap; nothing "
                      "is fabricated."),
        "allowed": "Marking an unknown as a [NEEDS:] gap or verify live.",
        "forbidden": "Filling an unknown deliverable, date, or fee with an invented value.",
    },
)
