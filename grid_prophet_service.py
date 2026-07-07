"""
PLMKR Grid-Prophet (Kai) — digital-marketing DOC-WRITER service (mock-first,
Option B).

Backs the Grid-Prophet (Kai — Digital Marketing) agent's tool_use loop in
/api/chat_stream (see GRID_PROPHET_TOOLS in main.py). Kai does not just
advise on social media, digital growth, and algorithms — these functions let
the agent take one real action: assemble organized preparation material from
Kai's real digital-marketing knowledge base — a structured lookup over the
digital-marketing corpus, and compact doc-scaffold ingredients the agent
turns into prose in its own turn.

DOC-WRITER OPTION B (Cree / Nadia / Reed / Lex / Miles / Mo precedent):
  build_marketing_doc_scaffold returns COMPACT ingredients only — matched
  doctrine, checklists, field lists, questions, aggregated gaps. The AGENT
  writes the prose in its turn. There is ZERO model-call in this module (no
  Anthropic SDK import, no create-message call) — AST-enforced by tests.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live social/ads APIs, no LLM.
  - NO secrets are read or embedded, and there is NO connection gate: both
    tools are pure corpus-read / data-scaffold tools that need no connected
    account (the old social-account gate and its schedule-post action are
    RETIRED; scheduling a live post is not this unit's domain here —
    organizing the artist's own stated campaign picture against Kai's
    sequencing/proof/budget doctrine is).
  - Deterministic: no timestamps or random values leak into return payloads,
    so tests can assert on exact structure.

HARD RULES honored here (mirroring digital_marketing_data.py's doctrine —
this domain touches ad budgets directly, so these are enforced with extra
care):
  - NO numeric spend/budget figure of ANY kind is ever computed, summed,
    projected, or estimated in this module. NO arithmetic is EVER performed
    here. This is the single most important invariant in this module: any
    artist-supplied budget-shaped input is never echoed back as a bare
    number anywhere in a scaffold response — only ever referenced (if at
    all) as an [ARTIST-SUPPLIED:budget] marker.
  - sequence_before_spend / organic_proof_first / never_buys_growth: Kai's
    own standing doctrine is surfaced verbatim on every scaffold header so no
    output can be mistaken for a guarantee of reach, a promise of virality,
    or a growth-buying recommendation.
  - NEVER fabricate: every artist-fact slot is the supplied input VERBATIM, a
    [NEEDS:<x>] gap, or an [ARTIST-SUPPLIED:<x>] marker — never invented. A
    supplied channels_in_place value that is not a recognized sequencing
    stage name is never silently accepted — it is noted as an
    unknown_channel_stage instead. Corpus content (doctrine, checklists,
    field lists) is pulled verbatim from digital_marketing_data.
"""
import digital_marketing_data


# ── Framing + gap markers (data, not logic) ───────────────────────────────────
_GAP = "[NEEDS:{}]"
_ARTIST_SUPPLIED = "[ARTIST-SUPPLIED:{}]"

# The two scaffolds this DOC-WRITER produces.
DOC_TYPES = ("campaign_plan", "ad_test_brief")

# Standing framing surfaced on every scaffold header — pulled verbatim from the
# corpus so no output can be read as a figure, a guarantee, or a growth-buying
# recommendation.
_SEQUENCE_BEFORE_SPEND = digital_marketing_data.KAI_DOCTRINE["sequence_before_spend"]
_ORGANIC_PROOF_FIRST_DOCTRINE = digital_marketing_data.KAI_DOCTRINE["organic_proof_first"]
_NEVER_BUYS_GROWTH = digital_marketing_data.KAI_DOCTRINE["never_buys_growth"]

# The four recognized channels_in_place stage names — the CHANNEL_SEQUENCE
# sequencing_order's own order, never guessed.
_CHANNEL_STAGES = tuple(digital_marketing_data.CHANNEL_SEQUENCE["sequencing_order"]["order"])

# The creative-variants checklist, restructured from BUDGET_MECHANICS's
# test_multiple_creatives_simultaneously description into checklist form. Not
# new content — a restructuring of the corpus's own prose, exactly like
# Miles's advance-package checklist restructures corpus prose into list form.
_CREATIVE_VARIANTS_CHECKLIST = [
    "at least two to three distinct creative variants running simultaneously",
    "each variant tested against the same objective and the same audience so "
    "performance is actually comparable",
    "a native, lo-fi, vertical-format variant included alongside any more "
    "polished variant",
    "a two-second hook confirmed on every variant before it goes live",
]

# Warm-audience inventory QUESTIONS only, never a computed figure. Derived
# from PLATFORM_SELECTION's warm_before_cold doctrine — module-level private
# constant list of questions, NOT corpus content itself, mirroring how
# Miles's settlement walk-the-numbers questions live in the service, not the
# corpus.
_WARM_AUDIENCE_INVENTORY_QUESTIONS = [
    "What email or SMS list does the artist already have, and roughly how large is it?",
    "Which organic posts already show real engagement (saves, shares, comments, replies) "
    "that could be boosted as a spark ad?",
    "Who has already engaged with the artist's social profiles in the last few months?",
    "Is there a pixel or tracking setup that has already captured any website or "
    "landing-page visitors to retarget?",
    "Are there past-purchaser or past-attendee lists (merch, tickets, prior release "
    "buyers) available to retarget before reaching for a cold audience?",
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
# lookup_digital_marketing_doctrine — structured lookup/filter over the
# digital_marketing_data corpus. Pure corpus read; NOT gated. No judgment is
# made about the artist's own campaign — this returns the standing doctrine
# the agent applies.
# ═══════════════════════════════════════════════════════════════════════════════
async def lookup_digital_marketing_doctrine(
    sequence_key: str = "",
    proof_key: str = "",
    platform_key: str = "",
    budget_key: str = "",
    measurement_key: str = "",
    momentum_key: str = "",
) -> dict:
    """Filter the digital-marketing corpus by any of channel-sequence key /
    organic-proof key / platform-selection key / budget-mechanics key /
    measurement key / first-72-hours (momentum) key.

    With NO filter, returns a compact index of the available keys per block so
    the agent can browse. With filters, returns the matched full records; any
    filter that matches nothing is recorded in ``not_found`` (value stays None,
    never guessed). Standing framing (Kai's own doctrine, the integrity rules,
    and the boundaries to the owning departments) rides through on every
    response. Pure — no I/O, no gate.
    """
    sqk = _norm(sequence_key)
    pfk = _norm(proof_key)
    plk = _norm(platform_key)
    bgk = _norm(budget_key)
    mek = _norm(measurement_key)
    mmk = _norm(momentum_key)
    any_filter = bool(sqk or pfk or plk or bgk or mek or mmk)

    result = {
        "status": "ok",
        "kai_doctrine": dict(digital_marketing_data.KAI_DOCTRINE),
        "integrity": [dict(i) for i in digital_marketing_data.INTEGRITY.values()],
        "boundaries": [dict(b) for b in digital_marketing_data.BOUNDARIES.values()],
    }

    if not any_filter:
        # Browse mode — index of keys only, kept compact.
        result["mode"] = "index"
        result["sequence_keys"] = list(digital_marketing_data.CHANNEL_SEQUENCE)
        result["proof_keys"] = list(digital_marketing_data.ORGANIC_PROOF_FIRST)
        result["platform_keys"] = list(digital_marketing_data.PLATFORM_SELECTION)
        result["budget_keys"] = list(digital_marketing_data.BUDGET_MECHANICS)
        result["measurement_keys"] = list(digital_marketing_data.MEASUREMENT)
        result["momentum_keys"] = list(digital_marketing_data.FIRST_72_HOURS)
        return result

    result["mode"] = "filtered"
    not_found = []

    result["sequence"] = []
    if sqk:
        rec = digital_marketing_data.CHANNEL_SEQUENCE.get(sqk)
        if rec:
            result["sequence"].append(dict(rec))
        else:
            not_found.append({"filter": "sequence_key", "value": sqk, "match": None})

    result["proof"] = []
    if pfk:
        rec = digital_marketing_data.ORGANIC_PROOF_FIRST.get(pfk)
        if rec:
            result["proof"].append(dict(rec))
        else:
            not_found.append({"filter": "proof_key", "value": pfk, "match": None})

    result["platform"] = []
    if plk:
        rec = digital_marketing_data.PLATFORM_SELECTION.get(plk)
        if rec:
            result["platform"].append(dict(rec))
        else:
            not_found.append({"filter": "platform_key", "value": plk, "match": None})

    result["budget"] = []
    if bgk:
        rec = digital_marketing_data.BUDGET_MECHANICS.get(bgk)
        if rec:
            result["budget"].append(dict(rec))
        else:
            not_found.append({"filter": "budget_key", "value": bgk, "match": None})

    result["measurement"] = []
    if mek:
        rec = digital_marketing_data.MEASUREMENT.get(mek)
        if rec:
            result["measurement"].append(dict(rec))
        else:
            not_found.append({"filter": "measurement_key", "value": mek, "match": None})

    result["momentum"] = []
    if mmk:
        rec = digital_marketing_data.FIRST_72_HOURS.get(mmk)
        if rec:
            result["momentum"].append(dict(rec))
        else:
            not_found.append({"filter": "momentum_key", "value": mmk, "match": None})

    result["not_found"] = not_found
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# build_marketing_doc_scaffold — OPTION B: compact ingredients only, agent
# writes prose. NOT gated. Mechanisms and sequencing, never a figure — no
# spend/budget number is ever computed or echoed by this function.
# ═══════════════════════════════════════════════════════════════════════════════
async def build_marketing_doc_scaffold(doc_type: str = "", inputs: dict = None) -> dict:
    """Build compact ingredients for one digital-marketing document; Kai writes
    the prose.

    Two doc types — ``campaign_plan`` and ``ad_test_brief``. Every scaffold
    header carries Kai's standing doctrine (sequence before spend, organic
    proof first, never buys growth). No corpus content is a judgment about the
    artist's specific campaign — the sequencing order, budget mechanics, and
    measurement doctrine are the standing toolkit the agent applies. NO
    arithmetic is ever performed here, and NO spend/budget figure is ever
    echoed: every artist-fact slot is verbatim, a [NEEDS:<x>] gap, or an
    [ARTIST-SUPPLIED:<x>] marker; all such markers aggregate into ``missing``.
    Unknown doc_type -> structured error listing the supported types.
    """
    dt = _norm(doc_type).lower()
    inputs = dict(inputs) if isinstance(inputs, dict) else {}
    if dt == "campaign_plan":
        return _scaffold_campaign_plan(inputs)
    if dt == "ad_test_brief":
        return _scaffold_ad_test_brief(inputs)
    return {
        "status": "unknown_doc_type",
        "doc_type": dt or "(missing)",
        "supported_doc_types": list(DOC_TYPES),
        "message": ("Unsupported doc_type. Supported: " + ", ".join(DOC_TYPES) + "."),
    }


def _header(title: str) -> dict:
    """Scaffold header — carries Kai's standing doctrine verbatim from the
    corpus on every doc type."""
    return {
        "title": _heading(title),
        "sequence_before_spend": _SEQUENCE_BEFORE_SPEND,
        "organic_proof_first": _ORGANIC_PROOF_FIRST_DOCTRINE,
        "never_buys_growth": _NEVER_BUYS_GROWTH,
    }


def _channels_in_place_info(inputs: dict):
    """Read ``inputs["channels_in_place"]`` and split it into (declared,
    recognized, unknown_channel_stage, missing_marker).

    ``declared`` is the artist-supplied list, verbatim. ``recognized`` is the
    subset that matches one of the four CHANNEL_SEQUENCE sequencing-order
    stage names. ``unknown_channel_stage`` is every supplied name that does
    NOT match a stage name — noted, never silently accepted. A missing/
    absent/non-list ``channels_in_place`` produces an
    [ARTIST-SUPPLIED:channels_in_place] marker; an explicit empty list is a
    legitimate answer (no stage dialed in yet), not a gap.
    """
    raw = inputs.get("channels_in_place")
    if not isinstance(raw, list):
        return [], [], [], _ARTIST_SUPPLIED.format("channels_in_place")
    declared = [s for s in raw if isinstance(s, str)]
    recognized = [s for s in declared if s in _CHANNEL_STAGES]
    unknown = [s for s in declared if s not in _CHANNEL_STAGES]
    return declared, recognized, unknown, None


def _budget_out_of_scope_section() -> dict:
    """Budget/spend is ALWAYS an artist-supplied marker, never a figure.

    This section never reads any budget/spend-shaped value out of ``inputs``
    — it is a fixed, corpus-independent note so no numeric spend can ever
    leak through it, no matter what the caller supplied.
    """
    return {
        "key": "budget",
        "heading": _heading("Budget"),
        "note": ("budget and spend specifics are artist-supplied and out of scope for "
                 "this tool — this scaffold never computes or echoes a spend figure, "
                 "under any circumstance"),
        "marker": _ARTIST_SUPPLIED.format("budget"),
    }


def _scaffold_campaign_plan(inputs: dict) -> dict:
    """Ingredients for a campaign plan: the CHANNEL_SEQUENCE sequencing order
    verbatim (always returned, even with no channels_in_place supplied) +
    artist-supplied channels_in_place (validated against the four recognized
    stage names, never silently accepted) + BUDGET_MECHANICS's testing
    approach verbatim + a MEASUREMENT checklist + a budget section that is
    ALWAYS an [ARTIST-SUPPLIED:budget] marker, never a figure."""
    missing: list = []
    notes: list = []
    sections: list = []

    order_rec = digital_marketing_data.CHANNEL_SEQUENCE["sequencing_order"]
    sections.append({
        "key": "sequencing_order",
        "heading": _heading("Channel sequencing order"),
        "order": list(order_rec["order"]),
        "description": order_rec["description"],
    })

    declared, recognized, unknown, marker = _channels_in_place_info(inputs)
    if marker:
        missing.append(marker)
        notes.append({
            "section": "channels_in_place",
            "marker": marker,
            "note": ("no channels_in_place supplied — the full sequencing order is still "
                     "returned above; no stage is assumed dialed in"),
        })
    if unknown:
        notes.append({
            "section": "channels_in_place",
            "error": "unknown_channel_stage",
            "note": ("the following supplied channels_in_place values are not recognized "
                     "sequencing-stage names and are not treated as dialed in: "
                     + ", ".join(unknown)),
            "unknown_channel_stage": list(unknown),
        })

    sections.append({
        "key": "channels_in_place",
        "heading": _heading("Channels already in place (artist-supplied)"),
        "declared": list(declared),
        "recognized": list(recognized),
        "not_yet_in_place": [s for s in _CHANNEL_STAGES if s not in recognized],
        "unknown_channel_stage": list(unknown),
    })

    test_rec = digital_marketing_data.BUDGET_MECHANICS["test_multiple_creatives_simultaneously"]
    kill_rec = digital_marketing_data.BUDGET_MECHANICS["kill_fast"]
    sections.append({
        "key": "testing_approach",
        "heading": _heading("Testing approach"),
        "test_multiple_creatives_simultaneously": test_rec["description"],
        "kill_fast": kill_rec["description"],
    })

    measurement = digital_marketing_data.MEASUREMENT
    sections.append({
        "key": "measurement_checklist",
        "heading": _heading("Measurement checklist"),
        "metrics": [
            {"key": k, "description": measurement[k]["description"]}
            for k in ("save_rate", "follower_add_rate", "cost_per_engaged_listener")
        ],
        "fake_growth_warning": measurement["streams_without_saves_is_fake_growth_warning"]["description"],
    })

    sections.append(_budget_out_of_scope_section())

    return _finish(_header("Campaign plan"), "campaign_plan", sections, missing, notes)


def _scaffold_ad_test_brief(inputs: dict) -> dict:
    """Ingredients for an ad-test brief: a creative-variants checklist
    (restructured from BUDGET_MECHANICS's test_multiple_creatives_simultaneously
    doctrine) + kill/scale criteria (BUDGET_MECHANICS's kill_fast and
    scale_only_what_already_works, verbatim) + a warm-audience inventory
    question set (derived from PLATFORM_SELECTION's warm_before_cold doctrine)
    + a budget section that is ALWAYS an [ARTIST-SUPPLIED:budget] marker,
    never a figure."""
    missing: list = []
    notes: list = []
    sections: list = []

    test_rec = digital_marketing_data.BUDGET_MECHANICS["test_multiple_creatives_simultaneously"]
    sections.append({
        "key": "creative_variants_checklist",
        "heading": _heading("Creative-variants checklist"),
        "items": list(_CREATIVE_VARIANTS_CHECKLIST),
        "source": test_rec["description"],
    })

    kill_rec = digital_marketing_data.BUDGET_MECHANICS["kill_fast"]
    scale_rec = digital_marketing_data.BUDGET_MECHANICS["scale_only_what_already_works"]
    sections.append({
        "key": "kill_scale_criteria",
        "heading": _heading("Kill / scale criteria"),
        "kill_fast": kill_rec["description"],
        "scale_only_what_already_works": scale_rec["description"],
    })

    warm_rec = digital_marketing_data.PLATFORM_SELECTION["warm_before_cold"]
    sections.append({
        "key": "warm_audience_inventory",
        "heading": _heading("Warm-audience inventory — questions, never assumed"),
        "questions": list(_WARM_AUDIENCE_INVENTORY_QUESTIONS),
        "source": warm_rec["description"],
    })

    sections.append(_budget_out_of_scope_section())

    return _finish(_header("Ad test brief"), "ad_test_brief", sections, missing, notes)


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
