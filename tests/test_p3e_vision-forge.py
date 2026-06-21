"""
Phase 3e — Per-agent deep consult test for vision-forge.

Scope: vision-forge only. Home domain "marketing". Six realistic
questions an artist or their team would ask Luna (AI Visuals), covering:
AI-generated visual press kit for a sync licensing pitch, brand sponsorship
visual identity package, DSP editorial playlist cover art, album artwork
delivery colorspace and spec QC, fan community AI-generated visual content
library, and a deliberately narrow AI tools / prompt style question.

For each cross-domain question we assert:
  (a) vision-forge's home domain "marketing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure AI image-tool and visual-prompt question that avoids
keywords from sync, bizdev, playlist_dsp, digital_ops, fan_social,
data_analytics, legal, finance_royalties, publishing, live_touring,
production, label_ops, or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "vision-forge"
_HOME  = "marketing"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "marketing" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # marketing:  home — always leads
        # sync:       "sync" (via "sync licensing"), "licens" (via "licensing"),
        #             "placement", "music supervisor", "tv", "film", "television"
        "We need a complete AI-generated visual press kit for our sync licensing "
        "pitch — album artwork, promotional imagery, and campaign assets designed "
        "for music supervisors and TV placement opportunities across film and "
        "television productions.",
        ["sync"],
    ),
    (
        # marketing:  home — always leads
        # bizdev:     "brand" (multiple), "sponsor" (via "sponsorship"),
        #             "endorsement", "partnership"
        "We are developing AI-generated visual brand materials and a visual "
        "identity package for a major clothing brand sponsorship deal — how do "
        "we create artwork that aligns with the sponsor's brand guidelines while "
        "maintaining our endorsement partnership's authenticity?",
        ["bizdev"],
    ),
    (
        # marketing:  home — always leads
        # playlist_dsp: "dsp", "editorial" (via "editorial playlist" and
        #               "editorial consideration"), "playlist", "playlist add"
        "We need AI-generated album cover artwork optimized for DSP editorial "
        "playlist pitching — what visual styles, aspect ratios, and image quality "
        "standards give our release the best chance of editorial consideration "
        "and a playlist add?",
        ["playlist_dsp"],
    ),
    (
        # marketing:  home — always leads
        # digital_ops: "colorspace", "artwork spec", "metadata",
        #              "pre-delivery qc" (via "pre-delivery QC"),
        #              "redelivery"
        "We are preparing AI-generated album artwork for distribution upload and "
        "need to understand colorspace requirements, artwork spec standards, and "
        "metadata tagging so cover images pass pre-delivery QC without rejection "
        "or redelivery.",
        ["digital_ops"],
    ),
    (
        # marketing:  home — always leads
        # fan_social: "fan community", "behind-the-scenes content", "superfan",
        #             "fan engagement", "fan loyalty", "owned channel"
        #             (via "owned channels")
        "We want to build an AI-generated visual content library to support our "
        "fan community — including behind-the-scenes content, exclusive artwork "
        "for our superfan tier, and social identity visuals that strengthen fan "
        "engagement and fan loyalty across our owned channels.",
        ["fan_social"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped AI image-tool and visual-prompt question that returns
# ONLY "marketing" (via home domain). Keywords triggered: none from other
# domains. Deliberately avoids:
# "sync" / "licens" / "placement" / "film" / "tv" / "music supervisor" (sync)
# "brand" / "sponsor" / "endorsement" / "partnership" (bizdev)
# "playlist" / "dsp" / "editorial" / "pre-save" (playlist_dsp)
# "colorspace" / "metadata" / "artwork spec" / "isrc" / "delivery spec" (digital_ops)
# "fan community" / "superfan" / "behind-the-scenes content" /
#   "fan engagement" / "fan loyalty" (fan_social)
# "analytics" / "metric" / "kpi" / "streaming data" (data_analytics)
# "contract" / "rights" / "copyright" / "legal" (legal)
# "royalt" / "mechanical" / "splits" (finance_royalties)
# "publish" / "catalog" / "songwrit" (publishing)
# "tour" / "concert" / "venue" (live_touring)
# "production" / "mixing" / "mastering" / "studio" (production)
# "label ops" / "distribution" / "release plan" / "release cadence" (label_ops)
# "intelligence" / "market intelligence" (intelligence)

_NARROW_QUERY = (
    "What AI image generation tools and visual prompt styles work best for "
    "creating album artwork, press photo sets, and video thumbnail imagery "
    "that match an artist's aesthetic and creative direction?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "sync-licensing-visual-press-kit-music-supervisors",
        "brand-sponsorship-visual-identity-endorsement-deal",
        "dsp-editorial-playlist-cover-art-submission",
        "album-artwork-colorspace-metadata-pre-delivery-qc",
        "fan-community-visual-content-superfan-tier-owned-channels",
    ],
)
def test_vision_forge_consult_home_leads_and_cross_domains_present(query, cross):
    """
    vision-forge's home domain 'marketing' is always first; every expected
    cross-domain is present. Verifies home-first invariant and AI visuals
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


def test_vision_forge_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped AI image-tool and visual-prompt question (no keywords
    from sync / bizdev / playlist_dsp / digital_ops / fan_social /
    data_analytics / legal / finance_royalties / publishing / live_touring /
    production / label_ops / or intelligence) must return only the home
    domain with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
