"""
Phase 3e — Per-agent deep consult test for ledger-lock.

Scope: ledger-lock only. Home domain "finance_royalties". Six realistic
questions an artist or their team would ask Nadia (Accountant), covering:
publishing royalty income tax, international withholding tax on streaming
income, touring expense deductions, royalty income forecasting for tax
planning, music grant income tax treatment, and a deliberately narrow
advance-payment accounting question.

For each cross-domain question we assert:
  (a) ledger-lock's home domain "finance_royalties" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — an advance-payment accounting question that contains no
keywords from publishing, legal, live_touring, data_analytics,
capital_funding, controller, label_ops, or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "ledger-lock"
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
        # finance_royalties: "royalt" (via "royalty")
        # publishing: "publish" (via "publishing"), "co-write", "catalog",
        #             "administration"
        "How do I calculate and pay quarterly taxes on my publishing royalty "
        "income from co-writes and catalog administration?",
        ["publishing"],
    ),
    (
        # finance_royalties: "royalt" (via "royalty")
        # legal: "contract", "rights"
        "The US label withheld 30% tax on our streaming royalty income — "
        "what contract rights do we have under the bilateral tax treaty and "
        "how do we recover the withheld amount?",
        ["legal"],
    ),
    (
        # finance_royalties: "accounting"
        # live_touring: "touring" (via "touring expenses"), "concert", "tour"
        "How do I track the accounting for touring expenses — per diems, "
        "hotel costs, and travel — and what are the tax deduction rules for "
        "a multi-city concert tour?",
        ["live_touring"],
    ),
    (
        # finance_royalties: "royalt" (via "royalty")
        # data_analytics: "forecast"
        "Can you help me forecast my annual royalty income from streaming "
        "to plan my quarterly estimated tax payments and avoid underpayment "
        "penalties?",
        ["data_analytics"],
    ),
    (
        # finance_royalties: "royalt" (via "royalty"), "advance"
        # capital_funding: "grant"
        "We received a government music grant and need to understand the "
        "tax implications — how do we properly account for this income "
        "alongside our ongoing royalty advances?",
        ["capital_funding"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped advance-payment accounting question that returns ONLY
# "finance_royalties". Keywords triggered: "accounting", "advance",
# "royalt" (via "royalty").
# Deliberately avoids: "publish" / "catalog" / "co-write" (publishing),
# "contract" / "rights" (legal), "tour" / "concert" (live_touring),
# "forecast" / "metric" (data_analytics), "grant" / "fund" (capital_funding),
# "bookkeep" / "reconcil" / "ledger" (controller), "distribution" (label_ops).

_NARROW_QUERY = (
    "What is the accounting treatment for advance payments received from "
    "our record label against future royalty earnings?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "publishing-royalty-income-tax-quarterly-co-write-catalog",
        "international-withholding-tax-streaming-royalties-contract-rights",
        "touring-expenses-accounting-concert-tax-deduction",
        "royalty-income-forecast-streaming-tax-planning",
        "music-grant-income-tax-royalty-advances-capital-funding",
    ],
)
def test_ledger_lock_consult_home_leads_and_cross_domains_present(query, cross):
    """
    ledger-lock's home domain 'finance_royalties' is always first; every
    expected cross-domain is present. Verifies home-first invariant and
    accounting/tax-specific cross-domain routing quality.
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


def test_ledger_lock_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped advance-payment accounting question (only
    'accounting', 'advance', and 'royalt' trigger — all finance_royalties)
    must return only the home domain with no spurious cross-domain routing
    from publishing/legal/live_touring/data_analytics/capital_funding terms.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
