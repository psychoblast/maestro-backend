"""
Phase 3e — Per-agent deep consult test for live-wire.

Scope: live-wire only. Home domain "live_touring". Six realistic
questions an artist or their team would ask Knox (Booking Agent),
covering: festival headliner booking contract and guarantee clause
review, show fee and tour revenue income splits with touring band and
promoter, building a marketing campaign around a confirmed festival
booking, creating superfan meet-and-greet and VIP experience packages
at concert venues, securing a brand partnership and merchandise deal
across a multi-city tour, and a deliberately narrow booking-logistics
question.

For each cross-domain question we assert:
  (a) live-wire's home domain "live_touring" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure promoter-pitch / gig-inquiry / load-in question
that avoids keywords from legal, finance_royalties, marketing, fan_social,
bizdev, label_ops, playlist_dsp, publishing, production, data_analytics,
capital_funding, digital_ops, intelligence, management, ar, sync,
controller, executive, or any other non-home domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "live-wire"
_HOME  = "live_touring"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "live_touring" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.
# NOTE: "upcoming" contains "upc" → digital_ops — use "next" instead.
# NOTE: "performance rights" → publishing; "performance royalt" → finance_royalties
#       — use "performance guarantee" / "performance fee" safely (neither is a
#       finance or publishing keyword alone).

DEEP_CONSULT_MATRIX = [
    (
        # live_touring: home — always leads ("festival", "headliner",
        #               "booking", "performance fee")
        # legal:        "negotiate" (→ "negotiat"), "contract",
        #               "clauses" (→ "clause"), "indemnity" (→ "indemnit"),
        #               "rights"
        "We have been offered a headliner slot at a major festival and need "
        "to negotiate the booking contract — examining the performance "
        "guarantee clauses, indemnity provisions, and our rights before we "
        "commit to the deal.",
        ["legal"],
    ),
    (
        # live_touring: home — always leads ("booking", "live show",
        #               "show fee", "touring", "venue", "promoter")
        # finance_royalties: "income split" (→ "income splits"),
        #                    "tour revenue", "show income"
        "We are booking a run of live shows and need to understand how the "
        "show fee and tour revenue are structured as income splits between "
        "the artist, the touring band, and the promoter — and how show "
        "income is divided after venue costs are deducted.",
        ["finance_royalties"],
    ),
    (
        # live_touring: home — always leads ("festival", "booking", "ticket",
        #               "touring", "concert")
        # marketing:    "marketing campaign", "audience", "growth",
        #               "instagram", "tiktok"
        "How do we build a marketing campaign to announce our confirmed "
        "festival booking, grow our audience reach, and drive ticket sales "
        "through Instagram and TikTok across the whole touring run?",
        ["marketing"],
    ),
    (
        # live_touring: home — always leads ("touring", "concert", "venue",
        #               "on the road")
        # fan_social:   "superfan", "meet and greet", "vip experience"
        "We are on a touring run and want to create superfan packages at "
        "each concert venue — meet and greet sessions with the artist, VIP "
        "experience access backstage, and exclusive access for the most "
        "loyal fans on the road.",
        ["fan_social"],
    ),
    (
        # live_touring: home — always leads ("booking", "tour", "venue",
        #               "touring")
        # bizdev:       "brand" (→ "brand partnership"), "partnership",
        #               "merchandise deal", "sponsorship" (→ "sponsor"),
        #               "activation"
        "We are booking a multi-city tour and want to lock in a brand "
        "partnership deal — including a merchandise deal at each venue and "
        "sponsorship activation packages across the whole touring run.",
        ["bizdev"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped promoter-pitch / gig-inquiry / load-in question that returns
# ONLY "live_touring" (via home domain). Deliberately avoids:
# "contract" / "clause" / "rights" / "legal" / "negotiat" / "indemnit" (legal)
# "royalt" / "splits" / "split " / "show income" / "tour revenue" /
#   "income split" / "show fee" (finance_royalties)
# "marketing" / "campaign" / "social media" / "audience" / "growth" /
#   "instagram" / "tiktok" (marketing)
# "superfan" / "meet and greet" / "vip experience" / "fan engagement" (fan_social)
# "brand" / "sponsor" / "merch" / "merchandise" / "partnership" /
#   "activation" (bizdev)
# "release schedule" / "delivery commitment" / "distribution" (label_ops)
# "playlist" / "dsp" / "editorial" (playlist_dsp)
# "publish" / "catalog" / "composition" / "songwrit" (publishing)
# "production" / "studio" / "mixing" / "mastering" (production)
# "analytics" / "metric" / "kpi" (data_analytics)
# "capital" / "fund" / "financ" / "invest" (capital_funding)
# "upcoming" — triggers digital_ops via "upc" substring — excluded here
# "intelligence" / "market trend" (intelligence)
# "artist manager" / "management" / "managing the artist" (management)
# "scouting" / "talent scout" / "unsigned" / "a&r" (ar)
# "sync" / "licens" / "film" / "tv" / "placement" (sync)
# "reconcil" / "ledger" / "controller" (controller)
# "executive" / "ceo" / "strategic" (executive)

_NARROW_QUERY = (
    "How do we pitch our act to independent promoters in three new cities, "
    "follow each gig inquiry through to a confirmed show date, and handle "
    "the load-in time and crew logistics on the road?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "festival-headliner-booking-contract-guarantee-clauses-indemnity-legal",
        "live-show-booking-show-fee-tour-revenue-income-splits-finance-royalties",
        "festival-booking-marketing-campaign-audience-ticket-sales-instagram-tiktok",
        "touring-concert-venue-superfan-meet-greet-vip-experience-fan-social",
        "multi-city-tour-booking-brand-partnership-merchandise-deal-sponsorship-bizdev",
    ],
)
def test_live_wire_consult_home_leads_and_cross_domains_present(query, cross):
    """
    live-wire's home domain 'live_touring' is always first; every expected
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


def test_live_wire_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped promoter-pitch / gig-inquiry / load-in question (no keywords
    from legal / finance_royalties / marketing / fan_social / bizdev / label_ops /
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
