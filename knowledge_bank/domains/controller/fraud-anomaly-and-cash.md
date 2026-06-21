# Fraud & Anomaly Detection, Compliance Timeliness, and Cash Accuracy

Three control areas the controller runs as routine close procedures: forensic
anomaly detection, reporting-deadline compliance, and cash/liquidity accuracy.
General frameworks followed by music-specific modules.

---

## FRAUD AND ANOMALY DETECTION

### Fraud risk is a standing assumption

Anomaly detection and journal entry review are routine close procedures, not
investigations reserved for suspicion. A documented fraud risk assessment maps the
entity's high-risk transaction types (cash disbursement, payroll, royalty
remittances, journal entries to irregular accounts) to the control activities that
mitigate them, and is refreshed at least annually.

### Routine detection procedures

- **Journal entry analytics.** Each close, screen entries for risk markers:
  entries posted by unusual users, at unusual times (after hours, at period
  boundaries), to unusual or rarely-used accounts, in round amounts just below
  authorization thresholds, or reversing shortly after period end. Flagged entries
  are reviewed and cleared by the controller.
- **Digit-distribution testing (Benford's Law).** On material transaction
  populations, the leading-digit distribution of naturally-occurring financial data
  approximates a known logarithmic pattern. Significant departures do not prove
  fraud but identify populations warranting closer review — fabricated or
  manipulated figures often deviate from the expected distribution.
- **Duplicate-payment screening.** Screen disbursements for duplicate vendor,
  amount, invoice number, and date combinations — a common source of both error and
  misappropriation.
- **Cash disbursement and remittance review.** Exception review of high-risk
  outflows against authorization and supporting documentation.

### Investigation protocol and escalation

Every anomaly above a de minimis threshold is investigated to conclusion and
root-cause analyzed — not logged and forgotten. The investigation summary states
what was examined, what was found, the potential exposure, and the resolution. A
reporting channel for suspected irregularities exists, is publicized, and is
tested. The strongest environments have journal entry analytics reviewed by an
independent function (internal audit or external accountant) and brief governance
on fraud-risk posture annually.

**Escalation flag — output, not runtime action.** Suspected or confirmed fraud,
material misstatement not correctable within the period, or a going-concern /
liquidity threat surfaced from the books is emitted as an explicit escalation flag
in the output, naming the specific finding — never quietly managed.

---

## COMPLIANCE AND REPORTING TIMELINESS

### The compliance calendar

Internal and external reporting deadlines — the close calendar, royalty-statement
deadlines, PRO/CMO reporting, regulatory filings — are tracked in a maintained
compliance calendar with, per deadline: the due date, the owner, the status, and
documented backup coverage. The controller monitors the calendar on a regular
cadence (weekly is the strong-practice benchmark), not reactively.

Standards rise from "external deadlines met in the current period" to "no missed
external deadlines in the trailing twelve months" to "every deadline met with a
buffer, the calendar system-triggered, regulatory changes tracked and the calendar
updated within days of an effective date, and filing completeness confirmed with
retained receipts or acknowledgments." A missed contractual or regulatory deadline
that produced a penalty notice not yet addressed is a serious deficiency.

---

## CASH AND LIQUIDITY ACCURACY

### Bank reconciliation and cash position

Bank reconciliations are completed within the close SLA (strong practice: within a
few business days of period end), with preparation and review segregated
(preparer ≠ approver). Outstanding items are aged and owned; aged items are
escalated with explanation. The cash position is available on request with same-day
accuracy, and restricted cash, escrow, intercompany cash, and sweep accounts are
reconciled and disclosed separately rather than netted into a single line. A
ledger cash balance that differs materially and unexplainedly from the bank
statement is a hard reconciliation failure.

### Rolling cash forecast

Where a cash forecast is maintained, a rolling short-horizon forecast (a 13-week
rolling forecast is the common discipline) is updated on a regular cadence and
variance-analyzed against actuals. The integrity test is not the forecast's
optimism but whether prior forecasts are reconciled to what actually happened and
the variances explained — an unreconciled forecast is an unverified projection.

---

## MUSIC MODULES

### Music-specific fraud and anomaly patterns

- **Phantom royalty recipients.** Disbursements to payees not supported by a signed
  agreement, or to recipients whose details were added without authorization.
  Royalty payable detail is screened against the contracted recipient register.
- **Unauthorized or duplicate remittances.** Royalty and advance remittances are
  high-value and recurring, making them a target for duplicate or unauthorized
  payment. Screen remittances for duplicate recipient/amount/period combinations and
  match each to an authorized statement or agreement.
- **Intercompany manipulation.** Shifting cost or revenue between group entities to
  flatter one entity's margin is detected by entity-wall checks and intercompany
  reconciliation, treated here as a fraud-risk vector, not only a reconciliation
  matter.
- **Recoupment manipulation.** Misapplication of royalties against recoupable
  advance balances — to accelerate or defer recoupment — is screened by reconciling
  the recoupable register's applications to Finance's computation.

### Music-specific cash patterns

Music cash flows are lumpy and event-driven — advance receipts, periodic royalty
remittances inbound and outbound, touring settlements, and MG drawdowns — rather
than a smooth operating cycle. The cash forecast and reconciliation must account
for the timing of statement-driven receipts and remittances, restricted balances
held against artist obligations, and escrow arrangements; treating these as
ordinary unrestricted operating cash overstates available liquidity.

### Music-specific compliance windows

Royalty-statement deadlines to artists and recipients, PRO/CMO reporting cycles,
and territorial regulatory filings each run on their own calendar. The compliance
calendar tracks them by stream and territory; current-period windows and effective
dates are held in the separate current-period reference layer and checked before any
timeliness determination.
