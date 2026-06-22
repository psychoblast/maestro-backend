"""
Phase 3e — Per-agent deep consult test for booking-agent.

Scope: booking-agent only. Home domain "live_touring". Six realistic
questions an artist or their team would ask a booking agent, covering:
headliner deal memo negotiation and contract clause review, show fee
and tour revenue income splits with touring band and promoter, marketing
campaign to announce a confirmed tour and drive ticket sales, superfan
VIP experience and meet-and-greet packages at concert venues, coordinating
a booking timeline against label delivery commitments and release schedule,
and a deliberately narrow routing/logistics question.

For each cross-domain question we assert:
  (a) booking-agent's home domain "live_touring" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped tour routing / promoter approach /
stage-plot question that avoids keywords from legal, finance_royalties,
marketing, fan_social, bizdev, label_ops, playlist_dsp, publishing,
production, data_analytics, capital_funding, digital_ops, intelligence,
management, ar, sync, controller, executive, or any other non-home domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "booking-agent"
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
        # live_touring: home — always leads ("booking", "headliner",
        #               "promoter", "show fee")
        # legal:        "negotiate" (→ "negotiat"), "deal memo",
        #               "clauses" (→ "clause"), "indemnity" (→ "indemnit"),
        #               "warranty" (→ "warrant"), "contract"
        "We are booking a headliner run and need to negotiate each deal memo "
        "with the promoter — examining the guarantee clauses, indemnity "
        "provisions, and warranty terms before we sign the booking contract.",
        ["legal"],
    ),
    (
        # live_touring: home — always leads ("booking", "concert",
        #               "touring", "promoter", "box office", "show fee")
        # finance_royalties: "show fee" (→ also live_touring, but home covers),
        #                    "tour revenue", "income split" (via "income splits"),
        #                    "splits"
        "We are booking a concert run and need to structure the show fee and "
        "tour revenue as income splits between the artist, the touring band, "
        "and the promoter after box office costs are deducted.",
        ["finance_royalties"],
    ),
    (
        # live_touring: home — always leads ("booking", "tour",
        #               "ticket", "touring")
        # marketing:    "marketing" (→ "marketing campaign"),
        #               "campaign", "audience", "reach",
        #               "instagram", "tiktok"
        "We have confirmed a 10-city booking run and want to build a marketing "
        "campaign to announce our tour dates, grow our audience reach, and "
        "drive ticket sales through Instagram and TikTok.",
        ["marketing"],
    ),
    (
        # live_touring: home — always leads ("booking", "concert",
        #               "venue", "touring")
        # fan_social:   "superfan", "vip experience",
        #               "meet and greet", "fan engagement"
        "We are booking a series of concerts at major venues and want to offer "
        "superfan packages at each stop — VIP experience access backstage, "
        "meet and greet sessions with the artist, and exclusive fan engagement "
        "for our most devoted supporters.",
        ["fan_social"],
    ),
    (
        # live_touring: home — always leads ("booking", "touring")
        # label_ops:    "delivery commitment" (via "delivery commitments"),
        #               "release schedule", "release tracking",
        #               "distribution deal"
        "We are booking a touring run across 12 cities but the label has "
        "delivery commitments that conflict with the release schedule — how "
        "do we coordinate the booking dates with release tracking and the "
        "distribution deal?",
        ["label_ops"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped tour routing / promoter approach / stage-plot question that
# returns ONLY "live_touring" (via home domain + keyword matches).
# Deliberately avoids:
# "contract"/"clause"/"rights"/"legal"/"negotiat"/"indemnit"/"warrant"/"deal memo" (legal)
# "royalt"/"splits"/"split "/"recoup"/"tour revenue"/"income split"/"show income"/
#   "show fee" (finance_royalties)
# "marketing"/"campaign"/"audience"/"reach"/"instagram"/"tiktok"/"social media" (marketing)
# "superfan"/"vip experience"/"meet and greet"/"fan engagement"/"fan community" (fan_social)
# "brand"/"sponsor"/"merch"/"merchandise"/"partnership"/"activation" (bizdev)
# "release schedule"/"delivery commitment"/"distribution"/"release tracking" (label_ops)
# "playlist"/"dsp"/"editorial" (playlist_dsp)
# "publish"/"catalog"/"songwriter"/"composition" (publishing)
# "production"/"studio"/"mixing"/"mastering" (production)
# "analytics"/"metric"/"kpi" (data_analytics)
# "capital"/"fund"/"financ"/"invest"/"grant" (capital_funding)
# "upcoming" — contains "upc" → digital_ops — excluded
# "intelligence"/"market trend"/"industry" (intelligence)
# "artist manager"/"management"/"managing the artist" (management)
# "scouting"/"unsigned"/"a&r" (ar)
# "sync"/"licens"/"film"/"tv"/"placement" (sync)
# "reconcil"/"ledger"/"controller" (controller)
# "executive"/"ceo"/"strategic" (executive)

_NARROW_QUERY = (
    "How do we build a routing map for a headliner run, approach local "
    "promoters at each city stop, confirm the concert dates at suitable "
    "venues, and coordinate the stage plot and crew rider for each show?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "headliner-booking-deal-memo-guarantee-clauses-indemnity-legal",
        "concert-booking-show-fee-tour-revenue-income-splits-finance-royalties",
        "booking-run-marketing-campaign-tour-announcement-audience-ticket-sales",
        "concert-venues-superfan-vip-experience-meet-greet-fan-engagement",
        "touring-run-label-delivery-commitments-release-schedule-distribution-deal",
    ],
)
def test_booking_agent_consult_home_leads_and_cross_domains_present(query, cross):
    """
    booking-agent's home domain 'live_touring' is always first; every expected
    cross-domain is present. Verifies home-first invariant and booking-agent
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


def test_booking_agent_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped tour routing / promoter approach / stage-plot question (no
    keywords from legal / finance_royalties / marketing / fan_social / bizdev /
    label_ops / playlist_dsp / publishing / production / data_analytics /
    capital_funding / digital_ops / intelligence / management / ar / sync /
    controller / executive) must return only the home domain with no spurious
    cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
