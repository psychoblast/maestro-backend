"""
Tests for the re-homed "data_analytics" domain (Data and analytics).

In-process only. NO network / LLM calls. The bank reads knowledge files already
present in the repo (under knowledge_bank/domains/data_analytics/).
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


# A query that is unambiguously in the data-and-analytics domain.
IN_DOMAIN_QUERY = (
    "forecast the streaming trajectory for this release and check the save rate "
    "against a cohort benchmark"
)


# ── registry ─────────────────────────────────────────────────────────────────────

def test_list_domains_includes_data_analytics():
    assert "data_analytics" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("data_analytics").display_name == "Data and analytics"


def test_load_domain_non_empty():
    text = registry.load_domain("data_analytics")
    assert isinstance(text, str)
    assert text.strip(), "data_analytics loaded empty knowledge"


def test_load_domain_assembles_core_doctrine():
    text = registry.load_domain("data_analytics").lower()
    # Core, domain-defining concepts must be present in the assembled knowledge.
    assert "forecast" in text
    assert "cohort" in text
    assert "anomaly" in text
    assert "benchmark" in text
    assert "save rate" in text


def test_load_domain_assembles_all_manifest_sections():
    # Seven knowledge files → seven sections joined by the standard separator.
    text = registry.load_domain("data_analytics")
    assert text.count("\n\n---\n\n") >= 6


# ── brain routing ─────────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_data_analytics():
    assert "data_analytics" in brain.route(IN_DOMAIN_QUERY)


def test_route_anomaly_query_to_data_analytics():
    assert "data_analytics" in brain.route(
        "investigate the stream spike — is this an outlier or a reporting artifact"
    )


def test_route_benchmark_query_to_data_analytics():
    assert "data_analytics" in brain.route(
        "build a reference class and benchmark this artist against a comparable case set"
    )


def test_route_cohort_query_to_data_analytics():
    assert "data_analytics" in brain.route(
        "what is the day-28 retention and save rate for the release-week cohort"
    )


def test_route_unrelated_query_excludes_data_analytics():
    # Guard against keyword over-reach: a pure royalties query must not pull this in.
    assert "data_analytics" not in brain.route("how do mechanical royalties and recoup work")


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────────

def test_consult_returns_data_analytics_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "data_analytics" in result["domains"]
    domain = registry.get_domain("data_analytics")
    assert f"# {domain.display_name} (data_analytics)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("data_analytics"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("anomaly detection on a stream spike with z-score testing", "data_analytics"),
        ("benchmark comparison against a reference class for a forecast", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
