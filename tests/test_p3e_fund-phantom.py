"""
Phase 3e — Per-agent deep consult test for fund-phantom.

Scope: fund-phantom only. Home domain "capital_funding". Six realistic
questions an artist or their team would ask fund-phantom, covering grant
applications, investor term sheets, royalty-backed financing, publishing
catalog securitization, marketing grant campaigns, and touring grant subsidy —
plus a deliberately narrow home-only scenario.

For each cross-domain question we assert:
  (a) fund-phantom's home domain "capital_funding" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "fund-phantom"
_HOME  = "capital_funding"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "capital_funding" leads; every expected cross-domain is present.

DEEP_CONSULT_MATRIX = [
    (
        # capital_funding: safe note, convertible, equity, term sheet, financ, invest
        # legal: term sheet, clause, negotiat, legal, rights, dispute
        "We have a SAFE note investor offering a convertible equity round — we "
        "need legal review of the term sheet clauses and to negotiate the rights "
        "and dispute resolution provisions before closing the financing",
        ["legal"],
    ),
    (
        # capital_funding: revenue-based, financ, capital
        # finance_royalties: royalt, advance, recoup, accounting, statement
        "We want to raise revenue-based financing against our future royalty "
        "income — help us understand the capital structure and how advance "
        "recoupment from royalty accounting statements works",
        ["finance_royalties"],
    ),
    (
        # capital_funding: grant, fund (in "fund a", "funding")
        # marketing: marketing, campaign, audience, fan base
        "We are applying for a FACTOR grant to fund a marketing campaign and "
        "need a strong audience growth strategy and fan base expansion plan to "
        "include in our funding application",
        ["marketing"],
    ),
    (
        # capital_funding: capital, raise capital, valuation
        # publishing: publish, catalog, songwrit, composition, administration
        "We are raising capital by monetizing our publishing catalog — can we "
        "structure a valuation deal that securitizes our songwriter compositions "
        "and catalog administration earnings?",
        ["publishing"],
    ),
    (
        # capital_funding: fund (in "funding"), grant, subsidy
        # live_touring: touring, festival, tour, festival appearance
        "We need touring grant funding to cover our festival appearances on the "
        "international live touring circuit — what subsidies and grant programs "
        "are available to offset tour costs for independent artists?",
        ["live_touring"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped grant-strategy question that returns ONLY "capital_funding".
# Keywords triggered: grant, fund (in "funding"), crowdfund, non-dilutive,
#                    capital, runway.
# No legal/marketing/publishing/touring/finance_royalties terms present.

_NARROW_QUERY = (
    "How do we structure a FACTOR grant application and what crowdfunding "
    "strategies work alongside non-dilutive funding to build our capital runway?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "safe-note-convertible-equity-term-sheet-legal-review",
        "revenue-based-financing-royalty-advance-recoupment",
        "factor-grant-marketing-campaign-audience-growth",
        "publishing-catalog-securitization-valuation",
        "touring-grant-festival-appearances-subsidy",
    ],
)
def test_fund_phantom_consult_home_leads_and_cross_domains_present(query, cross):
    """
    fund-phantom's home domain 'capital_funding' is always first; every
    expected cross-domain is present. Verifies home-first invariant and
    funding-specific cross-domain routing quality.
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


def test_fund_phantom_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped grant-strategy question (grant, fund, crowdfund,
    non-dilutive, capital, runway) must return only the home domain
    'capital_funding' — no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
