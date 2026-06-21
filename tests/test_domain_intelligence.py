"""
Tests for the re-homed "intelligence" domain (Market intelligence).

In-process only. NO network / LLM calls. The bank reads knowledge files already
present in the repo (under knowledge_bank/domains/intelligence/).
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


# A query that is unambiguously in the market-intelligence domain.
IN_DOMAIN_QUERY = (
    "scan the industry for structural developments and route decision-relevant "
    "market intelligence with source tiers to the right specialist"
)


# ── registry ─────────────────────────────────────────────────────────────────────

def test_list_domains_includes_intelligence():
    assert "intelligence" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("intelligence").display_name == "Market intelligence"


def test_load_domain_non_empty():
    text = registry.load_domain("intelligence")
    assert isinstance(text, str)
    assert text.strip(), "intelligence loaded empty knowledge"


def test_load_domain_assembles_core_doctrine():
    text = registry.load_domain("intelligence").lower()
    # Core, domain-defining concepts must be present in the assembled knowledge.
    assert "currency with consequence" in text
    assert "news is noise until it changes a decision" in text
    assert "decision-change test" in text
    assert "four-filter method" in text
    assert "star protocol" in text
    assert "not evaluable" in text


def test_load_domain_assembles_all_manifest_sections():
    # Eight knowledge files → eight sections joined by the standard separator.
    text = registry.load_domain("intelligence")
    assert text.count("\n\n---\n\n") >= 7


# ── brain routing ─────────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_intelligence():
    assert "intelligence" in brain.route(IN_DOMAIN_QUERY)


def test_route_sourcing_query_to_intelligence():
    assert "intelligence" in brain.route(
        "assign a source tier to this new trade source and check for a rumor before we alert"
    )


def test_route_classification_query_to_intelligence():
    assert "intelligence" in brain.route(
        "is this a rule-changer or just a contextual update — run the four-filter and cdm class"
    )


def test_route_timing_query_to_intelligence():
    assert "intelligence" in brain.route(
        "should this be an immediate alert or the weekly scan — avoid trigger fatigue on a monitoring signal"
    )


def test_route_unrelated_query_excludes_intelligence():
    # Guard against keyword over-reach: a pure delivery/metadata query must not pull this in.
    assert "intelligence" not in brain.route(
        "we have a duplicate isrc and the dsp delivery was rejected"
    )


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────────

def test_consult_returns_intelligence_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "intelligence" in result["domains"]
    domain = registry.get_domain("intelligence")
    assert f"# {domain.display_name} (intelligence)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("intelligence"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("source tier assignment and rumor handling with a corroborated trade source", "intelligence"),
        ("classify the consequential development and route it without trigger fatigue", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
