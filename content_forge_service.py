"""
PLMKR Pen — Content Creation action service (mock-first).

Backs the content-forge (Pen, Content Creation) agent's tool_use loop in /api/chat_stream
(see CONTENT_FORGE_TOOLS in main.py). Pen does not just advise — these functions
let the agent take real action: search_content_templates, review_copy, and publish_content_draft (a real action on the
artist's connected content management account).

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


class CmsNotConnected(Exception):
    """Raised when the artist has not connected a content management account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class CmsAuthExpired(Exception):
    """Raised when a previously connected content management account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_CONTENT_FORGE_CATALOG = [
    {'id': 'ct-1', 'platform': 'instagram', 'content_type': 'caption', 'name': 'Carousel Hook', 'note': 'Scroll-stopping first line for carousels.'},
    {'id': 'ct-2', 'platform': 'tiktok', 'content_type': 'script', 'name': '3-Second Hook', 'note': 'Open with tension in the first beat.'},
    {'id': 'ct-3', 'platform': 'newsletter', 'content_type': 'long_form', 'name': 'Release Story', 'note': 'Behind-the-song narrative structure.'},
    {'id': 'ct-4', 'platform': 'twitter', 'content_type': 'thread', 'name': 'Launch Thread', 'note': 'Announce a drop as a numbered thread.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_CONTENT_FORGE_HEUR = [
    ('click here', 'Weak, generic CTA', 'medium'),
    ('!!!', 'Overuse of exclamation — reads spammy', 'medium'),
    ('lorem ipsum', 'Placeholder text left in the draft', 'high'),
    ('link in bio', 'Passive CTA — be specific about the action', 'low'),
    ('buy now', 'Hard-sell tone may underperform organically', 'low'),
]


async def search_content_templates(platform: str = "", content_type: str = "") -> dict:
    """Search the reference catalog by platform and/or content_type.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (platform or "").strip().lower()
    b = (content_type or "").strip().lower()
    matches = [
        dict(c)
        for c in _CONTENT_FORGE_CATALOG
        if (not a or a in c["platform"]) and (not b or b in c["content_type"])
    ]
    return {"items": matches, "count": len(matches)}


async def review_copy(artist_id: str, draft_text: str = "", context: str = "") -> dict:
    """Screen draft_text against known indicators.

    Runs the pure ``_CONTENT_FORGE_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (draft_text or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _CONTENT_FORGE_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "rewrite" if has_high else ("polish" if findings else "ship_it")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's content management account.

    Driven purely by the ``CONTENT_FORGE_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise CmsAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("CONTENT_FORGE_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise CmsAuthExpired("content management account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def publish_content_draft(artist_id: str, title: str, channel: str = "blog") -> dict:
    """Take the draft published action on the artist's connected content management account.

    Raises CmsNotConnected / CmsAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise CmsNotConnected("artist has not connected a content management account")
    name = (title or "").strip()
    opt = (channel or "blog").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "CNT-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "title": name,
        "channel": opt,
    }
