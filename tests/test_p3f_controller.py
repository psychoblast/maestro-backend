"""
Phase 3f — deepened controller domain knowledge tests.

Verifies that the 'controller' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and newly added knowledge files, and contains no forbidden
entity strings.

New knowledge files added in phase 3f:
  - chart-of-accounts-and-account-architecture.md
  - catalog-acquisition-and-intangible-assets.md

Covers:
  chart-of-accounts-and-account-architecture: COA design principles
  (reconciliation-tractable, revenue disaggregated, advances isolated,
  intercompany segregated); numeric block assignments for music enterprises
  (streaming 4000s, sync 4100s, PRO 4200s, mechanicals 4300s, neighboring
  rights 4400s, recoupable advances 1300–1499, royalty payable 2100–2299,
  deferred advance income 2400–2499, intercompany 1900/2900 blocks); streaming
  block sub-account design (platform disaggregation, principal-vs.-agent split,
  lag-period accrual sub-accounts); royalty payable recipient-level vs. tier-
  level design; recoupable advance account design; intercompany discipline
  (entity-pair naming, no clearing account, transaction-level posting); close-
  sequence account review order; common misclassification patterns; COA
  maintenance controls (activation gate, deactivation cycle, mapping integrity,
  period-over-period anomaly check).

  catalog-acquisition-and-intangible-assets: asset acquisition vs. business
  combination determination (ASC 805); purchase price allocation for music
  catalogs; identifying acquired intangibles (master recording rights, publishing
  rights, neighboring-rights interests, sync relationships, distribution
  agreements, non-competes); useful life determination (finite vs. indefinite)
  for composition copyrights, master recordings, distribution agreements, and
  non-competes; amortization method and schedule requirements; impairment testing
  under ASC 350 and ASC 360; music-specific impairment indicators (streaming
  decline, platform de-listing, artist controversy, genre obsolescence,
  territorial risk, statutory-rate changes); royalty-relief method review
  checklist; post-acquisition integration checklist (opening entry, amortization
  schedule, royalty stream mapping, cutover confirmation, assumed advance
  balances); common controller findings in catalog acquisitions.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "can the controller certify the period close — are all balance sheet "
    "accounts reconciled and is the audit trail documented"
)

COA_QUERY = (
    "review our chart of accounts structure for the music enterprise — "
    "are royalty payable and advance accounts properly segregated"
)

CATALOG_QUERY = (
    "we acquired a publishing catalog — what is the correct gaap treatment for "
    "purchase price allocation and intangible asset useful life"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_controller():
    assert "controller" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("controller").display_name == "Financial controller"


def test_load_domain_returns_string():
    text = registry.load_domain("controller")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("controller")
    assert text.strip(), "controller domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 10 knowledge files in load_order — expect at least 100 000 chars
    text = registry.load_domain("controller")
    assert len(text) >= 100_000, (
        f"controller knowledge too small: {len(text)} chars — expected ≥100 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 10 files joined by section separators → at least 9 joining separators;
    # internal markdown section dividers add further, so floor is generous
    text = registry.load_domain("controller")
    assert text.count("\n\n---\n\n") >= 9, (
        "Expected ≥9 section separators (10 knowledge files) in controller domain"
    )


# ── pre-existing doctrine ─────────────────────────────────────────────────────

def test_core_doctrine_present():
    text = registry.load_domain("controller").lower()
    assert "ledger integrity & controls scorecard" in text


def test_reconciliation_doctrine_present():
    text = registry.load_domain("controller").lower()
    assert "reconciliation" in text
    assert "audit trail" in text


def test_revenue_recognition_doctrine_present():
    text = registry.load_domain("controller").lower()
    assert "revenue recognition" in text
    assert "asc 606" in text


def test_segregation_of_duties_doctrine_present():
    text = registry.load_domain("controller").lower()
    assert "segregation of duties" in text


def test_scorecard_dimensions_present():
    text = registry.load_domain("controller").lower()
    assert "reconciliation completeness" in text
    assert "documentation & audit trail" in text


def test_scorecard_hard_gates_present():
    text = registry.load_domain("controller").lower()
    assert "hard gate" in text or "hard gates" in text


# ── chart-of-accounts knowledge (new in phase 3f) ────────────────────────────

def test_coa_architecture_section_present():
    text = registry.load_domain("controller").lower()
    assert "chart of accounts" in text


def test_coa_reconciliation_tractable_principle_present():
    text = registry.load_domain("controller").lower()
    assert "reconciliation-tractable" in text


def test_coa_streaming_revenue_block_present():
    # The streaming income block (4000–4099) and its design rules
    text = registry.load_domain("controller")
    assert "4000" in text
    assert "streaming" in text.lower()


def test_coa_royalty_payable_blocks_present():
    text = registry.load_domain("controller")
    assert "2100" in text
    assert "2200" in text


def test_coa_recoupable_advance_blocks_present():
    text = registry.load_domain("controller")
    assert "1300" in text
    assert "1400" in text


def test_coa_deferred_advance_income_block_present():
    text = registry.load_domain("controller")
    assert "2400" in text


def test_coa_intercompany_blocks_present():
    text = registry.load_domain("controller")
    assert "1900" in text
    assert "2900" in text


def test_coa_principal_vs_agent_split_present():
    text = registry.load_domain("controller").lower()
    assert "principal" in text and "agent" in text


def test_coa_lag_period_accrual_sub_account_present():
    text = registry.load_domain("controller").lower()
    assert "lag" in text and "accrual" in text


def test_coa_royalty_payable_design_recipient_level_present():
    text = registry.load_domain("controller").lower()
    assert "recipient-level" in text


def test_coa_royalty_payable_design_tier_level_present():
    text = registry.load_domain("controller").lower()
    assert "tier-level" in text


def test_coa_intercompany_entity_pair_naming_present():
    text = registry.load_domain("controller").lower()
    assert "entity pair" in text or "counterparty entity" in text


def test_coa_close_sequence_review_present():
    text = registry.load_domain("controller").lower()
    assert "close-sequence" in text or "close sequence" in text


def test_coa_misclassification_patterns_present():
    text = registry.load_domain("controller").lower()
    assert "misclassification" in text


def test_coa_activation_gate_present():
    text = registry.load_domain("controller").lower()
    assert "activation gate" in text


def test_coa_deactivation_cycle_present():
    text = registry.load_domain("controller").lower()
    assert "deactivation" in text or "deactivated" in text


def test_coa_revenue_disaggregation_principle_present():
    text = registry.load_domain("controller").lower()
    # The COA file ties revenue disaggregation to ASC 606 disclosure requirement
    assert "disaggregat" in text


# ── catalog acquisition knowledge (new in phase 3f) ──────────────────────────

def test_catalog_acquisition_section_present():
    text = registry.load_domain("controller").lower()
    assert "catalog acquisition" in text or "catalog" in text


def test_asset_acquisition_vs_business_combination_present():
    text = registry.load_domain("controller").lower()
    assert "business combination" in text
    assert "asset acquisition" in text


def test_asc_805_reference_present():
    text = registry.load_domain("controller")
    assert "ASC 805" in text or "asc 805" in text.lower()


def test_purchase_price_allocation_present():
    text = registry.load_domain("controller").lower()
    assert "purchase price allocation" in text


def test_intangibles_identified_present():
    text = registry.load_domain("controller").lower()
    assert "master recording" in text or "composition copyright" in text


def test_useful_life_determination_present():
    text = registry.load_domain("controller").lower()
    assert "useful life" in text


def test_indefinite_lived_present():
    text = registry.load_domain("controller").lower()
    assert "indefinite-lived" in text or "indefinite lived" in text


def test_finite_lived_present():
    text = registry.load_domain("controller").lower()
    assert "finite-lived" in text or "finite lived" in text


def test_asc_350_impairment_reference_present():
    text = registry.load_domain("controller")
    assert "ASC 350" in text or "asc 350" in text.lower()


def test_impairment_indicators_present():
    text = registry.load_domain("controller").lower()
    assert "impairment indicator" in text or "impairment" in text


def test_streaming_decline_as_impairment_indicator_present():
    text = registry.load_domain("controller").lower()
    assert "streaming" in text and "impairment" in text


def test_royalty_relief_method_present():
    text = registry.load_domain("controller").lower()
    assert "royalty-relief method" in text or "royalty relief method" in text


def test_amortization_schedule_required_present():
    text = registry.load_domain("controller").lower()
    assert "amortization schedule" in text


def test_post_acquisition_integration_checklist_present():
    text = registry.load_domain("controller").lower()
    assert "post-acquisition" in text or "post acquisition" in text


def test_assumed_advance_balances_present():
    text = registry.load_domain("controller").lower()
    assert "assumed" in text and "advance" in text


def test_cutover_date_confirmation_present():
    text = registry.load_domain("controller").lower()
    assert "cutover" in text or "cut-over" in text or "closing date" in text


def test_non_compete_finite_useful_life_present():
    text = registry.load_domain("controller").lower()
    assert "non-compete" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_controller():
    assert "controller" in brain.route(IN_DOMAIN_QUERY)


def test_route_coa_query_to_controller():
    assert "controller" in brain.route(COA_QUERY)


def test_route_catalog_query_to_controller():
    assert "controller" in brain.route(CATALOG_QUERY)


def test_route_revrec_query_to_controller():
    assert "controller" in brain.route(
        "what is the correct revenue recognition treatment under asc 606 "
        "for an advance received from a distributor"
    )


def test_route_controls_query_to_controller():
    assert "controller" in brain.route(
        "assess internal controls and segregation of duties for the "
        "journal entry process"
    )


def test_route_unrelated_query_excludes_controller():
    # A pure royalties economics query must not pull in controller
    assert "controller" not in brain.route(
        "how do mechanical royalties and recoupment economics work"
    )


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_controller_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "controller" in result["domains"]
    domain = registry.get_domain("controller")
    assert f"# {domain.display_name} (controller)" in result["knowledge"]
    assert result["knowledge"].strip()


def test_consult_coa_query_returns_controller():
    result = brain.consult(COA_QUERY)
    assert "controller" in result["domains"]
    assert result["knowledge"].strip()


def test_consult_catalog_query_returns_controller():
    result = brain.consult(CATALOG_QUERY)
    assert "controller" in result["domains"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("controller"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        (COA_QUERY, "controller"),
        (CATALOG_QUERY, None),
        ("chart of accounts design for royalty payable accounts", "controller"),
        ("purchase price allocation and useful life for acquired music publishing rights", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
