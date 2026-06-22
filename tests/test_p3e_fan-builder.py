"""
Phase 3e — Per-agent deep consult test for fan-builder.

Scope: fan-builder only. Home domain "fan_social". Five realistic
questions an artist would ask Aria (Fan Engagement Specialist), covering:
email list growth via marketing campaign, superfan VIP meet-and-greet at
touring shows, fan data analytics and community health metrics, superfan
merchandise bundles with ambassador program, and a pre-save activation
that captures email and Discord sign-ups. Plus a deliberately narrow
question that should return home-only with no spurious cross-domain.

For each cross-domain question we assert:
  (a) fan-builder's home domain "fan_social" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure community-platform / superfan-tier question that
avoids keywords from marketing, live_touring, data_analytics, bizdev,
label_ops, playlist_dsp, legal, finance_royalties, publishing,
production, capital_funding, or any other non-home domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "fan-builder"
_HOME  = "fan_social"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "fan_social" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.
# NOTE: "evangelist" contains "angel" → capital_funding — use other fan archetypes.
# NOTE: "engagement" / "audience" / "fanbase" → marketing — avoid in data-only queries.
# NOTE: "upcoming" contains "upc" → digital_ops — use "next" instead.

DEEP_CONSULT_MATRIX = [
    (
        # fan_social:  home — always leads ("email list", "superfan", "casual listener")
        # marketing:   "marketing" (x2), "campaign", "email marketing"
        "We want to grow our fan email list and design a marketing campaign "
        "to convert casual listeners into superfans — what is the best email "
        "marketing approach?",
        ["marketing"],
    ),
    (
        # fan_social:  home — always leads ("meet and greet", "superfan")
        # live_touring: "ticket" (via "ticket bundles"), "tour", "festival"
        # NOTE: avoids "upcoming" (triggers digital_ops "upc")
        "We want to offer superfan meet and greet experiences and exclusive "
        "ticket bundles for fans attending our next tour dates and festival shows",
        ["live_touring"],
    ),
    (
        # fan_social:  home — always leads ("superfan", "superfan conversion",
        #              "fan community", "community health", "fan data")
        # data_analytics: "analytics" (via "fan data analytics"), "fan insight"
        #                 (via "fan insights"), "metric" (via "metrics")
        # NOTE: avoids "engagement" (marketing kw), "audience" (marketing kw),
        #       "fanbase" (marketing kw)
        "How do we measure superfan conversion rates, track fan community "
        "health metrics, and segment our highest-value fans using fan data "
        "analytics and fan insights?",
        ["data_analytics"],
    ),
    (
        # fan_social:  home — always leads ("superfan", "ambassador program",
        #              "ambassador tier" via "ambassador tiers")
        # bizdev:      "ambassador" (substring of "ambassador program"),
        #              "merchandise" (via "merchandise bundles"), "merch"
        "We want to create superfan merchandise bundles and an ambassador "
        "program for our most dedicated community members — how do we "
        "structure the merch offering and ambassador tiers?",
        ["bizdev"],
    ),
    (
        # fan_social:  home — always leads ("email list", "discord")
        # label_ops:   "pre-save" (standalone keyword)
        # playlist_dsp: "pre-save" (also a playlist_dsp keyword)
        "We want to build a pre-save landing page that collects email list "
        "sign-ups and converts fans into discord community members ahead of "
        "our next release",
        ["label_ops", "playlist_dsp"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped community-platform / membership tier question that returns
# ONLY "fan_social" (via home domain). Deliberately avoids:
# "marketing" / "campaign" / "audience" / "fanbase" / "engagement" (marketing)
# "tour" / "concert" / "venue" / "ticket" / "festival" / "stage" (live_touring)
# "analytics" / "metric" / "kpi" / "audience data" / "fan insight" (data_analytics)
# "merch" / "merchandise" / "ambassador" / "brand" / "sponsor" (bizdev)
# "pre-save" / "presave" / "release plan" / "editorial" (label_ops / playlist_dsp)
# "contract" / "rights" / "legal" (legal)
# "royalt" / "mechanical" / "master" (finance_royalties)
# "publish" / "catalog" / "administration" (publishing)
# "production" / "studio" / "mixing" (production)
# "capital" / "fund" / "financ" / "angel" (capital_funding)
# "upcoming" — triggers digital_ops via "upc" substring — excluded here
# "intelligence" / "market trend" (intelligence)

_NARROW_QUERY = (
    "How do we structure our Discord community channels and set up Patreon "
    "membership tiers for our superfan subscribers?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "email-list-marketing-campaign-casual-listeners-to-superfans",
        "meet-and-greet-ticket-bundles-tour-festival-superfan-vip",
        "fan-data-analytics-conversion-metrics-community-health-segmentation",
        "superfan-merchandise-bundles-ambassador-program-bizdev",
        "pre-save-email-list-discord-community-label-ops-playlist-dsp",
    ],
)
def test_fan_builder_consult_home_leads_and_cross_domains_present(query, cross):
    """
    fan-builder's home domain 'fan_social' is always first; every expected
    cross-domain is present. Verifies home-first invariant and fan engagement
    specialist cross-domain routing quality.
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


def test_fan_builder_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped Discord/Patreon/superfan-tier question (no keywords from
    marketing / live_touring / data_analytics / bizdev / label_ops /
    playlist_dsp / legal / finance_royalties / publishing / production /
    capital_funding / digital_ops / intelligence) must return only the home
    domain with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
