"""
Phase 3e — Per-agent deep consult test for release-strategist.

Scope: release-strategist only. Home domain "playlist_dsp". Six realistic
questions an artist or their team would ask Sage (Release Strategist),
covering: building a superfan engagement campaign around a DSP editorial
playlist release with social media rollout, designing a go-to-market
release strategy with digital marketing and fanbase growth, mapping the
release schedule with milestone timelines and delivery commitment gates,
using streaming data and DSP metrics to benchmark and forecast release
trajectory, coordinating the release date with touring schedule and venue
booking alongside a marketing campaign rollout, and a deliberately narrow
dsp-strategy / algorithmic-add / curator-connection question.

For each cross-domain question we assert:
  (a) release-strategist's home domain "playlist_dsp" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped DSP strategy / Discover Weekly /
algorithmic-add / independent-curator question that avoids keywords from
legal, finance_royalties, marketing, fan_social, bizdev, label_ops,
publishing, production, data_analytics, capital_funding, digital_ops,
intelligence, management, ar, sync, controller, executive, live_touring,
or any other non-home domain.

Routing gap noted: release-strategist's SKILL.md (Sage) orchestrates
cross-phase release campaigns — venue booking (live_touring), PR/social
rollout (marketing), label delivery milestones (label_ops), and curator
pitches (playlist_dsp). The home domain "playlist_dsp" is the correct
current mapping reflecting the agent's core DSP release and curator-pitch
focus. This test encodes the CURRENT correct behavior without changing
agent_home.py or shared files.

NOTE: "playlist" alone is a marketing keyword — queries containing
"playlist" will fire marketing as well as playlist_dsp.
NOTE: "distributor" fires BOTH digital_ops AND label_ops — avoid it when
digital_ops is not an intended cross-domain.
NOTE: "pre-save" and "editorial pitch" fire BOTH playlist_dsp and
label_ops; "pitch window" fires BOTH as well.
NOTE: "release strategy" is a marketing keyword (not label_ops).
NOTE: "recoup" alone fires finance_royalties (distinct from
"recoupment clock" which fires label_ops).

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "release-strategist"
_HOME  = "playlist_dsp"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "playlist_dsp" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.
# NOTE: "campaign" alone → marketing; "release campaign" → label_ops +
#       marketing (via "campaign" substring) — use "release schedule" /
#       "milestone timeline" when label_ops-only is intended.
# NOTE: "distributor" → both digital_ops AND label_ops — excluded from Q3.
# NOTE: "playlist" alone → marketing keyword (fires alongside playlist_dsp).

DEEP_CONSULT_MATRIX = [
    (
        # playlist_dsp: home — "dsp", "editorial playlist", "playlist"
        # marketing:    "social media", "rollout", "audience", "campaign",
        #               "playlist" (marketing also carries "playlist")
        # fan_social:   "superfan", "fan community"
        "We want to build a superfan engagement campaign around our DSP "
        "editorial playlist release and social media rollout to grow our "
        "fan community and streaming audience.",
        ["marketing", "fan_social"],
    ),
    (
        # playlist_dsp: home — "dsp", "playlist" (in "DSP playlist")
        # marketing:    "release strategy", "fanbase", "social media",
        #               "reach", "marketing", "audience", "playlist"
        # NOTE: "content reach" — "content" alone is not a marketing keyword
        #       ("content strategy" is); "reach" alone fires marketing. ✓
        "We need to build our release strategy, grow the fanbase through "
        "social media and content reach, and launch a marketing push that "
        "maximizes our streaming audience and DSP playlist consideration.",
        ["marketing"],
    ),
    (
        # playlist_dsp: home — "pre-save", "editorial pitch", "pitch window"
        #               (all three are also playlist_dsp keywords)
        # label_ops:    "release schedule", "milestone timeline",
        #               "readiness gate", "delivery commitment", "pre-save",
        #               "editorial pitch", "pitch window"
        # NOTE: "distributor" excluded — it fires digital_ops in addition to
        #       label_ops, which is not the focus of this scenario.
        "We need to map the release schedule with milestone timelines and "
        "readiness gates, align our delivery commitment to the label, and "
        "set the pre-save date before our editorial pitch window.",
        ["label_ops"],
    ),
    (
        # playlist_dsp: home — "dsp" (in "DSP metrics")
        # data_analytics: "streaming data", "dsp metric", "benchmark",
        #                 "comparable case", "forecast", "trajectory"
        "How do we use streaming data and DSP metrics to benchmark our "
        "release performance against comparable cases and forecast our "
        "listener trajectory after launch?",
        ["data_analytics"],
    ),
    (
        # playlist_dsp: home — (no explicit playlist_dsp keyword; home forced)
        # live_touring: "touring" (in "touring schedule"), "venue",
        #               "booking", "concert"
        # marketing:    "marketing campaign", "marketing" (substring),
        #               "social media", "rollout"
        "How do we time our release date around our touring schedule, "
        "coordinate venue booking announcements, and launch a marketing "
        "campaign with social media rollout that supports the concert "
        "promotion?",
        ["live_touring", "marketing"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped DSP strategy / Discover Weekly / algorithmic-add /
# independent-curator question that returns ONLY "playlist_dsp" (via home
# domain + keyword matches).
# Deliberately avoids:
# "contract"/"clause"/"rights"/"legal"/"negotiat"/"deal memo" (legal)
# "royalt"/"mechanical"/"bmi"/"splits"/"recoup"/"advance"/"statement" (finance_royalties)
# "marketing"/"campaign"/"audience"/"social media"/"playlist"/"growth"/
#   "rollout"/"follower"/"reach"/"release strategy" (marketing)
#   NOTE: "playlist" alone is a marketing keyword — excluded here.
#   NOTE: "follower" ≠ "follow"; "follow conversion" does NOT fire marketing. ✓
# "superfan"/"fan community"/"fan engagement"/"save rate" (fan_social)
# "brand"/"sponsor"/"partnership"/"activation"/"merch" (bizdev)
# "release schedule"/"milestone timeline"/"pre-save"/"editorial pitch"/
#   "pitch window"/"delivery commitment"/"distributor" (label_ops)
#   NOTE: "editorial consideration" is NOT a label_ops keyword. ✓
# "publish"/"catalog"/"songwrit"/"co-write"/"administration" (publishing)
# "production"/"studio"/"mixing"/"mastering"/"stems"/"lufs" (production)
# "analytics"/"metric"/"kpi"/"streaming data"/"dsp metric"/
#   "benchmark"/"forecast"/"trajectory" (data_analytics)
#   NOTE: "data" alone is not a data_analytics keyword. ✓
# "capital"/"fund"/"financ"/"invest"/"grant"/"equity" (capital_funding)
# "metadata"/"isrc"/"upc"/"ddex"/"dsp delivery"/"distributor" (digital_ops)
#   NOTE: "upcoming" contains "upc" substring → digital_ops — excluded. ✓
# "intelligence"/"market trend"/"industry" (intelligence)
# "artist manager"/"management"/"managing the artist" (management)
# "scouting"/"unsigned"/"a&r"/"emerging artist" (ar)
# "sync"/"licens"/"placement"/"film"/"tv"/"advert" (sync)
# "tour"/"concert"/"gig"/"venue"/"booking"/"festival"/"ticket" (live_touring)
# "reconcil"/"ledger"/"controller"/"close the books" (controller)
# "executive"/"ceo"/"go/no-go"/"build vs buy" (executive)

_NARROW_QUERY = (
    "How do we develop a dsp strategy for Discover Weekly algorithmic add "
    "optimization and editorial consideration, using our independent curator "
    "connections and follow conversion data to time our New Music Friday "
    "approach?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "superfan-campaign-dsp-editorial-playlist-social-rollout-fan-community-marketing-fan-social",
        "release-strategy-fanbase-social-media-marketing-push-dsp-playlist-marketing",
        "release-schedule-milestone-timelines-readiness-gates-delivery-commitment-pre-save-label-ops",
        "streaming-data-dsp-metrics-benchmark-comparable-cases-forecast-trajectory-data-analytics",
        "touring-schedule-venue-booking-marketing-campaign-social-rollout-concert-live-touring-marketing",
    ],
)
def test_release_strategist_consult_home_leads_and_cross_domains_present(query, cross):
    """
    release-strategist's home domain 'playlist_dsp' is always first; every
    expected cross-domain is present. Verifies home-first invariant and
    release-campaign orchestrator cross-domain routing quality.
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


def test_release_strategist_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped DSP strategy / Discover Weekly / algorithmic-add /
    independent-curator question (no keywords from legal / finance_royalties /
    marketing / fan_social / bizdev / label_ops / publishing / production /
    data_analytics / capital_funding / digital_ops / intelligence / management /
    ar / sync / controller / executive / live_touring) must return only the
    home domain with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
