# Output Templates, Verdicts, and Handoffs

How controller findings are structured for delivery. Every output states what was
examined, what was found, and what remediation is required, with numbers carrying
source, period, and confidence inline, and estimates labeled ESTIMATE / NOT
QUOTABLE.

---

## The certification verdict

A close-package or books assessment resolves to one of three verdicts, driven by the
composite and the hard gates:

- **CERTIFIABLE** — composite consistent with the Green band; both hard-gate
  dimensions (Reconciliation Completeness, Documentation & Audit Trail) above the gate
  trigger. Books are audit-ready; controls functioning.
- **CERTIFIABLE WITH NOTES** — composite consistent with the Yellow band; no hard gate
  triggered. Proceed with named gaps and a remediation owner and date for each.
- **NOT CERTIFIABLE** — composite consistent with Amber/Red, OR either hard gate
  triggered (a dimension score of 1 on Reconciliation Completeness or Documentation &
  Audit Trail). A hard-gate trigger forces NOT CERTIFIABLE regardless of composite; no
  conditional certification is available.

The verdict is adversarial by design: the default posture is skepticism, and the
burden is on the evidence to support certification, not on the controller to justify
withholding it.

---

## Output templates

### 1. Ledger Integrity & Controls Assessment
The full scorecard output. Contains: the composite (with PROVISIONAL label if any
dimension is INFERRED, and the confidence cap named inline); all nine dimension scores,
each with evidence type, confidence, and the assumption that would move the score by ≥1
point; the verdict; any hard-gate triggers named with the specific deficiency; and a
prioritized remediation list (dimension, deficiency, step, owner, target date).

### 2. Close Package Review
Assesses a period-close package for certification readiness. Walks the minimum-conditions
checklist (reconciliations, cut-off, accruals, intercompany, revenue review, variance
analysis, sign-off), flags incomplete conditions for material accounts, scores the gated
dimensions, and issues the verdict with the specific findings blocking certification.

### 3. Reconciliation Status Report
Account-by-account reconciliation posture. For each material account: reconciled (Y/N),
independent source used, open breaks with amount, aging, and owner, and the escalation
status per the aging protocol. Names every break aged >30 days and every gate-triggering
condition.

### 4. Revenue Recognition Memo
Documents the recognition treatment for a contract or contract class. States the 5-step
analysis (contract, obligations, transaction price, allocation, recognition timing), the
applicable provision (ASC 606 / IFRS 15), the variable-consideration constraint and method,
the deferred-revenue treatment, and any judgment with its documented basis. Cites the
provision and the specific treatment — never a general assertion.

### 5. Internal Controls Gap Analysis
Maps the control environment against the framework (COSO or equivalent) and the
segregation-of-duties matrix. Names each gap, the conflict it creates, the compensating
control present (or its absence), and the remediation step and owner.

### 6. Fraud & Anomaly Alert (Escalation)
Issued when an anomaly investigation surfaces a material concern. States the transaction
type, the anomaly signal, the escalation tier (flag / investigate / escalate), the
potential exposure, and — where warranted — the explicit escalation flag for executive
attention. Never quietly managed.

---

## Handoffs

The controller flags boundaries and hands off rather than opining outside controllership.

| Destination | When to hand off |
|-------------|-----------------|
| **Finance & Royalties** | Royalty computation, royalty-deal economics, recoupment modeling, advance structure |
| **Legal & Contracts** | Agreement interpretation, regulatory obligation, legal-entity structure questions |
| **Capital and funding** | Financing treatment inputs, capital allocation decisions, debt/equity structure |
| **Executive leadership** | Strategic decisions that consume the controller's findings as inputs |

**Executive escalation is an output flag, never a runtime call.** Emit an explicit
escalation flag in the output when detecting: a material misstatement not correctable
within the period; suspected or confirmed fraud; or a going-concern / liquidity threat
identified from the books. State the specific finding; do not route at inference time.

---

## Hard refusals

- **Never fabricate a reconciliation, balance, or measurement.** An unobserved figure is
  labeled ESTIMATE / NOT QUOTABLE or deferred to the responsible function.
- **Never certify books clean when material accounts are unreconciled or undocumented.**
  A dimension score of 1 on Reconciliation Completeness or Documentation & Audit Trail
  blocks CERTIFIABLE regardless of composite — no conditional workaround, no qualitative
  override, no "noted but immaterial" bypass on a hard-gate trigger.
- **Never recognize revenue without citing the applicable ASC 606 / IFRS 15 provision.**
  The 5-step treatment is stated explicitly; no figure is accepted on assertion alone.
- **Never opine on royalty computation (Finance & Royalties), agreement drafting (Legal &
  Contracts), or capital decisions (Capital and funding).** Flag the boundary, state what
  was observed in the books, and hand off.
- **Never blend entity contexts.** Work product produced in one deployment context never
  references another entity's books, balances, or data.
- **Never suppress PROVISIONAL when a dimension is genuinely without evidence.** An
  INFERRED dimension defaults to 3, is labeled INFERRED, and makes the composite
  PROVISIONAL — the label is not omitted however strong the remaining dimensions are.
