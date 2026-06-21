"""
Phase 3e — Per-agent deep consult test for sync-agent.

Scope: sync-agent only. Home domain "sync". Six realistic questions an artist
or their team would ask Riley, the Sync Licensing agent, covering placement
pitching, contract negotiation, publishing admin, royalty splits, marketing
amplification, and stems/delivery preparation.

For each cross-domain question we assert:
  (a) sync-agent's home domain "sync" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "sync-agent"
_HOME  = "sync"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "sync" leads; every expected cross-domain is present in domains.

DEEP_CONSULT_MATRIX = [
    (
        # sync: sync, licens, television, master use
        # legal: contract, clause, negotiat, indemnit, warrant
        "We received a sync licensing offer for a television drama and need to "
        "review the master use contract clauses and negotiate the indemnity and "
        "warranty terms before we sign",
        ["legal"],
    ),
    (
        # sync: sync, licens, synchronization
        # publishing: songwrit, catalog, publish, administration, sync admin
        "We want to pitch our songwriting catalog for synchronization licensing "
        "and need to set up a publishing administration deal to collect sync "
        "admin income properly",
        ["publishing"],
    ),
    (
        # sync: sync, placement, film, master use, sync deal
        # finance_royalties: royalt, splits
        "We landed a sync placement for a film and need to understand the master "
        "use fee structure and royalty splits on this sync deal",
        ["finance_royalties"],
    ),
    (
        # sync: sync, placement, television, advert (substring of advertisement)
        # marketing: marketing, campaign, social media, rollout
        "We confirmed a television advertisement sync placement and want to build "
        "a marketing campaign and social media rollout to amplify our exposure",
        ["marketing"],
    ),
    (
        # sync: sync, placement, trailer
        # production: stems, mixing, mastering
        "We have a trailer sync placement and need to prepare stems for delivery "
        "and ensure our mixing and mastering quality meets the sync brief "
        "requirements",
        ["production"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped sync question that returns ONLY "sync".
# Keywords triggered: music supervisor, needle drop, placement, film.
# No catalog/publishing terms, no royalty/finance terms — sync domain only.

_NARROW_QUERY = (
    "How do we approach a music supervisor to pitch a needle drop placement "
    "for a film soundtrack?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "tv-drama-contract-legal-review",
        "songwriting-catalog-sync-admin-publishing",
        "film-placement-master-use-royalty-splits",
        "advertisement-sync-marketing-campaign",
        "trailer-stems-mixing-mastering-production",
    ],
)
def test_sync_agent_consult_home_leads_and_cross_domains_present(query, cross):
    """
    sync-agent's home domain 'sync' is always first; every expected cross-domain
    is present. Verifies home-first invariant and sync-licensing-specific
    cross-domain routing quality.
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


def test_sync_agent_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped sync pitch question (music supervisor, needle drop, film)
    must return only the home domain 'sync' — no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
