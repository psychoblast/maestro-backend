"""
Agent → home-domain mapping for the knowledge bank.

PAIRED agents are the 9 whose expert knowledge lives in the bank; each has a
"home" domain that is included by default on every consultation. UNPAIRED agents
(every other agent, e.g. merch-empire, storefront) have NO home domain — they
still reach the bank, but only via query keyword matches.

``consult_for_agent`` is the convenience entrypoint a route/agent uses: it looks
up the agent's home (or None) and delegates to the deterministic brain.

NO LLM/API calls here.
"""
from knowledge_bank import brain

# Paired agent slug → home domain key. These 9 are the only paired agents;
# any slug not present here is treated as UNPAIRED (home = None).
AGENT_HOME: dict[str, str] = {
    "ar-scout":         "ar",
    "grid-prophet":     "marketing",
    "sync-agent":       "sync",
    "brand-connect":    "bizdev",
    "lex-cipher":       "legal",
    "tour-commander":   "live_touring",
    "ink-and-air":      "publishing",
    "royalty-doctor":   "finance_royalties",
    "producer-connect": "production",
}


def home_domain(agent_slug: str) -> str | None:
    """Return the agent's home domain key, or None if the agent is unpaired."""
    return AGENT_HOME.get(agent_slug)


def consult_for_agent(agent_slug: str, query: str, max_domains: int = 4) -> dict:
    """
    Consult the bank on behalf of an agent.

    Paired agents get their home domain by default (plus query matches); unpaired
    agents get pure query matches. Returns the brain's consult result enriched
    with ``agent`` and ``home_domain``.
    """
    home = home_domain(agent_slug)
    result = brain.consult(query, home_domain=home, max_domains=max_domains)
    result["agent"] = agent_slug
    result["home_domain"] = home
    return result
