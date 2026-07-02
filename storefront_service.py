"""
PLMKR Store — Fan Store action service (mock-first).

Backs the storefront (Store, Fan Store) agent's tool_use loop in /api/chat_stream
(see STOREFRONT_TOOLS in main.py). Store does not just advise — these functions
let the agent take real action: search_product_types, assess_pricing, and publish_store_product (a real action on the
artist's connected fan-store account).

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_connected``) driven by an env flag so tests can toggle
    connected / not-connected / expired deterministically — mirroring
    lex_cipher_service.RegistryNotConnected without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads.
"""
import hashlib
import os


class StoreAccountNotConnected(Exception):
    """Raised when the artist has not connected a fan-store account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class StoreAccountAuthExpired(Exception):
    """Raised when a previously connected fan-store account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_STOREFRONT_CATALOG = [
    {'id': 'sp-1', 'category': 'music', 'format': 'digital', 'name': 'Deluxe Bundle', 'note': 'Album + stems + demos as a paid download.'},
    {'id': 'sp-2', 'category': 'merch', 'format': 'physical', 'name': 'Signed Vinyl', 'note': 'Limited signed pressing, numbered.'},
    {'id': 'sp-3', 'category': 'membership', 'format': 'subscription', 'name': 'Inner Circle', 'note': 'Monthly membership with exclusive drops.'},
    {'id': 'sp-4', 'category': 'experience', 'format': 'ticketed', 'name': 'Livestream Show', 'note': 'Ticketed streaming performance.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_STOREFRONT_HEUR = [
    ('below cost', 'Priced below unit cost — negative margin', 'high'),
    ('no shipping', 'Shipping not factored into price', 'high'),
    ('too cheap', 'Underpriced vs perceived value', 'medium'),
    ('no tiers', 'No pricing tiers to capture superfans', 'medium'),
    ('no scarcity', 'No limited edition to drive urgency', 'low'),
]


async def search_product_types(category: str = "", format: str = "") -> dict:
    """Search the reference catalog by category and/or format.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (category or "").strip().lower()
    b = (format or "").strip().lower()
    matches = [
        dict(c)
        for c in _STOREFRONT_CATALOG
        if (not a or a in c["category"]) and (not b or b in c["format"])
    ]
    return {"items": matches, "count": len(matches)}


async def assess_pricing(artist_id: str, pricing_notes: str = "", context: str = "") -> dict:
    """Screen pricing_notes against known indicators.

    Runs the pure ``_STOREFRONT_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (pricing_notes or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _STOREFRONT_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "reprice" if has_high else ("adjust_tiers" if findings else "priced_well")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's fan-store account.

    Driven purely by the ``STOREFRONT_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise StoreAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("STOREFRONT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise StoreAccountAuthExpired("fan-store account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def publish_store_product(artist_id: str, product_title: str, store: str = "main") -> dict:
    """Take the product published action on the artist's connected fan-store account.

    Raises StoreAccountNotConnected / StoreAccountAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise StoreAccountNotConnected("artist has not connected a fan-store account")
    name = (product_title or "").strip()
    opt = (store or "main").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "PROD-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "product_title": name,
        "store": opt,
    }
