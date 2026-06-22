"""
Phase 3e — Per-agent deep consult test for music-edu.

Scope: music-edu only. Home domain "management". Five realistic cross-domain
questions an artist would ask Prof (Music Business Educator), covering: contract
terms in a management deal (legal), royalty advances and recoupment (finance_royalties),
major-label deal vs independent distribution (label_ops), publishing administration
before signing a publishing deal (publishing), and the marketing concepts a
developing artist needs during career growth (marketing). Plus one deliberately
narrow question about the artist-manager relationship that returns home-only with
no spurious cross-domain.

For each cross-domain question we assert:
  (a) music-edu's home domain "management" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped artist-manager-relationship question that avoids
all non-management domain keywords.

ROUTING NOTE: music-edu shares home domain "management" with artist-wellness;
their cross-domain matrices are intentionally distinct — music-edu routes through
education/business-knowledge angles (legal, finance_royalties, label_ops,
publishing, marketing) while artist-wellness routes through burnout/wellbeing
angles (live_touring). Both agents test the management home-first invariant
independently.

NOTE: "management contract" is an exact management keyword phrase — sufficient
  alone to anchor the management home even before the home mapping. ✓
NOTE: "clause" fires legal as a substring of "clauses" ("clause" in "clauses"). ✓
NOTE: "contract" is a standalone legal keyword — substring of "management contract"
  fires both management (management contract) and legal (contract). ✓
NOTE: "royalt" (stem) fires finance_royalties; "royalty" contains "royalt". ✓
NOTE: "advance" is a standalone finance_royalties keyword. ✓
NOTE: "recoup" (stem) fires finance_royalties; "unrecouped" contains "recoup". ✓
NOTE: "label deal" is an exact label_ops keyword phrase; it appears as a
  substring of "major label deal" ("label deal" ⊂ "major label deal"). ✓
NOTE: "distribution deal" is an exact label_ops keyword phrase. ✓
NOTE: "signing" alone does NOT fire ar; ar keywords require full phrases like
  "sign the artist" or "new signing" — neither is a substring of "signing a
  major label deal". ✓
NOTE: "publish" (stem) fires publishing; "publishing" contains "publish". ✓
NOTE: "publishing deal" is an exact publishing keyword phrase. ✓
NOTE: "administration" is a standalone publishing keyword ("administration" ⊂
  "publishing administration"). ✓
NOTE: "marketing" is a standalone marketing keyword. ✓
NOTE: "fanbase" is an exact marketing keyword (appears in marketing, NOT in
  fan_social — fan_social requires "fan community", "fandom", "superfan", etc.). ✓
NOTE: "audience" is a standalone marketing keyword. ✓
NOTE: "developing artist" does NOT fire ar; ar requires "artist development"
  or "develop the artist" as full-phrase substrings — neither matches
  "developing artist". ✓
NOTE: narrow query contains only management keywords ("artist-manager",
  "day-to-day manager") — no legal, finance_royalties, label_ops, publishing,
  marketing, or any other domain keyword is present. ✓
NOTE: "manager" alone does NOT fire management; only multi-word phrases like
  "artist manager", "music manager", "day-to-day manager" are keywords. ✓

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "music-edu"
_HOME  = "management"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "management" leads; every expected cross-domain is in domains.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # management: management contract (home keyword phrase + forced first)
        # legal: contract (substring of "management contract"),
        #        clause (substring of "clauses")
        # NOTE: "terms" alone does NOT fire legal; the legal keyword is "term sheet"
        #       (full phrase) — "terms" is not a superstring of "term sheet". ✓
        # NOTE: "power" is not registered as a keyword in any domain. ✓
        "Can you walk me through what terms to watch out for in a management "
        "contract and which clauses give managers too much power?",
        ["legal"],
    ),
    (
        # management: home (auto — no management phrase in this query;
        #             home mapping always fires first)
        # finance_royalties: royalt (from "royalty"), advance, recoup (from "unrecouped")
        # NOTE: "from labels" does NOT fire label_ops; "labels" is not a label_ops
        #       keyword — only multi-word phrases like "label deal", "label ops",
        #       "distribution deal" fire that domain. ✓
        "How do royalty advances from labels work and what does it mean for an "
        "artist to be unrecouped?",
        ["finance_royalties"],
    ),
    (
        # management: home (auto — no management phrase in this query)
        # label_ops: label deal (substring of "major label deal"),
        #            distribution deal
        # NOTE: "signing" alone does NOT fire ar — ar requires full phrases like
        #       "sign the artist" or "new signing"; neither is a substring of
        #       "signing a major label deal". ✓
        # NOTE: "deal" alone does NOT fire legal; legal needs "deal memo" or
        #       "term sheet" as a full phrase. ✓
        "What are the key differences between signing a major label deal versus "
        "going independent with a distribution deal?",
        ["label_ops"],
    ),
    (
        # management: home (auto — no management phrase in this query)
        # publishing: publish (from "publishing"), administration,
        #             publishing deal (exact keyword phrase)
        # NOTE: "signing" alone does NOT fire ar (same rationale as Q3). ✓
        # NOTE: "deal" alone does NOT fire legal; "publishing deal" contains
        #       "publishing deal" (publishing keyword) but not "deal memo"
        #       or "term sheet". ✓
        "How does publishing administration work and what should an artist "
        "look for in a publishing deal before signing?",
        ["publishing"],
    ),
    (
        # management: home (auto — "their manager" does NOT fire management
        #             keywords; only full phrases like "artist manager", "music manager",
        #             "day-to-day manager" are keywords, none of which appear here)
        # marketing: marketing, fanbase, audience
        # NOTE: "developing artist" does NOT fire ar — ar needs "artist development"
        #       or "develop the artist" as exact substrings; "developing artist"
        #       matches neither. ✓
        # NOTE: "fanbase" fires marketing (explicit marketing keyword) and NOT
        #       fan_social (fan_social requires "fan community", "fandom",
        #       "superfan", etc. — "fanbase" is NOT in fan_social keywords). ✓
        "What marketing concepts should a developing artist and their manager "
        "focus on to grow their fanbase and increase audience reach?",
        ["marketing"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped artist-manager-relationship question that returns ONLY
# "management". Keywords fired: artist-manager, day-to-day manager.
# Deliberately avoids:
# "contract" / "clause" / "legal" / "rights" / "negotiat" (legal)
# "royalt" / "advance" / "recoup" / "splits" / "mechanical" (finance_royalties)
# "label deal" / "distribution deal" / "distribution" / "catalog" (label_ops)
# "publish" / "administration" / "co-write" / "songwrit" (publishing)
# "marketing" / "campaign" / "fanbase" / "audience" (marketing)
# "tour" / "concert" / "venue" / "booking" / "festival" (live_touring)
# "playlist" / "dsp" / "editorial" / "streaming platform" (playlist_dsp)
# "capital" / "fund" / "invest" / "grant" (capital_funding)
# "brand" / "partner" / "sponsor" / "merch" (bizdev)
# "controller" / "ledger" / "reconcil" / "balance sheet" (controller)
# "analytics" / "metric" / "kpi" / "streaming data" (data_analytics)
# "executive" / "build vs buy" / "strategic" / "decision" (executive)
# "fan community" / "fan club" / "superfan" / "fandom" (fan_social)
# "intelligence" / "market trend" / "industry trend" (intelligence)
# "a&r" / "scouting" / "unsigned" / "talent scout" (ar)
# "production" / "producer" / "mixing" / "mastering" / "studio" (production)
# "digital ops" / "metadata" / "isrc" / "ddex" (digital_ops)
# NOTE: "handle" and "typically" are not keywords for any domain. ✓
# NOTE: "day-to-day" fires management via "day-to-day manager" (multi-word phrase);
#       the full phrase "day-to-day manager" appears as a substring of
#       "day-to-day manager handle". ✓

_NARROW_QUERY = (
    "How does an artist-manager relationship typically work and what does a "
    "day-to-day manager handle for their artist?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "management-contract-clauses-legal",
        "royalty-advances-recoupment-finance_royalties",
        "major-label-deal-vs-distribution-label_ops",
        "publishing-administration-deal-publishing",
        "marketing-fanbase-audience-career-growth",
    ],
)
def test_music_edu_consult_home_leads_and_cross_domains_present(query, cross):
    """
    music-edu's home domain 'management' is always first; every expected
    cross-domain is present. Verifies the home-first invariant and the
    Music Business Educator cross-domain routing quality.
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


def test_music_edu_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped artist-manager-relationship question (artist-manager,
    day-to-day manager) must return only the home domain 'management' — no
    spurious cross-domain routing from legal, finance_royalties, label_ops,
    publishing, or marketing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
