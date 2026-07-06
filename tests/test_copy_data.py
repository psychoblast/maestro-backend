"""
PROOF tests — copy_data (Cree Unit 1, corpus only).

Asserts the structured creative-copy conventions corpus faithfully encodes the
map: three bio specs with the correct word ranges (including bio_long's HONEST
open upper bound — (500, None), never guessed) plus the shared bio conventions;
the press-release spec with its FIXED section order and conventions; the
one-sheet ordered elements and doctrine (skip_unimpressive_stats encoded as a
structural choice OFFERED to the artist — never a silent edit); the EPK outline
core/optional components and doctrine; the caption-set elements with the
no-invented-urgency rule; and the section-F honesty rules with stable ids
(the three-way fact mapping: supplied verbatim / [NEEDS:<fact>] /
[ARTIST-SUPPLIED:<confirm>]) — plus the module-level guarantees: data-only
(no def/class/import/call), JSON-serializable throughout, entity-wall clean,
and the CREE-SPECIFIC hard rule that the corpus contains ZERO invented-looking
metrics: the only numeric leaves anywhere are the bio word-range bounds, and a
source scan finds no stat-shaped literal. No service or main.py wiring exists
yet; these tests import the data module directly.
"""
import ast
import json
import pathlib
import re

import copy_data as cd
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = (
    "COPY_DOC_TYPES", "BIO_SPECS", "BIO_CONVENTIONS", "PRESS_RELEASE_SPEC",
    "ONE_SHEET_SPEC", "EPK_OUTLINE_SPEC", "CAPTION_SET_SPEC", "HONESTY_RULES",
)

_SOURCE = pathlib.Path(cd.__file__).read_text(encoding="utf-8")


def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(cd, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(cd, name))  # raises TypeError on any leak


def test_module_is_data_only_no_def_class_or_import():
    tree = ast.parse(_SOURCE)
    for node in tree.body:
        assert isinstance(node, (ast.Expr, ast.Assign)), (
            f"non-data top-level node: {type(node).__name__}"
        )
        if isinstance(node, ast.Expr):
            assert isinstance(node.value, ast.Constant), "only the docstring may be an Expr"
    forbidden_nodes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                      ast.Import, ast.ImportFrom, ast.Call)
    for node in ast.walk(tree):
        assert not isinstance(node, forbidden_nodes), (
            f"forbidden node anywhere in module: {type(node).__name__}"
        )


def test_no_forbidden_entity_wall_terms_in_source():
    assert_no_forbidden_terms(_SOURCE)


# ── Vocabulary ─────────────────────────────────────────────────────────────────

def test_doc_type_vocabulary_is_the_seven_types():
    assert cd.COPY_DOC_TYPES == ("bio_short", "bio_medium", "bio_long",
                                 "press_release", "one_sheet", "epk_outline",
                                 "caption_set")


# ── Bio specs + conventions (section A) ────────────────────────────────────────

def test_three_bio_specs_with_correct_word_ranges():
    assert set(cd.BIO_SPECS) == {"bio_short", "bio_medium", "bio_long"}
    assert cd.BIO_SPECS["bio_short"]["word_range"] == (50, 100)
    assert cd.BIO_SPECS["bio_medium"]["word_range"] == (200, 300)
    for bid, spec in cd.BIO_SPECS.items():
        assert spec["id"] == bid
        assert len(spec["typical_uses"]) >= 1
        assert spec["content_expectations"]


def test_bio_long_upper_bound_is_honestly_open():
    # bio_long has NO upper bound — None, never a guessed ceiling.
    lower, upper = cd.BIO_SPECS["bio_long"]["word_range"]
    assert lower == 500
    assert upper is None, "an upper bound must never be guessed for bio_long"
    # bio_long is the ONLY open bound
    open_bounds = {bid for bid, spec in cd.BIO_SPECS.items()
                   if spec["word_range"][1] is None}
    assert open_bounds == {"bio_long"}


def test_bio_conventions_ids_stable():
    expected = {"third_person", "avoid_generic_cliches",
                "lead_with_distinctive_hook", "achievements_woven_not_listed",
                "press_quote_opener_optional_only_if_real",
                "every_fact_artist_supplied"}
    assert set(cd.BIO_CONVENTIONS) == expected
    for cid, conv in cd.BIO_CONVENTIONS.items():
        assert conv["id"] == cid
        assert conv["text"]
    assert "first person" in cd.BIO_CONVENTIONS["third_person"]["text"].lower()
    quote_conv = cd.BIO_CONVENTIONS["press_quote_opener_optional_only_if_real"]
    assert "never synthesized" in quote_conv["text"].lower()


# ── Press-release spec (section B) ─────────────────────────────────────────────

def test_press_release_section_order_fixed():
    assert [s["key"] for s in cd.PRESS_RELEASE_SPEC["sections"]] == [
        "for_immediate_release_line", "headline", "dateline", "para_1_pitch",
        "para_2_supporting_context", "para_3_short_bio", "boilerplate",
        "contact", "links",
    ]
    for section in cd.PRESS_RELEASE_SPEC["sections"]:
        assert section["title"] and section["guidance"]


def test_press_release_conventions_present():
    conv_ids = [c["id"] for c in cd.PRESS_RELEASE_SPEC["conventions"]]
    assert conv_ids == ["front_load_for_skimming",
                        "quotes_only_real_and_attributed",
                        "one_release_one_news_item"]
    quotes = next(c for c in cd.PRESS_RELEASE_SPEC["conventions"]
                  if c["id"] == "quotes_only_real_and_attributed")
    assert "verbatim" in quotes["text"].lower()
    assert "gap" in quotes["text"].lower()


def test_press_release_key_conventions_in_guidance():
    by_key = {s["key"]: s for s in cd.PRESS_RELEASE_SPEC["sections"]}
    # dateline is city + date, both supplied
    assert "city" in by_key["dateline"]["guidance"].lower()
    assert "date" in by_key["dateline"]["guidance"].lower()
    # para_1 is the news in one to two sentences
    assert "one to two sentences" in by_key["para_1_pitch"]["guidance"].lower()
    # contact carries name + role + email
    for token in ("name", "role", "email"):
        assert token in by_key["contact"]["guidance"].lower()
    # links: music + press photos, linked not attached
    assert "music" in by_key["links"]["guidance"].lower()
    assert "photo" in by_key["links"]["guidance"].lower()
    assert "not attachments" in by_key["links"]["guidance"].lower()


# ── One-sheet spec (section C) ─────────────────────────────────────────────────

def test_one_sheet_element_order_fixed():
    assert [e["key"] for e in cd.ONE_SHEET_SPEC["elements"]] == [
        "artist_name_prominent", "genre_2_to_3_words", "press_photo_slot",
        "short_bio", "highlights_stats_block", "press_quotes_with_citation",
        "release_block_optional", "social_streaming_links", "contact_with_role",
    ]
    release_block = next(e for e in cd.ONE_SHEET_SPEC["elements"]
                         if e["key"] == "release_block_optional")
    assert release_block["fields"] == ("title", "date", "one_sentence")


def test_one_sheet_doctrine_ids_stable():
    assert [d["id"] for d in cd.ONE_SHEET_SPEC["doctrine"]] == [
        "scannable_under_30_seconds", "skip_unimpressive_stats",
        "every_element_earns_its_place", "pdf_delivery_convention",
    ]


def test_skip_unimpressive_stats_is_offered_choice_not_silent_edit():
    # REQUIRED: the skip doctrine is a structural choice OFFERED to the artist
    # — never a silent edit. Encoded structurally, not just prose.
    skip = next(d for d in cd.ONE_SHEET_SPEC["doctrine"]
                if d["id"] == "skip_unimpressive_stats")
    assert skip["choice_type"] == "offered_to_artist"
    assert skip["never"] == "silent_edit"
    assert "offered" in skip["text"].lower()
    assert "silent" in skip["text"].lower()
    # and the stats element itself carries the verbatim + never-invented rule
    stats = next(e for e in cd.ONE_SHEET_SPEC["elements"]
                 if e["key"] == "highlights_stats_block")
    assert "verbatim" in stats["guidance"].lower()
    assert "never" in stats["guidance"].lower()


# ── EPK outline spec (section D) ───────────────────────────────────────────────

def test_epk_core_components():
    assert [c["key"] for c in cd.EPK_OUTLINE_SPEC["core_components"]] == [
        "bio_all_lengths", "artist_brief_3_to_5_sentences", "promo_photos_list",
        "music_3_to_5_tracks", "video", "press_and_reviews", "highlights",
        "social_streaming_links", "contact",
    ]
    bios = next(c for c in cd.EPK_OUTLINE_SPEC["core_components"]
                if c["key"] == "bio_all_lengths")
    for bio_id in cd.BIO_SPECS:
        assert bio_id in bios["guidance"]


def test_epk_optional_components_and_fact_sheet_fields():
    assert [c["key"] for c in cd.EPK_OUTLINE_SPEC["optional_components"]] == [
        "fact_sheet", "tour_dates", "artwork", "rider", "lyrics_liner_notes",
    ]
    fact_sheet = next(c for c in cd.EPK_OUTLINE_SPEC["optional_components"]
                      if c["key"] == "fact_sheet")
    assert fact_sheet["fields"] == ("location", "members", "genre", "key_points")


def test_epk_doctrine():
    assert [d["id"] for d in cd.EPK_OUTLINE_SPEC["doctrine"]] == [
        "decision_tool_not_scrapbook", "tailor_per_audience",
    ]
    tailor = next(d for d in cd.EPK_OUTLINE_SPEC["doctrine"]
                  if d["id"] == "tailor_per_audience")
    assert tailor["audiences"] == ("booking", "media", "radio")


# ── Caption-set spec (section E) ───────────────────────────────────────────────

def test_caption_set_elements_and_rule():
    assert [e["key"] for e in cd.CAPTION_SET_SPEC["elements"]] == [
        "hook_line", "context_line", "cta", "tag_link_placeholders",
    ]
    assert [r["id"] for r in cd.CAPTION_SET_SPEC["rules"]] == [
        "no_invented_urgency_or_milestones",
    ]
    rule = cd.CAPTION_SET_SPEC["rules"][0]
    assert "urgency" in rule["text"].lower()
    assert "supplied" in rule["text"].lower()


# ── Honesty rules (section F) ──────────────────────────────────────────────────

def test_honesty_rule_ids_stable():
    rule_ids = [r["id"] for r in cd.HONESTY_RULES]
    assert rule_ids == ["facts_supplied_or_marked",
                        "quotes_verbatim_with_source_or_omitted",
                        "stats_supplied_only", "comparisons_only_if_supplied",
                        "drafts_not_publish_ready"]
    for rule in cd.HONESTY_RULES:
        assert rule["statement"] and rule["allowed"] and rule["forbidden"]


def test_three_way_fact_mapping_encoded():
    facts = next(r for r in cd.HONESTY_RULES if r["id"] == "facts_supplied_or_marked")
    assert "VERBATIM" in facts["statement"]
    assert "[NEEDS:<fact>]" in facts["statement"]
    assert "[ARTIST-SUPPLIED:<confirm>]" in facts["statement"]
    assert "no fourth state" in facts["statement"].lower()


def test_quotes_rule_source_or_omitted():
    quotes = next(r for r in cd.HONESTY_RULES
                  if r["id"] == "quotes_verbatim_with_source_or_omitted")
    assert "verbatim" in quotes["statement"].lower()
    assert "never synthesized" in quotes["statement"].lower()
    assert "without its source" in quotes["forbidden"].lower()


def test_comparisons_rule_carries_convention_note():
    comparisons = next(r for r in cd.HONESTY_RULES
                       if r["id"] == "comparisons_only_if_supplied")
    assert comparisons["convention_note"], "the warning-against-comparisons note is required"
    assert "supplied" in comparisons["statement"].lower()


def test_drafts_not_publish_ready_rule():
    drafts = next(r for r in cd.HONESTY_RULES if r["id"] == "drafts_not_publish_ready")
    assert "DRAFT" in drafts["statement"]
    assert "publish-ready" in drafts["statement"].lower()


# ── CREE-SPECIFIC HARD RULE: zero invented-looking metrics in the corpus ───────

def test_only_numeric_leaves_are_bio_word_range_bounds():
    # The ONLY numeric values anywhere in the corpus are the bio word-range
    # bounds — a copy corpus with example stats would be a fabrication vector.
    def _numeric_leaves(value, path):
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            found.append((path, value))
        elif isinstance(value, dict):
            for k, v in value.items():
                _numeric_leaves(v, f"{path}.{k}")
        elif isinstance(value, (list, tuple)):
            for i, v in enumerate(value):
                _numeric_leaves(v, f"{path}[{i}]")

    found = []
    for name in _TOP_LEVEL_CONSTANTS:
        _numeric_leaves(getattr(cd, name), name)
    assert sorted(v for _, v in found) == [50, 100, 200, 300, 500], found
    for path, _ in found:
        assert ".word_range[" in path and path.startswith("BIO_SPECS."), (
            f"numeric value outside a bio word_range: {path}"
        )


def test_source_contains_no_stat_shaped_literals():
    # Scan the raw source for anything that could read as an invented metric:
    # comma-grouped figures, count abbreviations, digit+metric-noun pairs,
    # digit-percentages, and chart-position shapes. The corpus must be clean.
    stat_shapes = (
        r"\d{1,3}(?:,\d{3})+",                       # 1,000,000
        r"\d+(?:\.\d+)?\s*[MmKkBb]\+?\b",            # 1M / 10k / 2.5B
        r"\d+\s*(?:streams|followers|listeners|views|plays|sold|copies|fans)",
        r"\d\s*%",                                    # any digit-percentage
        r"#\s*\d+",                                   # chart positions
    )
    for shape in stat_shapes:
        matches = re.findall(shape, _SOURCE, flags=re.IGNORECASE)
        assert matches == [], f"stat-shaped literal(s) in corpus source: {matches}"
