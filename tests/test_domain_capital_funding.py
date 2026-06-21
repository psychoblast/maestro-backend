"""
Tests for the re-homed "capital_funding" domain (Capital and funding).

In-process only. NO network / LLM calls. The bank reads knowledge files already
present in the repo (under knowledge_bank/domains/capital_funding/).
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


# A query that is unambiguously in the capital-and-funding domain.
IN_DOMAIN_QUERY = "how should we raise capital and structure a funding round with investors"


# ── registry ─────────────────────────────────────────────────────────────────────

def test_list_domains_includes_capital_funding():
    assert "capital_funding" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("capital_funding").display_name == "Capital and funding"


def test_load_domain_non_empty():
    text = registry.load_domain("capital_funding")
    assert isinstance(text, str)
    assert text.strip(), "capital_funding loaded empty knowledge"


def test_load_domain_assembles_core_doctrine():
    text = registry.load_domain("capital_funding").lower()
    # Core, domain-defining concepts must be present in the assembled knowledge.
    assert "non-dilutive" in text
    assert "capital stack" in text
    assert "covenant" in text
    assert "soundness scorecard" in text


def test_load_domain_assembles_all_manifest_sections():
    # Six knowledge files → six sections joined by the standard separator.
    text = registry.load_domain("capital_funding")
    assert text.count("\n\n---\n\n") >= 5


# ── brain routing ─────────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_capital_funding():
    assert "capital_funding" in brain.route(IN_DOMAIN_QUERY)


def test_route_debt_query_to_capital_funding():
    assert "capital_funding" in brain.route("we are evaluating a term sheet for catalog debt financing")


def test_route_grant_query_to_capital_funding():
    assert "capital_funding" in brain.route("which non-dilutive grant and tax credit programs are we eligible for")


def test_route_unrelated_query_excludes_capital_funding():
    # Guard against keyword over-reach: a pure royalties query must not pull in capital_funding.
    assert "capital_funding" not in brain.route("how do mechanical royalties and recoup work")


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────────

def test_consult_returns_capital_funding_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "capital_funding" in result["domains"]
    domain = registry.get_domain("capital_funding")
    assert f"# {domain.display_name} (capital_funding)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("capital_funding"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("term sheet covenant and clawback analysis for a royalty advance", "capital_funding"),
        ("non-dilutive grant strategy and matching fund math", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
