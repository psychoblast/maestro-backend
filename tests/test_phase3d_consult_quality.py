"""
Phase 3d — Consult-quality test matrix for all 44 agents.

Goals
------
1. Every agent's home domain leads its consult result (home-first invariant).
2. Realistic domain-relevant questions pull the expected cross-domains.
3. Narrowly-scoped questions return the home domain only (no spurious cross-domain).
4. The three orphan domains (controller, digital_ops, intelligence) — which have
   no home agent — are genuinely reachable cross-domain from any agent.

All tests are deterministic, in-process, and make NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import AGENT_HOME, consult_for_agent


# ── Helpers ──────────────────────────────────────────────────────────────────────

def _consult(agent: str, query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(agent, query, max_domains=max_domains)


# ── Data tables ──────────────────────────────────────────────────────────────────

# CONSULT_MATRIX: one row per agent (all 44).
# (agent_slug, query, home_domain, expected_cross_domains)
# Asserts: home_domain is first; every expected_cross_domain is in domains.
CONSULT_MATRIX = [
    # ── Originally paired agents (9) ─────────────────────────────────────────
    (
        "ar-scout",
        "We discovered an unsigned emerging artist doing sync placements - should we scout them?",
        "ar",
        ["sync"],
    ),
    (
        "grid-prophet",
        "We need a marketing campaign supporting a DSP editorial playlist pitch and rollout",
        "marketing",
        ["playlist_dsp"],
    ),
    (
        "sync-agent",
        "We got a sync offer for a TV advertisement - what contract clauses should we review?",
        "sync",
        ["legal"],
    ),
    (
        "brand-connect",
        "We have a brand sponsorship deal including touring activation and legal review",
        "bizdev",
        ["live_touring", "legal"],
    ),
    (
        "lex-cipher",
        "We are reviewing a management contract covering publishing rights and royalty administration",
        "legal",
        ["management", "publishing"],
    ),
    (
        "tour-commander",
        "We have a festival offer - what are the contract terms and royalty splits to negotiate?",
        "live_touring",
        ["legal", "finance_royalties"],
    ),
    (
        "ink-and-air",
        "We want to sync our back catalog and maximize royalty income from licensing",
        "publishing",
        ["sync", "finance_royalties"],
    ),
    (
        "royalty-doctor",
        "Help us analyze this royalty statement and the publishing administration deductions",
        "finance_royalties",
        ["publishing"],
    ),
    (
        "producer-connect",
        "We are booking a studio session and need to understand producer royalties and mixing credits",
        "production",
        ["finance_royalties"],
    ),
    # ── Executive / strategy (2) ─────────────────────────────────────────────
    (
        "puppet-master",
        "Should we sign to a major label or stay independent - what is the strategic decision and legal analysis?",
        "executive",
        ["legal"],
    ),
    (
        "ai-navigator",
        "Should we build vs buy an AI analytics platform - what is the ROI and data-driven decision?",
        "executive",
        ["data_analytics"],
    ),
    # ── Finance & royalties (6) ──────────────────────────────────────────────
    (
        "fund-phantom",
        "We are raising capital and need equity term sheet legal review before finalizing the investment",
        "capital_funding",
        ["legal"],
    ),
    (
        "border-royalty",
        "How do neighbouring rights royalties interact with our publishing administration?",
        "finance_royalties",
        ["publishing"],
    ),
    (
        "mech-ledger",
        "We need to reconcile our mechanical royalties statement and understand the publishing split sheet",
        "finance_royalties",
        ["publishing"],
    ),
    (
        "vault-keeper",
        "Help us track touring income and royalty splits across the artist income streams",
        "finance_royalties",
        ["live_touring"],
    ),
    (
        "ledger-lock",
        "We need royalty accounting and tax planning for our publishing income streams",
        "finance_royalties",
        ["publishing"],
    ),
    (
        "rights-pulse",
        "We need to register our catalog with ASCAP and understand mechanical royalties for streaming",
        "publishing",
        ["finance_royalties"],
    ),
    # ── Marketing / press / content (9) ─────────────────────────────────────
    (
        "signal-blaster",
        "We are running a marketing PR campaign to support our sync licensing placement",
        "marketing",
        ["sync"],
    ),
    (
        "press-monitor",
        "We need to monitor media coverage and track streaming metrics for marketing performance",
        "marketing",
        ["data_analytics"],
    ),
    (
        "pr-agent",
        "We are planning a PR campaign around the editorial playlist submission and tour announcement",
        "marketing",
        ["playlist_dsp", "live_touring"],
    ),
    (
        "social-manager",
        "How do we build a social media strategy supporting our DSP release and playlist pitching?",
        "marketing",
        ["playlist_dsp"],
    ),
    (
        "vision-forge",
        "We need visual brand identity for our marketing campaign and sync licensing pitch",
        "marketing",
        ["sync"],
    ),
    (
        "design-studio",
        "Help us design album artwork meeting DSP delivery specifications for our marketing campaign",
        "marketing",
        ["digital_ops"],
    ),
    (
        "creative-director",
        "We need creative direction for the album rollout that includes a sync licensing pitch",
        "marketing",
        ["sync"],
    ),
    (
        "video-director",
        "We are producing a music video to support the marketing rollout and explore sync licensing",
        "marketing",
        ["sync"],
    ),
    (
        "content-forge",
        "We need marketing copy and bios that support the playlist pitch campaign",
        "marketing",
        ["playlist_dsp"],
    ),
    # ── Fan & social (1) ────────────────────────────────────────────────────
    (
        "fan-builder",
        "How do we launch a fan club and grow our community through direct-to-fan marketing campaigns?",
        "fan_social",
        ["marketing"],
    ),
    # ── Live & touring (5) ──────────────────────────────────────────────────
    (
        "venue-hawk",
        "We are researching festival venues and need to understand the promoter contract and box office splits",
        "live_touring",
        ["legal", "finance_royalties"],
    ),
    (
        "live-wire",
        "We are advancing a concert tour and need to review the promoter contract and royalty splits",
        "live_touring",
        ["legal", "finance_royalties"],
    ),
    (
        "booking-agent",
        "We have a festival booking offer and need to review the contract terms before signing",
        "live_touring",
        ["legal"],
    ),
    (
        "live-coach",
        "How do we prepare the stage show for the touring schedule and manage contractual performance obligations?",
        "live_touring",
        ["legal"],
    ),
    (
        "schedule-keeper",
        "How do we align the release planning timeline with our touring schedule and label delivery commitments?",
        "live_touring",
        ["label_ops"],
    ),
    # ── Playlist & DSP (2) ──────────────────────────────────────────────────
    (
        "airwave",
        "How do we develop a playlist pitching strategy alongside our marketing campaign for radio promotion?",
        "playlist_dsp",
        ["marketing"],
    ),
    (
        "release-strategist",
        "How do we build a DSP release strategy that supports the marketing rollout and fan community?",
        "playlist_dsp",
        ["marketing", "fan_social"],
    ),
    # ── Business development (3) ─────────────────────────────────────────────
    (
        "merch-empire",
        "How do mechanical royalties and publishing splits work on a track bundled with merch?",
        "bizdev",
        ["finance_royalties", "publishing"],
    ),
    (
        "storefront",
        "How do we build a D2C fan store with community features and brand partnerships?",
        "bizdev",
        ["fan_social"],
    ),
    (
        "mobile-monetize",
        "We want to build a platform partnership with royalty sharing and brand co-promotion",
        "bizdev",
        ["finance_royalties"],
    ),
    # ── A&R / talent (3) ────────────────────────────────────────────────────
    (
        "global-scout",
        "We are scouting emerging artists internationally and need to understand sync licensing and territory rights",
        "ar",
        ["sync", "legal"],
    ),
    (
        "collab-connect",
        "We want to set up an artist collaboration deal with a co-write and publishing admin agreement",
        "ar",
        ["bizdev", "publishing"],
    ),
    # ── Data & analytics (1) ────────────────────────────────────────────────
    (
        "data-oracle",
        "We need to analyze streaming data and DSP metrics to forecast listener trajectory",
        "data_analytics",
        ["playlist_dsp"],
    ),
    # ── Production (1) ──────────────────────────────────────────────────────
    (
        "audio-quality",
        "We need to QC mixing and mastering quality against DSP delivery specifications and metadata requirements",
        "production",
        ["digital_ops"],
    ),
    # ── Management (2) ──────────────────────────────────────────────────────
    (
        "music-edu",
        "We are helping an artist understand their management contract and career strategy options",
        "management",
        ["legal"],
    ),
    (
        "artist-wellness",
        "We are supporting an artist managing burnout while on a demanding touring schedule",
        "management",
        ["live_touring"],
    ),
    # ── Label operations (1) ────────────────────────────────────────────────
    (
        "label-services",
        "We need to deliver our release to DSPs, correct the metadata, and negotiate distribution deal terms",
        "label_ops",
        ["digital_ops"],
    ),
]

# NARROW_MATRIX: one row per distinct home-agent domain (16 domains covered).
# (agent_slug, narrow_query, home_domain)
# Asserts: result["domains"] == [home_domain]  (no spurious cross-domain)
NARROW_MATRIX = [
    ("ar-scout",        "Who are the top unsigned artists to scout in the indie scene right now?",                                              "ar"),
    ("grid-prophet",    "What is the best content strategy for growing Instagram followers and reach?",                                         "marketing"),
    ("sync-agent",      "How do we pitch a sync placement to a music supervisor for a film soundtrack?",                                        "sync"),
    ("brand-connect",   "What is the best approach for structuring a brand endorsement deal?",                                                  "bizdev"),
    ("lex-cipher",      "What is the difference between an indemnity clause and a liability waiver?",                                           "legal"),
    ("tour-commander",  "How do we build an efficient tour routing that minimizes travel costs between venues?",                                 "live_touring"),
    ("ink-and-air",     "How do we register a co-write and find a sub-publishing deal for our songs?",                                             "publishing"),
    ("royalty-doctor",  "How do we calculate mechanical royalty rates for streaming and physical formats?",                                      "finance_royalties"),
    ("producer-connect","What are the best LUFS and true peak targets for mixing and mastering today?",                                          "production"),
    ("fund-phantom",    "What non-dilutive grant programs are available for independent music companies?",                                       "capital_funding"),
    ("data-oracle",     "How do we build a cohort retention model to measure listener decay curves?",                                           "data_analytics"),
    ("puppet-master",   "How do we build a scenario planning framework for go/no-go strategic decisions?",                                      "executive"),
    ("fan-builder",     "How do we design a superfan tier system and track community health?",                                                   "fan_social"),
    ("label-services",  "How do we set up a release tracker and manage the distribution deal terms?",                                           "label_ops"),
    ("music-edu",       "How do we structure a management agreement with the right commission scope and sunset provisions?",                     "management"),
    ("airwave",         "How do we increase our Discover Weekly and Release Radar adds through DSP strategy improvements?",                     "playlist_dsp"),
]

# ORPHAN_REACH_MATRIX: the three domains with no home agent must be reachable
# cross-domain from any agent via keyword matching.
# (agent_slug, query, agent_home, orphan_domain_that_must_appear)
ORPHAN_REACH_MATRIX = [
    (
        "royalty-doctor",
        "We need to close the books, run bank reconciliation and verify our ledger integrity",
        "finance_royalties",
        "controller",
    ),
    (
        "label-services",
        "How do we handle ISRC metadata assignments and content id for DSP delivery?",
        "label_ops",
        "digital_ops",
    ),
    (
        "grid-prophet",
        "What market intelligence and industry developments should inform our marketing campaign?",
        "marketing",
        "intelligence",
    ),
]


# ── Sanity: all 44 agents are accounted for ──────────────────────────────────────

def test_consult_matrix_covers_all_44_agents():
    """Every agent in AGENT_HOME appears exactly once in CONSULT_MATRIX."""
    matrix_agents = [row[0] for row in CONSULT_MATRIX]
    missing = set(AGENT_HOME) - set(matrix_agents)
    duplicates = [a for a in matrix_agents if matrix_agents.count(a) > 1]
    assert not missing,    f"Agents missing from CONSULT_MATRIX: {sorted(missing)}"
    assert not duplicates, f"Duplicate agents in CONSULT_MATRIX: {sorted(set(duplicates))}"
    assert len(CONSULT_MATRIX) == 44


# ── Positive consult tests (44 agents) ──────────────────────────────────────────

@pytest.mark.parametrize(
    "agent, query, home, cross",
    CONSULT_MATRIX,
    ids=[row[0] for row in CONSULT_MATRIX],
)
def test_consult_home_leads_and_cross_domains_present(agent, query, home, cross):
    """
    Home domain is always first; every expected cross-domain is in the result.
    Verifies: home-first invariant + cross-domain routing quality.
    """
    result = _consult(agent, query)

    assert result["home_domain"] == home, (
        f"{agent}: expected home={home!r}, got {result['home_domain']!r}"
    )
    assert result["domains"], f"{agent}: domains list is empty"
    assert result["domains"][0] == home, (
        f"{agent}: home domain must be first; got {result['domains']}"
    )
    for d in cross:
        assert d in result["domains"], (
            f"{agent}: expected cross-domain {d!r} not found in {result['domains']}"
        )
    assert result["knowledge"].strip(), f"{agent}: knowledge text is empty"


# ── Negative / narrow tests (16 home domains) ───────────────────────────────────

@pytest.mark.parametrize(
    "agent, query, home",
    NARROW_MATRIX,
    ids=[row[0] for row in NARROW_MATRIX],
)
def test_narrow_query_returns_home_domain_only(agent, query, home):
    """
    A narrowly-scoped, domain-specific question must return only the home domain
    with no spurious cross-domain hits — proving the routing does not over-fire.
    """
    result = _consult(agent, query)

    assert result["home_domain"] == home
    assert result["domains"] == [home], (
        f"{agent}: expected ['{home}'] only, got {result['domains']!r}\n"
        f"Query: {query!r}"
    )


# ── Orphan-domain reachability tests (3 domains) ────────────────────────────────

@pytest.mark.parametrize(
    "agent, query, agent_home, orphan",
    ORPHAN_REACH_MATRIX,
    ids=[row[3] for row in ORPHAN_REACH_MATRIX],
)
def test_orphan_domain_reachable_cross_domain(agent, query, agent_home, orphan):
    """
    controller / digital_ops / intelligence have no home agent but must be
    reachable via keyword matching on any agent's cross-domain consult.
    """
    result = _consult(agent, query)

    assert result["home_domain"] == agent_home
    assert result["domains"][0] == agent_home
    assert orphan in result["domains"], (
        f"Orphan domain {orphan!r} not reached by {agent!r}.\n"
        f"Got domains: {result['domains']}\nQuery: {query!r}"
    )
    assert result["knowledge"].strip()
