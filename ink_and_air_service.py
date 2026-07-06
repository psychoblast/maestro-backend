"""
PLMKR Reed — Music Publisher action service (mock-first).

Backs the ink-and-air (Reed, Music Publisher) agent's tool_use loop in /api/chat_stream
(see INK_AND_AIR_TOOLS in main.py). Reed does not just advise — these functions
let the agent take real action: search_publishing_deals, lookup_publishing_societies,
review_split_sheet, validate_split_sheet, build_publishing_doc_scaffold, and
register_composition (a real action on the artist's connected publishing
administration account).

Unit 3: build_publishing_doc_scaffold is a DATA tool (Jade-U4 pattern) — it
returns compact ingredients (sections, [NEEDS: ...] gaps, [ARTIST-SUPPLIED: ...]
reminders); Reed writes the draft in his own turn. No model call here.

Honesty pass: the invented deal reference catalog is DELETED. lookup_deal_types
is a pure read of publishing_data's DEAL_TYPES / DEAL_TRAP_TERMS / DEAL_HONESTY
doctrine (structures and trap terms — never offer evaluations, never a quoted
market number; the only numeric range is the admin fee 10-25% of publisher's
share labeled typical/negotiable). search_publishing_deals remains as a thin
alias so the wired tool name keeps working.

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


async def lookup_deal_types(deal_type: str = "", territory: str = "") -> dict:
    """Look up publishing deal-TYPE doctrine — pure read of publishing_data.

    Honesty pass: the old invented reference catalog is GONE. This returns the
    corpus DEAL_TYPES records (structures: ownership, writer income flow,
    typical-and-negotiable shapes — the ONLY numeric range anywhere is the
    admin fee 10-25% of publisher's share, labeled a typical range), the
    DEAL_TRAP_TERMS every conversation should surface, and the DEAL_HONESTY
    doctrine (Reed explains structures and flags traps — he NEVER evaluates a
    specific offer; real agreements route to Lex as draft-for-review).

    ``deal_type`` optionally narrows to matching type records (matched
    case-insensitively, substring in either direction, against id and name).
    ``territory`` is accepted for call-shape compatibility but is NOT a filter
    — deal structures are not territory records; it is carried back as a note
    (HONESTY_RULES.free_text_is_note_only). Pure — no I/O.
    """
    a = (deal_type or "").strip().lower()
    matches = [
        dict(record)
        for record in publishing_data.DEAL_TYPES.values()
        if not a
        or a in record["id"] or record["id"] in a
        or a in record["name"].lower()
    ]
    result = {
        "count": len(matches),
        "deal_types": matches,
        "trap_terms": [dict(t) for t in publishing_data.DEAL_TRAP_TERMS],
        "honesty": dict(publishing_data.DEAL_HONESTY),
    }
    if a and not matches:
        result["supported_deal_types"] = list(publishing_data.DEAL_TYPES)
        result["message"] = ("No deal-type doctrine matches that filter — pick "
                             "from the supported types; a deal structure is "
                             "never invented.")
    if (territory or "").strip():
        result["notes"] = [{"source": "territory", "text": territory,
                            "note": ("free text — carried verbatim, never a "
                                     "filter; deal-type doctrine is not "
                                     "territory-scoped (sub-publishing is the "
                                     "territory-scoped cousin of admin/full "
                                     "deals — see the admin record's notes)")}]
    return result


async def search_publishing_deals(deal_type: str = "", territory: str = "") -> dict:
    """Thin alias for lookup_deal_types — kept so the wired tool name and its
    call sites keep working; the honest implementation lives in
    lookup_deal_types (honesty pass: the invented catalog this name used to
    search no longer exists)."""
    return await lookup_deal_types(deal_type=deal_type, territory=territory)


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


# ── Unit-3 doc-scaffold skeletons (data only, no logic) ───────────────────────
# build_publishing_doc_scaffold consumes these. Jade-U4 pattern: the tool
# returns compact INGREDIENTS; Reed writes the draft in his own turn.

_NOT_SUBMIT_READY_NOTE = (
    "Scaffold only — write the draft yourself from these ingredients. The draft "
    "is a review starting point for the artist and their manager — NOT "
    "submit-ready, NOT a legal document. Keep every [NEEDS: ...] marker "
    "verbatim and never invent a fact, an IPI, or a %. A split sheet is "
    "amendable only with re-signature by ALL parties."
)

# Section order for the split-sheet document (order matters).
SPLIT_SHEET_DOC_SECTIONS = (
    {"key": "song", "title": "Song",
     "guidance": "Identify the work: title, alternate titles, date, samples used (+ sources)."},
    {"key": "contributors", "title": "Contributors & Splits",
     "guidance": ("One block per contributor: legal name, contact, role, lyrics/music %, "
                  "PRO affiliation, writer IPI, publisher (+ 'SELF' if self-published), "
                  "publisher IPI.")},
    {"key": "writer_sum_status", "title": "Writer-Share Check",
     "guidance": "Writer shares must sum to exactly 100% — checked over supplied values only."},
    {"key": "publisher_sum_status", "title": "Publisher-Share Check",
     "guidance": ("Publisher shares must sum to exactly 100% — societies pay 50/50 "
                  "writer/publisher.")},
    {"key": "master_side_extension", "title": "Master-Side Extension (best practice)",
     "guidance": ("Composition split is not the master split — capture recording info, ISRC, "
                  "and master ownership % on the same sheet to prevent disputes.")},
    {"key": "amendment_rule", "title": "Amendments",
     "guidance": "State the amendment rule on the sheet itself."},
    {"key": "signatures", "title": "Signatures",
     "guidance": "Signature line per contributor — an unsigned split sheet is not enforceable."},
)

# Sync-pack field partition. Every corpus-native SYNC_METADATA_SPEC field must
# appear in exactly one group (or be the computed one_stop_status) — a test
# guards the union so spec drift is caught. clearance_contact_composition /
# clearance_contact_master are INPUT keys implementing the corpus field
# description "clearance contact per side"; they are not corpus field names.
SYNC_PACK_FIELD_GROUPS = (
    {"key": "core_metadata", "title": "Track Metadata",
     "guidance": "Specific genre, moods, tempo, instrumentation, vocals, comparisons, "
                 "placements, and the identifier set (ISRC / ISWC / PRO / IPI).",
     "fields": ("genre_specific", "moods", "tempo_bpm", "instrumentation", "vocals",
                "similar_artists", "suggested_placements", "isrc", "iswc",
                "pro_affiliation", "ipi")},
    {"key": "rights_clearance", "title": "Rights & Clearance Contacts",
     "guidance": "Rights breakdown with a clearance contact per side (composition and master).",
     "fields": ("rights_breakdown", "clearance_contact_composition",
                "clearance_contact_master")},
    {"key": "availability", "title": "Availability",
     "guidance": "Stems, instrumental, and clean-version availability.",
     "fields": ("stems_available", "instrumental_available", "clean_version_available")},
    {"key": "samples_declaration", "title": "Samples-Cleared Declaration",
     "guidance": "Explicit declaration that all samples are cleared.",
     "fields": ("samples_cleared_declaration",)},
)


async def build_publishing_doc_scaffold(artist_id: str, doc_type: str = "",
                                        inputs: dict = None) -> dict:
    """Build a compact document scaffold: split_sheet or sync_pack.

    DATA/SCAFFOLD tool — no model call, no prose, no I/O (Jade-U4 pattern; the
    service imports no anthropic). Every content field in the result is a
    supplied input verbatim, a [NEEDS: <field>] gap, or an
    [ARTIST-SUPPLIED: ...] reminder — nothing is ever fabricated. The
    split_sheet branch reuses validate_split_sheet (Unit 2) for the gap list
    and both 100%-sum checks rather than duplicating that logic. The sync_pack
    branch asserts one-stop ONLY when all three explicit-confirmation
    conditions from SYNC_METADATA_SPEC hold; a directly supplied
    one_stop_status input is disregarded with a note
    (HONESTY_RULES.one_stop_explicit_confirmation_only).
    """
    dt = (doc_type or "").strip().lower()
    inputs = dict(inputs) if isinstance(inputs, dict) else {}
    if dt == "split_sheet":
        return await _scaffold_split_sheet(artist_id, inputs)
    if dt == "sync_pack":
        return _scaffold_sync_pack(inputs)
    return {
        "status": "unknown_doc_type",
        "doc_type": dt or "(missing)",
        "supported_doc_types": ["split_sheet", "sync_pack"],
        "message": ("Unsupported doc_type. Supported: 'split_sheet' (song + contributor "
                    "splits) or 'sync_pack' (sync licensing metadata pack)."),
    }


async def _scaffold_split_sheet(artist_id: str, inputs: dict) -> dict:
    """Split-sheet scaffold — validation, sums, and gaps come from Unit 2."""
    spec = publishing_data.SPLIT_SHEET_SPEC
    song = inputs.get("song") if isinstance(inputs.get("song"), dict) else {}
    contributors = inputs.get("contributors") \
        if isinstance(inputs.get("contributors"), list) else []
    validation = await validate_split_sheet(artist_id, song=song,
                                            contributors=contributors)

    labels = []
    for i, c in enumerate(contributors):
        name = c.get("legal_name") if isinstance(c, dict) else None
        label = name.strip() if isinstance(name, str) and name.strip() else f"contributor {i + 1}"
        labels.append(label)

    def _value_or_gap(record, field, suffix=""):
        if isinstance(record, dict) and not _missing(record, field):
            return record[field]
        return _GAP.format(field + suffix)

    artist_supplied_reminders = []
    contributor_fields = tuple(f["field"] for f in spec["contributor_fields"]) \
        + ("publisher_share_percent",)
    contributor_blocks = [
        {"contributor": label,
         "fields": {f: _value_or_gap(c, f, f" for {label}") for f in contributor_fields}}
        for c, label in zip(contributors, labels)
    ] or [_GAP.format("contributors — at least one structured contributor record")]

    master_fields = {}
    for f in spec["master_side_extension"]["fields"]:
        field = f["field"]
        if not _missing(inputs, field):
            master_fields[field] = inputs[field]
        else:
            reminder = (f"[ARTIST-SUPPLIED: {field} — best-practice master-side detail "
                        "to confirm; composition split is not the master split]")
            master_fields[field] = reminder
            artist_supplied_reminders.append(reminder)

    content_by_key = {
        "song": {f["field"]: _value_or_gap(song, f["field"]) for f in spec["song_fields"]},
        "contributors": contributor_blocks,
        "writer_sum_status": validation["sum_status"]["writer"],
        "publisher_sum_status": validation["sum_status"]["publisher"],
        "master_side_extension": {"status": spec["master_side_extension"]["status"],
                                  "rationale": spec["master_side_extension"]["rationale"],
                                  "fields": master_fields},
        "amendment_rule": spec["amendment_rule"]["description"],
        "signatures": [{"contributor": label,
                        "signature": _value_or_gap(c, "signature", f" for {label}")}
                       for c, label in zip(contributors, labels)]
                      or [_GAP.format("signatures — one line per contributor")],
    }
    sections = [{"key": s["key"], "title": s["title"], "guidance": s["guidance"],
                 "content_or_gap": content_by_key[s["key"]]}
                for s in SPLIT_SHEET_DOC_SECTIONS]

    known_top = ("song", "contributors") + tuple(
        f["field"] for f in spec["master_side_extension"]["fields"])
    unmapped = {k: v for k, v in inputs.items() if k not in known_top}

    result = {
        "status": "scaffold_ready",
        "doc_type": "split_sheet",
        "signed_when": spec["signed_when"],
        "sections": sections,
        "missing": list(validation["needs"]),
        "artist_supplied_reminders": artist_supplied_reminders,
        "notes": validation["notes"],
        "note": _NOT_SUBMIT_READY_NOTE,
    }
    if unmapped:
        result["unmapped_inputs"] = unmapped
    return result


def _scaffold_sync_pack(inputs: dict) -> dict:
    """Sync-pack scaffold — one-stop from explicit confirmations ONLY."""
    spec = publishing_data.SYNC_METADATA_SPEC
    condition_ids = tuple(c["id"] for c in spec["one_stop_conditions"])
    confirmations = inputs.get("one_stop_confirmations")
    confirmations = confirmations if isinstance(confirmations, dict) else {}

    missing_conditions = [cid for cid in condition_ids
                          if confirmations.get(cid) is not True]
    one_stop = {
        "status": "one_stop" if not missing_conditions else "cannot_assert_one_stop",
        "missing_conditions": missing_conditions,
        "rule": spec["one_stop_rule"],
    }

    needs, notes, artist_supplied_reminders = [], [], []
    if not _missing(inputs, "one_stop_status"):
        notes.append({"source": "inputs", "field": "one_stop_status",
                      "text": inputs["one_stop_status"],
                      "note": ("disregarded — one-stop is asserted only from the three "
                               "explicit confirmations, never from a supplied status "
                               "(rule: one_stop_explicit_confirmation_only)")})
    by_desc = {c["id"]: c["description"] for c in spec["one_stop_conditions"]}
    for cid in missing_conditions:
        artist_supplied_reminders.append(
            f"[ARTIST-SUPPLIED: explicit confirmation — {by_desc[cid]}]")

    sections = []
    for group in SYNC_PACK_FIELD_GROUPS:
        content = {}
        for field in group["fields"]:
            if _missing(inputs, field):
                gap = _GAP.format(field)
                content[field] = gap
                needs.append(gap)
            else:
                content[field] = inputs[field]
        sections.append({"key": group["key"], "title": group["title"],
                         "guidance": group["guidance"], "content_or_gap": content})
    sections.insert(1, {
        "key": "one_stop", "title": "One-Stop Status",
        "guidance": ("Asserted ONLY when master control, 100% publishing control, and "
                     "no-uncleared-samples are each explicitly confirmed by the artist."),
        "content_or_gap": one_stop,
    })

    known = {f for g in SYNC_PACK_FIELD_GROUPS for f in g["fields"]} \
        | {"one_stop_confirmations", "one_stop_status"}
    unmapped = {k: v for k, v in inputs.items() if k not in known}

    result = {
        "status": "scaffold_ready",
        "doc_type": "sync_pack",
        "sections": sections,
        "one_stop": one_stop,
        "missing": list(dict.fromkeys(needs)),
        "artist_supplied_reminders": artist_supplied_reminders,
        "notes": notes,
        "note": _NOT_SUBMIT_READY_NOTE,
    }
    if unmapped:
        result["unmapped_inputs"] = unmapped
    return result


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
