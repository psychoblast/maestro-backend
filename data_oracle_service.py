"""
PLMKR Data-Oracle (Data) — streaming/audience-analytics DOC-WRITER service
(mock-first, Option B).

Backs the Data-Oracle (Data — Analytics) agent's tool_use loop in
/api/chat_stream (see DATA_ORACLE_TOOLS in main.py). Data does not just
describe the numbers — these functions let the agent take one real action:
assemble organized preparation material from Data's real analytics knowledge
base — a structured lookup over the analytics corpus, and compact
doc-scaffold ingredients the agent turns into prose in its own turn.

DOC-WRITER OPTION B (Cree / Nadia / Reed / Lex / Miles precedent):
  build_analytics_doc_scaffold returns COMPACT ingredients only — matched
  doctrine, applicable patterns, field lists, questions, aggregated gaps. The
  AGENT writes the prose in its turn. There is ZERO model-call in this module
  (no Anthropic SDK import, no create-message call) — AST-enforced by tests.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live DSP/analytics-warehouse APIs, no LLM.
  - NO secrets are read or embedded, and there is NO connection gate: both
    tools are pure corpus-read / data-scaffold tools that need no connected
    account (the old data-warehouse-account gate and its export-scheduling
    action are RETIRED; scheduling a live export is not Data's domain here —
    organizing an artist's own supplied numbers against Data's doctrine is).
  - Deterministic: no timestamps or random values leak into return payloads,
    so tests can assert on exact structure.

HARD RULES honored here (mirroring analytics_data.py's doctrine):
  - never_fabricate_numbers: Data never fabricates, estimates, or
    extrapolates an artist's own numbers. NO arithmetic is ever performed in
    this module — every metric field and every "want" is restated VERBATIM
    from artist-supplied inputs, never computed, summed, divided, or scored.
    This is the single most important invariant in this module.
  - notes_not_verdicts: interpretation bands are always surfaced in full,
    never narrowed to "the one that applies" — deciding which band actually
    fits the artist's own numbers requires arithmetic only the AGENT performs
    in its own turn, never this module.
  - BOUNDARIES: Data surfaces the numbers and the diagnosis; acting on that
    diagnosis (a campaign, a booking, a monetization or release-strategy
    change) belongs to the owning department, not to Data.
  - NEVER fabricate: every artist-fact slot is the supplied input VERBATIM, a
    [NEEDS:<x>] gap, or an [ARTIST-SUPPLIED:<x>] marker — never invented.
    Corpus content (doctrine, bands, patterns) is pulled verbatim from
    analytics_data.
"""
import analytics_data


# ── Framing + gap markers (data, not logic) ───────────────────────────────────
_GAP = "[NEEDS:{}]"
_ARTIST_SUPPLIED = "[ARTIST-SUPPLIED:{}]"

# The two scaffolds this DOC-WRITER produces.
DOC_TYPES = ("metrics_readout", "stakeholder_stat_sheet")

# Standing framing surfaced on every scaffold header — pulled verbatim from
# the corpus so no output can be read as a fabricated number, an executed
# action, or a pass/fail verdict.
_NEVER_FABRICATE_NUMBERS = analytics_data.DATA_DOCTRINE["never_fabricate_numbers"]
_INSIGHTS_NOT_ACTIONS    = analytics_data.DATA_DOCTRINE["insights_not_actions"]
_NOTES_NOT_VERDICTS      = analytics_data.DATA_DOCTRINE["notes_not_verdicts"]
_NO_DOLLAR_FIGURES       = analytics_data.DATA_DOCTRINE["no_dollar_figures"]

# Which DIAGNOSIS_PAIRS pattern keys become "worth considering" once the
# artist has supplied the metric fields that pattern is about. Surfacing a
# pattern KEY is not a verdict — the agent decides, in its own turn using the
# artist's actual numbers, whether the pattern actually applies.
_DIAGNOSIS_PAIR_FIELDS = {
    "high_streams_low_saves": ("stream", "saves"),
    "high_saves_low_streams": ("stream", "saves"),
    "playlist_spike_then_ratio_improves": ("streams_per_listener_ratio",),
    "followers_stay_listeners_fall": ("followers", "monthly_listeners"),
}

# Dig-in questions for a metrics readout — QUESTIONS only, never a computed
# figure. Derived from the corpus's own topics (source mix, save-rate trend,
# skip rate / interpretation bands, playlist-driven spikes, follower ratio).
_METRICS_READOUT_DIG_IN_QUESTIONS = [
    "What is the source mix across profile/catalog, algorithmic, editorial, "
    "and listener-playlist streams?",
    "How has the save rate trended over the last several release cycles, not "
    "just this one snapshot?",
    "What is the skip rate on this track, and where does it fall against the "
    "interpretation bands?",
    "Is any of this movement tied to a single playlist placement rather than "
    "broad-based, sustained growth?",
    "How does the follower-to-listener ratio compare to the artist's own "
    "historical baseline?",
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
# lookup_analytics_doctrine — structured lookup/filter over the analytics_data
# corpus. Pure corpus read; NOT gated. No judgment is made about the artist's
# own numbers — this returns the standing doctrine the agent applies.
# ═══════════════════════════════════════════════════════════════════════════════
async def lookup_analytics_doctrine(
    metric_key: str = "",
    band_key: str = "",
    source_key: str = "",
    diagnosis_key: str = "",
    quality_key: str = "",
    stakeholder_key: str = "",
) -> dict:
    """Filter the analytics corpus by any of metric key / interpretation-band key /
    source key / diagnosis-pair key / quality-vs-vanity key / stakeholder key.

    With NO filter, returns a compact index of the available keys per block so
    the agent can browse. With filters, returns the matched full records; any
    filter that matches nothing is recorded in ``not_found`` (value stays None,
    never guessed). Standing framing (Data's own doctrine, the integrity rules,
    and the boundaries to the owning departments) rides through on every
    response. Pure — no I/O, no gate.
    """
    mk  = _norm(metric_key)
    bk  = _norm(band_key)
    sk  = _norm(source_key)
    dk  = _norm(diagnosis_key)
    qk  = _norm(quality_key)
    stk = _norm(stakeholder_key)
    any_filter = bool(mk or bk or sk or dk or qk or stk)

    result = {
        "status": "ok",
        "data_doctrine": dict(analytics_data.DATA_DOCTRINE),
        "integrity": [dict(i) for i in analytics_data.INTEGRITY.values()],
        "boundaries": [dict(b) for b in analytics_data.BOUNDARIES.values()],
    }

    if not any_filter:
        # Browse mode — index of keys only, kept compact.
        result["mode"] = "index"
        result["metric_keys"] = list(analytics_data.METRIC_DEFINITIONS)
        result["band_keys"] = list(analytics_data.INTERPRETATION_BANDS)
        result["source_keys"] = list(analytics_data.SOURCE_BREAKDOWN)
        result["diagnosis_keys"] = list(analytics_data.DIAGNOSIS_PAIRS)
        result["quality_keys"] = list(analytics_data.QUALITY_VS_VANITY)
        result["stakeholder_keys"] = list(analytics_data.STAKEHOLDER_FRAMING)
        return result

    result["mode"] = "filtered"
    not_found = []

    result["metrics"] = []
    if mk:
        rec = analytics_data.METRIC_DEFINITIONS.get(mk)
        if rec:
            result["metrics"].append(dict(rec))
        else:
            not_found.append({"filter": "metric_key", "value": mk, "match": None})

    result["bands"] = []
    if bk:
        rec = analytics_data.INTERPRETATION_BANDS.get(bk)
        if rec:
            result["bands"].append(dict(rec))
        else:
            not_found.append({"filter": "band_key", "value": bk, "match": None})

    result["sources"] = []
    if sk:
        rec = analytics_data.SOURCE_BREAKDOWN.get(sk)
        if rec:
            result["sources"].append(dict(rec))
        else:
            not_found.append({"filter": "source_key", "value": sk, "match": None})

    result["diagnosis"] = []
    if dk:
        rec = analytics_data.DIAGNOSIS_PAIRS.get(dk)
        if rec:
            result["diagnosis"].append(dict(rec))
        else:
            not_found.append({"filter": "diagnosis_key", "value": dk, "match": None})

    result["quality"] = []
    if qk:
        rec = analytics_data.QUALITY_VS_VANITY.get(qk)
        if rec:
            result["quality"].append(dict(rec))
        else:
            not_found.append({"filter": "quality_key", "value": qk, "match": None})

    result["stakeholders"] = []
    if stk:
        rec = analytics_data.STAKEHOLDER_FRAMING.get(stk)
        if rec:
            result["stakeholders"].append(dict(rec))
        else:
            not_found.append({"filter": "stakeholder_key", "value": stk, "match": None})

    result["not_found"] = not_found
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# build_analytics_doc_scaffold — OPTION B: compact ingredients only, agent
# writes prose. NOT gated. Insights, never actions; notes, never verdicts.
# ═══════════════════════════════════════════════════════════════════════════════
async def build_analytics_doc_scaffold(doc_type: str = "", inputs: dict = None) -> dict:
    """Build compact ingredients for one analytics document; Data writes the prose.

    Two doc types — ``metrics_readout`` and ``stakeholder_stat_sheet``. Every
    scaffold header carries Data's standing doctrine (never fabricate numbers,
    insights not actions, notes not verdicts, no dollar figures). No corpus
    content is a judgment about the artist's specific numbers — the
    interpretation bands, diagnosis-pair keys, and dig-in questions are the
    standing analytics toolkit the agent applies. NO arithmetic is ever
    performed here: every artist-fact slot is verbatim, a [NEEDS:<x>] gap, or
    an [ARTIST-SUPPLIED:<x>] marker; all such markers aggregate into
    ``missing``. Unknown doc_type -> structured error listing the supported
    types.
    """
    dt = _norm(doc_type).lower()
    inputs = dict(inputs) if isinstance(inputs, dict) else {}
    if dt == "metrics_readout":
        return _scaffold_metrics_readout(inputs)
    if dt == "stakeholder_stat_sheet":
        return _scaffold_stakeholder_stat_sheet(inputs)
    return {
        "status": "unknown_doc_type",
        "doc_type": dt or "(missing)",
        "supported_doc_types": list(DOC_TYPES),
        "message": ("Unsupported doc_type. Supported: " + ", ".join(DOC_TYPES) + "."),
    }


def _header(title: str) -> dict:
    """Scaffold header — carries Data's standing doctrine verbatim from the
    corpus on every doc type."""
    return {
        "title": _heading(title),
        "never_fabricate_numbers": _NEVER_FABRICATE_NUMBERS,
        "insights_not_actions": _INSIGHTS_NOT_ACTIONS,
        "notes_not_verdicts": _NOTES_NOT_VERDICTS,
        "no_dollar_figures": _NO_DOLLAR_FIGURES,
    }


def _scaffold_metrics_readout(inputs: dict) -> dict:
    """Ingredients for a metrics readout: artist-supplied metric fields
    restated verbatim, the diagnosis-pair KEYS potentially applicable given
    which fields the artist supplied (never a verdict about which one
    applies), every interpretation band (which one actually fits depends on
    arithmetic only the agent performs), and dig-in questions.

    CRITICAL INVARIANT: this function never computes a percentage, ratio, or
    score itself — no arithmetic, ever; it only organizes verbatim inputs +
    doctrine text + questions."""
    missing: list = []
    notes: list = []
    sections: list = []

    supplied_fields = []
    for field in analytics_data.METRIC_DEFINITIONS:
        value = inputs.get(field)
        if _missing(value):
            marker = _ARTIST_SUPPLIED.format(field)
            missing.append(marker)
            supplied_fields.append({"field": field, "value": marker})
        else:
            supplied_fields.append({"field": field, "value": value})  # verbatim

    sections.append({
        "key": "supplied_metrics",
        "heading": _heading("Artist-supplied metrics"),
        "fields": supplied_fields,
    })

    applicable_pairs = []
    for pair_key, required_fields in _DIAGNOSIS_PAIR_FIELDS.items():
        if all(not _missing(inputs.get(f)) for f in required_fields):
            applicable_pairs.append(dict(analytics_data.DIAGNOSIS_PAIRS[pair_key]))
    sections.append({
        "key": "applicable_diagnosis_pairs",
        "heading": _heading("Diagnosis patterns to consider (not a verdict)"),
        "pairs": applicable_pairs,
    })

    sections.append({
        "key": "interpretation_bands",
        "heading": _heading("Interpretation bands — notes, not verdicts"),
        "bands": [dict(b) for b in analytics_data.INTERPRETATION_BANDS.values()],
    })

    sections.append({
        "key": "dig_in_questions",
        "heading": _heading("Dig-in questions"),
        "questions": list(_METRICS_READOUT_DIG_IN_QUESTIONS),
    })

    notes.append({
        "section": "integrity",
        "note": analytics_data.INTEGRITY["never_fabricate_numbers"]["description"],
    })

    return _finish(_header("Metrics readout"), "metrics_readout", sections, missing, notes)


def _scaffold_stakeholder_stat_sheet(inputs: dict) -> dict:
    """Ingredients for a stakeholder stat sheet: the named stakeholder's
    ``wants`` matched against ARTIST-SUPPLIED numbers, verbatim.

    ``inputs["stakeholder"]`` must be one of STAKEHOLDER_FRAMING's keys
    (``venues_and_agents`` or ``labels_and_ar``). A missing stakeholder
    becomes an [ARTIST-SUPPLIED:stakeholder] gap marker. A stakeholder that IS
    supplied but does not match a known key is NEVER silently defaulted — it
    is recorded as an ``unknown_stakeholder`` error note instead."""
    missing: list = []
    notes: list = []
    sections: list = []

    stakeholder = _norm(inputs.get("stakeholder"))
    if _missing(stakeholder):
        marker = _ARTIST_SUPPLIED.format("stakeholder")
        missing.append(marker)
        notes.append({
            "section": "stakeholder",
            "marker": marker,
            "note": ("no stakeholder supplied — stakeholder must be one of: " +
                     ", ".join(analytics_data.STAKEHOLDER_FRAMING) +
                     "; never guessed"),
        })
    elif stakeholder not in analytics_data.STAKEHOLDER_FRAMING:
        notes.append({
            "section": "stakeholder",
            "error": "unknown_stakeholder",
            "note": (f"'{stakeholder}' is not a known stakeholder key — supported: " +
                     ", ".join(analytics_data.STAKEHOLDER_FRAMING) +
                     "; never defaulted silently"),
        })
    else:
        rec = analytics_data.STAKEHOLDER_FRAMING[stakeholder]
        wants_matched = []
        for want in rec["wants"]:
            value = inputs.get(want)
            if _missing(value):
                marker = _ARTIST_SUPPLIED.format(want)
                missing.append(marker)
                wants_matched.append({"want": want, "value": marker})
            else:
                wants_matched.append({"want": want, "value": value})  # verbatim
        sections.append({
            "key": "stakeholder_wants",
            "heading": _heading(f"{stakeholder} — wants matched against artist-supplied numbers"),
            "stakeholder": stakeholder,
            "description": rec["description"],
            "wants": wants_matched,
        })

    return _finish(_header("Stakeholder stat sheet"), "stakeholder_stat_sheet",
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
