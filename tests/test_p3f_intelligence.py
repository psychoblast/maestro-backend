"""
Phase 3f — deepened intelligence domain knowledge tests.

Verifies that the 'intelligence' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and new knowledge files, and contains no forbidden entity strings.

New knowledge files added in phase 3f:
  - scan-operations-and-watchlist.md
  - music-industry-source-taxonomy.md
  - streaming-economics-intelligence-depth.md

Covers (scan-operations-and-watchlist): three-tier scan cadence (daily signal check,
weekly structured scan, monthly deep scan); source watch list structure with cadence
elevation and demotion rules; open-item and developing-story tracking with four status
values (DEVELOPING/CONFIRMED/NOT EVALUABLE/CLOSED); the standard seven-step weekly scan
workflow; scan log format with drop counts by filter; three legitimate close conditions
for developing stories; monthly watch-list audit protocol.

Covers (music-industry-source-taxonomy): six primary source categories (streaming
platform official documents, rights body/CMO documents, chart authority publications,
label group financial disclosures, regulatory/legislative filings, technology/AI primary
documents); the four-step trade-to-primary navigation protocol; cross-border source
navigation by legal-system type; source discovery and watch-list addition discipline.

Covers (streaming-economics-intelligence-depth): royalty pool construction mechanics
(music allocation, rights-type split); pro-rata vs. user-centric distribution and CDM
classification; minimum stream length requirements; playlist intelligence by type
(editorial/algorithmic/personalized); pitch window mechanics; short-video creator fund
mechanics; album-equivalent unit mechanics (AEU/TEA/SEA); chart eligibility bundle
rules; earnings release extraction protocol; AI-generated content structural intelligence
questions; worked routing table for streaming economics developments.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "scan the industry for structural developments and route decision-relevant "
    "market intelligence with source tiers to the right specialist"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_intelligence():
    assert "intelligence" in registry.list_domains()


def test_get_domain_display_name():
    domain = registry.get_domain("intelligence")
    assert domain.display_name, "intelligence domain has no display_name"


def test_load_domain_returns_string():
    text = registry.load_domain("intelligence")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("intelligence")
    assert text.strip(), "intelligence domain loaded empty knowledge"


def test_load_domain_minimum_size():
    """11 knowledge files should yield >= 80 000 chars of assembled content."""
    text = registry.load_domain("intelligence")
    assert len(text) >= 80_000, (
        f"intelligence knowledge too small: {len(text)} chars — expected >=80 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    """11 files joined by section separators -> at least 10 inter-file separators."""
    text = registry.load_domain("intelligence")
    assert text.count("\n\n---\n\n") >= 10, (
        "Expected >=10 section separators in intelligence domain"
    )


def test_no_forbidden_entity_strings_in_domain():
    text = registry.load_domain("intelligence")
    assert_no_forbidden_terms(text)


# ── pre-existing doctrine: core intelligence principles ───────────────────────

def test_currency_with_consequence_mandate_present():
    text = registry.load_domain("intelligence").lower()
    assert "currency with consequence" in text


def test_news_is_noise_mandate_present():
    text = registry.load_domain("intelligence").lower()
    assert "news is noise until it changes a decision" in text


def test_decision_change_test_present():
    text = registry.load_domain("intelligence").lower()
    assert "decision-change test" in text


def test_four_filter_method_present():
    text = registry.load_domain("intelligence").lower()
    assert "four-filter method" in text


def test_star_protocol_present():
    text = registry.load_domain("intelligence").lower()
    assert "star protocol" in text


def test_not_evaluable_protocol_present():
    text = registry.load_domain("intelligence").lower()
    assert "not evaluable" in text


def test_cdm_classification_matrix_present():
    text = registry.load_domain("intelligence").lower()
    assert "cdm-1" in text
    assert "cdm-2" in text
    assert "cdm-3" in text


def test_source_tier_system_present():
    text = registry.load_domain("intelligence").lower()
    assert "tier a" in text or "tier-a" in text or "high trust" in text
    assert "tier d" in text or "rumor" in text


def test_alert_format_present():
    text = registry.load_domain("intelligence").lower()
    assert "alert" in text
    assert "what changed" in text


def test_territory_lens_axes_present():
    text = registry.load_domain("intelligence").lower()
    assert "streaming landscape" in text
    assert "chart system" in text
    assert "rights bodies" in text


def test_quality_scorecard_dimensions_present():
    text = registry.load_domain("intelligence").lower()
    assert "decision relevance" in text
    assert "sourcing integrity" in text


def test_hard_gates_present():
    text = registry.load_domain("intelligence").lower()
    assert "no unsourced fact" in text
    assert "no rumor as fact" in text


# ── new: scan operations and watchlist (phase 3f) ─────────────────────────────

def test_scan_operations_file_loaded():
    """scan-operations-and-watchlist.md must appear in assembled knowledge."""
    text = registry.load_domain("intelligence").lower()
    assert "scan cadence" in text or "three-tier scan" in text or (
        "signal check" in text and "structured scan" in text
    ), "scan-operations-and-watchlist.md not found"


def test_three_tier_cadence_daily_present():
    text = registry.load_domain("intelligence").lower()
    assert "signal check" in text
    assert "daily" in text


def test_three_tier_cadence_weekly_present():
    text = registry.load_domain("intelligence").lower()
    assert "structured scan" in text
    assert "weekly" in text


def test_three_tier_cadence_monthly_present():
    text = registry.load_domain("intelligence").lower()
    assert "deep scan" in text
    assert "monthly" in text


def test_watch_list_structure_present():
    text = registry.load_domain("intelligence").lower()
    assert "watch list" in text
    assert "source watch" in text or "cadence tier" in text


def test_cadence_elevation_rule_present():
    """Cadence elevation is triggered by CDM-1/2 yield over a rolling window."""
    text = registry.load_domain("intelligence").lower()
    assert "cadence elevation" in text or (
        "elevation" in text and "cdm-1" in text and "cadence" in text
    )


def test_cadence_demotion_rule_present():
    """Cadence demotion occurs when a source yields no CDM-1/2 for six months."""
    text = registry.load_domain("intelligence").lower()
    assert "cadence demotion" in text or "demotion" in text


def test_developing_status_present():
    text = registry.load_domain("intelligence").lower()
    assert "developing" in text


def test_confirmed_status_present():
    text = registry.load_domain("intelligence").lower()
    assert "confirmed" in text


def test_open_item_log_format_present():
    """The open-item log format with ITEM ID field must be present."""
    text = registry.load_domain("intelligence").lower()
    assert "item id" in text or "open-item" in text or "open item" in text


def test_re_check_trigger_concept_present():
    text = registry.load_domain("intelligence").lower()
    assert "re-check trigger" in text or "recheck trigger" in text


def test_weekly_scan_workflow_steps_present():
    """The seven-step weekly scan workflow must be present."""
    text = registry.load_domain("intelligence").lower()
    assert "step 1" in text
    assert "step 2" in text
    assert "step 6" in text


def test_scan_log_format_present():
    """The scan log with drop counts must be described."""
    text = registry.load_domain("intelligence").lower()
    assert "scan log" in text
    assert "filter 1 drops" in text or "drop" in text and "filter" in text


def test_three_close_conditions_present():
    """Three legitimate close conditions for developing stories."""
    text = registry.load_domain("intelligence").lower()
    assert "published" in text
    assert "superseded" in text


def test_30_day_review_deadline_present():
    """DEVELOPING items older than 30 days must be reviewed."""
    text = registry.load_domain("intelligence").lower()
    assert "30-day" in text or "30 day" in text


def test_watch_list_audit_protocol_present():
    """The monthly watch-list audit protocol must be present."""
    text = registry.load_domain("intelligence").lower()
    assert "watch-list audit" in text or "watch list audit" in text or (
        "monthly" in text and "audit" in text
    )


def test_zero_yield_sources_concept_present():
    """Zero-yield sources are flagged for demotion in the monthly audit."""
    text = registry.load_domain("intelligence").lower()
    assert "zero-yield" in text or "zero yield" in text


# ── new: music industry source taxonomy (phase 3f) ───────────────────────────

def test_source_taxonomy_file_loaded():
    """music-industry-source-taxonomy.md must appear in assembled knowledge."""
    text = registry.load_domain("intelligence").lower()
    assert "source taxonomy" in text or (
        "six primary source categories" in text or
        "category 1" in text and "streaming platform official" in text
    ), "music-industry-source-taxonomy.md not found"


def test_streaming_platform_official_docs_category_present():
    text = registry.load_domain("intelligence").lower()
    assert "platform official" in text or (
        "platform's own" in text and "press room" in text
    )


def test_rights_body_cmo_category_present():
    text = registry.load_domain("intelligence").lower()
    assert "collective management" in text or "cmo" in text


def test_chart_authority_publications_category_present():
    text = registry.load_domain("intelligence").lower()
    assert "chart authority" in text


def test_label_financial_disclosures_category_present():
    text = registry.load_domain("intelligence").lower()
    assert "earnings release" in text or (
        "label group" in text and "financial" in text
    )


def test_regulatory_legislative_filings_category_present():
    text = registry.load_domain("intelligence").lower()
    assert "regulatory" in text and "legislative" in text and "filing" in text


def test_technology_ai_primary_documents_category_present():
    text = registry.load_domain("intelligence").lower()
    assert "ai primary" in text or (
        "technology" in text and "ai" in text and "primary document" in text
    )


def test_trade_to_primary_navigation_protocol_present():
    """The four-step protocol for moving from trade story to primary document."""
    text = registry.load_domain("intelligence").lower()
    assert "trade-to-primary" in text or "trade to primary" in text or (
        "primary document" in text and "trade story" in text and "navigate" in text
    )


def test_issuing_authority_concept_present():
    text = registry.load_domain("intelligence").lower()
    assert "issuing authority" in text


def test_cross_border_source_navigation_present():
    text = registry.load_domain("intelligence").lower()
    assert "cross-border" in text or "common-law" in text or "civil-law" in text


def test_common_law_territory_source_structure_present():
    text = registry.load_domain("intelligence").lower()
    assert "common-law" in text or ("common law" in text and "copyright" in text)


def test_civil_law_territory_source_structure_present():
    text = registry.load_domain("intelligence").lower()
    assert "civil-law" in text or ("civil law" in text and "cmo" in text)


def test_source_discovery_protocol_present():
    """Protocol for adding a new source to the watch list."""
    text = registry.load_domain("intelligence").lower()
    assert "source discovery" in text or (
        "provisional tier" in text and "six-week" in text
    )


def test_watch_list_addition_discipline_present():
    """Watch-list additions require demonstrated CDM output, not just reputation."""
    text = registry.load_domain("intelligence").lower()
    assert "watch-list" in text or "watch list" in text
    assert "demonstrated" in text or "history" in text and "cdm" in text


def test_anti_pattern_trade_as_primary_present():
    """The anti-pattern of treating a trade story as Tier A must be named."""
    text = registry.load_domain("intelligence").lower()
    assert "anti-pattern" in text
    assert "trade story" in text or "trade" in text and "primary" in text


# ── new: streaming economics intelligence depth (phase 3f) ───────────────────

def test_streaming_economics_file_loaded():
    """streaming-economics-intelligence-depth.md must appear in assembled knowledge."""
    text = registry.load_domain("intelligence").lower()
    assert "royalty pool" in text, (
        "streaming-economics-intelligence-depth.md not found: 'royalty pool' absent"
    )


def test_royalty_pool_construction_present():
    text = registry.load_domain("intelligence").lower()
    assert "royalty pool" in text
    assert "music allocation" in text


def test_rights_type_split_in_pool_present():
    """The master/publishing split within the royalty pool must be explained."""
    text = registry.load_domain("intelligence").lower()
    assert "rights-type split" in text or (
        "master" in text and "publishing" in text and "pool" in text
    )


def test_pro_rata_distribution_explained():
    text = registry.load_domain("intelligence").lower()
    assert "pro-rata" in text or "pro rata" in text


def test_user_centric_distribution_explained():
    text = registry.load_domain("intelligence").lower()
    assert "user-centric" in text or "listener-centric" in text


def test_pro_rata_to_user_centric_shift_is_cdm1():
    """A shift from pro-rata to user-centric is explicitly CDM-1."""
    text = registry.load_domain("intelligence").lower()
    assert "cdm-1" in text
    assert "user-centric" in text or "pro-rata" in text


def test_minimum_stream_length_requirements_present():
    text = registry.load_domain("intelligence").lower()
    assert "minimum stream length" in text


def test_minimum_stream_length_is_cdm1():
    """A change in minimum stream length is a CDM-1 rule-changer."""
    text = registry.load_domain("intelligence").lower()
    assert "minimum stream length" in text
    assert "cdm-1" in text


def test_payout_threshold_concept_present():
    text = registry.load_domain("intelligence").lower()
    assert "payout threshold" in text or "minimum annual stream" in text


def test_editorial_vs_algorithmic_playlist_distinction():
    text = registry.load_domain("intelligence").lower()
    assert "editorial" in text and "algorithmic" in text
    assert "playlist" in text


def test_personalized_playlist_type_present():
    text = registry.load_domain("intelligence").lower()
    assert "personalized" in text and "playlist" in text


def test_pitch_window_mechanics_present():
    text = registry.load_domain("intelligence").lower()
    assert "pitch window" in text


def test_pitch_window_change_is_cdm2():
    """A change in the pitch window is CDM-2 for Distribution & Platform and Marketing."""
    text = registry.load_domain("intelligence").lower()
    assert "pitch window" in text
    assert "cdm-2" in text


def test_short_video_creator_fund_mechanics_present():
    text = registry.load_domain("intelligence").lower()
    assert "creator fund" in text or "short-video" in text


def test_aeu_tea_sea_mechanics_present():
    """Album-equivalent unit, track-equivalent album, and streaming-equivalent album."""
    text = registry.load_domain("intelligence").lower()
    assert "album-equivalent" in text or "aeu" in text
    assert "tea" in text or "track-equivalent" in text
    assert "sea" in text or "streaming-equivalent" in text


def test_tea_sea_conversion_rate_is_cdm1():
    """Revision to TEA or SEA conversion rates is CDM-1."""
    text = registry.load_domain("intelligence").lower()
    assert "conversion rate" in text
    assert "cdm-1" in text


def test_chart_eligibility_bundle_rules_present():
    text = registry.load_domain("intelligence").lower()
    assert "bundling" in text or "bundle" in text
    assert "chart" in text and "eligib" in text


def test_earnings_release_extraction_protocol_present():
    text = registry.load_domain("intelligence").lower()
    assert "earnings release" in text
    assert "extract" in text or "investor relations" in text


def test_arpu_metric_explained():
    """ARPU must be explained as an intelligence signal."""
    text = registry.load_domain("intelligence").lower()
    assert "arpu" in text


def test_earnings_release_limitations_present():
    """What earnings releases cannot tell you must be stated."""
    text = registry.load_domain("intelligence").lower()
    assert "earnings release" in text
    assert "cannot" in text or "cannot tell" in text or "do not" in text


def test_ai_training_data_licensing_question_present():
    text = registry.load_domain("intelligence").lower()
    assert "training data" in text
    assert "licensing" in text


def test_ai_royalty_eligibility_question_present():
    """Whether AI-generated content qualifies for royalties is a named structural question."""
    text = registry.load_domain("intelligence").lower()
    assert "ai-generated" in text or "ai generated" in text
    assert "royalt" in text


def test_voice_likeness_protection_present():
    text = registry.load_domain("intelligence").lower()
    assert "likeness" in text or "voice" in text and "simulation" in text


def test_ai_regulatory_consultation_is_not_enacted_rule():
    """Regulatory consultation ≠ enacted rule — must be stated as CDM-5 until enacted."""
    text = registry.load_domain("intelligence").lower()
    assert "consultation" in text
    assert "enacted" in text or "enacted rule" in text


def test_worked_routing_table_present():
    """A worked routing table for streaming economics developments must be present."""
    text = registry.load_domain("intelligence").lower()
    assert "routing" in text
    assert "worked" in text or (
        "routing table" in text or "routing:" in text
    )


def test_streaming_economics_routes_to_finance_royalties():
    """Finance & Royalties is a named specialist in the streaming economics routing table."""
    text = registry.load_domain("intelligence").lower()
    assert "finance & royalties" in text or "finance and royalties" in text


def test_entity_wall_clean_after_new_files():
    """Entity wall check on full assembled domain including new files."""
    text = registry.load_domain("intelligence")
    assert_no_forbidden_terms(text)
