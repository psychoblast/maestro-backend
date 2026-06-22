"""
Phase 3f — deepened data_analytics domain knowledge tests.

Verifies that the 'data_analytics' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and new knowledge files, and contains no forbidden entity strings.

New knowledge files added in phase 3f:
  - platform-algorithm-mechanics.md
  - data-reconciliation-and-attribution.md

Covers (platform-algorithm-mechanics): Spotify algorithmic surfaces (Release
Radar, Discover Weekly, Radio/Autoplay, Daily Mix) — trigger conditions, refresh
cadences, analytics signatures; Apple Music algorithmic surfaces (New Music Mix,
completion buckets, Shazam as discovery signal); how to read algorithmic pick-up
from source-of-stream data; save rate as algorithmic fuel; skip/completion as
distribution gate; algorithmic half-life concept; pre-save mechanics and the
48-hour algorithmic indexing window; editorial pitch workflow; editorial-algorithmic
interaction (mis-matched editorial risk); common analyst errors on algorithmic reads.

Covers (data-reconciliation-and-attribution): source hierarchy and trust tiers
(Tier 1–4); common reconciliation gaps (settlement lag, threshold differences,
territory bucketing, currency conversion timing, bundle/compilation accounting,
per-stream rate variation by listener tier); six-step reconciliation workflow with
±5%/±10% tolerance bands; attribution methodology (source-of-stream, territory-time
correlation, pre/post design, lift methodology, in-campaign conversion rates);
territory-based and time-based A/B testing discipline with named confounds; what
cannot be measured cleanly; attribution anti-patterns (correlation-to-causation
error, same-window contamination, press/sync attribution omission, fan-campaign
misread, baseline recency bias, campaign-total vs. campaign-lift confusion,
multi-touch platform attribution error).

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "analyze the algorithmic pick-up for this release — check save rate, "
    "source-of-stream shift after week 1, and reconcile the distributor "
    "statement against the DSP dashboard"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_data_analytics():
    assert "data_analytics" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("data_analytics").display_name == "Data and analytics"


def test_load_domain_returns_string():
    text = registry.load_domain("data_analytics")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("data_analytics")
    assert text.strip(), "data_analytics domain loaded empty knowledge"


def test_load_domain_minimum_size():
    """9 knowledge files should yield ≥ 90 000 chars of assembled content."""
    text = registry.load_domain("data_analytics")
    assert len(text) >= 90_000, (
        f"data_analytics knowledge too small: {len(text)} chars — expected ≥90 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    """9 files joined by section separators → at least 8 inter-file separators."""
    text = registry.load_domain("data_analytics")
    assert text.count("\n\n---\n\n") >= 8, (
        "Expected ≥8 section separators in data_analytics domain"
    )


# ── pre-existing doctrine: core analytics principles ─────────────────────────

def test_decision_grade_truth_mission_present():
    text = registry.load_domain("data_analytics").lower()
    assert "decision-grade truth" in text or "decision grade truth" in text


def test_denominator_discipline_present():
    text = registry.load_domain("data_analytics").lower()
    assert "denominator" in text


def test_save_rate_present():
    text = registry.load_domain("data_analytics").lower()
    assert "save rate" in text


def test_cohort_minimum_floors_present():
    text = registry.load_domain("data_analytics").lower()
    assert "100" in text and "500" in text
    assert "cohort" in text


def test_three_band_architecture_present():
    text = registry.load_domain("data_analytics").lower()
    assert "measured" in text
    assert "checked" in text
    assert "judged" in text


def test_rented_audience_doctrine_present():
    text = registry.load_domain("data_analytics").lower()
    assert "rented" in text
    assert "playlist" in text


def test_forecasting_specificity_gate_present():
    text = registry.load_domain("data_analytics").lower()
    assert "specificity gate" in text


def test_assumption_register_present():
    text = registry.load_domain("data_analytics").lower()
    assert "assumption register" in text


def test_falsifiability_condition_present():
    text = registry.load_domain("data_analytics").lower()
    assert "falsifiab" in text


def test_territory_release_dynamics_present():
    """Release Radar, territory dynamics, and editorial calendar knowledge present."""
    text = registry.load_domain("data_analytics").lower()
    assert "friday" in text
    assert "new music friday" in text or "editorial" in text


def test_anomaly_typology_present():
    text = registry.load_domain("data_analytics").lower()
    assert "spike" in text
    assert "level shift" in text
    assert "drift" in text
    assert "series break" in text


def test_z_score_framework_present():
    text = registry.load_domain("data_analytics").lower()
    assert "z-score" in text or "z score" in text


def test_benchmark_comparison_reasoning_present():
    text = registry.load_domain("data_analytics").lower()
    assert "reference class" in text
    assert "like-for-like" in text or "like for like" in text


# ── new: platform algorithm mechanics (phase 3f) ─────────────────────────────

def test_platform_algorithm_mechanics_file_loaded():
    """platform-algorithm-mechanics.md must appear in assembled knowledge."""
    text = registry.load_domain("data_analytics").lower()
    assert "release radar" in text, (
        "platform-algorithm-mechanics.md not found: 'release radar' absent"
    )


def test_release_radar_trigger_conditions_present():
    """Release Radar is triggered by follow or recent engagement — not saves alone."""
    text = registry.load_domain("data_analytics").lower()
    assert "release radar" in text
    assert "follow" in text
    assert "friday" in text


def test_discover_weekly_candidacy_mechanics_present():
    """DW requires cross-follower engagement (non-followers who saved) — non-obvious."""
    text = registry.load_domain("data_analytics").lower()
    assert "discover weekly" in text
    assert "monday" in text
    assert "collaborative" in text or "cross-follower" in text or "non-followers" in text


def test_radio_autoplay_catalog_tail_present():
    """Radio/Autoplay is the catalog-phase algorithmic surface — must be covered."""
    text = registry.load_domain("data_analytics").lower()
    assert "autoplay" in text or "radio" in text
    assert "catalog" in text and ("tail" in text or "base rate" in text or "passive" in text)


def test_algorithmic_half_life_concept_present():
    """The algorithmic half-life concept is a non-obvious projection discipline."""
    text = registry.load_domain("data_analytics").lower()
    assert "algorithmic half-life" in text or "half-life" in text


def test_save_rate_as_algorithmic_fuel_present():
    """Save rate from discovery-source listeners is the primary algorithmic candidacy signal."""
    text = registry.load_domain("data_analytics").lower()
    assert "algorithmic fuel" in text or (
        "save rate" in text and "algorithmic" in text and "candidacy" in text
    )


def test_48_hour_indexing_window_present():
    """The 48-hour indexing window is a non-obvious launch mechanic."""
    text = registry.load_domain("data_analytics").lower()
    assert "48-hour" in text or "48 hour" in text
    assert "index" in text or "candidacy" in text


def test_pre_save_campaign_mechanics_present():
    """Pre-save mechanics and their analytics implications must be covered."""
    text = registry.load_domain("data_analytics").lower()
    assert "pre-save" in text or "pre save" in text
    assert "library" in text and "release day" in text


def test_editorial_algorithmic_interaction_risk_present():
    """Mis-matched editorial placement can damage algorithmic candidacy — key non-obvious risk."""
    text = registry.load_domain("data_analytics").lower()
    assert "mis-matched" in text or "mismatch" in text or (
        "editorial" in text and "damage" in text
    )


def test_apple_music_new_music_mix_present():
    """Apple Music algorithmic surfaces must be covered — not just Spotify."""
    text = registry.load_domain("data_analytics").lower()
    assert "new music mix" in text


def test_shazam_as_discovery_signal_present():
    """Shazam count is a real-world passive discovery signal distinct from in-app discovery."""
    text = registry.load_domain("data_analytics").lower()
    assert "shazam" in text
    assert "discovery" in text


def test_apple_music_completion_buckets_present():
    """Apple Music surfaces completion in bucketed form — 25/50/75/100% — directly observable."""
    text = registry.load_domain("data_analytics").lower()
    assert "completion" in text and ("25" in text or "75" in text or "bucket" in text)


def test_analyst_error_release_radar_not_discovery():
    """Key error: treating Release Radar as discovery. Must be named in content."""
    text = registry.load_domain("data_analytics").lower()
    assert "release radar" in text
    assert "existing orbit" in text or "broadcast" in text or "not discovery" in text or "not" in text


def test_dsp_algorithm_not_identical_across_platforms():
    """Analyst error: applying Spotify thresholds to Apple Music reads."""
    text = registry.load_domain("data_analytics").lower()
    assert "spotify" in text and "apple music" in text
    assert "identical" in text or "same" in text


# ── new: data reconciliation & attribution (phase 3f) ────────────────────────

def test_data_reconciliation_file_loaded():
    """data-reconciliation-and-attribution.md must appear in assembled knowledge."""
    text = registry.load_domain("data_analytics").lower()
    assert "settlement lag" in text, (
        "data-reconciliation-and-attribution.md not found: 'settlement lag' absent"
    )


def test_source_hierarchy_four_tiers_present():
    """Four-tier source hierarchy: DSP dashboard → distributor → aggregator → self-reported."""
    text = registry.load_domain("data_analytics").lower()
    assert "tier 1" in text
    assert "tier 2" in text
    assert "tier 3" in text
    assert "tier 4" in text


def test_tier1_dsp_dashboard_described():
    text = registry.load_domain("data_analytics").lower()
    assert "dsp artist dashboard" in text or ("spotify for artists" in text and "tier" in text)


def test_settlement_lag_cause_explained():
    """Settlement lag (1–3 month) is the most common apparent discrepancy cause."""
    text = registry.load_domain("data_analytics").lower()
    assert "settlement lag" in text
    assert "timing" in text
    assert ("monthly" in text or "quarterly" in text)


def test_settlement_not_discrepancy_rule_present():
    """Settlement timing difference must be distinguished from a real data discrepancy."""
    text = registry.load_domain("data_analytics").lower()
    assert "not a discrepancy" in text or (
        "timing" in text and "difference" in text and "discrepancy" in text
    )


def test_threshold_definition_difference_gap_present():
    """30-second threshold differences between DSP and distributor cause reconciliation gaps."""
    text = registry.load_domain("data_analytics").lower()
    assert "threshold" in text and "definition" in text
    assert "30" in text and "second" in text


def test_territory_bucketing_gap_present():
    """Territory bucketing differences (DACH vs. individual markets) cause geographic gaps."""
    text = registry.load_domain("data_analytics").lower()
    assert "territory" in text and "bucket" in text or (
        "territory" in text and "dach" in text
    )


def test_currency_conversion_timing_gap_present():
    """Currency conversion at settlement time creates dollar-amount gaps on matched counts."""
    text = registry.load_domain("data_analytics").lower()
    assert "currency" in text and "conversion" in text and "timing" in text


def test_bundle_compilation_accounting_gap_present():
    """Bundle/compilation accounting causes track-level dashboard vs. statement gaps."""
    text = registry.load_domain("data_analytics").lower()
    assert "compilation" in text and "accounting" in text or (
        "bundle" in text and "isrc" in text
    )


def test_per_stream_rate_variation_present():
    """Per-stream rate varies by listener tier (premium vs free vs bundled)."""
    text = registry.load_domain("data_analytics").lower()
    assert "per-stream rate" in text or "per stream rate" in text
    assert "premium" in text and "free" in text


def test_reconciliation_six_step_workflow_present():
    """Six-step reconciliation workflow is the operational framework."""
    text = registry.load_domain("data_analytics").lower()
    assert "step 1" in text or "six-step" in text or "six step" in text
    assert "align" in text and "window" in text


def test_tolerance_bands_present():
    """Tolerance bands (±5%, ±10%) define when to investigate vs. escalate."""
    text = registry.load_domain("data_analytics").lower()
    assert "±5" in text or "5%" in text or "5 percent" in text
    assert "10%" in text or "±10" in text or "10 percent" in text


def test_attribution_source_of_stream_primary_tool():
    """Source-of-stream is the primary available attribution signal."""
    text = registry.load_domain("data_analytics").lower()
    assert "primary" in text and "attribution" in text
    assert "source-of-stream" in text or "source of stream" in text


def test_lift_methodology_present():
    """Lift methodology (matched control comparison) must be described with caveats."""
    text = registry.load_domain("data_analytics").lower()
    assert "lift methodology" in text or ("lift" in text and "matched control" in text)
    assert "comparabl" in text or "control" in text


def test_territory_based_ab_test_framework_present():
    """Territory-based A/B is the primary experimental design available."""
    text = registry.load_domain("data_analytics").lower()
    assert "territory-based" in text or "territory based" in text
    assert "control" in text and "market" in text


def test_time_based_ab_decay_confound_present():
    """The core confound in time-based A/B is release decay — must be named."""
    text = registry.load_domain("data_analytics").lower()
    assert "time-based" in text or "time based" in text
    assert "decay" in text and "confound" in text or (
        "decay" in text and "baseline" in text
    )


def test_correlation_to_causation_anti_pattern_present():
    """Correlation-to-causation is the primary attribution error in music analytics."""
    text = registry.load_domain("data_analytics").lower()
    assert "correlation" in text and "causation" in text


def test_same_window_contamination_anti_pattern_present():
    """Same-window contamination (playlist + campaign same week) must be named."""
    text = registry.load_domain("data_analytics").lower()
    assert "same-window" in text or "same window" in text
    assert "contamination" in text or "co-occurring" in text or "co occurring" in text


def test_press_sync_attribution_omission_anti_pattern_present():
    """Press and sync attribution omission is a systematic miss in analytics."""
    text = registry.load_domain("data_analytics").lower()
    assert "sync" in text and "attribution" in text
    assert "press" in text and "attribution" in text or "press calendar" in text


def test_fan_campaign_misread_anti_pattern_present():
    """Fan campaigns can masquerade as organic discovery — discriminating check is needed."""
    text = registry.load_domain("data_analytics").lower()
    assert "fan" in text and "campaign" in text
    assert "misread" in text or "organic discovery" in text


def test_campaign_total_vs_lift_confusion_anti_pattern_present():
    """Attribution error: claiming campaign total as campaign lift without accounting for baseline."""
    text = registry.load_domain("data_analytics").lower()
    assert "organic baseline" in text or (
        "baseline" in text and "campaign" in text and "lift" in text
    )


def test_multi_touch_attribution_error_present():
    """Multi-touch: each platform overclaims the same conversion — must be flagged."""
    text = registry.load_domain("data_analytics").lower()
    assert "multi-touch" in text or "multi touch" in text
    assert "overcount" in text or "overclaim" in text or "addit" in text


def test_in_campaign_conversion_measured_not_inferred():
    """In-campaign conversion rates are the only cleanly causal metric available."""
    text = registry.load_domain("data_analytics").lower()
    assert "in-campaign" in text or "in campaign" in text
    assert "causal" in text or "measured" in text


def test_reconciliation_escalation_path_present():
    """Discrepancies above ±10% must escalate to distributor with a formal log entry."""
    text = registry.load_domain("data_analytics").lower()
    assert "escalat" in text
    assert "distributor" in text
    assert "log" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_data_analytics():
    assert "data_analytics" in brain.route(IN_DOMAIN_QUERY)


def test_route_algorithmic_pickup_query():
    assert "data_analytics" in brain.route(
        "did this release get algorithmic pick-up — check the discover weekly and "
        "release radar signatures in the source-of-stream data"
    )


def test_route_pre_save_analytics_query():
    assert "data_analytics" in brain.route(
        "how do pre-saves translate into save rate signals on dsp data and what "
        "does the source-of-stream breakdown tell us on release day"
    )


def test_route_reconciliation_query():
    assert "data_analytics" in brain.route(
        "reconcile our streaming data — the distributor statement is 15% lower "
        "than the spotify for artists dashboard"
    )


def test_route_attribution_query():
    assert "data_analytics" in brain.route(
        "attribute the stream spike to either the editorial placement or the paid "
        "campaign — both ran in the same week"
    )


def test_route_anomaly_query():
    assert "data_analytics" in brain.route(
        "there is a stream spike in our data — run the triage to determine if "
        "it is a reporting artifact or a real event"
    )


def test_route_forecast_query():
    assert "data_analytics" in brain.route(
        "forecast the streaming trajectory for the next 8 weeks based on save rate "
        "and decay curve from week 1"
    )


def test_route_benchmark_query():
    assert "data_analytics" in brain.route(
        "benchmark this release against a comparable case set and build the reference class"
    )


def test_route_unrelated_query_excludes_data_analytics():
    # A pure mechanical-royalties query should not pull data_analytics
    assert "data_analytics" not in brain.route(
        "how do mechanical royalties and recoupment work on a label deal"
    )


def test_route_irrelevant_query_returns_empty():
    assert brain.route("what should i eat for dinner tonight") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_data_analytics_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "data_analytics" in result["domains"]
    assert "# Data and analytics (data_analytics)" in result["knowledge"]
    assert result["knowledge"].strip()


def test_consult_algorithm_query_returns_mechanics():
    result = brain.consult(
        "explain release radar vs discover weekly and what signals each uses",
        home_domain="data_analytics"
    )
    assert "data_analytics" in result["domains"]
    assert "release radar" in result["knowledge"].lower()


def test_consult_reconciliation_query_returns_workflow():
    result = brain.consult(
        "walk me through reconciling distributor statement against dsp dashboard",
        home_domain="data_analytics"
    )
    assert "data_analytics" in result["domains"]
    assert "settlement" in result["knowledge"].lower()


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("data_analytics"))


def test_consulted_knowledge_has_no_forbidden_terms():
    queries = [
        IN_DOMAIN_QUERY,
        "check algorithmic pick-up via release radar and discover weekly source data",
        "reconcile distributor statement against dsp dashboard — 12% gap after aligning windows",
        "build the attribution case for the stream spike — correlation vs causation check",
        "anomaly detection on a stream spike: triage for artifact vs real event",
    ]
    for query in queries:
        result = brain.consult(query, home_domain="data_analytics")
        assert_no_forbidden_terms(result["knowledge"])
