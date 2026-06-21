"""
Phase 3e — Per-agent deep consult test for pr-agent.

Scope: pr-agent only. Home domain "marketing". Six realistic
questions an artist or their team would ask Quinn (PR Manager), covering:
sync placement editorial coverage amplification, brand endorsement
partnership PR announcement, concert tour press campaign with promoter
contract negotiation, streaming analytics and audience metrics press ROI
tracking, fan community launch direct-to-fan PR strategy, and a
deliberately narrow EPK and media outreach question.

For each cross-domain question we assert:
  (a) pr-agent's home domain "marketing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure press kit and media outreach question that
avoids keywords from sync, legal, live_touring, fan_social, playlist_dsp,
data_analytics, bizdev, finance_royalties, publishing, or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "pr-agent"
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
        # marketing:  home — always leads; "campaign", "reach"
        # sync:       "sync" (via "sync licensing", "sync deal"),
        #             "licens" (via "licensing"), "tv" (via "TV"), "placement"
        "We need editorial press coverage to amplify our sync licensing "
        "placement in a major TV series — how do we craft the campaign and "
        "pitch journalists to maximise the media reach of this sync deal?",
        ["sync"],
    ),
    (
        # marketing:  home — always leads; "campaign", "press strategy",
        #             "audience", "reach"
        # bizdev:     "brand" (via "brand endorsement", "brand partnership"),
        #             "endorsement", "sponsor", "partnership"
        "We have secured a brand endorsement deal with a major sponsor — how "
        "do we build a PR campaign and press strategy around the brand "
        "partnership announcement to grow audience and reach?",
        ["bizdev"],
    ),
    (
        # marketing:  home — always leads; "campaign"
        # live_touring: "concert", "tour" (via "concert tour"), "promoter"
        # legal:      "contract" (via "promoter contract"), "negotiat" (via "negotiate")
        "We are running a PR campaign for our concert tour announcement and "
        "need guidance on the promoter contract terms and how to negotiate "
        "our live fee before the press launch.",
        ["live_touring", "legal"],
    ),
    (
        # marketing:  home — always leads; "campaign", "audience", "growth"
        # data_analytics: "analytics" (via "streaming analytics"),
        #                 "metric" (via "audience metrics"), "streaming data"
        "We need to measure whether our press campaign is generating an "
        "impact on streaming analytics and audience metrics — how do we "
        "connect media coverage data to streaming data signals and growth?",
        ["data_analytics"],
    ),
    (
        # marketing:  home — always leads; "campaign", "engagement"
        # fan_social: "fan community", "direct-to-fan", "fan engagement"
        "We are launching a PR campaign to support our artist's fan community "
        "debut — what press and media strategy builds direct-to-fan coverage "
        "and fan engagement across outlets?",
        ["fan_social"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped press kit and media outreach question that returns ONLY
# "marketing". Keywords triggered: "audience", "reach", "impressions",
# "campaign" — all map to marketing.
# Deliberately avoids: "sync" / "licens" / "placement" / "tv" (sync),
# "contract" / "copyright" / "rights" / "legal" (legal),
# "tour" / "concert" / "promoter" (live_touring),
# "fan community" / "direct-to-fan" / "fan engagement" (fan_social),
# "analytics" / "metric" / "streaming data" (data_analytics),
# "brand" / "sponsor" / "partnership" / "endorsement" (bizdev),
# "playlist" / "dsp" / "editorial" (playlist_dsp),
# "royalt" / "splits" / "advance" (finance_royalties),
# "publish" / "catalog" / "songwriter" (publishing),
# "intelligence" / "market intelligence" (intelligence),
# "label ops" / "distribution" (label_ops).
# Note: "upcoming" excluded — "upc" is a digital_ops substring match trigger.
# Note: "newsletter" excluded — triggers fan_social.

_NARROW_QUERY = (
    "We need to write and format our artist's EPK for media outreach "
    "— how do we structure the bio, press photo, and pitch so every "
    "journalist contact understands our audience reach and campaign impressions?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "sync-placement-editorial-coverage-amplification",
        "brand-endorsement-partnership-pr-announcement",
        "concert-tour-promoter-contract-press-campaign",
        "streaming-analytics-audience-metrics-press-roi",
        "fan-community-launch-direct-to-fan-pr-strategy",
    ],
)
def test_pr_agent_consult_home_leads_and_cross_domains_present(query, cross):
    """
    pr-agent's home domain 'marketing' is always first; every expected
    cross-domain is present. Verifies home-first invariant and PR
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


def test_pr_agent_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped press kit and media outreach question (only 'audience',
    'reach', 'impressions', and 'campaign' trigger — all marketing) must
    return only the home domain with no spurious cross-domain routing from
    sync/legal/live_touring/fan_social/data_analytics/bizdev/playlist_dsp/
    finance_royalties/publishing or any other domain.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
