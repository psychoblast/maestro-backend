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

import release_data


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


# ── Unit-2 release doctrine plumbing (data only; reads release_data corpus) ─────
# Pure corpus reads + a deterministic checklist builder. NO model call, no I/O,
# no network, no secrets (Cree Unit-2 / Nadia lookup precedent). Every fact an
# artist would supply (codes, dates, credits) stays a run-time input — never
# invented here.

# The six lookup topics -> their corpus section. Reference only; nothing mutates
# these objects (they ride out through json.dumps downstream).
_RELEASE_TOPIC_SECTIONS = {
    "identifiers":       release_data.IDENTIFIER_RULES,
    "metadata":          release_data.METADATA_FIELDS,
    "artwork":           release_data.ARTWORK_SPEC,
    "timeline":          release_data.TIMELINE_DOCTRINE,
    "release_record":    release_data.RELEASE_RECORD_SPEC,
    "distributor_switch": release_data.DISTRIBUTOR_SWITCH_MECHANISM,
}

RELEASE_TOPICS = ("identifiers", "metadata", "artwork", "timeline",
                  "release_record", "distributor_switch")

# The recommended upload lead, in weeks — the boundary below which a timeline is
# "already inside the lead". Mirrors TIMELINE_DOCTRINE.upload_to_distributor.lead
# ("at least four weeks"); kept here as the one number the checker compares on.
_UPLOAD_LEAD_WEEKS = 4


async def lookup_release_requirements(topic: str = "") -> dict:
    """Look up the delivery conventions for ONE release topic — pure corpus read.

    Returns the relevant corpus section plus the FULL honesty-rule set (specs
    are current conventions to verify live; no identifier/date/credit is ever
    invented). An unknown topic returns a structured ``unknown_topic`` error
    listing the supported topics. No I/O, no LLM, nothing invented here.
    """
    t = (topic or "").strip().lower()
    honesty_rules = [dict(r) for r in release_data.HONESTY_RULES]
    if t in _RELEASE_TOPIC_SECTIONS:
        return {
            "status": "ok",
            "topic": t,
            "data": _RELEASE_TOPIC_SECTIONS[t],
            "honesty_rules": honesty_rules,
        }
    return {
        "status": "unknown_topic",
        "topic": t or "(missing)",
        "supported_topics": list(RELEASE_TOPICS),
        "message": ("Unsupported topic. Supported: " + ", ".join(RELEASE_TOPICS) + "."),
    }


def _needs_gap(value, name: str, missing: list, valid=None):
    """Three-way axis mapping: a supplied value, or an explicit [NEEDS:<axis>].

    ``valid`` (optional) restricts accepted values; anything else surfaces as a
    gap rather than being silently defaulted (the never-defaulted rule).
    """
    if isinstance(value, str):
        v = value.strip().lower()
        if v and (valid is None or v in valid):
            return v
    elif value is not None and (valid is None or value in valid):
        return value
    gap = f"[NEEDS:{name}]"
    missing.append(gap)
    return gap


async def build_release_checklist(release_type=None, weeks_to_release=None,
                                  first_release=None) -> dict:
    """Build an ordered, work-backwards release checklist — deterministic, no I/O.

    Ordered from TIMELINE_DOCTRINE (upload -> editorial pitch -> pre-release ->
    post-release), carrying the ink-and-air split-sheet / sync-pack cross-refs
    verbatim. Each unsupplied axis (release_type / weeks_to_release /
    first_release) comes back as an explicit [NEEDS:<axis>] gap — never
    defaulted. When weeks_to_release is inside the four-week upload lead, a
    ``timeline_already_inside_lead`` warning is attached and the checklist is
    NOT silently re-planned into a compressed schedule (no invented dates). The
    full honesty-rule set rides along.
    """
    missing: list = []
    warnings: list = []
    td = release_data.TIMELINE_DOCTRINE

    release_type_val = _needs_gap(release_type, "release_type", missing,
                                  valid={"single", "ep", "album"})

    # weeks_to_release: an integer or a gap. Guard bool (a subclass of int).
    if isinstance(weeks_to_release, bool):
        weeks = None
    elif isinstance(weeks_to_release, int):
        weeks = weeks_to_release
    elif isinstance(weeks_to_release, float) and weeks_to_release.is_integer():
        weeks = int(weeks_to_release)
    else:
        weeks = None
    if weeks is None:
        weeks_val = "[NEEDS:weeks_to_release]"
        missing.append(weeks_val)
    else:
        weeks_val = weeks

    if isinstance(first_release, bool):
        first_val = first_release
    else:
        first_val = "[NEEDS:first_release]"
        missing.append(first_val)

    # Honest inside-the-lead warning — surfaced, never used to re-plan.
    if isinstance(weeks_val, int) and weeks_val < _UPLOAD_LEAD_WEEKS:
        warnings.append({
            "id": "timeline_already_inside_lead",
            "message": ("only " + str(weeks_val) + " week(s) to the release date "
                        "— inside the recommended four-week-minimum upload lead. "
                        "This compresses distributor processing, the correction "
                        "buffer, and the editorial pitch window. Surface it to the "
                        "artist as a risk and let them decide; do NOT silently "
                        "re-plan or promise a compressed schedule."),
        })

    checklist = []
    if first_val is True:
        checklist.append({
            "step": "claim_artist_profiles", "phase": "pre_release",
            "guidance": ("first release: claim and verify Spotify for Artists and "
                         "Apple Music for Artists BEFORE pitching, so editorial "
                         "access exists."),
        })
    checklist.append({
        "step": "upload_to_distributor", "phase": "pre_release",
        "guidance": (td["upload_to_distributor"]["lead"] + " — "
                     + td["upload_to_distributor"]["covers"]),
    })
    checklist.append({
        "step": "editorial_pitch", "phase": "pre_release",
        "guidance": ("Spotify: " + td["editorial_pitch"]["spotify"]
                     + " Others: " + td["editorial_pitch"]["others"]
                     + " Copy: " + td["editorial_pitch"]["copy"]),
    })
    for key in td["pre_release"]:
        item = {"step": key, "phase": "pre_release"}
        if key in td["cross_refs"]:
            item["cross_ref"] = td["cross_refs"][key]
        checklist.append(item)
    for key in td["post_release"]:
        checklist.append({"step": key, "phase": "post_release"})

    return {
        "status": "ok",
        "release_type": release_type_val,
        "weeks_to_release": weeks_val,
        "first_release": first_val,
        "checklist": checklist,
        "warnings": warnings,
        "missing": list(dict.fromkeys(missing)),
        "cross_refs": dict(td["cross_refs"]),
        "note": ("Checklist of CURRENT delivery conventions — verify each with the "
                 "distributor/platform live. No identifier, date, or credit is "
                 "invented; unsupplied inputs are [NEEDS:] gaps, never defaulted."),
        "honesty_rules": [dict(r) for r in release_data.HONESTY_RULES],
    }
