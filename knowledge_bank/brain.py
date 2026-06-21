"""
Knowledge bank "brain" — deterministic retrieval/routing layer.

Given a free-text query (and optionally the asking agent's home domain), the
brain decides WHICH expert domains are relevant and assembles their knowledge.

This implementation is PURE deterministic Python: keyword routing over the
domain catalog. It performs NO LLM/API calls. ``route`` is intentionally the
single decision point so it can be swapped for a smarter implementation later
(embeddings, a classifier, an LLM) WITHOUT changing any caller of ``consult``.

Keywords are matched as lowercase substrings, so stems like ``royalt`` catch
"royalty"/"royalties" and ``licens`` catches "license"/"licensing"/"licensed".
"""
from knowledge_bank import registry

# ── Domain trigger keywords ──────────────────────────────────────────────────────
# Lowercase substrings. Stems are used deliberately to catch inflections.
# Keep cross-domain overlap minimal so routing stays predictable.
DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ar": (
        "a&r", "a & r", "scouting", "talent scout", "scout", "unsigned",
        "demo submission", "artist development", "develop the artist",
        "roster", "emerging artist", "breakout", "discovery", "prospect",
        "song selection", "single selection", "pick the song",
    ),
    "marketing": (
        "marketing", "campaign", "audience", "fanbase", "fan base", "growth",
        "social media", "instagram", "tiktok", "content strategy", "engagement",
        "playlist", "follower", "reach", "impressions", "ad spend", "rollout",
        "release strategy", "go-to-market", "go to market", "press strategy",
    ),
    "sync": (
        "sync", "synchronization", "licens", "placement", "film", "tv",
        "television", "advert", "trailer", "commercial spot", "cue sheet",
        "video game", "needle drop", "master use", "music supervisor", "spot ad",
    ),
    "bizdev": (
        "brand", "sponsor", "partnership", "partner ", "endorsement",
        "activation", "ambassador", "collaboration deal", "b2b",
        "business development", "brand deal", "commercial partnership",
    ),
    "legal": (
        "contract", "clause", "indemnit", "liabilit", "breach", "warrant",
        "copyright", "trademark", "infringement", "nda", "work for hire",
        "work-for-hire", "governing law", "jurisdiction", "rights", "dispute",
        "legal", "negotiat",
    ),
    "live_touring": (
        "tour", "touring", "concert", "gig", "venue", "booking", "stage",
        "live show", "setlist", "rider", "load-in", "load in", "promoter",
        "box office", "ticketing", "ticket", "festival", "routing", "on the road",
    ),
    "publishing": (
        "publish", "composition", "songwrit", "co-write", "cowrite", "co write",
        "catalog", "catalogue", "administration", "sub-publish", "subpublish",
        "writer share", "writer's share", "split sheet",
    ),
    "finance_royalties": (
        "royalt", "mechanical", "ascap", "bmi", "sesac", "performing rights org",
        "performance royalt", "splits", "split ", "recoup", "advance",
        "statement", "accounting", "collection society", "neighbouring rights",
        "neighboring rights", "points", "audit the label",
    ),
    "production": (
        "production", "producer", "beatmaker", "beat-maker", "mixing",
        "mix engineer", "mastering", "studio", "recording session",
        "stems", "vocal production", "loudness", "lufs", "true peak", "daw",
        "arrangement",
    ),
    "capital_funding": (
        "capital", "fund", "financ", "invest", "raise capital", "capital raise",
        "capital stack", "non-dilutive", "nondilutive", "dilut", "equity",
        "cap table", "valuation", "term sheet", "convertible", "safe note",
        "venture", "angel", "loan", "credit facility", "line of credit",
        "debt financing", "mezzanine", "covenant", "due diligence", "runway",
        "burn rate", "grant", "tax credit", "subsidy", "revenue-based",
        "war chest", "liquidation preference",
    ),
    "controller": (
        "controller", "ledger", "general ledger", "ledger integrity",
        "reconcil", "bank reconciliation", "balance sheet reconciliation",
        "period close", "month-end close", "month end close", "close the books",
        "close package", "close calendar", "closing the books",
        "audit trail", "audit-ready", "audit ready", "audit package",
        "audit readiness", "internal control", "segregation of duties",
        "revenue recognition", "rev-rec", "asc 606", "ifrs 15",
        "deferred revenue", "journal entry", "journal entries", "intercompany",
        "cost allocation", "misstatement", "materiality", "coso",
        "trial balance", "chart of accounts", "cut-off", "cutoff", "accrual",
        "benford", "duplicate payment", "duplicate-payment", "anomaly detection",
        "gaap", "certifiable",
    ),
    "data_analytics": (
        "analytics", "data analy", "data analyst", "data and analytics",
        "metric", "kpi", "denominator", "decision-grade", "decision grade",
        "save rate", "skip rate", "completion rate", "save-rate", "skip-rate",
        "listener-to-stream", "listener to stream", "streams per listener",
        "monthly listeners", "source of stream", "source-of-stream",
        "cohort", "retention", "churn", "trajectory", "decay curve", "decay rate",
        "forecast", "projection", "project the streams",
        "anomaly", "outlier", "stream spike", "level shift", "series break",
        "z-score", "z score", "standard deviation", "control chart",
        "statistical", "seasonal decomposition", "reference class",
        "benchmark", "comparable case", "like-for-like", "like for like",
        "artificial streaming", "bot stream", "stream farming", "fake streams",
        "streaming data", "stream count", "dsp metric", "dsp data",
        "spotify for artists", "apple music for artists",
        "chartmetric", "luminate", "songstats", "soundcharts",
        "chart position", "chart mechanics", "playlist add velocity",
    ),
    "digital_ops": (
        "digital operations", "digital ops", "metadata", "ddex", "ern",
        "id3", "isrc", "upc", "ean", "identifier", "barcode",
        "content id", "content-id", "content recognition", "rights manager",
        "rights management", "youtube cms", "claim dispute", "ugc claim",
        "fingerprint", "reference file", "takedown", "redeliver", "redelivery",
        "delivery spec", "delivery specification", "dsp delivery",
        "distributor", "ingestion", "metadata error", "delivery rejection",
        "rejected delivery", "artwork spec", "colorspace", "rights hygiene",
        "catalog metadata", "metadata governance", "metadata debt",
        "territory configuration", "territory availability", "rights coverage",
        "iswc", "pre-delivery qc", "pre delivery qc", "metadata completeness",
        "deduplication", "split isrc", "duplicate isrc", "isrc conflict",
    ),
    "executive": (
        "executive", "ceo", "chief executive", "c-suite", "c suite",
        "enterprise value", "enterprise-value", "enterprise decision",
        "shareholder value", "owner value", "value creation",
        "capital allocation", "allocate capital", "capital deployment",
        "deploy capital", "capital efficiency", "marginal dollar",
        "go/no-go", "go / no-go", "go no go", "no-go", "go-decision",
        "decision memo", "executive decision", "decision synthesis",
        "hurdle rate", "roic", "return on invested capital", "cost of capital",
        "npv", "discounted cash flow", "payback period", "reinvest",
        "build vs buy", "build-vs-buy", "build or buy", "build/buy",
        "buy vs build", "m&a", "merger", "acquisition", "catalog acquisition",
        "corporate strategy", "enterprise strategy", "business strategy",
        "strategic direction", "strategic priorit", "strategic fit",
        "where to play", "where-to-play", "how to win", "how-to-win",
        "moat", "competitive advantage", "competitive position",
        "durable advantage", "portfolio strategy", "portfolio construction",
        "portfolio coherence", "opportunity cost", "next-best alternative",
        "next best alternative", "prioritize", "prioritization", "prioritise",
        "kill criteria", "kill decision", "kill-or-continue",
        "scenario planning", "scenario forecast", "base case", "bull case",
        "bear case", "base/bull/bear", "stress test", "stress-test",
        "sensitivity analysis", "enterprise risk", "risk tolerance",
        "risk register", "risk appetite", "risk governance", "governance",
        "board report", "board-level", "fiduciary", "optionality",
        "staged commitment", "staged funding", "reversibility",
        "irreversible decision", "diversification", "concentration risk",
        "single point of failure", "single-point-of-failure", "key-person",
        "key person risk", "succession plan", "market entry", "market-entry",
        "business expansion", "expansion strategy", "crisis management",
        "crisis leadership", "crisis response", "spend authority",
        "decision rights", "competing priorities", "conflicting advice",
        "reconcile", "should we sign", "should we acquire", "should we enter",
    ),
    "fan_social": (
        "superfan", "super-fan", "super fan", "fandom", "parasocial",
        "fan community", "fan-community", "community architecture",
        "owned channel", "owned-channel", "owned vs rented", "rented platform",
        "d2c", "direct-to-fan", "direct to fan", "direct-to-consumer fan",
        "fan club", "fan-club", "street team", "street-team", "street captain",
        "ambassador program", "ambassador tier", "fan mobilization",
        "fan engagement", "fan relationship", "fan loyalty", "fan retention",
        "fan lifecycle", "fan journey", "fan data", "fan crm", "fan segmentation",
        "fan identity", "identity fusion", "superfan economics", "superfan tier",
        "superfan concentration", "fan monetization", "fan-funding", "fan funding",
        "membership tier", "subscription tier", "patreon", "discord",
        "community server", "listening party", "fan-to-fan", "casual listener",
        "casual fan", "evangelist fan", "ugc", "user-generated content",
        "user generated content", "behind-the-scenes content", "artist-voice content",
        "community health", "engagement rate", "save rate", "email list",
        "sms list", "fanbase health", "fan-base health", "build the community",
    ),
    "intelligence": (
        "intelligence", "market intelligence", "competitive intelligence",
        "industry intelligence", "industry scan", "scan the industry",
        "scan the market", "weekly scan", "intelligence scan", "intelligence feed",
        "industry news", "industry development", "structural development",
        "structural shift", "market structure shift", "what's changing",
        "what is changing", "keep us current", "stay current", "stay ahead",
        "early warning", "early-warning", "industry monitoring", "monitor the industry",
        "decision-relevant", "decision relevant", "decision-change", "decision change test",
        "so what test", "so-what test", "consequential development", "cdm class",
        "four-filter", "four filter", "signal vs noise", "signal-to-noise",
        "signal to noise", "source tier", "trust tier", "sourcing tier",
        "tier a", "tier b", "tier d", "primary source", "trade source",
        "strong trade", "corroborat", "triangulat", "star protocol",
        "rumor", "unconfirmed", "anti-fabrication", "temporal fabrication",
        "stale data", "recency", "currency with consequence",
        "trigger fatigue", "alert fatigue", "rule-changer", "rule changer",
        "strategy-invalidator", "opportunity-creator", "monitoring signal",
        "not evaluable", "quiet week", "quiet cycle", "trigger vs weekly",
        "route the development", "territory lens", "territory scan", "newsworth",
    ),
    "label_ops": (
        "label ops", "label operations", "label operation", "label gm",
        "label general manager", "vp of operations", "operations desk",
        "release planning", "release plan", "release campaign", "campaign arc",
        "release workflow", "release schedule", "release tracking", "release tracker",
        "release readiness", "release ready", "readiness gate", "release gate",
        "release type", "release window", "release-day", "release day protocol",
        "milestone timeline", "campaign timeline", "release cadence", "friday release",
        "pre-save", "presave", "pre-add", "pre-release activation",
        "editorial pitch", "editorial submission", "pitch window", "pitch the playlist",
        "pre-delivery qc", "pre delivery qc", "delivery qc", "delivery lead time",
        "delivery failure", "delivery rejection", "qc checklist", "qc workflow",
        "deliver the release", "release delivery",
        "distributor", "distribution partner", "distribution deal",
        "distribution selection", "distribution strategy", "distribution vehicle",
        "aggregator", "diy aggregator", "mid-tier distribution",
        "full-service distribution", "pick a distributor", "choose a distributor",
        "recoup", "recoupment", "recoupable", "unrecouped", "recoupment projection",
        "cross-collateral", "cross collateral", "controlled composition",
        "controlled comp", "recording agreement", "recording contract", "label deal",
        "deal structure", "deal terms", "360 deal", "multiple rights deal",
        "production deal", "vanity label", "option period", "delivery commitment",
        "advance sizing", "size the advance", "advance against streaming",
        "label p&l", "label economics", "label margin", "label profit",
        "cost center", "royalty waterfall", "royalty statement",
        "royalty accounting system", "recoupment clock",
        "catalog management", "catalog exploitation", "catalog audit",
        "catalog optimization", "catalog reissue", "re-release", "rerelease",
        "remaster", "catalog licensing", "catalog reversion", "reversion clause",
        "reversion clock", "catalog strategy", "exploit the catalog",
        "sync-readiness", "sync readiness",
        "roster coordination", "roster management", "artist roster coordination",
        "priority stack", "project kickoff", "kickoff checklist", "kickoff protocol",
        "a&r handoff", "a&r-to-ops", "handoff failure", "label head",
        "label tech stack", "four-layer stack", "rights management system",
        "master isrc registry", "spatial audio", "dolby atmos",
    ),
    "management": (
        "artist manager", "artist management", "personal manager",
        "music manager", "day-to-day manager", "manage the artist",
        "managing the artist", "manage an artist", "represent the artist",
        "artist representation", "manager-artist", "artist-manager",
        "management agreement", "management contract", "management commission",
        "management deal", "management term", "commission structure",
        "commission rate", "commission scope", "commission type",
        "gross commission", "net commission", "modified net", "adjusted gross",
        "touring commission", "recording commission", "post-term commission",
        "sunset clause", "sunset provision", "post-term provision", "post term",
        "key-person clause", "key person clause", "key-person", "holdback clause",
        "career phase", "career-phase", "career strategy", "career trajectory",
        "career architecture", "career stage", "career-stage", "phase fit",
        "positioning triangle", "artist positioning", "positioning consistency",
        "momentum management", "career momentum", "opportunity stack",
        "opportunity triage", "offer evaluation", "inbound triage",
        "team assembly", "team coordination", "assemble the team",
        "build the team", "professional team", "core team", "team completeness",
        "team sequencing", "hiring sequence", "entertainment attorney",
        "entertainment lawyer", "loan-out", "loan out company", "loanout",
        "approval funnel", "gatekeeping", "gatekeeper", "scope fence",
        "development vs market", "development vs. market", "market readiness",
        "artist readiness", "ready for market", "ready to market",
        "crisis management", "reputation management", "crisis triage",
        "image risk", "morality clause", "category exclusivity",
        "not ready for editorial", "say no to the artist", "protect the artist",
    ),
}


def _keyword_route(query: str) -> list[str]:
    """Return matched domain keys in catalog order (no home handling)."""
    q = (query or "").lower()
    matched: list[str] = []
    for key in registry.list_domains():
        for kw in DOMAIN_KEYWORDS.get(key, ()):  # tolerate a domain with no keywords
            if kw in q:
                matched.append(key)
                break
    return matched


def route(query: str, home_domain: str | None = None) -> list[str]:
    """
    Decide which domains are relevant to ``query``.

    Rules:
    - ``home_domain`` (if given) is ALWAYS included, and always first.
    - Any domain whose keywords appear in the lowercased query is added.
    - Results are de-duplicated; order is stable (home first, then catalog order).
    - No keyword match and no home domain → ``[]``.

    This is the single, swappable decision point for the bank. A smarter
    implementation can replace the body without changing ``consult`` or callers.
    """
    ordered: list[str] = []
    if home_domain:
        ordered.append(home_domain)
    for key in _keyword_route(query):
        if key not in ordered:
            ordered.append(key)
    return ordered


def consult(
    query: str,
    home_domain: str | None = None,
    max_domains: int = 4,
    skills_dir=None,
) -> dict:
    """
    Route ``query`` to domains and assemble their knowledge.

    Returns ``{"domains": [keys...], "knowledge": "<text sectioned per domain>"}``.
    The selected domains are capped at ``max_domains`` (home + earliest matches).
    Each domain's text is prefixed with a section header so the reader can orient.

    Pure deterministic assembly — NO LLM/API calls.
    """
    domains = route(query, home_domain=home_domain)[:max_domains]

    sections: list[str] = []
    for key in domains:
        domain = registry.get_domain(key)
        body = registry.load_domain(key, skills_dir=skills_dir)
        sections.append(f"# {domain.display_name} ({key})\n\n{body}")

    return {
        "domains": domains,
        "knowledge": "\n\n========================================\n\n".join(sections),
    }
