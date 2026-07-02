"""
PLMKR Audio — Quality Control action service (mock-first).

Backs the audio-quality (Audio, Quality Control) agent's tool_use loop in /api/chat_stream
(see AUDIO_QUALITY_TOOLS in main.py). Audio does not just advise — these functions
let the agent take real action: search_quality_standards, analyze_mix, and submit_master_qc (a real action on the
artist's connected mastering service account).

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


class MasteringAccountNotConnected(Exception):
    """Raised when the artist has not connected a mastering service account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class MasteringAccountAuthExpired(Exception):
    """Raised when a previously connected mastering service account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_AUDIO_QUALITY_CATALOG = [
    {'id': 'q-spot', 'platform': 'spotify', 'stage': 'master', 'name': 'Spotify Loudness', 'note': 'Target -14 LUFS integrated; -1 dBTP ceiling.'},
    {'id': 'q-apple', 'platform': 'apple_music', 'stage': 'master', 'name': 'Apple Sound Check', 'note': 'Target -16 LUFS; preserve dynamics.'},
    {'id': 'q-yt', 'platform': 'youtube', 'stage': 'master', 'name': 'YouTube Normalization', 'note': 'Normalizes to ~-14 LUFS; avoid over-limiting.'},
    {'id': 'q-mix', 'platform': 'spotify', 'stage': 'mix', 'name': 'Pre-Master Headroom', 'note': 'Leave -6 dB headroom before mastering.'},
]


# ── Heuristics (pure keyword screen) ──────────────────────────────────────────
# (phrase-to-match, human issue description, severity)
_AUDIO_QUALITY_HEUR = [
    ('clipping', 'Digital clipping — reduce gain before the ceiling', 'high'),
    ('muddy', 'Low-mid buildup masking clarity', 'high'),
    ('harsh', 'Harsh high-mids — tame 2-5 kHz', 'medium'),
    ('no low end', 'Thin low end — check sub balance', 'medium'),
    ('mono', 'Narrow image — check stereo width', 'low'),
]


async def search_quality_standards(platform: str = "", stage: str = "") -> dict:
    """Search the reference catalog by platform and/or stage.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (platform or "").strip().lower()
    b = (stage or "").strip().lower()
    matches = [
        dict(c)
        for c in _AUDIO_QUALITY_CATALOG
        if (not a or a in c["platform"]) and (not b or b in c["stage"])
    ]
    return {"items": matches, "count": len(matches)}


async def analyze_mix(artist_id: str, mix_notes: str = "", context: str = "") -> dict:
    """Screen mix_notes against known indicators.

    Runs the pure ``_AUDIO_QUALITY_HEUR`` heuristics over the supplied text and returns
    a structured assessment. Never contacts a wire; the screen is a deterministic
    keyword match, not an LLM call.
    """
    text = (mix_notes or "").lower()
    findings = [
        {"finding": desc, "severity": severity, "matched": phrase}
        for phrase, desc, severity in _AUDIO_QUALITY_HEUR
        if phrase in text
    ]
    has_high = any(f["severity"] == "high" for f in findings)
    recommendation = "remix_required" if has_high else ("targeted_fixes" if findings else "master_ready")
    return {
        "context": context or "unspecified",
        "findings": findings,
        "finding_count": len(findings),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's mastering service account.

    Driven purely by the ``AUDIO_QUALITY_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise MasteringAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("AUDIO_QUALITY_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise MasteringAccountAuthExpired("mastering service account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def submit_master_qc(artist_id: str, track_title: str, target: str = "streaming") -> dict:
    """Take the master submitted action on the artist's connected mastering service account.

    Raises MasteringAccountNotConnected / MasteringAccountAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise MasteringAccountNotConnected("artist has not connected a mastering service account")
    name = (track_title or "").strip()
    opt = (target or "streaming").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "QC-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "track_title": name,
        "target": opt,
    }
