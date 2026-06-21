"""
Phase 3e — Per-agent deep consult test for producer-connect.

Scope: producer-connect only. Home domain "production". Six realistic questions
an artist or their team would ask producer-connect, covering producer deal
recoupment, work-for-hire session contracts, sync pitching from the studio,
co-write publishing setup, and a multi-domain producer contract negotiation,
plus a deliberately narrow home-only mastering/technical scenario.

For each cross-domain question we assert:
  (a) producer-connect's home domain "production" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "producer-connect"
_HOME  = "production"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "production" leads; every expected cross-domain is in domains.

DEEP_CONSULT_MATRIX = [
    (
        # production: producer (home)
        # finance_royalties: royalt, advance, recoup, points, splits, accounting, statement
        "We signed a producer deal and need to map out the advance recoupment "
        "schedule — how do we track the producer royalty points and splits in "
        "our accounting statement?",
        ["finance_royalties"],
    ),
    (
        # production: studio, recording session, arrangement
        # legal: work for hire, contract, rights, legal, clause
        "We need to hire a studio and lock in a recording session with a "
        "work-for-hire contract that protects our master rights and covers "
        "the legal clauses around the arrangement",
        ["legal"],
    ),
    (
        # production: studio, mixing, producer
        # sync: sync, placement, music supervisor, licens
        "We completed a studio mixing session and the producer wants to pitch "
        "the track for sync placement — how do we approach the music supervisor "
        "and navigate the sync licensing process?",
        ["sync"],
    ),
    (
        # production: recording session, studio, arrangement
        # publishing: co-write, songwrit, split sheet, publishing admin
        "We have a recording session for a co-write and need to document the "
        "songwriting split sheet and set up the publishing administration "
        "before we finalize the studio arrangement",
        ["publishing"],
    ),
    (
        # production: producer (home)
        # legal: negotiat, contract, clause
        # finance_royalties: royalt, advance, points, recoup, accounting
        "We are negotiating a producer contract and need to review the royalty "
        "advance clause and understand how the points and recoupment schedule "
        "affect our accounting",
        ["legal", "finance_royalties"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped mastering-targets question returning ONLY "production".
# Keywords triggered: loudness, lufs, true peak, mastering, stems, studio.
# No legal/finance/sync/publishing/bizdev/touring terms — production only.

_NARROW_QUERY = (
    "What loudness targets in LUFS and true peak ceiling should we aim for "
    "when mastering the final stems in the studio?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "producer-advance-recoupment-royalties-finance",
        "studio-recording-work-for-hire-contract-legal",
        "studio-mixing-sync-placement-supervisor",
        "recording-co-write-publishing-split-sheet",
        "producer-contract-negotiation-royalty-points-multi-domain",
    ],
)
def test_producer_connect_consult_home_leads_and_cross_domains_present(query, cross):
    """
    producer-connect's home domain 'production' is always first; every expected
    cross-domain is present. Verifies home-first invariant and
    production-specific cross-domain routing quality.
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


def test_producer_connect_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped loudness/mastering question (loudness, lufs, true peak,
    mastering, stems, studio) must return only the home domain 'production' —
    no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
