"""
Phase 3f — deepened legal domain knowledge tests.

Verifies that the 'legal' domain loads via the bank's normal path (registry),
is non-trivially sized, includes all required sections from both pre-existing
and new knowledge files, and contains no forbidden entity strings.

One new knowledge file was added in phase 3f:
  - music-law-mechanics.md (statutory-and-deal-mechanics)

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "review this recording contract for red-flag clauses and assess the legal "
    "risk across all eight dimensions including audit rights and reversion"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_legal():
    assert "legal" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("legal").display_name == "Legal & Contracts"


def test_load_domain_returns_string():
    text = registry.load_domain("legal")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("legal")
    assert text.strip(), "legal domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 6 knowledge files → expect at least 80 000 chars of assembled content
    text = registry.load_domain("legal")
    assert len(text) >= 80_000, (
        f"legal knowledge too small: {len(text)} chars — expected ≥80 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 6 files joined by section separators → at least 5 separators between files
    text = registry.load_domain("legal")
    assert text.count("\n\n---\n\n") >= 5, (
        "Expected ≥5 section separators (6 knowledge files) in legal domain"
    )


# ── pre-existing doctrine presence ────────────────────────────────────────────

def test_legal_doctrine_present():
    text = registry.load_domain("legal").lower()
    assert "domain constraint" in text
    assert "drafts and flags" in text or "drafts" in text
    assert "qualified entertainment counsel" in text


def test_red_flag_sequence_present():
    text = registry.load_domain("legal").lower()
    assert "rights grant" in text
    assert "recoupment" in text
    assert "audit rights" in text


def test_deal_type_classification_present():
    text = registry.load_domain("legal").lower()
    assert "recording contract" in text or "recording agreement" in text
    assert "management agreement" in text
    assert "license" in text


def test_chain_of_title_framework_present():
    text = registry.load_domain("legal").lower()
    assert "chain of title" in text
    assert "blocking defect" in text
    assert "work-for-hire" in text or "work for hire" in text


def test_infringement_framework_present():
    text = registry.load_domain("legal").lower()
    assert "substantial similarity" in text
    assert "access" in text
    assert "not a legal opinion" in text


def test_deal_quality_rubric_present():
    text = registry.load_domain("legal").lower()
    assert "eight-dimension" in text or "eight dimension" in text or "dimension" in text
    assert "hard gate" in text
    assert "provisional composite" in text


def test_contract_architecture_present():
    text = registry.load_domain("legal").lower()
    assert "controlled composition" in text
    assert "cross-collateral" in text
    assert "audit rights" in text


def test_copyright_ip_present():
    text = registry.load_domain("legal").lower()
    assert "two copyrights" in text or "sound recording" in text
    assert "trademark" in text
    assert "neighboring rights" in text


def test_output_templates_present():
    text = registry.load_domain("legal").lower()
    assert "contract / deal review report" in text or "contract/deal review" in text
    assert "chain-of-title checklist" in text
    assert "business entity identification" in text


# ── new music-law-mechanics knowledge (phase 3f) ──────────────────────────────

def test_music_law_mechanics_file_loaded():
    """music-law-mechanics.md content must appear in the assembled knowledge."""
    text = registry.load_domain("legal").lower()
    assert "statutory framework" in text or "section 203" in text, (
        "music-law-mechanics.md content not found in assembled legal knowledge"
    )


def test_termination_rights_section_203_present():
    text = registry.load_domain("legal").lower()
    assert "section 203" in text
    assert "35 years" in text
    assert "inalienability" in text or "inalienable" in text


def test_termination_rights_section_304_present():
    text = registry.load_domain("legal").lower()
    assert "section 304" in text
    assert "56 years" in text


def test_termination_wfh_exclusion_present():
    text = registry.load_domain("legal").lower()
    assert "works-for-hire exclusion" in text or "wfh works cannot be terminated" in text or \
           "wfh" in text and "termination" in text


def test_compulsory_mechanical_section_115_present():
    text = registry.load_domain("legal").lower()
    assert "section 115" in text
    assert "compulsory mechanical" in text or "compulsory" in text


def test_mma_mlc_present():
    text = registry.load_domain("legal").lower()
    assert "music modernization act" in text
    assert "mechanical licensing collective" in text or "mlc" in text


def test_blanket_license_present():
    text = registry.load_domain("legal").lower()
    assert "blanket" in text
    assert "blanket license" in text or "blanket mechanical" in text


def test_unmatched_mechanicals_present():
    text = registry.load_domain("legal").lower()
    assert "unmatched" in text
    assert "black box" in text or "unmatched mechanical" in text


def test_360_deal_anatomy_present():
    text = registry.load_domain("legal").lower()
    assert "360" in text
    assert "multiple-rights" in text or "multiple rights" in text or "360-degree" in text


def test_360_revenue_categories_present():
    text = registry.load_domain("legal").lower()
    assert "touring" in text or "live performance" in text
    assert "merchandise" in text
    assert "endorsement" in text


def test_360_identification_protocol_present():
    text = registry.load_domain("legal").lower()
    assert "gross vs. net" in text or "gross vs net" in text or \
           ("gross" in text and "net" in text)


def test_sample_clearance_workflow_present():
    text = registry.load_domain("legal").lower()
    assert "sample clearance" in text
    assert "master use license" in text or "master recording" in text
    assert "composition clearance" in text or "composition" in text and "clearance" in text


def test_sample_clearance_bilateral_present():
    text = registry.load_domain("legal").lower()
    assert "bilateral" in text or ("master" in text and "composition" in text and "both" in text)


def test_recursive_clearance_present():
    text = registry.load_domain("legal").lower()
    assert "recursive" in text or "sampled work itself contains a sample" in text


def test_soundexchange_mechanics_present():
    text = registry.load_domain("legal").lower()
    assert "soundexchange" in text
    assert "non-interactive" in text
    assert "45%" in text


def test_soundexchange_direct_payment_present():
    """The key non-obvious fact: 45% flows directly to artist, NOT through label account."""
    text = registry.load_domain("legal").lower()
    assert "not recoupable" in text or "bypasses" in text or \
           "directly" in text and "artist" in text and "soundexchange" in text


def test_content_id_architecture_present():
    text = registry.load_domain("legal").lower()
    assert "content id" in text or "content-id" in text
    assert "youtube" in text


def test_digital_licensing_interactive_noninteractive_present():
    text = registry.load_domain("legal").lower()
    assert "interactive" in text
    assert "non-interactive" in text


def test_loi_deal_memo_trap_present():
    text = registry.load_domain("legal").lower()
    assert "letter of intent" in text or "loi" in text
    assert "deal memo" in text


def test_oral_agreements_trap_present():
    text = registry.load_domain("legal").lower()
    assert "oral agreement" in text or "oral agreements" in text
    assert "17 usc" in text or "section 204" in text or "in writing" in text


def test_side_letters_present():
    text = registry.load_domain("legal").lower()
    assert "side letter" in text


def test_option_agreement_present():
    text = registry.load_domain("legal").lower()
    assert "option" in text
    assert "first-look" in text or "first look" in text


def test_key_statutes_table_present():
    text = registry.load_domain("legal").lower()
    assert "17 usc" in text
    assert "dmca" in text or "§ 512" in text or "512" in text
    assert "berne" in text


def test_recoupment_unrecouped_position_present():
    text = registry.load_domain("legal").lower()
    assert "unrecouped" in text
    assert "royalty account" in text


def test_reserve_against_royalties_present():
    text = registry.load_domain("legal").lower()
    assert "reserve against royalties" in text or "reserve" in text
    assert "holdback" in text or "withheld" in text or "reserve" in text


def test_copyright_registration_workflow_present():
    text = registry.load_domain("legal").lower()
    assert "form pa" in text or "form sr" in text
    assert "statutory damages" in text
    assert "three months" in text or "3 months" in text


def test_audit_protocol_present():
    text = registry.load_domain("legal").lower()
    assert "audit window" in text
    assert "frequency cap" in text or "cost allocation" in text


def test_audit_window_vs_dispute_window_distinction_present():
    """Non-obvious distinction: audit window ≠ statement dispute window."""
    text = registry.load_domain("legal").lower()
    assert "dispute window" in text or "statement dispute" in text


def test_currency_sensitive_flag_present():
    text = registry.load_domain("legal").lower()
    assert "currency-sensitive" in text or "currency sensitive" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_contract_review_query_to_legal():
    assert "legal" in brain.route(IN_DOMAIN_QUERY)


def test_route_copyright_query_to_legal():
    assert "legal" in brain.route(
        "analyze the copyright ownership and check the chain of title for this recording"
    )


def test_route_nda_query_to_legal():
    assert "legal" in brain.route(
        "review this nda and identify the confidentiality scope and carve-outs"
    )


def test_route_termination_query_to_legal():
    assert "legal" in brain.route(
        "what are the legal rights in this contract and can it be terminated"
    )


def test_route_infringement_query_to_legal():
    assert "legal" in brain.route(
        "is there copyright infringement and what is the legal exposure"
    )


def test_route_unrelated_query_excludes_legal():
    # A pure DSP/streaming analytics query should not pull in the legal domain
    assert "legal" not in brain.route(
        "analyze the streams per listener and the algorithmic save rate decay curve"
    )


def test_route_irrelevant_query_returns_empty():
    assert brain.route("what is the best coffee in brooklyn") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_legal_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "legal" in result["domains"]
    assert "# Legal & Contracts (legal)" in result["knowledge"]
    assert result["knowledge"].strip()


def test_consult_with_home_domain():
    result = brain.consult(
        "review this management agreement for red-flag clauses",
        home_domain="legal",
    )
    assert "legal" in result["domains"]
    assert result["domains"][0] == "legal"


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("legal"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("review this recording contract for copyright and legal risk", "legal"),
        ("check the chain of title and the termination rights for this deal", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
