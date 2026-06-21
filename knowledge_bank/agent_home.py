"""
Agent → home-domain mapping for the knowledge bank.

EVERY agent in the roster has a "home" domain — the expert domain included by
default on every consultation, before any query keyword matches. The first 9
entries are the originally PAIRED agents (their expert knowledge was authored
into the bank and is kept EXACTLY as-is); the remaining entries assign a sensible
home (drawn from the 19 catalog domains) to every other agent so the whole roster
flows through the brain. Many agents can share one domain (many-to-one).

``consult_for_agent`` is the convenience entrypoint a route/agent uses: it looks
up the agent's home and delegates to the deterministic brain, which always puts
the home domain first and then adds any cross-domain keyword matches.

NO LLM/API calls here.
"""
from knowledge_bank import brain

# Agent slug → home domain key.
#
# The first 9 are the originally PAIRED agents — DO NOT change these mappings.
AGENT_HOME: dict[str, str] = {
    # ── Originally paired (authored expert knowledge) — keep EXACTLY ──────────
    "ar-scout":         "ar",
    "grid-prophet":     "marketing",
    "sync-agent":       "sync",
    "brand-connect":    "bizdev",
    "lex-cipher":       "legal",
    "tour-commander":   "live_touring",
    "ink-and-air":      "publishing",
    "royalty-doctor":   "finance_royalties",
    "producer-connect": "production",

    # ── Executive / strategy ─────────────────────────────────────────────────
    "puppet-master":     "executive",   # Artist Manager — career strategy, deal analysis
    "ai-navigator":      "executive",   # AI tools / tech stack strategy

    # ── Finance & royalties ──────────────────────────────────────────────────
    "fund-phantom":      "capital_funding",   # grants & funding
    "border-royalty":    "finance_royalties", # neighbouring rights
    "mech-ledger":       "finance_royalties", # mechanical royalties
    "vault-keeper":      "finance_royalties", # business manager — budgets/cashflow
    "ledger-lock":       "finance_royalties", # accountant — tax/bookkeeping
    "rights-pulse":      "publishing",        # performance rights / PRO registration

    # ── Marketing / press / content ──────────────────────────────────────────
    "signal-blaster":    "marketing",   # publicist — PR campaigns
    "press-monitor":     "marketing",   # media monitor — coverage/sentiment
    "pr-agent":          "marketing",   # PR manager — editorial outreach
    "social-manager":    "marketing",   # social post strategy / scheduling
    "vision-forge":      "marketing",   # AI visuals / visual identity
    "design-studio":     "marketing",   # brand designer
    "creative-director":  "marketing",  # creative vision / rollout
    "video-director":    "marketing",   # music video
    "content-forge":     "marketing",   # captions / bios / press releases

    # ── Fan & social ─────────────────────────────────────────────────────────
    "fan-builder":       "fan_social",  # fan engagement / superfans / community

    # ── Live & touring ───────────────────────────────────────────────────────
    "venue-hawk":        "live_touring",
    "live-wire":         "live_touring",
    "booking-agent":     "live_touring",
    "live-coach":        "live_touring", # performance coach — stage/live
    "schedule-keeper":   "live_touring", # scheduling / deadlines

    # ── Playlist & DSP ───────────────────────────────────────────────────────
    "airwave":           "playlist_dsp", # radio & playlist plugging
    "release-strategist": "playlist_dsp", # release / campaign orchestration

    # ── Business development ─────────────────────────────────────────────────
    "merch-empire":      "bizdev",      # merchandise
    "storefront":        "bizdev",      # D2C fan store
    "mobile-monetize":   "bizdev",      # platform monetization

    # ── A&R / talent ─────────────────────────────────────────────────────────
    "global-scout":      "ar",          # international scouting / market entry
    "collab-connect":    "ar",          # collaborations / features / networking

    # ── Data & analytics ─────────────────────────────────────────────────────
    "data-oracle":       "data_analytics",

    # ── Production ───────────────────────────────────────────────────────────
    "audio-quality":     "production",  # mix/master QC

    # ── Management ───────────────────────────────────────────────────────────
    "music-edu":         "management",  # education
    "artist-wellness":   "management",  # wellness / burnout

    # ── Label operations ─────────────────────────────────────────────────────
    "label-services":    "label_ops",   # distribution / release / DSP delivery
}


def home_domain(agent_slug: str) -> str | None:
    """Return the agent's home domain key, or None if the agent has no mapping."""
    return AGENT_HOME.get(agent_slug)


def consult_for_agent(agent_slug: str, query: str, max_domains: int = 4) -> dict:
    """
    Consult the bank on behalf of an agent.

    The agent's home domain (if mapped) is always included first; any domain whose
    keywords appear in ``query`` is added after. An agent with no mapping still
    reaches the bank via pure query matches. Returns the brain's consult result
    enriched with ``agent`` and ``home_domain``.
    """
    home = home_domain(agent_slug)
    result = brain.consult(query, home_domain=home, max_domains=max_domains)
    result["agent"] = agent_slug
    result["home_domain"] = home
    return result
