# PLMKR Legal Output Templates
Version: v1.0 — Lex-Cipher output templates (2026-06-20)
Status: ACTIVE — four output shapes governed by the deal-quality rubric.

**Binding domain constraint (all templates):** this agent drafts and flags — it
never advises. Every template output ends with: *"Route to qualified
entertainment counsel for execution, negotiation, and legal opinion."* Omitting
this footer is a domain-constraint violation.

**Negotiation handling (binding, all templates):** the agent never states a
target negotiation position or a specific term to seek (e.g., "negotiate a 2-year
audit window," "eliminate the recoupable-cost tail," "rate floor and cap"). In any
field describing red-flag remedies, counsel actions, "what would change this
answer," or NEXT BEST ACTION, the agent (a) names the deficiency and what the
clause does, and (b) routes the negotiation explicitly to the management function
(negotiation strategy / what position to take) plus qualified counsel (legal
execution). It identifies and routes — it does not prescribe the position.

**Anti-bloat rule:** modules attach when they change a decision, not to look
thorough. A quick red-flag identification does not ship with a full risk register.

**NOT EVALUABLE rule:** if a required document or data element is absent, mark NOT
EVALUABLE and state the minimum required data.

**NOT QUOTABLE discipline:** specific deal terms provided by the owner are
CLIENT-SPECIFIC — NOT QUOTABLE in output shared beyond the current session.

**Provisional composite rule:** all rubric composites are PROVISIONAL until ≥30
outcome-checked evaluations exist in feedback/outcomes/.

---

## Module Table

| Template | Rubric Scores | Risk Register | Alternatives | Next Best Action |
|----------|--------------|---------------|--------------|------------------|
| 1 — Contract/Deal Review Report | ✓ (8 dimensions) | ✓ | ✓ | ✓ |
| 2 — Copyright Infringement Preliminary Analysis | ✗ | ✓ (litigation risk factors) | ✓ | ✓ |
| 3 — IP Chain-of-Title Checklist | ✗ | ✓ (defect classification) | ✓ | ✓ |
| 4 — Business Entity Identification | ✗ | ✓ (entity-level risk factors) | ✓ | ✓ |

---

## Template 1 — Contract / Deal Review Report

**When to use:** formal review of any music-industry agreement — recording
contract, publishing deal, management agreement, sync license, endorsement deal,
performance agreement.

```
# CONTRACT / DEAL REVIEW REPORT
Date: [YYYY-MM-DD]
Rubric: PLMKR Deal/Document Quality Rubric v1.0 (8 dimensions)
Agreement type: [recording / publishing / management / sync license /
                 brand endorsement / performance / other]
Parties: [describe neutrally]
NOT QUOTABLE flag: [add if client-specific terms are present]

## Part 1 — Agreement Identification
- Deal type classification (apply the Deal-Type Classification Tree)
- Subtype, effective date, term (defined / perpetual / option-based)
- Rights granted (territory, term, media, exclusivity)
- Rights retained / reserved
- Rights NOT addressed (gaps identified)

## Part 2 — Eight-Dimension Rubric Assessment
| Dimension | Weight | Grade | Numeric | Sub-signals (SOURCED/ABSENT/AMBIGUOUS/NOT EVALUABLE) | Hard Gate | Confidence |
| D1 Rights Grant Clarity     | 0.18 | … | … | … | HG-1 … | … |
| D2 Compensation Structure   | 0.16 | … | … | … | —      | … |
| D3 Recoupment/Cost          | 0.14 | … | … | … | —      | … |
| D4 Exit/Reversion           | 0.13 | … | … | … | —      | … |
| D5 Audit Rights             | 0.13 | … | … | … | HG-2 … | … |
| D6 Warranties/Representations | 0.12 | … | … | … | HG-3 … | … |
| D7 Dispute Resolution       | 0.08 | … | … | … | —      | … |
| D8 Red-Flag Clause Absence  | 0.06 | … | … | … | HG-4 … | … |

Hard gates: HG-1, HG-2, HG-3, HG-4 — each CLEAR or TRIGGERED with reason.
PROVISIONAL COMPOSITE: [value] — "unlock condition: ≥30 outcome-checked
evaluations in feedback/outcomes/"
Risk classification: [LOW_RISK / NOTABLE_GAPS / SIGNIFICANT_GAPS /
MATERIALLY_DEFICIENT / CRITICALLY_DEFICIENT]

## Part 3 — Red-Flag Clause Table
| Clause | Location | What it does | Severity | Routing for counsel review |
(name the deficiency; do NOT state a target outcome, fix, or position)

## Part 4 — NOT EVALUABLE Sub-Signals
| Sub-signal | Why NOT EVALUABLE | Minimum data required |

## Part 5 — Scope-Fence Routing
| Topic identified | Routes to (management / publishing / finance / qualified counsel) |

## Part 6 — Alternatives & Next Best Action
- Alternatives: what condition would change the risk picture (descriptive, not a
  prescribed position).
- Next best action (24–72h): the single most useful documentation or counsel step
  — routes negotiation to the management function + qualified counsel.

Route to qualified entertainment counsel for execution, negotiation, and legal opinion.
```

---

## Template 2 — Copyright Infringement Preliminary Analysis

```
# PRELIMINARY INFRINGEMENT ANALYSIS — NOT A LEGAL OPINION
Date: [YYYY-MM-DD] · Territory: [state explicitly; default "In the US…"]

Part 1 — Access factors (opportunity to hear the original)
Part 2 — Substantial similarity
  - Extrinsic: protected musical elements compared (exclude unprotected
    elements — common chords, scales, genre conventions)
  - Intrinsic: total concept and feel (trier-of-fact question)
Litigation-risk factors register (identify; do not predict outcome)
Currency note: verify against current case law before reliance.
Alternatives / Next best action: route to copyright litigation counsel.

Route to qualified entertainment counsel for execution, negotiation, and legal opinion.
```

---

## Template 3 — IP Chain-of-Title Checklist

```
# IP CHAIN-OF-TITLE CHECKLIST
Date: [YYYY-MM-DD]
For each claimed right: executed assignment present? · split sheet present? ·
registration consistent? · WFH basis qualifying? · competing claims? · dispute
notices?
Defect classification per item: MINOR / BLOCKING / LITIGATION RISK
NOT EVALUABLE items + minimum data required.
Alternatives / Next best action: route resolution to qualified counsel.

Route to qualified entertainment counsel for execution, negotiation, and legal opinion.
```

---

## Template 4 — Business Entity Identification

```
# BUSINESS ENTITY IDENTIFICATION
Date: [YYYY-MM-DD] · Territory: [state explicitly]
Identify candidate entity types and what each does (loan-out, partnership/band
agreement, co-publishing/admin entity). Entity-level risk factors register.
Selection for this situation routes to qualified counsel and tax advisors — the
agent identifies, it does not recommend a choice.
Alternatives / Next best action.

Route to qualified entertainment counsel for execution, negotiation, and legal opinion.
```
