# Chart of Accounts Architecture for Music Enterprises

Controller's framework for account structure and GL design in music enterprises.
Current-period account codes, ERP-specific numbering, and COA policy decisions
(activation, deactivation, ownership) belong in the organization's formal COA
policy and the current-period reference layer; what follows governs assessment
of account structure adequacy and COA design integrity.

---

## GENERAL FRAMEWORKS

### The controller's stake in COA design

The chart of accounts is the architecture of the ledger. A poorly designed
COA — too broad to distinguish income types, too granular to produce useful
summaries, or inconsistently maintained — produces a record that passes
arithmetic checks but cannot be reconciled, cannot be audited, and cannot
produce meaningful management information. The controller's stake is not
aesthetic; account structure determines whether the required reconciliations
can be performed at all.

**Four design tests a controller applies to any COA:**

1. **Reconciliation-tractable.** Each account subject to a required
   reconciliation has a defined independent source against which it reconciles.
   An account that aggregates too many transaction types has no single
   independent source to reconcile against — it must be decomposed before the
   reconciliation can be meaningful. The number of accounts is not the test;
   whether accounts align to reconcilable populations is.

2. **Revenue disaggregated by obligation type.** ASC 606 / IFRS 15 requires
   disclosure of revenue disaggregated by how the nature, amount, timing, and
   uncertainty of revenue and cash flows are affected by economic factors. A
   music enterprise that books all royalty income to a single revenue line
   cannot produce this disaggregation from the ledger without sub-ledger
   reconstruction — a documentation and reporting risk at each close.

3. **Advance and liability accounts isolated.** Advances received are
   liabilities until obligations are satisfied. Advances paid are assets until
   recouped. An account structure that commingles advances with operating
   income or operating expense produces classification errors that compound
   into revenue-recognition and balance-sheet misstatements.

4. **Intercompany accounts segregated.** Every intercompany position has a
   dedicated account, by entity pair, that reconciles to zero on consolidation.
   An intercompany amount embedded in a shared operating account cannot be
   identified for elimination without reclassification — a consolidation risk.

---

### Account block assignments for music enterprises

Numeric block structure adapted to music-enterprise needs. Block ranges are
illustrative of the *structure* standard; specific numbers are an organizational
policy decision documented in the COA policy.

| Block | Category | Music-specific notes |
|---|---|---|
| 1000–1099 | Cash and cash equivalents | Sub-accounts per bank account; sweep and restricted cash segregated |
| 1100–1199 | Royalty and trade receivable | Streaming AR by platform; sync AR; PRO/mechanical receivable; neighboring-rights receivable |
| 1200–1299 | Prepaid expenses | Prepaid licensing fees; prepaid insurance by agreement |
| 1300–1399 | Recoupable recording advances | One sub-account per active advance-bearing recording agreement |
| 1400–1499 | Recoupable publishing and licensing advances | One sub-account per publishing or licensing advance |
| 1500–1599 | Other recoupable assets | Co-venture advances; video production recoupables |
| 1600–1699 | Music catalog and intangible assets (gross) | Acquired master rights; acquired publishing rights; by catalog or acquisition |
| 1700–1799 | Accumulated amortization and impairment | Contra-asset accounts mirroring 1600–1699 by catalog |
| 1800–1899 | Other long-term assets | Security deposits; equipment; leasehold improvements |
| 1900–1990 | Intercompany receivables | One sub-account per counterparty entity; eliminates on consolidation |
| 2000–2099 | Accounts payable and trade payables | Standard AP by vendor category |
| 2100–2199 | Royalty payable — recording | Sub-accounts by artist or recipient tier; unmatured vs. overdue segregated |
| 2200–2299 | Royalty payable — publishing and mechanical | Sub-accounts by publisher, songwriter, or CMO; by territory where material |
| 2300–2399 | Royalty payable — neighboring rights | Sub-accounts by CMO or performing-artist group |
| 2400–2499 | Deferred advance income | One sub-account per advance with a remaining performance obligation |
| 2500–2599 | Other deferred revenue | Non-advance deferred amounts; label-services retainers not yet earned |
| 2600–2699 | Accrued liabilities | Accrued streaming royalties payable to artists; accrued PRO settlements; accrued audit reserves |
| 2700–2799 | Tax liabilities | Withholding-tax payable by jurisdiction; income-tax payable |
| 2800–2899 | Debt and notes payable | Catalog-backed financing; production loans |
| 2900–2990 | Intercompany payables | Mirror to 1900 block; zero on consolidation |
| 3000–3999 | Equity accounts | Owner capital; retained earnings; accumulated other comprehensive income |
| 4000–4099 | Streaming royalty income | Sub-accounts by platform or contract tier; principal vs. agent treatment enforced in sub-accounts |
| 4100–4199 | Sync licensing fees | Sub-accounts by sync category (film, TV, advertising, video game, other) |
| 4200–4299 | PRO performance income | Sub-accounts by PRO (e.g., ASCAP, BMI, SESAC, SOCAN, PRS, APRA, STIM) |
| 4300–4399 | Mechanical royalty income | Sub-accounts by source (MLC blanket license, physical mechanical, direct mechanical) |
| 4400–4499 | Neighboring-rights income | Sub-accounts by CMO and by territory where material |
| 4500–4599 | Physical and download income | Sub-accounts by format and channel |
| 4600–4699 | Label-services and distribution income | Revenue from services rendered to roster or third-party clients; agent income on principal-agent test |
| 4700–4799 | Breakage income | Income recognized from permanently retained advance balances; distinct account per pattern |
| 4800–4899 | Other and non-operating income | Interest income; FX gains; miscellaneous |
| 5000–5999 | Cost of royalties | Artist and songwriter royalty expense where recognized on gross basis |
| 6000–6999 | A&R and creative expense | Recording, session, production costs not recoupable |
| 7000–7999 | Marketing and promotion | Radio promotion, playlist pitching, advertising, touring support (non-recoupable) |
| 8000–8999 | General and administrative | Salaries; professional fees; office; insurance |
| 9000–9999 | Intercompany income and expense | Internal management fees; shared-service charges; eliminates on consolidation |

**Account proliferation discipline.** A sub-account is added only when a
distinct reconciliation population requires it. Every inactive account is
deactivated on a defined review cycle — an account with a balance and no
recent activity is either obsolete (deactivate) or needs explanation
(document).

---

### Revenue account design: the streaming block in detail

Streaming income (4000–4099) is the highest-volume and highest-complexity
revenue stream for most music enterprises. COA design here determines whether
platform-level reconciliation is possible and whether the principal-vs.-agent
determination is enforced in the ledger rather than estimated at reporting time.

**Platform disaggregation minimum.** Material streaming platforms are
individually sub-coded. A platform representing more than approximately 5% of
streaming income is a natural threshold, but reconciliation tractability is
equally important — a platform sub-account can be reconciled to that platform's
statement; an aggregated account cannot.

**Principal-vs.-agent split.** Where the entity acts as principal on some
streaming arrangements (owns or controls the rights; licenses directly;
recognizes gross) and as agent on others (passes through rights; earns a
commission; recognizes net), these are in separate sub-accounts. Commingling
gross and net amounts in a single account makes the revenue-recognition
disaggregation unavailable from the GL and requires sub-ledger reconstruction
at each close — an audit-trail gap that should be eliminated by design.

**Lag-period accruals in a distinct sub-account.** Streaming accrual entries
for the lag period at close are posted to a distinct accrual sub-account within
the 4000 block. When the actual platform statement arrives, the accrual is
reversed and the confirmed amount posted to the platform sub-account. A system
that posts both to the same account cannot distinguish confirmed from estimated
income without reading the journal entry detail — an unnecessary audit burden
and a break-identification risk.

---

### Royalty payable account design: the reconciliation foundation

The royalty payable accounts (2100–2299) are the most complex and highest-risk
liability accounts. COA design choices made here have direct consequences for
reconciliation methodology at every close.

**Recipient-level vs. tier-level sub-accounting — two valid designs:**

- **Recipient-level:** one sub-account per contractual recipient. Maximum
  reconciliation granularity; the sub-ledger *is* the COA. Practical for
  rosters under approximately 50 active agreements; the GL itself produces
  the reconciliation schedule.

- **Tier-level with a sub-ledger:** accounts by recipient category (major
  artist; direct-signed artist; third-party publisher; mechanical payable)
  with sub-ledger detail maintained outside the GL. Scalable to larger
  rosters; requires the sub-ledger to reconcile to the GL at each close —
  an additional reconciliation layer, but standard practice for enterprises
  with hundreds of active agreements.

The design choice is documented in the COA policy; either is acceptable if
the reconciliation methodology is consistent with the chosen design. A
tier-level design with no reconciled sub-ledger is a controls gap — the GL
balance cannot be independently verified without it.

**Unmatured vs. overdue segregation.** Royalties earned but not yet due for
payment (before the contractual statement date) are distinguished from amounts
past the contractual remittance date. Commingling masks overdue obligations —
a compliance and contractual-breach risk that the account structure should
prevent structurally, not detect manually.

---

### Recoupable advance account design

Recording and publishing advances (1300–1499) are assets representing
amounts paid out that will be recovered through future royalty withholding.
Account design governs whether the required register reconciliation can run
from the GL.

**One sub-account per active advance-bearing agreement.** The recoupable
balance register (one row per agreement) reconciles in total to the sum of
the corresponding sub-accounts at each close. A pooled account aggregating
all recording advances cannot be reconciled against the register without a
sub-ledger. For portfolios beyond approximately 20 active agreements, a
sub-ledger with a pooled GL account is the standard design; for smaller
portfolios, direct GL sub-accounting avoids the additional reconciliation
layer.

**Impaired advances: segregated.** Once an advance balance is assessed as
impaired (unlikely to be fully recovered within the remaining term), the
impaired portion is tracked in a dedicated impairment reserve or contra
sub-account, with the full impairment disclosed separately from the
unimpaired balance. Netting the impaired and unimpaired amounts in a single
account obscures the accounting judgment and the remaining exposure.

---

### Intercompany account design

Intercompany accounts (1900s / 2900s) receive the most rigorous design
discipline because errors aggregate at the consolidated level.

- **Named by entity pair.** Account 1910 = Intercompany Receivable — [Entity
  B]; Account 2910 = Intercompany Payable — [Entity B]. On consolidation,
  the pair eliminates when correctly stated.
- **No general "intercompany clearing" account.** An account named
  "intercompany clearing" or "due to/from affiliates" without entity
  designation cannot be reconciled to a counterparty balance — a
  consolidation design failure that creates chronic break risk.
- **Transaction-level posting.** Each intercompany transaction is posted at
  transaction level, not netted at period end. Netting obscures the number
  of open transactions and makes period-end settlement confirmation
  impractical.

---

## MUSIC MODULES

### Close-sequence account review order

The controller's close review follows accounts in the order their
reconciliation dependencies resolve:

1. **Cash first.** Bank reconciliation is the most independent anchor;
   settled disbursements confirm payments that may affect royalty payable
   and advance accounts downstream.
2. **Royalty receivable (1100 block).** Streaming AR aged by platform,
   confirmed against platform statements or accrual methodology; PRO and
   mechanical receivable confirmed against distribution advice.
3. **Royalty payable (2100–2299).** Reconciled after corresponding
   receivable accruals are confirmed, since earned amounts drive the
   payable.
4. **Recoupable advances (1300–1499).** After royalties are confirmed,
   recoupment applications are updated and the register reconciled to the
   GL.
5. **Deferred income (2400–2499).** After advance receipt posting; release
   entries confirmed against performance milestones.
6. **Intercompany (1900 / 2900 blocks).** After intra-group transactions
   are confirmed; eliminations prepared before consolidated statements are
   assembled.
7. **Revenue accounts (4000–4799).** After all accruals are confirmed; the
   revenue accounts are the output of the above steps, not an independent
   source.

**Key misclassification patterns the close review must catch:**

| Incorrect classification | Correct classification | Misstatement impact |
|---|---|---|
| Advance received → revenue | Deferred advance income (2400 block) | Premature revenue recognition |
| Advance paid → A&R expense | Recoupable advance (1300/1400 block) | Balance sheet misstatement; distorted margins |
| Confirmed streaming income and lag accrual → same account | Confirmed: platform sub-account; accrual: lag accrual sub-account | Confirmed/estimated commingling |
| Intercompany charge → marketing expense | Intercompany expense (9000 block) | Elimination failure on consolidation |
| Impaired advance → no adjustment | Impairment reserve contra to advance account | Asset overstatement |
| Royalties due but not yet paid → commingled with unmatured | Overdue segregated from unmatured in royalty payable accounts | Masked compliance obligation |

---

### COA maintenance controls

A COA drifts without governance. The controller-owned maintenance controls:

- **Activation gate.** A new account is activated only by the controller
  against a stated need and reconciliation method; accounts are not
  self-provisioned by operating functions.
- **Deactivation cycle.** Inactive accounts (no postings in the trailing 12
  months for a recurring account) are reviewed and either deactivated or
  their inactivity documented. An active account with zero activity for 12
  months is either obsolete or needs an explanation.
- **Mapping integrity.** Accounts map to the reporting structure (P&L lines,
  balance sheet lines, revenue disaggregation schedule) in the ERP; the
  mapping is reviewed on a defined cycle and after any structural change to
  the entity's business model.
- **Period-over-period anomaly check.** At each close, the controller reviews
  accounts with no prior-period balance that have a current balance, and
  accounts with a prior balance now at zero — both are change signals
  requiring explanation, not automatically correct.
- **COA policy document.** The COA is governed by a written policy stating
  who can activate accounts, what the numbering scheme is, how sub-ledger
  accounts relate to GL accounts, and the review cycle. A COA with no
  governing policy is a configuration, not a controlled asset.
