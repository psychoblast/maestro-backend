"""
Phase 3e — Per-agent deep consult test for social-manager.

Scope: social-manager only. Home domain "marketing". Six realistic
questions an artist or their team would ask Riley (Social Media Manager),
covering: fan community growth from social channels, DSP release support
via playlist-pitch content cadence, social campaign analytics tracking,
combined superfan activation and pre-save playlist push, brand endorsement
integration into the social calendar, and a deliberately narrow posting
cadence question.

For each cross-domain question we assert:
  (a) social-manager's home domain "marketing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure posting cadence and content-format question that
avoids keywords from fan_social, playlist_dsp, data_analytics, bizdev,
live_touring, sync, legal, finance_royalties, publishing, or any other
domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "social-manager"
_HOME  = "marketing"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "marketing" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # marketing:    home — always leads; "social media", "content strategy",
        #               "engagement", "fanbase"
        # fan_social:   "fan community", "direct-to-fan", "fan retention"
        "We want to evolve our Instagram and TikTok social media presence "
        "into a real fan community — how do we build a content strategy "
        "that drives direct-to-fan engagement and improves fan retention "
        "across our social channels?",
        ["fan_social"],
    ),
    (
        # marketing:    home — always leads; "social media", "content strategy",
        #               "campaign", "rollout"
        # playlist_dsp: "dsp", "playlist", "editorial pitch", "pre-save"
        "We need a social media content strategy to support our DSP playlist "
        "pitch window and drive pre-save conversions ahead of the release "
        "rollout — what content cadence and platform mix should we use?",
        ["playlist_dsp"],
    ),
    (
        # marketing:    home — always leads; "social media", "campaign",
        #               "audience", "engagement"
        # data_analytics: "streaming analytics" (via "analytics"),
        #                 "social metric" (via "social metrics"),
        #                 "streaming data", "metric"
        "How do we measure whether our social media campaign is moving the "
        "needle on streaming analytics — which audience metrics and social "
        "metrics best connect our content output to streaming data signals "
        "and listener growth?",
        ["data_analytics"],
    ),
    (
        # marketing:    home — always leads; "instagram", "tiktok",
        #               "content strategy", "rollout"
        # fan_social:   "superfan", "fan engagement"
        # playlist_dsp: "pre-save", "playlist add"
        "We are building a multi-platform social rollout for a new single "
        "— how do we use Instagram and TikTok content to activate our "
        "superfan base, drive fan engagement, and convert that momentum "
        "into pre-save clicks and playlist adds?",
        ["fan_social", "playlist_dsp"],
    ),
    (
        # marketing:    home — always leads; "campaign", "rollout",
        #               "content strategy", "audience", "fanbase"
        # bizdev:       "brand endorsement", "endorsement", "sponsor",
        #               "brand" (via "brand endorsement")
        "We have secured a brand endorsement deal with a major sponsor — "
        "how do we integrate their messaging authentically into our social "
        "content calendar and build a campaign rollout that grows audience "
        "without alienating our existing fanbase?",
        ["bizdev"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped posting cadence and content format question that returns
# ONLY "marketing". Keywords triggered: "instagram", "tiktok", "social media",
# "follower", "reach", "impressions", "audience", "engagement" — all marketing.
# Deliberately avoids:
# "fan community" / "direct-to-fan" / "fan retention" / "superfan" /
# "fan engagement" / "engagement rate" / "newsletter" (fan_social)
# "playlist" / "dsp" / "editorial" / "pre-save" (playlist_dsp)
# "analytics" / "metric" / "streaming data" / "social metric" /
# "growth metric" (data_analytics)
# "brand" / "sponsor" / "endorsement" / "partnership" (bizdev)
# "tour" / "concert" / "promoter" (live_touring)
# "sync" / "licens" / "placement" / "film" / "tv" (sync)
# "contract" / "copyright" / "legal" / "rights" (legal)
# "royalt" / "advance" / "splits" / "mechanical" (finance_royalties)
# "publish" / "catalog" / "songwriter" / "co-write" (publishing)
# "label ops" / "distributor" / "release planning" / "release cadence" (label_ops)
# "intelligence" / "market intelligence" (intelligence)
# "upc" / "isrc" / "metadata" (digital_ops)

_NARROW_QUERY = (
    "What is the ideal posting cadence and content format mix across "
    "our Instagram and TikTok social media channels to grow our follower "
    "count, maximize reach and impressions, and sustain audience engagement "
    "for an indie artist account?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "fan-community-growth-direct-to-fan-retention",
        "dsp-playlist-pitch-pre-save-content-cadence",
        "social-campaign-streaming-analytics-metrics",
        "superfan-activation-pre-save-playlist-adds",
        "brand-endorsement-sponsor-content-calendar",
    ],
)
def test_social_manager_consult_home_leads_and_cross_domains_present(query, cross):
    """
    social-manager's home domain 'marketing' is always first; every expected
    cross-domain is present. Verifies home-first invariant and social media
    manager-specific cross-domain routing quality.
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


def test_social_manager_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped posting cadence and content format question (only
    'instagram', 'tiktok', 'social media', 'follower', 'reach', 'impressions',
    and 'audience' trigger — all marketing) must return only the home domain
    with no spurious cross-domain routing from fan_social/playlist_dsp/
    data_analytics/bizdev/live_touring/sync/legal/finance_royalties/
    publishing/label_ops or any other domain.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
