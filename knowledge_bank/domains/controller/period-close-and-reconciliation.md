# Period Close and Reconciliation

General close-and-reconciliation frameworks followed by music-specific modules.
Current-period filing calendars, platform reporting windows, and PRO distribution
schedules live in a separate current-period reference layer; the frameworks here
govern assessment methodology, not current-period specifics.

---

## GENERAL FRAMEWORKS

### The close as an evidence-assembly process

A period close is not a reporting exercise — it is an evidence-assembly process
that produces a defensible claim that the ledger correctly represents the
entity's financial position at a specific date. Every close activity —
reconciling accounts, reviewing journal entries, verifying cut-offs, posting
accruals — collects the evidence that makes that claim auditable. A close that
issues financial statements without completing the underlying evidence assembly
has not closed; it has attached an assertion to an unverified ledger.

A "reconciliation" that cross-references two numbers produced by the same team
proves nothing — it confirms internal consistency, not accuracy. A genuine
reconciliation traces the general-ledger balance to an *independently sourced*
amount, with each difference documented, owned, and aged. The independence of
the source is what makes the reconciliation meaningful; without it, a systematic
error in the GL can be mirrored in the reconciling source, the comparison passes,
and the balance remains wrong.

**Minimum conditions for a complete close:**

1. All material balance sheet accounts reconciled to an independent source — not
   a management summary prepared by the same function that prepared the entry.
2. Cut-off verified: transactions belonging to the closing period recorded in
   that period; transactions belonging to the following period excluded.
3. Accruals and estimates posted with documented basis — reflecting actual
   economic obligations, not desired results.
4. Intercompany positions confirmed and reconciled to zero (or to documented
   open items).
5. Revenue recognition reviewed against policy each period.
6. Variance analysis performed on material P&L and balance sheet lines, with
   unexplained variances above threshold investigated and documented.
7. Close package assembled, reviewed, and signed off by the controller.

If any condition is absent for a material account or line, the close is
incomplete regardless of whether statements have been issued.

---

### Close calendar design

A close calendar assigns every activity a deadline, an owner, and a dependency
structure — what must be done, in what sequence, by whom, by when. A close
without an explicit calendar is an ad hoc process whose outcomes are driven by
who happened to act rather than by what the process requires, and an ad hoc
process is unauditable by design.

- **Hard deadlines.** Final statement delivery and external filing deadlines
  define the outer boundary; every other deadline is derived by working backward
  from these fixed points.
- **Sub-ledger close.** Sub-ledgers (AR, AP, royalties payable, recoupable
  advances) are locked before the GL close begins. A GL close running concurrently
  with open sub-ledgers is unreliable.
- **Journal entry deadlines.** Standard entries post by a defined deadline; later
  entries require controller sign-off. Top-side manual adjustments carry their own
  deadline and dual sign-off. A soft deadline that accommodates latecomers creates
  incentive drift — the close never actually closes.
- **Reconciliation completion deadline.** Every reconciliation is due by a defined
  date, with a review-and-sign-off deadline following. The preparer ≠ reviewer
  requirement is not formality; it is the control that catches errors the preparer
  introduced.
- **Variance review.** A structured review of the preliminary package
  (period-over-period and budget-vs-actual) by the controller before issue. A
  quality gate, not a formatting step.
- **Final controller sign-off.** The documented conclusion of a controlled
  sequence — not the first time the controller has seen the period's position.

**Directional SLA benchmarks (ESTIMATE / NOT QUOTABLE — set against
organizational capability and external reporting requirements):**

| Close activity | Target SLA (calendar days post-period-end) |
|---|---|
| Sub-ledgers closed | Day 1–2 |
| Standard journal entries posted | Day 2–3 |
| Account reconciliations submitted | Day 3–5 |
| Reconciliations reviewed and signed | Day 4–6 |
| Preliminary variance review | Day 5–7 |
| Final controller sign-off | Day 6–8 |

The meaningful metric is not the absolute number of days but whether the SLA is
defined, consistently met, and whether deviations carry an approved rationale.

---

### Reconciliation methodology: the four-element standard

A reconciliation answers one question: does the GL balance for this account, at
this date, agree to an independently derived amount, and if not, why?

- **Element 1 — GL balance.** The account balance per the general ledger as of
  the reconciliation date. The number whose accuracy is being tested.
- **Element 2 — Independent source balance.** A balance from a source entirely
  independent of the GL — a bank statement, a counterparty confirmation, a
  sub-ledger independently verified against external inputs, an aged schedule
  built from invoices. Reconciling a GL balance to a summary prepared by the same
  team that prepared the entries proves only that two summaries agree.
- **Element 3 — Reconciling items.** A specific, documented list of differences —
  deposits in transit, outstanding payments, timing differences, accruals awaiting
  settlement. Each carries a description, an amount, an age, and an owner.
- **Element 4 — Conclusion.** Either the balances agree after accounting for
  reconciling items (the GL balance is supported), or an unexplained difference
  remains — an open break requiring investigation before the close is certified.

A reconciliation that reaches Element 4 without genuine independent sourcing in
Element 2 is not a reconciliation; it is a cross-reference, and is scored as such.

---

### Break investigation and escalation protocol

An open reconciling break is an unresolved claim about the accuracy of the
records. Every break is investigated to one of three resolutions:

- **Cleared.** Identified, explained, and the reconciliation re-run to show
  agreement.
- **Documented and aged.** Known and under investigation but not yet cleared —
  with the specific cause, aging from first identification, assigned owner, and
  expected resolution date.
- **Escalated.** Cannot be identified or resolved within the period — with a
  controller-directed investigation summary, the potential misstatement exposure,
  and a remediation plan with a target date.

**Break aging — escalation triggers:**

| Break age | Required action |
|---|---|
| < 30 days | Document; assign owner; track resolution |
| 30–60 days | Escalate to controller; investigation summary required |
| > 60 days | Material concern; controller documents remediation plan; provision or write-down considered |

A break open more than 60 days without documented investigation is not a managed
reconciling item — it is an unresolved error, and an external auditor treats it as
a potential misstatement, not normal close variance.

---

### Cut-off control: the time dimension of reconciliation

Cut-off ensures transactions are recorded in the period they economically belong
to, not the period they happen to be processed in. Cut-off errors inflate one
period and deflate another without any economic change — pure reporting
distortions, and the most common source of period misstatement.

**The cut-off test:** for any material account — is there a transaction in this
period that economically belongs to another period, and is there a transaction
that belongs to this period but has been omitted?

High-risk areas: revenue recognized on cash receipt rather than performance;
expense accruals over- or under-stated against the actual obligation; royalty
payable accruals where royalty periods and accounting periods don't align; and
advance receipts spanning multiple future periods that must be split and deferred.

A cut-off error caught before sign-off is normal close process. Caught by
auditors after close, it is a restatement risk. Unidentified, it is a
misstatement.

---

## MUSIC MODULES

### The music close calendar: structural complications

These are recurring characteristics requiring specific procedures in every close,
not exceptions to manage around.

- **Platform data lag.** Streaming platforms report on their own cycle, rarely
  aligned with the accounting period. Streaming revenue earned in the last days of
  a period may not appear in platform reporting for weeks. The controller either
  recognizes revenue on a documented accrual for the lag period (method, data
  source, period, preparer, reviewer all stated) or recognizes only confirmed data
  and discloses the lag. Either is acceptable under ASC 606 / IFRS 15 with
  documentation; inconsistent treatment across periods, or omission without
  disclosure, is not.
- **Royalty statement timing.** Statements from distributors, labels, PROs, and
  publishers arrive quarterly, semi-annually, or annually, creating a mismatch
  with the accounting period. The controller maintains a royalty-statement calendar
  tracking which streams report on what cycle, expected arrival date, the period
  covered, and the inter-statement accrual methodology. Without it, the royalty
  balance cannot be independently verified between statements.
- **PRO distribution cycles.** Performance-rights organizations distribute on
  their own schedule with significant territorial variation. PRO income is often
  recognized on a cash basis when it should be accrued; apply ASC 606 / IFRS 15
  criteria (performance obligation satisfied, amount estimable and probable) rather
  than defaulting to receipt-date recognition.
- **Multi-territory complexity.** Rights income earned across territories carries
  different reporting periods, currencies, withholding structures, and remittance
  timing. The close consolidates these into a single functional-currency balance
  sheet with FX translation, withholding netting, and reconciliation of each
  stream to its source. A missing territory's statement is a reconciliation gap.
- **Advance funding receipts.** Record as a liability (deferred income or advance
  payable) at receipt — not as revenue; clear from the liability only as
  performance obligations are satisfied or royalties are earned against the
  recoupable balance; reconcile to the signed contract. An advance booked directly
  to revenue at receipt is simultaneously a revenue-recognition error and a
  cut-off error.

---

### Royalty-payable reconciliation: the hardest music-specific account

The royalty payable balance — amounts owed to artists, songwriters, publishers,
and other recipients — is typically the most complex and highest-risk balance
sheet account, for three structural reasons:

- **Input diversity.** It aggregates streaming platforms, physical distributors,
  sync licensing, PROs, neighboring-rights organizations, and download platforms —
  each with different cycles, formats, and methodologies. A reconciliation that
  consolidates these without tracking each source separately has aggregated, not
  reconciled; a systematic error in one stream is invisible in the aggregate.
- **Computation dependency.** The balance cannot be independently verified without
  the royalty computation, which belongs to Finance & Royalties. The controller
  verifies that what Finance computed is what was booked — not the computation
  itself. If the computation is inaccessible, the reconciliation is at best
  INFERRED and labeled with a handoff notation.
- **Timing mismatches.** Royalties are earned on a different schedule than they are
  reported and paid. The balance aggregates a current-period earned accrual (not
  yet reported to recipients) plus the outstanding balance from prior statements
  reported but not yet remitted.

**Reconciliation structure for royalty payable:**

| Component | Source | Verification step |
|---|---|---|
| Opening balance | Prior close package | Agrees to prior GL balance at close |
| Additions — current-period earned | Finance & Royalties computation | Cross-check to computation; verify booking matches amount and period |
| Payments made | Bank disbursement records | Agree to remittance advice and bank statement; payee matches |
| Adjustments | Journal entry log | Each carries supporting document and approver |
| Closing balance | GL account | Agrees to GL; reconciling items listed with aging and owner |

Common break types: an accrual mismatch (computed amount ≠ booked accrual — trace
to posting error vs. policy difference); a payment-timing break (remittance
recorded but not yet cleared — document as an outstanding item); and a missing
statement accrual (period closed with no accrual posted between the last statement
and the accounting date — post with basis documented and reconcile when the
statement arrives).

---

### Advance reconciliation: tracking recoupable balances

A recoupable-balance register carries one row per advance-bearing agreement —
original advance paid (linked to disbursement record and signed contract),
additional recoupable charges applied (as authorized), royalties applied to reduce
the balance (per Finance's computation), net recoupable balance at close, and an
expected recoupment timeline (ESTIMATE — from Finance & Royalties).

The sum of all register rows must agree to the GL recoupable-advance account at
each close; any difference is a break. Common causes: an advance paid in the
period not yet entered; a royalty application not reflected; a write-off posted to
the GL without a register update.

**Impairment obligation.** A recoupable balance unlikely to be fully recouped
within the remaining contract term is an impaired asset. The controller does not
forecast whether the artist will generate sufficient royalties — that is Finance's
and A&R's domain — but verifies that recoverability was evaluated at each close,
with a documented judgment and adjustment (or documented immateriality waiver).
An unreviewed recoupable balance exceeding expected recoverable royalties is a
balance sheet misstatement risk.
