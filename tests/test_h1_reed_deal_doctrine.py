"""
PROOF tests — Honesty pass Unit 1 (Reed): deal-type doctrine replaces the
invented catalog.

The service's four invented deal records (fake names, fake territory rows, an
unattributed fee number) are DELETED — scan-asserted gone from source. In
their place: publishing_data.DEAL_TYPES (four researched STRUCTURE records —
co-pub 75/25 asserted; the admin fee is a RANGE labeled negotiable, never a
single invented number; the co-pub term/retention asymmetry encoded),
DEAL_TRAP_TERMS (stable ids), and DEAL_HONESTY (Reed explains structures and
flags traps — NEVER evaluates a specific offer; real agreements route to Lex
as draft-for-review). lookup_deal_types is the honest service read;
search_publishing_deals survives as a thin alias so the wired tool name and
its dispatch/tests keep working. The corpus stays data-only, JSON-round-trip
clean, and entity-wall clean.
"""
import ast
import json
import pathlib

import ink_and_air_service as svc
import publishing_data as pd
from entity_wall_terms import assert_no_forbidden_terms

import asyncio


def _run(coro):
    return asyncio.run(coro)


_PD_SOURCE = pathlib.Path(pd.__file__).read_text(encoding="utf-8")
_SVC_SOURCE = pathlib.Path(svc.__file__).read_text(encoding="utf-8")

_NEGOTIABLE = "typical range — every deal negotiable"


# ── the invented catalog is GONE (scan) ────────────────────────────────────────

def test_invented_catalog_gone_from_source():
    # The four old record ids and names, and the catalog constant itself,
    # must not appear anywhere in the service OR the corpus.
    for term in ("_INK_AND_AIR_CATALOG", "p-admin", "p-copub", "p-sub", "p-full",
                 "Admin Deal", "Co-Pub Deal", "EU Sub-Pub", "Full Publishing"):
        assert term not in _SVC_SOURCE, f"invented-catalog remnant in service: {term!r}"
        assert term not in _PD_SOURCE, f"invented-catalog remnant in corpus: {term!r}"


# ── corpus: DEAL_TYPES ─────────────────────────────────────────────────────────

def test_four_deal_types_with_stable_ids_and_ownership():
    assert set(pd.DEAL_TYPES) == {"admin", "co_publishing", "full_publishing",
                                  "work_for_hire"}
    expected_ownership = {
        "admin": "writer_retains_100",
        "co_publishing": "copyright_co_owned_50_50",
        "full_publishing": "publisher_owns_publisher_share",
        "work_for_hire": "everything_transferred",
    }
    for did, record in pd.DEAL_TYPES.items():
        assert record["id"] == did
        assert record["ownership"] == expected_ownership[did]
        for field in ("name", "writer_income_structure", "fee_or_split_typical",
                      "term_typical", "advance_norm", "services_norm"):
            assert record[field], f"{did}.{field}"


def test_admin_fee_is_a_range_never_a_single_number():
    fee = pd.DEAL_TYPES["admin"]["fee_or_split_typical"]
    assert tuple(fee["range_pct"]) == (10, 25)
    assert fee["of"] == "publisher's share"
    assert fee["label"] == _NEGOTIABLE
    assert "10-15% domestic / 15-20% foreign" in fee["shape_note"]
    assert "negotiable" in fee["shape_note"]


def test_co_pub_75_25_structure_asserted():
    copub = pd.DEAL_TYPES["co_publishing"]
    assert copub["writer_income_structure"] == (
        "100% writer's share + 50% publisher's share = 75% of total publishing "
        "income to the writer.")
    assert "75/25" in copub["fee_or_split_typical"]["structure"]
    assert "structural, not a fee" in copub["fee_or_split_typical"]["structure"]


def test_co_pub_term_retention_asymmetry_encoded():
    term = pd.DEAL_TYPES["co_publishing"]["term_typical"]
    assert "1-3 years" in term["deal_term"]
    assert "negotiable" in term["deal_term"]
    assert "life of copyright" in term["retention_asymmetry"]
    assert "different" in term["retention_asymmetry"].lower()


def test_work_for_hire_no_ongoing_income():
    wfh = pd.DEAL_TYPES["work_for_hire"]
    assert "flat fee" in wfh["writer_income_structure"].lower()
    assert "no ongoing income" in wfh["writer_income_structure"].lower()
    assert wfh["advance_norm"] == "flat_fee"


def test_advance_norms_ladder():
    assert pd.DEAL_TYPES["admin"]["advance_norm"] == "none_or_low"
    assert pd.DEAL_TYPES["co_publishing"]["advance_norm"] == "customary_recoupable"
    assert pd.DEAL_TYPES["full_publishing"]["advance_norm"] == "largest"


def test_every_numeric_shape_labeled_negotiable():
    for did, record in pd.DEAL_TYPES.items():
        assert record["fee_or_split_typical"]["label"] == _NEGOTIABLE, did


# ── corpus: DEAL_TRAP_TERMS + DEAL_HONESTY ─────────────────────────────────────

def test_trap_term_ids_stable():
    assert [t["id"] for t in pd.DEAL_TRAP_TERMS] == [
        "recoupment", "cross_collateralization", "retention_period",
        "pipeline_songs", "at_source_collection", "writers_share_untouchable",
    ]
    for t in pd.DEAL_TRAP_TERMS:
        assert t["term"] and t["explanation"] and t["writer_note"]


def test_recoupment_loan_not_repayable_but_extends():
    recoup = next(t for t in pd.DEAL_TRAP_TERMS if t["id"] == "recoupment")
    assert "LOAN" in recoup["explanation"]
    assert "not repayable" in recoup["explanation"]
    assert "extend" in recoup["explanation"].lower()


def test_retention_period_range_and_writer_bias():
    retention = next(t for t in pd.DEAL_TRAP_TERMS if t["id"] == "retention_period")
    assert "2 years to life of copyright" in retention["explanation"]
    assert "negotiable" in retention["explanation"]
    assert "Shorter favors the writer" in retention["explanation"]


def test_writers_share_is_a_red_flag():
    ws = next(t for t in pd.DEAL_TRAP_TERMS if t["id"] == "writers_share_untouchable")
    assert ws["red_flag"] is True
    assert "red flag" in ws["explanation"].lower()
    # it is the ONLY trap term carrying the structural red_flag marker
    flagged = [t["id"] for t in pd.DEAL_TRAP_TERMS if t.get("red_flag")]
    assert flagged == ["writers_share_untouchable"]


def test_deal_honesty_doctrine():
    assert set(pd.DEAL_HONESTY) == {"explains_never_evaluates",
                                    "every_number_negotiable",
                                    "real_agreements_to_lawyer"}
    assert "NEVER evaluates a specific offer" in pd.DEAL_HONESTY["explains_never_evaluates"]
    assert "Lex" in pd.DEAL_HONESTY["real_agreements_to_lawyer"]
    assert "draft-for-review" in pd.DEAL_HONESTY["real_agreements_to_lawyer"]


# ── corpus contract still holds with the new sections ──────────────────────────

def test_new_constants_json_serializable_and_data_only():
    for name in ("DEAL_TYPES", "DEAL_TRAP_TERMS", "DEAL_HONESTY"):
        json.dumps(getattr(pd, name))
    tree = ast.parse(_PD_SOURCE)
    forbidden_nodes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                       ast.Import, ast.ImportFrom, ast.Call)
    for node in ast.walk(tree):
        assert not isinstance(node, forbidden_nodes), (
            f"forbidden node in corpus: {type(node).__name__}"
        )


def test_corpus_and_service_entity_wall_clean():
    assert_no_forbidden_terms(_PD_SOURCE)
    assert_no_forbidden_terms(_SVC_SOURCE)


# ── service: lookup_deal_types + the alias ─────────────────────────────────────

def test_lookup_returns_all_four_types_plus_traps_and_honesty():
    res = _run(svc.lookup_deal_types())
    assert res["count"] == 4
    assert {r["id"] for r in res["deal_types"]} == set(pd.DEAL_TYPES)
    assert [t["id"] for t in res["trap_terms"]] == \
        [t["id"] for t in pd.DEAL_TRAP_TERMS]
    assert res["honesty"] == dict(pd.DEAL_HONESTY)


def test_lookup_filter_matches_either_direction():
    # the old wired enum value "administration" must still find the admin record
    res = _run(svc.lookup_deal_types(deal_type="administration"))
    assert res["count"] == 1
    assert res["deal_types"][0]["id"] == "admin"
    res = _run(svc.lookup_deal_types(deal_type="work_for_hire"))
    assert [r["id"] for r in res["deal_types"]] == ["work_for_hire"]


def test_lookup_unknown_filter_lists_supported_types_never_invents():
    res = _run(svc.lookup_deal_types(deal_type="sub_publishing_360_super_deal"))
    assert res["count"] == 0
    assert res["deal_types"] == []
    assert res["supported_deal_types"] == list(pd.DEAL_TYPES)
    assert "never invented" in res["message"]


def test_territory_is_a_note_never_a_filter():
    res = _run(svc.lookup_deal_types(territory="eu"))
    assert res["count"] == 4, "territory must not narrow the doctrine"
    note = res["notes"][0]
    assert note["source"] == "territory"
    assert note["text"] == "eu"
    assert "never a filter" in note["note"]


def test_search_publishing_deals_is_a_thin_alias():
    alias = _run(svc.search_publishing_deals(deal_type="co_publishing"))
    direct = _run(svc.lookup_deal_types(deal_type="co_publishing"))
    assert alias == direct
    assert alias["deal_types"][0]["id"] == "co_publishing"


def test_lookup_results_json_serializable():
    for kwargs in ({}, {"deal_type": "admin"}, {"deal_type": "nope"},
                   {"territory": "worldwide"}):
        json.dumps(_run(svc.lookup_deal_types(**kwargs)))
