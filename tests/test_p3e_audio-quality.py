"""
Phase 3e — Per-agent deep consult test for audio-quality.

Scope: audio-quality only. Home domain "production". Five realistic
cross-domain questions an artist would ask Audio (Quality Control Specialist),
covering: metadata and ISRC embedding before DSP delivery, stem preparation for
a sync licensing placement, sample clearance and mechanical royalty resolution
before mastering, Dolby Atmos spatial audio QC checklist, and co-write
publishing admin before distribution. Plus one deliberately narrow loudness
question that returns home-only with no spurious cross-domain.

For each cross-domain question we assert:
  (a) audio-quality's home domain "production" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped clipping/loudness question that avoids all
non-production domain keywords.

ROUTING NOTE: audio-quality shares home domain "production" with producer-connect;
their cross-domain matrix is intentionally distinct — audio-quality routes through
delivery/QC angles (digital_ops, label_ops) rather than producer deal angles
(legal, finance_royalties advance/recoupment). Both agents test the production
home-first invariant independently.

NOTE: "metadata" and "isrc" are exact digital_ops keywords — sufficient alone
  to pull digital_ops as a cross-domain from any production-home query. ✓
NOTE: "licens" (stem) fires sync; "licensing" contains "licens". ✓
NOTE: "stems" is a standalone production keyword — sufficient to anchor
  the production home even without "mastering" or "mixing". ✓
NOTE: "royalt" (stem) fires finance_royalties; "royalty" contains "royalt". ✓
NOTE: "mechanical" is a standalone finance_royalties keyword. ✓
NOTE: "sample clearance" is an enriched production keyword phrase. ✓
NOTE: "dolby atmos" and "spatial audio" are label_ops keywords. ✓
NOTE: "qc checklist" is a label_ops keyword; appears as substring of
  "QC checklist requirements" (lowercased match). ✓
NOTE: "co-write" and "songwrit" (stem, from "songwriting") are publishing
  keywords; "publishing admin" is an exact publishing keyword phrase and
  appears as substring of "publishing administration". ✓
NOTE: "split " (with trailing space) does NOT match "splits" — "splits and"
  has 's' between "split" and the space, so finance_royalties is not
  spuriously triggered by "splits" in Q3. ✓
NOTE: "delivery" alone does not fire any domain; only multi-word phrases like
  "dsp delivery", "delivery spec", "delivery qc" fire their domains. ✓
NOTE: "master" alone does NOT match "mastering" keyword — substring check is
  `"mastering" in query`, so "spatial audio master" does not fire production
  via keyword (home mapping handles it). ✓
NOTE: "distribut" (from "distributed") does NOT match "distributor" or any
  distribution keyword — keyword check requires the full phrase substring. ✓
NOTE: narrow query avoids all non-production keywords; "2-bus", "clipping",
  "overages" are not registered keywords for any domain. ✓

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "audio-quality"
_HOME  = "production"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "production" leads; every expected cross-domain is in domains.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # production: mixing, mastering (home keywords + forced first)
        # digital_ops: metadata, isrc
        # NOTE: "delivery" alone fires nothing; "embedded" / "wav" are not
        #       keywords — only metadata + isrc pull digital_ops. ✓
        "We finished mixing and mastering — what metadata and ISRC tags need "
        "to be correctly embedded in the WAV before delivery?",
        ["digital_ops"],
    ),
    (
        # production: stems (home keyword)
        # sync: sync, licens (substring of "licensing"), placement, film
        # NOTE: "technical specs" does not contain "delivery spec" — no
        #       spurious digital_ops trigger. ✓
        "We need stems ready for a potential sync licensing placement in a "
        "film — what technical specs and format requirements should we prepare?",
        ["sync"],
    ),
    (
        # production: mastering, sample clearance (home keywords)
        # finance_royalties: royalt (from "royalty"), mechanical
        # NOTE: "splits and" — "split " (space-terminated keyword) does NOT
        #       match "splits"; "splits" has 's' before the space. ✓
        # NOTE: "clearance requirements" — "clearance" alone is not a keyword;
        #       only "sample clearance" (already in production) fires. ✓
        "We are mastering a track that contains a sample clearance — what are "
        "the royalty splits and mechanical clearance requirements we need to "
        "resolve before the master is approved?",
        ["finance_royalties"],
    ),
    (
        # production: mastering (home keyword + forced first)
        # label_ops: dolby atmos, spatial audio, qc checklist
        # NOTE: "delivery" alone does not fire digital_ops or label_ops.
        #       "qc checklist" fires label_ops (substring of "QC checklist"). ✓
        "We are mastering a Dolby Atmos spatial audio mix — what are the QC "
        "checklist requirements and technical standards before we approve "
        "the final delivery?",
        ["label_ops"],
    ),
    (
        # production: mastering (home keyword + forced first)
        # publishing: co-write, songwrit (from "songwriting"),
        #             publishing admin (substring of "publishing administration"),
        #             administration
        # NOTE: "distribut" from "distributed" does NOT match "distributor"
        #       or "distribution" keywords. ✓
        # NOTE: "credits" is not a keyword for any domain. ✓
        "We are mastering a co-write and need to ensure all songwriting credits "
        "are correctly attributed and the publishing administration is in order "
        "before the track is distributed.",
        ["publishing"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped clipping/loudness question that returns ONLY "production".
# Keywords fired: true peak, loudness, mastering.
# Deliberately avoids:
# "mixing" / "mix engineer" (only "mix" appears — "mixing" keyword not matched)
# "metadata" / "isrc" / "ddex" / "identifier" (digital_ops)
# "sync" / "placement" / "licens" / "film" (sync)
# "royalt" / "mechanical" / "advance" / "splits" (finance_royalties)
# "dolby atmos" / "spatial audio" / "qc checklist" / "release plan" (label_ops)
# "co-write" / "publish" / "catalog" / "administration" (publishing)
# "contract" / "clause" / "rights" / "legal" (legal)
# "tour" / "concert" / "venue" / "booking" (live_touring)
# "playlist" / "dsp" / "editorial" (playlist_dsp)
# "capital" / "fund" / "invest" / "grant" (capital_funding)
# "brand" / "partner" / "merch" / "sponsor" (bizdev)
# "controller" / "ledger" / "reconcil" (controller)
# "analytics" / "metric" / "audience data" / "streaming data" (data_analytics)
# "executive" / "build vs buy" / "strategic" (executive)
# "fan community" / "fan club" / "superfan" (fan_social)
# "intelligence" / "market trend" / "industry trend" (intelligence)
# "artist manager" / "management" / "manage" (management)
# "a&r" / "scouting" / "unsigned" (ar)
# NOTE: "2-bus", "clipping", "overages" are not registered keywords. ✓
# NOTE: "levels" alone is not a keyword. ✓

_NARROW_QUERY = (
    "Our mix has clipping on the 2-bus — how do we identify true peak overages "
    "and fix the loudness levels before sending to mastering?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "metadata-isrc-before-delivery-digital_ops",
        "stems-sync-licensing-placement-film",
        "sample-clearance-royalty-mechanical-finance_royalties",
        "dolby-atmos-spatial-audio-qc-checklist-label_ops",
        "cowrite-songwriting-publishing-admin",
    ],
)
def test_audio_quality_consult_home_leads_and_cross_domains_present(query, cross):
    """
    audio-quality's home domain 'production' is always first; every expected
    cross-domain is present. Verifies the home-first invariant and the
    QC-specialist cross-domain routing quality.
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


def test_audio_quality_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped clipping/loudness question (true peak, loudness, mastering)
    must return only the home domain 'production' — no spurious cross-domain
    routing from digital_ops, sync, finance_royalties, label_ops, or publishing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
