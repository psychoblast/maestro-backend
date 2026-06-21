"""
Tests for the re-homed "management" domain (Artist management).

In-process only. NO network / LLM calls. The bank reads knowledge files already
present in the repo (under knowledge_bank/domains/management/).
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


# A query that is unambiguously in the artist-management domain.
IN_DOMAIN_QUERY = (
    "evaluate the management agreement and its commission structure, including the "
    "sunset clause and key-person clause, then set the artist's career strategy by "
    "career phase, assemble the professional team starting with an entertainment "
    "attorney, and run opportunity triage on inbound offers"
)


# ── registry ─────────────────────────────────────────────────────────────────────

def test_list_domains_includes_management():
    assert "management" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("management").display_name == "Artist management"


def test_load_domain_non_empty():
    text = registry.load_domain("management")
    assert isinstance(text, str)
    assert text.strip(), "management loaded empty knowledge"


def test_load_domain_assembles_core_doctrine():
    text = registry.load_domain("management").lower()
    # Core, domain-defining concepts must be present in the assembled knowledge.
    assert "the manager who cannot say no to their artist" in text
    assert "modified net" in text
    assert "sunset" in text
    assert "key-person" in text
    assert "career phase" in text
    assert "positioning triangle" in text
    assert "loan-out" in text
    assert "not evaluable" in text


def test_load_domain_assembles_all_manifest_sections():
    # Ten knowledge files → ten sections joined by the standard separator.
    text = registry.load_domain("management")
    assert text.count("\n\n---\n\n") >= 9


# ── brain routing ─────────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_management():
    assert "management" in brain.route(IN_DOMAIN_QUERY)


def test_route_agreement_query_to_management():
    assert "management" in brain.route(
        "compare a gross commission against a modified net commission in the "
        "management agreement and check the sunset provision"
    )


def test_route_career_query_to_management():
    assert "management" in brain.route(
        "map the artist's career phase, define the positioning triangle, and run "
        "the opportunity stack on these inbound offers"
    )


def test_route_team_query_to_management():
    assert "management" in brain.route(
        "assemble the professional team, retain an entertainment attorney first, "
        "and work out the hiring sequence"
    )


def test_route_crisis_query_to_management():
    assert "management" in brain.route(
        "run crisis triage and reputation management for this artist before any "
        "public statement"
    )


def test_route_unrelated_query_excludes_management():
    # Guard against keyword over-reach: a pure analytics query must not pull this in.
    assert "management" not in brain.route(
        "calculate the z-score and skip rate from the streaming data"
    )


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────────

def test_consult_returns_management_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "management" in result["domains"]
    domain = registry.get_domain("management")
    assert f"# {domain.display_name} (management)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("management"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("management commission structure and the sunset provision", "management"),
        ("career strategy, momentum management, and the positioning triangle", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
