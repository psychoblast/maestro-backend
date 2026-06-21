"""
Phase 3e — Per-agent deep consult test for press-monitor.

Scope: press-monitor only. Home domain "marketing". Six realistic
questions an artist or their team would ask Press (Media Monitor), covering:
copyright infringement press narrative and legal exposure, sync placement
media coverage amplification, concert tour press and revenue tracking,
fan community sentiment and social mention monitoring, streaming analytics
correlation with press coverage, and a deliberately narrow pure
media-tracking question.

For each cross-domain question we assert:
  (a) press-monitor's home domain "marketing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure press coverage and media tracking question that
avoids keywords from legal, sync, live_touring, fan_social, data_analytics,
finance_royalties, playlist_dsp, bizdev, or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "press-monitor"
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
        # marketing:  home — always leads
        # legal:      "copyright", "infringement", "legal", "dispute"
        "We need to monitor press coverage and media mentions around a copyright "
        "infringement claim against our artist — how do we track the narrative "
        "and manage the legal dispute coverage across major publications?",
        ["legal"],
    ),
    (
        # marketing:  home — always leads
        # sync:       "sync", "licens" (via "licensing"), "tv", "placement"
        "We need to track press coverage of our sync licensing placement in a "
        "major TV series — how do we monitor every media mention and measure "
        "the PR impact of this sync deal?",
        ["sync"],
    ),
    (
        # marketing:  home — always leads
        # live_touring: "concert", "tour"
        # finance_royalties: "tour revenue", "income split" (in "income splits")
        # Note: "announced" used instead of "upcoming" — "upcoming" contains
        # "upc" which triggers digital_ops as a substring match.
        "We are monitoring press coverage for our announced concert tour — what "
        "media tracking strategy captures coverage across outlets and how do we "
        "correlate tour revenue and income splits to press impact?",
        ["live_touring", "finance_royalties"],
    ),
    (
        # marketing:  home — always leads
        # fan_social: "fan community", "direct-to-fan", "fan engagement"
        "We need to track social mentions and sentiment in our fan community — "
        "what press monitoring strategy captures direct-to-fan conversation and "
        "fan engagement signals across platforms?",
        ["fan_social"],
    ),
    (
        # marketing:  home — always leads
        # data_analytics: "analytics" (via "streaming analytics"),
        #                 "metric" (via "audience metrics"),
        #                 "streaming data"
        "We need to correlate press coverage data with streaming analytics and "
        "audience metrics — how do we build a monitoring dashboard that connects "
        "media mentions to streaming data and growth?",
        ["data_analytics"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped media coverage tracking question that returns ONLY "marketing".
# Keywords triggered: "audience" (marketing), "reach" (marketing),
# "impressions" (marketing) — all map to marketing.
# Deliberately avoids: "copyright" / "infringement" / "legal" / "dispute" /
# "rights" (legal), "sync" / "licens" / "tv" / "placement" (sync),
# "tour" / "concert" (live_touring), "fan community" / "direct-to-fan" /
# "fan engagement" (fan_social), "analytics" / "metric" / "streaming data"
# (data_analytics), "royalt" / "splits" / "tour revenue" (finance_royalties),
# "playlist" / "dsp" / "editorial" (playlist_dsp), "brand" / "sponsor"
# (bizdev), "intelligence" / "monitor the industry" (intelligence).
# Note: "upcoming" excluded — "upc" is a digital_ops substring match trigger.
# Note: "publish" excluded — publishing is a domain keyword.

_NARROW_QUERY = (
    "We need to build a press coverage tracking system for our artist "
    "— what is the best process to capture every major review and "
    "media mention so we always know our audience reach and impressions?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "copyright-infringement-press-narrative-legal-exposure",
        "sync-placement-media-coverage-amplification",
        "concert-tour-press-revenue-income-splits",
        "fan-community-sentiment-direct-to-fan-monitoring",
        "streaming-analytics-audience-metrics-press-correlation",
    ],
)
def test_press_monitor_consult_home_leads_and_cross_domains_present(query, cross):
    """
    press-monitor's home domain 'marketing' is always first; every
    expected cross-domain is present. Verifies home-first invariant and
    media-monitor-specific cross-domain routing quality.
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


def test_press_monitor_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped media coverage and press tracking question (only
    'audience', 'reach', and 'impressions' trigger — all marketing) must
    return only the home domain with no spurious cross-domain routing from
    legal/sync/live_touring/fan_social/data_analytics/finance_royalties/
    playlist_dsp/bizdev or any other domain.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
