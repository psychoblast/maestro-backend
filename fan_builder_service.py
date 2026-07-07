"""
PLMKR Fan-Builder (Aria) — fan-engagement DOC-WRITER service (mock-first,
Option B).

Backs the Fan-Builder (Aria — Fan Engagement) agent's tool_use loop in
/api/chat_stream (see FAN_BUILDER_TOOLS in main.py). Aria does not just
advise on community building — these functions let the agent take one real
action: assemble organized preparation material from Aria's real
fan-engagement knowledge base — a structured lookup over the engagement
corpus, and compact doc-scaffold ingredients the agent turns into prose in
its own turn.

DOC-WRITER OPTION B (Cree / Nadia / Reed / Lex / Miles / Data precedent):
  build_engagement_doc_scaffold returns COMPACT ingredients only — matched
  doctrine, checklists, questions, aggregated gaps. The AGENT writes the
  prose in its turn. There is ZERO model-call in this module (no Anthropic
  SDK import, no create-message call) — AST-enforced by tests.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live fan-CRM/email/SMS/Discord rails, no LLM.
  - NO secrets are read or embedded, and there is NO connection gate: both
    tools are pure corpus-read / data-scaffold tools that need no connected
    account (the old fan-platform/CRM connection gate and its broadcast-
    scheduling action are RETIRED; actually sending a message is not
    something Aria does — that infrastructure does not exist yet, per
    engagement_data.BOUNDARIES).
  - Deterministic: no timestamps or random values leak into return payloads,
    so tests can assert on exact structure.

HARD RULES honored here (mirroring engagement_data.py's doctrine):
  - depth_over_scale / superfans_first / owned_over_rented: Aria's standing
    framing rides through on every scaffold header, verbatim from the corpus.
  - never_simulates_sending: Aria drafts copy, cadence, and audience
    strategy. Nothing in this module ever claims a message was sent,
    delivered, or scheduled — there is no send action here at all.
  - BOUNDARIES: post scheduling/execution belongs to grid-prophet; monetizing
    the fanbase belongs to mobile-monetize; Aria never presents her own work
    as either.
  - NEVER fabricate: every artist-fact slot is the supplied input VERBATIM, a
    [NEEDS:<x>] gap, or an [ARTIST-SUPPLIED:<x>] marker — never invented.
    Corpus content (doctrine, tiers, practices) is pulled verbatim from
    engagement_data.
"""
import engagement_data


# ── Framing + gap markers (data, not logic) ───────────────────────────────────
_GAP = "[NEEDS:{}]"
_ARTIST_SUPPLIED = "[ARTIST-SUPPLIED:{}]"

# The two scaffolds this DOC-WRITER produces.
DOC_TYPES = ("engagement_plan", "superfan_program_outline")

# Standing framing surfaced on every scaffold header — pulled verbatim from
# the corpus so no output can be read as a scheduling tool, a monetization
# tool, or a live sender.
_DEPTH_OVER_SCALE        = engagement_data.ARIA_DOCTRINE["depth_over_scale"]
_SUPERFANS_FIRST         = engagement_data.ARIA_DOCTRINE["superfans_first"]
_OWNED_OVER_RENTED       = engagement_data.ARIA_DOCTRINE["owned_over_rented"]
_NEVER_SIMULATES_SENDING = engagement_data.ARIA_DOCTRINE["never_simulates_sending"]

# Access-perk types Aria's doctrine names, derived from
# SUPERFAN_IDENTIFICATION's private_small_group_access_nurture_pattern
# description ("early listens ahead of public release, a vote on an upcoming
# decision, or beta/early access to new merch"). Not corpus content itself —
# a restructuring of that record's own prose into addressable perk-type keys,
# exactly like Miles's advance-package checklist restructures ADVANCING_
# DOCTRINE's own prose into list form.
_SUPERFAN_PERK_TYPES = ("early_listens", "decision_votes", "beta_merch")

# Funnel-stage / fan-tier assessment questions for an engagement plan —
# QUESTIONS only, never a doctrine restatement. Derived from FAN_FUNNEL's own
# stages and tiers, not corpus content itself — mirrors how Miles's
# _SETTLEMENT_WALK_THE_NUMBERS_QUESTIONS lives in the service, not the corpus.
_ENGAGEMENT_PLAN_ASSESSMENT_QUESTIONS = [
    "What share of the current audience is realistically still at the "
    "discovery stage versus already returning, recognizable listeners?",
    "What light-touch, consistent content is already in place to move a "
    "listener from discovery into interest?",
    "Where does genuine two-way engagement — a real reply, not a template — "
    "already happen, and where is it missing?",
    "Which fans have moved from casual into true-fan behavior over the last "
    "release cycle, and how was that recognized?",
    "What privileged access or recognition is currently offered to fans "
    "already showing advocacy behavior?",
    "How is the artist currently identifying superfans, if at all, before "
    "this plan?",
    "What would it take to give superfans meaningfully more attention than "
    "the rest of the audience, given the artist's actual time and resources?",
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
# lookup_engagement_doctrine — structured lookup/filter over the
# engagement_data corpus. Pure corpus read; NOT gated. No judgment is made
# about the artist's own fanbase — this returns the standing doctrine the
# agent applies.
# ═══════════════════════════════════════════════════════════════════════════════
async def lookup_engagement_doctrine(
    funnel_key: str = "",
    principle_key: str = "",
    signal_key: str = "",
    channel_key: str = "",
    cadence_key: str = "",
    waste_key: str = "",
) -> dict:
    """Filter the engagement corpus by any of funnel key / true-fans-principle
    key / superfan-signal key / owned-channel key / cadence key / time-waste key.

    With NO filter, returns a compact index of the available keys per block so
    the agent can browse. With filters, returns the matched full records; any
    filter that matches nothing is recorded in ``not_found`` (value stays None,
    never guessed). Standing framing (Aria's own doctrine + the boundaries to
    grid-prophet / mobile-monetize / the not-yet-built send infrastructure)
    rides through on every response. Pure — no I/O, no gate.
    """
    fk  = _norm(funnel_key)
    pk  = _norm(principle_key)
    sk  = _norm(signal_key)
    ck  = _norm(channel_key)
    cdk = _norm(cadence_key)
    wk  = _norm(waste_key)
    any_filter = bool(fk or pk or sk or ck or cdk or wk)

    result = {
        "status": "ok",
        "aria_doctrine": dict(engagement_data.ARIA_DOCTRINE),
        "boundaries": [dict(b) for b in engagement_data.BOUNDARIES.values()],
    }

    if not any_filter:
        # Browse mode — index of keys only, kept compact.
        result["mode"] = "index"
        result["funnel_keys"] = list(engagement_data.FAN_FUNNEL)
        result["principle_keys"] = list(engagement_data.THOUSAND_TRUE_FANS)
        result["signal_keys"] = list(engagement_data.SUPERFAN_IDENTIFICATION)
        result["channel_keys"] = list(engagement_data.OWNED_CHANNELS)
        result["cadence_keys"] = list(engagement_data.CADENCE_SPEC)
        result["waste_keys"] = list(engagement_data.WHAT_WASTES_TIME)
        return result

    result["mode"] = "filtered"
    not_found = []

    result["funnel"] = []
    if fk:
        rec = engagement_data.FAN_FUNNEL.get(fk)
        if rec:
            result["funnel"].append(dict(rec))
        else:
            not_found.append({"filter": "funnel_key", "value": fk, "match": None})

    result["principles"] = []
    if pk:
        rec = engagement_data.THOUSAND_TRUE_FANS.get(pk)
        if rec:
            result["principles"].append(dict(rec))
        else:
            not_found.append({"filter": "principle_key", "value": pk, "match": None})

    result["signals"] = []
    if sk:
        rec = engagement_data.SUPERFAN_IDENTIFICATION.get(sk)
        if rec:
            result["signals"].append(dict(rec))
        else:
            not_found.append({"filter": "signal_key", "value": sk, "match": None})

    result["channels"] = []
    if ck:
        rec = engagement_data.OWNED_CHANNELS.get(ck)
        if rec:
            result["channels"].append(dict(rec))
        else:
            not_found.append({"filter": "channel_key", "value": ck, "match": None})

    result["cadence"] = []
    if cdk:
        rec = engagement_data.CADENCE_SPEC.get(cdk)
        if rec:
            result["cadence"].append(dict(rec))
        else:
            not_found.append({"filter": "cadence_key", "value": cdk, "match": None})

    result["waste"] = []
    if wk:
        rec = engagement_data.WHAT_WASTES_TIME.get(wk)
        if rec:
            result["waste"].append(dict(rec))
        else:
            not_found.append({"filter": "waste_key", "value": wk, "match": None})

    result["not_found"] = not_found
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# build_engagement_doc_scaffold — OPTION B: compact ingredients only, agent
# writes prose. NOT gated. Aria never claims to have sent anything.
# ═══════════════════════════════════════════════════════════════════════════════
async def build_engagement_doc_scaffold(doc_type: str = "", inputs: dict = None) -> dict:
    """Build compact ingredients for one fan-engagement document; Aria writes
    the prose.

    Two doc types — ``engagement_plan`` and ``superfan_program_outline``.
    Every scaffold header carries Aria's standing doctrine (depth over scale,
    superfans first, owned over rented, never simulates sending). No corpus
    content is a judgment about the artist's specific fanbase — the
    assessment questions, cadence spec, and tier structure are the standing
    engagement toolkit the agent applies. Every artist-fact slot is verbatim,
    a [NEEDS:<x>] gap, or an [ARTIST-SUPPLIED:<x>] marker; all such markers
    aggregate into ``missing``. Unknown doc_type -> structured error listing
    the supported types.
    """
    dt = _norm(doc_type).lower()
    inputs = dict(inputs) if isinstance(inputs, dict) else {}
    if dt == "engagement_plan":
        return _scaffold_engagement_plan(inputs)
    if dt == "superfan_program_outline":
        return _scaffold_superfan_program_outline(inputs)
    return {
        "status": "unknown_doc_type",
        "doc_type": dt or "(missing)",
        "supported_doc_types": list(DOC_TYPES),
        "message": ("Unsupported doc_type. Supported: " + ", ".join(DOC_TYPES) + "."),
    }


def _header(title: str) -> dict:
    """Scaffold header — carries Aria's standing doctrine verbatim from the
    corpus on every doc type."""
    return {
        "title": _heading(title),
        "depth_over_scale": _DEPTH_OVER_SCALE,
        "superfans_first": _SUPERFANS_FIRST,
        "owned_over_rented": _OWNED_OVER_RENTED,
        "never_simulates_sending": _NEVER_SIMULATES_SENDING,
    }


def _scaffold_engagement_plan(inputs: dict) -> dict:
    """Ingredients for an engagement plan: funnel-stage/tier assessment
    questions, a cadence plan (weekly + per-release-cycle, restated verbatim
    from CADENCE_SPEC, plus the artist's own current-practice restatement),
    and a superfan-nurture checklist. The artist's current weekly focus is
    ARTIST-SUPPLIED context — restated verbatim when given, a gap marker
    otherwise; never invented."""
    missing: list = []
    notes: list = []
    sections: list = []

    sections.append({
        "key": "funnel_stage_assessment_questions",
        "heading": _heading("Funnel-stage assessment questions"),
        "questions": list(_ENGAGEMENT_PLAN_ASSESSMENT_QUESTIONS),
    })

    weekly_rec    = engagement_data.CADENCE_SPEC["weekly_cadence"]
    per_cycle_rec = engagement_data.CADENCE_SPEC["per_release_cycle_cadence"]

    current_weekly_focus = inputs.get("current_weekly_focus")
    if _missing(current_weekly_focus):
        marker = _ARTIST_SUPPLIED.format("current_weekly_focus")
        missing.append(marker)
        focus_value = marker
    else:
        focus_value = current_weekly_focus  # verbatim

    sections.append({
        "key": "cadence_plan",
        "heading": _heading("Cadence plan"),
        "weekly_cadence": dict(weekly_rec),
        "per_release_cycle_cadence": dict(per_cycle_rec),
        "current_weekly_focus": focus_value,
    })

    track_rec   = engagement_data.SUPERFAN_IDENTIFICATION["track_and_recognize_practice"]
    nurture_rec = engagement_data.SUPERFAN_IDENTIFICATION["private_small_group_access_nurture_pattern"]
    sections.append({
        "key": "superfan_nurture_checklist",
        "heading": _heading("Superfan nurture checklist"),
        "items": [dict(track_rec), dict(nurture_rec)],
    })

    return _finish(_header("Engagement plan"), "engagement_plan", sections, missing, notes)


def _scaffold_superfan_program_outline(inputs: dict) -> dict:
    """Ingredients for a superfan program outline: FAN_FUNNEL's three tiers
    (casual, true_fan, superfan) restated verbatim as the tier structure, plus
    access-perk ingredients sourced from ``inputs["offerings"]``. Every perk
    type Aria's doctrine names (early_listens, decision_votes, beta_merch)
    that the artist did NOT supply becomes an [ARTIST-SUPPLIED:<perk_type>]
    marker; perks the artist DID supply ride through verbatim."""
    missing: list = []
    notes: list = []
    sections: list = []

    tiers = [dict(engagement_data.FAN_FUNNEL[k]) for k in ("casual", "true_fan", "superfan")]
    sections.append({
        "key": "tier_structure",
        "heading": _heading("Superfan program tier structure"),
        "tiers": tiers,
    })

    offerings = inputs.get("offerings")
    offerings = dict(offerings) if isinstance(offerings, dict) else {}
    perks_out = []
    for perk_type in _SUPERFAN_PERK_TYPES:
        value = offerings.get(perk_type)
        if _missing(value):
            marker = _ARTIST_SUPPLIED.format(perk_type)
            missing.append(marker)
            perks_out.append({"perk_type": perk_type, "value": marker})
        else:
            perks_out.append({"perk_type": perk_type, "value": value})  # verbatim

    sections.append({
        "key": "access_perks",
        "heading": _heading("Access perks — artist-supplied offerings"),
        "source_doctrine": engagement_data.SUPERFAN_IDENTIFICATION[
            "private_small_group_access_nurture_pattern"]["description"],
        "perks": perks_out,
    })

    return _finish(_header("Superfan program outline"), "superfan_program_outline",
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
