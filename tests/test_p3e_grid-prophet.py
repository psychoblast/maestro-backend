"""
Phase 3e — Per-agent deep consult test for grid-prophet.

Scope: grid-prophet only. Home domain "marketing". Six realistic questions an
artist or their team would ask Kai, the Digital Marketing specialist, covering
social growth, analytics, release coordination, fan community, market trends,
and DSP/playlist strategy.

For each cross-domain question we assert:
  (a) grid-prophet's home domain "marketing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "grid-prophet"
_HOME  = "marketing"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "marketing" leads; every expected cross-domain is present.

DEEP_CONSULT_MATRIX = [
    (
        # marketing: campaign, fan base, newsletter
        # fan_social: superfan conversion, fan club tier, fan newsletter
        "How do we build a fan club tier system with superfan conversion "
        "tracking and a fan newsletter to deepen direct-to-fan relationships?",
        ["fan_social"],
    ),
    (
        # marketing: campaign, performance, benchmark
        # data_analytics: analytics, kpi, metric, benchmark
        "We need to set up analytics dashboards with KPI metrics and "
        "benchmark our campaign performance data across platforms",
        ["data_analytics"],
    ),
    (
        # marketing: campaign, rollout
        # label_ops: release tracking, distribution strategy, release readiness
        "We need to build a release tracking workflow and distribution "
        "strategy with release readiness milestones before our campaign launch",
        ["label_ops"],
    ),
    (
        # marketing: digital marketing, campaign
        # intelligence: market trend, competitive landscape (orphan domain)
        "What market trends and competitive landscape shifts should inform "
        "our digital marketing strategy for the next campaign cycle?",
        ["intelligence"],
    ),
    (
        # marketing: social media, rollout, release strategy
        # playlist_dsp: playlist pitch window, spotify editorial, pre-save
        "We want to time our social rollout to align with a playlist pitch "
        "window and Spotify editorial consideration for maximum impact",
        ["playlist_dsp"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped social media question that returns ONLY "marketing".
# Uses Instagram and hashtag/caption terms — all map to marketing only.

_NARROW_QUERY = (
    "What are the best caption and hashtag practices for growing "
    "Instagram Reels views organically?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "fan-club-tier-superfan-conversion-fan-social",
        "analytics-kpi-benchmark-data-analytics",
        "release-tracking-distribution-milestones-label-ops",
        "market-trends-competitive-landscape-intelligence",
        "social-rollout-playlist-pitch-spotify-editorial",
    ],
)
def test_grid_prophet_consult_home_leads_and_cross_domains_present(query, cross):
    """
    grid-prophet's home domain 'marketing' is always first; every expected
    cross-domain is present. Verifies home-first invariant and digital-marketing-
    specific cross-domain routing quality.
    """
    result = _consult(query)

    assert result["home_domain"] == _HOME, (
        f"expected home={_HOME!r}, got {result['home_domain']!r}"
    )
    assert result["domains"], "domains list is empty"
    assert result["domains"][0] == _HOME, (
        f"home domain must be first; got {result['domains']}"
    )
    for d in cross:
        assert d in result["domains"], (
            f"expected cross-domain {d!r} not found in {result['domains']}\n"
            f"Query: {query!r}"
        )
    assert result["knowledge"].strip(), "knowledge text is empty"


def test_grid_prophet_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped Instagram/hashtag question must return only the home
    domain 'marketing' — no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
