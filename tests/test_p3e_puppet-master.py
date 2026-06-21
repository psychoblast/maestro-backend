"""
Phase 3e — Per-agent deep consult test for puppet-master.

Scope: puppet-master only. Home domain "executive". Six realistic questions
an artist or their team would ask their artist manager (Marcus), covering
strategic career decisions, deal analysis, team coordination, capital planning,
data-driven independence decisions, and a multi-domain acquisition scenario,
plus a deliberately narrow home-only prioritization question.

For each cross-domain question we assert:
  (a) puppet-master's home domain "executive" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "puppet-master"
_HOME  = "executive"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "executive" leads; every expected cross-domain is present.

DEEP_CONSULT_MATRIX = [
    (
        # executive: go/no-go, enterprise decision
        # legal: contract, clause, negotiat (→ "negotiate")
        "We need to run a go/no-go decision on whether to sign to a major label "
        "— what is the enterprise decision framework and which contract clauses "
        "should we negotiate before committing?",
        ["legal"],
    ),
    (
        # executive: go/no-go, enterprise decision
        # finance_royalties: advance, royalt (→ "royalty"), splits, accounting, statement
        "We are at a go/no-go decision point on the next career cycle — what is "
        "the enterprise decision framework for evaluating how the recording advance "
        "affects our royalty splits and accounting statements?",
        ["finance_royalties"],
    ),
    (
        # executive: strategic direction
        # management: artist manager, entertainment attorney, career phase,
        #             professional team, assemble the team
        "We need to assemble the artist's professional team and align on a "
        "strategic direction for the next career phase — what does the ideal team "
        "look like and how do we coordinate the artist manager, entertainment "
        "attorney, and business manager?",
        ["management"],
    ),
    (
        # executive: business case, go/no-go, bear case
        # data_analytics: streaming analysis, trajectory
        "We need to build a business case for a go/no-go decision on independence "
        "— can the streaming analysis and listener trajectory data support our "
        "bear case scenario?",
        ["data_analytics"],
    ),
    (
        # executive: go/no-go, catalog acquisition
        # legal: contract, clause, negotiat (→ "negotiate")
        # finance_royalties: royalt (→ "royalty"), advance, recoup, accounting, statement
        "We need to make a go/no-go decision on a catalog acquisition deal — "
        "what are the key contract clauses to negotiate and how do we model the "
        "royalty advance recoupment and accounting statements?",
        ["legal", "finance_royalties"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped executive prioritization question returning ONLY "executive".
# Keywords triggered: prioritization, competing priorities, kill-or-continue — all executive.
# Deliberately avoids legal, finance, management, marketing, or any other domain term.

_NARROW_QUERY = (
    "What is the right prioritization framework for managing competing priorities "
    "and making a kill-or-continue decision when resources are stretched?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "go-no-go-major-label-contract-clauses-legal",
        "go-no-go-recording-advance-royalty-splits-finance",
        "strategic-direction-team-assembly-artist-manager-management",
        "business-case-streaming-analysis-trajectory-data-analytics",
        "catalog-acquisition-contract-royalty-advance-legal-finance-multi",
    ],
)
def test_puppet_master_consult_home_leads_and_cross_domains_present(query, cross):
    """
    puppet-master's home domain 'executive' is always first; every expected
    cross-domain is present. Verifies home-first invariant and
    executive-specific cross-domain routing quality.
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


def test_puppet_master_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped prioritization/kill-decision question (prioritization,
    competing priorities, kill-or-continue) must return only the home domain
    'executive' — no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
