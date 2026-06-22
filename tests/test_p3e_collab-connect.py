"""
Phase 3e — Per-agent deep consult test for collab-connect.

Scope: collab-connect only. Home domain "ar". Five realistic cross-domain
questions an artist or their team would ask Collab (Networking specialist),
covering: structuring a collaboration deal with co-write and publishing admin,
a feature deal with contract clauses and royalty splits, a joint release
needing a co-write publishing agreement and marketing campaign, a collaboration
track pitched for sync placement in a film, and leveraging a partner artist's
fanbase through fan community and marketing rollout. Plus one deliberately
narrow question about finding the right featured artists that returns home-only
with no spurious cross-domain.

For each cross-domain question we assert:
  (a) collab-connect's home domain "ar" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped artist-matching question that avoids all
domain keywords.

ROUTING GAP: The "ar" domain keywords do not include collab-connect's core
vocabulary ("collaboration", "feature", "networking", "industry introduction",
"relationship"). This means collab-connect's expertise is NOT reachable as a
cross-domain from other agents whose queries naturally use these words — only
the home-domain mapping makes "ar" appear in collab-connect's own results.
A future enrichment of the ar domain keywords (e.g., "artist feature",
"feature collaboration", "networking event") would make "ar" reachable from
e.g. sync-agent or bizdev-agent when they discuss featuring another artist.
This is CURRENT correct behavior (no shared files changed).

ROUTING GAP: The "bizdev" keyword "collaboration deal" fires only on the exact
phrase. Generic vocabulary ("working with", "partnering", "co-creating",
"collaborating") does NOT trigger bizdev — the full phrase is required. This is
CURRENT correct behavior.

NOTE: "collaboration deal" is an exact bizdev keyword — full phrase required.
NOTE: "co-write" fires publishing as a substring match.
NOTE: "publishing admin" is an exact publishing keyword.
NOTE: "contract" fires legal; "clause" (from "clauses") fires legal.
NOTE: "royalt" (stem) fires finance_royalties; "splits" fires finance_royalties.
NOTE: "streaming income" is an exact finance_royalties keyword.
NOTE: "fanbase" fires marketing; "fan community" fires fan_social — distinct keywords.
NOTE: "featured" does NOT contain "ern" (the digital_ops substring trap) ✓

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "collab-connect"
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
        # ar:         home — agent mapping (home forced first, no ar keyword needed)
        # bizdev:     "collaboration deal" (exact phrase)
        # publishing: "co-write" (exact substring), "publishing admin" (exact phrase)
        # NOTE: "agreement" is NOT a legal keyword — legal stays silent. ✓
        # NOTE: "featured" does NOT trigger any domain keyword. ✓
        "We want to structure a collaboration deal with a featured artist, "
        "including a co-write agreement and publishing admin setup.",
        ["bizdev", "publishing"],
    ),
    (
        # ar:                home — agent mapping
        # legal:             "contract" (→ "contract clauses"), "clause" (→ "clauses")
        # finance_royalties: "royalt" (→ "royalty"), "splits" (→ "royalty splits"),
        #                    "streaming income" (exact phrase)
        # NOTE: catalog order — legal (index 4) precedes finance_royalties (index 7)
        #       so legal appears before finance_royalties in the result list. ✓
        "We have a feature deal on a new single — what contract clauses govern "
        "the royalty splits and streaming income?",
        ["legal", "finance_royalties"],
    ),
    (
        # ar:        home — agent mapping
        # marketing: "marketing" (direct), "campaign" (direct)
        # publishing: "co-write" (direct), "publish" (→ "publishing agreement")
        # NOTE: "joint release" does NOT contain "release planning", "release plan",
        #       or "release campaign" (label_ops keywords) — label_ops silent. ✓
        # NOTE: catalog order — marketing (index 1) precedes publishing (index 6). ✓
        "We are planning a joint release with another artist and need a "
        "co-write publishing agreement and a joint marketing campaign.",
        ["marketing", "publishing"],
    ),
    (
        # ar:    home — agent mapping
        # sync:  "sync" (direct), "placement" (direct), "licens" (→ "licensing"),
        #        "film" (direct)
        # legal: "contract" (direct), "clause" (→ "clauses")
        # NOTE: catalog order — sync (index 2) precedes legal (index 4). ✓
        "We have a collaboration track pitched for sync placement in a film — "
        "what contract terms and licensing clauses should we review?",
        ["sync", "legal"],
    ),
    (
        # ar:        home — agent mapping
        # marketing: "fanbase" (direct), "marketing" (direct), "rollout" (direct)
        # fan_social: "fan community" (exact phrase)
        # NOTE: "fan community" is NOT a marketing keyword — fan_social only. ✓
        # NOTE: "fanbase" is NOT a fan_social keyword alone — marketing only. ✓
        # NOTE: catalog order — marketing (index 1) precedes fan_social (index 14). ✓
        "We are collaborating with a popular artist — how do we use their "
        "fanbase and our fan community to build a joint marketing rollout?",
        ["marketing", "fan_social"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped artist-matching question that returns ONLY "ar" (via home
# domain) with no spurious cross-domain routing.
# Deliberately avoids:
# "collaboration deal" / "b2b" / "brand" / "sponsor" / "partner " (bizdev)
# "contract" / "clause" / "rights" / "legal" / "copyright" / "negotiat" (legal)
# "publish" / "co-write" / "catalog" / "administration" / "split sheet" (publishing)
# "royalt" / "splits" / "split " / "advance" / "streaming income" (finance_royalties)
# "marketing" / "campaign" / "fanbase" / "fan base" / "rollout" (marketing)
# "fan community" / "superfan" / "newsletter" / "fan club" (fan_social)
# "sync" / "placement" / "licens" / "film" / "tv" (sync)
# "tour" / "concert" / "venue" / "festival" / "booking" (live_touring)
# "production" / "producer" / "studio" / "mixing" (production)
# "dsp" / "playlist" / "editorial" / "pre-save" (playlist_dsp)
# "analytics" / "metric" / "kpi" / "streaming data" (data_analytics)
# "metadata" / "isrc" / "upc" / "ddex" (digital_ops)
#   NOTE: also avoids words containing "ern" as a substring (digital_ops trap)
#         "featured" = f-e-a-t-u-r-e-d — no "ern" ✓
#         "genre" = g-e-n-r-e — no "ern" ✓
# "capital" / "fund" / "invest" / "grant" (capital_funding)
# "intelligence" / "market trend" / "industry trend" (intelligence)
# "artist manager" / "management" / "manage" (management)
# "label ops" / "release planning" / "distribution" (label_ops)
# "controller" / "ledger" / "reconcil" (controller)
# "executive" / "build vs buy" / "strategic" (executive)

_NARROW_QUERY = (
    "How do we find and approach the right featured artists for sonic fit "
    "and genre alignment?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "collaboration-deal-co-write-publishing-admin-bizdev-publishing",
        "feature-deal-contract-royalty-splits-streaming-income-legal-finance-royalties",
        "joint-release-co-write-publishing-agreement-marketing-campaign",
        "collaboration-track-sync-placement-film-contract-licensing-sync-legal",
        "artist-collaboration-fanbase-fan-community-marketing-rollout",
    ],
)
def test_collab_connect_consult_home_leads_and_cross_domains_present(query, cross):
    """
    collab-connect's home domain 'ar' is always first; every expected cross-domain
    is present. Verifies home-first invariant and networking specialist
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


def test_collab_connect_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped artist-matching question (no keywords from bizdev / legal /
    publishing / finance_royalties / marketing / fan_social / sync / live_touring /
    production / playlist_dsp / data_analytics / digital_ops / capital_funding /
    intelligence / management / label_ops / controller / or executive) must return
    only the home domain with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
