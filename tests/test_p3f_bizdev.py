"""
Phase 3f — deepened bizdev domain knowledge tests.

Verifies that the 'bizdev' domain loads via the bank's normal path (registry),
is non-trivially sized, includes all required sections from both pre-existing
and new knowledge files, and contains no forbidden entity strings.

New knowledge file added in phase 3f:
  - negotiation-playbook.md  (negotiation-doctrine)

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "evaluate this brand endorsement deal and advise on the negotiation "
    "strategy before we respond to the brand's opening offer"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_bizdev():
    assert "bizdev" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("bizdev").display_name == "Brand & Business Development"


def test_load_domain_returns_string():
    text = registry.load_domain("bizdev")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("bizdev")
    assert text.strip(), "bizdev domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 8 knowledge files → expect at least 102 000 chars of assembled content
    text = registry.load_domain("bizdev")
    assert len(text) >= 102_000, (
        f"bizdev knowledge too small: {len(text)} chars — expected ≥102 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 8 files joined by section separators → at least 7 separators
    text = registry.load_domain("bizdev")
    assert text.count("\n\n---\n\n") >= 7, (
        "Expected ≥7 section separators (8 knowledge files) in bizdev domain"
    )


# ── pre-existing doctrine presence ────────────────────────────────────────────

def test_scoring_rubric_present():
    text = registry.load_domain("bizdev").lower()
    assert "deal quality score" in text or "dqs" in text
    assert "strategic value" in text
    assert "economic value" in text
    assert "partner quality" in text


def test_deal_structure_axes_present():
    text = registry.load_domain("bizdev").lower()
    assert "time axis" in text
    assert "scope axis" in text
    assert "optionality axis" in text


def test_deal_economics_structures_present():
    text = registry.load_domain("bizdev").lower()
    assert "cash consideration" in text
    assert "in-kind" in text
    assert "co-marketing" in text
    assert "revenue participation" in text


def test_kill_fee_standards_present():
    text = registry.load_domain("bizdev").lower()
    assert "kill fee" in text
    assert "cancellation" in text


def test_exclusivity_standards_present():
    text = registry.load_domain("bizdev").lower()
    assert "category exclusivity" in text
    assert "carve-out" in text or "carve out" in text


def test_partner_due_diligence_domains_present():
    text = registry.load_domain("bizdev").lower()
    assert "track record" in text
    assert "financial health" in text
    assert "delivery capacity" in text
    assert "organizational alignment" in text


def test_foreclosing_term_identification_present():
    text = registry.load_domain("bizdev").lower()
    assert "foreclosing term" in text
    assert "morality clause" in text


def test_partnership_taxonomy_present():
    text = registry.load_domain("bizdev").lower()
    assert "ambassador" in text
    assert "paid social" in text or "paid campaign" in text


def test_output_templates_present():
    text = registry.load_domain("bizdev").lower()
    assert "deal quality assessment" in text or "assessment memo" in text


# ── new negotiation-playbook knowledge (phase 3f) ────────────────────────────

def test_negotiation_playbook_file_loaded():
    """negotiation-playbook.md content must appear in the assembled knowledge."""
    text = registry.load_domain("bizdev").lower()
    assert "negotiation playbook" in text or "deal origination" in text, (
        "negotiation-playbook.md content not found in assembled bizdev knowledge"
    )


def test_deal_origination_modes_present():
    text = registry.load_domain("bizdev").lower()
    assert "origination mode" in text or "deal origination" in text
    assert "inbound" in text
    assert "proactive outreach" in text


def test_agent_sourced_origination_present():
    text = registry.load_domain("bizdev").lower()
    assert "agent-sourced" in text or "agent sourced" in text
    assert "intermediary" in text


def test_pre_negotiation_stack_present():
    text = registry.load_domain("bizdev").lower()
    assert "pre-negotiation" in text or "pre negotiation" in text
    assert "budget cycle" in text
    assert "fiscal year" in text


def test_deal_champion_concept_present():
    text = registry.load_domain("bizdev").lower()
    assert "deal champion" in text


def test_opening_position_doctrine_present():
    text = registry.load_domain("bizdev").lower()
    assert "opening position" in text
    assert "payment schedule" in text or "payment timing" in text


def test_term_hierarchy_present():
    text = registry.load_domain("bizdev").lower()
    assert "term hierarchy" in text
    assert "hard line" in text or "hard-line" in text
    assert "low-priority" in text or "low priority" in text


def test_counter_offer_sequencing_present():
    text = registry.load_domain("bizdev").lower()
    assert "counter-offer" in text or "counter offer" in text
    assert "first counter" in text or "second counter" in text


def test_walk_away_triggers_present():
    text = registry.load_domain("bizdev").lower()
    assert "walk-away" in text or "walk away" in text
    assert "walk-away trigger" in text or "walk away trigger" in text


def test_brand_negotiating_tactics_present():
    text = registry.load_domain("bizdev").lower()
    assert "fixed budget" in text
    assert "other artists" in text or "in conversation with other" in text


def test_loi_vs_contract_close_present():
    text = registry.load_domain("bizdev").lower()
    assert "loi" in text or "letter of intent" in text
    assert "term sheet" in text
    assert "direct-to-contract" in text or "direct to contract" in text


def test_who_drafts_doctrine_present():
    text = registry.load_domain("bizdev").lower()
    assert "who drafts" in text or "party who drafts" in text


def test_post_deal_activation_present():
    text = registry.load_domain("bizdev").lower()
    assert "post-deal" in text or "post deal" in text or "activation" in text
    assert "delivery log" in text
    assert "approval clock" in text


def test_approval_sla_enforcement_present():
    text = registry.load_domain("bizdev").lower()
    assert "sla" in text
    assert "turnaround" in text


def test_performance_kicker_tactics_present():
    text = registry.load_domain("bizdev").lower()
    assert "performance kicker" in text or "kicker" in text


def test_intermediary_dynamics_present():
    text = registry.load_domain("bizdev").lower()
    assert "conflict check" in text or "conflict of interest" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_brand_deal_query_to_bizdev():
    assert "bizdev" in brain.route(IN_DOMAIN_QUERY)


def test_route_sponsorship_query_to_bizdev():
    assert "bizdev" in brain.route(
        "evaluate this brand sponsorship deal and negotiate the ambassador terms"
    )


def test_route_partnership_query_to_bizdev():
    assert "bizdev" in brain.route(
        "advise on a commercial partnership deal for the artist"
    )


def test_route_brand_deal_query_to_bizdev_keyword():
    assert "bizdev" in brain.route(
        "we received a brand deal offer and need to review it"
    )


def test_route_unrelated_query_excludes_bizdev():
    # A pure royalties-statement query should not pull in the bizdev domain
    assert "bizdev" not in brain.route(
        "how do mechanical royalties recoup against the advance on the statement"
    )


def test_route_irrelevant_query_returns_empty():
    assert brain.route("the weather in chicago") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_bizdev_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "bizdev" in result["domains"]
    assert "# Brand & Business Development (bizdev)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("bizdev"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("evaluate this brand endorsement and score the deal quality", "bizdev"),
        ("advise on the negotiation strategy for this brand partnership", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
