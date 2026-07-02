"""
PLMKR Tommy — Label Services action service (mock-first).

Backs the label-services (Tommy, Label Services) agent's tool_use loop in /api/chat_stream
(see LABEL_SERVICES_TOOLS in main.py). Tommy does not just advise — these functions
let the agent take real action: search_distribution_requirements, validate_release_metadata, and deliver_to_dsps (a real action on the
artist's connected distributor account).

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


class DistributorNotConnected(Exception):
    """Raised when the artist has not connected a distributor account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class DistributorAuthExpired(Exception):
    """Raised when a previously connected distributor account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_LABEL_SERVICES_CATALOG = [
    {'id': 'd-art', 'store': 'spotify', 'asset_type': 'artwork', 'name': 'Cover Art Spec', 'note': '3000x3000 px, RGB, no borders or promo text.'},
    {'id': 'd-audio', 'store': 'apple_music', 'asset_type': 'audio', 'name': 'Audio Master Spec', 'note': '24-bit/44.1kHz WAV or higher; no clipping.'},
    {'id': 'd-meta', 'store': 'spotify', 'asset_type': 'metadata', 'name': 'Metadata Rules', 'note': 'Correct ISRC, no ALL-CAPS titles, credited writers.'},
    {'id': 'd-lead', 'store': 'beatport', 'asset_type': 'timing', 'name': 'Lead Time', 'note': 'Deliver 3-4 weeks ahead for playlist consideration.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_LABEL_SERVICES_HEUR = [
    ('no isrc', 'Missing ISRC — required by stores', 'high'),
    ('all caps', 'ALL-CAPS title — stores reject or reformat', 'high'),
    ('no upc', 'Missing UPC/EAN for the release', 'high'),
    ('explicit not flagged', 'Explicit content not flagged', 'medium'),
    ('wrong date', 'Inconsistent release date fields', 'medium'),
]


async def search_distribution_requirements(store: str = "", asset_type: str = "") -> dict:
    """Search the reference catalog by store and/or asset_type.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (store or "").strip().lower()
    b = (asset_type or "").strip().lower()
    matches = [
        dict(c)
        for c in _LABEL_SERVICES_CATALOG
        if (not a or a in c["store"]) and (not b or b in c["asset_type"])
    ]
    return {"items": matches, "count": len(matches)}


async def validate_release_metadata(artist_id: str, metadata_text: str = "", context: str = "") -> dict:
    """Screen metadata_text against known indicators.

    Runs the pure ``_LABEL_SERVICES_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (metadata_text or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _LABEL_SERVICES_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "fix_before_delivery" if has_high else ("correct_fields" if findings else "delivery_ready")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's distributor account.

    Driven purely by the ``LABEL_SERVICES_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise DistributorAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("LABEL_SERVICES_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise DistributorAuthExpired("distributor account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def deliver_to_dsps(artist_id: str, release_title: str, store: str = "all") -> dict:
    """Take the delivery queued action on the artist's connected distributor account.

    Raises DistributorNotConnected / DistributorAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise DistributorNotConnected("artist has not connected a distributor account")
    name = (release_title or "").strip()
    opt = (store or "all").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "DIST-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "release_title": name,
        "store": opt,
    }
