"""
Phase 3e — Per-agent deep consult test for live-coach.

Scope: live-coach only. Home domain "live_touring". Six realistic
questions an artist or their team would ask Coach (Performance Coach),
covering: contract obligations and rider negotiation for a festival show,
performance fee and show income splits with touring band and crew, building
a marketing campaign around tour dates using live show content, designing
superfan meet-and-greet experiences on tour, aligning a release schedule
and DSP delivery commitment with the concert touring timeline, and a
deliberately narrow setlist/stage-craft question.

For each cross-domain question we assert:
  (a) live-coach's home domain "live_touring" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure setlist / stage-energy / vocal warm-up question that
avoids keywords from legal, finance_royalties, marketing, fan_social,
label_ops, playlist_dsp, publishing, production, bizdev, data_analytics,
capital_funding, digital_ops, intelligence, management, ar, sync,
controller, executive, or any other non-home domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "live-coach"
_HOME  = "live_touring"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "live_touring" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.
# NOTE: "upcoming" contains "upc" → digital_ops — use "next" instead.
# NOTE: "performance rights" → publishing, "performance royalt" → finance_royalties
#       — use "performance obligations" / "performance fee" safely.

DEEP_CONSULT_MATRIX = [
    (
        # live_touring: home — always leads ("concert", "festival", "venue",
        #               "rider", "stage")
        # legal:        "negotiat" (via "negotiate"), "clause" (via "clauses"),
        #               "contract" (via "contractual"), "rights"
        "We are advancing a concert show at a major festival venue and need to "
        "negotiate the rider clauses and understand our contractual performance "
        "obligations and rights before signing.",
        ["legal"],
    ),
    (
        # live_touring: home — always leads ("festival", "headliner",
        #               "performance fee", "touring")
        # finance_royalties: "show income" (enriched kw), "splits"
        "We are performing as headliner at a summer festival and need to "
        "understand how the performance fee and show income splits are structured "
        "with our touring band and crew after venue costs.",
        ["finance_royalties"],
    ),
    (
        # live_touring: home — always leads ("tour", "live show")
        # marketing:    "marketing campaign" (x2), "social media", "audience",
        #               "growth", "reach", "instagram", "tiktok"
        "How do we build a marketing campaign around our tour dates that leverages "
        "live show content for social media growth and audience reach on Instagram "
        "and TikTok?",
        ["marketing"],
    ),
    (
        # live_touring: home — always leads ("tour")
        # fan_social:   "fan engagement", "meet and greet", "superfan tier",
        #               "behind-the-scenes content"
        "How do we design fan engagement opportunities on tour — including meet "
        "and greet packages for our superfan tier and exclusive "
        "behind-the-scenes content from backstage?",
        ["fan_social"],
    ),
    (
        # live_touring: home — always leads ("concert", "tour", "stage")
        # label_ops:    "release schedule", "delivery commitment",
        #               "distribution partner" (via "distribution partners")
        "We are planning a concert tour and need to align our release schedule "
        "and delivery commitment to distribution partners with our stage "
        "rehearsal timeline.",
        ["label_ops"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped setlist / stage-energy / vocal warm-up question that returns
# ONLY "live_touring" (via home domain). Deliberately avoids:
# "contract" / "clause" / "rights" / "legal" / "negotiat" (legal)
# "royalt" / "splits" / "split " / "show income" / "performance fee" (finance_royalties)
# "marketing" / "campaign" / "social media" / "audience" / "growth" (marketing)
# "fan engagement" / "superfan" / "meet and greet" / "behind-the-scenes content" (fan_social)
# "release schedule" / "delivery commitment" / "distribution" / "label ops" (label_ops)
# "playlist" / "dsp" / "editorial" / "streaming platform" (playlist_dsp)
# "publish" / "catalog" / "composition" / "songwrit" (publishing)
# "production" / "studio" / "mixing" / "mastering" / "vocal production" (production)
# "brand" / "merch" / "merchandise" / "sponsor" / "partner " (bizdev)
# "analytics" / "metric" / "kpi" / "fan insight" (data_analytics)
# "capital" / "fund" / "financ" / "invest" (capital_funding)
# "upcoming" — triggers digital_ops via "upc" substring — excluded here
# "intelligence" / "market trend" (intelligence)
# "artist manager" / "management" / "commission" (management)
# "scouting" / "talent scout" / "unsigned" / "a&r" (ar)
# "sync" / "licens" / "film" / "tv" / "placement" (sync)
# "reconcil" / "ledger" / "controller" (controller)
# "executive" / "ceo" / "strategic" (executive)

_NARROW_QUERY = (
    "How do we structure a 30-minute setlist — opening strong, building to a "
    "mid-set peak, and closing on the artist's strongest song — while managing "
    "vocal warm-up routines and maintaining consistent stage energy night after night?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "concert-festival-rider-clause-contractual-rights-legal",
        "headliner-festival-performance-fee-show-income-splits-finance-royalties",
        "marketing-campaign-tour-live-show-social-media-audience-growth",
        "fan-engagement-meet-and-greet-superfan-tier-behind-scenes-tour",
        "release-schedule-delivery-commitment-distribution-concert-tour-label-ops",
    ],
)
def test_live_coach_consult_home_leads_and_cross_domains_present(query, cross):
    """
    live-coach's home domain 'live_touring' is always first; every expected
    cross-domain is present. Verifies home-first invariant and performance
    coach cross-domain routing quality.
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


def test_live_coach_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped setlist / stage-energy / vocal warm-up question (no keywords
    from legal / finance_royalties / marketing / fan_social / label_ops /
    playlist_dsp / publishing / production / bizdev / data_analytics /
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
