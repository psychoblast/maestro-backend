"""
Tests for the re-homed "fan_social" domain (Fan and social).

In-process only. NO network / LLM calls. The bank reads knowledge files already
present in the repo (under knowledge_bank/domains/fan_social/).
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


# A query that is unambiguously in the fan-and-social domain.
IN_DOMAIN_QUERY = (
    "how do we convert casual listeners into superfans and build an owned-channel "
    "fan community with a D2C membership tier"
)


# ── registry ─────────────────────────────────────────────────────────────────────

def test_list_domains_includes_fan_social():
    assert "fan_social" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("fan_social").display_name == "Fan and social"


def test_load_domain_non_empty():
    text = registry.load_domain("fan_social")
    assert isinstance(text, str)
    assert text.strip(), "fan_social loaded empty knowledge"


def test_load_domain_assembles_core_doctrine():
    text = registry.load_domain("fan_social").lower()
    # Core, domain-defining concepts must be present in the assembled knowledge.
    assert "own the relationship, not the algorithm" in text
    assert "superfan" in text
    assert "parasocial" in text
    assert "owned-channel test" in text
    assert "fan journey" in text


def test_load_domain_assembles_all_manifest_sections():
    # Eleven knowledge files → eleven sections joined by the standard separator.
    text = registry.load_domain("fan_social")
    assert text.count("\n\n---\n\n") >= 10


# ── brain routing ─────────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_fan_social():
    assert "fan_social" in brain.route(IN_DOMAIN_QUERY)


def test_route_superfan_economics_query_to_fan_social():
    assert "fan_social" in brain.route(
        "design the superfan tier and fan-funding membership economics for our D2C store"
    )


def test_route_community_query_to_fan_social():
    assert "fan_social" in brain.route(
        "assess our discord community health and the fan engagement lifecycle"
    )


def test_route_ambassador_query_to_fan_social():
    assert "fan_social" in brain.route(
        "should we launch a street team and an ambassador program for fan mobilization"
    )


def test_route_unrelated_query_excludes_fan_social():
    # Guard against keyword over-reach: a pure delivery/metadata query must not pull this in.
    assert "fan_social" not in brain.route(
        "we have a duplicate isrc and the dsp delivery was rejected"
    )


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────────

def test_consult_returns_fan_social_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "fan_social" in result["domains"]
    domain = registry.get_domain("fan_social")
    assert f"# {domain.display_name} (fan_social)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("fan_social"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("fan community health and superfan concentration with an owned channel plan", "fan_social"),
        ("parasocial dynamics, fandom psychology, and a community crisis response", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
