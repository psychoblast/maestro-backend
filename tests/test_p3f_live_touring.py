"""
Phase 3f — deepened live_touring domain knowledge tests.

Verifies that the 'live_touring' domain loads via the bank's normal path,
is non-trivially sized, includes required sections from both existing and new
knowledge files, and contains no forbidden entity strings.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "build a tour routing and P&L model for the upcoming headline run "
    "and evaluate the promoter offers we received"
)


# ── registry ─────────────────────────────────────────────────────────────────

def test_list_domains_includes_live_touring():
    assert "live_touring" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("live_touring").display_name == "Live & Touring"


def test_load_domain_returns_string():
    text = registry.load_domain("live_touring")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("live_touring")
    assert text.strip(), "live_touring domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 6 knowledge files (5 existing + new) → expect at least 70 000 chars
    text = registry.load_domain("live_touring")
    assert len(text) >= 70_000, (
        f"live_touring knowledge too small: {len(text)} chars — expected ≥70 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 6 files → at least 5 separators between them
    text = registry.load_domain("live_touring")
    assert text.count("\n\n---\n\n") >= 5, (
        "Expected ≥5 section separators (6 knowledge files) in live_touring domain"
    )


# ── existing knowledge sections ───────────────────────────────────────────────

def test_tour_doctrine_present():
    text = registry.load_domain("live_touring").lower()
    assert "anchor-first" in text
    assert "break-even" in text
    assert "dead leg" in text


def test_campaign_quality_rubric_present():
    text = registry.load_domain("live_touring").lower()
    assert "routing logic" in text
    assert "financial model integrity" in text
    assert "provisional composite" in text


def test_tour_operations_present():
    text = registry.load_domain("live_touring").lower()
    assert "routing efficiency ratio" in text
    assert "artist-to-gross" in text
    assert "production advance" in text


def test_live_business_ecosystem_present():
    text = registry.load_domain("live_touring").lower()
    assert "booking-agency" in text or "booking agency" in text
    assert "split point" in text
    assert "hall fee" in text


def test_output_templates_present():
    text = registry.load_domain("live_touring").lower()
    assert "tour routing assessment" in text or "routing assessment" in text
    assert "offer evaluation" in text


# ── new contracts / crew / on-sale knowledge ──────────────────────────────────

def test_new_file_present_in_assembled_knowledge():
    """New file contributed in phase 3f must be present in assembled knowledge."""
    text = registry.load_domain("live_touring").lower()
    assert "deal memo" in text, (
        "touring-contracts-crew-onsale.md content not found in assembled knowledge"
    )


def test_deal_memo_anatomy_content():
    text = registry.load_domain("live_touring").lower()
    assert "adjusted gross" in text
    assert "payment schedule" in text
    assert "radius clause" in text


def test_cancellation_force_majeure_content():
    text = registry.load_domain("live_touring").lower()
    assert "force majeure" in text
    assert "cancellation" in text


def test_support_slot_mechanics_content():
    text = registry.load_domain("live_touring").lower()
    assert "support slot" in text
    assert "support fee" in text or "support guarantee" in text


def test_support_slot_production_advance():
    text = registry.load_domain("live_touring").lower()
    assert "headliner" in text
    assert "production manager" in text


def test_nightly_settlement_deep_dive():
    text = registry.load_domain("live_touring").lower()
    assert "box-office statement" in text or "box office statement" in text
    assert "settlement sequence" in text or "settlement process" in text
    assert "under protest" in text


def test_on_sale_sequencing_content():
    text = registry.load_domain("live_touring").lower()
    assert "presale" in text or "pre-sale" in text
    assert "general on-sale" in text or "on-sale" in text
    assert "announcement" in text


def test_presale_ladder_content():
    text = registry.load_domain("live_touring").lower()
    assert "fan club" in text or "artist-to-fan" in text
    assert "credit-card" in text or "credit card" in text


def test_sales_velocity_monitoring():
    text = registry.load_domain("live_touring").lower()
    assert "sell-through" in text or "velocity" in text
    assert "venue right-sizing" in text or "right-siz" in text


def test_crew_hierarchy_content():
    text = registry.load_domain("live_touring").lower()
    assert "tour manager" in text
    assert "production manager" in text
    assert "foh engineer" in text or "front-of-house" in text
    assert "monitor engineer" in text


def test_union_considerations_content():
    text = registry.load_domain("live_touring").lower()
    assert "iatse" in text
    assert "union" in text
    assert "carry-through" in text or "stagehand" in text


def test_crew_classification_content():
    text = registry.load_domain("live_touring").lower()
    assert "per diem" in text or "per-diem" in text
    assert "independent contractor" in text


def test_road_book_day_sheet_content():
    text = registry.load_domain("live_touring").lower()
    assert "road book" in text
    assert "day sheet" in text


def test_curfew_overtime_content():
    text = registry.load_domain("live_touring").lower()
    assert "curfew" in text
    assert "overtime" in text


def test_tour_insurance_content():
    text = registry.load_domain("live_touring").lower()
    assert "cancellation insurance" in text or "non-appearance" in text
    assert "underwriting" in text or "premium" in text


def test_venue_tier_advancement_signals():
    text = registry.load_domain("live_touring").lower()
    assert "advancement signal" in text or "advancement signals" in text
    assert "85%" in text or "85 percent" in text


def test_luminate_soundscan_content():
    text = registry.load_domain("live_touring").lower()
    assert "luminate" in text


def test_marketing_obligations_content():
    text = registry.load_domain("live_touring").lower()
    assert "marketing budget" in text or "marketing commitment" in text
    assert "marketing deduction" in text or "marketing withholding" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_tour_routing_query():
    assert "live_touring" in brain.route(
        "build a tour routing plan for the upcoming headline run"
    )


def test_route_deal_memo_query():
    result = brain.route("negotiate a deal memo for the upcoming tour dates")
    assert "live_touring" in result


def test_route_venue_offer_query():
    assert "live_touring" in brain.route(
        "evaluate the promoter offer for the venue and check the split point"
    )


def test_route_show_advance_query():
    assert "live_touring" in brain.route(
        "advance the upcoming show with the venue and settle the promoter deal"
    )


def test_route_irrelevant_query_excludes_live_touring():
    # A pure publishing/mechanical-royalties query should not pull in live_touring
    result = brain.route(
        "calculate the mechanical royalty rate for the album on streaming"
    )
    assert "live_touring" not in result


def test_route_irrelevant_returns_empty_or_other():
    result = brain.route("the weather in chicago")
    assert "live_touring" not in result


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_live_touring_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "live_touring" in result["domains"]
    assert "# Live & Touring (live_touring)" in result["knowledge"]
    assert result["knowledge"].strip()


def test_consult_knowledge_contains_new_content():
    result = brain.consult(IN_DOMAIN_QUERY)
    text = result["knowledge"].lower()
    assert "deal memo" in text
    assert "support slot" in text


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("live_touring"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("route the tour and evaluate the offers", "live_touring"),
        ("build the production advance for the headline run", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
