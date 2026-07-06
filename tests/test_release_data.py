"""
PROOF tests — release_data (Tommy Unit 1, corpus only).

Asserts the structured release & delivery conventions corpus faithfully encodes
the map: the identifier doctrine (ISRC follows the recording and lives forever;
its new-vs-same rules complete; a distributor switch carries the SAME code; UPC
follows the container and is never recycled; ISWC follows the composition,
one-to-many with ISRCs; the duplicate doctrine); the ordered release- and
track-level metadata fields (artist_name EXACT-match doctrine; track_title is
the song name only); the artwork spec (labeled a current convention, verify
live); the work-backwards timeline (upload lead, Spotify editorial window, and
the split-sheet-BEFORE-upload cross-reference to ink-and-air); the permanent
release record; the ORDERED distributor-switch mechanism (export codes first,
remove old last); and the section-G honesty rules (never invent an identifier,
date, or credit; licensing routes elsewhere) — plus the module-level
guarantees: data-only (no def/class/import/call), JSON-serializable throughout,
entity-wall clean, and the TOMMY-SPECIFIC hard rule that the ONLY numeric leaf
anywhere is the artwork minimum dimension (3000) and no stat-shaped literal
appears in source. No service or main.py wiring exists yet; these tests import
the data module directly.
"""
import ast
import json
import pathlib
import re

import release_data as rd
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = (
    "IDENTIFIER_RULES", "METADATA_FIELDS", "ARTWORK_SPEC", "TIMELINE_DOCTRINE",
    "RELEASE_RECORD_SPEC", "DISTRIBUTOR_SWITCH_MECHANISM", "HONESTY_RULES",
)

_SOURCE = pathlib.Path(rd.__file__).read_text(encoding="utf-8")


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(rd, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(rd, name))  # raises TypeError on any leak


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


# ── Identifier doctrine (section A) ────────────────────────────────────────────

def test_isrc_follows_recording_and_is_permanent():
    isrc = rd.IDENTIFIER_RULES["isrc"]
    assert isrc["follows"] == "recording"
    assert isrc["permanence"] == "forever"


def test_isrc_new_when_rules_complete():
    new_when = rd.IDENTIFIER_RULES["isrc"]["new_when"]
    for trigger in ("remix", "radio_edit", "live", "acoustic", "clean_version",
                    "remaster_with_material_creative_change",
                    "own_cover_of_another_song"):
        assert trigger in new_when, f"missing ISRC new_when trigger: {trigger}"


def test_isrc_same_when_carries_code_on_switch_and_waterfall():
    isrc = rd.IDENTIFIER_RULES["isrc"]
    assert "distributor_switch" in isrc["same_when"]
    assert "identical_audio_on_new_release_waterfalling" in isrc["same_when"]
    note = isrc["same_when_note"].lower()
    assert "stream counts" in note
    assert "placement" in note
    assert "algorithmic" in note


def test_upc_follows_container_never_recycled():
    upc = rd.IDENTIFIER_RULES["upc"]
    assert upc["follows"] == "release_container"
    for trigger in ("any_configuration_change", "deluxe", "changed_tracklist"):
        assert trigger in upc["new_when"]
    assert "recycle" in upc["never"].lower()
    assert "twelve-digit" in upc["formats"].lower()
    assert "thirteen-digit" in upc["formats"].lower()


def test_iswc_follows_composition_one_to_many():
    iswc = rd.IDENTIFIER_RULES["iswc"]
    assert iswc["follows"] == "composition"
    assert "pro" in iswc["via"].lower()
    assert "many isrc" in iswc["note"].lower()


def test_duplicate_doctrine_blames_identifier_mismanagement():
    note = rd.IDENTIFIER_RULES["duplicate_doctrine"]["note"].lower()
    assert "isrc" in note and "upc" in note
    assert "mismanagement" in note


# ── Metadata fields (section B) ────────────────────────────────────────────────

def test_release_level_field_order_fixed():
    assert [f["field"] for f in rd.METADATA_FIELDS["release_level"]] == [
        "release_title", "artist_name", "upc", "release_date", "genre_subgenre",
        "label_name", "p_line", "c_line", "year", "territories",
    ]
    for rec in rd.METADATA_FIELDS["release_level"]:
        assert rec["note"]


def test_track_level_field_order_fixed():
    assert [f["field"] for f in rd.METADATA_FIELDS["track_level"]] == [
        "track_title", "version_field", "featured_artists", "isrc",
        "explicit_flag", "songwriter_credits", "producer_contributor_roles",
        "language", "lyrics_optional",
    ]
    for rec in rd.METADATA_FIELDS["track_level"]:
        assert rec["note"]


def test_artist_name_exact_match_doctrine_present():
    # REQUIRED: artist_name is byte-exact — "one character off" creates a dupe.
    name = next(f for f in rd.METADATA_FIELDS["release_level"]
                if f["field"] == "artist_name")
    assert "exact" in name["note"].lower()
    assert "one character off" in name["note"].lower()
    assert "verbatim" in name["note"].lower()


def test_track_title_song_name_only_version_and_features_split_out():
    title = next(f for f in rd.METADATA_FIELDS["track_level"]
                 if f["field"] == "track_title")
    assert "song name only" in title["note"].lower()
    assert "designated" in title["note"].lower()


def test_explicit_flag_when_in_doubt_and_clean_is_separate_isrc():
    flag = next(f for f in rd.METADATA_FIELDS["track_level"]
                if f["field"] == "explicit_flag")
    assert "when in doubt" in flag["note"].lower()
    assert "separate release" in flag["note"].lower()
    assert "own isrc" in flag["note"].lower()


def test_songwriter_credits_must_match_pro():
    credits = next(f for f in rd.METADATA_FIELDS["track_level"]
                   if f["field"] == "songwriter_credits")
    assert "pro" in credits["note"].lower()
    assert "royalt" in credits["note"].lower()


# ── Artwork spec (section C) ───────────────────────────────────────────────────

def test_artwork_spec_current_convention_and_verify():
    art = rd.ARTWORK_SPEC
    assert art["min_dimension_px"] == 3000
    assert art["color_mode"] == "RGB"
    assert set(art["formats"]) == {"JPG", "PNG"}
    assert art["labeled"] == "current_convention"
    assert "verify" in art["verify"].lower()
    assert len(art["prohibited"]) >= 3


# ── Timeline doctrine (section D) ──────────────────────────────────────────────

def test_upload_lead_and_editorial_windows():
    up = rd.TIMELINE_DOCTRINE["upload_to_distributor"]
    assert "four weeks" in up["lead"].lower()
    spotify = rd.TIMELINE_DOCTRINE["editorial_pitch"]["spotify"].lower()
    assert "seven days" in spotify
    assert "spotify for artists" in spotify


def test_split_sheet_before_upload_cross_ref_present():
    # REQUIRED: pre-release carries the split-sheet-BEFORE-upload item, and it
    # cross-references the ink-and-air split sheet tools (named, not resolved).
    assert "split_sheet_signed_before_upload" in rd.TIMELINE_DOCTRINE["pre_release"]
    xref = rd.TIMELINE_DOCTRINE["cross_refs"]["split_sheet_signed_before_upload"]
    assert "ink-and-air" in xref.lower()
    assert "before upload" in xref.lower()
    # the sync-pack cross-ref is present too
    assert "ink-and-air" in \
        rd.TIMELINE_DOCTRINE["cross_refs"]["stems_archived_for_sync"].lower()


def test_pre_and_post_release_ordered_items():
    assert rd.TIMELINE_DOCTRINE["pre_release"] == (
        "dashboard_access_verified", "release_shows_as_upcoming",
        "split_sheet_signed_before_upload", "stems_archived_for_sync",
    )
    assert rd.TIMELINE_DOCTRINE["post_release"][0] == "verify_live_on_every_platform"


# ── Permanent per-release record (section E) ───────────────────────────────────

def test_release_record_spec_fields_complete():
    fields = [f["field"] for f in rd.RELEASE_RECORD_SPEC["fields"]]
    for expected in ("title", "version", "artist_spelling", "isrc_per_track",
                     "upc", "distributor", "release_date", "platform_uris",
                     "writer_splits", "publisher_info", "master_owner",
                     "takedown_redelivery_notes"):
        assert expected in fields, f"missing release-record field: {expected}"
    assert rd.RELEASE_RECORD_SPEC["purpose"]


# ── Distributor-switch mechanism (section F) ───────────────────────────────────

def test_distributor_switch_mechanism_is_ordered():
    # REQUIRED: mechanism-not-advice, and the ORDER is load-bearing —
    # export first, remove old last.
    assert rd.DISTRIBUTOR_SWITCH_MECHANISM["steps"] == (
        "export_all_codes_first",
        "upload_to_new_with_same_isrcs",
        "verify_live_via_new",
        "only_then_remove_old",
    )
    never = rd.DISTRIBUTOR_SWITCH_MECHANISM["never"].lower()
    assert "codes" in never and "in hand" in never
    # every step has a note explaining the mechanism
    for step in rd.DISTRIBUTOR_SWITCH_MECHANISM["steps"]:
        assert rd.DISTRIBUTOR_SWITCH_MECHANISM["step_notes"][step]


# ── Honesty rules (section G) ──────────────────────────────────────────────────

def test_honesty_rule_ids_stable():
    rule_ids = [r["id"] for r in rd.HONESTY_RULES]
    assert rule_ids == [
        "specs_are_current_conventions_verify_live",
        "never_invent_identifier_date_or_credit",
        "no_strategy_as_fact",
        "legal_licensing_routes_elsewhere",
    ]
    for rule in rd.HONESTY_RULES:
        assert rule["statement"] and rule["allowed"] and rule["forbidden"]


def test_never_invent_rule_three_way_markers():
    rule = next(r for r in rd.HONESTY_RULES
                if r["id"] == "never_invent_identifier_date_or_credit")
    assert rule["markers"] == ("supplied", "[NEEDS:<fact>]", "[ARTIST-SUPPLIED:<confirm>]")
    assert "no fourth state" in rule["statement"].lower()
    assert "re-casing" in rule["forbidden"].lower()


def test_legal_licensing_routes_elsewhere_present():
    rule = next(r for r in rd.HONESTY_RULES
                if r["id"] == "legal_licensing_routes_elsewhere")
    stmt = rule["statement"].lower()
    assert "licensing" in stmt
    assert "publishing" in stmt


# ── TOMMY-SPECIFIC HARD RULE: 3000 is the only numeric leaf; no stat literals ──

def test_only_numeric_leaf_is_artwork_dimension():
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
        _numeric_leaves(getattr(rd, name), name)
    assert sorted(v for _, v in found) == [3000], found
    assert found[0][0] == "ARTWORK_SPEC.min_dimension_px"


def test_source_contains_no_stat_or_currency_or_date_literals():
    # A delivery corpus with example stats, prices, or concrete dates would be a
    # fabrication vector. Lead times are spelled as words, so digit runs beyond
    # the single 3000 dimension are forbidden.
    stat_shapes = (
        r"\d{1,3}(?:,\d{3})+",                       # 1,000,000
        r"[$£€]\s?\d",                                # currency amounts
        r"\d+(?:\.\d+)?\s*[MmKkBb]\+?\b",            # 1M / 10k / 2.5B
        r"\d+\s*(?:streams|followers|listeners|views|plays|sold|copies|fans)",
        r"\d\s*%",                                    # any digit-percentage
        r"#\s*\d+",                                   # chart positions
        r"\d{4}-\d{2}-\d{2}",                         # ISO dates (no invented dates)
    )
    for shape in stat_shapes:
        matches = re.findall(shape, _SOURCE, flags=re.IGNORECASE)
        assert matches == [], f"stat/currency/date-shaped literal(s) in source: {matches}"
