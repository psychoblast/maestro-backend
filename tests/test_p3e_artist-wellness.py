"""
Phase 3e — Per-agent deep consult test for artist-wellness.

Scope: artist-wellness only. Home domain "management". Six realistic
questions an artist or their team would bring to Maya (Wellness Advisor),
covering: burnout and career momentum on a demanding touring schedule,
negotiating mental health protections into a management agreement, parasocial
fan dynamics straining an artist's mental health, financial anxiety about
funding and capital, structuring a career architecture around wellbeing and
strategic opportunity triage, and a deliberately narrow self-care / creative
exhaustion question.

For each cross-domain question we assert:
  (a) artist-wellness's home domain "management" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure self-care / emotional-boundaries / creative-exhaustion
question that avoids keywords from live_touring, legal, fan_social,
capital_funding, executive, publishing, finance_royalties, production,
marketing, bizdev, data_analytics, digital_ops, intelligence, label_ops,
ar, sync, controller, or playlist_dsp.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "artist-wellness"
_HOME  = "management"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "management" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.
# NOTE: "upcoming" contains "upc" → digital_ops — use "next" instead.
# NOTE: "engagement" → marketing — use "interaction" for fan queries.
# NOTE: "financial" contains "financ" → capital_funding — exclude from
#       non-finance queries.

DEEP_CONSULT_MATRIX = [
    (
        # management:   home — always leads ("career momentum")
        # live_touring: "touring" (via "touring schedule"), "tour"
        #               (via "touring artist")
        "Our artist is experiencing severe burnout and creative exhaustion on a "
        "demanding touring schedule — how do we support their mental health, protect "
        "career momentum on the road, and build sustainable routines for a touring artist?",
        ["live_touring"],
    ),
    (
        # management: home — always leads ("management agreement",
        #             "artist representation", "management deal")
        # legal:      "negotiat" (via "negotiate"), "contract" (via "contract"),
        #             "clause" (via "clauses"), "rights" (via "right"),
        #             "breach" (via "breaching")
        "We need to negotiate a management agreement that includes mental health "
        "protections — what artist representation terms and contract clauses protect "
        "the artist's right to step back without breaching their management deal?",
        ["legal"],
    ),
    (
        # management: home — always leads ("career-phase")
        # fan_social: "parasocial", "fan community",
        #             "fan relationship" (via "fan relationships")
        "Our artist is struggling with parasocial fan dynamics and the mental health "
        "strain of constant fan community interaction — what career-phase boundaries "
        "should the artist set to protect their wellbeing without harming fan relationships?",
        ["fan_social"],
    ),
    (
        # management:      home — always leads ("career trajectory")
        # capital_funding: "fund" (via "funding"), "capital",
        #                  "financ" (via "financial")
        "Our artist is experiencing severe anxiety about their funding runway and capital "
        "situation — how do we support their career trajectory and mental wellness while "
        "they navigate the financial pressure of building a sustainable music career?",
        ["capital_funding"],
    ),
    (
        # management: home — always leads ("career architecture",
        #             "opportunity triage", "offer evaluation")
        # executive:  "prioritize" (via "prioritizes"),
        #             "strategic direction"
        "How do we build a career architecture that prioritizes artist wellbeing, sets "
        "clear boundaries around opportunity triage and offer evaluation, and ensures the "
        "artist can sustain their energy without burnout affecting the strategic direction "
        "of their team?",
        ["executive"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped self-care / creative-exhaustion / emotional-boundaries
# question that returns ONLY "management" (via home domain). Deliberately avoids:
# "tour" / "touring" / "concert" / "stage" (live_touring)
# "contract" / "clause" / "rights" / "negotiat" / "breach" / "legal" (legal)
# "parasocial" / "fan community" / "fan relationship" / "superfan" (fan_social)
# "capital" / "fund" / "financ" / "invest" (capital_funding)
# "executive" / "strategic" / "prioritize" (executive)
# "publish" / "catalog" / "composition" / "songwrit" (publishing)
# "royalt" / "mechanical" / "splits" / "advance" (finance_royalties)
# "production" / "producer" / "mixing" / "mastering" / "studio" (production)
# "marketing" / "campaign" / "social media" / "audience" / "growth" (marketing)
# "brand" / "merch" / "merchandise" / "sponsor" (bizdev)
# "analytics" / "metric" / "kpi" (data_analytics)
# "upc" / "upcoming" / "isrc" / "metadata" (digital_ops)
# "early warning" / "early-warning" / "market trend" / "intelligence" (intelligence)
# "release" / "distributor" / "delivery" (label_ops)
# "a&r" / "scouting" / "talent scout" / "unsigned" (ar)
# "sync" / "licens" / "film" / "tv" / "placement" (sync)
# "controller" / "ledger" / "reconcil" (controller)
# "playlist" / "dsp" / "editorial" (playlist_dsp)
# "engagement" → marketing, excluded
# "boundaries" — excluded; contains "nda" substring → triggers legal
# "nda" → legal, excluded

_NARROW_QUERY = (
    "How do we help an artist build daily self-care routines, recognize the onset of "
    "creative exhaustion before it becomes debilitating, and establish healthy personal "
    "limits to sustain their wellbeing throughout a long career without compromising "
    "their core artistic identity?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "touring-schedule-burnout-career-momentum-live-touring",
        "management-agreement-negotiate-contract-clause-legal",
        "parasocial-fan-community-career-phase-fan-social",
        "funding-capital-financial-pressure-career-trajectory-capital-funding",
        "career-architecture-opportunity-triage-strategic-direction-executive",
    ],
)
def test_artist_wellness_consult_home_leads_and_cross_domains_present(query, cross):
    """
    artist-wellness's home domain 'management' is always first; every expected
    cross-domain is present. Verifies home-first invariant and wellness advisor
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


def test_artist_wellness_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped self-care / creative-exhaustion / emotional-boundaries
    question (no keywords from live_touring / legal / fan_social /
    capital_funding / executive / publishing / finance_royalties / production /
    marketing / bizdev / data_analytics / digital_ops / intelligence /
    label_ops / ar / sync / controller / playlist_dsp) must return only the
    home domain with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
