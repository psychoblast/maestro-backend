"""
Phase 3e — Per-agent deep consult test for storefront.

Scope: storefront only. Home domain "bizdev". Six realistic questions an
artist or their team would ask Store (Fan Store Specialist), covering: fan
store platform service contract review including clauses and indemnity, fan
store revenue accounting and income splits on merchandise and digital download
sales, a fan store launch marketing campaign across social media, superfan
direct-to-fan membership programs with fan community tiers, fan store sales
analytics and KPI tracking, and a deliberately narrow Shopify product
configuration question that stays home-only.

For each cross-domain question we assert:
  (a) storefront's home domain "bizdev" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped Shopify store product listing / automated
delivery / pricing formula question that avoids keywords from legal,
finance_royalties, marketing, fan_social, live_touring, publishing,
production, data_analytics, capital_funding, digital_ops, intelligence,
management, ar, sync, controller, executive, playlist_dsp, or label_ops.

Routing gap noted: storefront shares the "bizdev" home domain with
brand-connect and merch-empire. All three agents map to "bizdev" — there is
no storefront-specific sub-domain. The current mapping is CORRECT given that
storefront's core knowledge (fan store setup, digital product sales, D2C
revenue hub) maps cleanly under the bizdev domain. This test encodes the
CURRENT correct behavior without changing agent_home.py or shared files.

NOTE: "direct-to-fan" and "d2c" are fan_social keywords, NOT bizdev keywords.
Queries using these phrases will cross-route to fan_social — intentional and
sensible for a storefront D2C conversation. Avoided in Q1 (legal-only scenario)
to prevent unintended fan_social firing.
NOTE: "merchandise" contains "merch" as a substring → fires bizdev via the
"merch" keyword. "merchandise" is also an explicit bizdev keyword — both paths
converge on home in any query containing it.
NOTE: "subscription tier" and "membership tier" are fan_social keywords.
Using "subscriptions" or "memberships" alone (without "tier") does NOT trigger
fan_social — the check is full-phrase substring match.
NOTE: avoid "recoup" in finance_royalties scenarios — also fires label_ops
keywords (recoupment, recoupable). Use "accounting", "income split",
"statement", "royalt", "splits" instead for clean single-domain targeting.
NOTE: avoid "tour revenue" — fires live_touring via "tour" substring.
NOTE: "patreon" (lowercase match via brain's q.lower()) fires fan_social —
"Patreon-style" in query lowercases to "patreon-style", and "patreon" is a
substring of it. Included in Q4 where fan_social is the intended cross-domain.
NOTE: "stems" is a production keyword — excluded from narrow query.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "storefront"
_HOME  = "bizdev"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "bizdev" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # bizdev:   home — agent mapping (no explicit bizdev keyword in query;
        #           home_domain forces bizdev first)
        # legal:    "negotiat" (→ "negotiating"), "contract" (→ "service contract"),
        #           "clause" (→ "clauses"), "rights" (→ "intellectual property rights"),
        #           "indemnit" (→ "indemnity"), "warrant" (→ "warranty terms")
        # NOTE: "direct-to-fan" avoided here — it is a fan_social keyword and
        #       would fire fan_social unintentionally. Using "fan store" instead.
        "We're setting up our fan store and need help negotiating the platform "
        "service contract — reviewing the payment processor clauses, "
        "intellectual property rights, indemnity provisions, and warranty "
        "terms before we sign up.",
        ["legal"],
    ),
    (
        # bizdev:            home — "merchandise" (→ "merch" + "merchandise" keywords)
        # finance_royalties: "accounting", "income split" (→ "income splits"),
        #                    "splits", "statement" (→ "statements"),
        #                    "royalt" (→ "royalty")
        # NOTE: avoid "recoup" — also fires label_ops.
        # NOTE: avoid "tour revenue" — fires live_touring via "tour" substring.
        # NOTE: "subscriptions" alone does NOT fire fan_social ("subscription tier"
        #       is the fan_social keyword, not "subscriptions" by itself).
        "How do we handle the revenue accounting and income splits from our "
        "merchandise store between the artist and management — reviewing "
        "monthly statements of digital download sales and understanding "
        "royalty payments from our fan store subscriptions?",
        ["finance_royalties"],
    ),
    (
        # bizdev:    home — agent mapping
        # marketing: "marketing" (→ "marketing campaign"), "campaign",
        #            "social media", "fanbase", "audience", "rollout"
        # NOTE: "fanbase" is a marketing keyword. "fanbase health" is a fan_social
        #       keyword but "fanbase" alone does NOT appear in fan_social keywords.
        "We're launching our fan store and want to plan a marketing campaign "
        "across social media to grow our fanbase, build audience awareness "
        "for our digital product offerings, and create a rollout strategy "
        "for the store announcement.",
        ["marketing"],
    ),
    (
        # bizdev:     home — agent mapping
        # fan_social: "superfan", "direct-to-fan", "fan loyalty",
        #             "patreon" (→ "Patreon-style" lowercased),
        #             "fan community"
        # NOTE: "direct-to-fan" is a fan_social keyword — its presence here
        #       intentionally pulls in fan_social, which is correct when Store
        #       is advising on a D2C membership program.
        "How do we build a tiered superfan membership program through our "
        "direct-to-fan store — offering exclusive access levels, fan loyalty "
        "rewards, Patreon-style perks, and building a fan community around "
        "our digital content?",
        ["fan_social"],
    ),
    (
        # bizdev:        home — "brand" (→ "brand's") fires bizdev via keyword,
        #                deduplicates with home
        # data_analytics: "analytics", "metric" (→ "metrics"),
        #                 "kpi", "forecast" (→ "forecasting")
        # NOTE: "performance" alone does NOT trigger finance_royalties
        #       ("performance royalt" is the keyword) or publishing
        #       ("performance rights" is the keyword). "direct sales performance"
        #       is safe.
        "What analytics and sales metrics should we track for our brand's "
        "fan store — including kpi targets for digital product purchases, "
        "forecasting store revenue, and using the data to optimize our "
        "direct sales performance?",
        ["data_analytics"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped Shopify product configuration / automated delivery /
# pricing formula question that returns ONLY "bizdev" (via home domain +
# "merch"/"merchandise" keyword matches on "band merchandise bundles").
# Deliberately avoids:
# "contract"/"clause"/"rights"/"legal"/"negotiat"/"indemnit"/"warrant" (legal)
# "royalt"/"splits"/"split "/"recoup"/"advance"/"statement"/"accounting"/
#   "tour revenue"/"income split" (finance_royalties)
# "marketing"/"campaign"/"audience"/"fanbase"/"social media"/"engagement"/
#   "follower"/"reach"/"rollout"/"release strategy"/"growth" (marketing)
# "superfan"/"fan community"/"fan loyalty"/"meet and greet"/"membership tier"/
#   "patreon"/"direct-to-fan"/"d2c"/"fan engagement" (fan_social)
# "tour"/"touring"/"venue"/"concert"/"gig"/"booking"/"ticket"/"box office" (live_touring)
# "publish"/"catalog"/"songwrit"/"composition"/"administration" (publishing)
# "production"/"producer"/"studio"/"mixing"/"mastering"/"stems" (production)
# "analytics"/"metric"/"kpi"/"benchmark"/"forecast"/"streaming data" (data_analytics)
# "capital"/"fund"/"financ"/"invest"/"grant"/"equity" (capital_funding)
# "metadata"/"isrc"/"upc"/"ddex"/"dsp delivery"/"distributor" (digital_ops)
#   NOTE: "upcoming" contains "upc" substring → digital_ops — excluded.
#   NOTE: "audio file delivery" is digital_ops — "file delivery" alone is safe
#         because the keyword check is full-phrase ("audio file delivery" in query).
# "intelligence"/"market trend"/"industry trend" (intelligence)
# "artist manager"/"artist management"/"manage the artist" (management)
# "scouting"/"unsigned"/"a&r"/"emerging artist" (ar)
# "sync"/"licens"/"placement"/"film"/"tv" (sync)
# "reconcil"/"ledger"/"controller"/"close the books" (controller)
# "executive"/"ceo"/"go/no-go"/"build vs buy" (executive)
# "playlist"/"dsp"/"editorial"/"airplay" (playlist_dsp)
# "release planning"/"release campaign"/"delivery commitment" (label_ops)
#
# "merchandise" in "band merchandise bundles" → fires bizdev (home dedup). ✓

_NARROW_QUERY = (
    "How do we configure our Shopify storefront to sell digital album "
    "downloads, exclusive artist prints, and band merchandise bundles — "
    "covering product types, automated file delivery after purchase, "
    "and setting the right pricing formula for each item?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "fan-store-platform-service-contract-clauses-indemnity-warranty-rights-negotiating-legal",
        "merchandise-store-revenue-accounting-income-splits-statements-royalty-finance-royalties",
        "fan-store-launch-marketing-campaign-social-media-fanbase-audience-rollout-marketing",
        "superfan-membership-direct-to-fan-fan-loyalty-patreon-fan-community-fan-social",
        "fan-store-brand-analytics-metrics-kpi-forecasting-data-analytics",
    ],
)
def test_storefront_consult_home_leads_and_cross_domains_present(query, cross):
    """
    storefront's home domain 'bizdev' is always first; every expected
    cross-domain is present. Verifies home-first invariant and fan store
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


def test_storefront_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped Shopify product configuration / automated file delivery /
    pricing formula question (no keywords from legal / finance_royalties /
    marketing / fan_social / live_touring / publishing / production /
    data_analytics / capital_funding / digital_ops / intelligence / management /
    ar / sync / controller / executive / playlist_dsp / label_ops) must return
    only the home domain with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
