"""
Phase 3e — Per-agent deep consult test for merch-empire.

Scope: merch-empire only. Home domain "bizdev". Six realistic questions an
artist or their team would ask Max (Merchandise Specialist), covering: merch
deal contract negotiation with indemnity and warranty clauses, merchandise
revenue accounting and income splits including royalty statement and
recoupment tracking, merchandise launch marketing campaign across social media,
superfan bundles with membership tiers and meet-and-greet access, tour merch
strategy managing venue hall fees and concert inventory alongside ticketing,
and a deliberately narrow print-on-demand vs. bulk-manufacturing pricing
question that stays home-only.

For each cross-domain question we assert:
  (a) merch-empire's home domain "bizdev" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped print-on-demand vs. bulk-manufacturing /
pricing-formula / online-store-platform question that avoids keywords from
legal, finance_royalties, marketing, fan_social, live_touring, publishing,
production, data_analytics, capital_funding, digital_ops, intelligence,
management, ar, sync, controller, executive, playlist_dsp, or label_ops.

Routing gap noted: merch-empire shares the "bizdev" home domain with
brand-connect and storefront. All three agents map to "bizdev" — there is no
merch-specific sub-domain. The current mapping is CORRECT given that
merch-empire's core knowledge (merchandise production, pricing, fulfillment,
tour merch operations) is authored under the bizdev domain. This test encodes
the CURRENT correct behavior without changing agent_home.py or shared files.

NOTE: "merchandise" contains "merch" as a substring → fires bizdev via the
"merch" keyword (home domain). "merchandise" itself is also a full bizdev
keyword — both paths converge on home.
NOTE: "engagement" alone is a marketing keyword — any query containing
"fan engagement" will also fire marketing. Queries in this matrix that target
fan_social use keywords that avoid "engagement" (e.g. "superfan", "meet and
greet", "membership tier", "patreon", "fan loyalty", "fan community").
NOTE: "licensing" / "licens" fires sync — avoid in legal-only scenarios;
use "contract"/"clause"/"indemnit"/"warrant"/"rights" instead.
NOTE: "tour revenue" fires both finance_royalties and live_touring — excluded
from Q2 which targets finance_royalties only.
NOTE: "production" is a production-domain keyword — avoid in narrow query.
NOTE: "upcoming" contains "upc" (digital_ops keyword) — excluded from narrow.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "merch-empire"
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
        # bizdev:   home — "merchandise" (→ "merch" substring), "merch deal"
        # legal:    "negotiat" (→ "negotiate"), "contract", "clause" (→ "clauses"),
        #           "indemnit" (→ "indemnity"), "warrant" (→ "warranty"), "rights"
        "We want to establish a merchandise operation and need to negotiate "
        "the merch deal contract — reviewing the clauses, indemnity provisions, "
        "warranty terms, and protecting our rights before signing.",
        ["legal"],
    ),
    (
        # bizdev:            home — "merchandise" (→ "merch"), "merchandise"
        # finance_royalties: "accounting", "income split" (→ "income splits"),
        #                    "royalt" (→ "royalty"), "statement", "recoup" (→ "recoupment")
        # NOTE: avoid "tour revenue" — fires live_touring via "tour" substring.
        "How do we handle the merchandise revenue accounting and income splits "
        "between the artist and management, including royalty statement reviews "
        "and recoupment tracking for our merchandise operation?",
        ["finance_royalties"],
    ),
    (
        # bizdev:    home — "merchandise" (→ "merch"), "merchandise"
        # marketing: "marketing" (→ "marketing campaign"), "campaign", "social media",
        #            "fanbase", "audience", "rollout"
        "We're launching our merchandise line and want to run a marketing campaign "
        "across social media to grow our fanbase, drive audience awareness, and "
        "build a rollout strategy for the drop announcement.",
        ["marketing"],
    ),
    (
        # bizdev:    home — "merch" (in "merch line")
        # fan_social: "superfan", "membership tier", "meet and greet",
        #             "patreon", "fan loyalty", "fan community"
        # NOTE: "engagement" is a marketing keyword — avoided here.
        "We want to design exclusive superfan bundles with our merch line — "
        "offering membership tier rewards, meet and greet access, Patreon perks, "
        "and fan loyalty incentives that deepen the connection between our artist "
        "and the fan community.",
        ["fan_social"],
    ),
    (
        # bizdev:     home — "merchandise" (→ "merch"), "merchandise"
        # live_touring: "touring" (→ "touring run"), "venue", "concert",
        #               "ticketing", "box office"
        "How do we build a profitable merchandise strategy for our touring run — "
        "managing venue hall fees, coordinating per-city inventory at each concert "
        "stop, and maximizing revenue alongside our ticketing and box office results?",
        ["live_touring"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped print-on-demand vs. bulk-manufacturing / pricing-formula /
# online-store-platform question that returns ONLY "bizdev" (via home domain +
# "merch" / "merchandise" keyword matches).
# Deliberately avoids:
# "contract"/"clause"/"rights"/"legal"/"negotiat"/"indemnit"/"warrant" (legal)
# "royalt"/"splits"/"split "/"recoup"/"advance"/"statement"/"accounting"/
#   "tour revenue"/"income split" (finance_royalties)
# "marketing"/"campaign"/"audience"/"fanbase"/"social media"/"engagement"/
#   "follower"/"reach"/"rollout"/"release strategy"/"growth" (marketing)
# "superfan"/"fan community"/"fan loyalty"/"meet and greet"/"membership tier"/
#   "patreon"/"fan engagement"/"vip experience" (fan_social)
# "tour"/"touring"/"venue"/"concert"/"gig"/"booking"/"ticket"/"box office" (live_touring)
# "publish"/"catalog"/"songwrit"/"composition"/"administration" (publishing)
# "production"/"producer"/"studio"/"mixing"/"mastering" (production)
# "analytics"/"metric"/"kpi"/"benchmark"/"forecast"/"streaming" (data_analytics)
# "capital"/"fund"/"financ"/"invest"/"grant"/"equity" (capital_funding)
# "metadata"/"isrc"/"upc"/"distributor"/"dsp delivery" (digital_ops)
#   NOTE: "upcoming" contains "upc" substring → digital_ops — excluded.
# "intelligence"/"market trend"/"industry trend" (intelligence)
# "artist manager"/"artist management"/"manage the artist" (management)
# "scouting"/"unsigned"/"a&r"/"emerging artist" (ar)
# "sync"/"licens"/"placement"/"film"/"tv" (sync)
# "reconcil"/"ledger"/"controller"/"close the books" (controller)
# "executive"/"ceo"/"go/no-go"/"build vs buy" (executive)
# "playlist"/"dsp"/"editorial" (playlist_dsp)
# "release schedule"/"release campaign"/"delivery commitment" (label_ops)

_NARROW_QUERY = (
    "How do we decide between print on demand and bulk manufacturing for our "
    "first merchandise run, set a pricing formula to maximize gross margin on "
    "each item, and choose the best online store platform to sell our products "
    "to fans?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "merch-deal-contract-negotiate-clauses-indemnity-warranty-rights-legal",
        "merchandise-revenue-accounting-income-splits-royalty-recoupment-finance-royalties",
        "merchandise-launch-marketing-campaign-social-media-fanbase-audience-rollout-marketing",
        "merch-superfan-bundles-membership-tier-meet-greet-patreon-fan-loyalty-community-fan-social",
        "merchandise-strategy-touring-run-venue-hall-fees-concert-ticketing-box-office-live-touring",
    ],
)
def test_merch_empire_consult_home_leads_and_cross_domains_present(query, cross):
    """
    merch-empire's home domain 'bizdev' is always first; every expected
    cross-domain is present. Verifies home-first invariant and merchandise
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


def test_merch_empire_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped print-on-demand vs. bulk-manufacturing / pricing-formula /
    online-store-platform question (no keywords from legal / finance_royalties /
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
