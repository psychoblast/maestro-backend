# Documentation, Audit Trail, and Internal Controls

Two control pillars: the documentation and audit trail that makes the ledger
traceable, and the internal-control environment (including segregation of duties)
that prevents error and fraud by design. General frameworks followed by
music-specific modules.

---

## DOCUMENTATION AND AUDIT TRAIL

### The vouching standard

Every material transaction must be traceable from the ledger back to a source
document that an independent reviewer can locate and examine. The audit trail is
the unbroken chain from a GL balance, through the journal entries that compose it,
to the source documents that authorize each entry. A break anywhere in that chain
for a material account means the balance cannot be vouched, and an unvouchable
balance is unverified regardless of how reasonable it appears.

**A source document must answer four questions:** what happened (the economic
event), when (the date driving period assignment), how much (the amount and its
basis), and who authorized it. A journal entry without a source document answering
these is an assertion, not a record.

**Journal entry control standard.** Each entry carries: preparer, approver (for
amounts above the authorization threshold), a supporting-document reference, and a
description sufficient for an independent reviewer to understand the entry without
asking the preparer. Reversals, corrections, and top-side adjustments carry
additional authorization and a stated rationale — these are the entries most often
used to manipulate results, so they receive the most scrutiny, not the least.

**Estimated accruals** are documented with the basis stated — method, rate, period
— so that a reviewer can reconstruct the estimate and a successor can roll it
forward. An accrual with an unexplained amount is undocumented even if the number
is correct.

**Retention and audit responsiveness.** A documented retention policy meets the
longer of the legal requirement and the organization's own policy, and is itself
tested for compliance. Audit-readiness is measured by responsiveness: the audit
trail from ledger to source should be reconstructable within a standard request
turnaround, with supporting documents attached in the accounting system at the
point of entry rather than reconstructed on demand.

---

## INTERNAL CONTROLS AND SEGREGATION OF DUTIES

### Controls are preventive by design

A control environment exists to prevent error and fraud before they enter the
record, not to detect them afterward. The governing framework (COSO 2013 or
equivalent) spans three layers — entity-level controls (tone, governance, risk
assessment), process-level controls (the transactional controls over AP, AR,
payroll, journal entries, banking), and IT general controls (access management,
change control, system-enforced authorization). A control framework that exists on
paper but is not assessed for operating effectiveness is documentation, not
control.

### Segregation of duties

The core principle: no single person should both *initiate* and *approve and
record* a material transaction. The four incompatible functions to separate are
authorization, custody (of assets/cash), recording, and reconciliation. A
segregation gap exists wherever one person controls enough of these to both cause
and conceal an error or misappropriation — for example, the same person who
initiates a payment also approves it and reconciles the bank account.

**A segregation-of-duties matrix** maps each financially-significant role to the
functions it can perform and flags conflicting combinations. Where full separation
is operationally impractical (small teams are the common case in music
enterprises), **compensating controls** are documented and specifically address
the conflict the gap creates — independent after-the-fact review of all
transactions by the conflicted individual, mandatory dual authorization above a low
threshold, independent bank-reconciliation review, or system-enforced access
restrictions. A compensating control that does not address the specific conflict
is not compensation; it is decoration.

**Authorization limits** are defined, communicated, and applied — including
journal entry posting limits and disbursement approval tiers. Limits that exist but
are routinely bypassed are worse than no limits: they create a false assurance.

**Access controls** in the accounting/ERP system enforce segregation
systematically — access provisioning, periodic access reviews, prompt
de-provisioning, and automatic flagging of segregation violations. The strongest
environments make the system, not individual discipline, the enforcer.

---

## MUSIC MODULES

### Documentation in a music-label structure

Music enterprises rely on source documents with distinctive characteristics that
the vouching standard must accommodate:

- **Contracts as primary source.** Recording, publishing, distribution, sync, and
  licensing agreements are the source documents that authorize advance disbursements,
  royalty obligations, and recognition treatment. A material royalty or advance
  booking that cannot be traced to a signed agreement is unvouchable — the contract
  is the source, not a summary of its terms.
- **Royalty statements and remittance advices.** Inbound statements from
  distributors, PROs, and CMOs, and outbound remittance advices to recipients, are
  the supporting documents for royalty income and payable bookings. They are
  retained and matched to the corresponding accrual and payment entries.
- **PRO and CMO remittance detail.** Distribution detail supports the recognition
  and reconciliation of performance and mechanical income; the summary distribution
  figure alone is insufficient documentation where the detail is available.

### Controls in a music-label structure

- **Royalty-advance approval limits.** Advance disbursements are a high-value,
  high-discretion outflow. Authorization tiers and dual approval above a threshold
  are essential controls; an advance disbursed without documented approval against
  a signed agreement is both a control failure and a documentation gap.
- **Small-team segregation reality.** Music enterprises frequently run lean finance
  functions where full segregation is impractical. The expectation is not headcount
  the organization does not have — it is *documented compensating controls* that
  specifically address each conflict, plus independent review (internal or external)
  of the conflicted individual's work.
- **System access over royalty and disbursement systems.** Access to royalty
  computation systems, the disbursement function, and the GL is provisioned by role,
  reviewed periodically, and de-provisioned promptly on role change — so that the
  person computing royalties is not also the person disbursing them without
  independent review.
