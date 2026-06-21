"""
Tests for the re-homed "digital_ops" domain (Digital operations).

In-process only. NO network / LLM calls. The bank reads knowledge files already
present in the repo (under knowledge_bank/domains/digital_ops/).
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


# A query that is unambiguously in the digital-operations domain.
IN_DOMAIN_QUERY = (
    "we have an ISRC conflict on a delivered release and the DSP delivery was "
    "rejected — diagnose the metadata error and plan the redelivery"
)


# ── registry ─────────────────────────────────────────────────────────────────────

def test_list_domains_includes_digital_ops():
    assert "digital_ops" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("digital_ops").display_name == "Digital operations"


def test_load_domain_non_empty():
    text = registry.load_domain("digital_ops")
    assert isinstance(text, str)
    assert text.strip(), "digital_ops loaded empty knowledge"


def test_load_domain_assembles_core_doctrine():
    text = registry.load_domain("digital_ops").lower()
    # Core, domain-defining concepts must be present in the assembled knowledge.
    assert "isrc" in text
    assert "upc" in text
    assert "metadata" in text
    assert "content recognition" in text
    assert "rights hygiene" in text


def test_load_domain_assembles_all_manifest_sections():
    # Seven knowledge files → seven sections joined by the standard separator.
    text = registry.load_domain("digital_ops")
    assert text.count("\n\n---\n\n") >= 6


# ── brain routing ─────────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_digital_ops():
    assert "digital_ops" in brain.route(IN_DOMAIN_QUERY)


def test_route_content_id_query_to_digital_ops():
    assert "digital_ops" in brain.route(
        "a third party filed a content id claim on our track — should we dispute it"
    )


def test_route_identifier_query_to_digital_ops():
    assert "digital_ops" in brain.route(
        "do we need a new ISRC for this remaster or can we reuse the existing identifier"
    )


def test_route_governance_query_to_digital_ops():
    assert "digital_ops" in brain.route(
        "run a rights hygiene audit on the catalog metadata and check territory configuration"
    )


def test_route_unrelated_query_excludes_digital_ops():
    # Guard against keyword over-reach: a pure royalties query must not pull this in.
    assert "digital_ops" not in brain.route("how do mechanical royalties and recoup work")


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────────

def test_consult_returns_digital_ops_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "digital_ops" in result["domains"]
    domain = registry.get_domain("digital_ops")
    assert f"# {domain.display_name} (digital_ops)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("digital_ops"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("content id claim dispute and meta rights manager registration", "digital_ops"),
        ("ddex ern delivery spec and pre-delivery qc checklist", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
