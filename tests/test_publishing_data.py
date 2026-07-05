"""
PROOF tests — publishing_data (Reed Unit 1, corpus only).

Asserts the structured publishing/sync corpus faithfully encodes
REED_PUBLISHING_SYNC_MAP_v1.md: per-country society routing (incl. the US
one-PRO-of-four rule, Canada's two RROs, the shared Nordic NCB, the DE/FR
unified CMOs, and PPL's out-of-scope boundary), the IPI/ISWC/ISRC
composition-vs-recording distinction, the split-sheet double-100% invariants,
the sync pack's one-stop conditions, and the section-E honesty rules — plus
the module-level guarantees: data-only (no def/class), JSON-serializable
throughout, and entity-wall clean. No service or main.py wiring exists yet;
these tests import the data module directly.
"""
import ast
import json
import pathlib

import publishing_data as pd
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = (
    "SOCIETY_ROLES", "MEMBERSHIP_MODELS", "IDENTIFIER_SUBJECTS", "RIGHTS_SIDES",
    "PUBLISHING_COUNTRIES", "SOCIETIES", "OUT_OF_SCOPE_BODIES",
    "COUNTRY_REGISTRATION", "IDENTIFIERS", "SPLIT_SHEET_SPEC",
    "SYNC_METADATA_SPEC", "HONESTY_RULES", "DOCTRINE",
)

_SOURCE = pathlib.Path(pd.__file__).read_text(encoding="utf-8")


def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(pd, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(pd, name))  # raises TypeError on any leak


def test_module_is_data_only_no_def_or_class():
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


def test_country_coverage_matches_map():
    expected = {"CA", "US", "UK", "AU", "NZ", "DE", "FR", "SE", "DK", "NO", "FI"}
    assert set(pd.COUNTRY_REGISTRATION) == expected
    assert set(pd.PUBLISHING_COUNTRIES) == expected
    for code, rec in pd.COUNTRY_REGISTRATION.items():
        assert rec["country"] == code


def test_country_records_reference_only_defined_societies():
    for code, rec in pd.COUNTRY_REGISTRATION.items():
        for stream in ("performance", "mechanical"):
            assert len(rec[stream]) >= 1, f"{code} has an empty {stream} tuple"
            for sid in rec[stream]:
                assert sid in pd.SOCIETIES, f"{code}.{stream} references undefined id {sid!r}"
    # cross-refs inside the society library resolve too
    for sid, soc in pd.SOCIETIES.items():
        ref = soc["administered_with"]
        assert ref is None or ref in pd.SOCIETIES, (
            f"{sid}.administered_with references undefined id {ref!r}"
        )


def test_us_writer_picks_one_pro_of_four():
    us = pd.COUNTRY_REGISTRATION["US"]
    assert us["writer_must_choose_one_pro"] is True
    assert len(us["performance"]) == 4
    for code, rec in pd.COUNTRY_REGISTRATION.items():
        if code != "US":
            assert rec["writer_must_choose_one_pro"] is False, (
                f"{code} wrongly flags a PRO choice — only the US has one"
            )


def test_us_sesac_and_gmr_are_invite_only():
    assert pd.SOCIETIES["sesac"]["membership_model"] == "invite_only"
    assert pd.SOCIETIES["gmr"]["membership_model"] == "invite_only"
    assert pd.SOCIETIES["ascap"]["membership_model"] == "open"
    assert pd.SOCIETIES["bmi"]["membership_model"] == "open"


def test_mlc_is_separate_and_free():
    us = pd.COUNTRY_REGISTRATION["US"]
    assert "the_mlc" in us["mechanical"]
    assert "the_mlc" not in us["performance"]
    fee_note = pd.SOCIETIES["the_mlc"]["registration_fee_notes"]
    assert fee_note is not None
    assert "separate" in fee_note.lower()
    assert "free" in fee_note.lower()


def test_canada_has_two_rros():
    ca = pd.COUNTRY_REGISTRATION["CA"]
    assert len(ca["mechanical"]) == 2
    assert set(ca["mechanical"]) == {"cmrra", "socan_rr"}
    assert pd.SOCIETIES["socan_rr"]["administered_with"] == "socan"


def test_ppl_is_out_of_scope_recording_side():
    ids = [b["id"] for b in pd.OUT_OF_SCOPE_BODIES]
    assert "ppl" in ids
    ppl = next(b for b in pd.OUT_OF_SCOPE_BODIES if b["id"] == "ppl")
    assert ppl["side"] == "recording"
    assert "ppl" not in pd.SOCIETIES
    for code, rec in pd.COUNTRY_REGISTRATION.items():
        assert "ppl" not in rec["performance"], f"PPL leaked into {code}.performance"
        assert "ppl" not in rec["mechanical"], f"PPL leaked into {code}.mechanical"


def test_ncb_shared_across_four_nordic_countries():
    nordic_pros = {"SE": "stim", "DK": "koda", "NO": "tono", "FI": "teosto"}
    for code, pro in nordic_pros.items():
        rec = pd.COUNTRY_REGISTRATION[code]
        assert rec["mechanical"] == ("ncb",), f"{code} mechanical is not NCB alone"
        assert rec["performance"] == (pro,), f"{code} performance is not {pro}"
    assert set(pd.SOCIETIES["ncb"]["countries"]) == set(nordic_pros)


def test_unified_cmo_flags_match_doctrine():
    unified = {c for c, rec in pd.COUNTRY_REGISTRATION.items() if rec["unified_cmo"]}
    assert unified == {"DE", "FR"}
    for sid in ("gema", "sacem"):
        assert set(pd.SOCIETIES[sid]["roles"]) == {"performance", "mechanical"}
    assert "anglo_split_vs_continental_unified" in pd.DOCTRINE
    # unified countries route both streams to the same single society
    for code in ("DE", "FR"):
        rec = pd.COUNTRY_REGISTRATION[code]
        assert rec["performance"] == rec["mechanical"]
        assert len(rec["performance"]) == 1


def test_identifier_composition_vs_recording_distinction():
    assert set(pd.IDENTIFIERS) == {"ipi", "iswc", "isrc"}
    assert pd.IDENTIFIERS["iswc"]["side"] == "composition"
    assert pd.IDENTIFIERS["iswc"]["identifies"] == ("composition",)
    assert pd.IDENTIFIERS["isrc"]["side"] == "recording"
    assert pd.IDENTIFIERS["isrc"]["identifies"] == ("recording",)
    assert set(pd.IDENTIFIERS["ipi"]["identifies"]) == {"writer", "publisher"}
    assert pd.IDENTIFIERS["ipi"]["formerly"] == "CAE"
    assert "split_sheet" in pd.IDENTIFIERS["ipi"]["required_on"]


def test_split_sheet_has_both_100_sum_invariants():
    invariants = pd.SPLIT_SHEET_SPEC["invariants"]
    by_id = {inv["id"]: inv for inv in invariants}
    assert set(by_id) == {"writer_shares_sum_100", "publisher_shares_sum_100"}, (
        "exactly the two map-stated invariants — nothing invented"
    )
    assert by_id["writer_shares_sum_100"]["side"] == "writer"
    assert by_id["publisher_shares_sum_100"]["side"] == "publisher"
    for inv in invariants:
        assert inv["rule"] == "sum"
        assert inv["target"] == 100


def test_split_sheet_master_extension_and_amendment_rule():
    ext = pd.SPLIT_SHEET_SPEC["master_side_extension"]
    assert ext["status"] == "best_practice"
    ext_fields = {f["field"] for f in ext["fields"]}
    assert {"isrc", "master_ownership_percent"} <= ext_fields
    assert pd.SPLIT_SHEET_SPEC["amendment_rule"]["requires_all_party_resignature"] is True
    contributor_fields = {f["field"] for f in pd.SPLIT_SHEET_SPEC["contributor_fields"]}
    assert {"legal_name", "lyrics_percent", "music_percent", "pro_affiliation",
            "writer_ipi", "publisher_name", "publisher_ipi",
            "signature"} <= contributor_fields


def test_sync_pack_one_stop_conditions_complete():
    cond_ids = {c["id"] for c in pd.SYNC_METADATA_SPEC["one_stop_conditions"]}
    assert cond_ids == {"master_control_confirmed",
                        "publishing_control_100_confirmed",
                        "no_uncleared_samples"}
    pack_fields = {f["field"] for f in pd.SYNC_METADATA_SPEC["fields"]}
    assert {"one_stop_status", "samples_cleared_declaration", "isrc", "iswc",
            "pro_affiliation", "ipi", "rights_breakdown"} <= pack_fields
    assert "explicit artist confirmation" in pd.SYNC_METADATA_SPEC["one_stop_rule"]


def test_honesty_rules_and_home_society_doctrine():
    rule_ids = [r["id"] for r in pd.HONESTY_RULES]
    assert rule_ids == ["unknown_is_none", "free_text_is_note_only",
                        "sum_checks_supplied_only",
                        "one_stop_explicit_confirmation_only"]
    sum_rule = next(r for r in pd.HONESTY_RULES if r["id"] == "sum_checks_supplied_only")
    assert sum_rule["allowed"]
    assert "[NEEDS:" in sum_rule["forbidden"]
    home = pd.DOCTRINE["home_society_once"]
    assert "once" in home.lower()
    assert "never" in home.lower()


def test_society_records_are_internally_consistent():
    for sid, soc in pd.SOCIETIES.items():
        assert soc["id"] == sid
        assert len(soc["roles"]) >= 1
        for role in soc["roles"]:
            assert role in pd.SOCIETY_ROLES
        model = soc["membership_model"]
        assert model is None or model in pd.MEMBERSHIP_MODELS
        for country in soc["countries"]:
            assert country in pd.PUBLISHING_COUNTRIES
    # every society is reachable from at least one country's routing
    referenced = set()
    for rec in pd.COUNTRY_REGISTRATION.values():
        referenced.update(rec["performance"])
        referenced.update(rec["mechanical"])
    assert referenced == set(pd.SOCIETIES), (
        "orphaned or missing society records vs country routing"
    )
