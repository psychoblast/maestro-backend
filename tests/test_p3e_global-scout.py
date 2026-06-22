"""
Phase 3e — Per-agent deep consult test for global-scout.

Scope: global-scout only. Home domain "ar". Six realistic questions an artist
or their team would ask Nova (International Markets Specialist), covering: TV
commercial sync licensing in the UK market, a Japan/South Korea festival tour
with promoter contract review, foreign PRO registration and sub-publishing
administration to collect royalties globally, a global Instagram/TikTok
marketing campaign for audience growth, a DSP editorial playlist strategy
across new markets, and a deliberately narrow question about top foreign
markets for a hip-hop artist.

For each cross-domain question we assert:
  (a) global-scout's home domain "ar" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped question about top foreign markets that
avoids all domain keywords.

NOTE: "ern" is a digital_ops keyword (DDEX standard name). ANY word
containing the substring "ern" — including "international" and
"internationally" — fires digital_ops as an unintended cross-domain. Queries
in this file are crafted to avoid "international"/"internationally" (using
"global", "foreign", or territory names directly) to prevent this spurious
routing. This is an existing brain.py keyword trap, not a bug in this file.
It is encoded here as a routing gap to flag.

ROUTING GAP: The keyword "ern" in digital_ops fires on "international" /
"internationally" as substring matches. global-scout's natural vocabulary
("entering the UK market", "international deals", "international touring") is
therefore a spurious trigger for digital_ops. This is CURRENT correct behavior
(no shared files changed), but a future tightening of the "ern" keyword to
require word-boundary context (e.g. "ddex ern", "ern message") would eliminate
the false positive. This test encodes the CURRENT correct behavior.

ROUTING GAP: global-scout's SKILL.md names territory-specific PROs (GEMA,
SACEM, GHAMRO, STIM, SAMI, APRA AMCOS) that carry no brain.py keywords. A
question specifically naming "GEMA" or "SACEM" will not cross-route to
publishing by PRO name alone — broader language ("performance rights",
"administration", "sub-publish") is required to pull in the publishing domain.
This is CURRENT correct behavior.

NOTE: "tv" is a sync keyword — any query referencing a TV placement fires
sync, which is correct for Nova's international sync work.
NOTE: "performance rights" fires publishing (not just legal or
finance_royalties) because it is an explicit publishing keyword.
NOTE: "rights" alone fires legal; avoid in queries where only publishing /
finance_royalties cross-domain is intended.
NOTE: "catalog" fires publishing — helpful when asking about PRO registration
for a full back catalog.
NOTE: "playlist" fires both playlist_dsp and marketing as substring matches.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "global-scout"
_HOME  = "ar"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "ar" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # ar:   home — agent mapping (home forced first, no ar keyword needed)
        # sync: "tv" (→ "TV commercial"), "placement" (→ "placement"),
        #       "licens" (→ "licensing")
        # NOTE: "tv commercial" does NOT match "commercial spot" (a sync keyword)
        #       because "commercial spot" is not in "tv commercial placement";
        #       "tv" alone is sufficient to fire sync.
        # NOTE: "market" does NOT match "market entry" (executive keyword) because
        #       "UK market" does not contain the full phrase "market entry". ✓
        "Our music has been selected for a TV commercial placement and sync "
        "licensing deal in the UK market.",
        ["sync"],
    ),
    (
        # ar:          home — agent mapping
        # legal:       "contract" (→ "contracts")
        # live_touring: "tour" (→ "tour"), "festival" (→ "festival appearances"),
        #               "festival appearance" (→ "festival appearances"),
        #               "promoter" (→ "promoter")
        # NOTE: catalog order — legal (index 4) precedes live_touring (index 5),
        #       so legal appears before live_touring in the result list.
        # NOTE: "signing" (as in "before signing") does NOT match "new signing"
        #       (ar keyword) because "before signing" does not contain the full
        #       phrase "new signing". ✓
        "We want to tour Japan and South Korea with festival appearances and "
        "need to review the promoter contracts before signing.",
        ["legal", "live_touring"],
    ),
    (
        # ar:               home — agent mapping
        # legal:            "rights" (→ "rights organizations")
        # publishing:       "catalog" (→ "catalog"), "performance rights" (→
        #                   "performance rights organizations"), "sub-publish" (→
        #                   "sub-publishing"), "administration" (→ "administration")
        # finance_royalties: "royalt" (→ "royalties")
        # NOTE: max_domains=4 → ["ar", "legal", "publishing", "finance_royalties"]
        #       all fit within the cap.
        # NOTE: "globally" does NOT contain "ern" → digital_ops stays silent. ✓
        # NOTE: "foreign" does NOT contain "ern" → digital_ops stays silent. ✓
        "We need to register our catalog with foreign performance rights "
        "organizations and set up sub-publishing administration to collect "
        "our royalties globally.",
        ["legal", "publishing", "finance_royalties"],
    ),
    (
        # ar:        home — agent mapping
        # marketing: "instagram" (→ "Instagram"), "tiktok" (→ "TikTok"),
        #            "marketing" (→ "marketing"), "campaign" (→ "campaign"),
        #            "audience" (→ "audience"), "fanbase" (→ "fanbase")
        # NOTE: "global" is NOT a domain keyword — it does not fire executive
        #       or any other domain. ✓
        "We want to launch an Instagram and TikTok marketing campaign to grow "
        "our global audience and fanbase.",
        ["marketing"],
    ),
    (
        # ar:          home — agent mapping
        # marketing:   "playlist" (→ "editorial playlists")
        # playlist_dsp: "dsp" (→ "DSP"), "editorial playlist" (→ "editorial
        #               playlists"), "playlist" (→ "editorial playlists")
        # NOTE: "playlist" fires both marketing (index 1) and playlist_dsp (index
        #       18) — both appear in the result with marketing leading due to
        #       catalog order. This test asserts only that playlist_dsp is present,
        #       not that marketing is absent.
        # NOTE: "new markets" does NOT contain "market entry" → executive stays
        #       silent. ✓
        "How do we build a DSP strategy and pitch our release to global "
        "editorial playlists to grow our streams across new markets?",
        ["marketing", "playlist_dsp"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped market-priority question for a hip-hop artist that returns
# ONLY "ar" (via home domain) with no spurious cross-domain routing.
# Deliberately avoids:
# "international" / "internationally" (contain "ern" → digital_ops)
# "contract"/"clause"/"rights"/"legal"/"negotiat" (legal)
# "royalt"/"splits"/"split "/"advance"/"statement"/"accounting" (finance_royalties)
# "marketing"/"campaign"/"audience"/"social media"/"tiktok"/"instagram"/"growth"
#   (marketing)
# "tour"/"concert"/"venue"/"festival"/"promoter"/"ticket" (live_touring)
# "publish"/"catalog"/"administration"/"sub-publish" (publishing)
# "production"/"producer"/"studio"/"mixing"/"mastering" (production)
# "analytics"/"metric"/"kpi"/"forecast"/"streaming data" (data_analytics)
# "capital"/"fund"/"financ"/"invest"/"grant" (capital_funding)
# "metadata"/"isrc"/"upc"/"distributor"/"delivery" (digital_ops)
#   NOTE: avoid "international" — contains substring "ern" → digital_ops fires
# "intelligence"/"market trend"/"music market"/"industry trend" (intelligence)
# "artist manager"/"management"/"manage" (management)
# "sync"/"licens"/"placement"/"film"/"tv" (sync)
# "executive"/"market entry"/"business strategy"/"should we sign" (executive)
# "superfan"/"fan community"/"patreon"/"membership tier" (fan_social)
# "playlist"/"dsp"/"editorial"/"airplay" (playlist_dsp / marketing via "playlist")
# "label ops"/"release planning"/"distribution deal"/"recording contract" (label_ops)
# "controller"/"ledger"/"reconcil"/"close the books" (controller)
#
# "breaking" does NOT match "breakout" (ar keyword) — different strings. ✓
# "foreign" does NOT contain "ern" → digital_ops stays silent. ✓

_NARROW_QUERY = (
    "What are the top foreign markets for breaking a hip-hop artist "
    "beyond their home country?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "uk-market-tv-commercial-placement-sync-licensing-sync",
        "japan-south-korea-festival-tour-promoter-contracts-legal-live-touring",
        "catalog-foreign-pro-registration-sub-publishing-administration-royalties-legal-publishing-finance-royalties",
        "instagram-tiktok-marketing-campaign-global-audience-fanbase-marketing",
        "dsp-editorial-playlists-global-streams-new-markets-marketing-playlist-dsp",
    ],
)
def test_global_scout_consult_home_leads_and_cross_domains_present(query, cross):
    """
    global-scout's home domain 'ar' is always first; every expected cross-domain
    is present. Verifies home-first invariant and international markets
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


def test_global_scout_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped question about top foreign markets for a hip-hop artist
    (no keywords from sync / legal / live_touring / publishing /
    finance_royalties / marketing / fan_social / production / data_analytics /
    capital_funding / digital_ops / intelligence / management / executive /
    bizdev / playlist_dsp / label_ops / controller) must return only the home
    domain with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
