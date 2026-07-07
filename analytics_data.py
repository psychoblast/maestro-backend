"""
PLMKR Data (data-oracle) — structured streaming/audience-analytics doctrine
(Data's real knowledge base).

Unit 1 (data-only): the researched streaming-metric-definition, interpretation,
and reporting-integrity map, encoded as structured records.
Source of truth: DATA_ANALYTICS_MAP_v1 (researched in chat July 6 2026,
web-sourced: DSP streaming-metric definitions, audience-analytics
interpretation conventions, and reporting-integrity doctrine for independent
artists).

WHAT THIS MODULE IS (and is NOT):
  - DATA ONLY. No functions, no filtering logic, no I/O, no network, no
    secrets. The service layer (built in a later unit) does all lookup /
    scaffold assembly. No diagnosis logic is encoded as code here — only as
    data records for the service to read.
  - Every record is a plain, JSON-serializable dict so the service can pass
    fields straight through into a scaffold without transformation.

HARD RULES honored here:
  - ZERO currency amounts or symbols anywhere. This domain is analytics, not
    money, so no currency symbol of any kind appears anywhere in this
    module.
  - INTEGRITY IS THE CENTRAL DOCTRINE: Data NEVER fabricates, estimates, or
    extrapolates an artist's own numbers. Every stat is either
    artist-supplied or explicitly marked as a gap — never guessed, never
    rounded up, never invented to fill a silence. Data also never endorses
    looping or incentivizing streams; that activity is artificial and gets
    filtered or penalized by the platforms themselves.
  - NOTES, NOT VERDICTS: every interpretation band in this corpus is framed
    as a contextual note the artist can use, never as a pass/fail judgment
    on the work. Context always matters more than the band alone.
  - BOUNDARIES: Data surfaces the numbers and the diagnosis. Acting on that
    diagnosis — running a campaign, booking a show, changing a release
    strategy — belongs to the owning department (grid-prophet, fan-builder,
    mobile-monetize, tour-commander). Data never claims their execution
    work.
  - Unknowns are described as mechanisms or open questions, never a guessed
    number or a guessed policy.

SCHEMA:
  DATA_DOCTRINE -> framing strings on what Data is and is not
  METRIC_DEFINITIONS[key] -> key, metric_name, description, formula (optional)
  INTERPRETATION_BANDS[key] -> key, band_type, range_label, description
  SOURCE_BREAKDOWN[key] -> key, source_type, description
  DIAGNOSIS_PAIRS[key] -> key, pattern, description
  QUALITY_VS_VANITY[key] -> key, metrics (list), description
  STAKEHOLDER_FRAMING[key] -> key, stakeholder, wants (list), description
  INTEGRITY[key] -> key, rule, description
  BOUNDARIES[key] -> key, what, owning_departments (list), description
"""

# ── Standing framing strings (data, not logic) ────────────────────────────────
# What Data is and is not — surfaced verbatim by the service so no output can
# be mistaken for a marketing plan, a booking decision, or a fabricated stat.
DATA_DOCTRINE = {
    "never_fabricate_numbers": (
        "Data reports and diagnoses using only artist-supplied numbers. Data "
        "never fabricates, estimates, or extrapolates an artist's own "
        "streaming or audience figures — a missing figure is marked as a gap, "
        "never guessed."
    ),
    "insights_not_actions": (
        "Data surfaces the numbers, the diagnosis, and the contextual notes. "
        "Data does not execute marketing, booking, or monetization actions "
        "itself — that execution belongs to the owning department, not to "
        "Data."
    ),
    "notes_not_verdicts": (
        "Every interpretation band Data cites is a contextual note the "
        "artist can use to think about their numbers, never a pass/fail "
        "verdict on the work itself. Context always matters more than the "
        "band alone."
    ),
    "no_dollar_figures": (
        "Data's domain is streaming and audience analytics, not money. Data "
        "never states a dollar figure, a revenue amount, or a fee amount of "
        "any kind."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# METRIC_DEFINITIONS — the base vocabulary every other block in this corpus is
# built on top of.
# ═══════════════════════════════════════════════════════════════════════════════
METRIC_DEFINITIONS = {
    "stream": {
        "key": "stream",
        "metric_name": "stream",
        "description": (
            "A stream is counted once a listener has played a track for at "
            "least 30 seconds. A play that ends before the 30-second mark "
            "counts instead as a skip, and a skip is a negative algorithmic "
            "signal to the platform, not simply a non-event."
        ),
    },
    "monthly_listeners": {
        "key": "monthly_listeners",
        "metric_name": "monthly_listeners",
        "description": (
            "Monthly listeners counts the unique listeners who played the "
            "artist at least once within a rolling 28-day window. It is a "
            "unique-listener count, not a play count, and the window rolls "
            "forward continuously rather than resetting on a calendar month."
        ),
    },
    "saves": {
        "key": "saves",
        "metric_name": "saves",
        "description": (
            "A save is a listener adding a track to their own library or to "
            "a playlist. Saves are the top engagement signal in this "
            "corpus — a save is a deliberate action a passive stream is not."
        ),
    },
    "followers": {
        "key": "followers",
        "metric_name": "followers",
        "description": (
            "Followers are the closest available proxy for an artist's "
            "actual fans. A follower has opted in to being notified about "
            "future releases, which a passive listener has not."
        ),
    },
    "save_rate": {
        "key": "save_rate",
        "metric_name": "save_rate",
        "description": (
            "Save rate is saves divided by streams. Save rate is always "
            "artist-computed from the artist's own supplied figures — Data "
            "never invents, estimates, or extrapolates a save rate on its "
            "own."
        ),
        "formula": "saves / streams",
    },
    "streams_per_listener_ratio": {
        "key": "streams_per_listener_ratio",
        "metric_name": "streams_per_listener_ratio",
        "description": (
            "Streams-per-listener ratio is streams divided by monthly "
            "listeners. It is the core repeat-engagement signal used across "
            "the interpretation bands: a low ratio reads as broad but "
            "shallow reach, a high ratio reads as a smaller audience "
            "listening back repeatedly."
        ),
        "formula": "streams / monthly_listeners",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# INTERPRETATION_BANDS — contextual NOTES, never verdicts. Every entry says so
# explicitly, and the ratio bands additionally carry a "context matters"
# caveat.
# ═══════════════════════════════════════════════════════════════════════════════
INTERPRETATION_BANDS = {
    "ratio_passive_reach": {
        "key": "ratio_passive_reach",
        "band_type": "streams_per_listener_ratio",
        "range_label": "1:1-1:2",
        "description": (
            "A streams-per-listener ratio in the 1:1-1:2 range reads as "
            "passive reach — the audience is hearing the music but is not "
            "yet listening back repeatedly. This is a note, not a verdict, "
            "and context matters: a brand-new release can sit here and "
            "still be healthy."
        ),
    },
    "ratio_moderate_engagement": {
        "key": "ratio_moderate_engagement",
        "band_type": "streams_per_listener_ratio",
        "range_label": "1:3-1:5",
        "description": (
            "A ratio in the 1:3-1:5 range reads as moderate engagement — "
            "listeners are coming back for repeat plays. This is a note, "
            "not a verdict, and context matters: catalog age, genre, and "
            "release cadence all shift where a healthy band actually sits."
        ),
    },
    "ratio_strong_fanbase_activity": {
        "key": "ratio_strong_fanbase_activity",
        "band_type": "streams_per_listener_ratio",
        "range_label": "1:6+",
        "description": (
            "A ratio of 1:6 or higher reads as strong fanbase activity — a "
            "smaller audience returning often enough to drive a high ratio "
            "on its own. This is a note, not a verdict, and context "
            "matters: a small, devoted niche audience can produce this "
            "band just as easily as a large one."
        ),
    },
    "skip_rate_high": {
        "key": "skip_rate_high",
        "band_type": "skip_rate",
        "range_label": "40%+",
        "description": (
            "A skip rate of 40% or higher is a note, not a verdict: it "
            "means the track is not hooking listeners, and the two most "
            "common mechanisms behind it are an intro that runs too long "
            "before the hook, or the track landing on wrong-audience "
            "playlists that do not match the listener's taste."
        ),
    },
    "skip_rate_normal": {
        "key": "skip_rate_normal",
        "band_type": "skip_rate",
        "range_label": "25%-40%",
        "description": (
            "A skip rate between 25% and 40% is a note, not a verdict: it "
            "sits in the normal range and does not by itself indicate a "
            "problem with the track or its placement."
        ),
    },
    "skip_rate_strong": {
        "key": "skip_rate_strong",
        "band_type": "skip_rate",
        "range_label": "under 25%",
        "description": (
            "A skip rate under 25% is a note, not a verdict: it reads as "
            "strong retention, and a track sitting here is a reasonable "
            "candidate to prioritize for promotion."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SOURCE_BREAKDOWN — where the streams actually come from, and what each
# source mechanism implies.
# ═══════════════════════════════════════════════════════════════════════════════
SOURCE_BREAKDOWN = {
    "profile_catalog_streams": {
        "key": "profile_catalog_streams",
        "source_type": "profile_catalog_streams",
        "description": (
            "Profile and catalog streams are plays that originate from the "
            "artist's own profile page or catalog rather than a playlist or "
            "algorithmic feed. A share of 30% or more from this source is "
            "the strongest signal available — it means fans are seeking the "
            "artist out directly rather than encountering the music "
            "passively."
        ),
    },
    "algorithmic": {
        "key": "algorithmic",
        "source_type": "algorithmic",
        "description": (
            "Algorithmic streams come from platform-generated recommendation "
            "feeds and auto-generated radio. This source can drive real "
            "growth, but it is volatile — it can disappear as quickly as it "
            "appeared once the algorithm's attention moves on."
        ),
    },
    "editorial": {
        "key": "editorial",
        "source_type": "editorial",
        "description": (
            "Editorial streams come from platform-curated playlists chosen "
            "by human editors. This source brings real exposure, but it is "
            "exposure the artist does not control — placement and removal "
            "are both editorial decisions made elsewhere."
        ),
    },
    "listener_playlists": {
        "key": "listener_playlists",
        "source_type": "listener_playlists",
        "description": (
            "Listener-playlist streams come from playlists built by "
            "ordinary fans rather than the platform or an editor. This "
            "source reflects organic fan growth and correlates strongly "
            "with saves, since a fan has to already value the track enough "
            "to add it to a playlist of their own."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# DIAGNOSIS_PAIRS — recurring patterns across the metrics above, and what each
# pattern implies (never a fabricated number, only a named pattern).
# ═══════════════════════════════════════════════════════════════════════════════
DIAGNOSIS_PAIRS = {
    "high_streams_low_saves": {
        "key": "high_streams_low_saves",
        "pattern": "high_streams_low_saves",
        "description": (
            "High streams paired with a low save rate is a retention "
            "problem: the track is reaching listeners but is not making "
            "enough of them want to keep it. The fix belongs downstream of "
            "the diagnosis, not to Data."
        ),
    },
    "high_saves_low_streams": {
        "key": "high_saves_low_streams",
        "pattern": "high_saves_low_streams",
        "description": (
            "A high save rate paired with low overall streams is a "
            "discovery problem — the listeners who do find the track love "
            "it, but not enough listeners are finding it in the first "
            "place. This is a different problem, and a different fix, from "
            "high_streams_low_saves."
        ),
    },
    "playlist_spike_then_ratio_improves": {
        "key": "playlist_spike_then_ratio_improves",
        "pattern": "playlist_spike_then_ratio_improves",
        "description": (
            "A playlist placement produces a short-term spike in raw "
            "streams that temporarily depresses the streams-per-listener "
            "ratio, because the spike brings in many one-time listeners at "
            "once. This is an exposure-first pattern, normal for small "
            "artists, and the ratio typically improves again once the "
            "playlist spike rolls off and the remaining audience is the "
            "more engaged core."
        ),
    },
    "followers_stay_listeners_fall": {
        "key": "followers_stay_listeners_fall",
        "pattern": "followers_stay_listeners_fall",
        "description": (
            "Followers can stay flat or keep growing even as monthly "
            "listeners dip in a given window. Followers persist because "
            "following is a one-time opt-in decision, while monthly "
            "listeners is a rolling, month-to-month measure of active "
            "listening that naturally rises and falls with release "
            "cadence."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY_VS_VANITY — which metrics are surface-level vanity signals and which
# are the quality signals worth actually tracking.
# ═══════════════════════════════════════════════════════════════════════════════
QUALITY_VS_VANITY = {
    "vanity_metrics": {
        "key": "vanity_metrics",
        "metrics": ["total_streams", "raw_follower_counts"],
        "description": (
            "Total streams and raw follower counts are vanity metrics — "
            "large numbers that look impressive on their own but say "
            "nothing about whether the audience behind them is actually "
            "engaged. A small engaged audience beats a large passive one, "
            "and vanity metrics alone cannot tell the two apart."
        ),
    },
    "quality_metrics": {
        "key": "quality_metrics",
        "metrics": ["saves", "follows", "listen_through", "follower_to_listener_ratio"],
        "description": (
            "Saves, follows, listen-through, and the follower-to-listener "
            "ratio are the quality metrics — signals that reflect actual "
            "engagement rather than raw reach. A small engaged audience "
            "beats a large passive one, and these are the numbers that "
            "actually show which kind of audience an artist has."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# STAKEHOLDER_FRAMING — the same underlying numbers, framed for who is
# actually asking.
# ═══════════════════════════════════════════════════════════════════════════════
STAKEHOLDER_FRAMING = {
    "venues_and_agents": {
        "key": "venues_and_agents",
        "stakeholder": "venues_and_agents",
        "wants": ["listeners_in_their_city", "draw_evidence"],
        "description": (
            "Venues and booking agents want to see listeners concentrated "
            "in their specific city and concrete draw evidence — proof "
            "there is an audience in that room's market, not just a global "
            "total."
        ),
    },
    "labels_and_ar": {
        "key": "labels_and_ar",
        "stakeholder": "labels_and_ar",
        "wants": ["growth_trend", "save_rate", "source_mix", "follower_ratio"],
        "description": (
            "Labels and A&R want the growth trend over time, the save "
            "rate, the source mix across profile/algorithmic/editorial/"
            "listener-playlist streams, and the follower-to-listener "
            "ratio — a fuller picture of trajectory and engagement quality, "
            "not a single snapshot number."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRITY — the hard rules. This is the single most important block in the
# corpus: Data never loops streams, and Data never fabricates a number.
# ═══════════════════════════════════════════════════════════════════════════════
INTEGRITY = {
    "never_loop_or_incentivize_streams": {
        "key": "never_loop_or_incentivize_streams",
        "rule": "never_loop_or_incentivize_streams",
        "description": (
            "Data never recommends looping a track or incentivizing "
            "streams in any way. Looped or incentivized streams are "
            "artificial activity, and platforms actively detect and filter "
            "or penalize exactly this kind of artificial pattern."
        ),
    },
    "never_fabricate_numbers": {
        "key": "never_fabricate_numbers",
        "rule": "never_fabricate_numbers",
        "description": (
            "Data never fabricates, estimates, or extrapolates an artist's "
            "own numbers. This is the single most important doctrine in "
            "this corpus. Every stat Data cites is either "
            "[ARTIST-SUPPLIED:metrics] when the artist has supplied it, or "
            "explicitly marked [NEEDS:x] when it is absent — never a "
            "guess, never a rounded estimate, never a number invented to "
            "fill a silence."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# BOUNDARIES — Data surfaces the numbers and the diagnosis; it does not
# execute the resulting marketing, booking, or monetization work itself.
# ═══════════════════════════════════════════════════════════════════════════════
BOUNDARIES = {
    "acting_on_insights": {
        "key": "acting_on_insights",
        "what": (
            "acting on a diagnosis by running a campaign, booking a show, "
            "or changing a release strategy"
        ),
        "owning_departments": [
            "grid-prophet",
            "fan-builder",
            "mobile-monetize",
            "tour-commander",
        ],
        "description": (
            "Data surfaces the numbers and the diagnosis; acting on that "
            "insight belongs to the owning department, not to Data. Digital "
            "marketing execution belongs to kai (grid-prophet); fan "
            "engagement execution belongs to aria (fan-builder); "
            "monetization execution belongs to mo (mobile-monetize); "
            "touring execution belongs to miles (tour-commander). Data "
            "never claims their execution work."
        ),
    },
}
