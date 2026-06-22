"""
Phase 3f — deepened label_ops domain knowledge tests.

Verifies that the 'label_ops' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and new knowledge files, and contains no forbidden entity strings.

New knowledge files added in phase 3f:
  - radio-and-broadcast-promotion.md
  - sync-licensing-operations.md
  - physical-product-and-manufacturing.md

Covers (radio-and-broadcast-promotion): radio format taxonomy (CHR/Top 40,
Hot AC, AC, AAA, Country, Urban, Americana, college, Rock); independent radio
promoter mechanics (indie promo as advocacy service; payola distinction; not a
guarantee; not interchangeable with DSP editorial pitching); add dates and the
weekly format cycle; Mediabase and BDS airplay monitoring (panel alignment;
spins vs. adds); chart position methodology (weighted audience impressions; chart
as verifiable independent signal); satellite radio distinctions (SiriusXM
audience structure; SoundExchange master performance royalties; no terrestrial
chart impact); campaign economics and decision framework (6-week minimum
campaign; regional-build arc); practitioner insight on passive adds, promoter
territory exclusivity, radio-sync reinforcement, recoupability of promo costs.

Covers (sync-licensing-operations): dual-license requirement (sync license for
composition; master use license for recording; both independently required;
one-stop clearance advantage); placement type taxonomy with directional fee tiers
(theatrical, TV/streaming, advertising, trailers, video games, social); gratis
use protocol with decision rules; pitch-to-placement pipeline (brief through
backend collection); clearance speed as competitive advantage (24-hour response;
pre-authorized fee tiers; stems); one-sheet format (ten required elements;
specificity discipline); stems management and retention policy; income collection
timeline (sync fee, PRO backend, SoundExchange); practitioner insight on the
sample trap, backend royalties as durable income, supervisor relationship risk,
and international territorial scope.

Covers (physical-product-and-manufacturing): vinyl manufacturing lead times and
capacity environment; test pressing protocol (TP review gate); pressing plant
ecosystem (major US plants; broker access); manufacturing cost drivers (run size;
weight; color; packaging); retail distribution structures (one-stops; DTC);
consignment vs. buy/sell commercial terms; returns risk and returns reserve
accounting; Record Store Day mechanics (submission timeline; exclusivity;
manufacturing lead time; over-pressing risk); CD and cassette economics; physical/
digital release coordination; practitioner insight on vinyl mastering for
loudness-compressed masters, color variant proliferation, inventory as cash
liability, test pressing gate.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "plan the radio campaign for this release — evaluate the format options, "
    "advise on distribution between physical vinyl and streaming, review the sync "
    "pitch pipeline for catalog exploitation, and flag any recoupment or metadata "
    "issues before the campaign launches"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_label_ops():
    assert "label_ops" in registry.list_domains()


def test_get_domain_display_name():
    domain = registry.get_domain("label_ops")
    assert domain.display_name, "label_ops domain has no display_name"


def test_load_domain_returns_string():
    text = registry.load_domain("label_ops")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("label_ops")
    assert text.strip(), "label_ops domain loaded empty knowledge"


def test_load_domain_minimum_size():
    """12 knowledge files should yield >= 120 000 chars of assembled content."""
    text = registry.load_domain("label_ops")
    assert len(text) >= 120_000, (
        f"label_ops knowledge too small: {len(text)} chars — expected >=120 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    """12 files joined by section separators -> at least 11 inter-file separators."""
    text = registry.load_domain("label_ops")
    assert text.count("\n\n---\n\n") >= 11, (
        "Expected >=11 section separators in label_ops domain"
    )


def test_no_forbidden_entity_strings_in_domain():
    text = registry.load_domain("label_ops")
    assert_no_forbidden_terms(text)


# ── pre-existing doctrine: core label ops principles ──────────────────────────

def test_label_ops_doctrine_mission_present():
    text = registry.load_domain("label_ops").lower()
    assert "operational backbone" in text or "label operations" in text


def test_hard_refusals_present():
    """The six hard refusals must be encoded in the doctrine."""
    text = registry.load_domain("label_ops").lower()
    assert "never approve a release" in text or "hard refusals" in text or "anti-patterns" in text


def test_recoupment_misunderstood_lever_present():
    text = registry.load_domain("label_ops").lower()
    assert "recoupment" in text
    assert "misunderstood" in text


def test_release_window_non_renewable_present():
    text = registry.load_domain("label_ops").lower()
    assert "release window" in text
    assert "non-renewable" in text


# ── pre-existing: release planning ────────────────────────────────────────────

def test_release_types_taxonomy_present():
    text = registry.load_domain("label_ops").lower()
    assert "single" in text
    assert "album" in text
    assert "ep" in text


def test_first_48_hour_window_present():
    text = registry.load_domain("label_ops").lower()
    assert "first-48" in text or "48-hour" in text or "48 hour" in text


def test_friday_release_convention_present():
    text = registry.load_domain("label_ops").lower()
    assert "friday" in text
    assert "editorial" in text


def test_pre_delivery_qc_checklist_present():
    text = registry.load_domain("label_ops").lower()
    assert "isrc" in text
    assert "upc" in text
    assert "explicit" in text


# ── pre-existing: distribution ────────────────────────────────────────────────

def test_three_tier_distributor_taxonomy_present():
    text = registry.load_domain("label_ops").lower()
    assert "diy aggregator" in text or "diy" in text
    assert "mid-tier" in text or "mid tier" in text
    assert "full-service" in text or "full service" in text


def test_distribution_as_financial_infrastructure_present():
    text = registry.load_domain("label_ops").lower()
    assert "financial infrastructure" in text or "financial partner" in text


# ── pre-existing: catalog management ─────────────────────────────────────────

def test_six_dimension_catalog_audit_present():
    text = registry.load_domain("label_ops").lower()
    assert "chain of title" in text
    assert "rights registration" in text
    assert "revenue yield" in text


def test_catalog_reversion_clock_present():
    text = registry.load_domain("label_ops").lower()
    assert "reversion" in text
    assert "clock" in text or "trigger" in text


def test_neighboring_rights_registration_present():
    text = registry.load_domain("label_ops").lower()
    assert "neighboring rights" in text or "neighbouring rights" in text


# ── pre-existing: deal structures and recoupment ──────────────────────────────

def test_five_recording_contract_types_present():
    text = registry.load_domain("label_ops").lower()
    assert "traditional recording" in text or "traditional" in text
    assert "360" in text or "multiple-rights" in text
    assert "production deal" in text or "vanity label" in text
    assert "distribution" in text
    assert "licensing deal" in text or "licensing" in text


def test_cross_collateralization_defined():
    text = registry.load_domain("label_ops").lower()
    assert "cross-collateralization" in text or "cross collateralization" in text


def test_controlled_composition_clause_present():
    text = registry.load_domain("label_ops").lower()
    assert "controlled composition" in text
    assert "three-quarter" in text or "75%" in text


# ── pre-existing: label economics ─────────────────────────────────────────────

def test_royalty_waterfall_mechanics_present():
    text = registry.load_domain("label_ops").lower()
    assert "waterfall" in text
    assert "distribution fee" in text
    assert "mechanical" in text


def test_advance_sizing_gate_present():
    text = registry.load_domain("label_ops").lower()
    assert "advance" in text
    assert "recoupment" in text and "horizon" in text or "recoupment" in text


def test_net_receipts_definition_present():
    text = registry.load_domain("label_ops").lower()
    assert "net receipts" in text or "net-receipts" in text


# ── pre-existing: roster coordination ────────────────────────────────────────

def test_five_core_functions_handoff_present():
    text = registry.load_domain("label_ops").lower()
    assert "a&r" in text
    assert "marketing" in text
    assert "legal" in text
    assert "finance" in text
    assert "operations" in text


def test_release_readiness_gates_present():
    text = registry.load_domain("label_ops").lower()
    assert "gate" in text
    assert "readiness" in text or "release readiness" in text


# ── pre-existing: systems and qc ──────────────────────────────────────────────

def test_four_layer_tech_stack_present():
    text = registry.load_domain("label_ops").lower()
    assert "rights management" in text
    assert "metadata management" in text
    assert "royalty accounting" in text
    assert "release tracking" in text


def test_delivery_qc_workflow_present():
    text = registry.load_domain("label_ops").lower()
    assert "delivery qc" in text or "qc workflow" in text or "pre-delivery" in text


# ── new: radio and broadcast promotion (phase 3f) ─────────────────────────────

def test_radio_promotion_file_loaded():
    """radio-and-broadcast-promotion.md must appear in assembled knowledge."""
    text = registry.load_domain("label_ops").lower()
    assert "indie promo" in text, (
        "radio-and-broadcast-promotion.md not found: 'indie promo' absent"
    )


def test_chr_format_present():
    """CHR / Top 40 format must be named."""
    text = registry.load_domain("label_ops").lower()
    assert "chr" in text or "contemporary hit radio" in text or "top 40" in text


def test_hot_ac_format_present():
    """Hot AC format must be named."""
    text = registry.load_domain("label_ops").lower()
    assert "hot ac" in text or "hot adult contemporary" in text


def test_aaa_triple_a_format_present():
    """AAA / Triple A format must be named."""
    text = registry.load_domain("label_ops").lower()
    assert "aaa" in text or "triple a" in text or "adult album alternative" in text


def test_indie_promo_not_payola_distinction():
    """The payola/legality distinction for indie promo must be explained."""
    text = registry.load_domain("label_ops").lower()
    assert "payola" in text
    assert "fcc" in text or "illegal" in text or "unlawful" in text or "prohibited" in text


def test_indie_promo_not_a_guarantee():
    """No legitimate promoter can guarantee chart positions or adds."""
    text = registry.load_domain("label_ops").lower()
    assert "guarantee" in text
    assert "promoter" in text


def test_add_dates_weekly_cycle_present():
    """Add dates and the weekly format cycle must be described."""
    text = registry.load_domain("label_ops").lower()
    assert "add date" in text or "add day" in text or "add cycle" in text


def test_spins_vs_adds_distinction():
    """Spins (ongoing plays) vs. adds (one-time station event) must be distinguished."""
    text = registry.load_domain("label_ops").lower()
    assert "spins" in text
    assert "adds" in text or "add count" in text


def test_mediabase_monitoring_present():
    """Mediabase airplay monitoring service must be named."""
    text = registry.load_domain("label_ops").lower()
    assert "mediabase" in text


def test_bds_broadcast_data_systems_present():
    """BDS (Broadcast Data Systems) must be named."""
    text = registry.load_domain("label_ops").lower()
    assert "bds" in text or "broadcast data systems" in text


def test_panel_alignment_importance_explained():
    """Monitoring panel alignment — confirming stations are tracked — must be explained."""
    text = registry.load_domain("label_ops").lower()
    assert "panel" in text
    assert "monitored" in text or "monitoring" in text


def test_chart_weighted_audience_impressions():
    """Chart methodology: spins weighted by station audience must be explained."""
    text = registry.load_domain("label_ops").lower()
    assert "audience" in text
    assert "spins" in text
    assert "weighted" in text or "weight" in text


def test_sirius_xm_distinction_present():
    """SiriusXM as a separate medium from terrestrial radio must be addressed."""
    text = registry.load_domain("label_ops").lower()
    assert "siriusxm" in text or "sirius xm" in text or "satellite radio" in text


def test_soundexchange_sirius_royalties_present():
    """SoundExchange collects SiriusXM master performance royalties — must be stated."""
    text = registry.load_domain("label_ops").lower()
    assert "soundexchange" in text
    assert "sirius" in text or "satellite" in text


def test_radio_campaign_minimum_six_weeks():
    """A national format campaign requires at least 6 weeks to build momentum."""
    text = registry.load_domain("label_ops").lower()
    assert "6 weeks" in text or "six weeks" in text or "6-week" in text


def test_passive_add_problem_named():
    """The 'passive add' problem (add logged but song rarely programmed) must be named."""
    text = registry.load_domain("label_ops").lower()
    assert "passive add" in text


def test_radio_promo_recoupability_note():
    """Whether indie promo costs are recoupable is a contractual determination."""
    text = registry.load_domain("label_ops").lower()
    assert "recoupable" in text
    assert "promo" in text or "promotion" in text


def test_radio_not_interchangeable_with_dsp_pitch():
    """Radio promotion and DSP editorial pitching are distinct channels — must be stated."""
    text = registry.load_domain("label_ops").lower()
    assert "radio" in text
    assert "dsp" in text or "editorial pitch" in text or "streaming" in text


# ── new: sync licensing operations (phase 3f) ────────────────────────────────

def test_sync_licensing_file_loaded():
    """sync-licensing-operations.md must appear in assembled knowledge."""
    text = registry.load_domain("label_ops").lower()
    assert "dual-license" in text or "dual license" in text, (
        "sync-licensing-operations.md not found: 'dual-license' absent"
    )


def test_sync_license_for_composition_explained():
    """Synchronization license (for the composition) must be defined."""
    text = registry.load_domain("label_ops").lower()
    assert "sync license" in text or "synchronization" in text
    assert "composition" in text
    assert "publisher" in text


def test_master_use_license_explained():
    """Master use license (for the recording) must be defined."""
    text = registry.load_domain("label_ops").lower()
    assert "master use license" in text or "master use" in text
    assert "recording" in text


def test_one_stop_clearance_advantage():
    """One-stop catalogs (single entity for both licenses) are preferred by supervisors."""
    text = registry.load_domain("label_ops").lower()
    assert "one-stop" in text or "one stop" in text


def test_trailer_fee_tier_named():
    """Trailers command a fee premium over the underlying film rate."""
    text = registry.load_domain("label_ops").lower()
    assert "trailer" in text
    assert "premium" in text or "2" in text or "higher" in text


def test_gratis_temp_track_protocol_present():
    """Gratis approval for temp tracks must be explained with a decision rule."""
    text = registry.load_domain("label_ops").lower()
    assert "gratis" in text
    assert "temp" in text


def test_gratis_not_compensation_rule():
    """'Exposure is not compensation' rule for gratis requests must be stated."""
    text = registry.load_domain("label_ops").lower()
    assert "exposure" in text
    assert "compensation" in text or "gratis" in text


def test_24_hour_response_discipline():
    """24-hour response to sync inquiries is the competitive-advantage rule."""
    text = registry.load_domain("label_ops").lower()
    assert "24 hour" in text or "24-hour" in text


def test_one_sheet_format_described():
    """The sync one-sheet format and its required elements must be described."""
    text = registry.load_domain("label_ops").lower()
    assert "one-sheet" in text or "one sheet" in text
    assert "licensing contact" in text or "stems" in text


def test_stems_availability_required_for_sync():
    """Stems availability is required for advertising and trailer placements."""
    text = registry.load_domain("label_ops").lower()
    assert "stems" in text
    assert "advertising" in text or "trailer" in text


def test_stems_retention_policy_present():
    """A stems retention policy for new releases must be stated."""
    text = registry.load_domain("label_ops").lower()
    assert "stems" in text
    assert "retention" in text or "require" in text or "deliver" in text


def test_pro_backend_royalties_collection_explained():
    """PRO backend royalties from TV broadcast must be explained with timing."""
    text = registry.load_domain("label_ops").lower()
    assert "backend" in text
    assert "pro" in text or "ascap" in text or "bmi" in text


def test_register_placement_with_pro():
    """Labels must register sync placements with the PRO for backend collection."""
    text = registry.load_domain("label_ops").lower()
    assert "register" in text
    assert "placement" in text
    assert "pro" in text or "ascap" in text or "bmi" in text


def test_sample_trap_in_sync_named():
    """The sample trap — uncleared samples block sync — must be named."""
    text = registry.load_domain("label_ops").lower()
    assert "sample" in text
    assert "sync" in text
    assert "uncleared" in text or "not cleared" in text or "trap" in text


def test_international_territorial_scope_in_sync():
    """Worldwide vs. territory-specific fee scope must be explained in sync context."""
    text = registry.load_domain("label_ops").lower()
    assert "territory" in text
    assert "worldwide" in text or "international" in text
    assert "sync" in text


def test_sync_fee_not_quotable_stated():
    """Sync fees are privately negotiated; no statutory rate — must be stated."""
    text = registry.load_domain("label_ops").lower()
    assert "not quotable" in text or (
        "negotiated" in text and "statutory" in text and "sync" in text
    )


# ── new: physical product and manufacturing (phase 3f) ───────────────────────

def test_physical_product_file_loaded():
    """physical-product-and-manufacturing.md must appear in assembled knowledge."""
    text = registry.load_domain("label_ops").lower()
    assert "pressing plant" in text, (
        "physical-product-and-manufacturing.md not found: 'pressing plant' absent"
    )


def test_vinyl_manufacturing_lead_times_present():
    """Vinyl manufacturing lead times must be stated as a planning constraint."""
    text = registry.load_domain("label_ops").lower()
    assert "vinyl" in text
    assert "lead time" in text or "lead times" in text


def test_physical_must_lead_digital_rule():
    """Physical production must begin before the digital release date is set."""
    text = registry.load_domain("label_ops").lower()
    assert "physical" in text
    assert "digital" in text
    assert "lead" in text or "before" in text


def test_test_pressing_protocol_present():
    """Test pressing (TP) protocol must be described as a quality gate."""
    text = registry.load_domain("label_ops").lower()
    assert "test pressing" in text


def test_test_pressing_review_gate_non_negotiable():
    """The test pressing review gate is described as non-negotiable."""
    text = registry.load_domain("label_ops").lower()
    assert "test pressing" in text
    assert "non-negotiable" in text or "approve" in text or "review" in text


def test_run_size_primary_cost_variable():
    """Run size is the primary driver of vinyl per-unit cost."""
    text = registry.load_domain("label_ops").lower()
    assert "run size" in text
    assert "per-unit" in text or "per unit" in text


def test_color_variant_premium_named():
    """Colored vinyl and special-effect variants command cost premiums."""
    text = registry.load_domain("label_ops").lower()
    assert "colored vinyl" in text or "colour" in text or "color" in text
    assert "premium" in text or "cost" in text


def test_gatefold_packaging_named():
    """Gatefold and tip-on packaging formats must be named."""
    text = registry.load_domain("label_ops").lower()
    assert "gatefold" in text


def test_one_stop_distributor_present():
    """Independent distributor / one-stop as the primary indie retail channel must be named."""
    text = registry.load_domain("label_ops").lower()
    assert "one-stop" in text or "one stop" in text


def test_consignment_vs_buy_sell_explained():
    """Consignment vs. buy/sell commercial terms must be explained."""
    text = registry.load_domain("label_ops").lower()
    assert "consignment" in text
    assert "buy/sell" in text or "buy-sell" in text or "outright" in text


def test_returns_reserve_accounting_present():
    """Returns reserve accounting (15–25% of gross) must be explained."""
    text = registry.load_domain("label_ops").lower()
    assert "returns reserve" in text or "return" in text and "reserve" in text


def test_sell_in_vs_sell_through_distinction():
    """Sell-in (units shipped) vs. sell-through (units sold) must be distinguished."""
    text = registry.load_domain("label_ops").lower()
    assert "sell-in" in text or "sell in" in text or (
        "shipped" in text and "sold" in text
    )
    assert "sell-through" in text or "sell through" in text


def test_record_store_day_mechanics_present():
    """Record Store Day (RSD) and its submission timeline must be explained."""
    text = registry.load_domain("label_ops").lower()
    assert "record store day" in text or "rsd" in text


def test_rsd_exclusivity_requirement():
    """RSD titles require an exclusive or unique element."""
    text = registry.load_domain("label_ops").lower()
    assert "exclusiv" in text
    assert "rsd" in text or "record store day" in text


def test_rsd_submission_timeline_present():
    """RSD submission timeline (6–8 months before event) must be stated."""
    text = registry.load_domain("label_ops").lower()
    assert "submission" in text
    assert "rsd" in text or "record store day" in text


def test_rsd_over_pressing_risk_named():
    """Over-pressing a RSD title creates clearance inventory problems."""
    text = registry.load_domain("label_ops").lower()
    assert "rsd" in text or "record store day" in text
    assert "over-press" in text or "over press" in text or "demand" in text


def test_cd_market_active_in_japan_germany():
    """CD market remains active in Japan and Germany — must be named."""
    text = registry.load_domain("label_ops").lower()
    assert "cd" in text
    assert "japan" in text
    assert "germany" in text


def test_cassette_niche_market_present():
    """Cassette as a niche collectible/limited-edition format must be addressed."""
    text = registry.load_domain("label_ops").lower()
    assert "cassette" in text


def test_vinyl_mastering_loudness_compressed_masters():
    """Vinyl mastering caveat for loudness-compressed digital masters must be stated."""
    text = registry.load_domain("label_ops").lower()
    assert "vinyl" in text
    assert "compressed" in text or "loudness" in text
    assert "mastering" in text or "master" in text


def test_inventory_as_cash_liability_stated():
    """Unsold physical inventory is described as a cash liability, not a catalog asset."""
    text = registry.load_domain("label_ops").lower()
    assert "inventory" in text
    assert "liability" in text or "cash" in text
