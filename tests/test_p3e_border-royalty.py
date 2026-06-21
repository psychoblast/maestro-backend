"""
Phase 3e — Per-agent deep consult test for border-royalty.

Scope: border-royalty only. Home domain "finance_royalties". Six realistic
questions an artist or their team would ask Cleo (Neighbouring Rights
Specialist), covering: SoundExchange vs publishing income, contract
protection for master ownership, European tour neighbouring rights,
analytics-based income forecasting, brand deal revenue structuring, and a
deliberately narrow home-only SoundExchange registration question.

For each cross-domain question we assert:
  (a) border-royalty's home domain "finance_royalties" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — only "royalt" triggers (SoundExchange payment cycles /
registration steps, no "rights", no publishing, no tour, no legal terms).

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "border-royalty"
_HOME  = "finance_royalties"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "finance_royalties" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # finance_royalties: "neighbouring rights"
        # publishing: "publishing admin" (substring of "publishing administration"),
        #             "songwrit" (substring of "songwriter")
        "How do our SoundExchange neighbouring rights collections interact "
        "with publishing administration income — specifically the songwriter "
        "share and how PRO registration affects both streams?",
        ["publishing"],
    ),
    (
        # finance_royalties: "neighbouring rights"
        # legal: "contract", "negotiat", "rights"
        "We need to negotiate our neighbouring rights agreement and ensure "
        "the contract terms protect our master recording ownership across all "
        "collection societies before we sign anything",
        ["legal"],
    ),
    (
        # finance_royalties: "neighbouring rights"
        # live_touring: "touring", "venue"
        "Our artist is touring Europe and we want to claim neighbouring "
        "rights income from German and Dutch radio broadcasts and public "
        "venue performances happening during the tour",
        ["live_touring"],
    ),
    (
        # finance_royalties: "neighbouring rights", "streaming income"
        # data_analytics: "analytics", "metric", "forecast"
        "Can we use streaming analytics and DSP metrics to forecast our "
        "neighbouring rights streaming income potential and benchmark "
        "SoundExchange revenue across all active territories?",
        ["data_analytics"],
    ),
    (
        # finance_royalties: "neighbouring rights", "royalt"
        # bizdev: "brand", "partnership"
        "We are structuring a brand partnership deal and want to include "
        "our neighbouring rights royalty income streams as a documented "
        "revenue asset in the partnership agreement",
        ["bizdev"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped SoundExchange registration question that returns ONLY
# "finance_royalties". Keyword triggered: "royalt" (via "royalty").
# Deliberately avoids: "copyright" (legal), "rights" (legal), "publish"
# (publishing), "tour" (live_touring), "contract" (legal),
# "analytics" (data_analytics).

_NARROW_QUERY = (
    "What royalty payment timelines and quarterly disbursement cycles should "
    "we expect from SoundExchange after we register as a featured performer?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "soundexchange-publishing-admin-songwriter-interaction",
        "neighbouring-rights-contract-negotiation-master-ownership",
        "european-tour-neighbouring-rights-venue-broadcasts",
        "streaming-analytics-dsp-metrics-income-forecast",
        "brand-partnership-royalty-revenue-asset",
    ],
)
def test_border_royalty_consult_home_leads_and_cross_domains_present(query, cross):
    """
    border-royalty's home domain 'finance_royalties' is always first; every
    expected cross-domain is present. Verifies home-first invariant and
    neighbouring-rights-specific cross-domain routing quality.
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


def test_border_royalty_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped SoundExchange registration question (only 'royalt'
    triggers) must return only the home domain 'finance_royalties' — no
    spurious cross-domain routing from legal/publishing/touring/analytics terms.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
