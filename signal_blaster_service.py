"""
PLMKR Signal-Blaster — publicist action service (mock-first, OUTREACH pattern).

Backs the Signal-Blaster (Zara — Publicist) agent's tool_use loop in
/api/chat_stream (see SIGNAL_BLASTER_TOOLS in main.py). Zara does not just advise on
press — these functions let the agent take real publicist actions, honestly:

  - search_media_outlets:   filter an ARTIST-SUPPLIED media list on beat / level. It
                            NEVER invents outlet or journalist names — with no real
                            media data it returns a [NEEDS:media_targets] gap.
  - build_pitch_plan:       Jade-style OPTION-B scaffold — returns COMPACT
                            ingredients (recommended mode + a lead-ordered timeline
                            derived from LEAD_TIME_DOCTRINE relative to a supplied
                            release date + a package checklist with aggregated
                            missing[]); the agent writes the prose. A weeks-short
                            timeline gets an HONEST compression warning, never a
                            silently compressed schedule.
  - lookup_publicity_doctrine: a PURE read over publicity_data.py — no gate, no I/O.
  - send_press_pitch:       the Marcus/Nia/Solo send seam — the MODEL writes the
                            pitch body and passes it in; this tool only SENDS
                            (deterministic mock, ``PPITCH-``+sha1) behind the
                            PRESS_OUTREACH_CONNECTED gate. pitch_mode is explicit;
                            an embargo pitch REQUIRES a zoned lift datetime or the
                            send is held with a [NEEDS:embargo_lift_datetime] gap.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live media databases, no email/PR-wire APIs, no LLM
    client and no model send call anywhere in this tool layer — the send seam is a
    deterministic sha1 mock only. Press-release/bio/EPK DRAFTING is NEVER done here
    (that is the creative department's build_copy_scaffold).
  - NO secrets are read or embedded. The only "credential" surface is a connection
    check (``_press_account_connected``) driven by the PRESS_OUTREACH_CONNECTED env
    flag so tests can toggle connected / not-connected / expired deterministically.
  - Deterministic: no timestamps or random values leak into return payloads.
  - NEVER fabricate an outlet name, a journalist name, or a coverage claim.
"""
import hashlib
import os

import publicity_data


class PressAccountNotConnected(Exception):
    """Raised when the artist has not connected a press/email account.

    The tool loop catches this and degrades gracefully into a structured 'connect
    your account first' result instead of crashing the stream.
    """


class PressAccountAuthExpired(Exception):
    """Raised when a previously connected press/email-account authorization expired."""


# Sentinel — an embargo lift datetime is the artist's to state, never guessed.
EMBARGO_LIFT_GAP = "[NEEDS:embargo_lift_datetime]"


# ── search_media_outlets — honest, artist-supplied only (never fabricates) ─────

def _outlet_field(o: dict, *keys) -> str:
    for k in keys:
        val = o.get(k)
        if val is not None:
            return str(val)
    return ""


def _match_outlet(o: dict, beat: str, level: str) -> bool:
    """Case-insensitive substring match on whichever structured fields exist."""
    if beat:
        hay = _outlet_field(o, "beat", "beats", "coverage").lower()
        if beat.lower() not in hay:
            return False
    if level:
        hay = _outlet_field(o, "level", "tier", "reach").lower()
        if level.lower() not in hay:
            return False
    return True


async def search_media_outlets(beat: str = "", level: str = "", media_list=None) -> dict:
    """Filter an ARTIST-SUPPLIED media list on structured fields — never invents.

    ``media_list`` is the artist's own list of outlet/journalist dicts (each may
    carry name, beat, level/tier). When present and non-empty the function filters
    it by ``beat`` / ``level`` and returns matches tagged ``[ARTIST-SUPPLIED:
    media_list]``. When NO real media data is supplied it returns a
    ``[NEEDS:media_targets]`` gap — it NEVER conjures an outlet or writer name.
    There is no live outlet directory here. Pure — no I/O.
    """
    bt = (beat or "").strip()
    lv = (level or "").strip()
    criteria = {"beat": bt, "level": lv}

    supplied = [o for o in (media_list or []) if isinstance(o, dict)]
    if not supplied:
        return {
            "status": "needs_targets",
            "source": "[NEEDS:media_targets]",
            "criteria": criteria,
            "outlets": [],
            "count": 0,
            "message": ("No media directory is connected and no media list was "
                        "supplied. Outlet and journalist names are never invented — "
                        "supply a media list personalized to writers covering the "
                        "artist's level and current beat."),
        }

    matches = [dict(o) for o in supplied if _match_outlet(o, bt, lv)]
    return {
        "status": "artist_supplied",
        "source": "[ARTIST-SUPPLIED:media_list]",
        "criteria": criteria,
        "outlets": matches,
        "count": len(matches),
    }


# ── build_pitch_plan — OPTION B: compact ingredients; the agent writes prose ────

def _recommend_mode(goal: str) -> tuple:
    """Return (recommended_mode, rationale) from the selection doctrine, no invention."""
    g = (goal or "").strip().lower()
    sd = publicity_data.PITCH_MECHANISM_TYPES["selection_doctrine"]
    if any(w in g for w in ("impression", "reach", "awareness", "broad", "many outlets")):
        return "standard", sd["max_impressions"]
    if any(w in g for w in ("exclusive", "feature", "relationship", "human-interest",
                            "human interest")):
        return "exclusive", sd["feature_or_relationship"]
    if any(w in g for w in ("embargo", "announcement", "dated", "coordinated", "news")):
        return "embargo", sd["embargo_suits"]
    return "standard", ("no goal specified — defaulting to standard (publish anytime); "
                        "state the goal to refine the recommendation.")


async def build_pitch_plan(artist_id: str, release_date: str = "", weeks_to_release=None,
                           goal: str = "", package=None) -> dict:
    """Build COMPACT pitch-plan ingredients — the agent writes the prose (Option B).

    Returns a recommended pitch mode (from the selection doctrine, never invented),
    a lead-ordered timeline from LEAD_TIME_DOCTRINE anchored to a supplied
    ``release_date``, and a package checklist scored against a supplied ``package``
    dict with an aggregated ``missing[]``. When ``weeks_to_release`` is supplied and
    is shorter than a slot's needed lead, that slot is marked ``compressed`` and an
    HONEST ``compression_warning`` is surfaced — the schedule is NEVER silently
    compressed. The press release is only ever REFERENCED (creative department's
    build_copy_scaffold), never drafted here. Deterministic; no network, no LLM.
    """
    rd = (release_date or "").strip()
    try:
        wtr = int(weeks_to_release) if weeks_to_release is not None else None
    except (TypeError, ValueError):
        wtr = None

    mode, rationale = _recommend_mode(goal)

    timeline = []
    compressed_slots = []
    for slot in publicity_data.LEAD_TIME_DOCTRINE["campaign_timeline"]:
        entry = {
            "slot": slot["slot"],
            "weeks_before_release": slot["weeks_before_release"],
            "note": slot["note"],
        }
        if wtr is None:
            entry["status"] = "unscheduled"
        elif slot["weeks_before_release"] > wtr:
            entry["status"] = "compressed"
            compressed_slots.append(slot["slot"])
        else:
            entry["status"] = "ok"
        timeline.append(entry)

    compression_warning = None
    if compressed_slots:
        compression_warning = (
            f"Only ~{wtr} week(s) to release — these slots cannot get their normal "
            f"lead and are compressed: {', '.join(compressed_slots)}. This is an "
            "honest warning, not a silently shortened plan; extend the runway or "
            "accept reduced reach for the compressed slots."
        )

    supplied_pkg = package if isinstance(package, dict) else {}
    checklist = []
    missing = []
    for comp in publicity_data.PITCH_PACKAGE_SPEC["components"]:
        val = supplied_pkg.get(comp)
        present = bool(val) if not isinstance(val, str) else bool(val.strip())
        checklist.append({"component": comp, "status": "supplied" if present else "missing"})
        if not present:
            missing.append(f"[NEEDS:{comp}]")

    return {
        "status": "plan_ready",
        "release_date": rd,
        "weeks_to_release": wtr,
        "recommended_mode": mode,
        "mode_rationale": rationale,
        "timeline": timeline,
        "compression_warning": compression_warning,
        "package_checklist": checklist,
        "missing": missing,
        "press_release_note": publicity_data.PITCH_PACKAGE_SPEC["press_release_ref"],
        "note": ("Compact ingredients only — write the pitch prose in your turn; the "
                 "press release comes from creative-director's build_copy_scaffold, "
                 "not from here. Coverage is never guaranteed; windows vary by outlet."),
    }


# ── lookup_publicity_doctrine — pure corpus read over publicity_data.py ────────

_PUBLICITY_TOPIC_SECTIONS = {
    "pitch_modes":     publicity_data.PITCH_MECHANISM_TYPES,
    "embargo":         publicity_data.EMBARGO_DOCTRINE,
    "lead_time":       publicity_data.LEAD_TIME_DOCTRINE,
    "personalization": publicity_data.LIST_AND_PERSONALIZATION_DOCTRINE,
    "pitch_package":   publicity_data.PITCH_PACKAGE_SPEC,
    "integrity":       publicity_data.INTEGRITY_DOCTRINE,
    "boundaries":      publicity_data.OUT_OF_SCOPE,
}

PUBLICITY_DOCTRINE_TOPICS = ("pitch_modes", "embargo", "lead_time", "personalization",
                             "pitch_package", "integrity", "boundaries")


async def lookup_publicity_doctrine(topic: str = "") -> dict:
    """Look up the doctrine for ONE publicity topic — pure corpus read, no gate.

    Returns the relevant publicity_data.py section plus the FULL honesty-rule set
    (outlets/writers/claims are never invented; DRAFTING belongs to the creative
    department; an embargo needs a zoned lift; earned media is never paid). A
    press-release DRAFTING request routes to creative-director's build_copy_scaffold
    via the 'boundaries' section — no cross-service call is made here. An unknown
    topic returns a structured ``unknown_topic`` error. No I/O, no LLM.
    """
    t = (topic or "").strip().lower()
    honesty_rules = [dict(r) for r in publicity_data.HONESTY_RULES]
    if t in _PUBLICITY_TOPIC_SECTIONS:
        return {
            "status": "ok",
            "topic": t,
            "data": _PUBLICITY_TOPIC_SECTIONS[t],
            "honesty_rules": honesty_rules,
        }
    return {
        "status": "unknown_topic",
        "topic": t or "(missing)",
        "supported_topics": list(PUBLICITY_DOCTRINE_TOPICS),
        "message": ("Unsupported topic. Supported: "
                    + ", ".join(PUBLICITY_DOCTRINE_TOPICS) + "."),
    }


# ── send_press_pitch — the Marcus send seam (model writes body; tool sends) ─────

def _press_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's press/email account.

    Driven purely by the ``PRESS_OUTREACH_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real secret.
    Values:
      - "expired"                     → raise PressAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("PRESS_OUTREACH_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise PressAccountAuthExpired("press-account authorization expired")
    return val in ("1", "true", "yes", "connected")


def _submit_press_pitch(artist_id: str, outlet_key: str, subject: str, body: str) -> str:
    """In-repo mock-send seam — deterministic ``PPITCH-`` sha1 reference, ZERO network."""
    digest = hashlib.sha1(
        f"{artist_id}:{outlet_key}:{subject}:{body}".encode("utf-8")
    ).hexdigest()
    return "PPITCH-" + digest[:10].upper()


async def send_press_pitch(artist_id: str, outlet_id: str = "", outlet: str = "",
                           subject: str = "", body: str = "", pitch_mode: str = "standard",
                           embargo_lift_datetime=None) -> dict:
    """Send an artist's press pitch — the MODEL wrote the body; this tool sends.

    ``subject`` and ``body`` are written by the model in its turn and passed in
    verbatim; this function NEVER generates or edits them and NEVER invents an outlet
    or a claim. ``pitch_mode`` is an explicit structured field (standard / embargo /
    exclusive). An EMBARGO pitch REQUIRES ``embargo_lift_datetime`` stated with a
    time zone; when it is missing the send is HELD and the result carries a
    ``[NEEDS:embargo_lift_datetime]`` gap — a lift time is never guessed. Follows the
    account-gate seam: raises PressAccountNotConnected / PressAccountAuthExpired when
    no account is linked, returns {"status":"missing_outlet"} when no outlet is
    identified, and on success returns a deterministic ``PPITCH-`` mock reference —
    NO network call is ever made. The supplied subject/body ride back byte-exact.
    """
    if not _press_account_connected(artist_id):
        raise PressAccountNotConnected("artist has not connected a press/email account")

    oid = (outlet_id or "").strip()
    on  = (outlet or "").strip()
    outlet_key = oid or on
    if not outlet_key:
        return {"status": "missing_outlet", "outlet_id": oid, "outlet": on}

    mode = (pitch_mode or "standard").strip().lower() or "standard"
    lift = embargo_lift_datetime
    if mode == "embargo" and not (isinstance(lift, str) and lift.strip()):
        # An embargo without a zoned lift is not sendable — hold, do not guess.
        return {
            "status": "needs_embargo_lift",
            "pitch_mode": mode,
            "embargo_lift_datetime": EMBARGO_LIFT_GAP,
            "outlet_id": oid,
            "outlet": on,
            "message": ("An embargo pitch requires a lift date/time WITH time zone in "
                        "every communication. Supply embargo_lift_datetime or send as "
                        "'standard' — a lift time is never invented."),
        }

    reference = _submit_press_pitch(artist_id, outlet_key, subject, body)
    return {
        "status": "sent",
        "reference": reference,
        "outlet_id": oid,
        "outlet": on,
        "pitch_mode": mode,
        "embargo_lift_datetime": lift if (isinstance(lift, str) and lift.strip()) else None,
        "subject": subject,   # verbatim — the tool never edits the model's pitch
        "body": body,         # verbatim — never generated or modified here
    }
