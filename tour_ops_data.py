"""
PLMKR Miles (tour-commander) — structured tour-operations data (Miles's real
knowledge base).

Unit 1 (data-only): the researched tour-advancing / day-sheet / settlement-prep
map, encoded as structured records.
Source of truth: MILES_TOUR_OPS_MAP_v1 (researched in chat July 6 2026,
web-sourced: tour advancing practice, day-sheet/routing conventions, and
settlement-prep vocabulary for independent touring artists).

WHAT THIS MODULE IS (and is NOT):
  - DATA ONLY. No functions, no filtering logic, no I/O, no network, no
    secrets. The service layer (built in Unit 2) does all lookup / scaffold
    assembly. No advancing or settlement logic is encoded as code here — only
    as data records for the service to read.
  - Every record is a plain, JSON-serializable dict so the service can pass
    fields straight through into a scaffold without transformation.

HARD RULES honored here:
  - ZERO currency amounts or symbols anywhere. This domain touches settlement
    and budgets directly, so this module is scrupulous about it: no currency
    symbols of any kind, and no digit sits next to a money word (dollars,
    cents, fee, guarantee-as-a-number, etc). Money is described only as a
    mechanism — "a nightly guarantee", "a flat fee", "a percentage of net" —
    never as a figure.
  - PRIVACY: day-sheet fields that touch artist hotel information, door
    codes, or flight details are flagged sensitive here; the service layer
    (Unit 2) is responsible for actually excluding them from any
    printable/shareable output. This module only declares the flag.
  - BOUNDARIES: booking and deal terms belong to venue-hawk (Miles starts work
    only after the deal memo exists and never renegotiates terms); the actual
    accounting / ledger reconciliation belongs to ledger-lock (the
    "ledger-lock boundary") — Miles preps for settlement, he does not do the
    accounting.
  - Unknowns are described as mechanisms or open questions, never a guessed
    number or a guessed policy.

SCHEMA:
  MILES_DOCTRINE -> framing strings on what Miles is and is not
  ADVANCING_DOCTRINE[key] -> key, topic, description, venue_provides (list),
    union_house_risk, parking_doctrine
  DAY_SHEET_SPEC -> list of field records: field, description, sensitive (bool)
  DAY_SHEET_VARIANTS -> dict describing principal-vs-crew sheet doctrine
  SETTLEMENT_PREP_DOCTRINE[key] -> key, topic, description
  SETTLEMENT_VOCABULARY[term] -> term, mechanism
  ROUTING_AND_PREP[key] -> key, topic, fields/description
  FESTIVAL_VARIANT[key] -> key, topic, description
  BOUNDARIES[key] -> key, what, owning_department, miles_role
"""

# ── Standing framing strings (data, not logic) ────────────────────────────────
# What Miles is and is not — surfaced verbatim by the service so no output can
# be mistaken for a booking negotiation or an accounting ledger.
MILES_DOCTRINE = {
    "prep_not_negotiation": (
        "Miles advances shows and preps for settlement. Miles never negotiates "
        "or renegotiates booking terms — those are set in the deal memo before "
        "Miles's work even starts, and the deal memo belongs to venue-hawk."
    ),
    "prep_not_accounting": (
        "Miles prepares for settlement — confirming the deal memo, the deposit, "
        "the banking info, and the pre-settlement review. The actual "
        "reconciliation and ledger work at settlement is the ledger-lock "
        "boundary, not Miles's job."
    ),
    "documents_not_figures": (
        "Miles produces day sheets, routing sheets, and settlement-prep "
        "checklists. Miles never states a dollar figure, a guarantee amount, "
        "or a fee amount — those live in the deal memo and the ledger, not in "
        "a Miles document."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCING_DOCTRINE — advancing is the tour aligning day-of-show details and
# tech requirements with the venue long before arrival. The tour initiates.
# ═══════════════════════════════════════════════════════════════════════════════
ADVANCING_DOCTRINE = {
    "advancing_overview": {
        "key": "advancing_overview",
        "topic": "advancing_overview",
        "description": (
            "Advancing is the process of the tour and the venue aligning every "
            "day-of-show detail and tech requirement well before load-in. The "
            "tour side initiates the advance, not the venue. The reference "
            "document for the whole advance is the deal memo — every question "
            "in the advance package traces back to what the deal memo already "
            "settled. Contacts and the deal memo itself come from the booking "
            "agent (cross-ref venue-hawk); Miles does not source venue contacts "
            "independently."
        ),
        "venue_provides": [],
        "union_house_risk": None,
        "parking_doctrine": None,
    },
    "advance_package_contents": {
        "key": "advance_package_contents",
        "topic": "advance_package_contents",
        "description": (
            "The advance package the tour sends to the venue typically bundles: "
            "the tech rider, the stage plot, the input list, the hospitality "
            "rider, the pass sheet (who gets access to what areas), and the "
            "settlement documents needed for show night."
        ),
        "venue_provides": [],
        "union_house_risk": None,
        "parking_doctrine": None,
    },
    "venue_advance": {
        "key": "venue_advance",
        "topic": "venue_advance",
        "description": (
            "The venue advance covers everything the building itself is "
            "responsible for: house policies, box office and will-call "
            "process, security and door staff, house sound and lighting "
            "systems and their limits, parking and load-in logistics, "
            "curfew and noise ordinances, and local labor requirements. It "
            "is a conversation with the venue's staff about what the room "
            "can and cannot do."
        ),
        "venue_provides": [
            "load-in description (dock, ramp, stairs, freight elevator, distance from truck to stage)",
            "stage and venue dimensions",
            "rigging points and rigging capacity",
            "house audio specifications",
            "house lighting specifications",
            "back-of-house layout (dressing rooms, catering space, production office)",
        ],
        "union_house_risk": (
            "Union houses layer local labor rules on top of everything else — "
            "who is allowed to touch what equipment, minimum crew calls, and "
            "meal-break timing. Misreading a union house's local rules is a "
            "genuine budget risk: unplanned local labor requirements can "
            "surface as unbudgeted costs on the settlement side if the "
            "advance did not flag them ahead of time."
        ),
        "parking_doctrine": None,
    },
    "production_advance": {
        "key": "production_advance",
        "topic": "production_advance",
        "description": (
            "The production advance covers everything the touring production "
            "itself brings and needs supported: the tech rider (backline, "
            "audio, lighting, video needs), the stage plot and input list, "
            "power requirements, the hospitality rider, and how the touring "
            "crew's gear integrates with what the house already provides. It "
            "is a conversation between the tour's production manager and the "
            "venue's production contact about how the show actually gets "
            "built on the day."
        ),
        "venue_provides": [],
        "union_house_risk": None,
        "parking_doctrine": None,
    },
    "parking_and_load_out": {
        "key": "parking_and_load_out",
        "topic": "parking_and_load_out",
        "description": (
            "Parking for the tour vehicles has to be a pre-determined plan "
            "confirmed during the advance, never something worked out on "
            "arrival. Premium, dense cities make a workable parking plan "
            "genuinely hard to secure, which is exactly why it has to be "
            "locked in ahead of time rather than improvised. The cardinal "
            "rule of parking doctrine: never risk being blocked in at "
            "load-out — a vehicle boxed in by other traffic or double-parked "
            "cars at the end of the night can cost the tour its overnight "
            "drive to the next date."
        ),
        "venue_provides": [],
        "union_house_risk": None,
        "parking_doctrine": (
            "A pre-determined parking plan is required before arrival; "
            "premium cities make this hard; never risk being blocked in at "
            "load-out."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# DAY_SHEET_SPEC — the concise daily snapshot given to artists and crew.
# Sensitive fields are FLAGGED here; actual exclusion from shareable output is
# Unit 2 (service layer) work.
# ═══════════════════════════════════════════════════════════════════════════════
DAY_SHEET_SPEC = [
    {"field": "day", "description": "day of the week and day-of-tour count", "sensitive": False},
    {"field": "date", "description": "calendar date of the show", "sensitive": False},
    {"field": "venue_name", "description": "name of the venue", "sensitive": False},
    {"field": "venue_address", "description": "street address of the venue", "sensitive": False},
    {"field": "doors", "description": "time doors open to the public", "sensitive": False},
    {"field": "set_times", "description": "set start times for each performer", "sensitive": False},
    {"field": "set_lengths", "description": "length of each set", "sensitive": False},
    {"field": "changeover", "description": "changeover time between sets", "sensitive": False},
    {"field": "curfew", "description": "hard curfew time the venue enforces", "sensitive": False},
    {"field": "wifi", "description": "venue wifi network name and password", "sensitive": False},
    {
        "field": "artist_hotel_info",
        "description": "hotel name, address, and room details for the artist",
        "sensitive": True,
    },
    {
        "field": "door_codes",
        "description": "backstage, dressing room, or building access codes",
        "sensitive": True,
    },
    {
        "field": "flight_details",
        "description": "flight numbers, times, and confirmation details",
        "sensitive": True,
    },
]

# Principal vs crew day-sheet doctrine — legitimate variants, not an error.
DAY_SHEET_VARIANTS = {
    "principal_vs_crew": (
        "Principal (artist-facing) and crew day sheets are legitimately "
        "different documents built from the same underlying information. A "
        "crew sheet can omit fields a principal sheet includes (for example, "
        "hotel information the crew does not need) and can include fields a "
        "principal sheet omits (for example, load-in and crew-call detail). "
        "Neither variant is the 'complete' one — they are audience-specific "
        "views of the same day."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# SETTLEMENT_PREP_DOCTRINE — settlement is the post-show reconciliation with
# the promoter. Miles PREPS ONLY; the accounting itself is the ledger-lock
# boundary.
# ═══════════════════════════════════════════════════════════════════════════════
SETTLEMENT_PREP_DOCTRINE = {
    "settlement_overview": {
        "key": "settlement_overview",
        "topic": "settlement_overview",
        "description": (
            "Settlement is the post-show reconciliation with the promoter: "
            "ticket sales, expenses, and the agreed fees are compared against "
            "what the deal memo promised. Miles's job is PREP ONLY — "
            "understanding the deal memo before the tour, confirming the "
            "numbers line up on paper, and getting the right documents in the "
            "promoter's hands ahead of time. The actual accounting and ledger "
            "reconciliation at the settlement table is the ledger-lock "
            "boundary: that work belongs to ledger-lock, not to Miles."
        ),
    },
    "understand_the_deal_memo_before_the_tour": {
        "key": "understand_the_deal_memo_before_the_tour",
        "topic": "understand_the_deal_memo_before_the_tour",
        "description": (
            "Miles reads and understands the deal memo before the tour ever "
            "leaves, so every settlement expectation on show day is already "
            "known rather than discovered at the settlement table."
        ),
    },
    "confirm_the_deposit": {
        "key": "confirm_the_deposit",
        "topic": "confirm_the_deposit",
        "description": (
            "The deposit is confirmed via the agency report ahead of the show "
            "date, so a missing or short deposit is caught during advancing, "
            "not discovered at settlement."
        ),
    },
    "banking_info_sent_ahead": {
        "key": "banking_info_sent_ahead",
        "topic": "banking_info_sent_ahead",
        "description": (
            "W9 (or local equivalent tax form), banking details, and wire "
            "information are sent to the promoter ahead of time, well before "
            "show day, so payment is not held up by paperwork on the night."
        ),
    },
    "pre_settlement_review_timing": {
        "key": "pre_settlement_review_timing",
        "topic": "pre_settlement_review_timing",
        "description": (
            "A pre-settlement review happens in the AFTERNOON of show day — "
            "well before doors — so any discrepancy in the running numbers "
            "can be raised with the promoter while there is still time to "
            "resolve it, instead of first surfacing at the settlement table "
            "after the show."
        ),
    },
    "unsettled_is_sometimes_correct": {
        "key": "unsettled_is_sometimes_correct",
        "topic": "unsettled_is_sometimes_correct",
        "description": (
            "A show CAN be left unsettled on the night if there is no "
            "immediate remedy available for a discrepancy. That is not a "
            "failure state to force a resolution on the spot — it is a "
            "legitimate outcome to note and hand off to ledger-lock for "
            "the actual reconciliation and remedy afterward."
        ),
    },
}

# Vocabulary block — mechanisms only, no numbers anywhere.
SETTLEMENT_VOCABULARY = {
    "sellable_vs_legal_capacity": {
        "term": "sellable_vs_legal_capacity",
        "mechanism": (
            "Sellable capacity is the number of tickets a venue actually puts "
            "on sale; legal capacity is the maximum the fire code or venue "
            "license allows. Sellable capacity is typically held below legal "
            "capacity to leave room for guests, comps, and production holds."
        ),
    },
    "advance_vs_walk_up_pricing": {
        "term": "advance_vs_walk_up_pricing",
        "mechanism": (
            "Advance pricing is what a ticket costs when bought ahead of the "
            "show; walk-up pricing is what it costs bought at the door, and "
            "the two are tracked separately in settlement because they can "
            "carry a different price mechanism."
        ),
    },
    "ticket_buys": {
        "term": "ticket_buys",
        "mechanism": (
            "A ticket buy is when a party purchases a block of tickets "
            "outright in advance, shifting the risk of those seats selling "
            "onto the buyer rather than the promoter."
        ),
    },
    "vip_settled_separately": {
        "term": "vip_settled_separately",
        "mechanism": (
            "VIP packages (upgrades, meet-and-greet add-ons, merchandise "
            "bundles) are frequently settled as their own line, separate from "
            "general ticket sales, because they can carry different vendors "
            "and different splits."
        ),
    },
    "regional_withholding": {
        "term": "regional_withholding",
        "mechanism": (
            "Some regions withhold a portion of the artist's settlement at "
            "the point of payment as a tax mechanism, which is later "
            "reconciled or reclaimed at tax time. Whether withholding applies "
            "and how it is reclaimed is the ledger-lock boundary — Miles "
            "flags that a withholding mechanism may apply, ledger-lock does "
            "the reconciliation."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTING_AND_PREP — the routing sheet and the advancing spreadsheet-as-dashboard.
# ═══════════════════════════════════════════════════════════════════════════════
ROUTING_AND_PREP = {
    "routing_sheet_fields": {
        "key": "routing_sheet_fields",
        "topic": "routing_sheet_fields",
        "fields": ["date", "city", "venue", "drive_distance", "travel_method"],
        "description": (
            "The routing sheet is the tour's date-by-date map: for each date "
            "it tracks the date, the city, the venue, the drive distance to "
            "get there, and the travel method (drive, fly, rail, ferry) used "
            "to make it."
        ),
    },
    "advancing_spreadsheet_dashboard": {
        "key": "advancing_spreadsheet_dashboard",
        "topic": "advancing_spreadsheet_dashboard",
        "fields": [
            "sent_done_outstanding_status",
            "hotels_status",
            "flights_status",
            "drive_times",
            "time_zone_change_flag",
        ],
        "description": (
            "The advancing spreadsheet functions as a live dashboard across "
            "the whole tour: a status column tracks whether each advance was "
            "sent, done, or is still outstanding; hotel and flight booking "
            "status is tracked per date; drive times between dates are "
            "logged; and any date where the time zone changes from the "
            "previous date is explicitly flagged so nobody miscounts a call "
            "time across a zone change."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FESTIVAL_VARIANT — festival dates use the artist welcome letter as the
# advance start, not the standard club/theater advance flow.
# ═══════════════════════════════════════════════════════════════════════════════
FESTIVAL_VARIANT = {
    "welcome_letter_topics": {
        "key": "welcome_letter_topics",
        "topic": "welcome_letter_topics",
        "fields": [
            "production",
            "parking",
            "hotels",
            "credentials",
            "comps",
            "merch",
            "settlement",
            "deadlines",
        ],
        "description": (
            "For a festival date, the artist welcome letter is the starting "
            "point of the advance rather than a direct venue conversation. "
            "It typically covers production details, parking, hotel "
            "arrangements or recommendations, credential (laminate/wristband) "
            "allocation, guest and comp ticket allocation, merch selling "
            "arrangements, settlement mechanics, and the deadlines by which "
            "the tour must respond with its own information."
        ),
    },
    "reconfirm_before_deep_prep": {
        "key": "reconfirm_before_deep_prep",
        "topic": "reconfirm_before_deep_prep",
        "description": (
            "Before advancing deep into festival prep, the stage assignment, "
            "set time, and set length must be reconfirmed — festival "
            "schedules shift more than a standard tour date's, so working off "
            "a stale time slot wastes the whole advance."
        ),
    },
    "festival_settlement_mechanism": {
        "key": "festival_settlement_mechanism",
        "topic": "festival_settlement_mechanism",
        "description": (
            "Festival settlement is usually structured as a flat fee rather "
            "than a nightly guarantee against a door split, with a possible "
            "withholding mechanism applied depending on the region. Merch "
            "selling at a festival is typically bounded by a merch limit "
            "(what percentage of gross merch sales the festival takes) — "
            "both the flat fee and the merch limit are described here only "
            "as mechanisms, never as a number."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# BOUNDARIES — Miles explains and consumes; he does not negotiate deals or do
# accounting. Mirrors legal_data.OUT_OF_SCOPE's shape.
# ═══════════════════════════════════════════════════════════════════════════════
BOUNDARIES = {
    "booking_and_deal_terms": {
        "key": "booking_and_deal_terms",
        "what": "negotiating or setting booking and deal terms for a show",
        "owning_department": "venue-hawk",
        "miles_role": (
            "Miles starts his work only AFTER the deal memo already exists, "
            "consumes its fields (dates, fees, venue, contacts) to build the "
            "advance, and never renegotiates any term in it. Booking and deal "
            "terms belong to venue-hawk."
        ),
    },
    "royalty_and_accounting": {
        "key": "royalty_and_accounting",
        "what": "royalty accounting and settlement ledger reconciliation",
        "owning_department": "ledger-lock",
        "miles_role": (
            "Miles preps for settlement — confirming the deal memo, the "
            "deposit, and the banking info, and running the afternoon "
            "pre-settlement review — but the actual accounting and ledger "
            "reconciliation is the ledger-lock boundary. Royalty and "
            "accounting work belongs to ledger-lock."
        ),
    },
}
