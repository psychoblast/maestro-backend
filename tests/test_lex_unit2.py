"""
PROOF tests — Lex Unit 2 (DOC-WRITER Option B service + wiring).

Locks the two replacement tools and THE ONE RULE ABOVE ALL, permanently:

  lookup_legal_concepts — pure corpus read/filter over legal_data, UNGATED
    (no env, no account); index mode with no filters; per-block filtering; a
    filter that matches nothing lands in not_found with value None (never guessed).

  build_legal_doc_scaffold — OPTION B: COMPACT ingredients only, no prose, no
    model call (AST-enforced: the service imports no LLM SDK and contains no
    ``messages.create``). Two doc types:
      * contract_review_brief — type-specific issue-spotting checklist + standing
        glossary + red-flag checklist; jurisdiction section WITHHELD unless a
        jurisdiction is supplied ([NEEDS:jurisdiction]); the actual contract is
        [ARTIST-SUPPLIED:contract_text]; all gap markers aggregate into missing[].
      * negotiation_prep_memo — everything framed as QUESTIONS to bring to
        counsel, never positions asserted as safe.

  Invariants (permanent): the scaffold header AND every section heading carry the
  "FOR YOUR LAWYER" framing string; no output field ever contains advice /
  signable-assurance language ("safe to sign", "this contract is fine", …);
  jurisdiction-dependent content is gated; never-fabricate — every artist-fact
  slot is verbatim, [NEEDS:x], or [ARTIST-SUPPLIED:x].

  This unit OWNS the exact Lex tool roster/count. NEVER asserts generated prose —
  scaffolds are structured; the Anthropic client is faked in the wiring tests.
"""
import ast
import asyncio
import importlib
import json
import pathlib
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import legal_data as ld
import lex_cipher_service as svc
from entity_wall_terms import assert_no_forbidden_terms

FYL = ld.FOR_YOUR_LAWYER
_ADVICE_BANS = ("safe to sign", "this contract is fine", "standard to sign",
                "fine to sign", "ok to sign", "okay to sign", "safe to put your name",
                "you should sign", "i recommend you sign")


def _run(coro):
    return asyncio.run(coro)


# ── fake Anthropic SDK shapes (wiring tests) ───────────────────────────────────

class _Block:
    def __init__(self, type, text=None, name=None, input=None, id=None):
        self.type = type
        self.text = text
        self.name = name
        self.input = input
        self.id = id


class _Resp:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class _FakeStream:
    def __init__(self, text):
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @property
    def text_stream(self):
        async def _gen():
            yield self._text
        return _gen()


def _load_main(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY",      "sk-ant-test")
    monkeypatch.setenv("BANK_CONSULT_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",                str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",           "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",        str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",            str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",     "")
    with patch("whisper.load_model", return_value=MagicMock()):
        # Same '/data'-rebake guard as test_cree_unit2 / test_nadia_unit3.
        import booking_service, phase4_service, pitch_service
        import pr_service, release_service, social_service
        for _svc_mod in (booking_service, phase4_service, pitch_service,
                         pr_service, release_service, social_service):
            importlib.reload(_svc_mod)
        import main as m
        importlib.reload(m)
    return m


def _parse_sse(body: str) -> list:
    events = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:"):].strip()))
    return events


def _all_headings(res: dict) -> list:
    return [res["header"]["title"]] + [s["heading"] for s in res["sections"]]


# ═══════════════════════════════════════════════════════════════════════════════
# lookup_legal_concepts — pure corpus read, ungated
# ═══════════════════════════════════════════════════════════════════════════════

def test_lookup_index_mode_lists_all_block_keys(monkeypatch):
    monkeypatch.delenv("IP_REGISTRY_CONNECTED", raising=False)  # no gate exists
    res = _run(svc.lookup_legal_concepts())
    assert res["status"] == "ok"
    assert res["mode"] == "index"
    assert res["agreement_types"] == list(ld.AGREEMENT_TYPES)
    assert res["clause_terms"] == list(ld.CLAUSE_GLOSSARY)
    assert res["flag_keys"] == list(ld.RED_FLAG_DOCTRINE)
    assert res["jurisdiction_keys"] == list(ld.JURISDICTION_DIVERGENCE)
    assert res["not_legal_advice"] == ld.LEX_DOCTRINE["not_legal_advice"]


def test_lookup_filters_each_block_and_returns_full_records():
    res = _run(svc.lookup_legal_concepts(
        agreement_type="recording_contract", clause_term="assignment_vs_license",
        flag_key="unsupported_360", jurisdiction_key="moral_rights"))
    assert res["mode"] == "filtered"
    assert res["agreement_types"][0]["key"] == "recording_contract"
    assert res["clauses"][0]["term"] == "assignment_vs_license"
    assert res["red_flags"][0]["flag"] == "unsupported_360"
    assert res["jurisdictions"][0]["topic"] == "moral_rights"
    assert res["not_found"] == []


def test_lookup_unknown_key_recorded_as_not_found_never_guessed():
    res = _run(svc.lookup_legal_concepts(clause_term="no_such_term"))
    assert res["clauses"] == []
    assert res["not_found"] == [{"filter": "clause_term", "value": "no_such_term", "match": None}]


def test_lookup_always_carries_boundaries_and_lawyer_doctrine():
    res = _run(svc.lookup_legal_concepts(agreement_type="nda"))
    boundary_keys = {b["key"] for b in res["boundaries"]}
    assert {"split_sheet", "royalty_registration", "lod_drafting",
            "booking_deal_memo", "grant_application"} <= boundary_keys
    assert any(p["id"] == "independent_counsel_only" for p in res["lawyer_doctrine"])


# ═══════════════════════════════════════════════════════════════════════════════
# build_legal_doc_scaffold — contract_review_brief
# ═══════════════════════════════════════════════════════════════════════════════

_FULL_BRIEF_INPUTS = {
    "agreement_type": "recording_contract",
    "jurisdiction": "United States (New York)",
    "deal_points": "One album, label funds recording, 360 on merch.",
    "contract_text": "FULL CONTRACT TEXT PROVIDED BY ARTIST",
}


def test_brief_full_inputs_ready_all_sections_no_gaps():
    res = _run(svc.build_legal_doc_scaffold("contract_review_brief", _FULL_BRIEF_INPUTS))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "contract_review_brief"
    keys = [s["key"] for s in res["sections"]]
    assert "issue_spotting_checklist" in keys
    assert "clause_glossary" in keys
    assert "red_flags" in keys
    assert "jurisdiction" in keys
    assert "artist_supplied_deal_points" in keys
    assert res["missing"] == []


def test_brief_header_and_every_section_heading_carry_for_your_lawyer():
    res = _run(svc.build_legal_doc_scaffold("contract_review_brief", _FULL_BRIEF_INPUTS))
    assert FYL in res["header"]["title"]
    assert res["header"]["framing"] == FYL
    for heading in _all_headings(res):
        assert FYL in heading, f"section heading missing framing: {heading!r}"


def test_brief_jurisdiction_withheld_and_gapped_when_unset():
    inp = dict(_FULL_BRIEF_INPUTS)
    del inp["jurisdiction"]
    res = _run(svc.build_legal_doc_scaffold("contract_review_brief", inp))
    assert "jurisdiction" not in [s["key"] for s in res["sections"]], \
        "jurisdiction-specific section must be WITHHELD without a jurisdiction"
    assert "[NEEDS:jurisdiction]" in res["missing"]


def test_brief_jurisdiction_value_rides_verbatim_when_supplied():
    res = _run(svc.build_legal_doc_scaffold("contract_review_brief", _FULL_BRIEF_INPUTS))
    juris = next(s for s in res["sections"] if s["key"] == "jurisdiction")
    assert juris["jurisdiction"] == _FULL_BRIEF_INPUTS["jurisdiction"]  # verbatim
    # every divergence note still ends with the counsel string
    for d in juris["divergences"]:
        assert d["note"].rstrip().endswith(ld.CONFIRM_WITH_LOCAL_COUNSEL + ".")


def test_brief_contract_text_missing_is_artist_supplied_marker():
    inp = dict(_FULL_BRIEF_INPUTS)
    del inp["contract_text"]
    res = _run(svc.build_legal_doc_scaffold("contract_review_brief", inp))
    assert "[ARTIST-SUPPLIED:contract_text]" in res["missing"]


def test_brief_agreement_type_missing_gaps_and_withholds_type_checklist():
    inp = {"jurisdiction": "US"}
    res = _run(svc.build_legal_doc_scaffold("contract_review_brief", inp))
    assert "[NEEDS:agreement_type]" in res["missing"]
    assert "issue_spotting_checklist" not in [s["key"] for s in res["sections"]]
    # standing glossary + red-flag checklist are still present (education).
    assert "clause_glossary" in [s["key"] for s in res["sections"]]


def test_brief_unknown_agreement_type_lists_supported_types():
    inp = {"agreement_type": "totally_made_up_deal"}
    res = _run(svc.build_legal_doc_scaffold("contract_review_brief", inp))
    note = next(n for n in res["notes"] if n["section"] == "issue_spotting_checklist")
    assert note["supported_agreement_types"] == list(ld.AGREEMENT_TYPES)
    assert "[NEEDS:agreement_type]" in res["missing"]


def test_brief_recording_deal_surfaces_ownership_control_doctrine():
    res = _run(svc.build_legal_doc_scaffold("contract_review_brief", _FULL_BRIEF_INPUTS))
    doctrine_notes = [n for n in res["notes"] if n.get("doctrine")]
    assert doctrine_notes, "record/distribution doctrine note expected"
    text = doctrine_notes[0]["doctrine"].lower()
    assert "ownership" in text and "control" in text


# ═══════════════════════════════════════════════════════════════════════════════
# build_legal_doc_scaffold — negotiation_prep_memo
# ═══════════════════════════════════════════════════════════════════════════════

def test_memo_full_inputs_ready_everything_is_questions():
    res = _run(svc.build_legal_doc_scaffold("negotiation_prep_memo", {
        "agreement_type": "management_contract",
        "priorities": "Keep publishing, short term.",
    }))
    assert res["status"] == "scaffold_ready"
    keys = [s["key"] for s in res["sections"]]
    assert "questions_for_this_agreement" in keys
    assert "typically_negotiable" in keys
    assert "carve_out_questions" in keys
    assert "artist_priorities" in keys
    # every negotiable item and lever is a QUESTION, never an asserted position.
    # (clause ask_counsel is interrogative; some carry a spec-faithful tail such
    # as reversion's "always ask for it", so we assert it CONTAINS a question.)
    negotiable = next(s for s in res["sections"] if s["key"] == "typically_negotiable")
    for q in negotiable["questions"]:
        assert "?" in q["ask_counsel"]
    # red-flag levers are strictly questions — each ends with '?'.
    carve = next(s for s in res["sections"] if s["key"] == "carve_out_questions")
    for lever_group in carve["levers"]:
        for lever in lever_group["counsel_levers"]:
            assert lever.rstrip().endswith("?")


def test_memo_priorities_missing_is_artist_supplied_marker():
    res = _run(svc.build_legal_doc_scaffold("negotiation_prep_memo", {
        "agreement_type": "management_contract"}))
    assert "[ARTIST-SUPPLIED:artist_priorities]" in res["missing"]
    assert "artist_priorities" not in [s["key"] for s in res["sections"]]


def test_memo_every_section_heading_carries_framing():
    res = _run(svc.build_legal_doc_scaffold("negotiation_prep_memo", {
        "agreement_type": "management_contract", "priorities": "x"}))
    for heading in _all_headings(res):
        assert FYL in heading


# ═══════════════════════════════════════════════════════════════════════════════
# THE ONE RULE — no advice / no signable-assurance language, ever
# ═══════════════════════════════════════════════════════════════════════════════

def _blob(res: dict) -> str:
    return json.dumps(res).lower()


def test_no_signable_assurance_language_in_any_scaffold():
    scaffolds = [
        _run(svc.build_legal_doc_scaffold("contract_review_brief", _FULL_BRIEF_INPUTS)),
        _run(svc.build_legal_doc_scaffold("contract_review_brief", {})),
        _run(svc.build_legal_doc_scaffold("negotiation_prep_memo",
                                          {"agreement_type": "recording_contract"})),
        _run(svc.build_legal_doc_scaffold("negotiation_prep_memo", {})),
    ]
    for res in scaffolds:
        blob = _blob(res)
        for banned in _ADVICE_BANS:
            assert banned not in blob, f"assurance language leaked: {banned!r}"


def test_header_states_not_advice_and_never_signable():
    res = _run(svc.build_legal_doc_scaffold("contract_review_brief", _FULL_BRIEF_INPUTS))
    assert res["header"]["not_legal_advice"] == ld.LEX_DOCTRINE["not_legal_advice"]
    assert res["header"]["never_signable"] == ld.LEX_DOCTRINE["never_signable"]


def test_unknown_doc_type_returns_structured_error():
    res = _run(svc.build_legal_doc_scaffold("mystery_doc", {}))
    assert res["status"] == "unknown_doc_type"
    assert res["supported_doc_types"] == list(svc.DOC_TYPES)


def test_service_layer_is_entity_wall_clean():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════════════════
# AST — the service imports no LLM SDK and never calls messages.create
# ═══════════════════════════════════════════════════════════════════════════════

def test_service_imports_no_anthropic_and_no_messages_create():
    source = pathlib.Path(svc.__file__).read_text(encoding="utf-8")
    assert "messages.create" not in source
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "anthropic" not in name.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Roster / tool counts (THIS UNIT OWNS THEM) + dispatch wiring
# ═══════════════════════════════════════════════════════════════════════════════

def test_lex_tool_roster_is_exactly_the_two_docwriter_tools(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.LEX_CIPHER_TOOLS]
    assert names == ["lookup_legal_concepts", "build_legal_doc_scaffold"]


def test_lookup_tool_enums_match_the_corpus(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    lookup = next(t for t in m.LEX_CIPHER_TOOLS if t["name"] == "lookup_legal_concepts")
    props = lookup["input_schema"]["properties"]
    assert props["agreement_type"]["enum"] == list(ld.AGREEMENT_TYPES)
    assert props["clause_term"]["enum"] == list(ld.CLAUSE_GLOSSARY)
    assert props["flag_key"]["enum"] == list(ld.RED_FLAG_DOCTRINE)
    assert props["jurisdiction_key"]["enum"] == list(ld.JURISDICTION_DIVERGENCE)
    assert "required" not in lookup["input_schema"]  # all filters optional


def test_build_tool_requires_doc_type_with_docwriter_enum(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    build = next(t for t in m.LEX_CIPHER_TOOLS if t["name"] == "build_legal_doc_scaffold")
    assert build["input_schema"]["required"] == ["doc_type"]
    assert build["input_schema"]["properties"]["doc_type"]["enum"] == list(svc.DOC_TYPES)


def test_dispatch_not_gated_and_returns_three_tuple(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("IP_REGISTRY_CONNECTED", raising=False)
    result, summary, rnc = _run(m._execute_lex_cipher_tool(
        "build_legal_doc_scaffold",
        {"doc_type": "contract_review_brief", "inputs": {"agreement_type": "nda"}},
        "artist-1"))
    assert result["status"] == "scaffold_ready"
    assert rnc is False  # gate retired — always False
    assert "section(s)" in summary["result"]


def test_dispatch_unknown_tool_is_structured(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    result, summary, rnc = _run(m._execute_lex_cipher_tool("file_ip_registration", {}, "a"))
    assert result["error"] == "unknown_tool"
    assert rnc is False
