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
