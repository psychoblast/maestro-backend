"""
Phase 3e — Per-agent deep consult test for design-studio.

Scope: design-studio only. Home domain "marketing". Six realistic
questions an artist or their team would ask Diego (Brand Designer), covering:
merch design direction and brand identity, album artwork for DSP editorial
playlist pitching, stage and live-show visual direction for touring, fan
community visual content strategy, sync licensing visual asset kit, and
a deliberately narrow visual identity / typography question.

For each cross-domain question we assert:
  (a) design-studio's home domain "marketing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure visual identity / typography question that avoids
keywords from bizdev, playlist_dsp, live_touring, fan_social, sync,
digital_ops, data_analytics, legal, finance_royalties, publishing,
production, label_ops, or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "design-studio"
_HOME  = "marketing"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "marketing" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.
# NOTE: "upcoming" triggers digital_ops via "upc" substring — use "next" instead.
# NOTE: "composition" triggers publishing — use "framing" instead.

DEEP_CONSULT_MATRIX = [
    (
        # marketing:  home — always leads
        # bizdev:     "merch" (via "merch design"), "merchandise" (x2),
        #             "brand" (via "brand identity")
        "We need merch design direction that aligns with our brand identity — "
        "how do we develop merchandise artwork and product visuals that extend "
        "our visual identity consistently across clothing, accessories, and "
        "limited-edition merchandise items?",
        ["bizdev"],
    ),
    (
        # marketing:  home — always leads
        # playlist_dsp: "dsp" (via "DSP release"), "editorial playlist",
        #               "editorial consideration", "streaming platform"
        # NOTE: avoids "upcoming" (triggers digital_ops "upc") and
        # "composition" (triggers publishing)
        "We are directing album artwork for our next DSP release and want to "
        "understand what visual qualities — image framing, contrast, and color "
        "palette — give cover art the best chance of standing out in editorial "
        "playlist consideration on major streaming platforms.",
        ["playlist_dsp"],
    ),
    (
        # marketing:  home — always leads
        # live_touring: "tour" (via "next tour"), "stage" (via "stage backdrop"),
        #               "concert", "festival"
        # NOTE: avoids "upcoming" (triggers digital_ops "upc")
        "We need visual direction for our artist's next tour — how do we design "
        "a cohesive stage backdrop, LED screen content, and wardrobe direction "
        "that aligns with the album's visual identity for festival and concert "
        "appearances?",
        ["live_touring"],
    ),
    (
        # marketing:  home — always leads (also "content strategy")
        # fan_social: "fan community", "behind-the-scenes content",
        #             "superfan tier", "fan engagement", "fan loyalty",
        #             "owned channel" (via "owned channels")
        "How do we build a visual content strategy for our fan community — "
        "including exclusive behind-the-scenes content for our superfan tier, "
        "social identity graphics, and visual storytelling assets that "
        "strengthen fan engagement and grow fan loyalty across our owned channels?",
        ["fan_social"],
    ),
    (
        # marketing:  home — always leads (also "campaign")
        # sync:       "sync" (via "sync licensing"), "licens" (via "licensing"),
        #             "placement", "music supervisor", "film", "television",
        #             "advert" (via "advertising")
        "We have a sync licensing pitch opportunity and need visual assets — "
        "a stylized press photo set, campaign imagery, and album artwork "
        "designed for music supervisor review and placement opportunities "
        "across film, television, and advertising.",
        ["sync"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped visual identity / typography question that returns
# ONLY "marketing" (via home domain). Deliberately avoids:
# "brand" / "merch" / "merchandise" / "sponsor" / "endorsement" (bizdev)
# "dsp" / "playlist" / "editorial" / "streaming platform" (playlist_dsp)
# "tour" / "stage" / "concert" / "festival" / "venue" (live_touring)
# "fan community" / "superfan" / "behind-the-scenes content" /
#   "fan engagement" / "fan loyalty" / "owned channel" (fan_social)
# "sync" / "licens" / "placement" / "film" / "tv" / "music supervisor" (sync)
# "colorspace" / "metadata" / "artwork spec" / "isrc" / "delivery spec" (digital_ops)
# "analytics" / "metric" / "kpi" / "streaming data" (data_analytics)
# "contract" / "rights" / "copyright" / "legal" (legal)
# "royalt" / "mechanical" / "splits" (finance_royalties)
# "publish" / "catalog" / "composition" / "songwrit" (publishing)
# "production" / "mixing" / "mastering" / "studio" (production)
# "upcoming" — triggers digital_ops via "upc" substring — excluded here
# "label ops" / "distribution" / "release plan" (label_ops)
# "intelligence" / "market trend" (intelligence)

_NARROW_QUERY = (
    "What primary color palette, typography choices, and photography style "
    "work best for an R&B artist developing a consistent visual identity "
    "across album covers, press photos, and social media imagery?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "merch-design-brand-identity-merchandise-artwork",
        "dsp-editorial-playlist-album-cover-art-streaming-platforms",
        "stage-backdrop-led-screen-tour-festival-concert-visual-direction",
        "fan-community-visual-content-superfan-tier-owned-channels",
        "sync-licensing-visual-asset-kit-music-supervisors-film-tv",
    ],
)
def test_design_studio_consult_home_leads_and_cross_domains_present(query, cross):
    """
    design-studio's home domain 'marketing' is always first; every expected
    cross-domain is present. Verifies home-first invariant and brand designer
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


def test_design_studio_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped visual identity / typography question (no keywords from
    bizdev / playlist_dsp / live_touring / fan_social / sync / digital_ops /
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
