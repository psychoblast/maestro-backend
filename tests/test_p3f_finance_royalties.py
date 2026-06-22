"""
Phase 3f — deepened finance_royalties domain knowledge tests.

Verifies that the 'finance_royalties' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and new knowledge files, and contains no forbidden entity strings.

New knowledge files added in phase 3f:
  - neighboring-rights-and-international-collection.md
  - music-finance-instruments-and-catalog-economics.md

Covers: neighboring rights mechanics (US SoundExchange regime, dual-account
registration, international territory societies), sub-publishing fee and lag
mechanics, PRO reciprocal-agreement double-waterfall, streaming economics and
per-stream rate derivation, recording deal structures (all-in royalty / net
receipts / profit split / licensing / pass-through), publishing advance
recoupment (full pub vs co-pub), catalog-backed lending, NPS-multiple catalog
valuation, due-diligence checklist, advance vs sale framework, and music income
tax basics (self-employment tax, quarterly estimates, international withholding).

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "audit our royalty collection across all pipelines and identify "
    "where income is missing or underpaid for this catalog"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_finance_royalties():
    assert "finance_royalties" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("finance_royalties").display_name == "Finance & Royalties"


def test_load_domain_returns_string():
    text = registry.load_domain("finance_royalties")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("finance_royalties")
    assert text.strip(), "finance_royalties domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 7 knowledge files (5 existing + 2 new) → expect at least 85 000 chars
    text = registry.load_domain("finance_royalties")
    assert len(text) >= 85_000, (
        f"finance_royalties knowledge too small: {len(text)} chars — expected ≥85 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 7 files joined by section separators → at least 6 separators between files
    text = registry.load_domain("finance_royalties")
    assert text.count("\n\n---\n\n") >= 6, (
        "Expected ≥6 section separators (7 knowledge files) in finance_royalties domain"
    )


# ── pre-existing doctrine presence ───────────────────────────────────────────

def test_recovery_posture_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "royalty statement is not a check" in text or "recovery posture" in text
    assert "unpaid dollar" in text


def test_pipeline_first_diagnosis_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "pipeline-first" in text or "pipeline first" in text
    assert "in transit" in text


def test_hard_refusals_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "hard refusal" in text or "never assert underpayment" in text
    assert "lag" in text and "underpayment" in text


def test_seven_dimension_rubric_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "registration integrity" in text
    assert "statement verification" in text
    assert "black-box recovery" in text
    assert "pipeline coverage" in text
    assert "audit readiness" in text


def test_hard_gates_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "hg-1" in text
    assert "hg-2" in text
    assert "hg-3" in text
    assert "hg-4" in text


def test_not_evaluable_discipline_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "not evaluable" in text


def test_pipeline_mechanics_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "master recording royalty" in text or "master royalty" in text
    assert "performance royalt" in text
    assert "mechanical royalt" in text


def test_collection_timelines_table_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "6" in text and "18 months" in text
    assert "tier c" in text


def test_pipeline_failure_taxonomy_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "missing mechanical registration" in text
    assert "missing pro registration" in text
    assert "reserve over-retention" in text


def test_unmatched_pool_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "unmatched pool" in text or "unmatched-pool" in text
    assert "redistribution" in text or "redistributed" in text


def test_recoupment_reality_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "recoupment" in text
    assert "unrecouped" in text


def test_reserve_accounting_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "reserve" in text
    assert "release schedule" in text or "liquidat" in text


def test_twelve_category_anomaly_checklist_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "anomaly" in text
    assert "below-rate mechanical" in text or "below rate mechanical" in text
    assert "currency-conversion" in text or "currency conversion" in text


def test_soft_audit_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "soft audit" in text
    assert "written inquiry" in text or "documented written" in text


def test_output_templates_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "royalty recovery audit" in text
    assert "statement anomaly report" in text
    assert "registration gap report" in text
    assert "black-box recovery plan" in text


# ── new: neighboring rights & international collection (phase 3f) ─────────────

def test_neighboring_rights_file_loaded():
    """neighboring-rights-and-international-collection.md must appear."""
    text = registry.load_domain("finance_royalties").lower()
    assert "neighboring rights" in text and "soundexchange" in text, (
        "neighboring-rights-and-international-collection.md not found in assembled knowledge"
    )


def test_neighboring_rights_distinct_from_copyright():
    text = registry.load_domain("finance_royalties").lower()
    assert "related right" in text or "rights related to copyright" in text
    assert "separate registration" in text or "separate collectors" in text


def test_us_neighboring_rights_digital_only():
    """Key fact: US neighboring rights do NOT apply to terrestrial broadcast."""
    text = registry.load_domain("finance_royalties").lower()
    assert "terrestrial" in text
    assert "does not recognize" in text or "not apply" in text or "no us terrestrial" in text


def test_soundexchange_split_mechanics():
    """SoundExchange 50/45/5 statutory split must be present."""
    text = registry.load_domain("finance_royalties").lower()
    assert "50%" in text
    assert "45%" in text
    assert "5%" in text
    assert "featured artist" in text


def test_soundexchange_dual_account_requirement():
    """Both artist AND owner accounts are required — the most common missed step."""
    text = registry.load_domain("finance_royalties").lower()
    assert "two" in text or "dual" in text
    assert "owner" in text and "featured artist" in text
    # Both registration requirements must appear
    assert "sound recording copyright owner" in text or "owner account" in text


def test_soundexchange_holding_period():
    text = registry.load_domain("finance_royalties").lower()
    assert "retention" in text or "held" in text
    assert "ages out" in text or "redistribution" in text or "claiming" in text


def test_international_territory_societies_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "ppl" in text
    assert "gvl" in text
    assert "re:sound" in text or "resound" in text


def test_international_neighboring_rights_split():
    text = registry.load_domain("finance_royalties").lower()
    assert "50%" in text
    assert "performer" in text
    assert "sound recording owner" in text


def test_us_terrestrial_blind_spot_present():
    """Key practitioner insight — US artists miss international neighboring rights."""
    text = registry.load_domain("finance_royalties").lower()
    assert "us terrestrial" in text or "us artist" in text
    assert "systematic" in text or "consistently" in text or "consistently uncollected" in text


def test_isrc_as_matching_key():
    text = registry.load_domain("finance_royalties").lower()
    assert "isrc" in text
    assert "matching" in text or "match" in text
    assert "unmatched" in text or "cannot be matched" in text


def test_sub_publishing_mechanics_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "sub-publishing" in text or "sub-publisher" in text
    assert "at source" in text or "at-source" in text
    assert "at receipt" in text or "at-receipt" in text


def test_sub_publishing_fee_ranges():
    text = registry.load_domain("finance_royalties").lower()
    assert "15" in text and "25" in text
    assert "sub-publisher" in text or "sub-publishing" in text


def test_pro_reciprocal_agreement_double_waterfall():
    text = registry.load_domain("finance_royalties").lower()
    assert "double waterfall" in text or "reciprocal" in text
    assert "home pro" in text or "home-country pro" in text
    assert "12" in text and "24 months" in text


def test_soundexchange_unclaimed_fund_search():
    text = registry.load_domain("finance_royalties").lower()
    assert "unclaimed" in text
    assert "name search" in text or "searchable" in text


def test_international_withholding_tax_flag():
    text = registry.load_domain("finance_royalties").lower()
    assert "withholding" in text
    assert "non-resident" in text or "non resident" in text


def test_international_collection_lag_table():
    text = registry.load_domain("finance_royalties").lower()
    assert "12–24 months" in text or "12-24 months" in text or "12 to 24" in text
    assert "direct registration" in text


# ── new: music finance instruments & catalog economics (phase 3f) ─────────────

def test_finance_instruments_file_loaded():
    """music-finance-instruments-and-catalog-economics.md must appear."""
    text = registry.load_domain("finance_royalties").lower()
    assert "streaming economics" in text or "per-stream rate" in text or "royalty pool" in text, (
        "music-finance-instruments-and-catalog-economics.md not found in assembled knowledge"
    )


def test_streaming_royalty_pool_mechanics():
    text = registry.load_domain("finance_royalties").lower()
    assert "royalty pool" in text
    assert "70%" in text or "seventy" in text
    assert "rights holder" in text or "rights-holder" in text


def test_per_stream_rate_not_fixed():
    """Core non-obvious insight: per-stream rate is derived, not fixed."""
    text = registry.load_domain("finance_royalties").lower()
    assert "not a fixed" in text or "derived rate" in text or "changes every period" in text


def test_service_type_pools_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "ad-supported" in text or "ad supported" in text
    assert "premium" in text
    assert "family plan" in text


def test_major_vs_independent_rate_difference():
    text = registry.load_domain("finance_royalties").lower()
    assert "minimum guarantee" in text or "minimum per-stream" in text
    assert "independent" in text and "major" in text


def test_all_in_royalty_deal_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "all-in royalty" in text or "all in royalty" in text
    assert "royalty base" in text
    assert "royalty rate" in text


def test_net_receipts_deal_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "net receipts" in text
    assert "deduction" in text or "deductions" in text


def test_profit_split_deal_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "profit split" in text or "profit-split" in text


def test_cross_collateralization_deal_risk():
    text = registry.load_domain("finance_royalties").lower()
    assert "cross-collateralization" in text or "cross collateralization" in text
    assert "multiple release" in text or "multiple albums" in text or "other album" in text


def test_full_pub_vs_copub_recoupment_difference():
    """The co-pub writer's-share protection from recoupment is the key distinction."""
    text = registry.load_domain("finance_royalties").lower()
    assert "co-publishing" in text or "co-pub" in text
    assert "writer's share" in text or "writer share" in text
    assert "publisher's share only" in text or "publisher share only" in text


def test_catalog_backed_lending_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "catalog-backed lending" in text or "catalog backed lending" in text
    assert "loan-to-value" in text or "ltv" in text


def test_lending_lockbox_mechanism():
    text = registry.load_domain("finance_royalties").lower()
    assert "lockbox" in text or "lock box" in text
    assert "debt service" in text


def test_nps_multiple_methodology_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "net publisher" in text or "nps" in text
    assert "multiple" in text


def test_nps_multiple_ranges_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "15" in text and "25" in text
    assert "catalog" in text and "type" in text or "catalog type" in text


def test_catalog_value_drivers_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "revenue durability" in text or "durability" in text
    assert "concentration risk" in text or "concentration" in text


def test_due_diligence_checklist_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "due diligence" in text or "due-diligence" in text
    assert "royalty statement" in text or "statement" in text
    assert "split" in text


def test_advance_vs_sale_framework():
    text = registry.load_domain("finance_royalties").lower()
    assert "advance" in text and "sale" in text
    assert "ownership" in text


def test_self_employment_tax_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "self-employment tax" in text or "self employment tax" in text


def test_quarterly_estimated_taxes_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "quarterly" in text and ("estimated" in text or "estimate" in text)
    assert "underpayment" in text


def test_1099_reporting_present():
    text = registry.load_domain("finance_royalties").lower()
    assert "1099" in text


def test_deal_economics_pre_signing_checklist():
    text = registry.load_domain("finance_royalties").lower()
    assert "pre-signing" in text or "before" in text
    assert "royalty rate" in text and "deduction" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_royalty_audit_query():
    result = brain.route(IN_DOMAIN_QUERY)
    assert "finance_royalties" in result


def test_route_statement_verification_query():
    assert "finance_royalties" in brain.route(
        "verify the royalty statement we received and check for anomalies"
    )


def test_route_registration_gap_query():
    assert "finance_royalties" in brain.route(
        "check if all our compositions are registered with the mechanical collector"
    )


def test_route_neighboring_rights_query():
    assert "finance_royalties" in brain.route(
        "register our recordings for neighboring rights collection internationally"
    )


def test_route_catalog_valuation_query():
    assert "finance_royalties" in brain.route(
        "estimate the NPS multiple and model the advance vs royalty catalog sale tradeoff"
    )


def test_route_unrelated_query_excludes_finance_royalties():
    # A pure social media query should not pull finance_royalties
    assert "finance_royalties" not in brain.route(
        "create instagram and tiktok content for the album rollout"
    )


def test_route_irrelevant_query_returns_empty():
    assert brain.route("what should i have for breakfast") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_finance_royalties_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "finance_royalties" in result["domains"]
    assert "# Finance & Royalties (finance_royalties)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("finance_royalties"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query in [
        IN_DOMAIN_QUERY,
        "register our recordings for neighboring rights collection internationally",
        "what is the NPS multiple for our publishing catalog",
    ]:
        result = brain.consult(query)
        assert_no_forbidden_terms(result["knowledge"])
