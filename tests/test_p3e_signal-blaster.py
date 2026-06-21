"""
Phase 3e — Per-agent deep consult test for signal-blaster.

Scope: signal-blaster only. Home domain "marketing". Six realistic
questions an artist or their team would ask Zara (Publicist), covering:
press campaign amplifying a sync licensing placement, crisis PR and legal
exposure management, tour announcement press strategy and revenue tracking,
fan community launch and direct-to-fan PR, DSP editorial release campaign
alignment, and a deliberately narrow press outreach question.

For each cross-domain question we assert:
  (a) signal-blaster's home domain "marketing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure press outreach and media messaging question that
avoids keywords from sync, legal, live_touring, fan_social, playlist_dsp,
finance_royalties, data_analytics, capital_funding, or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "signal-blaster"
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
        # marketing:     "campaign", "reach" (home)
        # sync:          "sync", "licens" (via "licensing"), "placement",
        #                "tv" (via "TV"), "advert" (via "advertisement")
        "We need a media strategy and press campaign to amplify our sync "
        "licensing placement in a major TV advertisement — how do we "
        "maximise the PR reach of this placement?",
        ["sync"],
    ),
    (
        # marketing:     "press strategy" (home)
        # legal:         "copyright", "infringement", "legal"
        "We need a press strategy to manage a copyright infringement claim "
        "— how do we control the narrative and limit our legal exposure?",
        ["legal"],
    ),
    (
        # marketing:     "campaign", "rollout" (home)
        # live_touring:  "concert", "tour" (via "concert tour", "tour revenue")
        # finance_royalties: "tour revenue", "income split" (via "income splits")
        "We are building a press campaign for our upcoming concert tour — "
        "what is the media rollout strategy and how do we track our tour "
        "revenue and income splits?",
        ["live_touring", "finance_royalties"],
    ),
    (
        # marketing:     "campaign", "engagement", "growth" (home)
        # fan_social:    "fan community", "direct-to-fan", "fan club"
        "We are building a PR campaign to support our fan community launch "
        "— what press and media strategy drives direct-to-fan engagement "
        "and fan club growth?",
        ["fan_social"],
    ),
    (
        # marketing:     "marketing", "campaign", "playlist", "rollout" (home)
        # playlist_dsp:  "dsp", "editorial playlist", "playlist"
        "We are planning a press and marketing campaign for our album "
        "release that includes a DSP editorial playlist submission — what "
        "media strategy supports the streaming rollout?",
        ["playlist_dsp"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped press outreach question that returns ONLY "marketing".
# Keywords triggered: "press strategy", "marketing" (via "marketing message"),
# "audience", "reach", "impressions" — all map to marketing.
# Deliberately avoids: "sync" / "licens" (sync), "contract" / "copyright" /
# "legal" (legal), "tour" / "concert" (live_touring), "fan community" /
# "direct-to-fan" / "fan club" (fan_social), "playlist" / "dsp" / "editorial"
# (playlist_dsp), "royalt" / "splits" (finance_royalties), "analytics" /
# "metric" (data_analytics), "capital" / "fund" (capital_funding),
# "label ops" / "distribution" (label_ops).
# Note: "brand" excluded — triggers bizdev.
# Note: "upcoming" excluded — "upc" is a digital_ops substring match trigger.

_NARROW_QUERY = (
    "We need a press strategy for our artist's new magazine feature "
    "— how do we shape our marketing message and media narrative to grow "
    "audience reach and impressions?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "sync-licensing-placement-press-campaign-amplification",
        "copyright-infringement-crisis-pr-legal-exposure",
        "concert-tour-press-campaign-revenue-income-splits",
        "fan-community-launch-direct-to-fan-pr-campaign",
        "dsp-editorial-playlist-release-campaign-alignment",
    ],
)
def test_signal_blaster_consult_home_leads_and_cross_domains_present(query, cross):
    """
    signal-blaster's home domain 'marketing' is always first; every
    expected cross-domain is present. Verifies home-first invariant and
    publicist-specific cross-domain routing quality.
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


def test_signal_blaster_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped press outreach and brand messaging question (only
    'press strategy', 'marketing', 'audience', 'reach', and 'impressions'
    trigger — all marketing) must return only the home domain with no
    spurious cross-domain routing from sync/legal/live_touring/fan_social/
    playlist_dsp/finance_royalties/bizdev or any other domain.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
