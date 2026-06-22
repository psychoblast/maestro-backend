"""
Phase 3f — deepened A&R domain knowledge tests.

Verifies that the 'ar' domain loads via the bank's normal path,
is non-trivially sized, includes the required sections, and contains
no forbidden entity strings.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "evaluate this unsigned artist for signing and build the investment case "
    "for the a&r committee"
)


# ── registry ─────────────────────────────────────────────────────────────────

def test_list_domains_includes_ar():
    assert "ar" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("ar").display_name == "A&R Scouting"


def test_load_domain_returns_string():
    text = registry.load_domain("ar")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("ar")
    assert text.strip(), "ar domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 6 knowledge files → expect at least 40 000 chars of assembled content
    text = registry.load_domain("ar")
    assert len(text) >= 40_000, (
        f"ar knowledge too small: {len(text)} chars — expected ≥40 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 6 files → 5 separators between them
    text = registry.load_domain("ar")
    assert text.count("\n\n---\n\n") >= 5, (
        "Expected ≥5 section separators (6 knowledge files) in ar domain"
    )


# ── core doctrine presence ────────────────────────────────────────────────────

def test_scoring_rubric_present():
    text = registry.load_domain("ar").lower()
    assert "five-pillar" in text
    assert "music quality" in text
    assert "artist identity" in text
    assert "commercial opportunity" in text


def test_song_evaluation_present():
    text = registry.load_domain("ar").lower()
    assert "three-axis" in text
    assert "commercial viability" in text
    assert "artistic distinctiveness" in text


def test_artist_development_present():
    text = registry.load_domain("ar").lower()
    assert "waterfall release" in text
    assert "development arc" in text
    assert "identity stack" in text


def test_global_ar_systems_present():
    text = registry.load_domain("ar").lower()
    assert "territory" in text
    assert "k-pop" in text
    assert "afrobeats" in text


def test_output_templates_present():
    text = registry.load_domain("ar").lower()
    assert "signing evaluation memo" in text
    assert "watch-list entry" in text
    assert "coach-mode" in text


# ── new deal-mechanics knowledge ──────────────────────────────────────────────

def test_deal_mechanics_file_present():
    """New file contributed in phase 3f must be present in the assembled knowledge."""
    text = registry.load_domain("ar").lower()
    assert "deal structures" in text or "deal type" in text, (
        "deal-mechanics.md content not found in assembled ar knowledge"
    )


def test_deal_mechanics_advance_content():
    text = registry.load_domain("ar").lower()
    assert "recoupment" in text
    assert "advance" in text
    assert "cross-collateral" in text


def test_deal_mechanics_rights_flags():
    text = registry.load_domain("ar").lower()
    assert "rights flag" in text or "ip review" in text


def test_deal_mechanics_deal_type_taxonomy():
    text = registry.load_domain("ar").lower()
    assert "360 deal" in text or "360" in text
    assert "license deal" in text or "license" in text
    assert "joint venture" in text or "jv" in text
    assert "development deal" in text


def test_deal_mechanics_offer_to_close():
    text = registry.load_domain("ar").lower()
    assert "offer-to-close" in text or "offer to close" in text or "due diligence" in text


def test_deal_mechanics_competitive_bidding():
    text = registry.load_domain("ar").lower()
    assert "competitive bidding" in text or "bidding" in text


def test_deal_mechanics_catalog_acquisition():
    text = registry.load_domain("ar").lower()
    assert "catalog acquisition" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_signing_query_to_ar():
    assert "ar" in brain.route(IN_DOMAIN_QUERY)


def test_route_scouting_query_to_ar():
    assert "ar" in brain.route(
        "scout unsigned talent in this genre and evaluate for the roster"
    )


def test_route_artist_development_query_to_ar():
    assert "ar" in brain.route(
        "develop the artist through the first release cycle"
    )


def test_route_unrelated_query_excludes_ar():
    # A pure royalties statement query should not pull in the ar domain
    assert "ar" not in brain.route(
        "how do mechanical royalties recoup against the advance on the statement"
    )


def test_route_irrelevant_query_returns_empty():
    assert brain.route("the weather in chicago") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_ar_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "ar" in result["domains"]
    assert "# A&R Scouting (ar)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("ar"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("evaluate this emerging artist and build the development plan", "ar"),
        ("sign this unsigned act to the roster", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
