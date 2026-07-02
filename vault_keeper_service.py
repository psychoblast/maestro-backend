"""
PLMKR Vault-Keeper — business-manager action service (mock-first).

Backs the Vault-Keeper (Victor — Business Manager) agent's tool_use loop in
/api/chat_stream (see VAULT_KEEPER_TOOLS in main.py). Victor does not just advise
on budgets and cashflow — these functions let the agent take real business-manager
actions: look up a budget template appropriate to the artist's project (a single
release, a tour, a video, a marketing campaign), build a concrete project budget
by applying that template's category allocations to an estimated revenue figure,
and schedule an expense payment to a payee out of the artist's operating account
so the money actually moves on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live banking APIs, no payment rails, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_vault_account_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring mech_ledger_service._mech_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os


class VaultAccountNotConnected(Exception):
    """Raised when the artist has not connected an operating/bank account.

    Mirrors mech_ledger_service.MechAccountNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class VaultAccountAuthExpired(Exception):
    """Raised when a previously connected operating-account authorization expired."""


# ── Budget template library (in-memory reference data) ─────────────────────────
# A curated set of business-manager budget templates. Each template carries a set
# of spend categories with percentage-of-revenue allocations that sum to 100, so
# the agent can build a concrete project budget by applying the template to an
# estimated revenue figure. Keyed loosely on project type / tier so the agent can
# surface the right starting point for an artist's plan. No I/O.
_TEMPLATES = [
    {
        "id": "budget-single-release",
        "name": "Single Release Budget",
        "project_type": "release",
        "tier": "starter",
        "categories": [
            {"name": "production", "pct": 30},
            {"name": "marketing", "pct": 40},
            {"name": "distribution", "pct": 10},
            {"name": "visuals", "pct": 20},
        ],
    },
    {
        "id": "budget-ep-release",
        "name": "EP Release Budget",
        "project_type": "release",
        "tier": "pro",
        "categories": [
            {"name": "production", "pct": 35},
            {"name": "marketing", "pct": 35},
            {"name": "distribution", "pct": 10},
            {"name": "visuals", "pct": 20},
        ],
    },
    {
        "id": "budget-club-tour",
        "name": "Club Tour Budget",
        "project_type": "tour",
        "tier": "starter",
        "categories": [
            {"name": "travel", "pct": 35},
            {"name": "lodging", "pct": 20},
            {"name": "crew", "pct": 25},
            {"name": "production", "pct": 20},
        ],
    },
    {
        "id": "budget-theatre-tour",
        "name": "Theatre Tour Budget",
        "project_type": "tour",
        "tier": "pro",
        "categories": [
            {"name": "travel", "pct": 25},
            {"name": "lodging", "pct": 20},
            {"name": "crew", "pct": 30},
            {"name": "production", "pct": 25},
        ],
    },
    {
        "id": "budget-music-video",
        "name": "Music Video Budget",
        "project_type": "video",
        "tier": "pro",
        "categories": [
            {"name": "crew", "pct": 35},
            {"name": "location", "pct": 15},
            {"name": "equipment", "pct": 25},
            {"name": "post_production", "pct": 25},
        ],
    },
    {
        "id": "budget-social-campaign",
        "name": "Social Campaign Budget",
        "project_type": "campaign",
        "tier": "starter",
        "categories": [
            {"name": "ad_spend", "pct": 55},
            {"name": "content", "pct": 30},
            {"name": "tools", "pct": 15},
        ],
    },
]

# Expense categories the platform recognises on a scheduled payment.
_VALID_CATEGORIES = (
    "production", "marketing", "distribution", "visuals", "travel", "lodging",
    "crew", "location", "equipment", "post_production", "ad_spend", "content",
    "tools", "other",
)


async def search_budget_templates(project_type: str = "", tier: str = "") -> dict:
    """Search budget templates by project type and/or tier.

    Both filters are optional and matched case-insensitively as substrings.
    ``project_type`` matches the template's project type (e.g. "release", "tour"),
    and ``tier`` matches the template tier (e.g. "starter", "pro").
    Returns {"templates": [...], "count": int}. Pure — no I/O.
    """
    pt = (project_type or "").strip().lower()
    tr = (tier or "").strip().lower()
    matches = [
        dict(t)
        for t in _TEMPLATES
        if (not pt or pt in t["project_type"].lower())
        and (not tr or tr in t["tier"].lower())
    ]
    return {"templates": matches, "count": len(matches)}


def _get_template(template_id: str) -> dict | None:
    tid = (template_id or "").strip()
    for t in _TEMPLATES:
        if t["id"] == tid:
            return t
    return None


async def build_project_budget(
    artist_id: str,
    template_id: str = "",
    project_name: str = "",
    estimated_revenue: float = 0,
) -> dict:
    """Build a concrete project budget by applying a template to an estimated revenue.

    Deterministic budget construction — never contacts a wire. Looks the template
    up by id, checks a project name and a positive revenue figure are present, and
    allocates the revenue across the template's categories per their percentages.
    Returns a structured budget with line items, totals, projected net, and a
    recommendation of "proceed" / "adjust" / "blocked".
    """
    template = _get_template(template_id)

    try:
        revenue = round(float(estimated_revenue or 0), 2)
    except (TypeError, ValueError):
        revenue = 0.0

    gaps = []
    if not (project_name or "").strip():
        gaps.append("missing_project_name")
    if not (template_id or "").strip():
        gaps.append("missing_template")
    elif template is None:
        gaps.append("unknown_template")
    if revenue <= 0:
        gaps.append("non_positive_revenue")

    line_items = []
    total_allocated = 0.0
    if template is not None and revenue > 0:
        for cat in template["categories"]:
            amount = round(revenue * cat["pct"] / 100.0, 2)
            line_items.append({
                "category": cat["name"],
                "pct": cat["pct"],
                "amount": amount,
            })
            total_allocated = round(total_allocated + amount, 2)

    projected_net = round(revenue - total_allocated, 2)

    if "unknown_template" in gaps or "missing_template" in gaps:
        # Without a valid template target the budget cannot be built at all.
        recommendation = "blocked"
    elif gaps or projected_net < 0:
        recommendation = "adjust"
    else:
        recommendation = "proceed"
    viable = recommendation == "proceed"

    return {
        "viable": viable,
        "gaps": gaps,
        "template_id": template["id"] if template else (template_id or "").strip(),
        "template_name": template["name"] if template else None,
        "project_name": (project_name or "").strip(),
        "estimated_revenue": revenue,
        "line_items": line_items,
        "total_allocated": total_allocated,
        "projected_net": projected_net,
        "recommendation": recommendation,
    }


def _vault_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's operating/bank account.

    In production this would look up a stored bank/operating-account link for the
    artist. Here it is driven purely by the ``VAULT_KEEPER_ACCOUNT_CONNECTED`` env
    flag so tests can toggle connected / expired / not-connected with ZERO network
    calls and NO real secret. Values:
      - "expired"                     → raise VaultAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("VAULT_KEEPER_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise VaultAccountAuthExpired("operating-account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def schedule_expense_payment(
    artist_id: str,
    payee: str,
    amount: float,
    category: str = "",
) -> dict:
    """Schedule an expense payment to a payee out of the artist's operating account.

    Raises VaultAccountNotConnected / VaultAccountAuthExpired when no operating
    account is linked so the caller can surface a 'connect your account' message
    instead of a hard failure. On success returns a deterministic mock payment
    reference — NO network call is ever made and no money actually moves.
    """
    if not _vault_account_connected(artist_id):
        raise VaultAccountNotConnected(
            "artist has not connected an operating/bank account"
        )
    p = (payee or "").strip()
    cat = (category or "").strip().lower()
    try:
        amt = round(float(amount or 0), 2)
    except (TypeError, ValueError):
        amt = 0.0
    digest = hashlib.sha1(f"{artist_id}:{p}:{amt}:{cat}".encode("utf-8")).hexdigest()
    reference = "PMT-" + digest[:10].upper()
    return {
        "status": "scheduled",
        "reference": reference,
        "payee": p,
        "amount": amt,
        "category": cat,
    }
