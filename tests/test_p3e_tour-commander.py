"""
Phase 3e — Per-agent deep consult test for tour-commander.

Scope: tour-commander only. Home domain "live_touring". Six realistic questions
an artist or their team would ask their touring specialist, covering the agent's
live-performance, routing, and show-logistics brief.

For each cross-domain question we assert:
  (a) tour-commander's home domain "live_touring" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "tour-commander"
_HOME  = "live_touring"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "live_touring" leads; every expected cross-domain is present.

DEEP_CONSULT_MATRIX = [
    (
        # live_touring: tour (in "tour revenue"), booking (in "booking agent")
        # finance_royalties: tour revenue, show income, income split (in "income splits")
        "How should we structure tour revenue sharing and show income splits "
        "between the artist, their team and booking agent for the upcoming run",
        ["finance_royalties"],
    ),
    (
        # live_touring: festival, performance fee, headliner, rider
        # legal: negotiat (in "negotiating"), contract, clause (in "clauses")
        "We are negotiating a festival contract that includes performance fee terms, "
        "headliner billing and rider clauses for the summer run",
        ["legal"],
    ),
    (
        # live_touring: tour (in "upcoming tour" and "touring partnership"), touring
        # bizdev: brand, sponsor, endorsement, touring partnership, activation
        "A major brand wants to sponsor our upcoming tour and we need to structure "
        "an endorsement deal and touring partnership activation with them",
        ["bizdev"],
    ),
    (
        # live_touring: concert, ticket (in "ticket sales")
        # marketing: social media, campaign, paid media, fan acquisition
        "We need a social media campaign and paid media strategy to drive fan "
        "acquisition and maximize ticket sales for our upcoming concert",
        ["marketing"],
    ),
    (
        # live_touring: live show (in "live shows"), tour (in "on tour")
        # fan_social: fan community, super-fan (in "super-fans"), fan loyalty,
        #             meet and greet
        "We want to mobilize our fan community and super-fans to attend live shows "
        "and reward fan loyalty through exclusive meet and greet experiences on tour",
        ["fan_social"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped show-logistics question returning ONLY the home domain.
# Keywords triggered: load-in, box office, support act, headliner, tour — all live_touring.
# Deliberately avoids:
#   - "standard" (contains substring "nda" → legal), "contract", "clause", "rider" (legal)
#   - "brand", "sponsor", "endorsement" (bizdev)
#   - "campaign", "social media" (marketing)
#   - "fan community", "super-fan", "meet and greet" (fan_social)
#   - "tour revenue", "show income", "income split" (finance_royalties)
#   - any other cross-domain trigger

_NARROW_QUERY = (
    "How do we handle load-in procedures and box office settlement "
    "for a support act on a 20-date headliner tour"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "tour-revenue-show-income-finance-split",
        "festival-contract-performance-fee-headliner-rider-legal",
        "brand-sponsor-endorsement-touring-partnership-bizdev",
        "social-media-campaign-ticket-sales-concert-marketing",
        "fan-community-super-fans-live-shows-fan-social",
    ],
)
def test_tour_commander_consult_home_leads_and_cross_domains_present(query, cross):
    """
    tour-commander's home domain 'live_touring' is always first; every expected
    cross-domain is present. Verifies home-first invariant and touring-specific
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


def test_tour_commander_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped stage-operations question (setup, setlist, support act)
    must return only the home domain 'live_touring' — no spurious cross-domain
    routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
