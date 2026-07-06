"""
PROOF tests — royalties_data (Nadia Unit 1, corpus only).

Asserts the structured recording-royalty & registration corpus faithfully
encodes the map: recording-side society library (SoundExchange's US
digital-non-interactive-only scope with the statutory 50/45/5 split — the ONLY
hard-coded split anywhere, enforced by a numeric scan; France's four-body
role split; SAMI performers-only; the two DISTINCT Gramex organizations),
the four royalty streams, per-country routing whose composition-side ids
resolve in publishing_data.SOCIETIES (cross-module consistency — Reed's
records are referenced, never duplicated) and whose recording-side ids resolve
in RECORDING_SOCIETIES (NZ honestly None + verify-live), the
registration-situation axes (every flag explicit-only) and rules, the LOD
canonical fields with the percentage-never-computed reminder, and the
section-G honesty rules with stable ids — plus the module-level guarantees:
data-only (no def/class/import/call), JSON-serializable throughout, and
entity-wall clean. No service or main.py wiring exists yet; these tests import
the data module directly.
"""
import ast
import json
import pathlib
import re

import publishing_data
import royalties_data as rd
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = (
    "REPRESENTS_VALUES", "STREAM_SIDES", "COLLECTED_BY_REFS", "ROYALTY_COUNTRIES",
    "SPLIT_UNKNOWN_SENTINEL", "RECORDING_SOCIETIES", "STREAMS",
    "COUNTRY_ROYALTY_TABLE", "REGISTRATION_SITUATION_SPEC", "REGISTRATION_RULES",
    "LOD_SPEC", "METADATA_DOCTRINE", "HONESTY_RULES", "WITHHOLDING_MECHANISM",
)

_SOURCE = pathlib.Path(rd.__file__).read_text(encoding="utf-8")


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


# ── Country coverage + CROSS-MODULE consistency with Reed's corpus ─────────────

def test_country_coverage_matches_map():
    expected = {"CA", "US", "UK", "AU", "NZ", "DE", "FR", "SE", "DK", "NO", "FI"}
    assert set(rd.COUNTRY_ROYALTY_TABLE) == expected
    assert set(rd.ROYALTY_COUNTRIES) == expected
    for code, rec in rd.COUNTRY_ROYALTY_TABLE.items():
        assert rec["country"] == code


def test_composition_ids_resolve_in_publishing_data():
    # CROSS-MODULE consistency: composition-side bodies live in Reed's corpus
    # and are referenced by id — every id must resolve there, none duplicated
    # here.
    for code, rec in rd.COUNTRY_ROYALTY_TABLE.items():
        for stream in ("composition_performance_ids", "composition_mechanical_ids"):
            ids = rec[stream]
            assert len(ids) >= 1, f"{code} has an empty {stream} tuple"
            for sid in ids:
                assert sid in publishing_data.SOCIETIES, (
                    f"{code}.{stream} references id {sid!r} that does not "
                    "resolve in publishing_data.SOCIETIES"
                )
                assert sid not in rd.RECORDING_SOCIETIES, (
                    f"composition-side id {sid!r} duplicated into RECORDING_SOCIETIES"
                )


def test_composition_routing_mirrors_reeds_country_registration():
    # The composition routing must AGREE with Reed's corpus, not fork from it.
    for code, rec in rd.COUNTRY_ROYALTY_TABLE.items():
        reed = publishing_data.COUNTRY_REGISTRATION[code]
        assert set(rec["composition_performance_ids"]) == set(reed["performance"]), code
        assert set(rec["composition_mechanical_ids"]) == set(reed["mechanical"]), code


def test_recording_ids_resolve_in_recording_societies():
    referenced = set()
    for code, rec in rd.COUNTRY_ROYALTY_TABLE.items():
        ids = rec["recording_performance_ids"]
        if ids is None:
            continue  # honest-unknown countries are covered separately (NZ)
        assert len(ids) >= 1, f"{code} has an empty recording tuple — use None instead"
        for sid in ids:
            assert sid in rd.RECORDING_SOCIETIES, (
                f"{code} references undefined recording body {sid!r}"
            )
        referenced.update(ids)
    assert referenced == set(rd.RECORDING_SOCIETIES), (
        "orphaned or missing recording-society records vs country routing"
    )


def test_expected_recording_society_roster():
    assert set(rd.RECORDING_SOCIETIES) == {
        "soundexchange", "resound", "ppl", "ppca", "gvl", "adami", "spedidam",
        "scpp", "sppf", "sami", "gramo", "gramex_dk", "gramex_fi",
    }


def test_recording_society_records_are_internally_consistent():
    for sid, soc in rd.RECORDING_SOCIETIES.items():
        assert soc["id"] == sid
        assert soc["country"] in rd.ROYALTY_COUNTRIES
        assert soc["represents"] in rd.REPRESENTS_VALUES
        assert soc["scope_notes"]
        assert soc["registration_notes"]


# ── US scope facts (verbatim-critical) ─────────────────────────────────────────

def test_us_soundexchange_digital_only_no_terrestrial():
    sx = rd.RECORDING_SOCIETIES["soundexchange"]
    assert sx["country"] == "US"
    assert sx["represents"] == "both"
    scope = sx["scope_notes"].lower()
    assert "digital non-interactive only" in scope
    assert "no terrestrial-radio neighbouring right" in scope
    us_notes = rd.COUNTRY_ROYALTY_TABLE["US"]["notes"].lower()
    assert "no terrestrial-radio neighbouring right" in us_notes
    assert rd.COUNTRY_ROYALTY_TABLE["US"]["recording_performance_ids"] == ("soundexchange",)


def test_soundexchange_statutory_split_50_45_5():
    split = rd.RECORDING_SOCIETIES["soundexchange"]["statutory_split"]
    assert split["rights_owner_pct"] == 50
    assert split["featured_performer_pct"] == 45
    assert split["non_featured_performer_pct"] == 5
    assert "statutory" in split["basis"].lower()


def test_soundexchange_international_mandate_note():
    notes = rd.RECORDING_SOCIETIES["soundexchange"]["registration_notes"]
    assert "International Mandate" in notes
    assert "90+" in notes and "reciprocal" in notes.lower()


def test_statutory_split_is_the_only_hardcoded_split():
    # HARD RULE: the ONLY numerics stated as fact anywhere in this corpus are
    # the SoundExchange statutory 50/45/5 split and the US statutory 30% NRA
    # withholding default (honesty pass — WITHHOLDING_MECHANISM).
    # 1) Numeric scan — the only non-bool numeric leaves in the whole corpus
    #    are the three statutory split percentages plus the statutory 30.
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
    assert sorted(v for _, v in found) == [5, 30, 45, 50], found
    for path, value in found:
        assert ("soundexchange.statutory_split" in path
                or path == "WITHHOLDING_MECHANISM.us_statutory_default.rate"), (
            f"numeric value outside the statutory split / statutory "
            f"withholding default: {path}={value}"
        )
    # 2) Source scan — every N/N(/N) split-shaped literal is the statutory one.
    for match in re.findall(r"\b\d{1,3}\s*/\s*\d{1,3}(?:\s*/\s*\d{1,3})?\b", _SOURCE):
        assert match.replace(" ", "") == "50/45/5", (
            f"split-shaped literal other than the statutory one: {match!r}"
        )
    # 3) The sentinel exists for everything else.
    assert rd.SPLIT_UNKNOWN_SENTINEL == "varies_verify_with_society"
    assert _SOURCE.count("varies_verify_with_society") >= 2


# ── France four-body role split ────────────────────────────────────────────────

def test_france_four_bodies_split_by_role():
    fr = rd.COUNTRY_ROYALTY_TABLE["FR"]
    assert set(fr["recording_performance_ids"]) == {"adami", "spedidam", "scpp", "sppf"}
    assert "role" in fr["notes"].lower()
    assert rd.RECORDING_SOCIETIES["adami"]["represents"] == "performers"
    assert "featured" in rd.RECORDING_SOCIETIES["adami"]["scope_notes"].lower()
    assert rd.RECORDING_SOCIETIES["spedidam"]["represents"] == "performers"
    assert "session" in rd.RECORDING_SOCIETIES["spedidam"]["scope_notes"].lower()
    for producer_body in ("scpp", "sppf"):
        assert rd.RECORDING_SOCIETIES[producer_body]["represents"] == "rights_owners"
        assert rd.RECORDING_SOCIETIES[producer_body]["country"] == "FR"


def test_sami_is_performers_only():
    sami = rd.RECORDING_SOCIETIES["sami"]
    assert sami["represents"] == "performers"
    assert sami["country"] == "SE"
    assert rd.COUNTRY_ROYALTY_TABLE["SE"]["recording_performance_ids"] == ("sami",)


# ── The two Gramex organizations are DISTINCT ──────────────────────────────────

def test_gramex_dk_and_gramex_fi_are_distinct():
    dk, fi = rd.RECORDING_SOCIETIES["gramex_dk"], rd.RECORDING_SOCIETIES["gramex_fi"]
    assert dk["country"] == "DK" and fi["country"] == "FI"
    assert dk["name"] != fi["name"]
    for rec in (dk, fi):
        assert "distinct" in rec["scope_notes"].lower()
    assert rd.COUNTRY_ROYALTY_TABLE["DK"]["recording_performance_ids"] == ("gramex_dk",)
    assert rd.COUNTRY_ROYALTY_TABLE["FI"]["recording_performance_ids"] == ("gramex_fi",)


# ── NZ honest-unknown ──────────────────────────────────────────────────────────

def test_nz_recording_side_is_honestly_unknown():
    nz = rd.COUNTRY_ROYALTY_TABLE["NZ"]
    assert nz["recording_performance_ids"] is None, "a body must never be invented"
    assert "verify live" in nz["notes"].lower()
    # NZ is the ONLY honest-unknown in the table
    unknown = {c for c, rec in rd.COUNTRY_ROYALTY_TABLE.items()
               if rec["recording_performance_ids"] is None}
    assert unknown == {"NZ"}


# ── The four streams ───────────────────────────────────────────────────────────

def test_streams_are_the_four_expected_with_correct_refs():
    assert set(rd.STREAMS) == {"composition_performance", "composition_mechanical",
                               "recording_performance", "us_digital_recording_performance"}
    for sid, stream in rd.STREAMS.items():
        assert stream["id"] == sid
        assert stream["side"] in rd.STREAM_SIDES
        assert stream["collected_by_ref"] in rd.COLLECTED_BY_REFS
    for comp_id in ("composition_performance", "composition_mechanical"):
        assert rd.STREAMS[comp_id]["side"] == "composition"
        assert rd.STREAMS[comp_id]["collected_by_ref"] == "publishing_data"
    for rec_id in ("recording_performance", "us_digital_recording_performance"):
        assert rd.STREAMS[rec_id]["side"] == "recording"
        assert rd.STREAMS[rec_id]["collected_by_ref"] == "royalties_data"


# ── Registration situation axes + rules ────────────────────────────────────────

def test_situation_axes_all_explicit_only():
    expected_axes = {"country_of_residence", "self_published", "owns_masters",
                     "performed_on_recording", "has_producers_or_session_players"}
    assert set(rd.REGISTRATION_SITUATION_SPEC) == expected_axes
    for axis, spec in rd.REGISTRATION_SITUATION_SPEC.items():
        assert spec["axis"] == axis
        assert spec["description"]
        assert spec["confirmation"] == "explicit confirmation required, never inferred"


def test_registration_rules_cover_the_map():
    by_id = {r["id"]: r for r in rd.REGISTRATION_RULES}
    assert set(by_id) == {"writer_home_pro", "self_published_publisher_registration",
                          "us_catalog_mlc", "masters_rights_owner_registration",
                          "performer_registration", "producers_session_players_lod"}
    for rule in rd.REGISTRATION_RULES:
        assert rule["condition"]["axis"] in rd.REGISTRATION_SITUATION_SPEC
        assert rule["stream_id"] in rd.STREAMS
        # exactly one of body_ref / body_lookup
        assert (rule["body_ref"] is None) != (rule["body_lookup"] is None)
        if rule["body_ref"] is not None:
            corpus = rule["body_ref_corpus"]
            assert corpus in rd.COLLECTED_BY_REFS
            pool = (publishing_data.SOCIETIES if corpus == "publishing_data"
                    else rd.RECORDING_SOCIETIES)
            assert rule["body_ref"] in pool, rule["id"]
        assert rule["reason"]

    assert by_id["writer_home_pro"]["capacity"] == "writer"
    assert by_id["self_published_publisher_registration"]["capacity"] == "publisher"
    mlc = by_id["us_catalog_mlc"]
    assert mlc["body_ref"] == "the_mlc"
    assert mlc["notes"] == "separate and free"
    assert mlc["condition"] == {"axis": "country_of_residence", "equals": "US"}
    masters = by_id["masters_rights_owner_registration"]
    assert masters["capacity"] == "rights_owner"
    assert masters["stream_id_us_override"] == "us_digital_recording_performance"
    assert "International Mandate" in masters["notes"]
    performer = by_id["performer_registration"]
    assert performer["capacity"] == "performer"
    assert "both" in performer["reason"].lower()  # both-hats = both capacities
    lod = by_id["producers_session_players_lod"]
    assert lod["registration"] == "letter_of_direction"
    assert lod["body_ref"] == "soundexchange"
    assert "ppl" in lod["notes"].lower()  # similar mechanism at PPL


# ── LOD spec ───────────────────────────────────────────────────────────────────

def test_lod_canonical_fields_present_and_required():
    fields = {f["field"]: f for f in rd.LOD_SPEC["fields"]}
    assert set(fields) == {"artist_legal_name", "payee_legal_name", "payee_contact",
                           "recordings_covered", "percentage_directed",
                           "effective_date", "signatures_both_parties"}
    for f in fields.values():
        assert f["required"] is True
    assert "isrc" in fields["recordings_covered"]["description"].lower()


def test_lod_percentage_never_computed_rule_present():
    pct = next(f for f in rd.LOD_SPEC["fields"] if f["field"] == "percentage_directed")
    assert "NEVER computed or suggested" in pct["description"]
    reminder_ids = [r["id"] for r in rd.LOD_SPEC["reminders"]]
    assert reminder_ids == ["draft_for_review_only", "percentage_directed_supplied_only"]
    pct_reminder = next(r for r in rd.LOD_SPEC["reminders"]
                        if r["id"] == "percentage_directed_supplied_only")
    assert "NEVER computed or suggested" in pct_reminder["text"]
    draft = next(r for r in rd.LOD_SPEC["reminders"] if r["id"] == "draft_for_review_only")
    assert "draft-for-review" in draft["text"].lower()
    assert "lex" in draft["text"].lower()


# ── Doctrine + honesty rules ───────────────────────────────────────────────────

def test_metadata_doctrine_present():
    assert set(rd.METADATA_DOCTRINE) == {"consistent_identifiers_everywhere",
                                         "distributor_does_not_collect_everything",
                                         "both_hats_us_registration"}
    consistent = rd.METADATA_DOCTRINE["consistent_identifiers_everywhere"]
    for token in ("ISRC", "ISWC", "IPI", "black box"):
        assert token in consistent
    assert "BOTH capacities" in rd.METADATA_DOCTRINE["both_hats_us_registration"]


def test_honesty_rule_ids_stable():
    rule_ids = [r["id"] for r in rd.HONESTY_RULES]
    assert rule_ids == ["unknown_is_none", "only_statutory_split_hardcoded",
                        "situation_flags_explicit_only", "free_text_is_note_only",
                        "no_tax_or_legal_advice"]
    for rule in rd.HONESTY_RULES:
        assert rule["statement"] and rule["allowed"] and rule["forbidden"]
    split_rule = next(r for r in rd.HONESTY_RULES
                      if r["id"] == "only_statutory_split_hardcoded")
    assert "varies_verify_with_society" in split_rule["forbidden"]
    flags_rule = next(r for r in rd.HONESTY_RULES
                      if r["id"] == "situation_flags_explicit_only")
    assert "[NEEDS:" in flags_rule["forbidden"]
    tax_rule = next(r for r in rd.HONESTY_RULES if r["id"] == "no_tax_or_legal_advice")
    assert "lex" in tax_rule["statement"].lower()
    assert "draft-for-review" in tax_rule["statement"].lower()
