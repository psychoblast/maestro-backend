"""
PLMKR Lex-Cipher — legal-education DOC-WRITER service (mock-first, Option B).

Backs the Lex-Cipher (Entertainment Lawyer) agent's tool_use loop in
/api/chat_stream (see LEX_CIPHER_TOOLS in main.py). Lex does NOT give legal
advice and does NOT produce signable contracts. These functions let the agent
take one real action: assemble organized preparation material FOR THE ARTIST'S
OWN LAWYER — a structured lookup over the legal-education corpus, and compact
doc-scaffold ingredients the agent turns into prose in its own turn.

THE ONE RULE ABOVE ALL (enforced here and in tests):
  - Lex NEVER gives legal advice and NEVER produces a signable contract.
  - Every scaffold is preparation material for the artist's own lawyer. The
    scaffold header and EVERY section heading carry the "FOR YOUR LAWYER"
    framing string.
  - No output asserts a contract is safe, fine, or standard to sign.
  - Jurisdiction-dependent content is WITHHELD unless a jurisdiction is supplied
    (emitting [NEEDS:jurisdiction]); when supplied it still ends by telling the
    artist to confirm with local counsel (the corpus note carries that string).
  - NEVER fabricate: every artist-fact slot is the supplied input VERBATIM, a
    [NEEDS:<x>] gap, or an [ARTIST-SUPPLIED:<x>] marker — never invented. Corpus
    content (questions, patterns, mechanisms) is pulled verbatim from legal_data.

DOC-WRITER OPTION B (Cree / Nadia / Reed precedent):
  build_legal_doc_scaffold returns COMPACT ingredients only — matched checklist
  items, glossary questions, red-flag levers, jurisdiction flags, aggregated
  gaps. The AGENT writes the prose in its turn. There is ZERO model-call in this
  module (no Anthropic SDK import, no create-message call) — AST-enforced by tests.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live legal databases, no filing APIs, no LLM.
  - NO secrets are read or embedded, and there is NO connection gate: both tools
    are pure corpus-read / data-scaffold tools that need no connected account
    (the old IP-registry filing action and its env gate are RETIRED — filing/
    registration is ledger-lock's domain, not Lex's).
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import legal_data


# ── Framing + gap markers (data, not logic) ───────────────────────────────────
FOR_YOUR_LAWYER = legal_data.FOR_YOUR_LAWYER  # "FOR YOUR LAWYER"

_GAP = "[NEEDS:{}]"
_ARTIST_SUPPLIED = "[ARTIST-SUPPLIED:{}]"

# The two scaffolds this DOC-WRITER produces.
DOC_TYPES = ("contract_review_brief", "negotiation_prep_memo")

# Standing framing surfaced on every scaffold so no output can be read as advice
# or as a signable instrument.
_NOT_LEGAL_ADVICE = legal_data.LEX_DOCTRINE["not_legal_advice"]
_NEVER_SIGNABLE = legal_data.LEX_DOCTRINE["never_signable"]


def _heading(text: str) -> str:
    """Every section heading carries the FOR YOUR LAWYER framing (THE ONE RULE)."""
    return f"{text} — {FOR_YOUR_LAWYER}"


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
# lookup_legal_concepts — structured lookup/filter over the legal_data corpus.
# Pure corpus read; NOT gated. No legal judgment is made about the artist's own
# deal — this returns education blocks the agent (and their lawyer) apply.
# ═══════════════════════════════════════════════════════════════════════════════
async def lookup_legal_concepts(
    agreement_type: str = "",
    clause_term: str = "",
    flag_key: str = "",
    jurisdiction_key: str = "",
) -> dict:
    """Filter the four corpus blocks by any of agreement type / clause term /
    flag key / jurisdiction key.

    With NO filter, returns a compact index of the available keys per block so the
    agent can browse. With filters, returns the matched full records; any filter
    that matches nothing is recorded in ``not_found`` (value stays absent, never
    guessed). The standing framing (not-advice note, lawyer doctrine, boundaries)
    rides through on every response. Pure — no I/O, no gate.
    """
    at = _norm(agreement_type)
    ct = _norm(clause_term)
    fk = _norm(flag_key)
    jk = _norm(jurisdiction_key)
    any_filter = bool(at or ct or fk or jk)

    result = {
        "status": "ok",
        "not_legal_advice": _NOT_LEGAL_ADVICE,
        "lawyer_doctrine": [dict(p) for p in legal_data.LAWYER_DOCTRINE],
        "boundaries": [dict(b) for b in legal_data.OUT_OF_SCOPE.values()],
    }

    if not any_filter:
        # Browse mode — index of keys only, kept compact.
        result["mode"] = "index"
        result["agreement_types"] = list(legal_data.AGREEMENT_TYPES)
        result["clause_terms"] = list(legal_data.CLAUSE_GLOSSARY)
        result["flag_keys"] = list(legal_data.RED_FLAG_DOCTRINE)
        result["jurisdiction_keys"] = list(legal_data.JURISDICTION_DIVERGENCE)
        result["agreement_doctrine"] = dict(legal_data.AGREEMENT_DOCTRINE)
        result["red_flag_notes"] = dict(legal_data.RED_FLAG_DOCTRINE_NOTES)
        return result

    result["mode"] = "filtered"
    not_found = []

    result["agreement_types"] = []
    if at:
        rec = legal_data.AGREEMENT_TYPES.get(at)
        if rec:
            result["agreement_types"].append(dict(rec))
            result["agreement_doctrine"] = dict(legal_data.AGREEMENT_DOCTRINE)
        else:
            not_found.append({"filter": "agreement_type", "value": at, "match": None})

    result["clauses"] = []
    if ct:
        rec = legal_data.CLAUSE_GLOSSARY.get(ct)
        if rec:
            result["clauses"].append(dict(rec))
        else:
            not_found.append({"filter": "clause_term", "value": ct, "match": None})

    result["red_flags"] = []
    if fk:
        rec = legal_data.RED_FLAG_DOCTRINE.get(fk)
        if rec:
            result["red_flags"].append(dict(rec))
            result["red_flag_notes"] = dict(legal_data.RED_FLAG_DOCTRINE_NOTES)
        else:
            not_found.append({"filter": "flag_key", "value": fk, "match": None})

    result["jurisdictions"] = []
    if jk:
        rec = legal_data.JURISDICTION_DIVERGENCE.get(jk)
        if rec:
            result["jurisdictions"].append(dict(rec))
        else:
            not_found.append({"filter": "jurisdiction_key", "value": jk, "match": None})

    result["not_found"] = not_found
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# build_legal_doc_scaffold — OPTION B: compact ingredients only, agent writes
# prose. NOT gated. THE ONE RULE rides through every branch.
# ═══════════════════════════════════════════════════════════════════════════════
async def build_legal_doc_scaffold(doc_type: str = "", inputs: dict = None) -> dict:
    """Build compact ingredients for one legal-prep document; Lex writes the prose.

    Two doc types — ``contract_review_brief`` and ``negotiation_prep_memo``.
    Every section heading carries the FOR YOUR LAWYER framing; the scaffold header
    states plainly that this is not advice and not signable. No corpus content is
    a legal judgment about the artist's specific deal — the checklist, glossary,
    and red-flag patterns are the standing education toolkit the agent and the
    lawyer apply. Every artist-fact slot is verbatim, a [NEEDS:<x>] gap, or an
    [ARTIST-SUPPLIED:<x>] marker; all such markers aggregate into ``missing``.
    Unknown doc_type -> structured error listing the supported types.
    """
    dt = _norm(doc_type).lower()
    inputs = dict(inputs) if isinstance(inputs, dict) else {}
    if dt == "contract_review_brief":
        return _scaffold_contract_review_brief(inputs)
    if dt == "negotiation_prep_memo":
        return _scaffold_negotiation_prep_memo(inputs)
    return {
        "status": "unknown_doc_type",
        "doc_type": dt or "(missing)",
        "supported_doc_types": list(DOC_TYPES),
        "message": ("Unsupported doc_type. Supported: " + ", ".join(DOC_TYPES) + "."),
    }


def _header(title: str) -> dict:
    """Scaffold header — carries the framing string and the not-advice / never-
    signable notes verbatim from the corpus."""
    return {
        "title": _heading(title),
        "framing": FOR_YOUR_LAWYER,
        "not_legal_advice": _NOT_LEGAL_ADVICE,
        "never_signable": _NEVER_SIGNABLE,
    }


def _glossary_section() -> dict:
    """The standing clause glossary as questions to walk with counsel."""
    return {
        "key": "clause_glossary",
        "heading": _heading("Clause glossary — terms to raise with counsel"),
        "terms": [
            {"term": t, "mechanism": r["mechanism"], "ask_counsel": r["ask_counsel"]}
            for t, r in legal_data.CLAUSE_GLOSSARY.items()
        ],
    }


def _red_flag_section() -> dict:
    """The standing red-flag checklist — patterns + levers framed as questions."""
    return {
        "key": "red_flags",
        "heading": _heading("Red-flag patterns to check for"),
        "flags": [
            {"flag": f, "pattern": r["pattern"], "why_it_matters": r["why_it_matters"],
             "counsel_levers": list(r["counsel_levers"])}
            for f, r in legal_data.RED_FLAG_DOCTRINE.items()
        ],
        "notes": dict(legal_data.RED_FLAG_DOCTRINE_NOTES),
    }


def _scaffold_contract_review_brief(inputs: dict) -> dict:
    """Ingredients for a brief the artist hands their lawyer alongside the actual
    contract. Type-specific issue-spotting from the corpus; standing glossary +
    red-flag checklist; jurisdiction section WITHHELD unless a jurisdiction is
    supplied; the actual contract text is [ARTIST-SUPPLIED:contract_text]."""
    missing: list = []
    notes: list = []
    sections: list = []

    # 1 — agreement-type-specific issue-spotting checklist (verbatim from corpus).
    at_raw = inputs.get("agreement_type")
    at = _norm(at_raw).lower()
    type_rec = legal_data.AGREEMENT_TYPES.get(at)
    if type_rec:
        sections.append({
            "key": "issue_spotting_checklist",
            "heading": _heading(f"Issue-spotting checklist — {type_rec['display_name']}"),
            "agreement_type": type_rec["key"],
            "parties": type_rec["parties"],
            "purpose": type_rec["purpose"],
            "questions_for_counsel": list(type_rec["core_questions"]),
            "key_clauses_to_examine": list(type_rec["typical_key_clauses"]),
            "owning_department": type_rec["owning_department"],
        })
        if at in ("recording_contract", "distribution_deal"):
            notes.append({
                "section": "issue_spotting_checklist",
                "doctrine": legal_data.AGREEMENT_DOCTRINE["record_deal_vs_distribution_deal"],
            })
    else:
        gap = _GAP.format("agreement_type")
        missing.append(gap)
        note = {"section": "issue_spotting_checklist", "marker": gap}
        if not _missing(at_raw):
            note["note"] = (f"agreement_type '{_norm(at_raw)}' is not in the corpus — "
                            "supply a supported type; the type-specific checklist is withheld")
            note["supported_agreement_types"] = list(legal_data.AGREEMENT_TYPES)
        else:
            note["note"] = "agreement_type not supplied — the type-specific checklist is withheld"
        notes.append(note)

    # 2 + 3 — standing glossary + red-flag checklist (education, always included).
    sections.append(_glossary_section())
    sections.append(_red_flag_section())

    # 4 — jurisdiction: WITHHELD unless supplied (THE ONE RULE — jurisdiction gate).
    juris_raw = inputs.get("jurisdiction")
    if _missing(juris_raw):
        gap = _GAP.format("jurisdiction")
        missing.append(gap)
        notes.append({
            "section": "jurisdiction",
            "marker": gap,
            "note": ("jurisdiction-specific issues are WITHHELD until a jurisdiction is "
                     "supplied; jurisdiction-dependent law cannot be prepared without it"),
        })
    else:
        juris = _norm(juris_raw)
        sections.append({
            "key": "jurisdiction",
            "heading": _heading(f"Jurisdiction-specific issues — {juris}"),
            "jurisdiction": juris,  # artist-supplied, verbatim
            "divergences": [
                {"topic": r["topic"], "mechanism": r["mechanism"], "note": r["note"]}
                for r in legal_data.JURISDICTION_DIVERGENCE.values()
            ],
        })

    # 5 — artist-supplied specifics: the actual contract + free-text deal points.
    if _missing(inputs.get("contract_text")):
        marker = _ARTIST_SUPPLIED.format("contract_text")
        missing.append(marker)
        notes.append({
            "section": "contract_text",
            "marker": marker,
            "note": ("the actual contract text is supplied by the artist to their lawyer — "
                     "Lex does not draft, hold, or summarize it in place of the document"),
        })
    dp = inputs.get("deal_points")
    if _missing(dp):
        marker = _ARTIST_SUPPLIED.format("deal_points")
        missing.append(marker)
        notes.append({"section": "deal_points", "marker": marker,
                      "note": "artist-supplied deal points not provided — none invented"})
    else:
        sections.append({
            "key": "artist_supplied_deal_points",
            "heading": _heading("Artist-supplied deal points"),
            "content": dp,  # verbatim
        })

    return _finish(_header("Contract review brief"), "contract_review_brief",
                   sections, missing, notes)


def _scaffold_negotiation_prep_memo(inputs: dict) -> dict:
    """Ingredients for a memo of QUESTIONS to bring to counsel — what is typically
    negotiable per the corpus and carve-outs to raise. Nothing is asserted as a
    safe position; every item is a question. Artist priorities ride verbatim or
    are marked [ARTIST-SUPPLIED:artist_priorities]."""
    missing: list = []
    notes: list = []
    sections: list = []

    # 1 — agreement-type-specific negotiation questions (verbatim from corpus).
    at_raw = inputs.get("agreement_type")
    at = _norm(at_raw).lower()
    type_rec = legal_data.AGREEMENT_TYPES.get(at)
    if type_rec:
        sections.append({
            "key": "questions_for_this_agreement",
            "heading": _heading(f"Questions to raise — {type_rec['display_name']}"),
            "agreement_type": type_rec["key"],
            "questions_for_counsel": list(type_rec["core_questions"]),
        })
    else:
        gap = _GAP.format("agreement_type")
        missing.append(gap)
        note = {"section": "questions_for_this_agreement", "marker": gap}
        if not _missing(at_raw):
            note["note"] = (f"agreement_type '{_norm(at_raw)}' is not in the corpus — "
                            "supply a supported type; type-specific questions are withheld")
            note["supported_agreement_types"] = list(legal_data.AGREEMENT_TYPES)
        else:
            note["note"] = "agreement_type not supplied — type-specific questions are withheld"
        notes.append(note)

    # 2 — what is typically negotiable, per the corpus: every clause question.
    sections.append({
        "key": "typically_negotiable",
        "heading": _heading("Typically negotiable — questions to bring to counsel"),
        "questions": [
            {"about": t, "ask_counsel": r["ask_counsel"]}
            for t, r in legal_data.CLAUSE_GLOSSARY.items()
        ],
    })

    # 3 — carve-out / red-flag negotiation levers, all framed as questions.
    sections.append({
        "key": "carve_out_questions",
        "heading": _heading("Carve-outs and red-flag levers — questions to raise"),
        "levers": [
            {"flag": f, "counsel_levers": list(r["counsel_levers"])}
            for f, r in legal_data.RED_FLAG_DOCTRINE.items()
        ],
        "notes": dict(legal_data.RED_FLAG_DOCTRINE_NOTES),
    })

    # 4 — artist priorities: verbatim or [ARTIST-SUPPLIED:artist_priorities].
    priorities = inputs.get("priorities")
    if _missing(priorities):
        marker = _ARTIST_SUPPLIED.format("artist_priorities")
        missing.append(marker)
        notes.append({"section": "artist_priorities", "marker": marker,
                      "note": "artist priorities not supplied — none invented"})
    else:
        sections.append({
            "key": "artist_priorities",
            "heading": _heading("Artist priorities to focus the questions"),
            "content": priorities,  # verbatim
        })

    return _finish(_header("Negotiation prep memo"), "negotiation_prep_memo",
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
