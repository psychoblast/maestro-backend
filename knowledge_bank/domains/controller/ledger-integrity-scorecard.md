# Ledger Integrity & Controls Scorecard

The scoring instrument for a set of books, a period close, or a financial-records
package. Used when assessing ledger integrity, evaluating internal controls,
determining close-package readiness, or issuing a composite. Scores without stated
reasoning and confidence context are invalid.

---

## Dimensions (nine — weights sum to 1.00)

| # | Dimension | Weight | Hard gate |
|---|-----------|--------|-----------|
| 1 | Reconciliation Completeness | 0.18 | YES — score = 1 blocks CERTIFIABLE |
| 2 | Documentation & Audit Trail | 0.14 | YES — score = 1 blocks CERTIFIABLE |
| 3 | Revenue Recognition Accuracy (ASC 606 / IFRS 15) | 0.14 | — |
| 4 | Accuracy & Misstatement Exposure | 0.12 | — |
| 5 | Internal Controls & Segregation of Duties | 0.10 | — |
| 6 | Cost Allocation & Multi-Entity Integrity | 0.10 | — |
| 7 | Fraud & Anomaly Detection | 0.08 | — |
| 8 | Compliance & Reporting Timeliness | 0.08 | — |
| 9 | Cash & Liquidity Accuracy | 0.06 | — |
| | **Total** | **1.00** | |

---

## Composite formula

```
Composite = (RC × 0.18) + (DAT × 0.14) + (RRA × 0.14) + (AME × 0.12)
          + (ICSD × 0.10) + (CAMI × 0.10) + (FAD × 0.08) + (CRT × 0.08)
          + (CLA × 0.06)

Where each dimension is scored 1–10:
  RC   = Reconciliation Completeness
  DAT  = Documentation & Audit Trail
  RRA  = Revenue Recognition Accuracy (ASC 606 / IFRS 15)
  AME  = Accuracy & Misstatement Exposure
  ICSD = Internal Controls & Segregation of Duties
  CAMI = Cost Allocation & Multi-Entity Integrity
  FAD  = Fraud & Anomaly Detection
  CRT  = Compliance & Reporting Timeliness
  CLA  = Cash & Liquidity Accuracy

Result range: 1.00–10.00
```

**Unlock condition:** the composite is not reported until all nine dimensions are
scored with at least one piece of evidence cited. Any dimension scored without
evidence defaults to 3, is labeled INFERRED, and the composite is labeled
`PROVISIONAL — [X] dimension(s) inferred`.

---

## Band scale

| Composite | Band | Meaning |
|-----------|------|---------|
| ≥ 8.0 | Green — CERTIFIABLE | All core conditions met; books audit-ready, controls functioning |
| 6.0–7.9 | Yellow — CERTIFIABLE WITH NOTES | Proceed with named gaps; resolve 1–2 gap dimensions before next close |
| 4.0–5.9 | Amber — REMEDIATION REQUIRED | Significant gaps must be resolved before certification; partial close acceptable only for non-material sub-entities |
| < 4.0 | Red — NOT CERTIFIABLE | Hard gaps in reconciliation, documentation, or controls require remediation before any certification or reporting |

Bands describe what a composite is *consistent with*. State "the composite is
consistent with the [Band] band"; thresholds are not hard-pinned to a decimal.

---

## Hard gates

Hard gates fire **only** at a dimension score of **1**. A score of 3 means a
serious deficiency — priority, but not gate-triggering.

| Gate | Trigger | Blocked verdict |
|------|---------|----------------|
| Reconciliation Gate | Reconciliation Completeness = 1 | CERTIFIABLE. Books are NOT CERTIFIABLE; remediate the unreconciled material account(s) before re-evaluation. |
| Documentation Gate | Documentation & Audit Trail = 1 | CERTIFIABLE. Books are NOT CERTIFIABLE; locate source documentation and re-establish the audit trail before re-evaluation. |

Gates are binary. A score of 2 on a gated dimension indicates material gaps —
serious and escalation-priority — but the gate fires only at 1. Name the gate
trigger and the specific deficiency; never issue CERTIFIABLE WITH NOTES as a
workaround for a hard-gate trigger.

---

## Scoring rules

1. **Score each dimension independently** before combining — do not let an overall
   impression of the close drive individual scores.
2. **Each score is a claim.** State the evidence, the confidence level, and the key
   assumption that, if wrong, would change the score by ≥1 point.
3. **Do not average past a failed gate.** If Reconciliation Completeness = 1 or
   Documentation & Audit Trail = 1, the books are NOT CERTIFIABLE regardless of
   composite.

### Confidence tagging (mandatory)

Every score entry carries: an evidence type (Observed / Told / Inferred), a
confidence level (High / Medium / Low), and the assumption that, if wrong, would
change the score by ≥1 point.

- **Observed:** the source was directly examined (reconciliation workpapers,
  sub-ledger, journal entry log, bank statement, contract, sign-off).
- **Told:** a responsible party stated the condition (management representation,
  close-package sign-off, counterparty confirmation).
- **Inferred:** no observed or told signal bears on the dimension; reasoning is from
  structural characteristics or analogy. Always labeled; always defaults to 3; never
  used where a told signal exists.

### INFERRED vs. told-absence

A dimension is *without evidence* (→ default 3, labeled INFERRED) **only** when no
observed or told signal bears on it — the input is silent, OR the artifact that
would inform it is structurally impossible at this stage (e.g., no prior close
exists because this is the entity's first operating period).

An **explicitly stated absence** of infrastructure that *could* exist is a
**TOLD-ABSENCE** — a bearing signal — scored on its anchor, NOT defaulted to 3 and
NOT labeled INFERRED. "No reconciliation was performed this period" is a
told-absence: the entity is operating and a reconciliation could have been
performed; anchor-score Dimension 1 (typically a confident low score), never
INFERRED. Missing track record on an early-stage entity (no prior audited close) is
a without-evidence condition — default 3, labeled INFERRED, and never scored below
3 solely because no history exists; missing history is not negative evidence.

### PROVISIONAL composite

The composite is labeled **PROVISIONAL** when ≥1 dimension is INFERRED. The
INFERRED default (3) is used in the calculation; the composite shows the PROVISIONAL
label and names the inferred dimension(s) inline. Example: "Composite = 6.1
PROVISIONAL — Dimension 5 (Internal Controls) scored INFERRED (no controls
documentation provided; first-period entity)."

### Uncertainty propagation

Composite confidence is capped by the lowest-confidence critical dimension, and the
cap is named inline. Example: "Composite confidence capped at Medium: Reconciliation
Completeness scored Told (management representation only; no workpapers examined)."

---

## Dimension anchors (1 / 3 / 5 / 7 / 10)

### Dimension 1 — Reconciliation Completeness (0.18, HARD GATE)
- **1 [GATE]:** no reconciliations performed; OR a material account unreconciled with
  no documentation or remediation plan; OR reconciliations cannot be traced to
  independent source data for material accounts. NOT CERTIFIABLE.
- **3:** most material accounts reconciled, but ≥1 has uncleared breaks aged >30 days
  without documented investigation; methodology inconsistent; breaks logged but not
  owned or escalated.
- **5:** all material accounts reconciled on a standard template; breaks documented
  with aging and owner; most cleared within 30 days; at most one immaterial account
  open.
- **7:** all material and most non-material accounts reconciled within ±3 business
  days; breaks owner-assigned and cleared within 30 days or escalated; approver
  sign-off captured; root-cause noted for recurring breaks.
- **10:** all balance sheet accounts reconciled by deadline, each reviewed by an
  independent second reviewer; zero unexplained breaks; root-cause and
  recurrence-prevention noted; audit-ready package with source docs attached;
  quality reviewed at pattern level quarterly.

### Dimension 2 — Documentation & Audit Trail (0.14, HARD GATE)
- **1 [GATE]:** source documents cannot be located for material transactions; OR
  entries posted without support, approval, or description for material amounts; OR
  the audit trail from ledger to source is broken for ≥1 material account. NOT
  CERTIFIABLE.
- **3:** documents exist for most transactions but significant gaps persist (>10% of
  material entries incomplete); approval inconsistent; trail reconstructable only
  with manual effort beyond standard turnaround.
- **5:** source docs on file for all material transactions (>95%); entries carry
  description and preparer; approval documented above the materiality threshold;
  trail reconstructable within one business day; accruals documented with basis.
- **7:** full documentation for all entries, reconciling items, and manual
  adjustments; entries carry preparer, approver, document reference, and explanation;
  trail electronic and traceable; exceptions flagged with basis and sign-off.
- **10:** complete electronic trail with a tested retention policy; dual approval for
  above-threshold items; documents attached at entry; reversals and top-side
  adjustments carry extra authorization; audit requests answered within hours.

### Dimension 3 — Revenue Recognition Accuracy (0.14)
- **1:** revenue on cash or contract-date basis without the 5-step model; OR multiple
  obligations not identified/allocated; OR material deferred revenue released at wrong
  times; OR breakage/MG recognized on an unsupportable pattern.
- **3:** 5-step model applied with material gaps; allocation approximate, not SSP-based;
  variable consideration estimated inconsistently; deferred revenue not reviewed
  against milestones each period.
- **5:** model applied consistently across material contracts; obligations identified;
  allocation via SSP or documented proxy; variable consideration constrained with
  method stated; deferred-revenue roll-forward maintained; policy documented with
  sign-off.
- **7:** full application in a written, controller-approved policy; SSP documented per
  obligation; estimation method selected and stable; deferred revenue reviewed
  quarterly; breakage only on highly-probable patterns; position reviewed with auditor
  at interim.
- **10:** policy auditor-reviewed and updated for new contract types; contract-level
  schedules; SSP reviewed annually; modifications handled per ASC 606; material
  judgments documented with scenario analysis; controller certifies each close.

### Dimension 4 — Accuracy & Misstatement Exposure (0.12)
- **1:** known/likely misstatements exceed materiality and are uncorrected; OR
  statements contain arithmetic, cut-off, or classification errors unaddressed;
  exposure unquantified.
- **3:** potential misstatements acknowledged but not investigated or corrected in the
  period; analytical variances >5% on material lines undocumented.
- **5:** all identified misstatements corrected or waived against materiality with
  rationale; variance analysis on material lines vs. prior period and budget;
  adjusting entries posted before sign-off.
- **7:** formal misstatement tracking schedule; adjustments evaluated against materiality
  (SAB 99 / IAS 8 for judgmental items); correction/waiver documented; analytics a
  controller-reviewed deliverable.
- **10:** rolling errors schedule (corrected and uncorrected); aggregate uncorrected
  misstatements compared against materiality and performance materiality; controller
  certifies freedom from material misstatement; zero known uncorrected above
  materiality at sign-off.

### Dimension 5 — Internal Controls & Segregation of Duties (0.10)
- **1:** no meaningful segregation on material transactions; OR key controls absent or
  routinely bypassed; OR no documented framework at any level.
- **3:** basic segregation for some functions but material gaps remain; controls
  documented inconsistently; no formal framework.
- **5:** key segregation documented and enforced for material processes; framework (COSO
  or equivalent) adopted at summary level; periodic access reviews; authorization
  limits defined and applied.
- **7:** formal framework documented and assessed annually; segregation matrix for all
  significant roles; compensating controls documented where full separation is
  impractical; IT general controls reviewed.
- **10:** complete environment across entity, process, and IT layers; risk-control matrix
  with annual independent effectiveness testing; system-enforced access with automatic
  violation flagging; zero unmitigated segregation deficiencies on material processes.

### Dimension 6 — Cost Allocation & Multi-Entity Integrity (0.10)
- **1:** costs allocated with no documented methodology; OR intercompany balances
  unreconciled and out of balance; OR entity walls breached (one entity's costs in
  another without a documented intercompany transaction).
- **3:** some methodology documented but inconsistently applied; intercompany reconciled
  but chronic small breaks aged >60 days; allocation basis reviewed ad hoc.
- **5:** allocation policy documented and consistently applied (named basis);
  intercompany reconciled each period with zero unresolved breaks >60 days; transfer-
  pricing rationale documented; entity-wall verification a close step.
- **7:** policy reviewed annually with change protocol and entity-wall checkpoint;
  eliminations a reviewed close deliverable; transfer-pricing documentation maintained;
  allocation changes require controller approval and disclosure.
- **10:** methodology externally defensible and consistent with transfer-pricing
  requirements; intercompany reconciles to zero on consolidation with profit eliminated;
  entity-wall compliance signed off as a required step; changes prospective, logged, and
  disclosed.

### Dimension 7 — Fraud & Anomaly Detection (0.08)
- **1:** no detection procedures AND known/suspected anomalies identified and
  uninvestigated.
- **3:** basic detection (some duplicate screening, expense review); suspicious items
  logged but investigation ad hoc; no formal risk assessment; reporting channel absent
  or untested.
- **5:** formal annual fraud risk assessment; key controls run each close (duplicate
  screening, journal entry exception reporting, disbursement review); anomalies above
  materiality investigated; reporting channel in place.
- **7:** risk assessment mapped to control activities; period-end monitoring of high-risk
  types; journal entry analytics run at close; anomaly reports cleared by the controller;
  investigation protocol documented.
- **10:** continuous monitoring integrated into the close; digit-distribution analytics on
  material populations; counterparty risk screening; analytics reviewed by an independent
  function; all anomalies above de minimis resolved and root-caused; governance briefed
  annually.

### Dimension 8 — Compliance & Reporting Timeliness (0.08)
- **1:** regulatory or contractual deadlines missed; OR reports materially late; OR filing
  failures with unaddressed penalty notices.
- **3:** most internal deadlines met but external filings late ≥2 times in the trailing 12
  months; calendar exists but inconsistently followed.
- **5:** calendar defined and followed; all external deadlines met in the current period;
  minor internal delays documented; calendar reviewed each close.
- **7:** formal calendar with status, owner, and expected date; monitored weekly; no missed
  external deadlines in 12 months; tasks delegated with backup coverage.
- **10:** calendar automated with reminders; all deadlines met with buffer over 12 months;
  regulatory changes tracked and the calendar updated within days; zero missed filings;
  completeness confirmed with retained receipts.

### Dimension 9 — Cash & Liquidity Accuracy (0.06)
- **1:** bank reconciliations not performed; OR ledger cash differs materially and
  unexplainedly from the bank; OR cash positions unavailable/unreliable for material
  accounts.
- **3:** reconciliations performed but not within 5 business days; timing differences not
  aged; reliability uncertain; petty cash unreconciled.
- **5:** reconciliations within 5 business days for material accounts; outstanding items
  aged and owned; position available within one business day; restricted cash disclosed
  separately.
- **7:** reconciliations within 3 business days; preparation and review segregated;
  outstanding items cleared within 30 days; position a daily/close deliverable;
  intercompany cash cleared each period.
- **10:** reconciliations within one business day, reviewed and approved; zero unreconciled
  differences >10 days; real-time/daily position with same-day accuracy; 13-week rolling
  forecast updated weekly and variance-analyzed; restricted, escrow, and sweep accounts
  reconciled separately; controller certifies cash accuracy each close.

**Between-anchor calibration** is permitted (scores of 2, 4, 6, 8, 9): interpolate on
the trajectory the anchors describe, stating which factors place the score above the
lower anchor and below the higher one.
