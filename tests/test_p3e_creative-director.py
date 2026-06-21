"""
Phase 3e — Per-agent deep consult test for creative-director.

Scope: creative-director only. Home domain "marketing". Six realistic
questions an artist or their team would ask Cree (Creative Director), covering:
album rollout tease activation with superfan community content, sync licensing
visual asset kit for music supervisors, DSP editorial playlist pitch for the
release reveal phase, summer album campaign tied to live tour and festival season,
brand deal and merchandise alignment with the release rollout, and a deliberately
narrow release format / seasonal timing question.

For each cross-domain question we assert:
  (a) creative-director's home domain "marketing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure release format / seasonal timing question that avoids
keywords from fan_social, sync, playlist_dsp, live_touring, bizdev, digital_ops,
data_analytics, legal, finance_royalties, publishing, production, label_ops,
or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "creative-director"
_HOME  = "marketing"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "marketing" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.
# NOTE: "upcoming" triggers digital_ops via "upc" substring — use "next" instead.
# NOTE: "composition" triggers publishing — use "sonic world" or "sonic direction" instead.
# NOTE: "catalog" triggers publishing and label_ops — omit from narrow query.

DEEP_CONSULT_MATRIX = [
    (
        # marketing:  home — always leads (also "rollout", "campaign", "content strategy")
        # fan_social: "fan community", "behind-the-scenes content",
        #             "superfan tier", "fan engagement", "fan loyalty",
        #             "owned channel" (via "owned channels")
        "We are building the Phase 1 tease of our album rollout and want to "
        "activate our fan community — how do we design exclusive "
        "behind-the-scenes content for our superfan tier, build fan engagement "
        "through the reveal phase, and grow fan loyalty across our owned "
        "channels throughout the campaign?",
        ["fan_social"],
    ),
    (
        # marketing:  home — always leads (also "campaign")
        # sync:       "sync licensing", "music supervisor",
        #             "film", "television", "placement"
        "We have a visual identity established for our next release — how do we "
        "adapt our album artwork, press photography, and campaign imagery to "
        "create a sync licensing asset kit suitable for music supervisor review, "
        "with assets ready for film and television placement opportunities?",
        ["sync"],
    ),
    (
        # marketing:  home — always leads (also "rollout", "release strategy")
        # playlist_dsp: "dsp" (via "DSP editorial"), "editorial" (via "editorial
        #               playlists" and "editorial consideration"), "playlist
        #               placement", "streaming platform"
        # NOTE: avoids "upcoming" (triggers digital_ops "upc")
        "We are planning the release reveal phase and need to pitch our single "
        "to DSP editorial playlists — what cover art direction, visual "
        "storytelling approach, and rollout timing give us the best chance of "
        "editorial consideration and playlist placement on major streaming "
        "platforms?",
        ["playlist_dsp"],
    ),
    (
        # marketing:  home — always leads (also "campaign", "rollout")
        # live_touring: "tour" (via "a tour"), "festival" (via "festival season"),
        #               "stage" (via "stage aesthetic"), "concert" (via "concert
        #               experience")
        "We are planning a summer album release that aligns with a tour — how "
        "do we build a rollout that creates momentum into festival season, ties "
        "our album's visual identity to the stage aesthetic and concert "
        "experience, and sustains the campaign across all tour dates?",
        ["live_touring"],
    ),
    (
        # marketing:  home — always leads (also "campaign", "rollout",
        #             "brand marketing")
        # bizdev:     "brand deal", "merchandise" (x2), "brand" (multiple),
        #             "partnership"
        "We have secured a brand deal with a fashion label for our album release "
        "campaign — how do we align our merchandise line, the brand's visual "
        "identity, and the release rollout to create a cohesive campaign that "
        "serves both the music and the brand partnership?",
        ["bizdev"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped release format and seasonal timing question that returns
# ONLY "marketing" (via home domain). Deliberately avoids:
# "fan community" / "superfan" / "behind-the-scenes content" /
#   "fan engagement" / "fan loyalty" / "owned channel" (fan_social)
# "sync" / "licens" / "placement" / "film" / "tv" / "music supervisor" (sync)
# "playlist" / "dsp" / "editorial" / "streaming platform" / "pre-save" (playlist_dsp)
# "tour" / "stage" / "concert" / "festival" / "venue" (live_touring)
# "brand" / "merch" / "merchandise" / "sponsor" / "endorsement" / "partnership"
#   (bizdev)
# "colorspace" / "metadata" / "artwork spec" / "isrc" / "upc" / "delivery spec"
#   (digital_ops) — also avoids "upcoming" (contains "upc")
# "analytics" / "metric" / "kpi" / "streaming data" (data_analytics)
# "contract" / "rights" / "copyright" / "legal" (legal)
# "royalt" / "mechanical" / "splits" / "advance" (finance_royalties)
# "publish" / "catalog" / "composition" / "songwrit" (publishing)
# "production" / "mixing" / "mastering" / "studio" / "arrangement" (production)
# "release plan" / "release campaign" / "release cadence" / "distributor" /
#   "release schedule" / "label ops" (label_ops)
# "intelligence" / "market trend" / "competitive landscape" (intelligence)

_NARROW_QUERY = (
    "What is the ideal release format — single, EP, or album — for an "
    "independent artist with four finished tracks in the same sonic direction, "
    "and which seasonal timing gives the strongest momentum for a debut project "
    "in the spring or fall?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "fan-community-superfan-tier-rollout-tease-owned-channels",
        "sync-licensing-visual-asset-kit-music-supervisors-film-television",
        "dsp-editorial-playlist-release-reveal-streaming-platforms",
        "summer-tour-festival-album-campaign-stage-concert-visual-identity",
        "brand-deal-merchandise-campaign-fashion-partnership-rollout",
    ],
)
def test_creative_director_consult_home_leads_and_cross_domains_present(query, cross):
    """
    creative-director's home domain 'marketing' is always first; every expected
    cross-domain is present. Verifies home-first invariant and creative director
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


def test_creative_director_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped release format / seasonal timing question (no keywords
    from fan_social / sync / playlist_dsp / live_touring / bizdev / digital_ops /
    data_analytics / legal / finance_royalties / publishing / production /
    label_ops / or intelligence) must return only the home domain with no
    spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
