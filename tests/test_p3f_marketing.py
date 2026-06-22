"""
Phase 3f — deepened marketing domain knowledge tests.

Verifies that the 'marketing' domain loads via the bank's normal path
(skills/maestro-grid-prophet/knowledge/), is non-trivially sized, includes
the required sections and new phase-3f content, and contains no forbidden
entity strings.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "build a full marketing campaign plan for this release including "
    "digital channels, paid media strategy, and audience growth targets"
)


# ── registry ─────────────────────────────────────────────────────────────────

def test_list_domains_includes_marketing():
    assert "marketing" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("marketing").display_name == "Marketing & Growth"


def test_get_domain_slug():
    assert registry.get_domain("marketing").slug == "grid-prophet"


def test_load_domain_returns_string():
    text = registry.load_domain("marketing")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("marketing")
    assert text.strip(), "marketing domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 9 knowledge files (7 original + 2 new) → expect at least 100 000 chars
    text = registry.load_domain("marketing")
    assert len(text) >= 100_000, (
        f"marketing knowledge too small: {len(text)} chars — expected ≥100 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 9 files → 8 separators between them
    text = registry.load_domain("marketing")
    assert text.count("\n\n---\n\n") >= 8, (
        "Expected ≥8 section separators (9 knowledge files) in marketing domain"
    )


# ── existing core content presence ───────────────────────────────────────────

def test_scoring_rubric_present():
    text = registry.load_domain("marketing").lower()
    assert "virality" in text
    assert "platform fit" in text
    assert "editorial readiness" in text


def test_campaign_architecture_present():
    text = registry.load_domain("marketing").lower()
    assert "full-funnel" in text or "full funnel" in text
    assert "awareness" in text
    assert "conversion" in text
    assert "retention" in text


def test_channel_economics_present():
    text = registry.load_domain("marketing").lower()
    assert "cpm" in text
    assert "spark ads" in text or "tiktok" in text
    assert "marquee" in text


def test_pr_press_strategy_present():
    text = registry.load_domain("marketing").lower()
    assert "pitchfork" in text or "press tier" in text
    assert "epk" in text
    assert "embargo" in text


def test_social_community_present():
    text = registry.load_domain("marketing").lower()
    assert "superfan" in text or "super-fan" in text
    assert "discord" in text or "community" in text


def test_content_lifecycle_present():
    text = registry.load_domain("marketing").lower()
    assert "content pillar" in text or "content calendar" in text
    assert "email" in text


# ── new analytics-and-attribution knowledge (phase 3f) ───────────────────────

def test_analytics_file_present():
    """marketing-analytics-and-attribution.md must be in assembled knowledge."""
    text = registry.load_domain("marketing").lower()
    assert "measurement stack" in text or "utm taxonomy" in text, (
        "marketing-analytics-and-attribution.md content not found"
    )


def test_analytics_measurement_layers():
    text = registry.load_domain("marketing").lower()
    assert "reach layer" in text or "engagement layer" in text
    assert "conversion layer" in text
    assert "ltv layer" in text or "ltv" in text


def test_analytics_utm_taxonomy():
    text = registry.load_domain("marketing").lower()
    assert "utm_source" in text or "utm source" in text
    assert "utm_medium" in text or "utm medium" in text
    assert "utm_campaign" in text or "utm campaign" in text


def test_analytics_attribution_models():
    text = registry.load_domain("marketing").lower()
    assert "last-click" in text or "last click" in text
    assert "first-click" in text or "first click" in text
    assert "attribution model" in text or "attribution" in text


def test_analytics_pixel_setup():
    text = registry.load_domain("marketing").lower()
    assert "pixel" in text
    assert "conversion api" in text or "server-side" in text


def test_analytics_streaming_attribution_windows():
    text = registry.load_domain("marketing").lower()
    assert "editorial algorithmic" in text or "attribution window" in text
    assert "release radar" in text or "discover weekly" in text


def test_analytics_decision_grade_metrics():
    text = registry.load_domain("marketing").lower()
    assert "save rate" in text
    assert "completion rate" in text
    assert "cost-per-email" in text or "cost per email" in text or "cpe" in text


def test_analytics_vanity_metrics():
    text = registry.load_domain("marketing").lower()
    assert "vanity metric" in text
    assert "follower count" in text or "impressions" in text


def test_analytics_post_mortem_framework():
    text = registry.load_domain("marketing").lower()
    assert "post-mortem" in text or "post mortem" in text
    assert "carry-forward" in text or "carry forward" in text


def test_analytics_dashboard_architecture():
    text = registry.load_domain("marketing").lower()
    assert "dashboard" in text
    assert "daily operations" in text or "weekly strategic" in text


# ── new release-strategy-decisions knowledge (phase 3f) ──────────────────────

def test_release_strategy_file_present():
    """release-strategy-decisions.md must be in assembled knowledge."""
    text = registry.load_domain("marketing").lower()
    assert "release format" in text or "release strategy" in text, (
        "release-strategy-decisions.md content not found"
    )


def test_release_format_framework():
    text = registry.load_domain("marketing").lower()
    assert "stand-alone single" in text or "stand alone single" in text or "ep (extended play)" in text or "extended play" in text
    assert "ep" in text
    assert "album" in text


def test_release_format_by_career_phase():
    text = registry.load_domain("marketing").lower()
    assert "development phase" in text
    assert "breakthrough phase" in text
    assert "peak phase" in text


def test_release_cadence_logic():
    text = registry.load_domain("marketing").lower()
    assert "cadence" in text
    assert "algorithm" in text


def test_release_cadence_antipatterns():
    text = registry.load_domain("marketing").lower()
    assert "too fast" in text or "too slow" in text
    assert "anti-pattern" in text or "antipattern" in text


def test_release_timing_day_of_week():
    text = registry.load_domain("marketing").lower()
    assert "friday" in text
    assert "new music friday" in text


def test_release_timing_seasonal_windows():
    text = registry.load_domain("marketing").lower()
    assert "q4" in text
    assert "february" in text or "spring" in text


def test_release_competition_avoidance():
    text = registry.load_domain("marketing").lower()
    assert "competition avoidance" in text or "competitive window" in text


def test_release_lead_single_criteria():
    text = registry.load_domain("marketing").lower()
    assert "lead single" in text
    assert "follow-up single" in text or "follow up single" in text


def test_release_album_announcement_timing():
    text = registry.load_domain("marketing").lower()
    assert "album announcement" in text
    assert "pre-order" in text or "pre-save" in text


def test_release_arc_sequencing():
    text = registry.load_domain("marketing").lower()
    assert "multi-release arc" in text or "release arc" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_marketing_query_to_marketing():
    assert "marketing" in brain.route(IN_DOMAIN_QUERY)


def test_route_campaign_query_to_marketing():
    assert "marketing" in brain.route(
        "design the go-to-market campaign for this artist's debut EP"
    )


def test_route_audience_growth_query_to_marketing():
    assert "marketing" in brain.route(
        "how do we grow the fanbase and increase engagement on social media"
    )


def test_route_paid_media_query_to_marketing():
    assert "marketing" in brain.route(
        "what ad spend and paid media strategy should we use for the release rollout"
    )


def test_route_unrelated_query_excludes_marketing():
    # A pure royalties query should not pull in the marketing domain
    assert "marketing" not in brain.route(
        "how do mechanical royalties recoup against the advance on the royalty statement"
    )


def test_route_irrelevant_query_returns_empty():
    assert brain.route("the weather in chicago") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_marketing_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "marketing" in result["domains"]
    assert "# Marketing & Growth (marketing)" in result["knowledge"]
    assert result["knowledge"].strip()


def test_consult_marketing_as_home_domain():
    result = brain.consult(
        "build a release strategy for this EP", home_domain="marketing"
    )
    assert "marketing" in result["domains"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("marketing"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("design a campaign for this emerging artist", "marketing"),
        ("what release format should we use and when should we drop it", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
