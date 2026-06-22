"""
Phase 3e — Per-agent deep consult test for venue-hawk.

Scope: venue-hawk only. Home domain "live_touring". Six realistic
questions an artist or their team would ask Ray B (Booking Agent),
covering: headliner festival contract and promoter clause review, show
income splits and tour revenue division after venue costs, marketing
campaign built around the touring schedule, superfan fan-engagement
packages at concert venues, venue sponsorship and merchandise deal
negotiation on a multi-city tour, and a deliberately narrow tour-routing
/ load-in question.

For each cross-domain question we assert:
  (a) venue-hawk's home domain "live_touring" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure tour-routing / load-in / on-the-road question that
avoids keywords from legal, finance_royalties, marketing, fan_social,
bizdev, label_ops, playlist_dsp, publishing, production, data_analytics,
capital_funding, digital_ops, intelligence, management, ar, sync,
controller, executive, or any other non-home domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "venue-hawk"
_HOME  = "live_touring"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "live_touring" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # live_touring: home — always leads ("festival", "venue", "promoter",
        #               "box office", "headliner")
        # legal:        "negotiat" (via "negotiating"), "contract",
        #               "indemnit" (via "indemnity"), "clause" (via "clauses"),
        #               "rights"
        "We are negotiating a headliner slot at a major festival venue and need "
        "to review the promoter contract — examining the indemnity clauses, box "
        "office guarantee, and our rights before we sign.",
        ["legal"],
    ),
    (
        # live_touring: home — always leads ("booking", "concert", "tour",
        #               "venue", "promoter")
        # finance_royalties: "show income", "splits", "tour revenue"
        "We are booking a summer concert tour and need to understand how the "
        "show income splits and tour revenue are divided between the artist, "
        "the venue, and the promoter after costs are deducted.",
        ["finance_royalties"],
    ),
    (
        # live_touring: home — always leads ("touring", "ticket")
        # marketing:    "marketing campaign", "audience", "social media",
        #               "instagram", "tiktok", "growth"
        "How do we build a marketing campaign around our touring schedule to "
        "grow audience reach and drive ticket sales using social media — "
        "Instagram and TikTok — in each city?",
        ["marketing"],
    ),
    (
        # live_touring: home — always leads ("concert", "tour", "venue", "stage")
        # fan_social:   "fan engagement", "meet and greet", "superfan tier"
        "We are planning a sold-out concert tour and want to create fan "
        "engagement packages at each venue — including meet and greet sessions "
        "for our superfan tier and exclusive backstage access on stage at key shows.",
        ["fan_social"],
    ),
    (
        # live_touring: home — always leads ("booking", "tour", "venue", "concert")
        # bizdev:       "sponsor" (via "sponsorship"), "brand",
        #               "merchandise deal"
        "We are booking a multi-city tour and want to negotiate venue "
        "sponsorship deals with brand partners while setting up a merchandise "
        "deal at each concert stop.",
        ["bizdev"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped tour-routing / load-in question that returns ONLY
# "live_touring" (via home domain). Deliberately avoids:
# "contract" / "clause" / "rights" / "legal" / "negotiat" / "indemnit" (legal)
# "royalt" / "splits" / "split " / "show income" / "tour revenue" (finance_royalties)
# "marketing" / "campaign" / "social media" / "audience" / "growth" (marketing)
# "fan engagement" / "superfan" / "meet and greet" (fan_social)
# "brand" / "sponsor" / "merch" / "merchandise" / "partner " (bizdev)
# "release schedule" / "distribution" / "delivery commitment" (label_ops)
# "playlist" / "dsp" / "editorial" / "streaming platform" (playlist_dsp)
# "publish" / "catalog" / "composition" / "songwrit" (publishing)
# "production" / "studio" / "mixing" / "mastering" (production)
# "analytics" / "metric" / "kpi" (data_analytics)
# "capital" / "fund" / "financ" / "invest" (capital_funding)
# "upcoming" — triggers digital_ops via "upc" substring — excluded here
# "intelligence" / "market trend" (intelligence)
# "artist manager" / "management" / "commission" (management)
# "scouting" / "talent scout" / "unsigned" / "a&r" (ar)
# "sync" / "licens" / "film" / "tv" / "placement" (sync)
# "reconcil" / "ledger" / "controller" (controller)
# "executive" / "ceo" / "strategic" (executive)

_NARROW_QUERY = (
    "How do we map a 12-city concert tour routing to minimize travel days between "
    "venues while keeping the load-in window manageable for crew members arriving "
    "on the road?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "headliner-festival-venue-promoter-contract-indemnity-clauses-legal",
        "concert-tour-booking-show-income-splits-tour-revenue-finance-royalties",
        "touring-ticket-marketing-campaign-social-media-audience-growth",
        "concert-tour-venue-fan-engagement-meet-greet-superfan-tier",
        "multi-city-tour-booking-venue-sponsorship-brand-merchandise-deal-bizdev",
    ],
)
def test_venue_hawk_consult_home_leads_and_cross_domains_present(query, cross):
    """
    venue-hawk's home domain 'live_touring' is always first; every expected
    cross-domain is present. Verifies home-first invariant and booking agent
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


def test_venue_hawk_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped tour-routing / load-in question (no keywords from legal /
    finance_royalties / marketing / fan_social / bizdev / label_ops /
    playlist_dsp / publishing / production / data_analytics / capital_funding /
    digital_ops / intelligence / management / ar / sync / controller /
    executive) must return only the home domain with no spurious cross-domain
    routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
