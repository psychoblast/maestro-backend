"""
Phase 3e — Per-agent deep consult test for rights-pulse.

Scope: rights-pulse only. Home domain "publishing". Six realistic
questions an artist or their team would ask Ray (Performance Rights
specialist), covering: PRO catalog registration and royalty collection,
publishing administration contract review, sync placement cue sheet
filing, live performance royalty collection, publishing deal negotiation
with royalty rights, and a deliberately narrow composition registration
question.

For each cross-domain question we assert:
  (a) rights-pulse's home domain "publishing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a songwriter composition registration question that
contains no keywords from finance_royalties, legal, sync, live_touring,
data_analytics, capital_funding, or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "rights-pulse"
_HOME  = "publishing"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "publishing" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # publishing:        "catalog" (home)
        # finance_royalties: "ascap", "royalt" (via "royalties")
        "How do we register our song catalog with ASCAP and set up "
        "collection for our performance royalties from radio and "
        "digital streaming?",
        ["finance_royalties"],
    ),
    (
        # publishing:        "publish" (via "publishing"), "administration"
        # legal:             "rights" (via "performance rights"), "contract"
        "We are reviewing a publishing administration agreement that assigns "
        "performance rights to our PRO — what contract provisions should we "
        "push back on?",
        ["legal"],
    ),
    (
        # publishing:        "composition"
        # sync:              "film", "sync", "placement", "cue sheet"
        # finance_royalties: "royalt" (via "royalty")
        "We got a film sync placement for our composition — how do we handle "
        "PRO cue sheet filing and performance royalty collection?",
        ["sync", "finance_royalties"],
    ),
    (
        # publishing:        "composition" (via "compositions") — home ensures lead
        # finance_royalties: "royalt" (via "royalties")
        # live_touring:      "concert", "festival"
        "How are royalties collected by our PRO when our compositions are "
        "performed live at concerts and festivals?",
        ["finance_royalties", "live_touring"],
    ),
    (
        # publishing:        "publish" (via "publishing"), "administration", "catalog"
        # finance_royalties: "royalt" (via "royalty")
        # legal:             "negotiat", "rights" (via "ownership rights")
        "We want to negotiate a publishing administration deal covering "
        "performance royalty collection and catalog ownership rights — "
        "what are the key points?",
        ["finance_royalties", "legal"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped composition registration question that returns ONLY
# "publishing". Keywords triggered: "publish" (via "publisher"),
# "composition", "songwrit" (via "songwriter"), "administration",
# "catalog" — all map to publishing.
# Deliberately avoids: "royalt" / "ascap" / "bmi" (finance_royalties),
# "contract" / "rights" / "legal" (legal), "sync" / "licens" (sync),
# "tour" / "concert" (live_touring), "fund" / "capital" (capital_funding),
# "metric" / "analytic" (data_analytics), "label ops" (label_ops).

_NARROW_QUERY = (
    "What information does a publisher need to register a new composition "
    "and set up songwriter administration for an existing catalog?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "pro-catalog-registration-ascap-performance-royalties",
        "publishing-administration-agreement-performance-rights-contract",
        "film-sync-placement-cue-sheet-pro-royalty-collection",
        "live-performance-royalties-concerts-festivals",
        "publishing-admin-deal-royalty-rights-negotiation",
    ],
)
def test_rights_pulse_consult_home_leads_and_cross_domains_present(query, cross):
    """
    rights-pulse's home domain 'publishing' is always first; every
    expected cross-domain is present. Verifies home-first invariant and
    PRO/performance-rights-specific cross-domain routing quality.
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


def test_rights_pulse_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped composition registration question (only 'publish',
    'composition', 'songwrit', 'administration', and 'catalog' trigger —
    all publishing) must return only the home domain with no spurious
    cross-domain routing from finance_royalties/legal/sync/live_touring
    or any other domain.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
