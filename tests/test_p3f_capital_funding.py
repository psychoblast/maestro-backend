"""
Phase 3f — deepened capital_funding domain knowledge tests.

Verifies that the 'capital_funding' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and new knowledge files, and contains no forbidden entity strings.

New knowledge files added in phase 3f:
  - tax-incentives-and-grants-mechanics.md
  - music-sector-funder-landscape-and-raise-process.md

Covers: sound recording production credit mechanics (refundable vs non-refundable,
eligible expenditures, management-commission exclusion, systemic credit lag),
tax credit bridge financing (LTV, directed-payment, true cost of bridge-plus-credit),
arts council grant application lifecycle (10 stages), multi-program stacking
discipline, export and market-development programs, multi-year grant calendar,
common compliance failures (eligible-expenditure creep, project-start-date
violations, commingling), cross-jurisdiction complexity; music-sector funder
typology (grant bodies, tax credit programs, revenue-based lenders, catalog-backed
lenders, label/distributor advance providers, venture/growth equity, sector banks),
underwriting criteria by funder type, capital raise process phases (preparation,
outreach, diligence, close), data room assembly, pipeline management, funder-type-
specific ask formats, closing mechanics, common process failures.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "we need to raise $400k for recording and market development — "
    "walk me through our capital options, starting with non-dilutive sources"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_capital_funding():
    assert "capital_funding" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("capital_funding").display_name == "Capital and funding"


def test_load_domain_returns_string():
    text = registry.load_domain("capital_funding")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("capital_funding")
    assert text.strip(), "capital_funding domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 8 knowledge files → expect at least 100 000 chars
    text = registry.load_domain("capital_funding")
    assert len(text) >= 100_000, (
        f"capital_funding knowledge too small: {len(text)} chars — expected ≥100 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 8 files joined by section separators → at least 7 separators
    text = registry.load_domain("capital_funding")
    assert text.count("\n\n---\n\n") >= 7, (
        "Expected ≥7 section separators (8 knowledge files) in capital_funding domain"
    )


# ── pre-existing doctrine: capital stack & sourcing ──────────────────────────

def test_non_dilutive_first_doctrine_present():
    text = registry.load_domain("capital_funding").lower()
    assert "non-dilutive-first" in text or "non-dilutive first" in text


def test_capital_stack_tiers_present():
    text = registry.load_domain("capital_funding").lower()
    assert "tier" in text
    assert "seniority" in text
    assert "collateral" in text


def test_wacc_present():
    text = registry.load_domain("capital_funding").lower()
    assert "weighted-average cost" in text or "wacc" in text


def test_irr_comparison_framework_present():
    text = registry.load_domain("capital_funding").lower()
    assert "internal rate of return" in text or "irr" in text


def test_effective_cost_framework_present():
    text = registry.load_domain("capital_funding").lower()
    assert "effective" in text and "cost" in text
    assert "all-in" in text or "true cost" in text


def test_source_ranking_methodology_present():
    text = registry.load_domain("capital_funding").lower()
    assert "accessibility" in text
    assert "constraint" in text
    assert "disposition" in text


def test_encumbrance_mapping_present():
    text = registry.load_domain("capital_funding").lower()
    assert "encumbrance" in text
    assert "optionality" in text


def test_music_sector_capital_adjustments_present():
    text = registry.load_domain("capital_funding").lower()
    assert "illiquidity premium" in text or "illiquidity" in text
    assert "catalog" in text
    assert "hit-rate" in text or "hit rate" in text


# ── pre-existing doctrine: non-dilutive & grant strategy ─────────────────────

def test_grant_disposition_discipline_present():
    text = registry.load_domain("capital_funding").lower()
    assert "eligible and pursuing" in text
    assert "eligible and declined" in text
    assert "ineligible" in text


def test_matching_fund_math_present():
    text = registry.load_domain("capital_funding").lower()
    assert "matching" in text and "match" in text
    assert "net capital received" in text


def test_eligible_expenditure_strings_present():
    text = registry.load_domain("capital_funding").lower()
    assert "eligible" in text and "expenditure" in text
    assert "management" in text and "commission" in text


def test_clawback_risk_present():
    text = registry.load_domain("capital_funding").lower()
    assert "clawback" in text
    assert "trigger" in text


def test_revenue_royalty_financing_sequencing_present():
    text = registry.load_domain("capital_funding").lower()
    assert "revenue" in text and "royalty" in text and "financing" in text


# ── pre-existing doctrine: debt & dilutive structures ────────────────────────

def test_dscr_present():
    text = registry.load_domain("capital_funding").lower()
    assert "dscr" in text or "debt service coverage" in text


def test_catalog_ip_backed_lending_present():
    text = registry.load_domain("capital_funding").lower()
    assert "catalog" in text and "lend" in text


def test_dilution_math_present():
    text = registry.load_domain("capital_funding").lower()
    assert "pre-money" in text or "pre money" in text
    assert "post-money" in text or "post money" in text


def test_liquidation_preference_waterfall_present():
    text = registry.load_domain("capital_funding").lower()
    assert "liquidation preference" in text or "liquidation-preference" in text
    assert "waterfall" in text


def test_convertible_instruments_present():
    text = registry.load_domain("capital_funding").lower()
    assert "convertible" in text
    assert "safe" in text or "discount" in text or "valuation cap" in text


# ── pre-existing doctrine: terms & covenant analysis ─────────────────────────

def test_fatal_term_taxonomy_present():
    text = registry.load_domain("capital_funding").lower()
    assert "fatal term" in text or "fatal-term" in text


def test_unlimited_personal_guarantee_fatal():
    text = registry.load_domain("capital_funding").lower()
    assert "unlimited personal guarantee" in text or "unlimited recourse" in text


def test_ip_alienation_fatal_term_present():
    text = registry.load_domain("capital_funding").lower()
    assert "ip alienation" in text or "permanent" in text and "transfer" in text


def test_uncapped_equity_ratchet_fatal():
    text = registry.load_domain("capital_funding").lower()
    assert "uncapped equity ratchet" in text or "uncapped ratchet" in text


def test_covenant_stress_testing_present():
    text = registry.load_domain("capital_funding").lower()
    assert "stress" in text and "covenant" in text
    assert "conservative case" in text or "conservative scenario" in text


def test_music_specific_covenant_hazards_present():
    text = registry.load_domain("capital_funding").lower()
    assert "360" in text or "revenue-participation" in text
    assert "cross-collateralization" in text or "cross collateralization" in text


def test_covenant_breach_monitoring_present():
    text = registry.load_domain("capital_funding").lower()
    assert "breach" in text and "monitor" in text
    assert "cure" in text


# ── pre-existing doctrine: soundness scorecard ───────────────────────────────

def test_eight_dimensions_present():
    text = registry.load_domain("capital_funding").lower()
    assert "eight" in text or "8" in text
    assert "dimension" in text


def test_hard_gates_present():
    text = registry.load_domain("capital_funding").lower()
    assert "hard gate" in text or "hard-gate" in text


def test_repayment_recoupment_gate_present():
    text = registry.load_domain("capital_funding").lower()
    assert "repayment" in text and "recoupment" in text


def test_composite_formula_present():
    text = registry.load_domain("capital_funding").lower()
    assert "composite" in text
    assert "0.16" in text
    assert "0.14" in text


def test_fundable_verdict_bands_present():
    text = registry.load_domain("capital_funding").lower()
    assert "fundable" in text
    assert "not fundable" in text
    assert "with conditions" in text


# ── new: tax incentives and grants mechanics (phase 3f) ──────────────────────

def test_tax_incentives_file_loaded():
    """tax-incentives-and-grants-mechanics.md must appear in assembled knowledge."""
    text = registry.load_domain("capital_funding").lower()
    assert "sound recording production" in text or "refundable" in text and "credit" in text, (
        "tax-incentives-and-grants-mechanics.md not found in assembled knowledge"
    )


def test_refundable_vs_non_refundable_credit_distinction():
    """Core non-obvious insight: non-refundable credits have no cash value pre-profit."""
    text = registry.load_domain("capital_funding").lower()
    assert "refundable" in text
    assert "non-refundable" in text
    assert "no current tax" in text or "no tax" in text or "loss" in text


def test_management_commission_exclusion_present():
    """Key compliance pitfall: management commissions are excluded from eligible expenditures."""
    text = registry.load_domain("capital_funding").lower()
    assert "management" in text and "commission" in text
    assert "exclusion" in text or "excluded" in text or "ineligible" in text


def test_credit_timing_lag_present():
    """Systemic timing lag between expenditure and credit receipt must be modeled."""
    text = registry.load_domain("capital_funding").lower()
    assert "lag" in text
    assert "fiscal year" in text or "year following" in text or "following" in text


def test_credit_bridge_financing_present():
    text = registry.load_domain("capital_funding").lower()
    assert "bridge" in text and "credit" in text
    assert "advance" in text


def test_bridge_ltv_ratio_present():
    text = registry.load_domain("capital_funding").lower()
    assert "loan-to-credit" in text or "ltv" in text or "70" in text or "85" in text


def test_directed_payment_arrangement_present():
    """Directed-payment instruction is the bridge lender's primary repayment protection."""
    text = registry.load_domain("capital_funding").lower()
    assert "directed" in text and "payment" in text


def test_bridge_true_cost_model_required():
    text = registry.load_domain("capital_funding").lower()
    assert "true cost" in text or "net capital" in text
    assert "bridge" in text and ("interest" in text or "cost" in text)


def test_grant_cycle_lifecycle_stages_present():
    text = registry.load_domain("capital_funding").lower()
    assert "grant agreement" in text
    assert "activity period" in text
    assert "reporting" in text


def test_pre_activity_start_date_requirement():
    """Grant expenditures before the project start date are ineligible — common pitfall."""
    text = registry.load_domain("capital_funding").lower()
    assert "start date" in text or "project start" in text
    assert "before" in text and "ineligible" in text


def test_multi_program_stacking_rules_present():
    text = registry.load_domain("capital_funding").lower()
    assert "stacking" in text
    assert "double-count" in text or "double count" in text or "same dollar" in text


def test_export_market_development_programs_present():
    text = registry.load_domain("capital_funding").lower()
    assert "export" in text and "market" in text and "development" in text


def test_grant_calendar_management_present():
    text = registry.load_domain("capital_funding").lower()
    assert "grant calendar" in text or "calendar" in text and "grant" in text


def test_eligible_expenditure_creep_pitfall_present():
    text = registry.load_domain("capital_funding").lower()
    assert "creep" in text or "eligible-expenditure creep" in text


def test_commingling_funds_pitfall_present():
    text = registry.load_domain("capital_funding").lower()
    assert "commingling" in text or "commingl" in text


def test_cross_jurisdiction_complexity_present():
    text = registry.load_domain("capital_funding").lower()
    assert "jurisdiction" in text
    assert "labor" in text and "content" in text
    assert "residency" in text


def test_audit_right_retention_period_present():
    text = registry.load_domain("capital_funding").lower()
    assert "audit right" in text or "audit-right" in text
    assert "retain" in text and "record" in text


# ── new: music-sector funder landscape and raise process (phase 3f) ──────────

def test_funder_landscape_file_loaded():
    """music-sector-funder-landscape-and-raise-process.md must appear."""
    text = registry.load_domain("capital_funding").lower()
    assert "funder landscape" in text or "funder typology" in text or "funder type" in text, (
        "music-sector-funder-landscape-and-raise-process.md not found in assembled knowledge"
    )


def test_revenue_based_lender_type_present():
    text = registry.load_domain("capital_funding").lower()
    assert "revenue-based" in text or "revenue based" in text
    assert "advance" in text


def test_catalog_backed_lender_type_present():
    text = registry.load_domain("capital_funding").lower()
    assert "catalog-backed lender" in text or "catalog lender" in text


def test_sector_bank_type_present():
    text = registry.load_domain("capital_funding").lower()
    assert "sector" in text and "bank" in text or "credit union" in text


def test_label_distributor_advance_effective_cost_warning():
    """Key non-obvious insight: label advance effective cost is often the highest in the stack."""
    text = registry.load_domain("capital_funding").lower()
    assert "label" in text and "advance" in text
    assert "effective cost" in text
    assert "expensive" in text or "most expensive" in text or "highest" in text


def test_cross_collateralization_label_risk_present():
    text = registry.load_domain("capital_funding").lower()
    assert "cross-collateralization" in text or "cross collateralization" in text
    assert "unrecouped" in text


def test_venture_equity_last_resort_present():
    """Core sequencing principle: venture/growth equity is structurally last resort."""
    text = registry.load_domain("capital_funding").lower()
    assert "last resort" in text or "last tier" in text or "last in" in text or "last" in text and "equity" in text


def test_underwriting_criteria_table_present():
    text = registry.load_domain("capital_funding").lower()
    assert "underwriting" in text
    assert "primary" in text and "signal" in text or "criteria" in text or "underwriting signal" in text


def test_raise_process_preparation_phase_present():
    text = registry.load_domain("capital_funding").lower()
    assert "preparation" in text
    assert "use of proceeds" in text or "use-of-proceeds" in text


def test_data_room_assembly_present():
    text = registry.load_domain("capital_funding").lower()
    assert "data room" in text
    assert "chain" in text and "title" in text or "chain-of-title" in text


def test_pipeline_tracker_present():
    text = registry.load_domain("capital_funding").lower()
    assert "pipeline" in text and "track" in text
    assert "funder" in text and "stage" in text


def test_funder_type_ask_format_present():
    """Key process discipline: format the ask for the funder type — grant body vs investor."""
    text = registry.load_domain("capital_funding").lower()
    assert "format" in text and "funder" in text or "pitch deck" in text
    assert "grant body" in text or "grant program" in text


def test_lead_lag_timeline_management_present():
    text = registry.load_domain("capital_funding").lower()
    assert "timeline" in text
    assert "60" in text and "120" in text or "60–120" in text


def test_conditions_precedent_close_mechanics_present():
    text = registry.load_domain("capital_funding").lower()
    assert "conditions precedent" in text


def test_compliance_calendar_at_close_present():
    text = registry.load_domain("capital_funding").lower()
    assert "compliance calendar" in text
    assert "close" in text


def test_common_process_failures_present():
    text = registry.load_domain("capital_funding").lower()
    assert "too late" in text or "common" in text and "failure" in text
    assert "grant" in text and "cycle" in text


def test_verbal_indications_not_capital_warning():
    """Non-obvious: verbal indications of intent must not be treated as committed capital."""
    text = registry.load_domain("capital_funding").lower()
    assert "verbal" in text
    assert "not a commitment" in text or "not committed" in text or "not" in text and "committed capital" in text


def test_single_funder_concentration_risk_warning():
    text = registry.load_domain("capital_funding").lower()
    assert "single" in text and "funder" in text or "one conversation" in text or "leverage" in text
    assert "alternative" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_capital_raise_query():
    result = brain.route(IN_DOMAIN_QUERY)
    assert "capital_funding" in result


def test_route_grant_search_query():
    assert "capital_funding" in brain.route(
        "what grants are available for our recording project and how do we apply"
    )


def test_route_tax_credit_query():
    assert "capital_funding" in brain.route(
        "can we claim a sound recording tax credit for this production and bridge it"
    )


def test_route_term_sheet_review_query():
    assert "capital_funding" in brain.route(
        "review this term sheet for fatal terms and covenant risk before we sign"
    )


def test_route_catalog_backed_loan_query():
    assert "capital_funding" in brain.route(
        "can we raise debt financing against our catalog IP — what capital structure works and what do lenders require"
    )


def test_route_equity_dilution_query():
    assert "capital_funding" in brain.route(
        "model the dilution from this investment and show the cap table waterfall"
    )


def test_route_unrelated_query_excludes_capital_funding():
    # A pure social media content query should not pull capital_funding
    assert "capital_funding" not in brain.route(
        "write an instagram caption for our new single release"
    )


def test_route_irrelevant_query_returns_empty():
    assert brain.route("what should i have for breakfast") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_capital_funding_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "capital_funding" in result["domains"]
    assert "# Capital and funding (capital_funding)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("capital_funding"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query in [
        IN_DOMAIN_QUERY,
        "what grants are available for our recording project",
        "bridge our tax credit and tell me the true effective cost",
        "what funder types are available for a catalog-backed loan",
    ]:
        result = brain.consult(query)
        assert_no_forbidden_terms(result["knowledge"])
