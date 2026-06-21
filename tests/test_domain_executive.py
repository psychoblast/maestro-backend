"""
Tests for the re-homed "executive" domain (Executive strategy).

In-process only. NO network / LLM calls. The bank reads knowledge files already
present in the repo (under knowledge_bank/domains/executive/).
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


# A query that is unambiguously in the executive-strategy domain.
IN_DOMAIN_QUERY = (
    "give me a go/no-go executive decision memo on this catalog acquisition — "
    "weigh the capital allocation against the hurdle rate and name the opportunity cost"
)


# ── registry ─────────────────────────────────────────────────────────────────────

def test_list_domains_includes_executive():
    assert "executive" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("executive").display_name == "Executive strategy"


def test_load_domain_non_empty():
    text = registry.load_domain("executive")
    assert isinstance(text, str)
    assert text.strip(), "executive loaded empty knowledge"


def test_load_domain_assembles_core_doctrine():
    text = registry.load_domain("executive").lower()
    # Core, domain-defining concepts must be present in the assembled knowledge.
    assert "enterprise value" in text
    assert "capital allocation" in text
    assert "hurdle rate" in text
    assert "opportunity cost" in text
    assert "decision memo" in text


def test_load_domain_assembles_all_manifest_sections():
    # Seven knowledge files → seven sections joined by the standard separator.
    text = registry.load_domain("executive")
    assert text.count("\n\n---\n\n") >= 6


# ── brain routing ─────────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_executive():
    assert "executive" in brain.route(IN_DOMAIN_QUERY)


def test_route_capital_allocation_query_to_executive():
    assert "executive" in brain.route(
        "how should we allocate capital across the roster given our hurdle rate and ROIC"
    )


def test_route_strategy_query_to_executive():
    assert "executive" in brain.route(
        "what is our where-to-play and how-to-win — is this market entry a strong strategic fit"
    )


def test_route_risk_governance_query_to_executive():
    assert "executive" in brain.route(
        "assess the enterprise risk and concentration risk before this go/no-go decision"
    )


def test_route_unrelated_query_excludes_executive():
    # Guard against keyword over-reach: a pure delivery/metadata query must not pull this in.
    assert "executive" not in brain.route(
        "we have a duplicate isrc and the dsp delivery was rejected"
    )


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────────

def test_consult_returns_executive_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "executive" in result["domains"]
    domain = registry.get_domain("executive")
    assert f"# {domain.display_name} (executive)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("executive"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("enterprise risk governance and capital allocation plan", "executive"),
        ("scenario planning with base case bull case bear case and a decision memo", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
