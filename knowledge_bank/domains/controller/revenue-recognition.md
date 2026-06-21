# Revenue Recognition (ASC 606 / IFRS 15)

General five-step framework followed by music-specific modules. Standard
amendments and jurisdiction-specific adoption timelines live in a separate
current-period reference layer; verify currency there before applying the model to
a novel transaction type.

---

## GENERAL FRAMEWORKS

### The five-step model: controller application

ASC 606 (US GAAP) and IFRS 15 (international) establish a single,
principles-based revenue recognition model applied to each contract with a
customer. The controller's role is not to decide business outcomes — it is to
verify that the standard was applied correctly, that the judgment is documented
at each step, and that the recognition pattern is consistent with the documented
policy across periods and contract types.

**Step 1 — Identify the contract.** A contract exists when both parties have
approved it, payment rights and obligations are identified, it has commercial
substance, and collection of substantially all consideration is probable. A
booking without a qualifying contract, or where collection is not probable, is
premature recognition. Whether an unsigned exchange constitutes a binding
agreement is a Legal determination, not a controller one.

**Step 2 — Identify the performance obligations.** Performance obligations are the
distinct goods or services promised. A promise is distinct when the customer can
benefit from it on its own (capable of being distinct) and the promise is
separately identifiable in the contract context. A contract with multiple distinct
obligations treated as one will recognize all revenue on delivery of the first
item — overstating early periods, understating later ones. A license grant bundled
with ongoing promotional services, reporting obligations, or rights maintenance
distinct from the grant contains multiple obligations; each is identified and
accounted for separately before Steps 3 and 4.

**Step 3 — Determine the transaction price.** The amount the entity expects to
receive, net of amounts collected for third parties. Where the price includes
variable consideration — usage royalties, performance bonuses, returns, price
concessions, penalties — the variable component is estimated and constrained.
Variable consideration is included only to the extent it is *highly probable* that
a significant reversal in cumulative recognized revenue will not occur when the
uncertainty resolves. "Highly probable" is deliberately higher than "probable,"
creating an asymmetry: the entity is more conservative recognizing upside than
fixed amounts.

Two estimation methods — a policy decision applied consistently within each class:
the **expected-value method** (probability-weighted sum across outcomes; suited to
many possible outcomes with supporting history) and the **most-likely-amount
method** (the single most probable amount; suited to binary outcomes). Switching
methods without a documented policy change is a consistency violation and a
prior-period-adjustment risk.

**Step 4 — Allocate the transaction price.** Allocate to each performance
obligation by relative standalone selling price (SSP). Where SSP is observable,
use it; where not, estimate via adjusted market assessment, expected cost plus a
margin, or — restricted in use — the residual approach (which cannot allocate zero
or a negative amount to an obligation). Allocation is based on SSP, not on
management's preferred revenue timing.

**Step 5 — Recognize revenue when (or as) each obligation is satisfied.** Revenue
is recognized when control transfers — at a point in time or over time.
Over-time recognition applies when the customer consumes the benefit as the entity
performs, the entity enhances a customer-controlled asset, or the entity's
performance creates no asset with alternative use and there is an enforceable right
to payment for work to date. Otherwise, point-in-time recognition applies on
control indicators (present right to payment, legal title, physical possession,
risks and rewards, acceptance). Recognition timing corresponds to when control
actually transferred — not when cash was received, the contract signed, or the
invoice issued. A Step 5 error is a period misstatement even when all prior steps
were correct.

---

### Variable consideration: the constraint analysis

Variable consideration is the element most susceptible to manipulation and most
frequently misapplied. The constraint prevents premature recognition of amounts
that may not be received.

Factors arguing for a *tighter* constraint: the amount is highly susceptible to
factors outside the entity's control; the uncertainty resolves only over a long
window; the entity has limited experience with similar contracts; the range of
outcomes is wide or contains interacting contingencies; past practice shows a
pattern of concessions. Factors allowing a *less-constrained* estimate: a large
portfolio of similar contracts; quick uncertainty resolution; the entity controls
the reversal events; a narrow outcome range.

The **ceiling rule**: recognized variable consideration cannot exceed the amount
highly probable not to reverse — a maximum, not a guaranteed minimum. Estimates are
**reassessed each reporting period**; a change produces a current-period
cumulative catch-up, not a prior-period restatement.

---

### Deferred revenue: release discipline

Deferred revenue — amounts received before obligations are satisfied — is a
liability representing an obligation to perform, not income. Release to income is
triggered by obligation satisfaction, not management preference, cash needs, or
the passage of calendar time.

The release test for each balance: which obligation does it correspond to
(documented per contract when the liability is established); what is the
obligation's completion status; what is the appropriate release (point-in-time:
release when control transfers; over-time: release proportional to a consistently
applied measure of progress); and is there evidence of satisfaction.

Common errors — each a recognition deficiency: releasing on a straight-line time
basis when the obligation is not time-based; releasing the full balance on the
first item when a second distinct obligation remains; carrying deferred revenue
for obligations already satisfied because the release entry was not posted;
releasing where the satisfaction condition was not met; and failing to review
balances at each close.

**The deferred-revenue roll-forward — a required close deliverable:**

```
Opening deferred revenue balance
+ Additions (new deferrals — cash received or invoiced before obligation satisfied)
− Releases (obligations satisfied in the period, released to revenue)
= Closing deferred revenue balance
```

Reconciled to the GL at each close, with each addition referencing the contract
and obligation and each release referencing satisfaction evidence. An unreconciled
roll-forward is simultaneously a reconciliation break and a documentation gap.

---

## MUSIC MODULES

### Advances and minimum guarantees: lifecycle treatment

The recording advance or minimum guarantee (MG) is the most consequential and most
frequently mistreated revenue/liability transaction in music accounting.

**Stage 1 — Advance received (entity as payee): deferred liability, not income.**
An advance or MG received from a counterparty is a prepayment against future
obligations (the counterparty earns it back through streaming or sync performance).
Book it as a deferred income liability; release to revenue as the underlying
obligation is satisfied. Booking to revenue at receipt is a Step 5 error. The
exception — current income at receipt — applies only when the advance is
contractually non-refundable AND the obligation is fully satisfied at receipt
(e.g., delivery of a perpetual, fully-exploitable license with no ongoing
obligations). If any ongoing obligation exists, defer to the extent it relates to
the unfulfilled obligation, with the Step 4 allocation documented.

**Stage 2 — Advance paid (entity as payor): recoupable asset, not expense.** An
advance disbursed under a recording, publishing, or licensing agreement is a
recoupable asset representing the balance recoverable through future royalty
withholding — carried until royalties recoup it to zero or it is impaired.
Treating disbursements as marketing expense or cost of goods is a balance sheet
misclassification that distorts period-over-period comparisons.

**Stage 3 — Impairment.** A recoupable balance unlikely to be fully recovered
within the remaining term is impaired. The assessment needs projected earnings
over the term (from Finance & Royalties), the probability the trajectory continues
(ESTIMATE — from Finance & Royalties and A&R; the controller does not
independently forecast), and the gap between expected recovery and carrying value.
The controller verifies the assessment was performed and documented at each close;
it does not substitute its own recovery estimate.

---

### Breakage: the highly-probable standard

Breakage — recognizing income from advance or MG balances no longer recoverable by
the payor — arises most often where the entity is the payee of a distribution MG
or licensing advance and performance is insufficient to recoup within the term, so
the entity permanently retains the unrecouped balance. Under ASC 606-10-55, this
retained balance is recognized as revenue only when a documented pattern shows a
portion is highly probable to be permanently retained.

The controller verifies: (1) historical pattern evidence exists (a portfolio of
comparable transactions showing consistent non-recovery — the data from Finance &
Royalties); (2) the estimate is conservative (the minimum amount highly probable of
retention, not the expected value); (3) recognition is proportional and ongoing
(recognized as the advance is consumed, not in a lump sum at term end); and (4)
the recognition is reviewed each close with a cumulative catch-up as probability
shifts. A breakage entry without documented history, constraint analysis, and
proportional treatment is a recognition error returned to Finance & Royalties for
documentation before acceptance.

---

### Streaming and digital platform revenue

Streaming royalties are usage-based royalties under ASC 606 — recognized as usage
occurs, not when the reporting cycle runs or payment is received. The operational
challenge is the lag between usage and reporting. For the lag portion of a period,
estimate earned royalties with documented method: data source (prior-period
actuals, platform preliminary estimates, trailing-three-month trend — specify),
methodology, period covered, preparer and reviewer, and the reconciliation path
when actual data arrives. When actual reports arrive, reconcile estimate to actual
and post the difference; an organization that systematically fails to reconcile is
perpetuating rolling errors that compound across periods.

**Gross vs. net (principal vs. agent).** Where the entity controls the rights and
licenses them directly to the platform (principal), recognize gross — full license
fee as revenue, artist royalty as expense or payable. Where the entity arranges a
transaction for a third-party rights holder for a commission (agent), recognize
net — only the commission. The test is who controls the right before transfer to
the customer; the determination is documented at inception, and consistent
misclassification produces systematic over- or under-statement.

---

### Sync licensing revenue

Sync licensing produces an upfront synchronization fee and backend performance
royalties. Under ASC 606, a point-in-time license is appropriate where the entity
grants the right to use the IP as it stands, the entity's activities do not
significantly affect that IP, and the IP is not ongoing performance — the fee is
recognized when the license is made available. The critical Step 2 question:
does the agreement contain only the grant, or also ongoing obligations (rights
maintenance, marketing support, periodic deliverables)? Distinct ongoing
obligations are separate performance obligations requiring Step 4 allocation;
recognizing the full fee at delivery when a material ongoing obligation remains is
a Step 5 error. Backend sync royalties are usage-based — recognized as broadcast
occurs, estimated for lag periods, and constrained. A bundled sync fee covering
both a master and a composition license (where the entity controls both, possibly
as principal on one and agent on the other) is two distinct obligations resolved in
Step 2 before any revenue is recognized.

---

### PRO and mechanical royalty income

**PRO income** — public-performance royalties — is usage-based under ASC 606,
earned when the performance occurs, not when the PRO distributes. Accrue for
periods between distributions with a documented method; reconcile the distribution
to the accrual and post the difference. PRO distribution lags can be substantial,
and a receipt-date policy for material, estimable amounts misapplies Step 5.

**Mechanical royalties** accrue as units are reproduced or streams occur, at the
applicable statutory or negotiated rate (administered by the Mechanical Licensing
Collective for US blanket digital licenses, and by collective management
organizations elsewhere). The income is earned when reproduction occurs; accrue
for the lag between usage and distribution and reconcile when the distribution
arrives. Statutory rates are set by regulatory proceedings and change periodically
— any specific rate cited must be sourced to the applicable rate-setting decision
or the specific contract, never assumed (NOT QUOTABLE); an accrual using an
outdated rate is a precision error.
