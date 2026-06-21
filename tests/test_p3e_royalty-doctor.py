"""
Phase 3e — Per-agent deep consult test for royalty-doctor.

Scope: royalty-doctor only. Home domain "finance_royalties". Six realistic
questions an artist or their team would ask royalty-doctor, covering royalty
statement review, contract dispute, touring income splits, sync royalties,
producer advance recoupment, and a deliberately narrow home-only scenario.

For each cross-domain question we assert:
  (a) royalty-doctor's home domain "finance_royalties" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "royalty-doctor"
_HOME  = "finance_royalties"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "finance_royalties" leads; every expected cross-domain is present.

DEEP_CONSULT_MATRIX = [
    (
        # finance_royalties: royalt, statement, splits, accounting
        # publishing: publish, administration, writer share, catalog
        "We received our annual royalty statement showing publishing administration "
        "deductions and need to understand the writer share splits and catalog "
        "royalties through proper accounting",
        ["publishing"],
    ),
    (
        # finance_royalties: royalt, accounting, audit the label
        # legal: contract, rights, dispute, clause
        "Our royalty accounting reveals consistent underpayment — we want to "
        "audit the label and need to review the contract rights and the dispute "
        "resolution clause before we take action",
        ["legal"],
    ),
    (
        # finance_royalties: tour revenue, show income, income split
        # live_touring: tour, touring, festival
        "We need to reconcile our tour revenue and show income splits across all "
        "festival appearances this year against our projected touring income",
        ["live_touring"],
    ),
    (
        # finance_royalties: royalt, splits, ascap, performing rights org
        # sync: sync, placement, master use, licens
        "We secured a sync placement deal and need to understand the royalty splits "
        "on the master use licensing fees and collect the income through ASCAP as "
        "the performing rights org",
        ["sync"],
    ),
    (
        # finance_royalties: advance, recoup, points, royalt, accounting, statement
        # production: producer
        "We signed a producer deal and need to understand the advance recoupment "
        "schedule — how are the producer points and royalties tracked in our "
        "accounting statement?",
        ["production"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped royalty-rates question that returns ONLY "finance_royalties".
# Keywords triggered: mechanical, royalt, accounting.
# No publishing/sync/legal/touring/production terms — finance_royalties only.

_NARROW_QUERY = (
    "What are the statutory mechanical royalty rates for streaming and how do "
    "we calculate the per-stream accounting?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "statement-publishing-admin-deductions",
        "underpayment-audit-label-contract-dispute",
        "tour-revenue-show-income-festival-splits",
        "sync-placement-royalty-splits-ascap",
        "producer-advance-recoupment-points",
    ],
)
def test_royalty_doctor_consult_home_leads_and_cross_domains_present(query, cross):
    """
    royalty-doctor's home domain 'finance_royalties' is always first; every
    expected cross-domain is present. Verifies home-first invariant and
    royalty-specific cross-domain routing quality.
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


def test_royalty_doctor_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped mechanical-rates question (mechanical, royalt, accounting)
    must return only the home domain 'finance_royalties' — no spurious
    cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
