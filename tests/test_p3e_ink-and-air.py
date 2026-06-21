"""
Phase 3e — Per-agent deep consult test for ink-and-air.

Scope: ink-and-air only. Home domain "publishing". Five realistic cross-domain
questions an artist would ask their publishing and rights specialist, plus one
deliberately narrow question that must return home-only with no spurious
cross-domain routing.

For each cross-domain question we assert:
  (a) ink-and-air's home domain "publishing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One narrow question asserts home-only to verify the router does not over-fire.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "ink-and-air"
_HOME  = "publishing"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "publishing" leads; every expected cross-domain is present.

DEEP_CONSULT_MATRIX = [
    (
        # publishing: mechanical (in "mechanical royalties"), royalt, songwrit (in "songwriting"),
        #             catalog — all publishing keywords
        # finance_royalties: "mechanical" and "royalt" (in "royalties", twice)
        "My streaming mechanical royalties aren't matching my songwriting catalog "
        "— how do I recover unmatched royalties from the MLC black-box pool?",
        ["finance_royalties"],
    ),
    (
        # publishing: composition (in "compositions")
        # legal: work-for-hire, copyright, negotiat (in "negotiate")
        "I was asked to sign a work-for-hire agreement on my compositions "
        "— how does that affect my copyright ownership and what terms should I negotiate?",
        ["legal"],
    ),
    (
        # publishing: catalog, composition, publishing (in "publishing catalog")
        # sync: tv, sync (in "sync placement"), placement
        "We received a TV sync placement offer for our publishing catalog "
        "— how do we evaluate the composition fee and confirm all clearances are in place?",
        ["sync"],
    ),
    (
        # publishing: catalog, administration, publishing (in "publishing administration")
        # digital_ops: iswc, identifier (in "identifiers"), metadata, metadata completeness
        "We need to register ISWC identifiers and audit catalog metadata completeness "
        "for our publishing administration",
        ["digital_ops"],
    ),
    (
        # publishing: administration, songwrit (in "songwriter"), catalog, publishing
        # label_ops: controlled comp (substring of "controlled comp provisions"),
        #            label deal
        "How do controlled comp provisions in a label deal interact with our publishing "
        "administration and songwriter catalog ownership?",
        ["label_ops"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped publishing infrastructure question returning ONLY the home domain.
# Keywords triggered: co-write, songwrit (in "songwriter's"), composition — all publishing.
# Deliberately avoids:
#   - "royalt", "mechanical", "ascap", "bmi", "splits" (finance_royalties)
#   - "copyright", "contract", "clause", "rights", "legal" (legal)
#   - "sync", "licens", "placement", "tv" (sync)
#   - "iswc", "metadata", "identifier" (digital_ops)
#   - "label deal", "controlled comp", "recoup" (label_ops)
#   - any other cross-domain trigger

_NARROW_QUERY = (
    "I want to document each songwriter's co-write share "
    "and register the composition with our PRO before the song goes live"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "mechanical-royalties-mlc-black-box-finance",
        "work-for-hire-composition-copyright-legal",
        "tv-sync-placement-catalog-composition-sync",
        "iswc-identifier-metadata-publishing-digital-ops",
        "controlled-comp-label-deal-publishing-label-ops",
    ],
)
def test_ink_and_air_consult_home_leads_and_cross_domains_present(query, cross):
    """
    ink-and-air's home domain 'publishing' is always first; every expected
    cross-domain is present. Verifies home-first invariant and publishing-specific
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


def test_ink_and_air_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped publishing-infrastructure question (co-write splits,
    PRO registration) must return only the home domain 'publishing' — no
    spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
