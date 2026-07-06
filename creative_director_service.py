"""
PLMKR Creative-Director — creative-direction action service (mock-first).

Backs the Creative-Director (Cree — Creative Director) agent's tool_use loop in
/api/chat_stream (see CREATIVE_DIRECTOR_TOOLS in main.py). Cree does not just
advise on aesthetics — these functions let the agent take real creative-direction
actions: search the library of proven release-rollout campaign templates (single,
EP, album) by release type and creative goal, assess how ready a specific creative
concept is against a chosen template's aesthetic, timing, and asset requirements,
and schedule that rollout on the artist's behalf through their connected creative
studio / content-calendar account.

Unit 3: build_copy_scaffold is a DATA tool (Jade-U4 / Reed-U3 / Nadia-U3
pattern, option B) — it returns compact ingredients (sections ordered per the
relevant copy_data spec, [NEEDS:<fact>] gaps, [ARTIST-SUPPLIED: ...]
reminders); Cree writes the prose in his own turn. No model call here — this
module imports no LLM SDK. THE HARD RULE OF THIS DOMAIN rides through every
branch: no fact, stat, press quote, or comparison is ever invented — every
slot is the supplied input verbatim, a [NEEDS:<fact>] gap, or an
[ARTIST-SUPPLIED: ...] reminder. A press-release quote missing its source is
withheld from the quote slot entirely ([NEEDS:quote_source] — never included
unattributed); a one-sheet with an empty stats block surfaces the
skip-unimpressive-stats doctrine as a structural choice OFFERED to the artist,
never a silent edit.

Unit 2: lookup_copy_conventions is a pure read over the copy_data corpus (Cree
Unit 1) — the corpus is the single source of truth; no domain fact is invented
here (and the corpus itself contains no artist facts at all — copy conventions
are structural doctrine). Every doc type's result carries its spec, its
conventions/doctrine, and the full honesty-rule set (all five rules apply to
every copy document — this domain is made of facts, and no fact, stat, quote,
or comparison is ever invented: HONESTY_RULES.facts_supplied_or_marked).
bio_long's word range surfaces its open upper bound honestly — (500, None),
never a guessed ceiling. An unknown doc_type returns a structured error
listing the supported types.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live content calendars, no publishing tools, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_creative_studio_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring sync_agent_service._sync_catalogue_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os

import copy_data


class CreativeStudioNotConnected(Exception):
    """Raised when the artist has not connected a creative studio / content account.

    Mirrors sync_agent_service.SyncCatalogueNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your studio first'
    result instead of crashing the stream.
    """


class CreativeStudioAuthExpired(Exception):
    """Raised when a previously connected creative-studio authorization expired."""


# ── Rollout template library (in-memory reference data) ─────────────────────────
# A curated set of proven release-rollout campaign templates a creative director
# might reach for. Each template carries the release type (single / ep / album),
# the primary creative goal it serves, the aesthetic themes it suits, a
# recommended lead-time window (weeks before release), whether finished visual
# assets are required up front, and a headline phase count. The agent surfaces the
# right starting point for a project, then assesses a specific concept against a
# chosen template. No I/O.
_TEMPLATES = [
    {
        "id": "tpl-single-slow-burn",
        "title": "Single — Slow-Burn Teaser Rollout",
        "release_type": "single",
        "goal": "awareness",
        "themes": ["nostalgic", "intimate", "moody"],
        "lead_min": 3,
        "lead_max": 8,
        "visual_assets_required": False,
        "phases": 3,
    },
    {
        "id": "tpl-single-viral-hook",
        "title": "Single — Short-Form Viral Hook Push",
        "release_type": "single",
        "goal": "streams",
        "themes": ["bold", "playful", "energetic"],
        "lead_min": 2,
        "lead_max": 5,
        "visual_assets_required": True,
        "phases": 4,
    },
    {
        "id": "tpl-ep-story-arc",
        "title": "EP — Serialized Story-Arc Rollout",
        "release_type": "ep",
        "goal": "superfans",
        "themes": ["cinematic", "conceptual", "moody"],
        "lead_min": 6,
        "lead_max": 12,
        "visual_assets_required": True,
        "phases": 5,
    },
    {
        "id": "tpl-album-era-launch",
        "title": "Album — Full Era Launch Campaign",
        "release_type": "album",
        "goal": "press",
        "themes": ["bold", "cinematic", "conceptual"],
        "lead_min": 8,
        "lead_max": 16,
        "visual_assets_required": True,
        "phases": 6,
    },
    {
        "id": "tpl-album-intimate-reveal",
        "title": "Album — Intimate Direct-to-Fan Reveal",
        "release_type": "album",
        "goal": "superfans",
        "themes": ["intimate", "nostalgic", "acoustic"],
        "lead_min": 5,
        "lead_max": 10,
        "visual_assets_required": False,
        "phases": 4,
    },
    {
        "id": "tpl-single-brand-moment",
        "title": "Single — Brand / Cultural Moment Tie-In",
        "release_type": "single",
        "goal": "press",
        "themes": ["bold", "playful", "cinematic"],
        "lead_min": 4,
        "lead_max": 9,
        "visual_assets_required": True,
        "phases": 4,
    },
]


async def search_rollout_templates(release_type: str = "", goal: str = "") -> dict:
    """Search proven release-rollout templates by release type and/or creative goal.

    Both filters are optional and matched case-insensitively. ``release_type``
    matches the template's release type (e.g. "single", "ep", "album") as a
    substring; ``goal`` matches the template's primary creative goal (e.g.
    "awareness", "streams", "superfans", "press").
    Returns {"templates": [...], "count": int}. Pure — no I/O.
    """
    rt = (release_type or "").strip().lower()
    gl = (goal or "").strip().lower()
    matches = [
        dict(t)
        for t in _TEMPLATES
        if (not rt or rt in t["release_type"].lower())
        and (not gl or gl in t["goal"].lower())
    ]
    return {"templates": matches, "count": len(matches)}


def _get_template(template_id: str) -> dict | None:
    tid = (template_id or "").strip()
    for t in _TEMPLATES:
        if t["id"] == tid:
            return t
    return None


async def assess_creative_concept(
    artist_id: str,
    template_id: str = "",
    release_title: str = "",
    theme: str = "",
    weeks_to_release: float = 0,
    has_visual_assets: bool = False,
) -> dict:
    """Assess how ready a specific creative concept is against a chosen template.

    Deterministic readiness assessment — never contacts a wire. Looks the template
    up by id, then scores the concept against the template's aesthetic themes,
    recommended lead-time window, and visual-asset requirement. Each satisfied
    criterion adds to a readiness score out of 100. Returns a structured
    assessment with matched/missing criteria, the score, and a recommendation of
    "proceed" / "adjust" / "blocked".
    """
    template = _get_template(template_id)

    try:
        weeks = round(float(weeks_to_release or 0), 1)
    except (TypeError, ValueError):
        weeks = 0.0

    gaps = []
    if not (release_title or "").strip():
        gaps.append("missing_release_title")
    if not (template_id or "").strip():
        gaps.append("missing_template")
    elif template is None:
        gaps.append("unknown_template")

    matched = []
    missing = []
    score = 0
    if template is not None:
        th = (theme or "").strip().lower()
        if th and any(th in t.lower() or t.lower() in th for t in template["themes"]):
            matched.append("theme")
            score += 40
        else:
            missing.append("theme")

        if weeks > 0 and template["lead_min"] <= weeks <= template["lead_max"]:
            matched.append("timing")
            score += 35
        else:
            missing.append("timing")

        if not template["visual_assets_required"] or has_visual_assets:
            matched.append("visual_assets")
            score += 25
        else:
            missing.append("visual_assets")

    if "unknown_template" in gaps or "missing_template" in gaps:
        # Without a valid template target the concept cannot be assessed at all.
        recommendation = "blocked"
    elif gaps or score < 60:
        recommendation = "adjust"
    else:
        recommendation = "proceed"
    ready = recommendation == "proceed"

    return {
        "ready": ready,
        "gaps": gaps,
        "template_id": template["id"] if template else (template_id or "").strip(),
        "template_title": template["title"] if template else None,
        "release_title": (release_title or "").strip(),
        "score": score,
        "matched": matched,
        "missing": missing,
        "recommendation": recommendation,
    }


# ── Unit-2 plumbing (pure; corpus-driven) ─────────────────────────────────────

async def lookup_copy_conventions(doc_type: str = "") -> dict:
    """Look up the conventions for one copy document type — pure corpus read.

    Returns the relevant spec (structure/word ranges/ordered sections), the
    conventions or doctrine that govern it, and the FULL honesty-rule set —
    all five rules apply to every copy document; this domain is made of facts
    and no fact, stat, quote, or comparison is ever invented
    (HONESTY_RULES.facts_supplied_or_marked). bio_long's word range carries
    its open upper bound honestly — (500, None), never a guessed ceiling. An
    unknown doc_type returns a structured ``unknown_doc_type`` error listing
    the supported types. No I/O, no LLM, nothing invented here.
    """
    dt = (doc_type or "").strip().lower()
    honesty_rules = [dict(r) for r in copy_data.HONESTY_RULES]

    if dt in copy_data.BIO_SPECS:
        return {
            "status": "ok",
            "doc_type": dt,
            "spec": dict(copy_data.BIO_SPECS[dt]),
            "conventions": [dict(c) for c in copy_data.BIO_CONVENTIONS.values()],
            "honesty_rules": honesty_rules,
        }
    if dt == "press_release":
        return {
            "status": "ok",
            "doc_type": dt,
            "spec": {"sections": [dict(s) for s in
                                  copy_data.PRESS_RELEASE_SPEC["sections"]]},
            "conventions": [dict(c) for c in
                            copy_data.PRESS_RELEASE_SPEC["conventions"]],
            "honesty_rules": honesty_rules,
        }
    if dt == "one_sheet":
        return {
            "status": "ok",
            "doc_type": dt,
            "spec": {"elements": [dict(e) for e in
                                  copy_data.ONE_SHEET_SPEC["elements"]]},
            "conventions": [dict(d) for d in copy_data.ONE_SHEET_SPEC["doctrine"]],
            "honesty_rules": honesty_rules,
        }
    if dt == "epk_outline":
        return {
            "status": "ok",
            "doc_type": dt,
            "spec": {"core_components": [dict(c) for c in
                                         copy_data.EPK_OUTLINE_SPEC["core_components"]],
                     "optional_components": [dict(c) for c in
                                             copy_data.EPK_OUTLINE_SPEC["optional_components"]]},
            "conventions": [dict(d) for d in copy_data.EPK_OUTLINE_SPEC["doctrine"]],
            "honesty_rules": honesty_rules,
        }
    if dt == "caption_set":
        return {
            "status": "ok",
            "doc_type": dt,
            "spec": {"elements": [dict(e) for e in
                                  copy_data.CAPTION_SET_SPEC["elements"]]},
            "conventions": [dict(r) for r in copy_data.CAPTION_SET_SPEC["rules"]],
            "honesty_rules": honesty_rules,
        }
    return {
        "status": "unknown_doc_type",
        "doc_type": dt or "(missing)",
        "supported_doc_types": list(copy_data.COPY_DOC_TYPES),
        "message": ("Unsupported doc_type. Supported: "
                    + ", ".join(copy_data.COPY_DOC_TYPES) + "."),
    }


# ── Unit-3 copy-scaffold plumbing (data only; Cree writes the prose) ───────────

_DRAFT_NOT_PUBLISH_READY_NOTE = (
    "Scaffold only — write the draft yourself from these ingredients. The draft "
    "is for the artist's REVIEW — never publish-ready, never sent or posted on "
    "your say-so. Keep every [NEEDS:...] and [ARTIST-SUPPLIED: ...] marker "
    "verbatim and NEVER invent a fact, stat, press quote, comparison, or "
    "milestone — every fact is the artist's supplied input verbatim or an "
    "explicit gap."
)

_GAP = "[NEEDS:{}]"

# The ingredient slots each bio length expects. These are STRUCTURAL prompts
# for what a bio of that length conventionally covers (copy_data
# BIO_SPECS.content_expectations as slots) — they enforce nothing about the
# prose Cree writes; an unsupplied slot is a [NEEDS:<slot>] gap, never filled.
_BIO_FACT_SLOTS = {
    "bio_short":  ("artist_name", "genre_or_sound", "distinctive_hook"),
    "bio_medium": ("artist_name", "hometown_or_scene", "genre_or_sound",
                   "distinctive_hook", "current_project", "achievements"),
    "bio_long":   ("artist_name", "hometown_or_scene", "genre_or_sound",
                   "distinctive_hook", "origin_story", "current_project",
                   "achievements", "artistic_direction"),
}


def _missing_input(inputs: dict, field: str) -> bool:
    """A field is missing when absent, None, or an empty/whitespace string."""
    value = inputs.get(field)
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _slot(inputs: dict, field: str, missing: list):
    """The three-way mapping for one fact slot: supplied verbatim or a gap."""
    if _missing_input(inputs, field):
        gap = _GAP.format(field)
        missing.append(gap)
        return gap
    return inputs[field]


def _finish_scaffold(result: dict, inputs: dict, consumed: set) -> dict:
    """Dedup gaps and let unmapped inputs ride along verbatim — never dropped."""
    result["missing"] = list(dict.fromkeys(result["missing"]))
    unmapped = {k: v for k, v in inputs.items() if k not in consumed}
    if unmapped:
        result["unmapped_inputs"] = unmapped
    return result


async def build_copy_scaffold(doc_type: str = "", inputs: dict = None) -> dict:
    """Build compact ingredients for one copy document; Cree writes the prose.

    DATA/SCAFFOLD tool — no model call, no prose, no I/O (Jade-U4 / Reed-U3 /
    Nadia-U3 pattern; this module imports no LLM SDK). Sections are ordered
    per the relevant copy_data spec, and every fact slot is exactly one of:
    the supplied input VERBATIM, a [NEEDS:<fact>] gap (aggregated into
    missing[]), or an [ARTIST-SUPPLIED: ...] reminder — nothing is ever
    invented (HONESTY_RULES.facts_supplied_or_marked). Branch specifics:
    bios carry word_range + conventions as reminders and enforce nothing
    about the prose; a press-release quote missing its source becomes
    [NEEDS:quote_source] and the quote is WITHHELD from the quote slot; a
    one-sheet with an empty stats block surfaces skip_unimpressive_stats as
    an OFFERED structural choice, never a silent edit; captions carry the
    no-invented-urgency rule. Unknown doc_type -> structured error.
    """
    dt = (doc_type or "").strip().lower()
    inputs = dict(inputs) if isinstance(inputs, dict) else {}
    if dt in _BIO_FACT_SLOTS:
        return _scaffold_bio(dt, inputs)
    if dt == "press_release":
        return _scaffold_press_release(inputs)
    if dt == "one_sheet":
        return _scaffold_one_sheet(inputs)
    if dt == "epk_outline":
        return _scaffold_epk_outline(inputs)
    if dt == "caption_set":
        return _scaffold_caption_set(inputs)
    return {
        "status": "unknown_doc_type",
        "doc_type": dt or "(missing)",
        "supported_doc_types": list(copy_data.COPY_DOC_TYPES),
        "message": ("Unsupported doc_type. Supported: "
                    + ", ".join(copy_data.COPY_DOC_TYPES) + "."),
    }


def _scaffold_bio(dt: str, inputs: dict) -> dict:
    """Bio ingredients — fact slots + word_range + conventions as reminders.

    Enforces NOTHING about the prose (Cree writes it); the word range and the
    shared bio conventions ride along as reminders. The optional press-quote
    opener follows the quote discipline: included ONLY with its source; a
    quote missing its source is withheld ([NEEDS:press_quote_source]).
    """
    spec = copy_data.BIO_SPECS[dt]
    missing, notes, sections = [], [], []

    for field in _BIO_FACT_SLOTS[dt]:
        sections.append({
            "key": field,
            "title": field.replace("_", " ").title(),
            "content_or_gap": _slot(inputs, field, missing),
        })

    # Optional press-quote opener — only ever real, verbatim, and attributed.
    if not _missing_input(inputs, "press_quote"):
        if _missing_input(inputs, "press_quote_source"):
            gap = _GAP.format("press_quote_source")
            missing.append(gap)
            notes.append({"source": "press_quote",
                          "note": ("a press quote was supplied WITHOUT its source — "
                                   "withheld from the scaffold until the source is "
                                   "supplied; a quote is never included unattributed "
                                   "and never synthesized")})
        else:
            sections.append({
                "key": "press_quote_opener",
                "title": "Press Quote Opener (optional)",
                "guidance": copy_data.BIO_CONVENTIONS[
                    "press_quote_opener_optional_only_if_real"]["text"],
                "content_or_gap": {"quote": inputs["press_quote"],
                                   "source": inputs["press_quote_source"]},
            })

    consumed = set(_BIO_FACT_SLOTS[dt]) | {"press_quote", "press_quote_source"}
    return _finish_scaffold({
        "status": "scaffold_ready",
        "doc_type": dt,
        "sections": sections,
        "missing": missing,
        "notes": notes,
        "reminders": {
            "word_range": list(spec["word_range"]),
            "content_expectations": spec["content_expectations"],
            "conventions": [dict(c) for c in copy_data.BIO_CONVENTIONS.values()],
        },
        "note": _DRAFT_NOT_PUBLISH_READY_NOTE,
    }, inputs, consumed)


def _scaffold_press_release(inputs: dict) -> dict:
    """Press-release ingredients — sections in the FIXED corpus order.

    REQUIRED discipline: a supplied quote missing its source becomes
    [NEEDS:quote_source] and the quote text is WITHHELD from the quote slot —
    a quote is never included unattributed and never synthesized.
    """
    spec_sections = {s["key"]: s for s in copy_data.PRESS_RELEASE_SPEC["sections"]}
    missing, notes, sections = [], [], []

    def _section(key, content):
        sections.append({
            "key": key,
            "title": spec_sections[key]["title"],
            "guidance": spec_sections[key]["guidance"],
            "content_or_gap": content,
        })

    # Quote slot for para_2 — included ONLY when real AND attributed.
    if not _missing_input(inputs, "quote"):
        if _missing_input(inputs, "quote_source"):
            quote_slot = _GAP.format("quote_source")
            missing.append(_GAP.format("quote_source"))
            notes.append({"source": "quote",
                          "note": ("a quote was supplied WITHOUT its source — "
                                   "withheld from the quote slot until the source "
                                   "is supplied; a quote is never included "
                                   "unattributed and never synthesized")})
        else:
            quote_slot = {"quote": inputs["quote"], "source": inputs["quote_source"]}
    else:
        quote_slot = None  # quotes are optional — only ever real and attributed

    _section("for_immediate_release_line", "FOR IMMEDIATE RELEASE")
    _section("headline", _slot(inputs, "headline", missing))
    _section("dateline", {"city": _slot(inputs, "city", missing),
                          "date": _slot(inputs, "date", missing)})
    _section("para_1_pitch", _slot(inputs, "news_item", missing))
    _section("para_2_supporting_context",
             {"supporting_context": _slot(inputs, "supporting_context", missing),
              "quote": quote_slot})
    _section("para_3_short_bio", _slot(inputs, "short_bio", missing))
    _section("boilerplate", _slot(inputs, "boilerplate", missing))
    _section("contact", {"name": _slot(inputs, "contact_name", missing),
                         "role": _slot(inputs, "contact_role", missing),
                         "email": _slot(inputs, "contact_email", missing)})
    _section("links", {"music": _slot(inputs, "music_link", missing),
                       "press_photos": _slot(inputs, "press_photos_link", missing)})

    consumed = {"headline", "city", "date", "news_item", "supporting_context",
                "quote", "quote_source", "short_bio", "boilerplate",
                "contact_name", "contact_role", "contact_email", "music_link",
                "press_photos_link"}
    return _finish_scaffold({
        "status": "scaffold_ready",
        "doc_type": "press_release",
        "sections": sections,
        "missing": missing,
        "notes": notes,
        "reminders": {
            "conventions": [dict(c) for c in
                            copy_data.PRESS_RELEASE_SPEC["conventions"]],
        },
        "note": _DRAFT_NOT_PUBLISH_READY_NOTE,
    }, inputs, consumed)


def _scaffold_one_sheet(inputs: dict) -> dict:
    """One-sheet ingredients — elements in the corpus order.

    REQUIRED discipline: supplied stats pass through VERBATIM; an empty stats
    block surfaces skip_unimpressive_stats as a structural choice OFFERED to
    the artist — the element is never silently dropped and the choice is
    never auto-decided.
    """
    spec_elements = {e["key"]: e for e in copy_data.ONE_SHEET_SPEC["elements"]}
    skip_doctrine = next(d for d in copy_data.ONE_SHEET_SPEC["doctrine"]
                         if d["id"] == "skip_unimpressive_stats")
    missing, artist_supplied_reminders, sections = [], [], []
    offered_choices = []

    def _element(key, content, extra=None):
        record = {
            "key": key,
            "title": spec_elements[key]["title"],
            "guidance": spec_elements[key]["guidance"],
            "content_or_gap": content,
        }
        if extra:
            record.update(extra)
        sections.append(record)

    _element("artist_name_prominent", _slot(inputs, "artist_name", missing))
    _element("genre_2_to_3_words", _slot(inputs, "genre", missing))
    _element("press_photo_slot", _slot(inputs, "press_photo_link", missing))
    _element("short_bio", _slot(inputs, "short_bio", missing))

    # Stats: verbatim pass-through, or the OFFERED skip choice — never decided.
    if not _missing_input(inputs, "stats"):
        _element("highlights_stats_block", inputs["stats"])
    else:
        _element("highlights_stats_block", _slot(inputs, "stats", missing),
                 extra={"offered_choice": dict(skip_doctrine)})
        offered_choices.append(dict(skip_doctrine))

    if not _missing_input(inputs, "press_quotes"):
        _element("press_quotes_with_citation", inputs["press_quotes"])
    else:
        reminder = ("[ARTIST-SUPPLIED: press_quotes_with_citation — include only "
                    "real quotes verbatim with their citation, or omit the block; "
                    "a quote is never synthesized]")
        artist_supplied_reminders.append(reminder)
        _element("press_quotes_with_citation", reminder)

    release_fields = ("release_title", "release_date", "release_one_sentence")
    if any(not _missing_input(inputs, f) for f in release_fields):
        _element("release_block_optional",
                 {"title": _slot(inputs, "release_title", missing),
                  "date": _slot(inputs, "release_date", missing),
                  "one_sentence": _slot(inputs, "release_one_sentence", missing)})
    else:
        reminder = ("[ARTIST-SUPPLIED: release_block_optional — optional block; "
                    "confirm whether there is a current release to feature]")
        artist_supplied_reminders.append(reminder)
        _element("release_block_optional", reminder)

    _element("social_streaming_links", _slot(inputs, "social_streaming_links", missing))
    _element("contact_with_role", {"name": _slot(inputs, "contact_name", missing),
                                   "role": _slot(inputs, "contact_role", missing)})

    consumed = {"artist_name", "genre", "press_photo_link", "short_bio", "stats",
                "press_quotes", "release_title", "release_date",
                "release_one_sentence", "social_streaming_links", "contact_name",
                "contact_role"}
    return _finish_scaffold({
        "status": "scaffold_ready",
        "doc_type": "one_sheet",
        "sections": sections,
        "missing": missing,
        "artist_supplied_reminders": artist_supplied_reminders,
        "offered_choices": offered_choices,
        "reminders": {
            "doctrine": [dict(d) for d in copy_data.ONE_SHEET_SPEC["doctrine"]],
        },
        "note": _DRAFT_NOT_PUBLISH_READY_NOTE,
    }, inputs, consumed)


def _scaffold_epk_outline(inputs: dict) -> dict:
    """EPK ingredients — core components as ordered sections; optional
    components included ONLY when supplied, and listed as not-included
    otherwise so nothing disappears silently."""
    core = copy_data.EPK_OUTLINE_SPEC["core_components"]
    optional = copy_data.EPK_OUTLINE_SPEC["optional_components"]
    missing, sections = [], []

    core_field_map = {
        "bio_all_lengths": None,  # composite of the three bio ids
        "artist_brief_3_to_5_sentences": "artist_brief",
        "promo_photos_list": "promo_photos",
        "music_3_to_5_tracks": "tracks",
        "video": "video_links",
        "press_and_reviews": "press_and_reviews",
        "highlights": "highlights",
        "social_streaming_links": "social_streaming_links",
        "contact": "contact",
    }
    for component in core:
        key = component["key"]
        if key == "bio_all_lengths":
            content = {bio_id: _slot(inputs, bio_id, missing)
                       for bio_id in copy_data.BIO_SPECS}
        else:
            content = _slot(inputs, core_field_map[key], missing)
        sections.append({
            "key": key,
            "title": component["title"],
            "guidance": component["guidance"],
            "content_or_gap": content,
        })

    optional_not_included = []
    for component in optional:
        key = component["key"]
        if not _missing_input(inputs, key):
            sections.append({
                "key": key,
                "title": component["title"],
                "guidance": component["guidance"],
                "content_or_gap": inputs[key],
            })
        else:
            optional_not_included.append({
                "key": key,
                "title": component["title"],
                "note": "optional component — not supplied, so not included; "
                        "offer it to the artist rather than inventing content",
            })

    consumed = (set(copy_data.BIO_SPECS)
                | {f for f in core_field_map.values() if f}
                | {c["key"] for c in optional})
    return _finish_scaffold({
        "status": "scaffold_ready",
        "doc_type": "epk_outline",
        "sections": sections,
        "missing": missing,
        "optional_components_not_included": optional_not_included,
        "reminders": {
            "doctrine": [dict(d) for d in copy_data.EPK_OUTLINE_SPEC["doctrine"]],
        },
        "note": _DRAFT_NOT_PUBLISH_READY_NOTE,
    }, inputs, consumed)


def _scaffold_caption_set(inputs: dict) -> dict:
    """Caption ingredients — elements per spec, carrying the
    no-invented-urgency-or-milestones rule as a reminder."""
    missing, sections = [], []
    for element in copy_data.CAPTION_SET_SPEC["elements"]:
        key = element["key"]
        sections.append({
            "key": key,
            "title": element["title"],
            "guidance": element["guidance"],
            "content_or_gap": _slot(inputs, key, missing),
        })
    consumed = {e["key"] for e in copy_data.CAPTION_SET_SPEC["elements"]}
    return _finish_scaffold({
        "status": "scaffold_ready",
        "doc_type": "caption_set",
        "sections": sections,
        "missing": missing,
        "reminders": {
            "rules": [dict(r) for r in copy_data.CAPTION_SET_SPEC["rules"]],
        },
        "note": _DRAFT_NOT_PUBLISH_READY_NOTE,
    }, inputs, consumed)


def _creative_studio_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's creative studio / content account.

    In production this would look up a stored creative-studio / content-calendar
    link for the artist. Here it is driven purely by the
    ``CREATIVE_DIRECTOR_STUDIO_CONNECTED`` env flag so tests can toggle connected /
    expired / not-connected with ZERO network calls and NO real secret. Values:
      - "expired"                     → raise CreativeStudioAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("CREATIVE_DIRECTOR_STUDIO_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise CreativeStudioAuthExpired("creative-studio authorization expired")
    return val in ("1", "true", "yes", "connected")


async def schedule_rollout(
    artist_id: str,
    template_id: str,
    release_title: str,
    kickoff: str = "",
) -> dict:
    """Schedule a release rollout for the artist against a chosen template.

    Raises CreativeStudioNotConnected / CreativeStudioAuthExpired when no creative
    studio is linked so the caller can surface a 'connect your studio' message
    instead of a hard failure. On success returns a deterministic mock rollout
    reference — NO network call is ever made and nothing is actually scheduled.
    """
    if not _creative_studio_connected(artist_id):
        raise CreativeStudioNotConnected(
            "artist has not connected a creative studio / content account"
        )
    tid   = (template_id or "").strip()
    title = (release_title or "").strip()
    kick  = (kickoff or "").strip()
    digest = hashlib.sha1(f"{artist_id}:{tid}:{title}".encode("utf-8")).hexdigest()
    reference = "ROLLOUT-" + digest[:10].upper()
    return {
        "status": "scheduled",
        "reference": reference,
        "template_id": tid,
        "release_title": title,
        "kickoff": kick,
    }
