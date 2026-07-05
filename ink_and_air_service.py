"""
PLMKR Reed — Music Publisher action service (mock-first).

Backs the ink-and-air (Reed, Music Publisher) agent's tool_use loop in /api/chat_stream
(see INK_AND_AIR_TOOLS in main.py). Reed does not just advise — these functions
let the agent take real action: search_publishing_deals, lookup_publishing_societies,
review_split_sheet, validate_split_sheet, and register_composition (a real action on
the artist's connected publishing administration account).

Unit 2: lookup_publishing_societies and validate_split_sheet are pure reads/
computations over the publishing_data corpus (Unit 1) — the corpus is the single
source of truth; no domain fact is invented here. review_split_sheet routes
through validate_split_sheet (the old keyword heuristics are gone): free text is
carried as a note, never parsed into a rule (HONESTY_RULES.free_text_is_note_only),
and percentage sums are arithmetic on SUPPLIED values only — a missing share
becomes a [NEEDS: ...] gap, never an inferred remainder
(HONESTY_RULES.sum_checks_supplied_only).

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

import publishing_data


class PublishingAdminNotConnected(Exception):
    """Raised when the artist has not connected a publishing administration account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class PublishingAdminAuthExpired(Exception):
    """Raised when a previously connected publishing administration account's authorization expired."""


# ── Reference catalog (in-memory reference data — no I/O) ─────────────────────
_INK_AND_AIR_CATALOG = [
    {'id': 'p-admin', 'deal_type': 'administration', 'territory': 'worldwide', 'name': 'Admin Deal', 'note': 'Writer keeps copyright; admin takes 10-15% for collection.'},
    {'id': 'p-copub', 'deal_type': 'co_publishing', 'territory': 'worldwide', 'name': 'Co-Pub Deal', 'note': "Publisher takes 50% of publisher's share; writer keeps writer's share."},
    {'id': 'p-sub', 'deal_type': 'sub_publishing', 'territory': 'eu', 'name': 'EU Sub-Pub', 'note': 'Local collection in-territory; short term.'},
    {'id': 'p-full', 'deal_type': 'full_publishing', 'territory': 'worldwide', 'name': 'Full Publishing', 'note': 'Assign copyright — highest advance, least ownership.'},
]


# ── Split-sheet validation plumbing (pure; corpus-driven) ─────────────────────
_GAP = "[NEEDS: {}]"


def _share(value):
    """Return a float for a supplied numeric share, else None.

    None means "not arithmetic-safe" — either free text (never parsed) or a
    boolean. The caller decides whether the value was missing (a [NEEDS: ...]
    gap) or supplied-but-non-numeric (a note).
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _missing(record: dict, field: str) -> bool:
    """A field is missing when absent, None, or an empty/whitespace string."""
    value = record.get(field)
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _yes(value) -> bool:
    """True only for an explicit yes (bool True or a 'yes'-like string)."""
    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() in ("yes", "y", "true")


async def search_publishing_deals(deal_type: str = "", territory: str = "") -> dict:
    """Search the reference catalog by deal_type and/or territory.

    Both filters are optional and matched case-insensitively as substrings.
    Returns {"items": [...], "count": int}. Pure — no I/O.
    """
    a = (deal_type or "").strip().lower()
    b = (territory or "").strip().lower()
    matches = [
        dict(c)
        for c in _INK_AND_AIR_CATALOG
        if (not a or a in c["deal_type"]) and (not b or b in c["territory"])
    ]
    return {"items": matches, "count": len(matches)}


async def lookup_publishing_societies(country_code: str = "") -> dict:
    """Look up where a writer registers in one country — pure read of publishing_data.

    Returns the performance (PRO) and mechanical society records for the country,
    the unified-CMO flag, the home-society-once/CISAC doctrine, and (for the US
    only) the pick-ONE-PRO rule. A country outside the 11-country corpus returns
    a structured ``country_not_in_corpus`` result listing the supported codes —
    a society is NEVER guessed (HONESTY_RULES.unknown_is_none).
    """
    code = (country_code or "").strip().upper()
    record = publishing_data.COUNTRY_REGISTRATION.get(code)
    if record is None:
        return {
            "status": "country_not_in_corpus",
            "country": code or "(missing)",
            "supported_countries": list(publishing_data.PUBLISHING_COUNTRIES),
            "message": ("No verified society data for this country in the corpus. "
                        "Do not guess a society — tell the artist to verify with "
                        "their local authority, or pick from the supported list."),
        }
    result = {
        "status": "ok",
        "country": code,
        "performance": [dict(publishing_data.SOCIETIES[sid]) for sid in record["performance"]],
        "mechanical": [dict(publishing_data.SOCIETIES[sid]) for sid in record["mechanical"]],
        "unified_cmo": record["unified_cmo"],
        "writer_must_choose_one_pro": record["writer_must_choose_one_pro"],
        "notes": record["notes"],
        "doctrine": {"home_society_once": publishing_data.DOCTRINE["home_society_once"]},
    }
    if record["writer_must_choose_one_pro"]:
        # Corpus text only — the rule lives in the US registration record's notes.
        result["pro_choice_rule"] = record["notes"]
    return result


async def validate_split_sheet(artist_id: str, song: dict = None,
                               contributors: list = None, free_text: str = "") -> dict:
    """Validate a STRUCTURED split sheet against publishing_data.SPLIT_SHEET_SPEC.

    Pure computation, no I/O, no LLM. Field requiredness comes from the corpus
    spec; every missing required value becomes a [NEEDS: ...] gap — never filled.
    Percentage sums are arithmetic on SUPPLIED values only: a side with any
    missing share reports sum_not_checkable (plus the NEEDS entries) and the
    remainder is NOT inferred. Unknown keys and non-numeric share values pass
    through as notes, never parsed into a rule.

    ``valid_structure`` is True iff there are no [NEEDS: ...] gaps and no side
    reports sum_mismatch.
    """
    spec = publishing_data.SPLIT_SHEET_SPEC
    song = dict(song) if isinstance(song, dict) else {}
    contributors = [dict(c) for c in contributors if isinstance(c, dict)] \
        if isinstance(contributors, list) else []

    needs, notes = [], []

    # ── Song-level required fields (from the corpus spec, never hardcoded) ────
    song_field_names = tuple(f["field"] for f in spec["song_fields"])
    for f in spec["song_fields"]:
        if f["required"] and _missing(song, f["field"]):
            needs.append(_GAP.format(f["field"]))
    if _yes(song.get("samples_used")) and _missing(song, "sample_sources"):
        needs.append(_GAP.format("sample_sources — required when samples_used is yes"))
    for key, value in song.items():
        if key not in song_field_names:
            notes.append({"source": "song", "field": key, "text": value,
                          "note": "free text — carried verbatim, never parsed"})

    # ── Contributor required fields ────────────────────────────────────────────
    contributor_field_names = tuple(f["field"] for f in spec["contributor_fields"])
    known_optional = ("publisher_share_percent",) + tuple(
        f["field"] for f in spec["master_side_extension"]["fields"])
    labels = []
    for i, c in enumerate(contributors):
        label = (c.get("legal_name") or "").strip() if isinstance(c.get("legal_name"), str) else ""
        label = label or f"contributor {i + 1}"
        labels.append(label)
        for f in spec["contributor_fields"]:
            if f["required"] and _missing(c, f["field"]):
                needs.append(_GAP.format(f"{f['field']} for {label}"))
        for key, value in c.items():
            if key not in contributor_field_names and key not in known_optional:
                notes.append({"source": label, "field": key, "text": value,
                              "note": "free text — carried verbatim, never parsed"})
    if not contributors:
        needs.append(_GAP.format("contributors — at least one structured contributor record"))

    # ── Percentage sums: arithmetic on SUPPLIED values ONLY ────────────────────
    def _sum_axis(field: str) -> dict:
        """Sum one share axis across contributors; never infer a missing value."""
        total, checkable = 0.0, bool(contributors)
        for c, label in zip(contributors, labels):
            if _missing(c, field):
                checkable = False  # the NEEDS entry is already collected above,
                continue           # except publisher_share_percent — handled below
            value = _share(c.get(field))
            if value is None:
                checkable = False
                notes.append({"source": label, "field": field, "text": c.get(field),
                              "note": "non-numeric share — carried as a note, never parsed"})
                continue
            total += value
        if not checkable:
            return {"status": "sum_not_checkable", "total": None,
                    "rule_id": "sum_checks_supplied_only"}
        if abs(total - 100.0) < 1e-9:
            return {"status": "sum_ok", "total": total}
        return {"status": "sum_mismatch", "total": total}

    # publisher_share_percent is the publisher invariant's field but not a
    # required contributor field — a missing share still gets its NEEDS entry.
    for c, label in zip(contributors, labels):
        if _missing(c, "publisher_share_percent"):
            needs.append(_GAP.format(f"publisher_share_percent for {label}"))

    lyrics = _sum_axis("lyrics_percent")
    music = _sum_axis("music_percent")
    if lyrics["status"] == "sum_mismatch" or music["status"] == "sum_mismatch":
        writer_status = "sum_mismatch"
    elif lyrics["status"] == "sum_ok" and music["status"] == "sum_ok":
        writer_status = "sum_ok"
    else:
        writer_status = "sum_not_checkable"
    sum_status = {
        "writer": {"status": writer_status, "lyrics": lyrics, "music": music},
        "publisher": _sum_axis("publisher_share_percent"),
    }

    if (free_text or "").strip():
        notes.append({"source": "raw_split_text", "field": "split_text",
                      "text": free_text,
                      "note": "free text — carried verbatim, never parsed"})

    mismatch = writer_status == "sum_mismatch" or sum_status["publisher"]["status"] == "sum_mismatch"
    # De-dupe NEEDS, order-preserved (Jade scaffold convention).
    needs = list(dict.fromkeys(needs))
    return {
        "valid_structure": not needs and not mismatch,
        "sum_status": sum_status,
        "needs": needs,
        "notes": notes,
        "contributor_count": len(contributors),
        "spec_reminders": {
            "signed_when": spec["signed_when"],
            "amendment_rule": spec["amendment_rule"]["description"],
            "master_side_extension": (spec["master_side_extension"]["status"] + ": "
                                      + spec["master_side_extension"]["rationale"]),
        },
    }


async def review_split_sheet(artist_id: str, split_text: str = "", context: str = "") -> dict:
    """Screen a split sheet by routing through validate_split_sheet.

    The old keyword heuristics are gone. Free text is carried as a note — never
    parsed into a rule — so a text-only sheet honestly reports every canonical
    field as a [NEEDS: ...] gap instead of pretending a keyword scan validated
    it. ``finding_count`` / ``recommendation`` keys are kept for the tool loop.
    """
    validation = await validate_split_sheet(artist_id, song=None, contributors=None,
                                            free_text=split_text)
    writer = validation["sum_status"]["writer"]["status"]
    publisher = validation["sum_status"]["publisher"]["status"]
    if writer == "sum_mismatch" or publisher == "sum_mismatch":
        recommendation = "resolve_before_release"
    elif validation["needs"]:
        recommendation = "provide_structured_split_fields"
    else:
        recommendation = "clean"
    return {
        "context": context or "unspecified",
        "validation": validation,
        "finding_count": len(validation["needs"]),
        "recommendation": recommendation,
    }


def _connected(artist_id: str) -> bool:
    """Mock connection check for the artist's publishing administration account.

    Driven purely by the ``INK_AND_AIR_CONNECTED`` env flag so tests can toggle
    connected / expired / not-connected with ZERO network calls and NO real
    secret. Values:
      - "expired"                     → raise PublishingAdminAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("INK_AND_AIR_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise PublishingAdminAuthExpired("publishing administration account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def register_composition(artist_id: str, work_title: str, work_type: str = "song") -> dict:
    """Take the composition registered action on the artist's connected publishing administration account.

    Raises PublishingAdminNotConnected / PublishingAdminAuthExpired when no account is linked so the caller can
    surface a 'connect your account' message instead of a hard failure. On
    success returns a deterministic mock reference — NO network call is made.
    """
    if not _connected(artist_id):
        raise PublishingAdminNotConnected("artist has not connected a publishing administration account")
    name = (work_title or "").strip()
    opt = (work_type or "song").strip()
    digest = hashlib.sha1(f"{artist_id}:{name}:{opt}".encode("utf-8")).hexdigest()
    reference = "PUB-" + digest[:10].upper()
    return {
        "status": "done",
        "reference": reference,
        "work_title": name,
        "work_type": opt,
    }
