"""
Phase 3e — Per-agent deep consult test for ai-navigator.

Scope: ai-navigator only. Home domain "executive". Six realistic questions
an artist or their team would ask their AI Tools specialist (Neo), covering
build-vs-buy decisions on AI platforms, AI-powered content automation,
AI stem/mixing tool adoption, AI music generation copyright risk, capital
allocation for an AI tech stack, and a deliberately narrow executive-only
prioritization scenario.

For each cross-domain question we assert:
  (a) ai-navigator's home domain "executive" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "ai-navigator"
_HOME  = "executive"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "executive" leads; every expected cross-domain is present.

DEEP_CONSULT_MATRIX = [
    (
        # executive: build vs buy, business case, go/no-go
        # data_analytics: analytics, streaming data, metric
        "We need to run a build vs buy decision on an AI analytics platform "
        "— what is the business case framework and which streaming data metrics "
        "and analytics KPIs should drive the go/no-go verdict?",
        ["data_analytics"],
    ),
    (
        # executive: go/no-go, enterprise decision
        # marketing: content strategy, marketing, campaign, rollout
        "We want to make an enterprise decision on adopting AI tools to automate "
        "our content strategy — run a go/no-go on investing in an AI-powered "
        "marketing campaign rollout tool for the artist.",
        ["marketing"],
    ),
    (
        # executive: enterprise decision, business case
        # production: stems, mixing, studio, production
        "We need an enterprise decision on adopting AI stem separation and "
        "automated mixing tools — what are the production workflow trade-offs "
        "compared to traditional studio sessions and how do we size the business case?",
        ["production"],
    ),
    (
        # executive: business case, go/no-go
        # legal: copyright, legal, rights
        "We are building a business case for deploying an AI music generation "
        "tool — what copyright ownership and legal rights issues must we resolve "
        "before we commit to the go/no-go decision?",
        ["legal"],
    ),
    (
        # executive: capital allocation, build vs buy, invest
        # capital_funding: capital, invest, financ
        "We are making a capital allocation decision to invest in a build vs buy "
        "evaluation of our AI tech stack — how do we structure the capital raise "
        "and financial model for an independent artist operation?",
        ["capital_funding"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped executive prioritization question returning ONLY "executive".
# Keywords triggered: build vs buy, go/no-go, competing priorities, prioritiz —
# all executive. Deliberately avoids production, legal, marketing, finance,
# data_analytics, or any other domain term.

_NARROW_QUERY = (
    "What is the right build vs buy framework for evaluating AI tools and how "
    "do we apply a go/no-go decision to prioritize our tech roadmap when facing "
    "competing priorities across different enterprise use cases?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "build-vs-buy-ai-analytics-platform-data-analytics",
        "ai-content-automation-go-no-go-marketing-campaign",
        "ai-stem-mixing-tools-enterprise-decision-production",
        "ai-music-generation-copyright-legal-rights",
        "capital-allocation-ai-tech-stack-build-capital-funding",
    ],
)
def test_ai_navigator_consult_home_leads_and_cross_domains_present(query, cross):
    """
    ai-navigator's home domain 'executive' is always first; every expected
    cross-domain is present. Verifies home-first invariant and
    ai-navigator-specific cross-domain routing quality.
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


def test_ai_navigator_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped build-vs-buy / go/no-go / competing-priorities question
    must return only the home domain 'executive' — no spurious cross-domain
    routing into production, legal, marketing, or any other domain.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
