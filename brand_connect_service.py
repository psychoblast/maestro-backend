"""
PLMKR Brand Connect — brand-partnership action service (mock-first).

Backs the Brand Connect (Nia — Brand Partnerships) agent's tool_use loop in
/api/chat_stream (see BRAND_CONNECT_TOOLS in main.py). Nia does not just advise on
brand deals, endorsements, and sponsorships — these functions let the agent take
real partnership actions: search the directory of brands seeking artist
partnerships (each carrying the category it sits in, its sponsorship budget tier,
its typical deal fee, the audience-fit it has with the artist, and how many
campaign slots it opens), draft a concrete partnership proposal by applying a
brand's numbers to a specific campaign so the artist has a value-backed offer to
send, and submit that proposal through the artist's connected brand-partnerships
account so a deal actually gets pitched on their behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live brand/agency/DSP APIs, no submission rails, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_brand_connect_account_connected``) driven by an env flag
    so tests can toggle the connected / not-connected / expired states
    deterministically — mirroring airwave_service._airwave_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os

import brand_partnerships_data


class BrandConnectAccountNotConnected(Exception):
    """Raised when the artist has not connected a brand-partnerships account.

    Mirrors airwave_service.AirwaveAccountNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your brand-partnerships
    account first' result instead of crashing the stream.
    """


class BrandConnectAuthExpired(Exception):
    """Raised when a previously connected brand-partnerships authorization expired."""


# ── Brand directory (in-memory reference data) ─────────────────────────────────
# A curated set of brands actively seeking artist partnerships. Each brand carries
# its category, its sponsorship budget tier, the typical fee it pays for a single
# campaign, the artist's realistic audience-fit (percent overlap that makes the
# partnership land), and how many campaign slots it opens. The agent can surface
# the right brands for a campaign and apply a brand's numbers to draft a real
# proposal. No I/O.
_BRANDS = [
    {
        "id": "brand-solace-audio",
        "name": "Solace Audio",
        "category": "tech",
        "budget_tier": "premium",
        "typical_fee": 40000,
        "audience_fit_pct": 30,
        "campaign_slots": 3,
    },
    {
        "id": "brand-v612-apparel",
        "name": "V612 Apparel",
        "category": "apparel",
        "budget_tier": "growth",
        "typical_fee": 18000,
        "audience_fit_pct": 45,
        "campaign_slots": 6,
    },
    {
        "id": "brand-northbrew",
        "name": "Northbrew Coffee",
        "category": "beverage",
        "budget_tier": "emerging",
        "typical_fee": 6000,
        "audience_fit_pct": 25,
        "campaign_slots": 10,
    },
    {
        "id": "brand-pulse-gaming",
        "name": "Pulse Gaming",
        "category": "gaming",
        "budget_tier": "premium",
        "typical_fee": 55000,
        "audience_fit_pct": 20,
        "campaign_slots": 2,
    },
    {
        "id": "brand-lumen-beauty",
        "name": "Lumen Beauty",
        "category": "beauty",
        "budget_tier": "growth",
        "typical_fee": 22000,
        "audience_fit_pct": 38,
        "campaign_slots": 5,
    },
    {
        "id": "brand-ridgeline-outdoor",
        "name": "Ridgeline Outdoor",
        "category": "apparel",
        "budget_tier": "emerging",
        "typical_fee": 9000,
        "audience_fit_pct": 33,
        "campaign_slots": 8,
    },
]


async def search_brand_partners(category: str = "", budget_tier: str = "") -> dict:
    """Search brand partners by the category they sit in and/or their budget tier.

    Both filters are optional and matched case-insensitively as substrings.
    ``category`` matches the brand's category (e.g. "tech", "apparel", "beverage",
    "gaming", "beauty"), and ``budget_tier`` matches the sponsorship budget tier it
    operates at (e.g. "emerging", "growth", "premium"). Returns
    {"brands": [...], "count": int}. Pure — no I/O.
    """
    cat = (category or "").strip().lower()
    tier = (budget_tier or "").strip().lower()
    matches = [
        dict(b)
        for b in _BRANDS
        if (not cat or cat in b["category"].lower())
        and (not tier or tier in b["budget_tier"].lower())
    ]
    return {"brands": matches, "count": len(matches)}


def _get_brand(brand_id: str) -> dict | None:
    bid = (brand_id or "").strip()
    for b in _BRANDS:
        if b["id"] == bid:
            return b
    return None


async def draft_partnership_proposal(
    artist_id: str,
    brand_id: str = "",
    campaign_type: str = "",
    fee: int = 0,
) -> dict:
    """Draft a concrete brand-partnership proposal by applying a brand's numbers to a campaign.

    Deterministic proposal construction — never contacts a brand, agency, or API.
    Looks the brand up by id, checks a campaign type is present, and estimates the
    fair deal value (the brand's typical fee adjusted for audience-fit) alongside
    the artist's proposed fee. Returns a structured proposal with line items, the
    fair value, gaps, and a recommendation of "send" / "revise" / "blocked".
    """
    brand = _get_brand(brand_id)

    try:
        proposed_fee = int(fee or 0)
    except (TypeError, ValueError):
        proposed_fee = 0

    gaps = []
    if not (campaign_type or "").strip():
        gaps.append("missing_campaign_type")
    if proposed_fee <= 0:
        gaps.append("missing_fee")
    if not (brand_id or "").strip():
        gaps.append("missing_brand")
    elif brand is None:
        gaps.append("unknown_brand")

    line_items = []
    fair_value = 0
    if brand is not None:
        fair_value = int(
            round(brand["typical_fee"] * (100 + brand["audience_fit_pct"]) / 100.0)
        )
        line_items.append({"label": "typical_fee", "amount": brand["typical_fee"]})
        line_items.append({"label": "audience_fit_pct", "amount": brand["audience_fit_pct"]})
        line_items.append({"label": "fair_value", "amount": fair_value})

    if "unknown_brand" in gaps or "missing_brand" in gaps:
        # Without a valid brand the proposal cannot be built at all.
        recommendation = "blocked"
    elif gaps:
        recommendation = "revise"
    else:
        recommendation = "send"
    viable = recommendation == "send"

    return {
        "viable": viable,
        "gaps": gaps,
        "brand_id": brand["id"] if brand else (brand_id or "").strip(),
        "brand_name": brand["name"] if brand else None,
        "category": brand["category"] if brand else None,
        "budget_tier": brand["budget_tier"] if brand else None,
        "campaign_type": (campaign_type or "").strip(),
        "proposed_fee": proposed_fee,
        "line_items": line_items,
        "fair_value": fair_value,
        "recommendation": recommendation,
    }


def _brand_connect_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's brand-partnerships account.

    In production this would look up a stored brand-partnerships link for the
    artist. Here it is driven purely by the ``BRAND_CONNECT_ACCOUNT_CONNECTED`` env
    flag so tests can toggle connected / expired / not-connected with ZERO network
    calls and NO real secret. Values:
      - "expired"                     → raise BrandConnectAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("BRAND_CONNECT_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise BrandConnectAuthExpired("brand-partnerships authorization expired")
    return val in ("1", "true", "yes", "connected")


async def submit_partnership_proposal(
    artist_id: str,
    brand_id: str,
    campaign_type: str,
    fee: int = 0,
) -> dict:
    """Submit a brand-partnership proposal via the artist's connected account.

    Raises BrandConnectAccountNotConnected / BrandConnectAuthExpired when no
    brand-partnerships account is linked so the caller can surface a 'connect your
    account' message instead of a hard failure. When the brand id is unknown,
    returns a structured {"status": "unknown_brand"} result rather than raising. On
    success returns a deterministic mock proposal reference — NO network call is
    ever made and no proposal is actually delivered.
    """
    if not _brand_connect_account_connected(artist_id):
        raise BrandConnectAccountNotConnected(
            "artist has not connected a brand-partnerships account"
        )
    brand = _get_brand(brand_id)
    if brand is None:
        return {"status": "unknown_brand", "brand_id": (brand_id or "").strip()}
    ct = (campaign_type or "").strip()
    try:
        proposed_fee = int(fee or 0)
    except (TypeError, ValueError):
        proposed_fee = 0
    digest = hashlib.sha1(
        f"{artist_id}:{brand['id']}:{ct}:{proposed_fee}".encode("utf-8")
    ).hexdigest()
    reference = "PROP-" + digest[:10].upper()
    return {
        "status": "submitted",
        "reference": reference,
        "brand_id": brand["id"],
        "brand_name": brand["name"],
        "campaign_type": ct,
        "proposed_fee": proposed_fee,
    }


# ── Unit-2 doctrine lookup + pitch send rail ───────────────────────────────────
# lookup_brand_deal_doctrine is a PURE read over brand_partnerships_data (no gate,
# no I/O). send_brand_pitch follows the Marcus send seam: the MODEL writes the
# pitch body in its turn and passes it in — the tool SENDS (mock), it never
# generates or edits the body — behind the same BRAND_CONNECT_ACCOUNT_CONNECTED
# gate as submit_partnership_proposal, with a deterministic mock sha1 reference
# and ZERO network. No market rate is ever invented in either function.

# The one-topic doctrine surface: the seven DEAL_TERMS records by their stable id,
# plus the category surface and the outreach doctrine. Built at import from the
# corpus so the ids stay in lockstep. Reference only — nothing mutates these
# objects (they ride out through json.dumps downstream).
_BRAND_DOCTRINE_SECTIONS = {r["id"]: r for r in brand_partnerships_data.DEAL_TERMS}
_BRAND_DOCTRINE_SECTIONS["categories"] = brand_partnerships_data.BRAND_CATEGORIES
_BRAND_DOCTRINE_SECTIONS["outreach"] = brand_partnerships_data.OUTREACH_DOCTRINE

BRAND_DOCTRINE_TOPICS = ("deliverables", "compensation", "usage_rights",
                         "exclusivity", "approval_workflow", "disclosure",
                         "termination_morals", "categories", "outreach")


async def lookup_brand_deal_doctrine(topic: str = "") -> dict:
    """Look up the doctrine for ONE brand-deal topic — pure corpus read, no gate.

    Returns the relevant brand_partnerships_data section plus the FULL honesty-rule
    set (no market rate is ever invented; deal evaluation is structural, never a
    good/bad verdict; disclosure is convention, not legal advice). An unknown topic
    returns a structured ``unknown_topic`` error listing the supported topics. No
    I/O, no LLM, nothing invented.
    """
    t = (topic or "").strip().lower()
    honesty_rules = [dict(r) for r in brand_partnerships_data.HONESTY_RULES]
    if t in _BRAND_DOCTRINE_SECTIONS:
        return {
            "status": "ok",
            "topic": t,
            "data": _BRAND_DOCTRINE_SECTIONS[t],
            "honesty_rules": honesty_rules,
        }
    return {
        "status": "unknown_topic",
        "topic": t or "(missing)",
        "supported_topics": list(BRAND_DOCTRINE_TOPICS),
        "message": ("Unsupported topic. Supported: "
                    + ", ".join(BRAND_DOCTRINE_TOPICS) + "."),
    }


async def send_brand_pitch(artist_id: str, brand_id: str, subject: str = "",
                           body: str = "") -> dict:
    """Send an artist's brand pitch — the MODEL wrote the body; this tool only sends.

    The pitch ``subject`` and ``body`` are written by the model in its turn and
    passed in verbatim; this function NEVER generates or edits them and NEVER
    invents a rate. It follows submit_partnership_proposal's gate seam: raises
    BrandConnectAccountNotConnected / BrandConnectAuthExpired when no
    brand-partnerships account is linked (so the caller can surface a 'connect your
    account' message), returns a structured {"status": "unknown_brand"} for an
    unknown brand, and on success returns a deterministic mock send reference —
    NO network call is ever made and no pitch is actually delivered. The supplied
    subject/body ride back out byte-exact so the caller can confirm what was sent.
    """
    if not _brand_connect_account_connected(artist_id):
        raise BrandConnectAccountNotConnected(
            "artist has not connected a brand-partnerships account"
        )
    brand = _get_brand(brand_id)
    if brand is None:
        return {"status": "unknown_brand", "brand_id": (brand_id or "").strip()}
    digest = hashlib.sha1(
        f"{artist_id}:{brand['id']}:{subject}:{body}".encode("utf-8")
    ).hexdigest()
    reference = "BPITCH-" + digest[:10].upper()
    return {
        "status": "sent",
        "reference": reference,
        "brand_id": brand["id"],
        "brand_name": brand["name"],
        "subject": subject,   # verbatim — the tool never edits the model's pitch
        "body": body,         # verbatim — never generated or modified here
    }
