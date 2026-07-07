"""
PLMKR Mo (mobile-monetize) — revenue-diversification DOC-WRITER service
(mock-first, Option B).

Backs the Mo (mobile-monetize, Monetization) agent's tool_use loop in
/api/chat_stream (see MOBILE_MONETIZE_TOOLS in main.py). Mo does not just
describe revenue streams — these functions let the agent take one real
action: assemble organized preparation material from Mo's real
revenue-diversification knowledge base — a structured lookup over the
monetization corpus, and compact doc-scaffold ingredients the agent turns
into prose in its own turn.

DOC-WRITER OPTION B (Cree / Nadia / Reed / Lex / Miles / Data precedent):
  build_monetization_doc_scaffold returns COMPACT ingredients only — matched
  doctrine, taxonomy records, sequencing classifications, aggregated gaps.
  The AGENT writes the prose in its turn. There is ZERO model-call in this
  module (no Anthropic SDK import, no create-message call) — AST-enforced by
  tests.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live platform/monetization APIs, no LLM.
  - NO secrets are read or embedded, and there is NO connection gate: both
    tools are pure corpus-read / data-scaffold tools that need no connected
    account (the old platform-monetization-account gate and its
    enable-monetization action are RETIRED; flipping a live monetization
    switch is not Mo's domain here — organizing the artist's own stated
    revenue picture against Mo's doctrine is).
  - Deterministic: no timestamps or random values leak into return payloads,
    so tests can assert on exact structure.

HARD RULES honored here (mirroring monetization_data.py's doctrine — this
domain is explicitly about money, so these are enforced with extra care):
  - no_income_projections / mechanisms_not_figures: Mo never states an income
    projection, a dollar figure, a percentage, or any other computed numeric
    income figure, for any stream, under any circumstance. NO arithmetic is
    EVER performed in this module. This is the single most important
    invariant in this module.
  - diversify_dont_concentrate: sequencing questions/considerations
    (compounding relationships, no-catastrophic-single-point,
    start-small-then-add) are surfaced verbatim from the corpus — never a
    computed total or percentage of anything.
  - BOUNDARIES: Mo maps the revenue landscape and sequences the strategy; Mo
    does not execute any other department's specialized work (grants ->
    fund-phantom, brand outreach -> brand-connect, royalty registration/
    collection -> ledger-lock, sync pitching -> ink-and-air, booking/touring
    -> tour-commander).
  - NEVER fabricate: every artist-fact slot is the supplied input VERBATIM, a
    [NEEDS:<x>] gap, or an [ARTIST-SUPPLIED:<x>] marker — never invented. A
    supplied active_stream name that is not a recognized taxonomy key is
    never silently accepted — it is noted as an unknown_stream instead.
    Corpus content (doctrine, taxonomy, sequencing, diversification) is
    pulled verbatim from monetization_data.
"""
import monetization_data


# ── Framing + gap markers (data, not logic) ───────────────────────────────────
_GAP = "[NEEDS:{}]"
_ARTIST_SUPPLIED = "[ARTIST-SUPPLIED:{}]"

# The two scaffolds this DOC-WRITER produces.
DOC_TYPES = ("revenue_map", "diversification_plan")

# The two recognized audience_stage values (artist-supplied, never guessed).
_AUDIENCE_STAGE_VALUES = ("pre_audience", "has_audience")

# Standing framing surfaced on every scaffold header — pulled verbatim from
# the corpus so no output can be read as an income projection or a figure.
_NO_INCOME_PROJECTIONS      = monetization_data.MO_DOCTRINE["no_income_projections"]
_MECHANISMS_NOT_FIGURES     = monetization_data.MO_DOCTRINE["mechanisms_not_figures"]
_DIVERSIFY_DONT_CONCENTRATE = monetization_data.MO_DOCTRINE["diversify_dont_concentrate"]

# SEQUENCING's own classification of which taxonomy streams are addressable
# regardless of audience stage versus only once an audience exists. Any
# taxonomy stream NOT named in either list is not classified by the corpus at
# all — this module never invents a stage restriction the corpus does not
# state, so such a stream's ``addressable`` field is always True (no known
# restriction), never guessed as gated.
_AUDIENCE_INDEPENDENT_STREAMS = set(
    monetization_data.SEQUENCING["audience_independent_streams"]["streams"])
_AUDIENCE_DEPENDENT_STREAMS = set(
    monetization_data.SEQUENCING["audience_dependent_streams"]["streams"])


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
# lookup_monetization_doctrine — structured lookup/filter over the
# monetization_data corpus. Pure corpus read; NOT gated. No judgment is made
# about the artist's own revenue — this returns the standing doctrine the
# agent applies.
# ═══════════════════════════════════════════════════════════════════════════════
async def lookup_monetization_doctrine(
    stream_key: str = "",
    diversification_key: str = "",
    sequencing_key: str = "",
    admin_key: str = "",
) -> dict:
    """Filter the monetization corpus by any of revenue-stream key /
    diversification key / sequencing key / admin key.

    With NO filter, returns a compact index of the available keys per block so
    the agent can browse. With filters, returns the matched full records; any
    filter that matches nothing is recorded in ``not_found`` (value stays None,
    never guessed). Standing framing (Mo's own doctrine, the integrity rules,
    and the boundaries to the owning departments) rides through on every
    response. Pure — no I/O, no gate.
    """
    sk  = _norm(stream_key)
    dk  = _norm(diversification_key)
    sqk = _norm(sequencing_key)
    ak  = _norm(admin_key)
    any_filter = bool(sk or dk or sqk or ak)

    result = {
        "status": "ok",
        "mo_doctrine": dict(monetization_data.MO_DOCTRINE),
        "integrity": [dict(i) for i in monetization_data.INTEGRITY.values()],
        "boundaries": [dict(b) for b in monetization_data.BOUNDARIES.values()],
    }

    if not any_filter:
        # Browse mode — index of keys only, kept compact.
        result["mode"] = "index"
        result["stream_keys"] = list(monetization_data.REVENUE_STREAM_TAXONOMY)
        result["diversification_keys"] = list(monetization_data.DIVERSIFICATION)
        result["sequencing_keys"] = list(monetization_data.SEQUENCING)
        result["admin_keys"] = list(monetization_data.ADMIN)
        return result

    result["mode"] = "filtered"
    not_found = []

    result["streams"] = []
    if sk:
        rec = monetization_data.REVENUE_STREAM_TAXONOMY.get(sk)
        if rec:
            result["streams"].append(dict(rec))
        else:
            not_found.append({"filter": "stream_key", "value": sk, "match": None})

    result["diversification"] = []
    if dk:
        rec = monetization_data.DIVERSIFICATION.get(dk)
        if rec:
            result["diversification"].append(dict(rec))
        else:
            not_found.append({"filter": "diversification_key", "value": dk, "match": None})

    result["sequencing"] = []
    if sqk:
        rec = monetization_data.SEQUENCING.get(sqk)
        if rec:
            result["sequencing"].append(dict(rec))
        else:
            not_found.append({"filter": "sequencing_key", "value": sqk, "match": None})

    result["admin"] = []
    if ak:
        rec = monetization_data.ADMIN.get(ak)
        if rec:
            result["admin"].append(dict(rec))
        else:
            not_found.append({"filter": "admin_key", "value": ak, "match": None})

    result["not_found"] = not_found
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# build_monetization_doc_scaffold — OPTION B: compact ingredients only, agent
# writes prose. NOT gated. Mechanisms, never figures; sequencing questions,
# never a projection.
# ═══════════════════════════════════════════════════════════════════════════════
async def build_monetization_doc_scaffold(doc_type: str = "", inputs: dict = None) -> dict:
    """Build compact ingredients for one monetization document; Mo writes the prose.

    Two doc types — ``revenue_map`` and ``diversification_plan``. Every
    scaffold header carries Mo's standing doctrine (no income projections,
    mechanisms not figures, diversify don't concentrate). No corpus content is
    a judgment about the artist's specific finances — the taxonomy,
    sequencing classification, and diversification doctrine are the standing
    toolkit the agent applies. NO arithmetic is ever performed here: every
    artist-fact slot is verbatim, a [NEEDS:<x>] gap, or an
    [ARTIST-SUPPLIED:<x>] marker; all such markers aggregate into ``missing``.
    Unknown doc_type -> structured error listing the supported types.
    """
    dt = _norm(doc_type).lower()
    inputs = dict(inputs) if isinstance(inputs, dict) else {}
    if dt == "revenue_map":
        return _scaffold_revenue_map(inputs)
    if dt == "diversification_plan":
        return _scaffold_diversification_plan(inputs)
    return {
        "status": "unknown_doc_type",
        "doc_type": dt or "(missing)",
        "supported_doc_types": list(DOC_TYPES),
        "message": ("Unsupported doc_type. Supported: " + ", ".join(DOC_TYPES) + "."),
    }


def _header(title: str) -> dict:
    """Scaffold header — carries Mo's standing doctrine verbatim from the
    corpus on every doc type."""
    return {
        "title": _heading(title),
        "no_income_projections": _NO_INCOME_PROJECTIONS,
        "mechanisms_not_figures": _MECHANISMS_NOT_FIGURES,
        "diversify_dont_concentrate": _DIVERSIFY_DONT_CONCENTRATE,
    }


def _active_streams_info(inputs: dict):
    """Read ``inputs["active_streams"]`` and split it into (declared,
    recognized_keys, unknown_streams, missing_marker).

    ``declared`` is the artist-supplied list, verbatim. ``recognized_keys`` is
    the subset that matches a REVENUE_STREAM_TAXONOMY key. ``unknown_streams``
    is every supplied name that does NOT match a taxonomy key — noted, never
    silently accepted. A missing/absent/non-list ``active_streams`` produces a
    [ARTIST-SUPPLIED:active_streams] marker; an explicit empty list is a
    legitimate answer (no streams active yet), not a gap.
    """
    raw = inputs.get("active_streams")
    if not isinstance(raw, list):
        return [], set(), [], _ARTIST_SUPPLIED.format("active_streams")
    declared = [s for s in raw if isinstance(s, str)]
    recognized = {s for s in declared if s in monetization_data.REVENUE_STREAM_TAXONOMY}
    unknown = [s for s in declared if s not in monetization_data.REVENUE_STREAM_TAXONOMY]
    return declared, recognized, unknown, None


def _addressable_candidates(recognized_keys: set, audience_stage: str, stage_valid: bool) -> list:
    """Every taxonomy stream NOT already active, carrying its sequencing
    classification and an ``addressable`` tri-state:
      - True  -> plausible now (audience-independent, or no stage restriction
        the corpus states, or the artist already has an audience)
      - False -> audience-dependent and the artist's stated stage is
        pre_audience
      - None  -> audience-dependent and the stage is unknown/unrecognized —
        never guessed either way
    Never a projection of what any stream might earn — mechanism,
    prerequisites, payment_pattern, and owning_department only, verbatim.
    """
    candidates = []
    for key, rec in monetization_data.REVENUE_STREAM_TAXONOMY.items():
        if key in recognized_keys:
            continue
        entry = {
            "key": key,
            "description": rec["description"],
            "mechanism": rec["mechanism"],
            "prerequisites": list(rec["prerequisites"]),
            "payment_pattern": rec["payment_pattern"],
            "owning_department": rec["owning_department"],
        }
        if key in _AUDIENCE_INDEPENDENT_STREAMS:
            entry["sequencing_classification"] = "audience_independent"
            entry["addressable"] = True
        elif key in _AUDIENCE_DEPENDENT_STREAMS:
            entry["sequencing_classification"] = "audience_dependent"
            entry["addressable"] = (audience_stage == "has_audience") if stage_valid else None
        else:
            entry["sequencing_classification"] = "unclassified"
            entry["addressable"] = True
        candidates.append(entry)
    return candidates


def _active_streams_section(declared: list, recognized_keys: set, unknown_streams: list) -> dict:
    recognized_records = [
        {
            "key": k,
            "description": monetization_data.REVENUE_STREAM_TAXONOMY[k]["description"],
            "mechanism": monetization_data.REVENUE_STREAM_TAXONOMY[k]["mechanism"],
            "payment_pattern": monetization_data.REVENUE_STREAM_TAXONOMY[k]["payment_pattern"],
            "owning_department": monetization_data.REVENUE_STREAM_TAXONOMY[k]["owning_department"],
        }
        for k in monetization_data.REVENUE_STREAM_TAXONOMY if k in recognized_keys
    ]
    return {
        "key": "active_streams",
        "heading": _heading("Active streams (artist-supplied)"),
        "declared": list(declared),
        "recognized": recognized_records,
        "unknown_streams": list(unknown_streams),
    }


def _resolve_audience_stage(inputs: dict, missing: list, notes: list):
    """Reads inputs["audience_stage"], appending gap/error notes as needed.

    Returns (audience_stage_normalized_or_empty, stage_valid_bool). A missing
    value becomes a gap marker; a supplied-but-unrecognized value is noted as
    an error and never silently defaulted — both cases leave stage_valid
    False so addressability is never falsely asserted for audience-dependent
    streams.
    """
    raw = inputs.get("audience_stage")
    audience_stage = _norm(raw)
    stage_valid = audience_stage in _AUDIENCE_STAGE_VALUES
    if _missing(raw):
        marker = _ARTIST_SUPPLIED.format("audience_stage")
        missing.append(marker)
        notes.append({
            "section": "audience_stage",
            "marker": marker,
            "note": ("no audience_stage supplied — addressable candidates are grouped for "
                     "every non-active stream WITHOUT a stage-based filtering claim; "
                     "audience-dependent streams are marked addressable: null rather than "
                     "guessed either way"),
        })
    elif not stage_valid:
        notes.append({
            "section": "audience_stage",
            "error": "unknown_audience_stage",
            "note": (f"'{audience_stage}' is not a recognized audience_stage value — expected "
                     "one of: " + ", ".join(_AUDIENCE_STAGE_VALUES) + "; addressable candidates "
                     "are grouped WITHOUT a stage-based filtering claim rather than guessed"),
        })
    return audience_stage, stage_valid


def _scaffold_revenue_map(inputs: dict) -> dict:
    """Ingredients for a revenue map: the artist's current streams matched
    against the full taxonomy, every other taxonomy stream surfaced as an
    addressable_next candidate (stage-aware, never guessed), and
    DIVERSIFICATION's compounding_relationships / no_catastrophic_single_point
    doctrine verbatim.

    CRITICAL INVARIANT: never a projection, never a computed total or
    percentage of anything — only restated inputs + verbatim corpus text +
    structural classification."""
    missing: list = []
    notes: list = []
    sections: list = []

    declared, recognized_keys, unknown_streams, marker = _active_streams_info(inputs)
    if marker:
        missing.append(marker)
        notes.append({
            "section": "active_streams",
            "marker": marker,
            "note": ("no active_streams supplied — treated as none currently active for this "
                     "map; never guessed"),
        })
    if unknown_streams:
        notes.append({
            "section": "active_streams",
            "error": "unknown_stream",
            "note": ("the following supplied active_streams are not recognized taxonomy stream "
                     "keys and are not treated as active: " + ", ".join(unknown_streams)),
            "unknown_streams": list(unknown_streams),
        })

    sections.append(_active_streams_section(declared, recognized_keys, unknown_streams))

    audience_stage, stage_valid = _resolve_audience_stage(inputs, missing, notes)
    candidates = _addressable_candidates(recognized_keys, audience_stage, stage_valid)

    sections.append({
        "key": "addressable_next",
        "heading": _heading("Addressable next streams"),
        "audience_stage": audience_stage or None,
        "stage_filtering_applied": stage_valid,
        "candidates": candidates,
    })

    div = monetization_data.DIVERSIFICATION
    sections.append({
        "key": "diversification_doctrine",
        "heading": _heading("Diversification doctrine — sequencing considerations, never a projection"),
        "compounding_relationships": div["compounding_relationships"]["description"],
        "no_catastrophic_single_point": div["no_catastrophic_single_point"]["description"],
    })

    return _finish(_header("Revenue map"), "revenue_map", sections, missing, notes)


def _scaffold_diversification_plan(inputs: dict) -> dict:
    """Ingredients for a diversification plan: 2-3 next-stream CANDIDATES
    (same stage-aware addressability logic as revenue_map), each carrying its
    prerequisites and owning_department verbatim so the agent can route
    execution, plus DIVERSIFICATION's start_small_then_add doctrine verbatim.

    CRITICAL INVARIANT: never a projection of what any candidate stream might
    earn — no arithmetic, no figure, ever."""
    missing: list = []
    notes: list = []
    sections: list = []

    declared, recognized_keys, unknown_streams, marker = _active_streams_info(inputs)
    if marker:
        missing.append(marker)
        notes.append({
            "section": "active_streams",
            "marker": marker,
            "note": ("no active_streams supplied — treated as none currently active for this "
                     "plan; never guessed"),
        })
    if unknown_streams:
        notes.append({
            "section": "active_streams",
            "error": "unknown_stream",
            "note": ("the following supplied active_streams are not recognized taxonomy stream "
                     "keys and are not treated as active: " + ", ".join(unknown_streams)),
            "unknown_streams": list(unknown_streams),
        })

    sections.append(_active_streams_section(declared, recognized_keys, unknown_streams))

    audience_stage, stage_valid = _resolve_audience_stage(inputs, missing, notes)
    all_candidates = _addressable_candidates(recognized_keys, audience_stage, stage_valid)
    next_candidates = [c for c in all_candidates if c["addressable"] is True][:3]

    sections.append({
        "key": "next_stream_candidates",
        "heading": _heading("Next stream candidates — never a projection of what any might earn"),
        "audience_stage": audience_stage or None,
        "stage_filtering_applied": stage_valid,
        "candidates": next_candidates,
    })

    sections.append({
        "key": "start_small_then_add_doctrine",
        "heading": _heading("Start small, then add"),
        "doctrine": monetization_data.DIVERSIFICATION["start_small_then_add"]["description"],
    })

    return _finish(_header("Diversification plan"), "diversification_plan", sections, missing, notes)


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
