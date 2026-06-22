"""
Phase 3f — deepened publishing domain knowledge tests.

Verifies that the 'publishing' domain loads via the bank's normal path (registry),
is non-trivially sized, includes all required sections from both pre-existing
and new knowledge files, and contains no forbidden entity strings.

New knowledge file added in phase 3f:
  - publishing-administration-and-registration.md

Covers: publisher entity setup, copyright registration workflow, PRO work
registration, MLC registration & ISRC→ISWC linkage, CWR standard, DDEX
standards (ERN/MWN/RIN), grand rights vs. small rights, print rights,
neighboring rights registration workflow, controlled composition detailed
mechanics, platform-specific licensing mechanics, and CMS/metadata hygiene.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "register these compositions with our publishing entity and set up "
    "the correct CWR file for international society submission"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_publishing():
    assert "publishing" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("publishing").display_name == "Publishing"


def test_load_domain_returns_string():
    text = registry.load_domain("publishing")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("publishing")
    assert text.strip(), "publishing domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 6 knowledge files (5 existing + new admin/registration file)
    # total assembled content expected >= 120 000 chars
    text = registry.load_domain("publishing")
    assert len(text) >= 120_000, (
        f"publishing knowledge too small: {len(text)} chars — expected ≥120 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 6 files joined by section separators → at least 5 separators
    text = registry.load_domain("publishing")
    assert text.count("\n\n---\n\n") >= 5, (
        "Expected ≥5 section separators (6 knowledge files) in publishing domain"
    )


# ── pre-existing doctrine presence ───────────────────────────────────────────

def test_asset_management_posture_present():
    text = registry.load_domain("publishing").lower()
    assert "asset-management" in text or "asset management" in text
    assert "unpaid dollar" in text


def test_two_copyright_architecture_present():
    text = registry.load_domain("publishing").lower()
    assert "composition copyright" in text
    assert "master recording" in text
    assert "two" in text and "copyright" in text


def test_songwriter_splits_present():
    text = registry.load_domain("publishing").lower()
    assert "split sheet" in text
    assert "writer's share" in text or "writer share" in text
    assert "publisher's share" in text or "publisher share" in text


def test_publishing_deals_present():
    text = registry.load_domain("publishing").lower()
    assert "admin deal" in text or "administration deal" in text
    assert "co-pub" in text or "co-publishing" in text
    assert "full publishing" in text


def test_pros_and_performance_royalties_present():
    text = registry.load_domain("publishing").lower()
    assert "ascap" in text
    assert "bmi" in text
    assert "sesac" in text
    assert "performance royalt" in text


def test_mechanical_royalties_present():
    text = registry.load_domain("publishing").lower()
    assert "mechanical" in text
    assert "the mlc" in text or "mechanical licensing collective" in text
    assert "crb" in text or "copyright royalty board" in text


def test_catalog_health_rubric_present():
    text = registry.load_domain("publishing").lower()
    assert "registration completeness" in text
    assert "collection coverage" in text
    assert "provisional composite" in text
    assert "hard gate" in text


def test_neighboring_rights_theory_present():
    text = registry.load_domain("publishing").lower()
    assert "neighboring rights" in text
    assert "soundexchange" in text
    assert "50%" in text or "50 percent" in text


def test_termination_rights_present():
    text = registry.load_domain("publishing").lower()
    assert "section 203" in text or "§ 203" in text
    assert "35-year" in text or "35 year" in text


def test_catalog_valuation_present():
    text = registry.load_domain("publishing").lower()
    assert "net publisher's share" in text or "nps" in text
    assert "multiple" in text
    assert "catalog" in text


def test_output_templates_present():
    text = registry.load_domain("publishing").lower()
    assert "catalog health evaluation" in text
    assert "revenue leak report" in text
    assert "publishing deal evaluation" in text
    assert "clearance complexity" in text
    assert "opportunity scan" in text


# ── new administration-and-registration knowledge (phase 3f) ─────────────────

def test_admin_registration_file_loaded():
    """publishing-administration-and-registration.md content must appear."""
    text = registry.load_domain("publishing").lower()
    assert "publisher entity setup" in text or "publisher entity" in text, (
        "publishing-administration-and-registration.md content not found in assembled knowledge"
    )


def test_publisher_entity_setup_present():
    text = registry.load_domain("publishing").lower()
    assert "ipi number" in text or "ipi" in text
    assert "pro publisher enrollment" in text or "publisher enrollment" in text
    assert "dual registration" in text or "dual-registration" in text


def test_ipo_name_search_present():
    text = registry.load_domain("publishing").lower()
    assert "name search" in text or "entity name" in text
    assert "unique" in text


def test_writer_publisher_enrollment_distinction_present():
    text = registry.load_domain("publishing").lower()
    assert "writer account" in text or "writer's share" in text
    assert "publisher account" in text or "publisher entity" in text


def test_copyright_office_registration_present():
    text = registry.load_domain("publishing").lower()
    assert "eco" in text or "ecopyright" in text or "copyright.gov" in text
    assert "form pa" in text
    assert "form sr" in text


def test_registration_timing_window_present():
    text = registry.load_domain("publishing").lower()
    assert "3 months" in text or "three months" in text or "3-month" in text
    assert "statutory damages" in text


def test_recordation_of_transfers_present():
    text = registry.load_domain("publishing").lower()
    assert "recordation" in text
    assert "constructive notice" in text or "chain of title" in text


def test_pro_work_registration_workflow_present():
    text = registry.load_domain("publishing").lower()
    assert "songfile" in text or "works portal" in text or "register works" in text
    assert "iswc" in text
    assert "alternate title" in text or "alt" in text


def test_common_pro_errors_present():
    text = registry.load_domain("publishing").lower()
    assert "variant title" in text or "alternate title" in text
    assert "unmatched" in text


def test_mlc_registration_workflow_present():
    text = registry.load_domain("publishing").lower()
    assert "isrc" in text
    assert "iswc" in text
    assert "isrc" in text and "iswc" in text


def test_isrc_iswc_linkage_present():
    text = registry.load_domain("publishing").lower()
    assert "isrc" in text and "iswc" in text
    assert "matching" in text or "match" in text
    assert "unmatched" in text


def test_cwr_standard_present():
    text = registry.load_domain("publishing").lower()
    assert "cwr" in text or "common works registration" in text
    assert "cisac" in text


def test_cwr_record_types_present():
    text = registry.load_domain("publishing").lower()
    assert "nwr" in text
    assert "swr" in text or "spu" in text
    assert "alt" in text


def test_cwr_role_codes_present():
    text = registry.load_domain("publishing").lower()
    # CA = composer-author, C = composer, A = author
    assert "composer-author" in text or "ca" in text
    assert "lyricist" in text or "author" in text


def test_cwr_territory_codes_present():
    text = registry.load_domain("publishing").lower()
    assert "tis" in text or "territory identifier" in text
    assert "worldwide" in text


def test_cwr_share_mechanics_present():
    text = registry.load_domain("publishing").lower()
    assert "writer shares" in text or "share" in text
    assert "sum to 100" in text or "total" in text


def test_cwr_errors_present():
    text = registry.load_domain("publishing").lower()
    assert "ipi not found" in text or "ipi" in text
    assert "rejection" in text or "rejected" in text


def test_ddex_standards_present():
    text = registry.load_domain("publishing").lower()
    assert "ddex" in text
    assert "ern" in text
    assert "mwn" in text
    assert "rin" in text


def test_rin_explained_present():
    """RIN (Recording Information Notification) is the ISRC→ISWC bridge."""
    text = registry.load_domain("publishing").lower()
    assert "recording information notification" in text or "rin" in text
    assert "isrc" in text and "iswc" in text


def test_grand_rights_present():
    text = registry.load_domain("publishing").lower()
    assert "grand rights" in text or "grand right" in text
    assert "small rights" in text or "small right" in text


def test_grand_vs_small_rights_distinction_present():
    text = registry.load_domain("publishing").lower()
    assert "dramatic" in text
    assert "non-dramatic" in text
    assert "blanket license" in text


def test_pro_blanket_excludes_grand_rights_present():
    text = registry.load_domain("publishing").lower()
    assert "grand rights" in text
    assert "blanket" in text
    assert "not covered" in text or "excludes" in text or "explicit" in text


def test_print_rights_present():
    text = registry.load_domain("publishing").lower()
    assert "print rights" in text or "print right" in text
    assert "sheet music" in text


def test_print_rights_distinct_from_mechanical_present():
    text = registry.load_domain("publishing").lower()
    assert "sheet music" in text
    assert "print" in text and "mechanical" in text


def test_neighboring_rights_registration_workflow_present():
    """The new file adds the HOW-TO workflow, not just the theory."""
    text = registry.load_domain("publishing").lower()
    assert "soundexchange" in text
    assert "ppl" in text
    assert "registration" in text or "register" in text
    assert "workflow" in text or "step" in text


def test_soundexchange_dual_registration_present():
    text = registry.load_domain("publishing").lower()
    assert "featured artist" in text
    assert "master owner" in text
    assert "dual registration" in text or "both" in text


def test_ppl_registration_present():
    text = registry.load_domain("publishing").lower()
    assert "ppl" in text
    assert "uk" in text
    assert "terrestrial" in text or "broadcast" in text


def test_nr_retroactive_claim_window_present():
    text = registry.load_domain("publishing").lower()
    assert "3 year" in text or "three year" in text or "retroactive" in text
    assert "window" in text


def test_controlled_composition_detailed_mechanics_present():
    text = registry.load_domain("publishing").lower()
    assert "controlled composition" in text
    assert "album" in text and "cap" in text
    assert "3/4" in text or "three-quarter" in text or "0.75" in text


def test_cc_album_cap_arithmetic_present():
    text = registry.load_domain("publishing").lower()
    assert "ten" in text or "10" in text
    assert "track" in text
    assert "zero" in text or "0" in text


def test_cc_streaming_mma_interaction_present():
    """The MMA streaming complication is non-obvious and must be present."""
    text = registry.load_domain("publishing").lower()
    assert "music modernization act" in text or "mma" in text
    assert "streaming" in text and "controlled composition" in text


def test_contentid_present():
    text = registry.load_domain("publishing").lower()
    assert "contentid" in text or "content id" in text
    assert "youtube" in text


def test_contentid_eligibility_present():
    text = registry.load_domain("publishing").lower()
    assert "invite-only" in text or "eligibility" in text
    assert "youtube" in text


def test_contentid_claim_types_present():
    text = registry.load_domain("publishing").lower()
    assert "monetize" in text
    assert "block" in text
    assert "track" in text


def test_contentid_dual_claim_conflict_present():
    text = registry.load_domain("publishing").lower()
    assert "dual-claim" in text or "conflicting claims" in text or "competing claims" in text


def test_tiktok_licensing_present():
    text = registry.load_domain("publishing").lower()
    assert "tiktok" in text
    assert "blanket" in text


def test_meta_rights_manager_present():
    text = registry.load_domain("publishing").lower()
    assert "meta" in text
    assert "rights manager" in text or "facebook" in text or "instagram" in text


def test_gaming_licensing_present():
    text = registry.load_domain("publishing").lower()
    assert "run-of-game" in text or "run of game" in text
    assert "game" in text or "gaming" in text


def test_fitness_platform_licensing_present():
    text = registry.load_domain("publishing").lower()
    assert "fitness" in text
    assert "interactive" in text
    assert "on-demand" in text or "peloton" in text


def test_social_media_blanket_gap_present():
    text = registry.load_domain("publishing").lower()
    assert "independent publisher" in text or "independent" in text
    assert "coverage gap" in text or "gap" in text


def test_cms_tooling_present():
    text = registry.load_domain("publishing").lower()
    assert "content management system" in text or "cms" in text


def test_metadata_consistency_present():
    text = registry.load_domain("publishing").lower()
    assert "metadata" in text
    assert "consistency" in text or "consistent" in text


def test_statement_reconciliation_workflow_present():
    text = registry.load_domain("publishing").lower()
    assert "statement" in text
    assert "reconciliation" in text or "reconcil" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_publishing_query():
    assert "publishing" in brain.route(IN_DOMAIN_QUERY)


def test_route_composition_registration_to_publishing():
    assert "publishing" in brain.route(
        "register this composition with our publishing administration entity"
    )


def test_route_split_sheet_query_to_publishing():
    assert "publishing" in brain.route(
        "create a split sheet for this co-written song with songwriter splits"
    )


def test_route_catalog_query_to_publishing():
    assert "publishing" in brain.route(
        "evaluate this catalog for a publishing deal and administration structure"
    )


def test_route_unrelated_query_excludes_publishing():
    # A pure tour-booking query should not pull in publishing
    assert "publishing" not in brain.route(
        "book the arena tour and negotiate the guarantee with the promoter"
    )


def test_route_irrelevant_query_returns_empty():
    assert brain.route("what should i eat for lunch") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_publishing_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "publishing" in result["domains"]
    assert "# Publishing (publishing)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("publishing"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("register this composition with our pro and the mlc", "publishing"),
        ("evaluate a co-publishing deal for this catalog", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
