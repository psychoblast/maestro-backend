"""
PLMKR Tour-Commander (Miles) — tour-operations DOC-WRITER service (mock-first,
Option B).

Backs the Tour-Commander (Miles — Tour Manager) agent's tool_use loop in
/api/chat_stream (see TOUR_COMMANDER_TOOLS in main.py). Miles does not just
advise on advancing, day sheets, and settlement — these functions let the agent
take one real action: assemble organized preparation material from Miles's real
tour-operations knowledge base — a structured lookup over the tour-ops corpus,
and compact doc-scaffold ingredients the agent turns into prose in its own turn.

DOC-WRITER OPTION B (Cree / Nadia / Reed / Lex precedent):
  build_tour_doc_scaffold returns COMPACT ingredients only — matched doctrine,
  checklists, field lists, questions, aggregated gaps. The AGENT writes the
  prose in its turn. There is ZERO model-call in this module (no Anthropic SDK
  import, no create-message call) — AST-enforced by tests.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live routing/production/crewing APIs, no LLM.
  - NO secrets are read or embedded, and there is NO connection gate: both
    tools are pure corpus-read / data-scaffold tools that need no connected
    account (the old tour-ops-account gate and its crewing-confirmation action
    are RETIRED; crewing/production booking is not Miles's domain here, and
    confirming a hold requires no account check to PREP the paperwork for one).
  - Deterministic: no timestamps or random values leak into return payloads,
    so tests can assert on exact structure.

HARD RULES honored here (mirroring tour_ops_data.py's doctrine):
  - documents_not_figures: Miles never states a dollar figure, guarantee
    amount, or fee amount. No arithmetic is ever performed in this module —
    deal terms and deal-memo content are restated VERBATIM from artist-
    supplied inputs, never computed or summed.
  - PRIVACY (day_sheet): fields flagged ``sensitive: True`` in
    tour_ops_data.DAY_SHEET_SPEC (hotel info, door codes, flight details) are
    EXCLUDED from the default/printable output. Only an explicit
    ``include_sensitive`` request on the ``principal`` variant surfaces them;
    every other variant (including the default) always excludes them.
  - BOUNDARIES: booking and deal terms belong to venue-hawk (Miles starts work
    only after the deal memo exists and never renegotiates it); the actual
    settlement accounting/ledger reconciliation belongs to ledger-lock (Miles
    PREPS ONLY — never a computed total, ever).
  - NEVER fabricate: every artist-fact slot is the supplied input VERBATIM, a
    [NEEDS:<x>] gap, or an [ARTIST-SUPPLIED:<x>] marker — never invented.
    Corpus content (doctrine, checklists, fields) is pulled verbatim from
    tour_ops_data.
"""
import tour_ops_data


# ── Framing + gap markers (data, not logic) ───────────────────────────────────
_GAP = "[NEEDS:{}]"
_ARTIST_SUPPLIED = "[ARTIST-SUPPLIED:{}]"

# The three scaffolds this DOC-WRITER produces.
DOC_TYPES = ("advance_pack", "day_sheet", "settlement_prep_sheet")

# Standing framing surfaced on every scaffold header — pulled verbatim from the
# corpus so no output can be read as a figure, a negotiation, or an accounting.
_PREP_NOT_NEGOTIATION  = tour_ops_data.MILES_DOCTRINE["prep_not_negotiation"]
_PREP_NOT_ACCOUNTING   = tour_ops_data.MILES_DOCTRINE["prep_not_accounting"]
_DOCUMENTS_NOT_FIGURES = tour_ops_data.MILES_DOCTRINE["documents_not_figures"]

# The advance-package bundle, restructured from ADVANCING_DOCTRINE's
# ``advance_package_contents`` description into a checklist. Not new content —
# a restructuring of the corpus's own prose, exactly like Lex's glossary/
# red-flag section builders restructure legal_data into list form.
_ADVANCE_PACKAGE_CHECKLIST = [
    "tech rider", "stage plot", "input list", "hospitality rider",
    "pass sheet", "settlement documents",
]

# Walk-the-numbers questions for settlement prep — QUESTIONS only, never a
# computed figure. Derived from SETTLEMENT_PREP_DOCTRINE's own topics.
_SETTLEMENT_WALK_THE_NUMBERS_QUESTIONS = [
    "What is the confirmed deposit per the agency report?",
    "Has the W9 (or local equivalent tax form) and banking/wire information "
    "been sent to the promoter ahead of show day?",
    "Is the pre-settlement review scheduled for the afternoon of show day, "
    "well before doors?",
    "Are sellable capacity and legal capacity both confirmed for tonight's numbers?",
    "Are any VIP packages being settled separately from general ticket sales?",
    "Does a regional withholding mechanism apply to tonight's settlement?",
    "If a discrepancy surfaces, is there an immediate remedy available — or "
    "does this stay unsettled tonight and hand off to ledger-lock?",
]


def _heading(text: str) -> str:
    """Every section heading routes through here for uniform styling."""
    return text


def _missing(value) -> bool:
    """A supplied input is missing when absent, None, or empty/whitespace text."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _norm(value) -> str:
    return (value or "").strip() if isinstance(value, str) else ""


# ═══════════════════════════════════════════════════════════════════════════════
# lookup_tour_ops_doctrine — structured lookup/filter over the tour_ops_data
# corpus. Pure corpus read; NOT gated. No booking/settlement judgment is made
# about the artist's own tour — this returns the standing doctrine the agent
# applies.
# ═══════════════════════════════════════════════════════════════════════════════
async def lookup_tour_ops_doctrine(
    advancing_key: str = "",
    day_sheet_field: str = "",
    settlement_key: str = "",
    routing_key: str = "",
    festival_key: str = "",
    vocabulary_term: str = "",
) -> dict:
    """Filter the tour-ops corpus by any of advancing key / day-sheet field /
    settlement-prep key / routing key / festival key / settlement-vocabulary term.

    With NO filter, returns a compact index of the available keys per block so
    the agent can browse. With filters, returns the matched full records; any
    filter that matches nothing is recorded in ``not_found`` (value stays None,
    never guessed). Standing framing (Miles's own doctrine + the boundaries to
    venue-hawk / ledger-lock) rides through on every response. Pure — no I/O,
    no gate.
    """
    ak  = _norm(advancing_key)
    dsf = _norm(day_sheet_field)
    sk  = _norm(settlement_key)
    rk  = _norm(routing_key)
    fk  = _norm(festival_key)
    vt  = _norm(vocabulary_term)
    any_filter = bool(ak or dsf or sk or rk or fk or vt)

    result = {
        "status": "ok",
        "miles_doctrine": dict(tour_ops_data.MILES_DOCTRINE),
        "boundaries": [dict(b) for b in tour_ops_data.BOUNDARIES.values()],
    }

    if not any_filter:
        # Browse mode — index of keys only, kept compact.
        result["mode"] = "index"
        result["advancing_keys"] = list(tour_ops_data.ADVANCING_DOCTRINE)
        result["day_sheet_fields"] = [rec["field"] for rec in tour_ops_data.DAY_SHEET_SPEC]
        result["settlement_keys"] = list(tour_ops_data.SETTLEMENT_PREP_DOCTRINE)
        result["routing_keys"] = list(tour_ops_data.ROUTING_AND_PREP)
        result["festival_keys"] = list(tour_ops_data.FESTIVAL_VARIANT)
        result["vocabulary_terms"] = list(tour_ops_data.SETTLEMENT_VOCABULARY)
        result["day_sheet_variant_keys"] = list(tour_ops_data.DAY_SHEET_VARIANTS)
        return result

    result["mode"] = "filtered"
    not_found = []

    result["advancing"] = []
    if ak:
        rec = tour_ops_data.ADVANCING_DOCTRINE.get(ak)
        if rec:
            result["advancing"].append(dict(rec))
        else:
            not_found.append({"filter": "advancing_key", "value": ak, "match": None})

    result["day_sheet"] = []
    if dsf:
        rec = next((r for r in tour_ops_data.DAY_SHEET_SPEC if r["field"] == dsf), None)
        if rec:
            result["day_sheet"].append(dict(rec))
        else:
            not_found.append({"filter": "day_sheet_field", "value": dsf, "match": None})

    result["settlement"] = []
    if sk:
        rec = tour_ops_data.SETTLEMENT_PREP_DOCTRINE.get(sk)
        if rec:
            result["settlement"].append(dict(rec))
        else:
            not_found.append({"filter": "settlement_key", "value": sk, "match": None})

    result["routing"] = []
    if rk:
        rec = tour_ops_data.ROUTING_AND_PREP.get(rk)
        if rec:
            result["routing"].append(dict(rec))
        else:
            not_found.append({"filter": "routing_key", "value": rk, "match": None})

    result["festival"] = []
    if fk:
        rec = tour_ops_data.FESTIVAL_VARIANT.get(fk)
        if rec:
            result["festival"].append(dict(rec))
        else:
            not_found.append({"filter": "festival_key", "value": fk, "match": None})

    result["vocabulary"] = []
    if vt:
        rec = tour_ops_data.SETTLEMENT_VOCABULARY.get(vt)
        if rec:
            result["vocabulary"].append(dict(rec))
        else:
            not_found.append({"filter": "vocabulary_term", "value": vt, "match": None})

    result["not_found"] = not_found
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# build_tour_doc_scaffold — OPTION B: compact ingredients only, agent writes
# prose. NOT gated. Documents, never figures; prep, never negotiation or
# accounting.
# ═══════════════════════════════════════════════════════════════════════════════
async def build_tour_doc_scaffold(doc_type: str = "", inputs: dict = None) -> dict:
    """Build compact ingredients for one tour-ops document; Miles writes the prose.

    Three doc types — ``advance_pack``, ``day_sheet``, ``settlement_prep_sheet``.
    Every scaffold header carries Miles's standing doctrine (prep not
    negotiation, prep not accounting, documents not figures). No corpus content
    is a judgment about the artist's specific tour — the checklists, field
    lists, and questions are the standing operations toolkit the agent applies.
    Every artist-fact slot is verbatim, a [NEEDS:<x>] gap, or an
    [ARTIST-SUPPLIED:<x>] marker; all such markers aggregate into ``missing``.
    Unknown doc_type -> structured error listing the supported types.
    """
    dt = _norm(doc_type).lower()
    inputs = dict(inputs) if isinstance(inputs, dict) else {}
    if dt == "advance_pack":
        return _scaffold_advance_pack(inputs)
    if dt == "day_sheet":
        return _scaffold_day_sheet(inputs)
    if dt == "settlement_prep_sheet":
        return _scaffold_settlement_prep_sheet(inputs)
    return {
        "status": "unknown_doc_type",
        "doc_type": dt or "(missing)",
        "supported_doc_types": list(DOC_TYPES),
        "message": ("Unsupported doc_type. Supported: " + ", ".join(DOC_TYPES) + "."),
    }


def _header(title: str) -> dict:
    """Scaffold header — carries Miles's standing doctrine verbatim from the
    corpus on every doc type."""
    return {
        "title": _heading(title),
        "prep_not_negotiation": _PREP_NOT_NEGOTIATION,
        "prep_not_accounting": _PREP_NOT_ACCOUNTING,
        "documents_not_figures": _DOCUMENTS_NOT_FIGURES,
    }


def _scaffold_advance_pack(inputs: dict) -> dict:
    """Ingredients for an advance package: venue-vs-production-advance
    distinction, the package checklist, venue-provides fields, the union-house
    labor-rule risk note, and parking doctrine. The deal memo is
    ARTIST-SUPPLIED — Miles consumes it and never invents its terms (booking
    and deal terms are venue-hawk's domain, per BOUNDARIES)."""
    missing: list = []
    notes: list = []
    sections: list = []

    venue_rec      = tour_ops_data.ADVANCING_DOCTRINE["venue_advance"]
    production_rec = tour_ops_data.ADVANCING_DOCTRINE["production_advance"]
    sections.append({
        "key": "venue_vs_production_advance",
        "heading": _heading("Venue advance vs production advance"),
        "venue_advance": venue_rec["description"],
        "production_advance": production_rec["description"],
    })

    sections.append({
        "key": "advance_package_checklist",
        "heading": _heading("Advance package checklist"),
        "items": list(_ADVANCE_PACKAGE_CHECKLIST),
        "source": tour_ops_data.ADVANCING_DOCTRINE["advance_package_contents"]["description"],
    })

    sections.append({
        "key": "venue_provides",
        "heading": _heading("What the venue provides"),
        "fields": list(venue_rec["venue_provides"]),
    })

    sections.append({
        "key": "union_house_risk",
        "heading": _heading("Union-house labor-rule risk"),
        "note": venue_rec["union_house_risk"],
    })

    parking_rec = tour_ops_data.ADVANCING_DOCTRINE["parking_and_load_out"]
    sections.append({
        "key": "parking_doctrine",
        "heading": _heading("Parking and load-out doctrine"),
        "doctrine": parking_rec["parking_doctrine"],
        "description": parking_rec["description"],
    })

    # Deal memo — artist-supplied, consumed verbatim, never invented.
    deal_memo = inputs.get("deal_memo")
    if _missing(deal_memo):
        marker = _ARTIST_SUPPLIED.format("deal_memo")
        missing.append(marker)
        notes.append({
            "section": "deal_memo",
            "marker": marker,
            "note": ("the deal memo is supplied by the artist/team — Miles consumes its "
                     "terms and never invents them; booking and deal terms are "
                     "venue-hawk's domain"),
        })
    else:
        sections.append({
            "key": "deal_memo",
            "heading": _heading("Deal memo (artist-supplied, consumed verbatim)"),
            "content": deal_memo,  # verbatim
        })

    notes.append({
        "section": "boundaries",
        "note": tour_ops_data.BOUNDARIES["booking_and_deal_terms"]["miles_role"],
    })

    return _finish(_header("Advance pack"), "advance_pack", sections, missing, notes)


def _scaffold_day_sheet(inputs: dict) -> dict:
    """Build a day sheet from DAY_SHEET_SPEC + DAY_SHEET_VARIANTS.

    HARD PRIVACY RULE: fields flagged ``sensitive: True`` are EXCLUDED from the
    printable/default output list entirely (not just their values — the field
    itself is omitted) unless the caller explicitly passes
    ``inputs["include_sensitive"] = True`` AND the variant is ``principal``
    (never a distributed/printable variant). Field VALUES are artist-supplied
    per field ([ARTIST-SUPPLIED:<field>] when not given in ``inputs``)."""
    missing: list = []
    notes: list = []
    sections: list = []

    variant = _norm(inputs.get("variant")).lower() or "printable"
    # The default/printable output ALWAYS excludes sensitive fields, regardless
    # of include_sensitive — only an explicit request on the principal variant
    # can surface them.
    include_sensitive = bool(inputs.get("include_sensitive")) and variant == "principal"

    fields_out = []
    excluded_sensitive_fields = []
    for rec in tour_ops_data.DAY_SHEET_SPEC:
        field = rec["field"]
        sensitive = rec["sensitive"]
        if sensitive and not include_sensitive:
            excluded_sensitive_fields.append(field)
            continue  # omitted entirely from the output field list
        value = inputs.get(field)
        if _missing(value):
            marker = _ARTIST_SUPPLIED.format(field)
            missing.append(marker)
            fields_out.append({"field": field, "description": rec["description"],
                                "sensitive": sensitive, "value": marker})
        else:
            fields_out.append({"field": field, "description": rec["description"],
                                "sensitive": sensitive, "value": value})  # verbatim

    sections.append({
        "key": "day_sheet_fields",
        "heading": _heading(f"Day sheet fields — {variant} variant"),
        "variant": variant,
        "fields": fields_out,
        "sensitive_fields_excluded": excluded_sensitive_fields,
    })

    notes.append({
        "section": "day_sheet_fields",
        "note": ("sensitive fields (artist hotel info, door codes, flight details) are "
                 "excluded from the printable/default output; only an explicit "
                 "include_sensitive request on the principal variant surfaces them"),
    })

    sections.append({
        "key": "day_sheet_variants_doctrine",
        "heading": _heading("Principal vs crew day-sheet doctrine"),
        "doctrine": tour_ops_data.DAY_SHEET_VARIANTS["principal_vs_crew"],
    })

    return _finish(_header("Day sheet"), "day_sheet", sections, missing, notes)


def _scaffold_settlement_prep_sheet(inputs: dict) -> dict:
    """Ingredients for a settlement-prep sheet: deal terms RESTATED VERBATIM
    from artist-supplied inputs (never invented) + a prep checklist pulled from
    SETTLEMENT_PREP_DOCTRINE + walk-the-numbers QUESTIONS.

    CRITICAL INVARIANT: this function never computes or outputs any total/sum/
    arithmetic result — no computed totals, ever, only restated inputs +
    checklist + questions."""
    missing: list = []
    notes: list = []
    sections: list = []

    # Deal terms — artist-supplied, restated verbatim, never computed.
    deal_terms = inputs.get("deal_terms")
    if _missing(deal_terms):
        marker = _ARTIST_SUPPLIED.format("deal_terms")
        missing.append(marker)
        notes.append({
            "section": "deal_terms_restated",
            "marker": marker,
            "note": "deal terms not supplied — restated verbatim only when supplied, never invented",
        })
    else:
        sections.append({
            "key": "deal_terms_restated",
            "heading": _heading("Deal terms — restated verbatim"),
            "content": deal_terms,  # verbatim — never a computed total
        })

    sections.append({
        "key": "settlement_prep_checklist",
        "heading": _heading("Settlement prep checklist"),
        "items": [
            {"key": k, "topic": r["topic"], "description": r["description"]}
            for k, r in tour_ops_data.SETTLEMENT_PREP_DOCTRINE.items()
        ],
    })

    sections.append({
        "key": "walk_the_numbers_questions",
        "heading": _heading("Walk-the-numbers — questions, never a computed total"),
        "questions": list(_SETTLEMENT_WALK_THE_NUMBERS_QUESTIONS),
    })

    notes.append({
        "section": "ledger_lock_boundary",
        "note": tour_ops_data.BOUNDARIES["royalty_and_accounting"]["miles_role"],
    })

    return _finish(_header("Settlement prep sheet"), "settlement_prep_sheet",
                   sections, missing, notes)


def _finish(header: dict, doc_type: str, sections: list, missing: list, notes: list) -> dict:
    """Assemble the scaffold, deduping the aggregated gap markers."""
    return {
        "status": "scaffold_ready",
        "doc_type": doc_type,
        "header": header,
        "sections": sections,
        "missing": list(dict.fromkeys(missing)),
        "notes": notes,
    }
