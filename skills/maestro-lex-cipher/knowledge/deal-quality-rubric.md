# PLMKR Deal / Document Quality Rubric
Version: v1.0 — Eight-Dimension Deal/Document Quality Model (2026-06-20)
Status: SCOREABLE — composite is PROVISIONAL until the unlock condition is met.

This rubric evaluates the legal quality of a music-industry agreement or deal
structure. Its scores identify legal-risk dimensions and their severity. They do
NOT constitute legal opinions, legal advice, or negotiation recommendations.
Every output using this rubric ends with: *"Route to qualified entertainment
counsel for execution, negotiation, and legal opinion."*

---

## Provisional Composite Discipline

This rubric's composite output is **PROVISIONAL** until an outcome corpus of ≥30
outcome-checked deal evaluations exists in `feedback/outcomes/`. Until then:

1. Score each dimension A+–F with per-dimension justification citing evaluable
   sub-signals.
2. Calculate the provisional composite (formula below).
3. Report it with the label: **PROVISIONAL COMPOSITE**.
4. State the unlock condition in every output: *"This composite is PROVISIONAL —
   unlock condition: ≥30 outcome-checked deal evaluations in feedback/outcomes/"*
5. The provisional composite is secondary to per-dimension grades and is LOCKED
   from client-facing use until the unlock condition is met.
6. Do NOT present the provisional composite as calibrated or comparable across
   deals.

---

## The Domain-Constraint Reminder (Required Before Every Evaluation)

**Drafts and flags — never advises. Qualified counsel signs off.**

This rubric scores legal risk; it does not produce legal opinions, legal advice,
or negotiation recommendations. Every output ends with the counsel footer.

---

## Eight-Dimension Model

| # | Dimension | Weight | Legal-Risk Connection |
|---|-----------|--------|-----------------------|
| 1 | **Rights Grant Clarity** | **0.18** | Foundation: undefined rights scope creates licensing uncertainty and dispute risk |
| 2 | **Compensation Structure Clarity** | **0.16** | Revenue: ambiguous payment terms are the primary source of royalty disputes |
| 3 | **Recoupment / Cost Transparency** | **0.14** | Economics: undefined cost deductions produce unverifiable recoupment accounts |
| 4 | **Exit / Reversion Provisions** | **0.13** | Term: absence of exit mechanisms creates indefinite-obligation risk |
| 5 | **Audit Rights Adequacy** | **0.13** | Enforcement: audit rights are the only mechanism to verify accounting obligations |
| 6 | **Warranties & Representations** | **0.12** | IP ownership: absence creates downstream chain-of-title risk and indemnification exposure |
| 7 | **Dispute Resolution Clarity** | **0.08** | Process: undefined dispute resolution defaults to expensive litigation |
| 8 | **Red-Flag Clause Absence** | **0.06** | Baseline: known high-risk clauses, when present, cap the overall evaluation |
|   | **Total** | **1.00** | |

---

## Anti-Fake-Precision Mechanics

Each sub-signal within a dimension is classified as:
- **SOURCED** — verifiable from the document text itself (clause present, term
  defined, rate stated).
- **ABSENT** — the provision is not found in the document (absence is evaluable
  — it is a gap).
- **AMBIGUOUS** — provision exists but is undefined, circular, or subject to
  conflicting interpretation.
- **NOT EVALUABLE** — required information absent from context (e.g., "industry
  standard" referenced but not defined without market data).

**Grading rules:**
1. Grade a sub-signal only where evidence exists in the document.
2. Provision missing entirely → mark **ABSENT** (typically a negative signal).
3. Provision present but undefined → mark **AMBIGUOUS**.
4. Evaluation requires external data not in the document → mark **NOT
   EVALUABLE** and state the minimum required data.
5. Each dimension receives a letter grade (A+ through F).

---

## Letter Grade → Numeric Equivalent

| Grade | Numeric | Grade | Numeric |
|-------|---------|-------|---------|
| A+ | 10.0 | C+ | 6.5 |
| A | 9.5 | C | 6.0 |
| A– | 9.0 | C– | 5.5 |
| B+ | 8.5 | D+ | 5.0 |
| B | 8.0 | D | 4.5 |
| B– | 7.5 | D– | 4.0 |
| C+ | 7.0 | F | 2.0 |

---

## Hard Gates

Four hard gates apply regardless of dimension scores. Any triggered gate reduces
the overall evaluation and must be disclosed in every output referencing the
document.

**HG-1 — Absent Rights Grant (objective):** if the agreement contains no
identifiable rights-grant clause — no definition of what rights are transferred,
licensed, or retained — the evaluation is INCOMPLETE for Rights Grant Clarity (D
forced).
- CLEAR: rights grant present, terms defined (even if inadequately).
- TRIGGERED: no rights-grant clause present, or grant entirely circular/undefined.

**HG-2 — Missing Audit Rights:** if the agreement contains no audit-rights
provision, D is forced for Audit Rights Adequacy. An agreement without audit
rights provides no mechanism to verify royalty accounting, regardless of how
favorable the stated rates appear.
- CLEAR: audit rights present with defined scope and window.
- TRIGGERED: audit rights absent; or present but window shorter than 12 months
  from statement date (industry-convention default threshold).

**HG-3 — Unresolved IP Ownership Gap:** if the agreement involves IP transfer or
license and the chain of title cannot be established from the document and stated
context, D is forced for Warranties & Representations.
- CLEAR: chain of title established within stated context; ownership warranties
  present.
- TRIGGERED: ownership not established; no IP-ownership warranties; or prior
  chain contains a blocking defect.

**HG-4 — Active Red-Flag Clause Present:** if the agreement contains one or more
identified red-flag clauses (Dimension 8 table), the Red-Flag Clause Absence
dimension is D or lower and this must be disclosed prominently. The agent does
not recommend proceeding or not proceeding with a red-flag clause present — that
is a legal-strategy determination for qualified counsel. The agent identifies the
clause, explains what it does, and routes.
- CLEAR: no identified red-flag clauses present.
- TRIGGERED: one or more present — list each with clause reference.

---

## Dimension Sub-Signals & Grade Anchors

### Dimension 1 — Rights Grant Clarity (0.18)
Sub-signals: territory defined · term defined · media defined · exclusivity
stated · reserved rights stated · rights scope defined.
- **A:** all six sourced and specific; commercially operable without
  interpretation.
- **C:** three to four sourced; some licensing uncertainty.
- **F:** rights grant absent or entirely circular (HG-1 triggered).

### Dimension 2 — Compensation Structure Clarity (0.16)
Sub-signals: payment type · royalty base (SRLP/PPD/net/gross) · deductions ·
accounting periods · payment timing · reserve provisions.
- **A:** all six sourced; no deduction categories undefined; payment timeline
  certain.
- **D:** payment type defined but rate/base undefined; no accounting period.
- **F:** compensation not defined in the agreement.

### Dimension 3 — Recoupment / Cost Transparency (0.14)
Sub-signals: recoupable-cost categories enumerated · cross-collateralization
present/scope · recoupment calculation method · reserves-against-recoupment.
- **A:** recoupable costs fully enumerated; cross-collateralization absent or
  scoped; calculation basis defined.
- **D:** open-ended recoupable-cost definition ("all costs incurred by the
  label…"); cross-collateralization unrestricted; calculation undefined.
- **F:** recoupment provisions entirely absent where advances are paid.

### Dimension 4 — Exit / Reversion Provisions (0.13)
Sub-signals: termination for cause · termination for convenience · reversion
trigger conditions · post-term rights/obligations · cure period on breach.
- **A:** termination for cause and convenience defined; reversion conditions
  clear; post-term provisions stated.
- **D:** no defined termination right; no reversion clause; open-ended obligation.
- **F:** purports to bind the artist in perpetuity with no exit or reversion.

### Dimension 5 — Audit Rights Adequacy (0.13)
Sub-signals: audit-rights clause present · scope (books/records/sub-licensees) ·
window from statement date · notice requirement · cost allocation · frequency cap.
- **A:** present; scope includes books, records, and sub-licensee records;
  window ≥ 2 years; notice and cost allocation defined.
- **D:** present but window shorter than 12 months from statement (HG-2
  triggered), or audit rights absent (HG-2 triggered).
- **F:** no audit-rights clause; or audit expressly restricted to a 6-month
  window or shorter.

### Dimension 6 — Warranties & Representations (0.12)
Sub-signals: IP-ownership warranty · non-infringement warranty · indemnification
scope · indemnification proportionality (cap vs. unlimited) · survival.
- **A:** ownership and non-infringement warranties; proportionate indemnification
  with cap; representations survive.
- **D:** no IP-ownership warranty; no indemnification; chain relies on implied
  warranties only.
- **F:** active IP-ownership dispute present without disclosure.

### Dimension 7 — Dispute Resolution Clarity (0.08)
Sub-signals: governing law · forum/jurisdiction · mandatory vs. optional
arbitration · fee/cost allocation · confidentiality of proceedings.
- **A:** governing law, forum, arbitration rules, cost allocation, and
  confidentiality all defined.
- **D:** no governing law; no forum; defaults to state court with no cost
  allocation.
- **F:** agreement excludes all dispute-resolution mechanisms by express
  provision.

### Dimension 8 — Red-Flag Clause Absence (0.06)

| Clause | What it does | Severity | HG-4 trigger? |
|--------|-------------|----------|--------------|
| Open-ended recoupable cost definition | "All costs incurred by label" without enumeration | HIGH — unlimited recoupable scope | Yes |
| Audit window shorter than 12 months | Practical waiver of audit rights | HIGH — accounting unenforceable | Yes |
| Perpetual term without reversion trigger | Indefinite obligation, no exit | HIGH — career-binding | Yes |
| Cross-collateralization without scope limit | All advances netted across all projects | HIGH — structurally non-recoupable | No (document) |
| MFN clause with no defined comparator | "Most favored" without specifying compared to what | MEDIUM — unenforceable trigger | No |
| Controlled-composition clause at 75% of statutory | Reduces mechanical income on the writer's own songs | MEDIUM — income reduction | No |
| Morals clause with purely subjective trigger | Counterparty may terminate at sole discretion | MEDIUM — unilateral termination without cause | No |
| WFH language applied to musical composition | Legally ineffective; creates dispute risk | MEDIUM — litigation uncertainty | No |
| Re-recording restriction without term limit | Perpetual restriction on covering own songs | MEDIUM — limits future rights | No |
| No liability cap in performance agreement | Unlimited exposure for venue incidents | HIGH — personal liability | Yes |

- **A+:** no red-flag clauses identified.
- **C:** one or more medium-severity clauses without adequate negotiation visible.
- **D:** one or more high-severity clauses present (HG-4 triggered).
- **F:** multiple high-severity clauses; document systematically disadvantageous.

---

## Provisional Composite Calculation

```
Provisional Composite =
  (D1 × 0.18) + (D2 × 0.16) + (D3 × 0.14) + (D4 × 0.13) +
  (D5 × 0.13) + (D6 × 0.12) + (D7 × 0.08) + (D8 × 0.06)
```

**Hard-gate override:** if any hard gate is triggered, the composite is still
calculated, but the output must prominently disclose the triggered gate(s) before
presenting the composite. No composite obscures a triggered hard gate.

**Composite interpretation (provisional, directional bands):**
- 8.5–10.0: professionally negotiated; low identified legal-risk exposure.
- 7.0–8.4: adequate baseline; notable gaps to resolve pre-execution.
- 5.5–6.9: significant gaps; qualified-counsel review required before proceeding.
- 4.0–5.4: materially deficient; high legal risk.
- Below 4.0: critically deficient; multiple hard gates or systemic risk.

These bands describe legal-risk severity — they are not a recommendation to
proceed or not proceed. That determination is legal strategy and routes to
qualified counsel.

**Unlock condition:** the composite scale and thresholds are PROVISIONAL until
≥30 outcome-checked deal evaluations exist in feedback/outcomes/. Until then the
composite is directional context only, not a calibrated benchmark.

---

## Risk Classification (Descriptive, Not Prescriptive)

Map the composite band to a descriptive legal-risk tier. This labels severity; it
does not tell the user whether to sign:

| Composite band | Risk classification |
|----------------|---------------------|
| 8.5–10.0 | LOW_RISK |
| 7.0–8.4 | NOTABLE_GAPS |
| 5.5–6.9 | SIGNIFICANT_GAPS |
| 4.0–5.4 | MATERIALLY_DEFICIENT |
| Below 4.0 | CRITICALLY_DEFICIENT |

Any triggered hard gate is disclosed alongside the classification regardless of
band.
