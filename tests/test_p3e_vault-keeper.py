"""
Phase 3e — Per-agent deep consult test for vault-keeper.

Scope: vault-keeper only. Home domain "finance_royalties". Six realistic
questions an artist or their team would ask Victor (Business Manager),
covering: touring run show-fee cash-flow model, brand endorsement deal
income splits, year-end ledger integrity closure, streaming-data income
forecasting, publishing administration revenue, and a deliberately narrow
monthly-budget/cashflow question.

For each cross-domain question we assert:
  (a) vault-keeper's home domain "finance_royalties" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure monthly operating-budget / cashflow question that
contains no keywords from live_touring, bizdev, controller, data_analytics,
publishing, capital_funding, legal, or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "vault-keeper"
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
        # finance_royalties: home (always first); "tour revenue" re-confirms
        # live_touring: "touring", "venue", "show fee"
        "We are planning a six-month touring run and need to model show fee "
        "budgets, project venue settlement cashflow, and track tour revenue "
        "across each date",
        ["live_touring"],
    ),
    (
        # finance_royalties: home + "splits" (via "income splits")
        # bizdev: "brand", "endorsement", "partnership"
        "We have a brand endorsement offer with guaranteed monthly payments "
        "and backend participation — how do we evaluate the income splits "
        "and structure the partnership fee terms?",
        ["bizdev"],
    ),
    (
        # finance_royalties: home
        # controller: "ledger integrity", "closing the books",
        #             "trial balance", "audit-ready"
        "We need to verify ledger integrity after closing the books on the "
        "annual accounts, review the trial balance, and ensure our records "
        "are audit-ready for year-end",
        ["controller"],
    ),
    (
        # finance_royalties: home + "royalt" (via "royalty")
        # data_analytics: "streaming data", "metrics", "trajectory",
        #                 "forecast", "projection" (via "projections")
        "We want to use streaming data metrics and listener trajectory trends "
        "to forecast annual royalty income and build quarterly revenue "
        "projections",
        ["data_analytics"],
    ),
    (
        # finance_royalties: home + "royalt" (via "royalties")
        # publishing: "publish" (via "publishing"), "catalog",
        #             "administration", "sub-publish"
        "We need to understand the publishing administration income flowing "
        "into our annual revenue budget — specifically the catalog royalties "
        "from our publishing deal and sub-publishing arrangements",
        ["publishing"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A pure monthly operating-budget and cashflow question that returns ONLY
# "finance_royalties". Deliberately avoids: "tour"/"touring"/"venue"/"show fee"
# (live_touring — note "revenue" contains "venue" so "revenue" is also avoided),
# "brand"/"endorsement"/"partnership" (bizdev), "ledger"/"reconcil"/
# "closing the books" (controller), "streaming data"/"metrics"/"trajectory"/
# "forecast" (data_analytics), "publish"/"catalog"/"administration" (publishing),
# "financ"/"capital"/"fund" (capital_funding), "contract"/"legal"/"rights"
# (legal), "royalt"/"mechanical"/"accounting" (finance_royalties cross-trigger).

_NARROW_QUERY = (
    "How do we structure a monthly artist operating budget, manage day-to-day "
    "business expenses, and project quarterly cashflow to maintain a healthy "
    "cash position?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "touring-run-show-fee-venue-settlement-tour-revenue",
        "brand-endorsement-income-splits-partnership-fee-terms",
        "ledger-integrity-closing-books-trial-balance-audit-ready",
        "streaming-data-metrics-trajectory-forecast-royalty-projections",
        "publishing-admin-catalog-royalties-sub-publishing-budget",
    ],
)
def test_vault_keeper_consult_home_leads_and_cross_domains_present(query, cross):
    """
    vault-keeper's home domain 'finance_royalties' is always first; every
    expected cross-domain is present. Verifies home-first invariant and
    business-manager-specific cross-domain routing quality.
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


def test_vault_keeper_narrow_query_returns_home_domain_only():
    """
    A purely scoped monthly-budget and cashflow question (no cross-domain
    keywords) must return only the home domain 'finance_royalties' — no
    spurious routing to live_touring, bizdev, controller, data_analytics,
    publishing, capital_funding, legal, or any other domain.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
