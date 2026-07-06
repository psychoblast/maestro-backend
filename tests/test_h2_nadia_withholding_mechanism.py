"""
PROOF tests — Honesty pass Unit 2 (Nadia): withholding MECHANISM replaces the
invented per-source rate buckets.

The service's invented 0/15/20/30 withholding buckets are DELETED —
scan-asserted gone from source, and no numeric leaf survives anywhere in
_SOURCES. In their place: royalties_data.WITHHOLDING_MECHANISM — the US
statutory 30% NRA default (IRC 1441) is the ONLY withholding rate stated as a
number anywhere; treaty reduction is rate-None + verify pointer (W-8BEN /
W-8BEN-E filed with the WITHHOLDING AGENT, not the IRS; TIN generally
required; no valid form on file → the agent must withhold the full 30%);
reporting mechanics (1042-S / W-9 → 1099-MISC / 1040-NR recovery); royalty
categories treated separately per treaty; non-US regimes rate-None +
verify-live; file-before-first-payment doctrine. Consumers
(search_royalty_sources, reconcile_royalty_statement) produce mechanism-based
output: the withheld figure is statement-supplied or a [NEEDS:withheld_amount]
gap — NEVER a computed rate.
"""
import json
import pathlib
import re

import asyncio

import ledger_lock_service as svc
import royalties_data as rd
from entity_wall_terms import assert_no_forbidden_terms


def _run(coro):
    return asyncio.run(coro)


_RD_SOURCE = pathlib.Path(rd.__file__).read_text(encoding="utf-8")
_SVC_SOURCE = pathlib.Path(svc.__file__).read_text(encoding="utf-8")


# ── the invented buckets are GONE (scan) ───────────────────────────────────────

def test_bucket_key_gone_from_service_source():
    assert "withholding_pct" not in _SVC_SOURCE


def test_sources_carry_no_numeric_leaves_at_all():
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
    _numeric_leaves(svc._SOURCES, "_SOURCES")
    assert found == [], f"a source stores a number — bucket remnant: {found}"


def test_no_treaty_rate_stated_numerically_anywhere():
    # The only percent literals permitted in the corpus source are the
    # statutory ones: 50/45/5 (SoundExchange) and 30 (NRA default). The old
    # bucket values 15 and 20 must not appear as a percentage anywhere.
    for pct in re.findall(r"(\d{1,3})\s*%", _RD_SOURCE):
        assert int(pct) in (5, 30, 45, 50), f"non-statutory percent literal: {pct}%"
    for record in rd.WITHHOLDING_MECHANISM.values():
        if "rate" in record and record["id"] != "us_statutory_default":
            assert record["rate"] is None, (
                f"a non-statutory rate is stated numerically: {record['id']}"
            )


# ── corpus: WITHHOLDING_MECHANISM records complete ─────────────────────────────

def test_us_statutory_default_is_the_only_number():
    rec = rd.WITHHOLDING_MECHANISM["us_statutory_default"]
    assert rec["rate"] == 30
    assert "IRC 1441" in rec["scope"]
    assert "foreign persons" in rec["scope"]
    assert "ONLY withholding rate stated as a number" in rec["note"]


def test_treaty_reduction_varies_with_verify_pointer_and_forms():
    rec = rd.WITHHOLDING_MECHANISM["treaty_reduction"]
    assert rec["rate"] is None
    assert "varies by specific treaty AND income category" in rec["note"]
    assert "IRS Tax Treaty Tables" in rec["note"]
    assert "Pub 515" in rec["note"] and "Pub 901" in rec["note"]
    assert tuple(rec["claim_forms"]) == ("W-8BEN individuals", "W-8BEN-E entities")
    assert "NOT the IRS" in rec["filed_with"]
    assert "withholding agent" in rec["filed_with"]
    assert rec["tin_generally_required"] is True
    assert "30%" in rec["without_valid_form"]


def test_reporting_mechanics():
    rec = rd.WITHHOLDING_MECHANISM["reporting"]
    assert rec["foreign_payee"] == "1042-S"
    assert rec["us_person"] == "W-9 → 1099-MISC"
    assert "1040-NR" in rec["over_withheld_recovery"]


def test_royalty_categories_and_non_us_regimes():
    cats = rd.WITHHOLDING_MECHANISM["royalty_categories_note"]
    assert "treated separately" in cats["note"]
    assert "motion picture/TV" in cats["note"]
    assert "never state one number" in cats["note"]
    non_us = rd.WITHHOLDING_MECHANISM["non_us_regimes"]
    assert non_us["rate"] is None
    assert "home society statement" in non_us["note"]
    assert "tax professional" in non_us["note"]


def test_file_before_first_payment_doctrine():
    rec = rd.WITHHOLDING_MECHANISM["file_before_first_payment"]
    assert "BEFORE the first payment" in rec["doctrine"]
    assert "withhold the full statutory 30%" in rec["doctrine"]


def test_mechanism_json_serializable_and_entity_wall_clean():
    json.dumps(rd.WITHHOLDING_MECHANISM)
    assert_no_forbidden_terms(_RD_SOURCE)
    assert_no_forbidden_terms(_SVC_SOURCE)


# ── consumer: search_royalty_sources ───────────────────────────────────────────

def test_search_sources_resolve_mechanism_not_rates():
    res = _run(svc.search_royalty_sources())
    assert res["count"] == 7
    assert res["withholding_policy"] == "statement_supplied_or_verify_live"
    assert "no_tax_or_legal_advice" in res["withholding_honesty_rule_ids"]
    for s in res["sources"]:
        assert "withholding_pct" not in s
        ids = [m["id"] for m in s["withholding_mechanism"]]
        if s["region"] == "foreign":
            assert "us_statutory_default" in ids
            assert "treaty_reduction" in ids
            assert "non_us_regimes" in ids
        else:
            assert ids == ["reporting"]


def test_search_filters_still_work():
    res = _run(svc.search_royalty_sources(source_type="streaming", region="foreign"))
    assert res["count"] == 1
    assert res["sources"][0]["id"] == "src-streaming-foreign"
    json.dumps(res)


# ── consumer: reconcile_royalty_statement ──────────────────────────────────────

def test_reconcile_books_statement_supplied_figures_only():
    res = _run(svc.reconcile_royalty_statement(
        "artist-1", source_id="src-streaming-foreign",
        statement_period="2026-Q1", gross_amount=10000, withheld_amount=3000))
    assert res["reconciled"] is True
    assert res["recommendation"] == "record"
    assert res["withheld_amount"] == 3000.0
    assert res["net_amount"] == 7000.0
    labels = [li["label"] for li in res["line_items"]]
    assert labels == ["gross", "withholding_as_reported_on_statement", "net"]
    assert "withholding_pct" not in res
    assert res["withholding_basis"]["policy"] == "statement_supplied_or_verify_live"
    json.dumps(res)


def test_reconcile_missing_withheld_is_a_needs_gap_never_a_computed_rate():
    res = _run(svc.reconcile_royalty_statement(
        "artist-1", source_id="src-streaming-foreign",
        statement_period="2026-Q1", gross_amount=10000))
    assert "missing_withheld_amount" in res["gaps"]
    assert res["reconciled"] is False
    assert res["recommendation"] == "adjust"
    assert res["withheld_amount"] is None
    assert res["net_amount"] is None, "a net here would mean a rate was computed"
    assert res["line_items"] == []
    basis = res["withholding_basis"]
    assert basis["gap"] == "[NEEDS:withheld_amount]"
    assert "verify" in basis
    mech_ids = [m["id"] for m in basis["mechanism"]]
    assert "us_statutory_default" in mech_ids and "treaty_reduction" in mech_ids


def test_reconcile_mechanism_carries_the_statutory_default_only_number():
    res = _run(svc.reconcile_royalty_statement(
        "artist-1", source_id="src-performance-foreign",
        statement_period="2026-Q1", gross_amount=500))
    rates = [m.get("rate") for m in res["withholding_basis"]["mechanism"]
             if "rate" in m]
    assert sorted(r for r in rates if r is not None) == [30]


def test_reconcile_domestic_source_routes_to_reporting_mechanics():
    res = _run(svc.reconcile_royalty_statement(
        "artist-1", source_id="src-sync",
        statement_period="2026-Q1", gross_amount=1200, withheld_amount=0))
    assert res["recommendation"] == "record"
    assert [m["id"] for m in res["withholding_basis"]["mechanism"]] == ["reporting"]


def test_reconcile_guards_bad_withheld_figures():
    res = _run(svc.reconcile_royalty_statement(
        "artist-1", source_id="src-mechanical",
        statement_period="2026-Q1", gross_amount=100, withheld_amount=250))
    assert "withheld_exceeds_gross" in res["gaps"]
    assert res["recommendation"] == "adjust"
    res = _run(svc.reconcile_royalty_statement(
        "artist-1", source_id="src-mechanical",
        statement_period="2026-Q1", gross_amount=100, withheld_amount=-5))
    assert "negative_withheld_amount" in res["gaps"]
    assert res["net_amount"] is None


def test_reconcile_unknown_source_still_blocked():
    res = _run(svc.reconcile_royalty_statement(
        "artist-1", source_id="src-nope",
        statement_period="2026-Q1", gross_amount=100, withheld_amount=10))
    assert res["recommendation"] == "blocked"
    assert res["reconciled"] is False
    # even blocked output carries the full mechanism to verify against
    ids = {m["id"] for m in res["withholding_basis"]["mechanism"]}
    assert ids == set(rd.WITHHOLDING_MECHANISM)
    json.dumps(res)
