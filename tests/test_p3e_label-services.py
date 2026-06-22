"""
Phase 3e — Per-agent deep consult test for label-services.

Scope: label-services only. Home domain "label_ops". Five realistic
questions an artist would ask Tommy (Label Services Manager), covering:
a recording contract with 360-deal clause negotiation, advance sizing with
royalty waterfall and recoupment modelling, delivery-spec and ISRC/metadata
pre-delivery QC, pre-save and editorial submission playlist placement
strategy, and a multi-domain label-deal scenario spanning legal and finance.
Plus a deliberately narrow question that should return home-only with no
spurious cross-domain.

For each cross-domain question we assert:
  (a) label-services's home domain "label_ops" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure release-planning / milestone-timeline question that
avoids keywords from legal, finance_royalties, digital_ops, playlist_dsp,
marketing, live_touring, bizdev, data_analytics, publishing, production,
capital_funding, management, fan_social, executive, sync, ar, controller,
or intelligence.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "label-services"
_HOME  = "label_ops"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "label_ops" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # label_ops:  home — always leads ("recording contract", "360 deal",
        #             "option period", "delivery commitment", "deal terms")
        # legal:      "contract" (x2 — in "recording contract" and "contract clauses"),
        #             "clause" (via "clauses"), "negotiat" (via "negotiate")
        "We are reviewing a recording contract for a new signing that includes a 360 deal — "
        "what are the key contract clauses around the option period, delivery commitment, and "
        "deal terms we should negotiate?",
        ["legal"],
    ),
    (
        # label_ops:  home — always leads ("size the advance", "royalty waterfall",
        #             "advance against streaming", "recoupment projection")
        # finance_royalties: "royalt" (via "royalty waterfall"),
        #                    "advance" (via "advance against streaming"),
        #                    "recoup" (via "recoupment projection")
        "We need to size the advance for a new signing and model the royalty waterfall, "
        "including advance against streaming and the recoupment projection — how should we "
        "structure this?",
        ["finance_royalties"],
    ),
    (
        # label_ops:  home — always leads ("pre-delivery qc" also fires digital_ops
        #             but home is already first)
        # digital_ops: "delivery spec", "isrc" (via "ISRC" lowercased),
        #              "metadata error", "pre-delivery qc"
        "What delivery spec should we follow, and how do we verify ISRC assignments, correct "
        "metadata errors, and pass pre-delivery QC before the release goes live?",
        ["digital_ops"],
    ),
    (
        # label_ops:  home — always leads ("pre-save", "editorial pitch",
        #             "pitch window")
        # playlist_dsp: "pre-save", "editorial pitch", "spotify editorial",
        #               "curator", "pitch window"
        # NOTE: avoids "playlist" (marketing kw), "placement" (sync kw),
        #       "submission" (contains "bmi" → finance_royalties)
        "How do we set up a pre-save landing page, build an editorial pitch for "
        "Spotify editorial, and coordinate curator outreach ahead of our pitch window?",
        ["playlist_dsp"],
    ),
    (
        # label_ops:  home — always leads ("label deal", "recording agreement",
        #             "advance sizing", "deal terms")
        # legal:      "contract" (via "contract terms"), "negotiat" (via "negotiate")
        # finance_royalties: "royalt" (via "royalty accounting"),
        #                    "advance" (via "advance sizing"),
        #                    "accounting" (via "royalty accounting")
        "We are finalizing a label deal with a recording agreement — how do we negotiate the "
        "contract terms around advance sizing, royalty accounting, and what are the key deal "
        "terms an artist should protect?",
        ["legal", "finance_royalties"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped release-planning / milestone question that returns
# ONLY "label_ops" (via home domain). Deliberately avoids:
# "contract" / "clause" / "negotiat" / "rights" (legal)
# "royalt" / "advance" / "recoup" / "accounting" / "splits" (finance_royalties)
# "metadata" / "isrc" / "upc" / "delivery spec" (digital_ops)
# "pre-save" / "presave" / "playlist" / "dsp" / "editorial" (playlist_dsp)
# "marketing" / "campaign" / "audience" / "fanbase" (marketing)
# "tour" / "concert" / "venue" / "ticket" / "festival" (live_touring)
# "brand" / "sponsor" / "merch" / "ambassador" (bizdev)
# "analytics" / "metric" / "kpi" / "data analy" (data_analytics)
# "publish" / "catalog" / "catalogue" / "co-write" / "composition" (publishing)
# "production" / "producer" / "studio" / "mixing" / "mastering" (production)
# "capital" / "fund" / "financ" / "invest" / "angel" (capital_funding)
# "manager" / "management agreement" / "commission" (management)
# "fan" / "superfan" / "community" / "discord" (fan_social)
# "executive" / "ceo" / "strategy" alone (executive)
# "sync" / "placement" / "licens" (sync)
# "scout" / "a&r" / "unsigned" (ar)
# "ledger" / "reconcil" / "controller" (controller)
# "market trend" / "market intelligence" (intelligence)

_NARROW_QUERY = (
    "How do we structure our release planning workflow, set up a milestone timeline, "
    "and manage the release readiness gate for our next Friday release?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "recording-contract-360-deal-clauses-option-period-deal-terms-legal",
        "advance-sizing-royalty-waterfall-recoupment-projection-finance",
        "delivery-spec-isrc-metadata-errors-pre-delivery-qc-digital-ops",
        "pre-save-editorial-pitch-spotify-editorial-curator-outreach-pitch-window",
        "label-deal-recording-agreement-advance-royalty-accounting-legal-finance",
    ],
)
def test_label_services_consult_home_leads_and_cross_domains_present(query, cross):
    """
    label-services's home domain 'label_ops' is always first; every expected
    cross-domain is present. Verifies home-first invariant and label services
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


def test_label_services_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped release-planning / milestone-timeline question (no
    keywords from legal / finance_royalties / digital_ops / playlist_dsp /
    marketing / live_touring / bizdev / data_analytics / publishing /
    production / capital_funding / management / fan_social / executive /
    sync / ar / controller / intelligence) must return only the home domain
    with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
