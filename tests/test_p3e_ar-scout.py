"""
Phase 3e — Per-agent deep consult test for ar-scout.

Scope: ar-scout only. Home domain "ar". Six realistic questions an artist or
their team would ask the A&R Scout agent, covering the agent's core scouting
and development brief.

For each cross-domain question we assert:
  (a) ar-scout's home domain "ar" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "ar-scout"
_HOME  = "ar"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "ar" leads; every expected cross-domain is present in domains.

DEEP_CONSULT_MATRIX = [
    (
        # ar: scouting, unsigned, emerging artist
        # sync: sync, placement, film, tv
        "We are scouting an unsigned emerging artist who has secured sync "
        "placements in film and TV - should we sign them?",
        ["sync"],
    ),
    (
        # ar: new signing
        # legal: contract, indemnit, liabilit, clause, legal
        "We have a candidate for a new signing but the recording contract "
        "indemnity and liability clauses need careful legal review before we commit",
        ["legal"],
    ),
    (
        # ar: a&r, roster, unsigned
        # data_analytics: analytics, dsp metric
        "We are building our A&R roster and need streaming analytics and DSP "
        "metrics to evaluate which unsigned artists we should sign",
        ["data_analytics"],
    ),
    (
        # ar: up-and-coming
        # publishing: songwrit (from songwriter), catalog, co-write, publishing admin
        "We found an up-and-coming songwriter with strong catalog and want to "
        "structure a co-write and publishing administration deal",
        ["publishing"],
    ),
    (
        # ar: emerging artist, scouting, roster
        # sync: sync, placement
        # live_touring: touring
        "We are evaluating an emerging artist with a strong touring schedule "
        "and existing sync placements - should we add them to our scouting roster?",
        ["sync", "live_touring"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped A&R question returning ONLY the home domain "ar".
# Triggered by: prospect, discovery.
# "submission" is intentionally avoided — "bmi" is a substring of "submission"
# and would spuriously fire the finance_royalties domain.

_NARROW_QUERY = (
    "What criteria do you use to assess a new talent prospect on initial discovery?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "scouting-unsigned-artist-sync-film-tv",
        "new-signing-contract-legal-review",
        "ar-roster-streaming-analytics-dsp",
        "up-and-coming-songwriter-publishing-deal",
        "emerging-artist-touring-sync-multi-domain",
    ],
)
def test_ar_scout_consult_home_leads_and_cross_domains_present(query, cross):
    """
    ar-scout's home domain 'ar' is always first; every expected cross-domain
    is present. Verifies home-first invariant and A&R-specific cross-domain
    routing quality.
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


def test_ar_scout_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped A&R question (demo submission, talent prospect) must return
    only the home domain 'ar' — no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
