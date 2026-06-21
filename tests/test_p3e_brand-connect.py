"""
Phase 3e — Per-agent deep consult test for brand-connect.

Scope: brand-connect only. Home domain "bizdev". Six realistic questions an
artist or their team would ask Nia, the Brand Partnerships Specialist, covering
brand deal evaluation, sponsorship activation, ambassador campaigns, royalty
advance structures, and multi-domain concert tour sponsorship scenarios.

For each cross-domain question we assert:
  (a) brand-connect's home domain "bizdev" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "brand-connect"
_HOME  = "bizdev"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "bizdev" leads; every expected cross-domain is present in domains.

DEEP_CONSULT_MATRIX = [
    (
        # bizdev: brand, endorsement
        # legal: contract, clause, indemnit
        "We received a brand endorsement deal and need to review the contract "
        "clause by clause, particularly the indemnity provisions, before we proceed",
        ["legal"],
    ),
    (
        # bizdev: brand, sponsor, activation, brand tour
        # live_touring: touring (contains "tour"), festival
        "We have a brand sponsor offering a touring activation across the festival "
        "run — what should we evaluate before committing to the brand tour?",
        ["live_touring"],
    ),
    (
        # bizdev: brand, ambassador, partnership
        # marketing: campaign, social media, rollout
        "We are finalizing a brand ambassador deal and want to build a social "
        "media campaign and content rollout to maximize the partnership value",
        ["marketing"],
    ),
    (
        # bizdev: brand, partnership
        # finance_royalties: royalt (royalty), advance, income split, recoup
        "We are evaluating a brand partnership that includes a royalty advance "
        "and want to understand the income split and recoupment structure",
        ["finance_royalties"],
    ),
    (
        # bizdev: brand, sponsor, activation
        # live_touring: tour (multi-city tour), concert
        # legal: contract, indemnit (indemnity), clause (clauses)
        "We have a multi-city tour with a brand sponsor providing full activation "
        "and need to review the concert sponsorship contract indemnity clauses "
        "before we sign",
        ["live_touring", "legal"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped brand partnership question returning ONLY "bizdev".
# Triggered by: brand, sponsor, endorsement, partner (with trailing space).
# No contract/legal, no touring, no marketing campaign, no financial terms.

_NARROW_QUERY = (
    "How do we identify the right brand sponsor category and approach a potential "
    "endorsement partner for our artist?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "brand-endorsement-contract-clause-legal",
        "brand-sponsor-touring-activation-festival-live-touring",
        "brand-ambassador-social-campaign-rollout-marketing",
        "brand-partnership-royalty-advance-income-split-finance",
        "concert-tour-sponsor-activation-contract-indemnity-multi-domain",
    ],
)
def test_brand_connect_consult_home_leads_and_cross_domains_present(query, cross):
    """
    brand-connect's home domain 'bizdev' is always first; every expected
    cross-domain is present. Verifies home-first invariant and brand-partnership-
    specific cross-domain routing quality.
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


def test_brand_connect_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped brand sponsorship question (brand, sponsor, endorsement,
    partner) must return only the home domain 'bizdev' — no spurious cross-domain
    routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
