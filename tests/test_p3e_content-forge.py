"""
Phase 3e — Per-agent deep consult test for content-forge.

Scope: content-forge only. Home domain "marketing". Five realistic
cross-domain questions an artist or their team would ask Pen (Content Creation
specialist), covering: press release for a sync placement in a TV advert, artist
bio that references a songwriting catalog deal and co-write credits, brand
partnership sponsored content package, EPK assembled for a label deal
negotiation with legal rights framing, and fan newsletter plus behind-the-scenes
copy for a superfan tier. Plus one deliberately narrow bio-and-captions question
that returns home-only with no spurious cross-domain.

For each cross-domain question we assert:
  (a) content-forge's home domain "marketing" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure copywriting question (bio + captions) that avoids
keywords from sync, publishing, bizdev, legal, label_ops, fan_social,
finance_royalties, live_touring, production, data_analytics, playlist_dsp,
digital_ops, capital_funding, executive, management, intelligence, controller,
or any other domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "content-forge"
_HOME  = "marketing"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "marketing" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.
# NOTE: "upcoming" triggers digital_ops via "upc" substring — use "next" instead.
# NOTE: "composition" triggers publishing — avoid in non-publishing queries.
# NOTE: "catalog" triggers publishing (bare keyword) — intentional in query 2 only.
# NOTE: "recording session" is the production keyword; bare "recordings" does NOT
#       trigger production — verified in query 4's recording-ownership context.

DEEP_CONSULT_MATRIX = [
    (
        # marketing:  home — always leads (also "reach" via "maximize reach")
        # sync:       "sync" (direct), "placement" (direct), "tv" (via "TV advert"),
        #             "advert" (direct)
        "We need to write a press release for our song that just landed a sync "
        "placement in a TV advert — what details should we lead with to maximize "
        "reach and media pickup?",
        ["sync"],
    ),
    (
        # marketing:  home — always leads
        # publishing: "songwrit" (via "songwriting"), "catalog" (direct in keyword list),
        #             "co-write" (direct), "publish" (via "publishing")
        "We need an artist bio that mentions our songwriting catalog deal and "
        "co-write credits with other producers — how should we frame the "
        "publishing background in the narrative?",
        ["publishing"],
    ),
    (
        # marketing:  home — always leads
        # bizdev:     "brand" (multiple), "sponsor" (via "sponsored"),
        #             "partnership" (direct)
        "A fashion brand wants to collaborate with us on a sponsored content "
        "package — captions, a press kit, and social posts promoting the brand "
        "partnership. How do we write copy that satisfies their brand guidelines "
        "and our artistic voice?",
        ["bizdev"],
    ),
    (
        # marketing:  home — always leads
        # legal:      "contract" (via "contracts"), "legal" (via "legal rights"),
        #             "rights" (direct), "copyright" (direct),
        #             "negotiat" (via "negotiation")
        # label_ops:  "label deal" (exact phrase)
        "We are putting together an EPK for a label deal negotiation — what "
        "contracts and legal rights should the bio section address, and how do "
        "we frame the copyright ownership of our recordings in the press kit?",
        ["legal", "label_ops"],
    ),
    (
        # marketing:  home — always leads
        # fan_social: "newsletter" (direct), "behind-the-scenes content" (exact phrase),
        #             "superfan tier" (exact phrase), "fan community" (exact phrase)
        "We want to write a fan newsletter series and create behind-the-scenes "
        "content updates for our superfan tier — how should we tailor the copy "
        "for fan community engagement?",
        ["fan_social"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped copywriting question (bio + captions for platform profiles)
# that returns ONLY "marketing" (via home domain). Deliberately avoids:
# "sync" / "licens" / "placement" / "film" / "tv" / "advert" / "commercial" (sync)
# "publish" / "songwrit" / "co-write" / "catalog" / "catalogue" (publishing)
# "brand" / "sponsor" / "partner " / "endorsement" / "merchandise" (bizdev)
# "contract" / "rights" / "copyright" / "legal" / "clause" / "negotiat" (legal)
# "label deal" / "release plan" / "distributor" / "recoup" (label_ops)
# "newsletter" / "superfan" / "behind-the-scenes content" / "fan community"
#   / "fan engagement" / "fan club" (fan_social)
# "royalt" / "advance" / "splits" / "mechanical" / "income split" (finance_royalties)
# "tour" / "stage" / "concert" / "venue" / "festival" (live_touring)
# "production" / "producer" / "mixing" / "studio" / "recording session" (production)
# "analytics" / "metric" / "kpi" / "streaming data" (data_analytics)
# "playlist" / "dsp" / "editorial" / "pre-save" (playlist_dsp)
# "metadata" / "isrc" / "upc" / "ddex" (digital_ops) — also avoids "upcoming"
# "capital" / "fund" / "invest" / "grant" (capital_funding)
# "executive" / "ceo" / "strategic" (executive)
# "artist manager" / "management agreement" / "commission" (management)
# "intelligence" / "market trend" / "competitive landscape" (intelligence)
# "controller" / "reconcil" / "ledger" / "journal entry" (controller)

_NARROW_QUERY = (
    "We need to write a punchy 150-word Instagram bio and eye-catching captions "
    "for our artist's profile pages."
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "press-release-sync-placement-tv-advert",
        "artist-bio-songwriting-catalog-co-write-publishing",
        "brand-partnership-sponsored-content-package",
        "epk-label-deal-negotiation-legal-rights-copyright",
        "fan-newsletter-superfan-tier-behind-the-scenes-community",
    ],
)
def test_content_forge_consult_home_leads_and_cross_domains_present(query, cross):
    """
    content-forge's home domain 'marketing' is always first; every expected
    cross-domain is present. Verifies home-first invariant and content creation
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


def test_content_forge_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped bio-and-captions copywriting question (no keywords from
    sync / publishing / bizdev / legal / label_ops / fan_social /
    finance_royalties / live_touring / production / data_analytics /
    playlist_dsp / digital_ops / capital_funding / executive / management /
    intelligence / or controller) must return only the home domain with no
    spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
