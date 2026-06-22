"""
Phase 3e — Per-agent deep consult test for data-oracle.

Scope: data-oracle only. Home domain "data_analytics". Five realistic
cross-domain questions an artist or their team would ask Data (Analytics
Specialist), covering: audience data and streaming analysis feeding a
marketing campaign, playlist add velocity and DSP metrics for editorial
forecast, streaming data trends driving royalty income projection,
competitive intelligence and industry trends alongside performance
metrics shaping a marketing campaign, and analytics evaluating release
campaign tracking and delivery readiness. Plus one deliberately narrow
question about skip rate and completion rate benchmarking that returns
home-only with no spurious cross-domain.

For each cross-domain question we assert:
  (a) data-oracle's home domain "data_analytics" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a tightly-scoped metrics interpretation question that
avoids all non-analytics domain keywords.

ROUTING GAP: "streaming" alone does NOT trigger data_analytics — the
exact phrases "streaming data" or "streaming analysis" are required.
Generic streaming-performance questions ("how are my streams doing?")
hit no data_analytics keyword; only the home-domain mapping ensures
data_analytics appears in data-oracle's own consults. From OTHER agents,
plain "streaming" language won't route to data_analytics.

ROUTING GAP: "audience" alone fires marketing, not data_analytics — the
exact phrase "audience data" is required for the data_analytics trigger.
Audience questions without the "data" qualifier go to marketing only,
missing the analytics cross-domain from non-home agents.

NOTE: "playlist add velocity" contains the substring "playlist add"
(playlist_dsp keyword), creating intentional dual-domain coverage
whenever that phrase appears — correct behavior.
NOTE: "dsp metric" (data_analytics keyword) is matched as a substring
of "dsp metrics" (query text) — trailing s is transparent. ✓
NOTE: "trajectory" is a standalone data_analytics keyword.
NOTE: "royalt" (stem) fires finance_royalties; "royalty income" suffices.
NOTE: "streaming data" is an exact data_analytics keyword phrase.
NOTE: "audience data" is an exact data_analytics keyword phrase.
NOTE: "analytics" fires data_analytics; "audience" alone fires marketing.
NOTE: "competitive intelligence" and "industry trend" fire intelligence.
NOTE: "release campaign" and "release tracking" fire label_ops.
NOTE: "fan acquisition" is an enriched marketing keyword — does NOT fire
  fan_social ✓ (fan_social requires "fan community", "fan club", etc.)
NOTE: no word in any query contains "ern" as a substring (digital_ops trap)
  — "performance" = p-e-r-f-o-r-m-a-n-c-e, no "ern" ✓
  — "interpret" = i-n-t-e-r-p-r-e-t, no "ern" ✓
NOTE: "streaming trajectory" contains "trajectory" (data_analytics) but NOT
  "streaming data" — only "trajectory" fires data_analytics here. ✓
NOTE: catalog order — marketing (index 2) precedes intelligence (index 16)
  precedes label_ops (index 17) precedes playlist_dsp (index 19). ✓

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "data-oracle"
_HOME  = "data_analytics"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────
#
# (query, expected_cross_domains)
# Invariant: "data_analytics" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.

DEEP_CONSULT_MATRIX = [
    (
        # data_analytics: home — agent mapping (forced first)
        #                 + "audience data" (exact phrase)
        #                 + "streaming analysis" (exact phrase)
        # marketing:      "marketing" (direct), "campaign" (direct),
        #                 "audience" (in "audience data"), "fan acquisition" (enriched)
        # NOTE: "strategy" does NOT match any domain keyword alone. ✓
        # NOTE: "optimize" does NOT match any domain keyword. ✓
        "We need to analyze audience data and streaming analysis to optimize "
        "our marketing campaign and fan acquisition strategy.",
        ["marketing"],
    ),
    (
        # data_analytics: home — agent mapping
        #                 + "playlist add velocity" (exact phrase)
        #                 + "dsp metric" (substring of "dsp metrics")
        #                 + "forecast" (direct)
        #                 + "trajectory" (in "streaming trajectory")
        # playlist_dsp:   "playlist" (direct), "dsp" (in "dsp metrics"),
        #                 "editorial playlist" (exact phrase),
        #                 "playlist add" (substring of "playlist add velocity")
        # NOTE: "streaming trajectory" fires only "trajectory" (data_analytics),
        #       not "streaming data" — "streaming" alone is not a keyword. ✓
        "We want to track playlist add velocity and DSP metrics to forecast "
        "our editorial playlist performance and streaming trajectory.",
        ["playlist_dsp"],
    ),
    (
        # data_analytics: home — agent mapping
        #                 + "forecast" (direct)
        #                 + "streaming data" (exact phrase, in "streaming data trends")
        #                 + "stream count" (exact phrase)
        # finance_royalties: "royalt" (stem, in "royalty income")
        # NOTE: "income" alone is not a finance_royalties keyword — "royalt" fires it. ✓
        # NOTE: "projection" alone does NOT match data_analytics; keyword is
        #       "project the streams" (full phrase not present here). ✓
        "We need to forecast our royalty income by analyzing streaming data "
        "trends and stream count projections for the quarter.",
        ["finance_royalties"],
    ),
    (
        # data_analytics: home — agent mapping
        #                 + "audience data" (exact phrase)
        #                 + "metric" (in "performance metrics")
        # marketing:      "marketing" (direct), "campaign" (direct),
        #                 "audience" (in "audience data")
        # intelligence:   "competitive intelligence" (exact phrase),
        #                 "industry trend" (enriched, exact phrase)
        # NOTE: "data-driven" does NOT contain "analytics" — no extra data_analytics
        #       hit from this phrase, which is intentional. ✓
        # NOTE: catalog order — marketing (index 2) before intelligence (index 16). ✓
        "We want to analyze competitive intelligence and industry trends "
        "alongside our audience data and performance metrics to shape a "
        "data-driven marketing campaign.",
        ["marketing", "intelligence"],
    ),
    (
        # data_analytics: home — agent mapping
        #                 + "analytics" (direct)
        #                 + "metric" (in "tracking metrics")
        # label_ops:      "release campaign" (exact phrase),
        #                 "release tracking" (exact phrase)
        # NOTE: "delivery readiness" does NOT match "release readiness" (label_ops)
        #       or any digital_ops delivery keyword — only "release campaign" and
        #       "release tracking" fire label_ops here. ✓
        # NOTE: "project" alone does NOT trigger executive. ✓
        "We need analytics to evaluate our release campaign performance and "
        "release tracking metrics to improve delivery readiness for the "
        "next project.",
        ["label_ops"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────
#
# A tightly-scoped metrics interpretation question that returns ONLY
# "data_analytics" (via home domain) with no spurious cross-domain routing.
# Deliberately avoids:
# "marketing" / "campaign" / "audience" / "fanbase" / "rollout" (marketing)
# "streaming data" / "streaming analysis" / "analytics" (would also fire data_analytics — ok)
#   but also avoids "fan acquisition", "email campaign" (marketing enriched)
# "playlist" / "dsp" / "editorial" / "pre-save" (playlist_dsp)
# "royalt" / "splits" / "advance" / "streaming income" / "statement" (finance_royalties)
# "release campaign" / "release plan" / "release tracking" (label_ops)
# "contract" / "clause" / "rights" / "legal" / "copyright" (legal)
# "tour" / "concert" / "venue" / "festival" / "booking" (live_touring)
# "publish" / "co-write" / "catalog" / "administration" (publishing)
# "production" / "producer" / "mixing" / "mastering" / "studio" (production)
# "capital" / "fund" / "invest" / "equity" / "grant" (capital_funding)
# "controller" / "ledger" / "reconcil" / "anomaly detection" (controller)
#   NOTE: "anomaly" alone fires data_analytics — but not used here
# "metadata" / "isrc" / "ern" / "ddex" / "identifier" (digital_ops)
#   NOTE: also avoids all words containing "ern" as a substring
#         "performance" = p-e-r-f-o-r-m-a-n-c-e — no "ern" ✓
#         "interpret" = i-n-t-e-r-p-r-e-t — no "ern" ✓
#         "comparable" = c-o-m-p-a-r-a-b-l-e — no "ern" ✓
# "executive" / "build vs buy" / "strategic" / "scenario" (executive)
# "superfan" / "fan community" / "fan club" / "fan engagement" (fan_social)
# "intelligence" / "market trend" / "industry trend" (intelligence)
# "artist manager" / "management" / "manage" (management)
# "sync" / "placement" / "licens" / "film" (sync)
# "brand" / "sponsor" / "partnership" / "merch" (bizdev)
# "a&r" / "scouting" / "unsigned" / "roster" (ar)
# "save rate" — fires BOTH data_analytics AND fan_social; use skip/completion instead

_NARROW_QUERY = (
    "How do we interpret our skip rate, completion rate, and streams per "
    "listener to benchmark our track's performance against comparable releases?"
)


# ── Tests ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "audience-data-streaming-analysis-marketing-campaign-fan-acquisition",
        "playlist-add-velocity-dsp-metrics-editorial-forecast-trajectory",
        "royalty-income-streaming-data-stream-count-finance-royalties",
        "competitive-intelligence-industry-trends-audience-data-metrics-marketing",
        "analytics-release-campaign-tracking-metrics-delivery-readiness-label-ops",
    ],
)
def test_data_oracle_consult_home_leads_and_cross_domains_present(query, cross):
    """
    data-oracle's home domain 'data_analytics' is always first; every expected
    cross-domain is present. Verifies home-first invariant and analytics
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


def test_data_oracle_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped metrics interpretation question (no keywords from marketing /
    playlist_dsp / finance_royalties / label_ops / legal / live_touring /
    publishing / production / capital_funding / controller / digital_ops /
    executive / fan_social / intelligence / management / sync / bizdev / or ar)
    must return only the home domain with no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
