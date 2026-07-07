"""
PLMKR Kai (grid-prophet) — structured digital-marketing data (Kai's real
knowledge base).

Unit 1 (data-only): the researched independent-artist digital-marketing /
paid-promotion map, encoded as structured records.
Source of truth: KAI_MARKETING_MAP_v1 (researched in chat July 6 2026,
web-sourced: channel-sequencing doctrine, the organic-proof-first / "spark ad"
paid-promotion pattern, platform-selection-by-objective practice, budget
mechanics for independent-artist ad spend, post-release momentum and
measurement doctrine, and paid-vs-payola integrity doctrine for music
marketing).

WHAT THIS MODULE IS (and is NOT):
  - DATA ONLY. No functions, no filtering logic, no I/O, no network, no
    secrets. The service layer (built in a later unit) does all lookup /
    scaffold assembly. No marketing logic is encoded as code here — only as
    data records for the service to read.
  - Every record is a plain, JSON-serializable dict so the service can pass
    fields straight through into a scaffold without transformation.

HARD RULES honored here (this domain touches ad budgets directly, so these are
enforced with extra care):
  - ZERO currency symbols or dollar amounts anywhere.
  - BUDGET_MECHANICS in particular describes mechanism and practice only —
    start small, test multiple creatives, kill fast, never spend it all on one
    ad, scale only what already works — and contains ZERO dollar amounts,
    ZERO specific spend numbers, and ZERO percentages of budget. A budget
    mechanism is a practice, never a figure.
  - Numeric time thresholds are spelled out in words rather than bare digits
    wherever avoidable (e.g. "a couple of days"), except the platform-momentum
    window ("the first 48 to 72 hours") which the source map states as that
    specific framing — that window describes algorithmic momentum, not a
    spend figure, so it is kept as researched.
  - INTEGRITY is absolute: Kai never recommends buying streams or buying
    followers, full stop — that is fabricated, artificial growth, in the same
    integrity family as data-oracle's (Data's) never-fabricate-a-number rule.
    Paid promotion is explicitly NOT the same mechanism as pay-for-editorial /
    payola — cross-ref signal-blaster's own earned-media-is-never-paid
    doctrine: Kai's paid-ads doctrine and signal-blaster's press-integrity
    doctrine are a matched pair, not the same mechanism.
  - BOUNDARIES: unlike several sibling corpora, Kai DOES own post
    scheduling/execution himself (grid-prophet is the digital-marketing
    department) — that is a deliberate difference from the pattern used by
    the other agents' corpora, where post scheduling routes elsewhere. Press
    and earned-media work still belongs to signal-blaster; playlist and
    curator pitching belongs to puppet-master and airwave; fan-relationship
    depth/nurture work belongs to fan-builder (Aria).
  - Unknowns are described as mechanisms or open questions, never a guessed
    number or a guessed policy.

SCHEMA:
  KAI_DOCTRINE -> framing strings on what Kai is and is not
  CHANNEL_SEQUENCE[key] -> key, category ("order" | "doctrine"), description,
    order (list, only on the "sequencing_order" entry)
  ORGANIC_PROOF_FIRST[key] -> key, category ("doctrine"), description
  PLATFORM_SELECTION[key] -> key, category ("channel" | "doctrine"),
    best_for (list, channel entries only), description
  BUDGET_MECHANICS[key] -> key, category ("mechanism"), description
  MEASUREMENT[key] -> key, category ("metric" | "doctrine"), description
  FIRST_72_HOURS[key] -> key, category ("doctrine"), description
  INTEGRITY[key] -> key, category ("rule"), description
  BOUNDARIES[key] -> key, what, owning_department (None or a cross-ref agent
    id string, or a list of ids when more than one department is involved),
    kai_role
"""

# ── Standing framing strings (data, not logic) ────────────────────────────────
# What Kai is and is not — surfaced verbatim by the service so no output can be
# mistaken for a guarantee of reach, a promise of virality, or a growth-buying
# recommendation.
KAI_DOCTRINE = {
    "sequence_before_spend": (
        "Kai sequences effort before he sequences spend: streaming-platform "
        "optimization first, organic short-form content second, email third, "
        "and PAID promotion last. Paid promotion only starts once the first "
        "three are already dialed in — it is never the first move."
    ),
    "organic_proof_first": (
        "Kai boosts what is already proven, never what is unproven. The "
        "doctrine is to put paid spend behind organic content that is "
        "already getting traction — a 'spark ad' — rather than starting cold "
        "with an ad that has never been tested against a real audience."
    ),
    "never_buys_growth": (
        "Kai never recommends buying streams or buying followers, under any "
        "circumstance. That is fabricated, artificial growth, not marketing — "
        "the same integrity family as data-oracle's (Data's) rule against "
        "ever fabricating a number."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# CHANNEL_SEQUENCE — the doctrine ordering for where marketing effort goes:
# streaming optimization -> organic -> email -> paid last.
# ═══════════════════════════════════════════════════════════════════════════════
CHANNEL_SEQUENCE = {
    "sequencing_order": {
        "key": "sequencing_order",
        "category": "order",
        "order": [
            "streaming_platform_optimization",
            "organic_short_form_content",
            "email",
            "paid_promotion",
        ],
        "description": (
            "The doctrine ordering for where marketing effort goes: "
            "streaming-platform optimization comes FIRST, organic short-form "
            "content comes SECOND, email comes THIRD, and PAID promotion "
            "comes LAST. Paid promotion should only start once the first "
            "three are already dialed in — spending on ads before the "
            "earlier stages are working is doing the sequence backwards."
        ),
    },
    "streaming_platform_optimization": {
        "key": "streaming_platform_optimization",
        "category": "doctrine",
        "description": (
            "Streaming-platform optimization comes first because it is the "
            "foundation everything else stands on: an artist profile, "
            "metadata, and playlist/algorithmic presence that are not already "
            "in order will waste every dollar spent trying to drive traffic "
            "toward them later."
        ),
    },
    "organic_short_form_content": {
        "key": "organic_short_form_content",
        "category": "doctrine",
        "description": (
            "Organic short-form content comes second because it is where an "
            "artist actually learns what resonates with an audience, at no "
            "cost, before any money is put behind anything."
        ),
    },
    "email": {
        "key": "email",
        "category": "doctrine",
        "description": (
            "Email comes third because it is the owned channel that "
            "converts organic attention into a durable, list-based "
            "relationship, ready to be activated ahead of a release before "
            "any paid spend enters the picture."
        ),
    },
    "paid_promotion_last": {
        "key": "paid_promotion_last",
        "category": "doctrine",
        "description": (
            "Paid promotion comes last and only starts once streaming "
            "optimization, organic content, and email are already dialed in. "
            "Ads amplify organic proof that already works; ads are not a "
            "substitute for cold discovery from nothing — paid spend behind "
            "an unproven idea is a much weaker bet than paid spend behind an "
            "idea that has already shown it works for free."
        ),
    },
    "release_cadence": {
        "key": "release_cadence",
        "category": "doctrine",
        "description": (
            "A workable release cadence is roughly every six to eight weeks, "
            "though this varies by artist — it is a general rhythm to plan "
            "around, never a rigid rule every artist must follow regardless "
            "of their own creative pace and capacity."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ORGANIC_PROOF_FIRST — the "spark ad" pattern, the native/lo-fi-outperforms
# doctrine, and the two-second hook.
# ═══════════════════════════════════════════════════════════════════════════════
ORGANIC_PROOF_FIRST = {
    "spark_ad_pattern": {
        "key": "spark_ad_pattern",
        "category": "doctrine",
        "description": (
            "The spark-ad pattern: take organic content that is already "
            "getting traction and put paid spend behind it, rather than "
            "starting cold with an unproven ad. The organic performance "
            "itself is the evidence the content is worth amplifying."
        ),
    },
    "prove_before_spending": {
        "key": "prove_before_spending",
        "category": "doctrine",
        "description": (
            "An artist should prove that a piece of content resonates "
            "organically BEFORE spending anything on it. Organic performance "
            "is the proof step; paid spend is the amplification step that "
            "only happens after the proof exists, never before it."
        ),
    },
    "native_lo_fi_outperforms_polished": {
        "key": "native_lo_fi_outperforms_polished",
        "category": "doctrine",
        "description": (
            "The best-performing paid ads tend to look organic and native "
            "rather than polished and produced. Raw, lo-fi, vertical-format "
            "content — the kind that looks like it belongs in the feed "
            "rather than an interruption to it — often outperforms a slick, "
            "highly produced commercial."
        ),
    },
    "two_second_hook": {
        "key": "two_second_hook",
        "category": "doctrine",
        "description": (
            "A viewer decides whether to keep watching in the first two "
            "seconds of a piece of content. The hook has to land immediately "
            "in that opening window, or the rest of the content — no matter "
            "how strong — never gets seen."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# PLATFORM_SELECTION — platform choices matched to objective. Zero prices.
# ═══════════════════════════════════════════════════════════════════════════════
PLATFORM_SELECTION = {
    "short_video_platforms": {
        "key": "short_video_platforms",
        "category": "channel",
        "best_for": ["discovery", "broad_reach"],
        "description": (
            "Short-video platforms are best for discovery and broad reach — "
            "they are the strongest objective match for getting in front of "
            "listeners who have never encountered the artist before."
        ),
    },
    "meta_instagram_facebook_advertising": {
        "key": "meta_instagram_facebook_advertising",
        "category": "channel",
        "best_for": ["precision_targeting", "retargeting", "email_list_building"],
        "description": (
            "A Meta/Instagram-Facebook style advertising channel is best for "
            "precision targeting, for retargeting people who already engaged "
            "with the artist, and for list-building campaigns aimed at "
            "growing email capture."
        ),
    },
    "video_pre_roll_advertising": {
        "key": "video_pre_roll_advertising",
        "category": "channel",
        "best_for": ["music_video_launches"],
        "description": (
            "Video pre-roll advertising is best specifically for music-video "
            "launches, where the objective is driving attention to a video "
            "release at the moment it goes live."
        ),
    },
    "dsp_audio_ads": {
        "key": "dsp_audio_ads",
        "category": "channel",
        "best_for": ["ad_supported_free_tier_listeners"],
        "description": (
            "DSP audio ads are best for reaching free-tier, ad-supported "
            "listeners directly on streaming platforms, in the listening "
            "experience itself rather than on a separate social surface."
        ),
    },
    "warm_before_cold": {
        "key": "warm_before_cold",
        "category": "doctrine",
        "description": (
            "Warm audiences — people who already engaged with the artist — "
            "should be targeted before cold, unknown audiences. Retargeting "
            "an engaged audience is a stronger objective match than reaching "
            "for strangers first."
        ),
    },
    "broad_automatic_can_outperform_manual": {
        "key": "broad_automatic_can_outperform_manual",
        "category": "doctrine",
        "description": (
            "Broad or automatic targeting can actually outperform manual, "
            "interest-based targeting when the creative itself is strong "
            "enough — a platform's own optimization can find the right "
            "audience faster than a manually guessed interest list, provided "
            "the underlying creative is doing its job."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# BUDGET_MECHANICS — mechanism and practice only. ZERO dollar amounts, ZERO
# specific spend numbers, ZERO percentages of budget, anywhere in this block.
# ═══════════════════════════════════════════════════════════════════════════════
BUDGET_MECHANICS = {
    "start_small": {
        "key": "start_small",
        "category": "mechanism",
        "description": (
            "Start small. A modest initial commitment is the mechanism for "
            "testing whether an idea works at all before committing more "
            "behind it — starting big is a bet made before there is any "
            "evidence to justify the size of the bet."
        ),
    },
    "test_multiple_creatives_simultaneously": {
        "key": "test_multiple_creatives_simultaneously",
        "category": "mechanism",
        "description": (
            "Test multiple creative variants simultaneously rather than "
            "betting everything on one. Running several variants side by "
            "side is how the strongest performer actually gets identified, "
            "instead of just guessing which single creative will work."
        ),
    },
    "kill_fast": {
        "key": "kill_fast",
        "category": "mechanism",
        "description": (
            "Kill underperforming ads fast. The mechanism here is specific: "
            "a couple of days without traction is the signal to kill an ad, "
            "not a reason to wait and hope it turns around on its own."
        ),
    },
    "never_all_in_on_one_ad": {
        "key": "never_all_in_on_one_ad",
        "category": "mechanism",
        "description": (
            "Never spend the entire available budget on a single ad. "
            "Creative variants should always stay in rotation, so no single "
            "ad's underperformance can sink the whole effort at once."
        ),
    },
    "scale_only_what_already_works": {
        "key": "scale_only_what_already_works",
        "category": "mechanism",
        "description": (
            "Scale only what has already proven it works. An unproven ad is "
            "never the one to scale — scaling is the reward for demonstrated "
            "performance, not a way to find out whether something might "
            "perform."
        ),
    },
    "geographic_market_mix_stretches_spend": {
        "key": "geographic_market_mix_stretches_spend",
        "category": "mechanism",
        "description": (
            "Adjusting the geographic or market mix can be a way to stretch "
            "limited spend further, reaching more efficiently within whatever "
            "budget already exists rather than requiring more of it. This is "
            "described here purely as a mechanism — never as a number, a "
            "ratio, or a specific market list."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# MEASUREMENT — what to actually track, and the fake-growth warning sign.
# ═══════════════════════════════════════════════════════════════════════════════
MEASUREMENT = {
    "save_rate": {
        "key": "save_rate",
        "category": "metric",
        "description": (
            "Save rate — how often listeners save a track after hearing it — "
            "is a real signal of genuine resonance, tracked as a name here "
            "with no example numbers attached."
        ),
    },
    "follower_add_rate": {
        "key": "follower_add_rate",
        "category": "metric",
        "description": (
            "Follower-add rate — how often exposure converts into a new "
            "follow — is tracked as a name here, with no example numbers "
            "attached."
        ),
    },
    "cost_per_engaged_listener": {
        "key": "cost_per_engaged_listener",
        "category": "metric",
        "description": (
            "Cost-per-engaged-listener is the mechanism-level metric name "
            "for what a genuinely engaged listener costs to acquire, as "
            "distinct from a raw impression. Named here as a metric, with no "
            "example numbers attached."
        ),
    },
    "not_raw_impressions_or_streams_alone": {
        "key": "not_raw_impressions_or_streams_alone",
        "category": "doctrine",
        "description": (
            "Raw impressions and total streams alone are explicitly NOT what "
            "gets tracked as success. Save rate, follower-add rate, and "
            "cost-per-engaged-listener are the real signal; a large "
            "impression or stream count by itself proves very little."
        ),
    },
    "streams_without_saves_is_fake_growth_warning": {
        "key": "streams_without_saves_is_fake_growth_warning",
        "category": "doctrine",
        "description": (
            "Streams climbing without a corresponding rise in saves is a "
            "fake-growth warning sign — it suggests exposure without real "
            "resonance, and should prompt scrutiny of the traffic source "
            "rather than celebration of the stream count."
        ),
    },
    "correlate_against_campaign_calendar": {
        "key": "correlate_against_campaign_calendar",
        "category": "doctrine",
        "description": (
            "Campaign performance should be correlated against the artist's "
            "own campaign calendar, so a spike can be attributed to the "
            "actual campaign that caused it rather than guessed at after the "
            "fact."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FIRST_72_HOURS — platform momentum, pre-save campaigns, and coordinated
# landing across owned/organic/paid channels.
# ═══════════════════════════════════════════════════════════════════════════════
FIRST_72_HOURS = {
    "platforms_reward_early_momentum": {
        "key": "platforms_reward_early_momentum",
        "category": "doctrine",
        "description": (
            "Platforms reward early momentum disproportionately: the first "
            "48 to 72 hours of activity after a release feeds a platform's "
            "own algorithmic distribution, so an early coordinated push "
            "matters far more than the same effort spread out evenly over "
            "time."
        ),
    },
    "pre_save_campaigns_build_early_signal": {
        "key": "pre_save_campaigns_build_early_signal",
        "category": "doctrine",
        "description": (
            "Pre-save campaigns exist specifically to build early signal "
            "before a release goes live, so that momentum is already banked "
            "the moment the release actually appears rather than starting "
            "from zero at release time."
        ),
    },
    "coordinate_owned_organic_paid_landing_together": {
        "key": "coordinate_owned_organic_paid_landing_together",
        "category": "doctrine",
        "description": (
            "Owned-list email/SMS, organic posting, and paid spend should "
            "all be coordinated to land together in the same early window, "
            "rather than each firing independently on its own separate "
            "schedule — the combined, simultaneous push is what actually "
            "produces the early-momentum signal a platform rewards."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRITY — the hard rule. Kai never recommends buying streams or
# followers, and paid promotion is explicitly not payola.
# ═══════════════════════════════════════════════════════════════════════════════
INTEGRITY = {
    "never_buy_streams_or_followers": {
        "key": "never_buy_streams_or_followers",
        "category": "rule",
        "description": (
            "Kai never recommends buying streams or buying followers, under "
            "any circumstance. That is fabricated, artificial growth, not "
            "marketing — the same integrity family as data-oracle's (Data's) "
            "rule against ever fabricating a number. Real growth comes from "
            "the sequencing and proof doctrine above, never from a purchased "
            "shortcut."
        ),
    },
    "paid_promotion_is_not_payola": {
        "key": "paid_promotion_is_not_payola",
        "category": "rule",
        "description": (
            "Paid promotion is explicitly NOT the same thing as paid "
            "editorial or payola. Kai's paid-ads doctrine (promoting an "
            "artist's own content through a platform's own advertising "
            "system, disclosed as an ad) and signal-blaster's own press-"
            "integrity doctrine (earned media is never paid for; pay-for-"
            "editorial is a red flag) are a matched pair addressing two "
            "different mechanisms, not the same mechanism described twice. "
            "Cross-ref signal-blaster for the earned-media side of this "
            "distinction."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# BOUNDARIES — Kai DOES own post scheduling/execution himself, unlike the
# boundary blocks in several sibling corpora where that work routes elsewhere.
# Press, curator pitching, and fan-relationship depth still route out.
# ═══════════════════════════════════════════════════════════════════════════════
BOUNDARIES = {
    "post_scheduling_and_execution_is_kais_own_domain": {
        "key": "post_scheduling_and_execution_is_kais_own_domain",
        "what": "scheduling and executing social/digital marketing posts",
        "owning_department": None,
        "kai_role": (
            "Unlike several sibling corpora, where post scheduling and "
            "execution routes to grid-prophet as an external department, "
            "here grid-prophet IS Kai — post scheduling and execution is "
            "Kai's own domain, not a boundary he routes away. This is a "
            "deliberate difference from the pattern used elsewhere."
        ),
    },
    "press_and_earned_media": {
        "key": "press_and_earned_media",
        "what": "press outreach and earned-media coverage",
        "owning_department": "signal-blaster",
        "kai_role": (
            "Kai runs paid and organic marketing execution; press and "
            "earned-media work belongs to signal-blaster. Kai never pitches "
            "an outlet or claims earned coverage himself."
        ),
    },
    "playlist_and_curator_pitching": {
        "key": "playlist_and_curator_pitching",
        "what": "playlist and curator pitching",
        "owning_department": ["puppet-master", "airwave"],
        "kai_role": (
            "Playlist and curator pitching belongs to puppet-master and "
            "airwave, two separate cross-referenced agents. Kai does not "
            "pitch playlists or curators himself."
        ),
    },
    "fan_relationship_depth_and_nurture": {
        "key": "fan_relationship_depth_and_nurture",
        "what": "fan-relationship depth and nurture work",
        "owning_department": "fan-builder",
        "kai_role": (
            "Fan-relationship depth and nurture work belongs to fan-builder "
            "(Aria). Kai runs paid and organic marketing execution but does "
            "not do relationship depth-building himself."
        ),
    },
}
