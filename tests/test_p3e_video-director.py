"""
Phase 3e — Per-agent deep consult test for video-director.

Scope: video-director only. Home domain "marketing". Five realistic
cross-domain questions an artist or their team would ask Reel (Music Video
Specialist), covering: music video as a sync pitch for film and TV placement,
director contract with work-for-hire rights, label video budget advance and
royalty recoupment, brand sponsorship of the shoot combined with a sync pitch
for TV advertisements, and behind-the-scenes content for fan community
engagement. Plus one deliberately narrow director-selection question that
returns home-only with no spurious cross-domain.

For each cross-domain question we assert:
  (a) video-director's home domain "marketing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure director-selection and treatment-planning question that
avoids keywords from sync, legal, finance_royalties, bizdev, fan_social,
data_analytics, publishing, live_touring, production, label_ops, management,
or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "video-director"
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
        # sync:       "sync" (direct), "film", "tv", "placement" — all in sync keywords
        "We're planning a music video that will double as a sync pitch for film "
        "and TV placement — what treatment approach maximises the sync placement "
        "chances?",
        ["sync"],
    ),
    (
        # marketing:  home — always leads
        # legal:      "contract", "work-for-hire" (hyphenated form in legal keywords),
        #             "rights", "clause" — all in legal keywords;
        #             "master footage" does NOT contain "master use" as substring
        "We need to sign a contract with our director covering work-for-hire rights "
        "and master footage ownership — what clauses are critical to protect us?",
        ["legal"],
    ),
    (
        # marketing:  home — always leads
        # finance_royalties: "advance", "royalt" (via "royalty"), "recoup"
        #                    (via "recoupment"), "income split" (via "income splits")
        "The label is providing a $40k video budget advance and we need to "
        "understand royalty recoupment — how are the income splits calculated "
        "after the advance recoups?",
        ["finance_royalties"],
    ),
    (
        # marketing:  home — always leads
        # bizdev:     "brand" (multiple), "sponsor" (via "sponsor our")
        # sync:       "sync", "placement", "tv", "advert" (via "advertisements")
        "A fashion brand wants to sponsor our music video shoot and we want to "
        "pitch the finished video for sync placements in TV advertisements.",
        ["bizdev", "sync"],
    ),
    (
        # marketing:  home — always leads
        # fan_social: "behind-the-scenes content" (exact phrase in fan_social
        #             keywords), "fan community" (exact phrase), "fan engagement"
        #             (via "fan community engagement"), "superfan tier" (exact
        #             phrase), "newsletter" (via "fan newsletter audience")
        "We want to create a behind-the-scenes content series from our music video "
        "shoot to strengthen fan community engagement, grow our superfan tier, and "
        "build our fan newsletter audience.",
        ["fan_social"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped director-selection and treatment-planning question that
# returns ONLY "marketing" (via home domain). Deliberately avoids:
# "sync" / "film" / "tv" / "placement" / "licens" / "advert" / "trailer"
#   / "music supervisor" (sync)
# "brand" / "sponsor" / "partner " / "endorsement" (bizdev)
# "contract" / "rights" / "clause" / "legal" / "copyright" / "work for hire" (legal)
# "royalt" / "recoup" / "advance" / "splits" / "income split" (finance_royalties)
# "behind-the-scenes content" / "fan community" / "superfan" / "newsletter"
#   / "fan engagement" / "fan club" (fan_social)
# "production" / "producer" / "mixing" / "studio" / "recording" (production)
# "tour" / "stage" / "venue" / "concert" / "festival" / "performance fee" (live_touring)
# "publish" / "catalog" / "songwrit" / "composition" (publishing)
# "analytics" / "metric" / "kpi" / "streaming data" (data_analytics)
# "label ops" / "release plan" / "distribution" (label_ops)
# "artist manager" / "management" / "commission" (management)
# "intelligence" / "market intelligence" (intelligence)
# "playlist" / "dsp" / "editorial" (playlist_dsp)

_NARROW_QUERY = (
    "We need to choose the right director and plan the creative treatment "
    "for our next music video."
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "sync-pitch-film-tv-placement-treatment",
        "director-contract-work-for-hire-footage-rights",
        "label-advance-royalty-recoupment-income-splits",
        "brand-sponsor-shoot-sync-tv-advertisements",
        "behind-the-scenes-fan-community-superfan-newsletter",
    ],
)
def test_video_director_consult_home_leads_and_cross_domains_present(query, cross):
    """
    video-director's home domain 'marketing' is always first; every expected
    cross-domain is present. Verifies home-first invariant and music video
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


def test_video_director_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped director-selection and treatment-planning question (no
    keywords from sync / legal / finance_royalties / bizdev / fan_social /
    production / live_touring / publishing / data_analytics / label_ops /
    management / intelligence / or playlist_dsp) must return only the home
    domain with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
