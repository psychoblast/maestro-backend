"""
Phase 3f — deepened executive domain knowledge tests.

Verifies that the 'executive' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and the three new knowledge files added in phase 3f, and contains
no forbidden entity strings.

New knowledge files added in phase 3f:
  - crisis-leadership-and-rapid-response.md
  - organizational-design-and-talent-strategy.md
  - board-governance-and-investor-communication.md

Covers (crisis-leadership-and-rapid-response): five music-industry crisis types
(artist conduct/reputational, platform/distribution disruption, legal/regulatory,
financial distress/liquidity, key talent/executive departure); first-hour triage
protocol (reversibility window, public status assessment, decision-authority
naming); crisis decision framework (don't-make-it-worse principle, must-act-now
vs. wait-for-more-information classification, kill-switch decision discipline and
its three-step gate); crisis authority matrix by decision type; Type 1 artist-
conduct crisis playbook (Phase 1/2/3 sequencing, holding statement purpose, conduct-
provision literacy requirement, power-law concentration problem); Type 4 liquidity
crisis (runway math, obligation triage, communication sequencing, preservation
priority order); post-crisis retrospective five-question protocol.

Covers (organizational-design-and-talent-strategy): structure-follows-strategy
principle and the structural lag problem; four organizational design variables
(grouping logic, span of control, decision rights, information flow); music company
structural archetypes by stage (early-stage, growth, scale) and their design risks;
talent strategy as capital allocation (leverage multiplier, leverage roles in a
music company); hire vs. build vs. promote decision framework; retention as a
portfolio problem (replacement-cost calibration, flight-risk identification protocol,
counter-offer failure mode); planned vs. unplanned senior departure management;
termination-for-cause discipline; culture as competitive advantage (culture-strategy
alignment test, creative talent motivational factors); organizational capacity as
a binding constraint (capacity test, over-commitment cycle, hiring-lead-time reality).

Covers (board-governance-and-investor-communication): three board director types
(independent, investor, founder/management) and composition test; governance boundary
(board owns vs. management decides, two failure modes); board information architecture
(what governance requires vs. what management tends to present); board agenda design
with segment allocation table; pre-read discipline; managing a difficult quarter
(pre-notification protocol); investor communication purpose and three audience
segments; quarterly investor update template (headline summary, financial summary,
what went well, what didn't go as planned, key risks, asks, next-quarter plan);
investor rights and material-event obligation; capital-raising investor selection
matrix; music company narrative framework (four investor questions); financing
structure governance implications (protective provisions, cap table as governance);
deal-approval tiered framework; governance in conflict-of-interest scenarios.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "give me a go/no-go executive decision memo on this catalog acquisition — "
    "weigh the capital allocation against the hurdle rate and name the opportunity cost"
)

CRISIS_QUERY = (
    "walk me through the crisis response protocol for an artist conduct allegation — "
    "what is the first-hour triage, who has authority to issue a statement, "
    "and when do we activate the kill-switch on the upcoming release"
)

ORG_QUERY = (
    "how do we structure the organization and make the senior hire vs. promote decision — "
    "assess span of control, decision rights, and whether organizational capacity "
    "is the binding constraint before we commit to the next strategic phase"
)

BOARD_QUERY = (
    "prepare me for the board meeting — we missed plan by 20% and need to present "
    "the risk update, the investor communication plan, and a revised capital allocation"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_executive():
    assert "executive" in registry.list_domains()


def test_get_domain_display_name():
    domain = registry.get_domain("executive")
    assert domain.display_name == "Executive strategy"


def test_load_domain_returns_string():
    text = registry.load_domain("executive")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("executive")
    assert text.strip(), "executive domain loaded empty knowledge"


def test_load_domain_minimum_size():
    """10 knowledge files should yield substantially more than the prior 7-file base."""
    text = registry.load_domain("executive")
    assert len(text) >= 120_000, (
        f"executive knowledge too small: {len(text)} chars — expected ≥120 000 "
        f"after three new phase-3f files"
    )


def test_load_domain_assembles_all_manifest_sections():
    """Ten knowledge files → ten sections joined by the standard separator."""
    text = registry.load_domain("executive")
    assert text.count("\n\n---\n\n") >= 9, (
        f"Expected ≥9 section separators for 10 files; got {text.count(chr(10)*2+'---'+chr(10)*2)}"
    )


# ── pre-existing sections still present ───────────────────────────────────────

def test_core_doctrine_terms_present():
    text = registry.load_domain("executive").lower()
    for term in ("enterprise value", "capital allocation", "hurdle rate",
                 "opportunity cost", "decision memo"):
        assert term in text, f"Core doctrine term missing: {term!r}"


def test_decision_synthesis_terms_present():
    text = registry.load_domain("executive").lower()
    for term in ("evidence quality", "pre-mortem", "dissent", "go/no-go",
                 "averaging trap"):
        assert term in text, f"Decision-synthesis term missing: {term!r}"


def test_capital_and_strategy_terms_present():
    text = registry.load_domain("executive").lower()
    for term in ("roic", "npv", "where-to-play", "how-to-win",
                 "build/buy/partner", "power-law"):
        assert term in text, f"Capital/strategy term missing: {term!r}"


def test_risk_governance_terms_present():
    text = registry.load_domain("executive").lower()
    for term in ("risk taxonomy", "likelihood", "fatal unmitigated",
                 "residual", "risk tolerance"):
        assert term in text, f"Risk/governance term missing: {term!r}"


def test_prioritization_forecasting_terms_present():
    text = registry.load_domain("executive").lower()
    for term in ("sunk cost", "binding constraint", "base case", "bull case",
                 "bear case", "kill-decision"):
        assert term in text, f"Prioritization/forecasting term missing: {term!r}"


# ── crisis-leadership-and-rapid-response (new phase-3f) ──────────────────────

def test_crisis_file_loads_in_domain():
    text = registry.load_domain("executive").lower()
    assert "crisis" in text, "Crisis leadership content missing from assembled knowledge"


def test_crisis_typology_present():
    text = registry.load_domain("executive").lower()
    for term in ("artist conduct", "platform", "liquidity", "legal",
                 "key talent", "reputational"):
        assert term in text, f"Crisis typology term missing: {term!r}"


def test_crisis_triage_protocol_present():
    text = registry.load_domain("executive").lower()
    for term in ("reversibility", "holding statement", "decision authority",
                 "triage"):
        assert term in text, f"Crisis triage term missing: {term!r}"


def test_crisis_kill_switch_concept_present():
    text = registry.load_domain("executive").lower()
    assert "kill-switch" in text or "kill switch" in text, (
        "Kill-switch concept missing from crisis leadership content"
    )


def test_crisis_post_retrospective_present():
    text = registry.load_domain("executive").lower()
    assert "retrospective" in text, (
        "Post-crisis retrospective protocol missing from assembled knowledge"
    )


def test_crisis_power_law_concentration_problem_present():
    text = registry.load_domain("executive").lower()
    assert "power-law concentration" in text or "power-law" in text, (
        "Power-law concentration risk concept missing from crisis content"
    )


def test_crisis_conduct_provision_literacy_present():
    text = registry.load_domain("executive").lower()
    assert "conduct provision" in text, (
        "Conduct provision literacy concept missing from artist crisis playbook"
    )


# ── organizational-design-and-talent-strategy (new phase-3f) ─────────────────

def test_org_design_file_loads_in_domain():
    text = registry.load_domain("executive").lower()
    assert "organizational design" in text, (
        "Organizational design content missing from assembled knowledge"
    )


def test_org_design_four_variables_present():
    text = registry.load_domain("executive").lower()
    for term in ("grouping", "span of control", "decision rights",
                 "information flow"):
        assert term in text, f"Org design variable missing: {term!r}"


def test_talent_leverage_concept_present():
    text = registry.load_domain("executive").lower()
    assert "leverage" in text and "leverage role" in text, (
        "Leverage role concept missing from talent strategy content"
    )


def test_hire_build_promote_framework_present():
    text = registry.load_domain("executive").lower()
    assert "hire" in text and "promote" in text, (
        "Hire vs. promote framework missing from talent strategy"
    )


def test_retention_portfolio_concept_present():
    text = registry.load_domain("executive").lower()
    assert "retention" in text and "replacement cost" in text, (
        "Retention as portfolio problem (replacement cost) missing from talent content"
    )


def test_counter_offer_failure_mode_present():
    text = registry.load_domain("executive").lower()
    assert "counter-offer" in text, (
        "Counter-offer failure mode missing from talent retention content"
    )


def test_culture_strategy_alignment_present():
    text = registry.load_domain("executive").lower()
    assert "culture" in text, (
        "Culture as competitive advantage missing from org design content"
    )


def test_over_commitment_cycle_present():
    text = registry.load_domain("executive").lower()
    assert "over-commitment" in text or "overcommit" in text, (
        "Over-commitment cycle concept missing from organizational capacity content"
    )


def test_org_capacity_binding_constraint_section_present():
    text = registry.load_domain("executive").lower()
    assert "organizational capacity" in text and "binding constraint" in text, (
        "Organizational capacity as binding constraint missing from content"
    )


# ── board-governance-and-investor-communication (new phase-3f) ───────────────

def test_board_governance_file_loads_in_domain():
    text = registry.load_domain("executive").lower()
    assert "board" in text, (
        "Board governance content missing from assembled knowledge"
    )


def test_board_composition_types_present():
    text = registry.load_domain("executive").lower()
    for term in ("independent director", "investor director",
                 "founder"):
        assert term in text, f"Board composition type missing: {term!r}"


def test_governance_boundary_present():
    text = registry.load_domain("executive").lower()
    assert "governance boundary" in text or "board owns" in text, (
        "Governance boundary concept missing from board content"
    )


def test_board_agenda_design_present():
    text = registry.load_domain("executive").lower()
    assert "board agenda" in text or "agenda" in text, (
        "Board agenda content missing from board governance"
    )


def test_pre_read_discipline_present():
    text = registry.load_domain("executive").lower()
    assert "pre-read" in text, (
        "Pre-read discipline missing from board governance content"
    )


def test_investor_update_template_present():
    text = registry.load_domain("executive").lower()
    assert "investor update" in text or "quarterly investor" in text, (
        "Investor update template missing from investor communication content"
    )


def test_investor_audience_segments_present():
    text = registry.load_domain("executive").lower()
    for term in ("institutional investor", "strategic investor",
                 "angel"):
        assert term in text, f"Investor audience segment missing: {term!r}"


def test_material_event_obligation_present():
    text = registry.load_domain("executive").lower()
    assert "material event" in text, (
        "Material event obligation missing from investor communication content"
    )


def test_protective_provisions_concept_present():
    text = registry.load_domain("executive").lower()
    assert "protective provision" in text, (
        "Protective provisions concept missing from financing structure content"
    )


def test_cap_table_governance_concept_present():
    text = registry.load_domain("executive").lower()
    assert "cap table" in text, (
        "Cap table as governance concept missing from board/investor content"
    )


def test_deal_approval_tiered_framework_present():
    text = registry.load_domain("executive").lower()
    assert "deal-approval" in text or "deal approval" in text, (
        "Deal-approval tiered framework missing from governance content"
    )


def test_music_narrative_framework_four_questions_present():
    text = registry.load_domain("executive").lower()
    assert "narrative" in text and "investor" in text, (
        "Investor narrative framework missing from capital-raising content"
    )


# ── routing ───────────────────────────────────────────────────────────────────

def test_route_core_executive_query():
    from knowledge_bank import brain
    assert "executive" in brain.route(IN_DOMAIN_QUERY)


def test_route_crisis_query_to_executive():
    from knowledge_bank import brain
    result = brain.route(CRISIS_QUERY)
    assert "executive" in result, (
        f"Crisis query did not route to executive; got: {result}"
    )


def test_route_org_design_query_to_executive():
    from knowledge_bank import brain
    result = brain.route(ORG_QUERY)
    assert "executive" in result, (
        f"Org-design query did not route to executive; got: {result}"
    )


def test_route_board_query_to_executive():
    from knowledge_bank import brain
    result = brain.route(BOARD_QUERY)
    assert "executive" in result, (
        f"Board governance query did not route to executive; got: {result}"
    )


def test_route_unrelated_query_excludes_executive():
    from knowledge_bank import brain
    assert "executive" not in brain.route(
        "we have a duplicate isrc and the dsp delivery was rejected"
    )


# ── entity safety ─────────────────────────────────────────────────────────────

def test_crisis_file_no_forbidden_terms():
    import os
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "knowledge_bank", "domains", "executive",
        "crisis-leadership-and-rapid-response.md",
    )
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    assert_no_forbidden_terms(content)


def test_org_design_file_no_forbidden_terms():
    import os
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "knowledge_bank", "domains", "executive",
        "organizational-design-and-talent-strategy.md",
    )
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    assert_no_forbidden_terms(content)


def test_board_governance_file_no_forbidden_terms():
    import os
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "knowledge_bank", "domains", "executive",
        "board-governance-and-investor-communication.md",
    )
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    assert_no_forbidden_terms(content)


def test_assembled_executive_knowledge_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("executive"))
