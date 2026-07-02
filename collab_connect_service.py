"""
PLMKR Collab — Networking action service (mock-first).

Backs the collab-connect (Collab, Networking) agent's tool_use loop in /api/chat_stream
(see COLLAB_CONNECT_TOOLS in main.py). Collab does not just advise — these functions
let the agent take real action: search_collaborators, assess_collab_fit, and send_collab_invite (a real action on the
artist's connected collaboration network account).

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


class NetworkAccountNotConnected(Exception):
    """Raised when the artist has not connected a collaboration network account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class NetworkAccountAuthExpired(Exception):
    """Raised when a previously connected collaboration network account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_COLLAB_CONNECT_CATALOG = [
    {'id': 'c-1', 'genre': 'pop', 'role': 'topliner', 'name': 'Ava Reed', 'note': 'Toplines with a strong hook sensibility.'},
    {'id': 'c-2', 'genre': 'hip_hop', 'role': 'producer', 'name': 'Marz', 'note': 'Boom-bap and trap hybrid production.'},
    {'id': 'c-3', 'genre': 'electronic', 'role': 'vocalist', 'name': 'Nyx', 'note': 'Ethereal vocals for dance records.'},
    {'id': 'c-4', 'genre': 'rnb', 'role': 'songwriter', 'name': 'Solae', 'note': 'Emotive R&B songwriting.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_COLLAB_CONNECT_HEUR = [
    ('no credits', 'No verifiable credits — vet before committing', 'high'),
    ('unclear splits', 'Split expectations unclear up front', 'high'),
    ('different genre', "Genre mismatch with the artist's lane", 'medium'),
    ('timezone', 'Timezone gap may slow the process', 'low'),
    ('no contract', 'No agreement in place yet', 'medium'),
]


async def search_collaborators(genre: str = "", role: str = "") -> dict:
    """Search the reference catalog by genre and/or role.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (genre or "").strip().lower()
    b = (role or "").strip().lower()
    matches = [
        dict(c)
        for c in _COLLAB_CONNECT_CATALOG
        if (not a or a in c["genre"]) and (not b or b in c["role"])
    ]
    return {"items": matches, "count": len(matches)}


async def assess_collab_fit(artist_id: str, collaborator_profile: str = "", context: str = "") -> dict:
    """Screen collaborator_profile against known indicators.

    Runs the pure ``_COLLAB_CONNECT_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (collaborator_profile or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _COLLAB_CONNECT_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "proceed_with_caution" if has_high else ("align_terms_first" if findings else "strong_fit")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's collaboration network account.

    Driven purely by the ``COLLAB_CONNECT_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise NetworkAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("COLLAB_CONNECT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise NetworkAccountAuthExpired("collaboration network account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def send_collab_invite(artist_id: str, collaborator_name: str, channel: str = "platform") -> dict:
    """Take the invite sent action on the artist's connected collaboration network account.

    Raises NetworkAccountNotConnected / NetworkAccountAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise NetworkAccountNotConnected("artist has not connected a collaboration network account")
    name = (collaborator_name or "").strip()
    opt = (channel or "platform").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "COL-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "collaborator_name": name,
        "channel": opt,
    }
