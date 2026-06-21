"""
Tests for the re-homed "label_ops" domain (Label operations).

In-process only. NO network / LLM calls. The bank reads knowledge files already
present in the repo (under knowledge_bank/domains/label_ops/).
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


# A query that is unambiguously in the label-operations domain.
IN_DOMAIN_QUERY = (
    "build the release campaign arc, file the editorial pitch in the pitch window, "
    "choose a distribution partner, run pre-delivery qc before delivery, and model "
    "recoupment and cross-collateralization for the recording agreement"
)


# ── registry ─────────────────────────────────────────────────────────────────────

def test_list_domains_includes_label_ops():
    assert "label_ops" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("label_ops").display_name == "Label operations"


def test_load_domain_non_empty():
    text = registry.load_domain("label_ops")
    assert isinstance(text, str)
    assert text.strip(), "label_ops loaded empty knowledge"


def test_load_domain_assembles_core_doctrine():
    text = registry.load_domain("label_ops").lower()
    # Core, domain-defining concepts must be present in the assembled knowledge.
    assert "operational failures are commercial failures" in text
    assert "catalog is a business, not a library" in text
    assert "controlled composition" in text
    assert "cross-collateralization" in text
    assert "recoupment" in text
    assert "priority stack" in text
    assert "four-layer label tech stack" in text
    assert "not evaluable" in text


def test_load_domain_assembles_all_manifest_sections():
    # Nine knowledge files → nine sections joined by the standard separator.
    text = registry.load_domain("label_ops")
    assert text.count("\n\n---\n\n") >= 8


# ── brain routing ─────────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_label_ops():
    assert "label_ops" in brain.route(IN_DOMAIN_QUERY)


def test_route_distribution_query_to_label_ops():
    assert "label_ops" in brain.route(
        "compare a diy aggregator versus a mid-tier distribution partner and run the "
        "distribution selection for this artist"
    )


def test_route_deal_query_to_label_ops():
    assert "label_ops" in brain.route(
        "model the recoupment projection and the controlled composition clause in the "
        "recording agreement, and flag any cross-collateral risk"
    )


def test_route_catalog_query_to_label_ops():
    assert "label_ops" in brain.route(
        "run a catalog audit and plan catalog exploitation, including a remaster and the "
        "reversion clock"
    )


def test_route_roster_query_to_label_ops():
    assert "label_ops" in brain.route(
        "set the project kickoff and the release readiness gate, then work the priority "
        "stack across the roster"
    )


def test_route_unrelated_query_excludes_label_ops():
    # Guard against keyword over-reach: a pure analytics query must not pull this in.
    assert "label_ops" not in brain.route(
        "calculate the z-score and skip rate from the streaming data"
    )


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────────

def test_consult_returns_label_ops_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "label_ops" in result["domains"]
    domain = registry.get_domain("label_ops")
    assert f"# {domain.display_name} (label_ops)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("label_ops"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("distribution partner selection and recoupment for the label deal", "label_ops"),
        ("catalog exploitation, sync readiness, and the reversion clock", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
