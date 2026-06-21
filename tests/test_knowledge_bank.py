"""
Tests for the shared knowledge bank (registry + deterministic brain).

All tests are in-process. NO network / LLM calls. The bank only reads knowledge
files already present in the repo.
"""
import pytest

from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


EXPECTED_DOMAINS = [
    "ar",
    "marketing",
    "sync",
    "bizdev",
    "legal",
    "live_touring",
    "publishing",
    "finance_royalties",
    "production",
    "capital_funding",
    "controller",
]


# ── registry: list_domains / load_domain ─────────────────────────────────────────

def test_list_domains_is_the_expected_keys():
    assert registry.list_domains() == EXPECTED_DOMAINS
    assert len(registry.list_domains()) == 11


def test_load_domain_non_empty_for_every_domain():
    for key in registry.list_domains():
        text = registry.load_domain(key)
        assert isinstance(text, str)
        assert text.strip(), f"Domain {key!r} loaded empty knowledge"


def test_load_domain_unknown_key_raises():
    with pytest.raises(KeyError):
        registry.load_domain("not-a-real-domain")


def test_get_domain_unknown_key_raises_clearly():
    with pytest.raises(KeyError) as exc:
        registry.get_domain("nope")
    # Error message names the bad key (clear error).
    assert "nope" in str(exc.value)


def test_load_domain_assembles_known_content():
    # The finance/royalties domain comes from the royalty-doctor knowledge base.
    text = registry.load_domain("finance_royalties").lower()
    assert "royalt" in text


# ── brain.route ──────────────────────────────────────────────────────────────────

def test_route_royalties_query_to_finance():
    domains = brain.route("how do mechanical royalties and recoup work")
    assert "finance_royalties" in domains


def test_route_sync_query_to_sync():
    domains = brain.route("we need a sync placement for a film trailer")
    assert "sync" in domains


def test_route_cross_domain_query_hits_both():
    domains = brain.route("sync placement and royalty splits")
    assert "sync" in domains
    assert "finance_royalties" in domains


def test_route_always_includes_home_domain_even_when_unmatched():
    domains = brain.route("just a general question with no triggers", home_domain="ar")
    assert domains == ["ar"]


def test_route_home_domain_is_first_and_deduped():
    # Home is finance; query also mentions sync → home first, no duplicate.
    domains = brain.route("royalty splits plus a sync placement", home_domain="finance_royalties")
    assert domains[0] == "finance_royalties"
    assert "sync" in domains
    assert domains.count("finance_royalties") == 1


def test_route_irrelevant_query_no_home_returns_empty():
    assert brain.route("the weather is nice today") == []


def test_route_is_deterministic():
    q = "sync placement and royalty splits"
    assert brain.route(q) == brain.route(q)


# ── brain.consult ────────────────────────────────────────────────────────────────

def test_consult_returns_domains_and_knowledge():
    result = brain.consult("mechanical royalties question", home_domain="finance_royalties")
    assert "domains" in result
    assert "knowledge" in result
    assert "finance_royalties" in result["domains"]
    assert result["knowledge"].strip()


def test_consult_caps_at_max_domains():
    # A query that matches many domains, capped to 2.
    query = "contract clause, sync placement, royalty splits, tour booking, brand sponsor"
    result = brain.consult(query, max_domains=2)
    assert len(result["domains"]) <= 2


def test_consult_has_a_section_per_domain():
    result = brain.consult("sync placement and royalty splits", max_domains=4)
    for key in result["domains"]:
        domain = registry.get_domain(key)
        assert f"# {domain.display_name} ({key})" in result["knowledge"]


def test_consult_no_match_no_home_is_empty():
    result = brain.consult("the weather is nice today")
    assert result["domains"] == []
    assert result["knowledge"] == ""


# ── entity safety ────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    """Knowledge assembled across several queries must leak no provenance markers."""
    queries = [
        ("mechanical royalties and publishing splits", None),
        ("sync placement for a film trailer", "sync"),
        ("contract clause and indemnity negotiation", "legal"),
        ("tour booking and venue rider", "live_touring"),
        ("brand sponsorship partnership deal", "bizdev"),
        ("marketing campaign and audience growth", "marketing"),
        ("artist development and scouting", "ar"),
        ("mixing, mastering and stems delivery", "production"),
    ]
    for query, home in queries:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])


def test_every_domain_individually_has_no_forbidden_terms():
    for key in registry.list_domains():
        assert_no_forbidden_terms(registry.load_domain(key))
