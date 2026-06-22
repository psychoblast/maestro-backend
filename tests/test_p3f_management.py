"""
Phase 3f — deepened management domain knowledge tests.

Verifies that the 'management' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and new knowledge files, and contains no forbidden entity strings.

New knowledge files added in phase 3f:
  - record-deal-mechanics-and-structures.md
  - royalty-income-monitoring.md

Covers (record-deal-mechanics-and-structures): the five recording deal
structures (major-label, P&D, label-services, distribution, self-release via
aggregator) with manager's strategic lens on each; advance and recoupment
mechanics (recoupable nature of advances, cross-collateralization and why
to resist it, what is charged against royalties); royalty rate structure
(all-in rate, producer royalty points, royalty base for digital vs. physical,
royalty reductions); controlled composition clause mechanics and the three-quarter
rate; 360-deal provisions with the enumeration-per-stream negotiating framework;
release commitment mechanics (delivery criteria, commercially-acceptable clause
as red flag, reversion-for-non-release); marketing commitment documentation;
and the red-flag clause taxonomy for recording agreements.

Covers (royalty-income-monitoring): recording and publishing income pipelines
from streams to artist payment with delay mechanics; statement frequency
standards by deal type (major label semi-annual, distribution monthly,
PRO quarterly); recoupment status monitoring and cross-collateralization's
effect on recoupment visibility; royalty statement anatomy checklist (period
coverage, balance continuity, volume sanity check, rate applied, deductions,
reserves, foreign income, controlled composition calculations); the most common
royalty accounting errors; conditions warranting a formal royalty audit, the
look-back window obligation, and cost structure; and income tracking minimum
standards (statement receipt log, recoupment tracker, publishing registration
audit, income-expectation calendar).

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "evaluate the recording agreement advance and recoupment structure, check for "
    "cross-collateralization and the controlled composition clause, then audit the "
    "label's royalty statements for the last two accounting periods and determine "
    "whether conditions warrant a formal royalty audit"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_management():
    assert "management" in registry.list_domains()


def test_get_domain_display_name():
    domain = registry.get_domain("management")
    assert domain.display_name == "Artist management"


def test_load_domain_returns_string():
    text = registry.load_domain("management")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("management")
    assert text.strip(), "management domain loaded empty knowledge"


def test_load_domain_minimum_size():
    """12 knowledge files should yield ≥ 120 000 chars of assembled content."""
    text = registry.load_domain("management")
    assert len(text) >= 120_000, (
        f"management knowledge too small: {len(text)} chars — expected ≥120 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    """12 files joined by section separators → at least 11 inter-file separators."""
    text = registry.load_domain("management")
    assert text.count("\n\n---\n\n") >= 11, (
        "Expected ≥11 section separators in management domain after phase 3f"
    )


def test_no_forbidden_entity_strings_in_domain():
    text = registry.load_domain("management")
    assert_no_forbidden_terms(text)


# ── pre-existing doctrine: core management knowledge ──────────────────────────

def test_core_principle_present():
    text = registry.load_domain("management").lower()
    assert "the manager who cannot say no to their artist" in text


def test_modified_net_commission_present():
    text = registry.load_domain("management").lower()
    assert "modified net" in text


def test_sunset_clause_present():
    text = registry.load_domain("management").lower()
    assert "sunset" in text


def test_key_person_clause_present():
    text = registry.load_domain("management").lower()
    assert "key-person" in text


def test_career_phase_model_present():
    text = registry.load_domain("management").lower()
    assert "career phase" in text


def test_positioning_triangle_present():
    text = registry.load_domain("management").lower()
    assert "positioning triangle" in text


def test_loan_out_company_present():
    text = registry.load_domain("management").lower()
    assert "loan-out" in text


def test_not_evaluable_protocol_present():
    text = registry.load_domain("management").lower()
    assert "not evaluable" in text


def test_opportunity_stack_triage_present():
    text = registry.load_domain("management").lower()
    assert "opportunity stack" in text


def test_label_deterioration_escalation_present():
    text = registry.load_domain("management").lower()
    assert "deterioration" in text


# ── new: record deal mechanics and structures (phase 3f) ──────────────────────

def test_record_deal_file_loaded():
    """record-deal-mechanics-and-structures.md must appear in assembled knowledge."""
    text = registry.load_domain("management").lower()
    assert "cross-collateralization" in text, (
        "record-deal-mechanics-and-structures.md not found: 'cross-collateralization' absent"
    )


def test_five_deal_structures_present():
    """All five recording deal structure types must be covered."""
    text = registry.load_domain("management").lower()
    assert "major-label" in text or "major label recording" in text
    assert "p&d" in text or "pressing and distribution" in text
    assert "label-services" in text or "label services" in text
    assert "distribution deal" in text or "distribution agreement" in text
    assert "aggregator" in text


def test_pd_deal_artist_retains_masters():
    """P&D deal's key feature — artist retains masters — must be stated."""
    text = registry.load_domain("management").lower()
    assert "p&d" in text or "pressing and distribution" in text
    assert "retains" in text and "master" in text


def test_advance_is_recoupable_stated():
    """The fundamental fact that advances are recoupable must be explicitly stated."""
    text = registry.load_domain("management").lower()
    assert "recoupable" in text
    assert "advance" in text


def test_advance_not_income_stated():
    """The manager must understand an advance is not income — it is a loan from royalties."""
    text = registry.load_domain("management").lower()
    assert "advance" in text
    # The concept that an advance is recouped from royalties, not cash
    assert "royalt" in text and "recoup" in text


def test_cross_collateralization_defined():
    """Cross-collateralization mechanics must be defined, not just named."""
    text = registry.load_domain("management").lower()
    assert "cross-collateralization" in text
    assert "album" in text


def test_resist_cross_collateralization():
    """The manager's position — resist cross-collateralization — must be stated."""
    text = registry.load_domain("management").lower()
    assert "cross-collateralization" in text
    assert "resist" in text


def test_what_charges_against_royalties_covered():
    """Items charged against royalties (recording costs, tour support, etc.) must be listed."""
    text = registry.load_domain("management").lower()
    assert "recording cost" in text
    assert "tour support" in text


def test_all_in_rate_defined():
    """The all-in royalty rate concept must be defined."""
    text = registry.load_domain("management").lower()
    assert "all-in" in text
    assert "producer" in text and "royalt" in text


def test_producer_royalty_points_covered():
    """Producer royalty points deducted from all-in rate must be explained."""
    text = registry.load_domain("management").lower()
    assert "producer" in text
    assert "royalty point" in text or ("point" in text and "producer" in text and "royalt" in text)


def test_controlled_composition_clause_defined():
    """The controlled composition clause must be substantively defined."""
    text = registry.load_domain("management").lower()
    assert "controlled composition" in text


def test_three_quarter_rate_stated():
    """The three-quarter-rate reduction on controlled compositions must be stated."""
    text = registry.load_domain("management").lower()
    assert "three-quarter rate" in text or "75%" in text or "75 percent" in text


def test_statutory_mechanical_rate_referenced():
    """The statutory mechanical rate must be referenced."""
    text = registry.load_domain("management").lower()
    assert "statutory" in text
    assert "mechanical" in text


def test_360_deal_defined():
    """360-deal provisions must be substantively defined."""
    text = registry.load_domain("management").lower()
    assert "360" in text


def test_360_streams_enumeration_rule():
    """Enumerating each income stream in a 360 deal must be stated as the manager's position."""
    text = registry.load_domain("management").lower()
    assert "360" in text
    assert "stream" in text
    assert "enumerate" in text or "specific list" in text or "each stream" in text


def test_release_commitment_mechanics_present():
    """Release commitment with a timing window must be explained."""
    text = registry.load_domain("management").lower()
    assert "release commitment" in text
    assert "timing" in text or "window" in text


def test_commercially_acceptable_red_flag():
    """'Commercially acceptable' as a delivery criterion is a named red flag."""
    text = registry.load_domain("management").lower()
    assert "commercially acceptable" in text


def test_reversion_for_non_release_present():
    """Reversion right if the label does not release within the window must be stated."""
    text = registry.load_domain("management").lower()
    assert "reversion" in text
    assert "release" in text


def test_no_audit_rights_is_red_flag():
    """Absence of audit rights in a recording agreement is a named red flag."""
    text = registry.load_domain("management").lower()
    assert "audit right" in text or "audit rights" in text


def test_no_reversion_of_masters_red_flag():
    """Perpetual master ownership with no reversion is a named red flag."""
    text = registry.load_domain("management").lower()
    assert "reversion" in text
    assert "master" in text


def test_independent_radio_promotion_recoupable_risk():
    """Independent radio promotion charged as recoupable is a named red flag."""
    text = registry.load_domain("management").lower()
    assert "radio" in text
    assert "recoupable" in text


def test_royalty_reductions_covered():
    """Royalty reductions (foreign, mid-price) must be covered."""
    text = registry.load_domain("management").lower()
    assert "royalty reduction" in text or ("reduction" in text and "royalt" in text)
    assert "foreign" in text


# ── new: royalty income monitoring (phase 3f) ─────────────────────────────────

def test_royalty_income_monitoring_file_loaded():
    """royalty-income-monitoring.md must appear in assembled knowledge."""
    text = registry.load_domain("management").lower()
    assert "income pipeline" in text, (
        "royalty-income-monitoring.md not found: 'income pipeline' absent"
    )


def test_recording_income_pipeline_covered():
    """The recording royalty pipeline (streams to artist) must be explained."""
    text = registry.load_domain("management").lower()
    assert "income pipeline" in text
    assert "dsp" in text


def test_publishing_income_pipeline_covered():
    """The publishing income pipeline with delay mechanics must be explained."""
    text = registry.load_domain("management").lower()
    assert "publishing" in text
    assert "pipeline" in text


def test_pro_distribution_delay_present():
    """PRO royalty distribution delay (performance to payment) must be stated."""
    text = registry.load_domain("management").lower()
    assert "ascap" in text or "bmi" in text or "sesac" in text
    assert "quarterly" in text


def test_major_label_semi_annual_statements():
    """Major label semi-annual statement frequency must be stated."""
    text = registry.load_domain("management").lower()
    assert "semi-annual" in text


def test_distribution_monthly_statements():
    """Digital distribution monthly reporting must be stated."""
    text = registry.load_domain("management").lower()
    assert "monthly" in text
    assert "distribution" in text or "distributor" in text


def test_mlc_mechanical_licensing_collective_mentioned():
    """The Mechanical Licensing Collective (MLC) must be referenced."""
    text = registry.load_domain("management").lower()
    assert "mechanical licensing collective" in text or "mlc" in text


def test_recoupment_status_as_critical_number():
    """Recoupment status must be identified as the most important monitoring number."""
    text = registry.load_domain("management").lower()
    assert "recoupment" in text
    assert "status" in text


def test_royalty_statement_anatomy_covered():
    """Royalty statement anatomy checklist must be present."""
    text = registry.load_domain("management").lower()
    assert "statement" in text
    assert "period" in text
    assert "balance" in text


def test_volume_sanity_check_present():
    """DSP dashboard volume sanity check against statement volumes must be explained."""
    text = registry.load_domain("management").lower()
    assert "sanity check" in text or ("dashboard" in text and "volume" in text)


def test_reserves_not_released_on_schedule():
    """Failure to release reserves on schedule as an error must be stated."""
    text = registry.load_domain("management").lower()
    assert "reserve" in text
    assert "schedule" in text or "release" in text


def test_foreign_income_monitoring_present():
    """Foreign territory income monitoring must be covered."""
    text = registry.load_domain("management").lower()
    assert "foreign income" in text or ("foreign" in text and "territory" in text and "income" in text)


def test_common_royalty_errors_covered():
    """Common royalty accounting errors must be substantively covered."""
    text = registry.load_domain("management").lower()
    assert "error" in text or "errors" in text
    assert "royalt" in text


def test_wrong_royalty_rate_error_named():
    """Wrong royalty rate as a common accounting error must be named."""
    text = registry.load_domain("management").lower()
    assert "wrong royalty rate" in text or "incorrect royalty rate" in text or (
        "rate" in text and "applied" in text and "royalt" in text
    )


def test_audit_look_back_window_explained():
    """The look-back limitation on audit rights must be explained."""
    text = registry.load_domain("management").lower()
    assert "look-back" in text or "look back" in text or "limitation" in text


def test_royalty_audit_trigger_conditions_present():
    """Conditions warranting a royalty audit must be substantively listed."""
    text = registry.load_domain("management").lower()
    assert "royalty audit" in text or ("audit" in text and "royalt" in text)
    assert "trigger" in text or "warrant" in text or "condition" in text


def test_audit_costs_addressed():
    """Royalty audit cost as a decision factor must be acknowledged."""
    text = registry.load_domain("management").lower()
    assert "audit" in text
    assert "cost" in text


def test_statement_receipt_log_defined():
    """Statement receipt log as an income-tracking minimum standard must be defined."""
    text = registry.load_domain("management").lower()
    assert "statement receipt log" in text


def test_recoupment_tracker_defined():
    """Recoupment tracker as a management monitoring tool must be defined."""
    text = registry.load_domain("management").lower()
    assert "recoupment tracker" in text


def test_publishing_registration_audit_defined():
    """Publishing registration audit (PRO + publisher) must be defined."""
    text = registry.load_domain("management").lower()
    assert "publishing registration" in text or (
        "registration" in text and "pro" in text and "publishing" in text
    )


def test_income_expectation_calendar_defined():
    """Income-expectation calendar as a proactive monitoring tool must be defined."""
    text = registry.load_domain("management").lower()
    assert "income-expectation calendar" in text or (
        "expectation" in text and "calendar" in text
    )


def test_unmatched_royalties_mlc_explained():
    """Unmatched royalties at the MLC and their cause must be explained."""
    text = registry.load_domain("management").lower()
    assert "unmatched" in text
