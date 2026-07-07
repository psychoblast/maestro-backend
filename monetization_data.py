"""
PLMKR Mo (mobile-monetize) — structured revenue-diversification data (Mo's
real knowledge base).

Unit 1 (data-only): the researched independent-artist revenue-diversification
map, encoded as structured records.
Source of truth: MO_MONETIZATION_MAP_v1 (researched in chat July 6 2026,
web-sourced: independent-artist revenue-stream taxonomy, diversification and
stream-stacking doctrine, audience-independent vs audience-dependent
sequencing, and catalog/metadata administration practice).

WHAT THIS MODULE IS (and is NOT):
  - DATA ONLY. No functions, no filtering logic, no I/O, no network, no
    secrets. The service layer (built in a later unit) does all lookup /
    scaffold assembly. No monetization logic is encoded as code here — only
    as data records for the service to read.
  - Every record is a plain, JSON-serializable dict so the service can pass
    fields straight through into a scaffold without transformation.

HARD RULES honored here (this domain is explicitly about money, so these are
enforced with extra care):
  - ZERO currency symbols or dollar amounts anywhere.
  - ZERO income projections or dollar figures of ANY kind — not a ballpark,
    not a range, not a "typical" number. This is the single hardest integrity
    rule in this corpus: every "how much" answer is mechanism + a note that
    the real numbers are [ARTIST-SUPPLIED] + "it varies" — never a number Mo
    invented or estimated. See INTEGRITY.
  - Stream counts and sequencing language (e.g. "three to five streams") are
    spelled out in words rather than digits throughout, so no digit anywhere
    in this corpus can ever be mistaken for a dollar figure.
  - BOUNDARIES: Mo maps the revenue landscape and sequences the strategy;
    Mo does not execute any other department's specialized work. Grant
    applications belong to fund-phantom, brand outreach/negotiation belongs
    to brand-connect, royalty registration/collection belongs to ledger-lock,
    sync-licensing pitching belongs to ink-and-air, and booking/touring
    execution belongs to tour-commander (Miles).
  - Unknowns are described as mechanisms or open questions, never a guessed
    number or a guessed policy.

SCHEMA:
  MO_DOCTRINE -> framing strings on what Mo is and is not
  REVENUE_STREAM_TAXONOMY[key] -> key, description, mechanism,
    prerequisites (list), payment_pattern
    ("recurring" | "lumpy" | "one_time" | "royalty_based", or a list of more
    than one when a stream genuinely mixes patterns),
    owning_department (None, a cross-ref agent id string, or a list of
    cross-ref agent id strings when more than one department is involved)
  DIVERSIFICATION[key] -> key, description
  SEQUENCING[key] -> key, category ("audience_independent" |
    "audience_dependent"), streams (list of REVENUE_STREAM_TAXONOMY keys),
    description
  ADMIN[key] -> key, description
  INTEGRITY[key] -> key, description
  BOUNDARIES[key] -> key, what, owning_department, mo_role
"""

# ── Standing framing strings (data, not logic) ────────────────────────────────
# What Mo is and is not — surfaced verbatim by the service so no output can be
# mistaken for a financial projection or a promise of income.
MO_DOCTRINE = {
    "no_income_projections": (
        "Mo never states an income projection or a dollar figure of any kind, "
        "for any revenue stream, ever. Every 'how much' question is answered "
        "with the mechanism plus a note that the real numbers are "
        "[ARTIST-SUPPLIED] and 'it varies' — never a number Mo invented or "
        "estimated."
    ),
    "mechanisms_not_figures": (
        "Mo explains how each revenue stream actually works — the mechanism "
        "money flows through, what has to be true for it to pay, and how "
        "regularly it tends to pay — never how much it pays. Mechanism, "
        "prerequisites, and payment pattern are data; a dollar amount never is."
    ),
    "diversify_dont_concentrate": (
        "A full-time independent income typically stacks three to five "
        "revenue streams, mixing predictable/recurring streams with "
        "lumpy/irregular ones, so that no single stream's disruption is "
        "catastrophic to the artist's income as a whole."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# REVENUE_STREAM_TAXONOMY — what each revenue stream IS, how the money actually
# flows, what has to be true first, and who owns execution if it is not Mo.
# ═══════════════════════════════════════════════════════════════════════════════
REVENUE_STREAM_TAXONOMY = {
    "streaming_royalties": {
        "key": "streaming_royalties",
        "description": (
            "Streaming royalties work constantly in the background and "
            "compound with every other stream in this taxonomy — a stream "
            "never stops accruing once a recording is live — but streaming "
            "income is rarely sufficient by itself as a full income source "
            "for an independent artist. It works best as one strand in a "
            "stack, not as a foundation on its own."
        ),
        "mechanism": (
            "Royalties accrue whenever a recording is streamed; payment is "
            "split between the master rights holder and the composition's "
            "rights holders and flows to the artist through distributors "
            "and/or collection societies. There is no fixed per-play rate — "
            "the mechanism is proportional to a platform's royalty pool and "
            "total stream volume, not a flat unit price."
        ),
        "prerequisites": [
            "recordings distributed to streaming platforms",
            "accurate metadata and rights registration so streams are correctly attributed and paid",
        ],
        "payment_pattern": "recurring",
        "owning_department": None,
    },
    "live_performance": {
        "key": "live_performance",
        "description": (
            "Live performance is the dominant revenue source for most "
            "independent artists. Margins at the club level are thin until "
            "three things are in place together: merchandise selling "
            "alongside the show, efficient date-to-date routing that avoids "
            "wasted travel, and an actual draw (an audience willing to buy "
            "tickets). Without all three working together, a live date can "
            "look like income on paper and still net very little."
        ),
        "mechanism": (
            "Live income flows from guarantees, door splits, or a "
            "combination of both, settled with the venue or promoter after "
            "the show. Touring adds routing and travel cost that offsets "
            "gross ticket revenue unless the whole system — dates, merch, "
            "draw — works together rather than separately."
        ),
        "prerequisites": [
            "a bookable live show and material to perform",
            "an existing draw sufficient to sell tickets",
            "routing that does not burn revenue on unnecessary travel",
            "merch-selling infrastructure at the show",
        ],
        "payment_pattern": "lumpy",
        "owning_department": "tour-commander",
    },
    "merchandise": {
        "key": "merchandise",
        "description": (
            "Merchandise creates a tangible fan connection that streaming "
            "and other digital formats cannot replicate, and it carries a "
            "higher margin than streaming per unit of fan spend. It is "
            "strongest specifically at live shows, where an already-engaged "
            "audience is standing in front of the merch table."
        ),
        "mechanism": (
            "Merchandise is sold directly to fans — at shows, online, or "
            "both — and revenue is the sale price less production and "
            "fulfillment cost. Margin depends heavily on where and how it is "
            "sold, with live-show sales carrying the least friction between "
            "fan and product."
        ),
        "prerequisites": [
            "physical or digital product to sell",
            "a live show or online storefront as the point of sale",
            "an existing fan connection to spend against",
        ],
        "payment_pattern": "one_time",
        "owning_department": None,
    },
    "sync_licensing": {
        "key": "sync_licensing",
        "description": (
            "Sync-licensing payments are larger but far less frequent than "
            "streaming or live income. A sync opportunity only works if the "
            "underlying rights are clear and the recording's and "
            "composition's metadata is clean enough for a music supervisor "
            "or licensing platform to find and clear the work quickly — sync "
            "moves fast, and unclear rights or messy metadata simply cause "
            "the opportunity to move on to someone else's catalog."
        ),
        "mechanism": (
            "A rights holder licenses a recording and/or composition for "
            "synchronization to picture — film, TV, advertising, games — "
            "with payment negotiated per placement rather than accrued per "
            "play, making the stream inherently irregular rather than a "
            "running total."
        ),
        "prerequisites": [
            "clear, unencumbered rights to license",
            "clean, discoverable metadata",
            "a pitching or placement channel",
        ],
        "payment_pattern": "lumpy",
        "owning_department": "ink-and-air",
    },
    "publishing_royalties": {
        "key": "publishing_royalties",
        "description": (
            "Publishing royalties are the composition-side counterpart to "
            "streaming and performance royalties on the recording side, and "
            "they depend entirely on registration and collection being done "
            "correctly — money owed on a composition that was never "
            "registered with the right society is simply never collected."
        ),
        "mechanism": (
            "Publishing royalties — mechanical, performance, and "
            "sync-adjacent — accrue on the composition itself, separate from "
            "the master recording, and are collected through publishers and "
            "collection societies rather than paid directly by a platform or "
            "venue."
        ),
        "prerequisites": [
            "the composition registered with the correct publishing administrator or society",
            "accurate songwriter and publisher split documentation",
        ],
        "payment_pattern": "royalty_based",
        "owning_department": ["ink-and-air", "ledger-lock"],
    },
    "direct_fan_support": {
        "key": "direct_fan_support",
        "description": (
            "Direct fan support covers two related but distinct mechanisms "
            "living under one stream. Subscriptions are predictable, "
            "recurring revenue built on ongoing exclusivity and "
            "consistency — a subscriber expects something extra, delivered "
            "reliably, in exchange for a recurring commitment. Crowdfunding "
            "is different: it activates fan loyalty that already exists "
            "rather than creating loyalty from nothing, which is why a "
            "crowdfunding campaign succeeds or fails on the strength of the "
            "existing fan relationship going in, not on the campaign's own "
            "marketing."
        ),
        "mechanism": (
            "Subscriptions: a fan pays on a recurring basis in exchange for "
            "ongoing exclusive access or content, and revenue compounds as "
            "the subscriber base grows and is retained. Crowdfunding: a fan "
            "makes a one-time or campaign-bound contribution, often in "
            "exchange for a reward tier, activating an existing relationship "
            "rather than building a new one during the campaign itself."
        ),
        "prerequisites": [
            "an existing fan relationship to activate (crowdfunding) or retain (subscriptions)",
            "a mechanism or platform for recurring billing or campaign collection",
            "something genuinely exclusive or reward-worthy to offer in exchange",
        ],
        "payment_pattern": ["recurring", "one_time"],
        "owning_department": None,
    },
    "teaching_and_session_work": {
        "key": "teaching_and_session_work",
        "description": (
            "Teaching and session work is the one stream in this taxonomy "
            "that produces immediate income without requiring an existing "
            "audience. Every other stream here needs some baseline reach or "
            "fan connection before it can pay meaningfully; a lesson booked "
            "or a session played pays now, independent of how large an "
            "artist's following is."
        ),
        "mechanism": (
            "An artist is paid directly for time and skill — teaching a "
            "lesson, playing a session, arranging or engineering for "
            "someone else's project — with payment tied to the work "
            "performed rather than to audience size or catalog reach."
        ),
        "prerequisites": [
            "a marketable skill (instrument, production, arrangement, engineering)",
            "a channel to find students or session-hiring clients",
        ],
        "payment_pattern": "one_time",
        "owning_department": None,
    },
    "content_monetization": {
        "key": "content_monetization",
        "description": (
            "Content monetization covers platform advertising revenue and "
            "sponsorships tied to content an artist produces — video, "
            "livestreams, and other recurring content formats — as distinct "
            "from the underlying music itself."
        ),
        "mechanism": (
            "Platforms share a portion of advertising revenue generated "
            "against a creator's content based on view and watch metrics, "
            "and separately, sponsors may pay directly for placement within "
            "that content. Both mechanisms depend on the platform's own ad "
            "system and on audience size and engagement rather than on music "
            "sales."
        ),
        "prerequisites": [
            "a content platform and a body of content",
            "sufficient audience engagement for a platform's ad-revenue threshold or a sponsor's interest",
        ],
        "payment_pattern": "recurring",
        "owning_department": None,
    },
    "brand_partnerships": {
        "key": "brand_partnerships",
        "description": (
            "Brand partnerships pair an artist's audience and image with a "
            "company's marketing goals. Outreach and negotiation for this "
            "stream is specialized work that lives with brand-connect — Mo "
            "maps that this stream exists and where it fits in a stack, but "
            "does not run the outreach itself."
        ),
        "mechanism": (
            "A brand pays — in cash, product, or services — for an artist's "
            "endorsement, content collaboration, or association with a "
            "campaign, negotiated deal by deal rather than accrued "
            "automatically."
        ),
        "prerequisites": [
            "an audience or image a brand wants to reach",
            "a negotiated agreement defining scope and deliverables",
        ],
        "payment_pattern": "one_time",
        "owning_department": "brand-connect",
    },
    "grants": {
        "key": "grants",
        "description": (
            "Grants provide funding from arts councils, foundations, or "
            "government programs, typically tied to a specific project or "
            "purpose rather than to general income. Application and "
            "submission execution for this stream lives with fund-phantom — "
            "Mo maps that grants exist as a stream and how they fit the "
            "sequencing strategy, but does not prepare or submit "
            "applications itself."
        ),
        "mechanism": (
            "A funding body awards money against a submitted application, "
            "usually restricted to a defined project or purpose and subject "
            "to a competitive review and intake cycle rather than being "
            "available on demand."
        ),
        "prerequisites": [
            "a project or purpose that fits a fund's eligibility criteria",
            "a submitted, competitive application",
        ],
        "payment_pattern": "lumpy",
        "owning_department": "fund-phantom",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# DIVERSIFICATION — why a full-time independent income stacks multiple streams,
# how they compound on each other, and how to sequence building them.
# ═══════════════════════════════════════════════════════════════════════════════
DIVERSIFICATION = {
    "stream_count_range": {
        "key": "stream_count_range",
        "description": (
            "A full-time independent income typically stacks three to five "
            "revenue streams rather than relying on one. Fewer than that "
            "usually means too much weight sitting on too few sources; more "
            "than that usually means attention spread so thin that no stream "
            "gets the focus it needs to actually work."
        ),
    },
    "no_catastrophic_single_point": {
        "key": "no_catastrophic_single_point",
        "description": (
            "No single stream should be so dominant that its disruption is "
            "catastrophic. A platform policy change, a canceled tour, or a "
            "lost brand deal should dent the income, not erase it — that "
            "protection only exists if the artist was never depending on one "
            "stream for most of their income in the first place."
        ),
    },
    "predictable_vs_lumpy_balance": {
        "key": "predictable_vs_lumpy_balance",
        "description": (
            "A healthy mix balances predictable, recurring streams (like "
            "streaming royalties or subscriptions) against lumpy, irregular "
            "streams (like live performance, sync placements, or grants) so "
            "that cash flow stays stable even when the irregular streams pay "
            "out unevenly across the year."
        ),
    },
    "compounding_relationships": {
        "key": "compounding_relationships",
        "description": (
            "Streams compound on each other rather than sitting in "
            "isolation. Three relationships matter most: live performance "
            "drives merch sales, because a captive, already-engaged crowd at "
            "a show is the easiest possible audience to sell merch to; "
            "streaming attracts sync-licensing interest, because a "
            "discoverable, well-performing catalog is exactly what a music "
            "supervisor or licensing platform is looking for; and teaching "
            "builds session-work credibility, because visible teaching "
            "experience signals the exact skill and reliability a "
            "session-hiring client is trying to verify."
        ),
    },
    "start_small_then_add": {
        "key": "start_small_then_add",
        "description": (
            "The practical sequencing advice is to start with two to three "
            "streams, master those — meaning they are reliably working, not "
            "merely attempted — and only then add more. Spreading across "
            "every available stream immediately, before any one of them is "
            "actually working, tends to produce shallow, underperforming "
            "effort across all of them rather than a working stack."
        ),
    },
    "match_artist_strengths": {
        "key": "match_artist_strengths",
        "description": (
            "The mix an artist builds should match their own strengths and "
            "what they actually enjoy doing, not a generic template copied "
            "from another artist's stack. A stream that fights an artist's "
            "actual skills or interests is much less likely to be sustained "
            "long enough to compound with the others."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SEQUENCING — audience-independent streams that can start on day one versus
# audience-dependent streams that require an existing fanbase to work at all.
# ═══════════════════════════════════════════════════════════════════════════════
SEQUENCING = {
    "audience_independent_streams": {
        "key": "audience_independent_streams",
        "category": "audience_independent",
        "streams": ["teaching_and_session_work"],
        "description": (
            "Teaching and session work can start generating income on day "
            "one — no existing audience is required before either one pays. "
            "A teaching relationship or a session booking is a direct "
            "exchange of skill for payment, independent of how many fans an "
            "artist currently has."
        ),
    },
    "audience_dependent_streams": {
        "key": "audience_dependent_streams",
        "category": "audience_dependent",
        "streams": ["merchandise", "direct_fan_support", "streaming_royalties"],
        "description": (
            "Merchandise, subscriptions (direct fan support), and "
            "meaningful streaming revenue all require an existing fanbase "
            "before they work at all. Merch needs someone already invested "
            "enough to buy it, subscriptions need someone already invested "
            "enough to pay recurring, and streaming only becomes meaningful "
            "income at a volume of plays that requires an existing audience "
            "finding and replaying the work."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN — every revenue stream carries administrative obligations of its own,
# and sloppy metadata is a mechanism that quietly loses money.
# ═══════════════════════════════════════════════════════════════════════════════
ADMIN = {
    "per_stream_registration_and_reporting": {
        "key": "per_stream_registration_and_reporting",
        "description": (
            "Each revenue stream carries its own registration requirements, "
            "metadata requirements, and reporting obligations. A stream is "
            "not 'set and forget' once it starts paying — the ongoing "
            "administrative upkeep is part of what keeps the stream working "
            "at all."
        ),
    },
    "sloppy_metadata_quietly_loses_money": {
        "key": "sloppy_metadata_quietly_loses_money",
        "description": (
            "Sloppy metadata quietly loses money: mismatched writer or "
            "publisher splits and missing registrations mean royalties are "
            "earned but never claimed, sitting unclaimed at a collection "
            "society, or paid out to the wrong party entirely. The mechanism "
            "here is a paperwork failure, not a lack of demand for the work — "
            "the money exists, it simply cannot find its way to the artist."
        ),
    },
    "catalog_as_structured_asset": {
        "key": "catalog_as_structured_asset",
        "description": (
            "An artist's catalog is itself a structured asset, not a loose "
            "pile of recordings — the same registration, metadata, and "
            "split-of-record discipline that lets any one stream pay "
            "correctly is what makes the catalog as a whole valuable and "
            "auditable. Cross-ref ledger-lock for the catalog and "
            "royalty-accounting angle: Mo maps why the discipline matters, "
            "ledger-lock does the actual accounting."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRITY — the hard rule for this entire corpus. Mo never states an income
# projection or a dollar figure of any kind.
# ═══════════════════════════════════════════════════════════════════════════════
INTEGRITY = {
    "never_states_a_dollar_figure": {
        "key": "never_states_a_dollar_figure",
        "description": (
            "Mo never states an income projection or a dollar figure of any "
            "kind, for any stream, under any circumstance. This is the "
            "hardest integrity rule in this entire corpus, because this "
            "domain is explicitly about money and the temptation to sound "
            "concrete by inventing a number is exactly the failure mode this "
            "rule exists to prevent."
        ),
    },
    "how_much_gets_mechanism_and_it_varies": {
        "key": "how_much_gets_mechanism_and_it_varies",
        "description": (
            "Every 'how much' question is answered with the mechanism "
            "behind the stream, a note that the real numbers are "
            "[ARTIST-SUPPLIED], and an explicit 'it varies' framing — never "
            "a specific number Mo invented, estimated, or extrapolated from "
            "any other artist's results."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# BOUNDARIES — Mo maps the revenue landscape and sequences the strategy; Mo
# does not execute any other department's specialized work. Mirrors
# legal_data.OUT_OF_SCOPE's shape.
# ═══════════════════════════════════════════════════════════════════════════════
BOUNDARIES = {
    "grant_application_execution": {
        "key": "grant_application_execution",
        "what": "preparing or submitting a grant application",
        "owning_department": "fund-phantom",
        "mo_role": (
            "Mo maps that grants exist as a revenue stream and where they "
            "sequence into the artist's overall stack; preparing or "
            "submitting the actual application is fund-phantom's job."
        ),
    },
    "brand_partnership_outreach": {
        "key": "brand_partnership_outreach",
        "what": "brand outreach and negotiation",
        "owning_department": "brand-connect",
        "mo_role": (
            "Mo maps that brand partnerships exist as a revenue stream and "
            "how they fit alongside an artist's other streams; running the "
            "outreach and negotiating the deal is brand-connect's job."
        ),
    },
    "royalty_registration_and_collection": {
        "key": "royalty_registration_and_collection",
        "what": "royalty registration and collection accounting",
        "owning_department": "ledger-lock",
        "mo_role": (
            "Mo maps how streaming and publishing royalties flow and why "
            "registration matters; actually registering works and "
            "reconciling collected royalties is ledger-lock's job."
        ),
    },
    "sync_licensing_pitching": {
        "key": "sync_licensing_pitching",
        "what": "pitching and placing sync-licensing opportunities",
        "owning_department": "ink-and-air",
        "mo_role": (
            "Mo maps sync licensing as a revenue stream and what has to be "
            "true (clear rights, clean metadata) for it to work; pitching "
            "and placing the actual opportunity is ink-and-air's job."
        ),
    },
    "booking_and_touring_execution": {
        "key": "booking_and_touring_execution",
        "what": "booking shows and executing tour logistics",
        "owning_department": "tour-commander",
        "mo_role": (
            "Mo maps live performance as a revenue stream and how it "
            "compounds with merch and other streams; booking the shows and "
            "running the tour is tour-commander's (Miles's) job."
        ),
    },
}
