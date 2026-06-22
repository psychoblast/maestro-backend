"""
Phase 3e — Per-agent deep consult test for mobile-monetize.

Scope: mobile-monetize only. Home domain "bizdev". Six realistic questions an
artist or their team would ask Mo (Monetization Specialist), covering: YouTube
AdSense revenue and royalty splits from streaming income, TikTok Creativity
Program campaign with social media content strategy and audience growth,
negotiating a brand partnership contract with a digital platform including
content rights, building a Patreon membership tier system with a superfan
community and direct-to-fan income, building a DSP platform strategy combining
algorithmic playlist pitching with brand partnership activation, and a
deliberately narrow YouTube Partner Program requirements question.

For each cross-domain question we assert:
  (a) mobile-monetize's home domain "bizdev" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped YouTube Partner Program eligibility /
payout-rates question that avoids keywords from legal, finance_royalties,
marketing, fan_social, live_touring, publishing, production, data_analytics,
capital_funding, digital_ops, intelligence, management, ar, sync, controller,
executive, playlist_dsp, or label_ops. NOTE: "revenue" contains the substring
"venue" (a live_touring keyword) — "income" is used instead.

Routing gap noted: mobile-monetize's SKILL.md (Mo) is rich in platform-specific
content — Bandcamp, Cameo, Twitch, NFT platforms — whose names carry no domain
keywords. These platforms are only reachable cross-domain via surrounding
conceptual keywords (e.g. "membership tier", "superfan") rather than by platform
name. This is CORRECT current behavior: the home domain "bizdev" covers the
business/partnership angle and keyword matching fills in cross-domain routing
when the question's language contains the right triggers. This test encodes the
CURRENT correct behavior without changing agent_home.py or shared files.

NOTE: "tiktok" and "instagram" are marketing keywords — any query naming these
platforms will cross-route to marketing. "youtube" is NOT a marketing keyword;
YouTube-specific questions stay home-only unless other marketing terms appear.
NOTE: "patreon" (lowercased) is a fan_social keyword — queries naming Patreon
intentionally pull in fan_social, which is correct for membership/community work.
NOTE: "playlist" alone fires marketing in addition to playlist_dsp.
NOTE: "partner " (with trailing space) fires bizdev via keyword and is a
substring of "Partner Program" (lowercased: "partner program") — covered by the
home domain dedup so it does not add a second bizdev entry.
NOTE: "rights" alone is a legal keyword — avoid in finance_royalties-only queries.
NOTE: "streaming income" fires finance_royalties; "streaming" alone does not.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "mobile-monetize"
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
        # bizdev:            home — agent mapping (no explicit bizdev keyword in
        #                    query; home_domain forces bizdev first)
        # finance_royalties: "royalt" (→ "royalty"), "splits" (→ "splits"),
        #                    "streaming income" (→ "streaming income")
        # NOTE: "youtube" is NOT a marketing keyword — this query stays clean
        #       with only finance_royalties as cross-domain.
        # NOTE: "AdSense" lowercases to "adsense" — "ad spend" is a marketing
        #       keyword but "ad spend" contains a space and "adsense" has no space,
        #       so there is no substring match. ✓
        "How do we maximize our YouTube AdSense revenue and understand the "
        "royalty splits and streaming income from our channel?",
        ["finance_royalties"],
    ),
    (
        # bizdev:    home — agent mapping
        # marketing: "tiktok", "campaign", "social media",
        #            "content strategy", "audience", "growth"
        # NOTE: "tiktok" is an explicit marketing keyword — any TikTok query
        #       cross-routes to marketing, which is sensible for Mo's work.
        "We want to launch a TikTok Creativity Program campaign and build a "
        "social media content strategy for audience growth.",
        ["marketing"],
    ),
    (
        # bizdev:  home — "brand" (→ "brand partnership") fires bizdev via
        #          keyword, deduplicates with home
        # legal:   "negotiat" (→ "negotiating"), "contract", "rights"
        # NOTE: "brand marketing" is a marketing keyword but "brand partnership"
        #       does NOT contain "brand marketing" as a substring. ✓
        # NOTE: "commercial partnership" is a bizdev keyword but our query uses
        #       "brand partnership" which matches the simpler "brand" keyword. ✓
        "We are negotiating a brand partnership contract with a digital platform "
        "for exclusive content monetization rights.",
        ["legal"],
    ),
    (
        # bizdev:     home — agent mapping
        # fan_social: "patreon" (→ "Patreon"), "membership tier",
        #             "superfan", "fan community" (substring of "superfan community"),
        #             "direct-to-fan"
        # NOTE: "Patreon" lowercases to "patreon" which is a fan_social keyword —
        #       intentionally cross-routes to fan_social for membership/community work.
        # NOTE: "income" alone does NOT fire finance_royalties; only "streaming income",
        #       "tour revenue", "show income", or "income split" do.
        "How do we build a Patreon membership tier system and grow our superfan "
        "community to generate direct-to-fan income?",
        ["fan_social"],
    ),
    (
        # bizdev:      home — "brand" (→ "brand partnership"), "activation",
        #              deduplicates with home
        # playlist_dsp: "dsp", "algorithmic playlist" (→ "algorithmic playlist
        #               pitching"), "playlist pitch" (substring of "playlist pitching")
        # NOTE: "playlist" is also a marketing keyword, so marketing may appear
        #       in the result alongside playlist_dsp — this test asserts only
        #       that playlist_dsp is present, not that marketing is absent.
        "How do we build a DSP platform strategy that combines algorithmic "
        "playlist pitching with brand partnership activation?",
        ["playlist_dsp"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped YouTube Partner Program eligibility / payout-rates question
# that returns ONLY "bizdev" (via home domain + "partner " keyword match on
# "Partner Program" lowercased to "partner program", where "partner " —
# partner+space — is a bizdev keyword substring of "partner program").
# Deliberately avoids:
# "contract"/"clause"/"rights"/"legal"/"negotiat"/"indemnit"/"warrant" (legal)
# "royalt"/"splits"/"split "/"advance"/"statement"/"accounting"/
#   "streaming income"/"tour revenue"/"income split" (finance_royalties)
# "marketing"/"campaign"/"audience"/"social media"/"tiktok"/"instagram"/
#   "content strategy"/"growth"/"rollout"/"follower"/"reach" (marketing)
#   NOTE: "youtube" is NOT a marketing keyword — YouTube-only questions are safe.
# "superfan"/"patreon"/"fan community"/"fan loyalty"/"membership tier"/
#   "direct-to-fan"/"d2c"/"fan engagement" (fan_social)
# "tour"/"touring"/"venue"/"concert"/"gig"/"booking"/"ticket"/"festival" (live_touring)
#   NOTE: "revenue" contains the substring "venue" → fires live_touring! Use
#         "income" instead of "revenue" to avoid this hidden substring trap.
# "publish"/"catalog"/"songwrit"/"co-write"/"administration" (publishing)
# "production"/"producer"/"studio"/"mixing"/"mastering"/"stems"/"lufs" (production)
# "analytics"/"metric"/"kpi"/"benchmark"/"forecast"/"streaming data"/"dsp metric" (data_analytics)
# "capital"/"fund"/"financ"/"invest"/"grant"/"equity" (capital_funding)
# "metadata"/"isrc"/"upc"/"ddex"/"dsp delivery"/"content id" (digital_ops)
#   NOTE: "upcoming" contains "upc" → digital_ops — excluded.
# "intelligence"/"market trend"/"industry trend"/"competitive" (intelligence)
# "artist manager"/"management"/"managing the artist"/"manage a career" (management)
# "scouting"/"unsigned"/"a&r"/"emerging artist"/"discovery" (ar)
# "sync"/"licens"/"placement"/"film"/"tv" (sync)
#   NOTE: "tv" is 2 chars; "payout" does not contain "tv". ✓
# "reconcil"/"ledger"/"controller"/"close the books" (controller)
# "executive"/"ceo"/"go/no-go"/"build vs buy" (executive)
# "playlist"/"dsp"/"editorial"/"airplay" (playlist_dsp / marketing via "playlist")
# "release planning"/"release campaign"/"delivery commitment"/"distributor" (label_ops)
#
# "partner " in "Partner Program" (lowercased: "partner program") → bizdev
# keyword match, deduplicates with home. ✓

_NARROW_QUERY = (
    "What are the channel subscriber count and ad income payout rates "
    "for the YouTube Partner Program?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "youtube-adsense-royalty-splits-streaming-income-finance-royalties",
        "tiktok-creativity-program-campaign-social-media-content-strategy-audience-growth-marketing",
        "brand-partnership-contract-digital-platform-content-rights-negotiating-legal",
        "patreon-membership-tier-superfan-community-direct-to-fan-fan-social",
        "dsp-algorithmic-playlist-pitching-brand-partnership-activation-playlist-dsp",
    ],
)
def test_mobile_monetize_consult_home_leads_and_cross_domains_present(query, cross):
    """
    mobile-monetize's home domain 'bizdev' is always first; every expected
    cross-domain is present. Verifies home-first invariant and platform
    monetization specialist cross-domain routing quality.
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


def test_mobile_monetize_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped YouTube Partner Program eligibility / payout-rates
    question (no keywords from legal / finance_royalties / marketing /
    fan_social / live_touring / publishing / production / data_analytics /
    capital_funding / digital_ops / intelligence / management / ar / sync /
    controller / executive / playlist_dsp / label_ops) must return only the
    home domain with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
