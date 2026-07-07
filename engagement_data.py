"""
PLMKR Aria (fan-builder) — structured fan-engagement data (Aria's real
knowledge base).

Unit 1 (data-only): the researched fan-engagement / superfan-cultivation map,
encoded as structured records.
Source of truth: ARIA_ENGAGEMENT_MAP_v1 (researched in chat July 6 2026,
web-sourced: fan-funnel and fan-tier doctrine, the "1,000 true fans" depth-
over-scale principle, superfan behavioral-identification practice, owned-vs-
rented channel doctrine, and sustainable weekly / release-cycle engagement
cadence for independent artists).

WHAT THIS MODULE IS (and is NOT):
  - DATA ONLY. No functions, no filtering logic, no I/O, no network, no
    secrets. The service layer (built in a later unit) does all lookup /
    scaffold assembly. No engagement logic is encoded as code here — only as
    data records for the service to read.
  - Every record is a plain, JSON-serializable dict so the service can pass
    fields straight through into a scaffold without transformation.

HARD RULES honored here:
  - ZERO currency amounts or symbols anywhere. Fan engagement touches ticket
    sales and merch purchases, so this module is scrupulous about it:
    mechanisms and doctrine only, never a figure.
  - ZERO fan-count numbers presented as doctrine. THOUSAND_TRUE_FANS states
    the depth-over-scale PRINCIPLE only — no specific count of fans is
    asserted as a target.
  - PRIORITIZATION, NOT EQUAL ENERGY: FAN_FUNNEL and ARIA_DOCTRINE both encode
    that superfans are a small percentage of the audience who generate most
    of the word-of-mouth, ticket sales, and merch purchases, and therefore
    deserve prioritized attention — spreading equal energy across every tier
    is named explicitly as the classic mistake.
  - BOUNDARIES: post scheduling/execution belongs to grid-prophet (Kai,
    digital marketing); monetizing the fanbase belongs to mobile-monetize
    (Mo, monetization); actual email/SMS SENDING infrastructure does not
    exist yet — Aria must never fake or simulate sending a message, only
    draft/plan copy and cadence.
  - Unknowns and future integrations are described as mechanisms or open
    gaps, never a guessed capability.

SCHEMA:
  ARIA_DOCTRINE -> framing strings on what Aria is and is not
  FAN_FUNNEL[key] -> key, category ("funnel_stage" | "fan_tier" | "doctrine"),
    description
  THOUSAND_TRUE_FANS[key] -> key, category ("principle"), description
  SUPERFAN_IDENTIFICATION[key] -> key,
    category ("behavioral_signal" | "practice"), description
  OWNED_CHANNELS[key] -> key, category ("owned" | "rented" | "doctrine"),
    description
  CADENCE_SPEC[key] -> key, cadence_type ("weekly" | "per_release_cycle" |
    "doctrine"), tasks (list), description
  WHAT_WASTES_TIME[key] -> key, description
  BOUNDARIES[key] -> key, what, owning_department (None or a cross-ref agent
    id), aria_role
"""

# ── Standing framing strings (data, not logic) ────────────────────────────────
# What Aria is and is not — surfaced verbatim by the service so no output can
# be mistaken for a scheduling tool, a monetization tool, or a live sender.
ARIA_DOCTRINE = {
    "depth_over_scale": (
        "A modest number of genuinely engaged fans can sustain a career. Aria "
        "optimizes for depth of engagement, not breadth of audience — a "
        "smaller, truly connected fan base outperforms a larger, passive one."
    ),
    "superfans_first": (
        "Superfans are a small percentage of the audience who generate most "
        "of the word-of-mouth, ticket sales, and merch purchases. They "
        "deserve prioritized attention. Giving every fan tier equal energy is "
        "the classic mistake — Aria names it as a mistake, not a neutral "
        "choice."
    ),
    "owned_over_rented": (
        "Owned channels (email and SMS) are the inner circle where the "
        "artist controls the relationship directly. Social media is a rented "
        "channel and functions as top-of-funnel only, because the platform's "
        "algorithm — not the artist — controls reach there."
    ),
    "never_simulates_sending": (
        "Aria drafts copy, cadence, and audience strategy. Aria never claims "
        "to have sent an email or a text message, because no email/SMS "
        "sending infrastructure is wired up yet. That capability is a future "
        "integration, not something Aria fakes or simulates today."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# FAN_FUNNEL — the four funnel stages, the three fan tiers, and the
# prioritization doctrine that ties them together.
# ═══════════════════════════════════════════════════════════════════════════════
FAN_FUNNEL = {
    "discovery": {
        "key": "discovery",
        "category": "funnel_stage",
        "description": (
            "Discovery is the stage where a listener first encounters the "
            "artist — through algorithmic recommendation, a playlist "
            "placement, a support-slot show, or a friend's share. The "
            "listener has no relationship with the artist yet. The right "
            "strategy here is broad, low-friction exposure, not personal "
            "outreach."
        ),
    },
    "interest": {
        "key": "interest",
        "category": "funnel_stage",
        "description": (
            "Interest is the stage where a listener follows, saves, or "
            "returns to the artist's content without yet being personally "
            "invested. The right strategy here is light-touch, recognizable, "
            "consistent content that earns a second and third look — not the "
            "deep personal attention reserved for connected fans."
        ),
    },
    "connection": {
        "key": "connection",
        "category": "funnel_stage",
        "description": (
            "Connection is the stage where a fan begins two-way engagement: "
            "commenting, replying to a story, attending a first show, "
            "sending a direct message. The right strategy here is genuine, "
            "individual acknowledgment — a real reply, not a template — "
            "because this is where a passive follower starts becoming a true "
            "fan."
        ),
    },
    "advocacy": {
        "key": "advocacy",
        "category": "funnel_stage",
        "description": (
            "Advocacy is the stage where a fan actively promotes the artist "
            "to others — unprompted sharing, bringing friends to a show, "
            "defending the artist in a comment section. The right strategy "
            "here is recognition and privileged access, because advocacy is "
            "the behavior that compounds an audience without paid reach."
        ),
    },
    "casual": {
        "key": "casual",
        "category": "fan_tier",
        "description": (
            "A casual fan follows or listens passively. They may enjoy the "
            "music but do not yet engage, comment, or return reliably. Casual "
            "fans are the largest tier by count and the lowest-leverage "
            "target for personal, one-to-one attention."
        ),
    },
    "true_fan": {
        "key": "true_fan",
        "category": "fan_tier",
        "description": (
            "A true fan engages with regularity: they comment sometimes, "
            "attend shows when the artist tours nearby, and buy merch "
            "occasionally. They are a meaningfully smaller tier than casual "
            "fans and respond well to consistent, recognizable engagement."
        ),
    },
    "superfan": {
        "key": "superfan",
        "category": "fan_tier",
        "description": (
            "A superfan is a small percentage of the total audience who "
            "generates a disproportionate share of word-of-mouth, ticket "
            "sales, and merch purchases. Because their impact is outsized "
            "relative to their number, superfans deserve prioritized, "
            "personal attention rather than the same generic treatment given "
            "to every other tier."
        ),
    },
    "tier_and_stage_prioritization_doctrine": {
        "key": "tier_and_stage_prioritization_doctrine",
        "category": "doctrine",
        "description": (
            "Each funnel stage and each fan tier needs a different strategy — "
            "there is no single engagement tactic that serves discovery and "
            "advocacy equally, or casual fans and superfans equally. "
            "Superfans are a small percentage of the audience who generate "
            "most of the word-of-mouth, ticket sales, and merch purchases, so "
            "they deserve prioritized attention. Giving every tier equal "
            "energy — spreading the same effort across casual fans, true "
            "fans, and superfans alike — is the classic mistake Aria is built "
            "to avoid."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# THOUSAND_TRUE_FANS — the depth-over-scale principle. No fan counts, no
# figures — principle only.
# ═══════════════════════════════════════════════════════════════════════════════
THOUSAND_TRUE_FANS = {
    "depth_over_scale_principle": {
        "key": "depth_over_scale_principle",
        "category": "principle",
        "description": (
            "A modest number of genuinely engaged fans can sustain an "
            "independent career. Depth of engagement beats scale of "
            "audience — a smaller group of fans who reliably show up, buy, "
            "and share outperforms a much larger group of passive followers "
            "who do neither."
        ),
    },
    "engagement_compounds_before_reach_does": {
        "key": "engagement_compounds_before_reach_does",
        "category": "principle",
        "description": (
            "Chasing raw audience size before cultivating genuine engagement "
            "gets the sequence backwards. A base of deeply engaged fans is "
            "what makes any later growth in reach durable, because those "
            "fans are the ones who carry the artist's name to new listeners "
            "through word-of-mouth."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SUPERFAN_IDENTIFICATION — behavioral signals plus the nurture practice.
# ═══════════════════════════════════════════════════════════════════════════════
SUPERFAN_IDENTIFICATION = {
    "comments_on_every_post": {
        "key": "comments_on_every_post",
        "category": "behavioral_signal",
        "description": (
            "A fan who comments on every post, not just the occasional one, "
            "is signaling a level of attention well above the casual tier."
        ),
    },
    "shares_unprompted": {
        "key": "shares_unprompted",
        "category": "behavioral_signal",
        "description": (
            "A fan who shares the artist's content or news without being "
            "asked to is doing unpaid advocacy work — one of the clearest "
            "superfan signals there is."
        ),
    },
    "buys_repeatedly": {
        "key": "buys_repeatedly",
        "category": "behavioral_signal",
        "description": (
            "A fan who buys tickets, merch, or releases more than once, "
            "rather than a single one-time purchase, is showing sustained "
            "commitment rather than a one-off impulse."
        ),
    },
    "creates_fan_content": {
        "key": "creates_fan_content",
        "category": "behavioral_signal",
        "description": (
            "A fan who creates their own content about the artist — fan art, "
            "cover videos, edits, playlists — is investing creative effort "
            "that casual and true fans typically do not."
        ),
    },
    "saves_and_repeat_listens_within_48_hours": {
        "key": "saves_and_repeat_listens_within_48_hours",
        "category": "behavioral_signal",
        "description": (
            "A fan who saves a new release and returns to repeat-listen "
            "within the first 48 hours of it going live is showing an "
            "immediacy of attention that is a strong early superfan signal, "
            "well before broader streaming numbers settle in."
        ),
    },
    "track_and_recognize_practice": {
        "key": "track_and_recognize_practice",
        "category": "practice",
        "description": (
            "The practice doctrine: track which fans show these signals, "
            "recognize them individually rather than treating them as an "
            "anonymous aggregate, and give them more personal attention than "
            "the rest of the audience receives."
        ),
    },
    "private_small_group_access_nurture_pattern": {
        "key": "private_small_group_access_nurture_pattern",
        "category": "practice",
        "description": (
            "The nurture pattern for identified superfans is private, "
            "small-group access: early listens ahead of public release, a "
            "vote on an upcoming decision, or beta/early access to new merch. "
            "This access is deliberately not offered to the whole audience — "
            "it is the reward mechanism for the fans already showing superfan "
            "signals."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# OWNED_CHANNELS — owned (email/SMS) vs rented (social) channel doctrine.
# ═══════════════════════════════════════════════════════════════════════════════
OWNED_CHANNELS = {
    "owned_channels_email_sms": {
        "key": "owned_channels_email_sms",
        "category": "owned",
        "description": (
            "Email and SMS are owned channels: the artist controls the "
            "relationship and the list directly, independent of any "
            "platform's policies or algorithm. Nothing about reach on an "
            "owned channel can be throttled by a third party the way social "
            "reach can."
        ),
    },
    "rented_channels_social_media": {
        "key": "rented_channels_social_media",
        "category": "rented",
        "description": (
            "Social media is a rented channel: the platform's algorithm, not "
            "the artist, controls how many people actually see any given "
            "post. The artist can be de-prioritized, throttled, or cut off "
            "entirely by a policy change outside their control."
        ),
    },
    "subscribers_get_news_first_doctrine": {
        "key": "subscribers_get_news_first_doctrine",
        "category": "doctrine",
        "description": (
            "List subscribers must get news FIRST — before it appears on "
            "social media. If a subscriber sees the same announcement on "
            "social before or at the same time as their inbox, there is no "
            "reason for them to stay subscribed to the owned channel at all."
        ),
    },
    "social_as_top_of_funnel_doctrine": {
        "key": "social_as_top_of_funnel_doctrine",
        "category": "doctrine",
        "description": (
            "Social media is framed as top-of-funnel only: a discovery and "
            "interest surface that feeds the funnel, not the inner circle. "
            "The owned channels — email and SMS — are the inner circle where "
            "the deepest relationship with a fan actually lives."
        ),
    },
    "genuine_two_way_replies_doctrine": {
        "key": "genuine_two_way_replies_doctrine",
        "category": "doctrine",
        "description": (
            "Genuine two-way replies — real, individual sentences written to "
            "a specific fan, never a templated response — create durable "
            "loyalty. A fan who receives a real reply remembers it far longer "
            "than any single post they scrolled past."
        ),
    },
    "in_person_merch_table_doctrine": {
        "key": "in_person_merch_table_doctrine",
        "category": "doctrine",
        "description": (
            "An in-person merch table at a show creates superfans at a rate "
            "online effort alone cannot match. A face-to-face moment — a "
            "conversation, a signature, a photo — converts a true fan into a "
            "superfan faster than any amount of online engagement can "
            "replicate."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# CADENCE_SPEC — weekly and per-release-cycle engagement cadence, plus the
# consistency-over-intensity doctrine.
# ═══════════════════════════════════════════════════════════════════════════════
CADENCE_SPEC = {
    "weekly_cadence": {
        "key": "weekly_cadence",
        "cadence_type": "weekly",
        "tasks": [
            "review comments across recent posts",
            "spot new superfans showing behavioral signals",
            "reshare fan-created content",
        ],
        "description": (
            "A small, consistent weekly block of time: review comments, spot "
            "new superfans as they emerge, and reshare fan content. This is "
            "meant to be sustainable in a fixed amount of time each week, not "
            "an open-ended commitment."
        ),
    },
    "per_release_cycle_cadence": {
        "key": "per_release_cycle_cadence",
        "cadence_type": "per_release_cycle",
        "tasks": [
            "send an early-access email to the owned list",
            "run one poll or vote with the audience",
            "post several behind-the-work posts across the cycle",
        ],
        "description": (
            "Per release cycle: send an early-access email ahead of the "
            "public release, run one poll or vote so fans participate in a "
            "decision, and post several behind-the-work posts across the "
            "cycle rather than a single day-of announcement."
        ),
    },
    "consistency_over_intensity_doctrine": {
        "key": "consistency_over_intensity_doctrine",
        "cadence_type": "doctrine",
        "tasks": [],
        "description": (
            "Consistency at a sustainable pace beats short bursts of "
            "intensity followed by silence. A fan base built on a steady "
            "weekly and per-cycle rhythm trusts the artist to keep showing "
            "up; a fan base whipsawed between a flurry of posts and long "
            "silence learns not to expect anything."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# WHAT_WASTES_TIME — low-leverage engagement patterns to avoid.
# ═══════════════════════════════════════════════════════════════════════════════
WHAT_WASTES_TIME = {
    "replying_to_everything_at_scale": {
        "key": "replying_to_everything_at_scale",
        "description": (
            "Trying to reply to every single comment or message at scale, "
            "rather than focusing engagement on fans already showing "
            "superfan signals, spreads limited time across the least "
            "leveraged interactions instead of the highest-leverage ones."
        ),
    },
    "unplanned_livestreams": {
        "key": "unplanned_livestreams",
        "description": (
            "Doing livestreams with no plan or purpose burns a large block "
            "of engagement time for an uncertain, often low, return, "
            "compared to the planned weekly and per-release-cycle cadence."
        ),
    },
    "chasing_vanity_metrics": {
        "key": "chasing_vanity_metrics",
        "description": (
            "Optimizing for follower counts or like counts rather than the "
            "depth-of-engagement signals that actually identify true fans "
            "and superfans is time spent on a number that does not predict "
            "ticket sales, merch purchases, or word-of-mouth."
        ),
    },
    "responding_to_trolls": {
        "key": "responding_to_trolls",
        "description": (
            "Engaging with bad-faith commenters draws attention and time away "
            "from genuine fans, and rarely changes the troll's behavior — it "
            "is time that could go to a real reply for a real fan instead."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# BOUNDARIES — Aria drafts strategy and copy; she does not schedule/execute
# posts, does not own monetization, and does not send anything yet.
# ═══════════════════════════════════════════════════════════════════════════════
BOUNDARIES = {
    "post_scheduling_and_execution": {
        "key": "post_scheduling_and_execution",
        "what": "scheduling and executing social media posts",
        "owning_department": "grid-prophet",
        "aria_role": (
            "Aria plans fan-engagement strategy and cadence, but the actual "
            "scheduling and execution of posts belongs to grid-prophet (Kai, "
            "digital marketing). Aria hands off content and timing "
            "recommendations rather than posting anything herself."
        ),
    },
    "monetizing_the_fanbase": {
        "key": "monetizing_the_fanbase",
        "what": "monetizing the fanbase directly",
        "owning_department": "mobile-monetize",
        "aria_role": (
            "Aria builds and nurtures fan relationships, but turning that "
            "fanbase into revenue is the monetization doctrine owned by "
            "mobile-monetize (Mo, monetization). Aria never presents her own "
            "engagement work as a monetization plan."
        ),
    },
    "email_sms_sending_infrastructure": {
        "key": "email_sms_sending_infrastructure",
        "what": "actually sending email or SMS messages to fans",
        "owning_department": None,
        "aria_role": (
            "Real email/SMS sending infrastructure is a future integration "
            "that does not exist yet. Aria must never fake or simulate "
            "sending a message, never claim a message has gone out, and "
            "never report delivery or open statistics as if a send already "
            "happened. Aria drafts copy and cadence only, until that "
            "infrastructure is actually wired up."
        ),
    },
}
