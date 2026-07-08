"""
PLMKR Merch Empire — merchandise consult service (data-only + pure costing).

Backs the Merch Empire (Max — Merchandise) agent's tool_use loop in
/api/chat_stream (see MERCH_EMPIRE_TOOLS in main.py). Max is consult-only: search the
catalogue of blank product types the platform can produce (each carrying the
category it sits in, its production tier, the per-unit production cost, a suggested
retail price, and the minimum order quantity), and build a concrete production run
by applying a product's economics to a quantity so the artist has a costed,
margin-backed plan. The mock schedule_fulfillment_order terminal-action tool (and
its MERCH_EMPIRE_ACCOUNT_CONNECTED gate) was retired — Max never actually placed a
fulfilment order, so the tool implied a real-world action that never happened.

CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live print/fulfilment/POD APIs, no order rails, no LLM.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""


# ── Product catalogue (in-memory reference data) ───────────────────────────────
# A curated set of blank merch products the platform can produce. Each product
# carries its category, its production tier, the per-unit production cost, a
# suggested retail price, and the minimum order quantity. The agent can surface the
# right products for a drop and apply a product's numbers to cost a real production
# run. No I/O.
_PRODUCTS = [
    {
        "id": "merch-classic-tee",
        "name": "Classic Tee",
        "category": "apparel",
        "tier": "starter",
        "unit_cost": 8,
        "suggested_retail": 30,
        "min_order_qty": 25,
    },
    {
        "id": "merch-premium-hoodie",
        "name": "Premium Hoodie",
        "category": "apparel",
        "tier": "pro",
        "unit_cost": 22,
        "suggested_retail": 65,
        "min_order_qty": 25,
    },
    {
        "id": "merch-dad-cap",
        "name": "Embroidered Dad Cap",
        "category": "accessories",
        "tier": "starter",
        "unit_cost": 6,
        "suggested_retail": 25,
        "min_order_qty": 50,
    },
    {
        "id": "merch-tote-bag",
        "name": "Canvas Tote Bag",
        "category": "accessories",
        "tier": "starter",
        "unit_cost": 5,
        "suggested_retail": 20,
        "min_order_qty": 50,
    },
    {
        "id": "merch-tour-poster",
        "name": "Screen-Printed Tour Poster",
        "category": "print",
        "tier": "pro",
        "unit_cost": 4,
        "suggested_retail": 25,
        "min_order_qty": 100,
    },
    {
        "id": "merch-vinyl-lp",
        "name": "180g Vinyl LP",
        "category": "music",
        "tier": "pro",
        "unit_cost": 12,
        "suggested_retail": 35,
        "min_order_qty": 100,
    },
]

# Product categories the platform recognises on a search filter.
_VALID_CATEGORIES = ("apparel", "print", "accessories", "music")


async def search_merch_products(category: str = "", tier: str = "") -> dict:
    """Search the merch product catalogue by the category it sits in and/or its tier.

    Both filters are optional and matched case-insensitively as substrings.
    ``category`` matches the product's category (e.g. "apparel", "print",
    "accessories", "music"), and ``tier`` matches the production tier (e.g.
    "starter", "pro"). Returns {"products": [...], "count": int}. Pure — no I/O.
    """
    cat = (category or "").strip().lower()
    tr = (tier or "").strip().lower()
    matches = [
        dict(p)
        for p in _PRODUCTS
        if (not cat or cat in p["category"].lower())
        and (not tr or tr in p["tier"].lower())
    ]
    return {"products": matches, "count": len(matches)}


def _get_product(product_id: str) -> dict | None:
    pid = (product_id or "").strip()
    for p in _PRODUCTS:
        if p["id"] == pid:
            return p
    return None


async def build_production_run(
    artist_id: str,
    product_id: str = "",
    design_name: str = "",
    quantity: int = 0,
) -> dict:
    """Build a concrete merch production run by applying a product's economics to a quantity.

    Deterministic run construction — never contacts a printer, fulfilment house, or
    API. Looks the product up by id, checks a design name and a positive quantity
    are present (and at/above the product's minimum order), then computes total
    production cost, projected revenue at the suggested retail, and the projected
    margin. Returns a structured run with line items, totals, margin, gaps, and a
    recommendation of "produce" / "adjust" / "blocked".
    """
    product = _get_product(product_id)

    try:
        qty = int(quantity or 0)
    except (TypeError, ValueError):
        qty = 0

    gaps = []
    if not (design_name or "").strip():
        gaps.append("missing_design_name")
    if not (product_id or "").strip():
        gaps.append("missing_product")
    elif product is None:
        gaps.append("unknown_product")
    if qty <= 0:
        gaps.append("non_positive_quantity")
    elif product is not None and qty < product["min_order_qty"]:
        gaps.append("below_min_order")

    line_items = []
    total_cost = 0
    projected_revenue = 0
    if product is not None and qty > 0:
        total_cost = product["unit_cost"] * qty
        projected_revenue = product["suggested_retail"] * qty
        line_items.append({"label": "unit_cost", "amount": product["unit_cost"]})
        line_items.append({"label": "suggested_retail", "amount": product["suggested_retail"]})
        line_items.append({"label": "quantity", "amount": qty})
        line_items.append({"label": "total_cost", "amount": total_cost})
        line_items.append({"label": "projected_revenue", "amount": projected_revenue})

    projected_margin = projected_revenue - total_cost
    margin_pct = (
        int(round(projected_margin * 100.0 / projected_revenue))
        if projected_revenue > 0
        else 0
    )

    if "unknown_product" in gaps or "missing_product" in gaps:
        # Without a valid product target the run cannot be built at all.
        recommendation = "blocked"
    elif gaps or projected_margin <= 0:
        recommendation = "adjust"
    else:
        recommendation = "produce"
    viable = recommendation == "produce"

    return {
        "viable": viable,
        "gaps": gaps,
        "product_id": product["id"] if product else (product_id or "").strip(),
        "product_name": product["name"] if product else None,
        "category": product["category"] if product else None,
        "tier": product["tier"] if product else None,
        "design_name": (design_name or "").strip(),
        "quantity": qty,
        "line_items": line_items,
        "total_cost": total_cost,
        "projected_revenue": projected_revenue,
        "projected_margin": projected_margin,
        "margin_pct": margin_pct,
        "recommendation": recommendation,
    }
