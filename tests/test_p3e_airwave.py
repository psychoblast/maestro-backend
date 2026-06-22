"""
Phase 3e — Per-agent deep consult test for airwave.

Scope: airwave only. Home domain "playlist_dsp". Six realistic
questions an artist or their team would ask Solo (Radio & Playlist
Specialist), covering: building a playlist campaign with social media
rollout and independent curator outreach, using DSP editorial tracking
and streaming analytics to understand algorithmic add performance,
coordinating editorial pitch deadlines with label delivery commitments
and pre-save dates, building a social media and superfan fan-community
strategy alongside playlist pitching, leveraging a sync placement to
support Discover Weekly editorial consideration and radio promotion, and
a deliberately narrow curator-outreach / airplay / DSP question.

For each cross-domain question we assert:
  (a) airwave's home domain "playlist_dsp" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped independent-curator / airplay / DSP
question that avoids keywords from legal, finance_royalties, marketing,
fan_social, bizdev, label_ops, publishing, production, data_analytics,
capital_funding, digital_ops, intelligence, management, ar, sync,
controller, executive, live_touring, or any other non-home domain.

Routing gap noted: airwave's SKILL.md (Solo) is rich in international
radio promotion strategy — BBC Radio 1, Nigerian radio, Canadian radio,
college/community radio, tier-aware radio promoter hiring — territory
logic that lives conceptually closer to "intelligence" or "label_ops",
but the home domain "playlist_dsp" is the correct current mapping and
covers the agent's DSP/playlist and airplay/radio-promotion keywords
cleanly. This test encodes the CURRENT correct behavior without
changing agent_home.py or shared files.

NOTE: "playlist" alone fires marketing (marketing keyword), so any
query that mentions "playlist" picks up marketing as a cross-domain.
NOTE: "submission" contains the substring "bmi" → fires finance_royalties
— avoid "submission" unless finance_royalties is an intended cross-domain.
NOTE: "editorial pitch" fires both playlist_dsp and label_ops; use
"editorial consideration" when only playlist_dsp is intended.
NOTE: "spotify for artists" fires data_analytics as well as playlist_dsp.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "airwave"
_HOME  = "playlist_dsp"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "playlist_dsp" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # playlist_dsp: home — "playlist campaign", "independent curator",
        #               "playlist" (substring)
        # marketing:    "social media", "campaign", "audience", "growth",
        #               "rollout", "follower", "playlist" (marketing also
        #               carries "playlist" as a standalone keyword)
        "We want to build a playlist campaign and social media audience "
        "growth strategy for our release rollout with independent curator "
        "outreach and fan follower targets.",
        ["marketing"],
    ),
    (
        # playlist_dsp: home — "editorial consideration", "dsp",
        #               "algorithmic add", "discover weekly"
        # data_analytics: "analytics" (in "streaming analytics")
        # NOTE: "submission" avoided — contains "bmi" → finance_royalties.
        # NOTE: "editorial consideration" does NOT fire label_ops
        #       (label_ops needs "editorial pitch" or "editorial submission").
        "How do we use DSP editorial consideration tracking and streaming "
        "analytics to understand our algorithmic add performance and refine "
        "our Discover Weekly approach?",
        ["data_analytics"],
    ),
    (
        # playlist_dsp: home — "editorial pitch", "pre-save",
        #               "new music friday"
        # label_ops:    "editorial pitch", "delivery commitment",
        #               "pre-save", "release planning"
        # NOTE: "activation" avoided — fires bizdev.
        # NOTE: "editorial pitch" fires both playlist_dsp and label_ops —
        #       intentional cross-domain here.
        "We need to coordinate our editorial pitch deadline with the label "
        "delivery commitment and pre-save date to stay on our New Music "
        "Friday release planning schedule.",
        ["label_ops"],
    ),
    (
        # playlist_dsp: home — "playlist pitch" (via "playlist pitching"),
        #               "dsp", "playlist" (substring)
        # marketing:    "social media", "campaign", "rollout",
        #               "playlist" (marketing keyword), "engagement"
        # fan_social:   "superfan", "fan community"
        "We want a social media strategy that builds superfan engagement "
        "and fan community support while driving playlist pitching momentum "
        "for our DSP campaign rollout.",
        ["marketing", "fan_social"],
    ),
    (
        # playlist_dsp: home — "discover weekly", "editorial consideration",
        #               "radio promotion"
        # sync:         "tv" (in "TV advertising"), "advert" (in "advertising"),
        #               "sync", "placement", "licens" (in "licensing")
        # NOTE: "editorial consideration" does NOT fire label_ops (needs
        #       "editorial pitch" or "editorial submission"). ✓
        "We secured a TV advertising sync placement — how do we leverage "
        "the licensing momentum to support our Discover Weekly editorial "
        "consideration and build a radio promotion push?",
        ["sync"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped independent-curator / airplay / New Music Friday question
# that returns ONLY "playlist_dsp" (via home domain + keyword matches).
# Deliberately avoids:
# "contract"/"clause"/"rights"/"legal"/"negotiat"/"deal memo" (legal)
# "royalt"/"splits"/"split "/"recoup"/"tour revenue"/"show income" (finance_royalties)
# "submission" — contains substring "bmi" → finance_royalties (excluded)
# "marketing"/"campaign"/"audience"/"social media"/"playlist"/"growth"/
#   "rollout"/"follower"/"reach"/"engagement"/"content strategy" (marketing)
#   NOTE: "playlist" alone is a marketing keyword — avoided here.
#   NOTE: "outreach" contains the substring "reach" → fires marketing —
#         use "relations" or "connections" instead.
# "superfan"/"fan community"/"fan engagement"/"casual listener"/"save rate"
#   (fan_social — "save rate" fires both fan_social and data_analytics)
# "brand"/"sponsor"/"partnership"/"activation"/"merch" (bizdev)
# "editorial pitch"/"editorial submission"/"pre-save"/"release planning"/
#   "delivery commitment"/"release schedule"/"distributor" (label_ops)
# "publish"/"catalog"/"songwrit"/"co-write"/"administration" (publishing)
# "production"/"studio"/"mixing"/"mastering"/"stems"/"lufs" (production)
# "analytics"/"metric"/"kpi"/"streaming analysis"/"dsp metric"/
#   "spotify for artists" (data_analytics — "spotify for artists" fires da)
# "capital"/"fund"/"financ"/"invest"/"grant"/"equity" (capital_funding)
# "upcoming" — contains "upc" substring → digital_ops (excluded)
# "metadata"/"isrc"/"upc"/"ddex"/"dsp delivery" (digital_ops)
# "intelligence"/"market intelligence"/"industry"/"weekly scan" (intelligence)
#   NOTE: "discover weekly" has "weekly" but "weekly scan" ≠ "weekly" alone ✓
# "artist manager"/"management"/"managing the artist" (management)
# "scouting"/"unsigned"/"a&r"/"emerging artist"/"discovery" (ar)
#   NOTE: "discover" ≠ "discovery" — substring check does not fire ar ✓
# "sync"/"licens"/"placement"/"film"/"tv" (sync)
#   NOTE: "land a" is safe — "land a placement" needs the full phrase ✓
# "tour"/"concert"/"gig"/"venue"/"booking"/"festival"/"ticket" (live_touring)
# "reconcil"/"ledger"/"controller"/"close the books" (controller)
# "executive"/"ceo"/"go/no-go"/"build vs buy" (executive)
#   NOTE: "build our" does NOT match "build vs buy" ✓

_NARROW_QUERY = (
    "How do we build our independent curator relations and airplay strategy "
    "to land a New Music Friday add and strengthen our Discover Weekly "
    "momentum through DSP support tools?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "playlist-campaign-social-media-curator-outreach-release-rollout-marketing",
        "dsp-editorial-tracking-streaming-analytics-algorithmic-add-data-analytics",
        "editorial-pitch-deadline-label-delivery-pre-save-release-planning-label-ops",
        "social-media-superfan-fan-community-playlist-pitching-dsp-campaign-marketing-fan-social",
        "tv-sync-placement-licensing-discover-weekly-editorial-radio-promotion-sync",
    ],
)
def test_airwave_consult_home_leads_and_cross_domains_present(query, cross):
    """
    airwave's home domain 'playlist_dsp' is always first; every expected
    cross-domain is present. Verifies home-first invariant and
    radio-and-playlist specialist cross-domain routing quality.
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


def test_airwave_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped independent-curator / airplay / DSP question (no
    keywords from legal / finance_royalties / marketing / fan_social /
    bizdev / label_ops / publishing / production / data_analytics /
    capital_funding / digital_ops / intelligence / management / ar / sync /
    controller / executive / live_touring) must return only the home domain
    with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
