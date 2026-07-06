"""
PLMKR Ray B — booking / live-touring doctrine corpus (data only).

A data-only sibling of grant_data.py / brand_partnerships_data.py: the mechanism
anatomy of live booking — the hold/challenge/confirm system, the deal STRUCTURES
(never their numbers), the deal-memo and rider minimum specs, the outreach and
routing doctrine, agent economics, and the department boundaries Ray B works
inside. Source map: RAY_B_BOOKING_MAP_v1 (researched in chat, July 6 2026,
web-sourced).

MOCK-FIRST / CORPUS CONTRACT (hard rules for this module):
  - Data only: no def / class / import / call anywhere. Pure literals.
  - JSON-serializable throughout; ``None`` for an unknown, paired with a
    "verify live" note — never a guessed value.
  - Free text is a NOTE (a convention to convey), never a hard rule the code
    branches on.
  - ZERO currency amounts anywhere. No rate tables (the Nadia-withholding
    precedent): deal splits, guarantees, and commissions are NEGOTIATED — the
    MECHANISM is encoded, and any figure appears only as a "varies, negotiated"
    note, never as a number. A numeric scan in the tests enforces this.
  - Deal evaluation is STRUCTURAL — it flags which terms are pinned or missing,
    never good/bad. Concrete agreements route to legal framing as a
    draft-for-review.
"""

# ── HOLD_SYSTEM — the hold / challenge / confirm mechanism. ─────────────────────
# How touring dates are held before they are confirmed. Numbers appear only as
# "commonly ~N days" NOTES — no window is a rule; every venue runs its own.
HOLD_SYSTEM = {
    "id": "hold_system",
    "distribution": ("holds are distributed first-come, first-served; competing "
                     "requests queue behind the 1st hold as 2nd, 3rd holds — the "
                     "queued ones are called 'pencils'."),
    "hold_order": ("first", "second", "third"),
    "pencil_note": ("a 'pencil' is a soft/queued hold below the 1st; a 'firm' "
                    "pencil signals stronger intent — terminology varies by venue."),
    "challenge": ("when a lower hold wants to confirm, the venue offers the date "
                  "UP the chain in hold order: the 1st hold is asked to confirm or "
                  "release before the challenger can take it."),
    "challenge_response_window": ("a challenged hold is commonly given ~24-48h to "
                                  "confirm or release — NOTE: varies by venue, not "
                                  "a standard; verify with the specific venue."),
    "unchallenged_window": ("an unchallenged 1st hold commonly runs ~14 days; 2nd "
                            "holds are typically shorter — NOTE: varies, no official "
                            "standard exists."),
    "scope_doctrine": ("the hold system is used mainly by mid-to-large venues "
                       "booking touring acts; small bars and restaurants generally "
                       "do NOT use it — never assume a venue speaks hold-language "
                       "until confirmed."),
}


# ── DEAL_MECHANISMS — the STRUCTURES a live deal can take (no numbers). ─────────
# Each record names ONE structure and how it pays out in words. No guarantee,
# split percentage, or fee figure is ever encoded — those are negotiated.
DEAL_MECHANISMS = {
    "id": "deal_mechanisms",
    "structures": (
        {
            "id": "flat_guarantee",
            "note": ("the act is paid a fixed, negotiated fee regardless of ticket "
                     "sales; the figure varies and is negotiated, never quoted here."),
        },
        {
            "id": "door_split",
            "note": ("the act takes a straight negotiated percentage of the door / "
                     "ticket revenue; the split percentage varies, negotiated."),
        },
        {
            "id": "versus_deal",
            "note": ("the act is paid the GREATER OF a guarantee or a percentage of "
                     "the gross ('guarantee versus percentage'); both figures vary, "
                     "negotiated."),
        },
        {
            "id": "guarantee_plus_bonus",
            "note": ("a guarantee plus a bonus that triggers at negotiated "
                     "ticket-count milestones; amounts and milestones vary, "
                     "negotiated."),
        },
        {
            "id": "guarantee_plus_percentage_after_split_point",
            "note": ("a guarantee, then a percentage to the act once revenue passes "
                     "a defined split point — expenses (and optionally a promoter "
                     "profit) are deducted BEFORE the percentage applies; all "
                     "figures vary, negotiated."),
        },
    ),
    "net_definition_doctrine": ("HARD DOCTRINE: a 'percentage of net' with no WRITTEN "
                                "definition of net is a settlement dispute waiting to "
                                "happen. The gross-vs-net definition — which taxes, "
                                "facility fees, ticketing fees, and which expenses are "
                                "deducted — MUST be pinned in the deal memo before the "
                                "structure means anything."),
    "red_flags": (
        {"id": "pay_to_play",
         "note": ("pay-to-play (the act pays the venue / buys tickets to perform) is "
                  "a red flag and is never recommended.")},
        {"id": "merch_hall_fee",
         "note": ("a merch hall fee (a cut of merch sales taken by the room) exists "
                  "at larger venues and is SOMETIMES negotiable — flag it, never "
                  "assume it is fixed; verify live.")},
    ),
}


# ── DEAL_MEMO_SPEC — the minimum fields a deal memo must pin down. ──────────────
# Structural checklist. Presence/absence is what Ray B flags — never a verdict.
DEAL_MEMO_SPEC = {
    "id": "deal_memo",
    "minimum_fields": (
        "artist_legal_and_performing_name",
        "date_venue_city",
        "fee_structure_with_all_terms_defined",
        "nbor_gbor_definition_with_specific_deductions",
        "production_rider_reference",
        "radius_clause_terms",
        "deposit_amount_and_payment_schedule",
        "cancellation_and_force_majeure",
    ),
    "field_notes": {
        "fee_structure_with_all_terms_defined": ("every term in the chosen "
                                                 "DEAL_MECHANISMS structure must be "
                                                 "defined in words — no undefined "
                                                 "'net'."),
        "nbor_gbor_definition_with_specific_deductions": ("Net/Gross Box Office "
                                                          "Receipts must name the "
                                                          "SPECIFIC deductions; "
                                                          "'NBOR'/'GBOR' as a bare "
                                                          "label is not a definition."),
        "radius_clause_terms": ("the geographic distance AND the period before/after "
                                "the show — check this BEFORE stacking regional "
                                "dates, or a radius clause can void a nearby booking."),
        "deposit_amount_and_payment_schedule": ("amount varies, negotiated — encoded "
                                                "only as a field to pin, never a "
                                                "number."),
    },
}


# ── RIDER_SPEC — hospitality vs technical rider anatomy. ────────────────────────
RIDER_SPEC = {
    "id": "rider",
    "hospitality_rider": ("green room; meals or a buy-out; a runner; comps / guest "
                          "list; accommodations; security."),
    "technical_rider": ("stage plot; input / output list; lighting; backline; crew."),
    "backline_note": ("backline (shared/provided instruments and amps) is common at "
                      "festivals with tight changeovers and on international dates; "
                      "confirm what is provided vs carried — never assume."),
}


# ── OUTREACH_DOCTRINE — how Ray B reaches venues, and routing. ──────────────────
# Timing appears only as "~N months/weeks" NOTES; nothing here is a rule.
OUTREACH_DOCTRINE = {
    "id": "outreach",
    "cold_start": ("cold outreach can start ~6 months out; batch regionally so the "
                   "ask matches a routing plan."),
    "email_style": ("emails are short and pertinent — the ask, the act, the routing "
                    "window, the avails. NO bio, NO persuasive essay."),
    "follow_up_cadence": ("follow up ~1 month after a cold send, then weekly inside "
                          "the final ~2-month window — always AFTER checking the "
                          "venue's public calendar first."),
    "routing_doctrine": ("dates must loop geographically — a route that backtracks "
                         "burns days and money; batch a region into one run."),
    "avails_term": ("'avails' = asking a venue which nights are free / available in "
                    "a window."),
}


# ── AGENT_ECONOMICS — booking-agent economics, every entry a NOTE not a rule. ───
AGENT_ECONOMICS = {
    "id": "agent_economics",
    "commission_note": ("agent commission on live revenue is commonly in the range "
                        "of a low-double-digit percentage of gross (often cited "
                        "around 10-15%) — VARIES; never assert a figure for a "
                        "specific deal."),
    "no_upfront_fees": ("legitimate agents never charge upfront / registration "
                        "fees — an upfront-fee ask is a red flag."),
    "scope_of_commission": ("a booking agent is entitled to commission on LIVE "
                            "revenue only — never on record sales, songwriting, or "
                            "publishing income."),
}


# ── OUT_OF_SCOPE — department boundaries. Ray B books; these belong elsewhere. ──
OUT_OF_SCOPE = {
    "tour_operations": {
        "owner": "tour-commander",
        "reason": ("advancing shows and day-of-show logistics are tour operations — "
                   "handed off to tour-commander, not booked here."),
    },
    "playlist_curator_outreach": {
        "owner": "puppet-master",
        "reason": ("playlist / curator outreach belongs to the management department "
                   "(puppet-master), not booking."),
    },
    "radio_dsp_promotion": {
        "owner": "airwave",
        "reason": ("radio and DSP editorial promotion belong to airwave, not "
                   "booking."),
    },
}


# ── HONESTY_RULES — the guardrails, stable ids (id / statement / allowed / ──────
# forbidden), mirroring the sibling corpora.
HONESTY_RULES = (
    {
        "id": "never_fabricate_venues",
        "statement": ("Venue names, promoter names, and their contacts are NEVER "
                      "invented. Real targets are artist-supplied or an explicit "
                      "gap — never conjured from a directory."),
        "allowed": "Filtering an artist-supplied venue list by capacity, region, or genre fit.",
        "forbidden": "Producing a venue name, address, or promoter contact the artist did not supply.",
    },
    {
        "id": "no_deal_figures_ever",
        "statement": ("No guarantee, split percentage, commission, or currency figure "
                      "is ever invented or quoted. A deal figure is only ever the "
                      "artist's own supplied number; mechanisms are encoded, numbers "
                      "are negotiated."),
        "allowed": "Explaining a versus deal or a door split as a structure.",
        "forbidden": "Ballparking a guarantee, a split percentage, or an agent commission for a deal.",
    },
    {
        "id": "deal_evaluation_is_structural",
        "statement": ("Evaluation flags which deal-memo terms are pinned or missing "
                      "and whether 'net' is defined — it never renders a good/bad "
                      "verdict. A concrete agreement goes to legal framing as a "
                      "draft-for-review."),
        "allowed": "Flagging that the radius clause or the net definition is undefined.",
        "forbidden": "Declaring a deal 'good', 'fair', or 'bad', or approving it as final.",
    },
    {
        "id": "holds_are_not_confirmations",
        "statement": ("A hold is not a confirmed booking and a booking inquiry is not "
                      "a signed deal; hold windows and challenge windows vary by venue "
                      "and are always verify-live, never asserted as standard."),
        "allowed": "Recording a hold request and surfacing that windows vary by venue.",
        "forbidden": "Telling the artist a date is 'confirmed' off a hold, or quoting a fixed hold window as a rule.",
    },
)
