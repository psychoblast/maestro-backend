# Catalog Acquisition and Intangible Asset Accounting

Controller's framework for the accounting treatment of acquired music catalogs and
other music-IP intangibles: purchase price allocation, useful-life determination,
amortization, and impairment. Valuation work and deal-economics judgment belong to
Finance; the controller verifies that the accounting treatment is correct,
documented, and consistently applied. Current-period specifics — discount rates,
statutory amortization periods, copyright term details by jurisdiction — are
maintained in the current-period reference layer and verified there before use.

---

## GENERAL FRAMEWORKS

### Asset acquisition vs. business combination: the threshold determination

Not every catalog purchase is an ASC 805 business combination. Whether a
transaction qualifies as a business combination (acquiring an integrated set
of assets *and* processes capable of producing outputs) or an asset acquisition
(acquiring assets without a process capable of independently producing outputs)
is the first accounting determination — and it changes subsequent treatment
materially.

**The business test (ASC 805-10-55):** does the acquired set include, at minimum,
inputs and a substantive process together capable of contributing to producing
outputs? A catalog plus the personnel and operational processes that actively
manage it typically meets the business test. A bare rights acquisition — a set
of master recordings or composition copyrights without operational infrastructure
or personnel — typically does not, and is accounted for as an asset acquisition:
no goodwill recognized; acquisition costs capitalized rather than expensed;
assets allocated by relative fair value at the acquisition date.

In practice, most standalone catalog acquisitions (buying rights from a rights
holder without acquiring an operating team) are asset acquisitions. Most
full music-company acquisitions that include management contracts, distribution
arrangements, and personnel are business combinations. The determination is
made and documented by the controller, in consultation with Legal where the
structure is ambiguous, before any purchase price allocation begins.

---

### Purchase price allocation: identifying acquired intangibles

Whether a business combination or an asset acquisition, acquired intangibles
must be identified and measured separately — from goodwill in a business
combination, or from each other by relative fair value in an asset acquisition.
The controller's obligation is to verify that the identification, measurement,
and resulting accounting treatment are documented — not to perform the
valuation.

**The recognition test for a separately identified intangible (ASC 805-20-25):**
an intangible is recognized separately from goodwill if it meets the separability
criterion (can be sold, transferred, licensed, rented, or exchanged separately
from the entity) or the contractual-legal criterion (arises from contractual or
legal rights, regardless of separability). Most music IP meets one or both tests.

**Intangibles commonly identified in music catalog acquisitions:**

| Intangible class | Recognition criterion | Common valuation approach |
|---|---|---|
| Master recording rights | Contractual-legal (ownership or control of masters) | Royalty-relief method; income approach on royalty streams |
| Music publishing rights (composition ownership) | Contractual-legal (copyright in composition) | Royalty-relief method; multi-income-stream income approach |
| Neighboring-rights interests | Contractual-legal | Income approach on CMO distributions |
| Sync licensing relationships | Separable (assignable) | Excess-earnings on identified sync client relationships |
| Distribution agreements | Contractual-legal | Income approach on distribution fee stream over remaining term |
| Artist service agreements | Contractual-legal | Remaining contractual cash flows |
| Non-compete agreements | Contractual-legal | Income approach on avoided-loss basis |
| Trade names and brand elements | Separable | Relief-from-royalty; applicable only where a recognized brand independently drives demand |

**The residual must represent something real.** Goodwill in a music-company
business combination typically represents assembled workforce, strategic platform
value, operating efficiencies, and market position — not catalog IP itself.
A purchase price allocation that collapses acquired music IP into goodwill
rather than identifying it separately is a misclassification: it understates
amortizable intangibles, overstates goodwill, distorts earnings from the
acquisition date forward, and creates an audit inquiry at every impairment test.

---

### Useful life determination: finite vs. indefinite

Acquired intangibles are classified as finite-lived (amortized over useful life)
or indefinite-lived (no amortization; annual impairment test). This determination
is the most consequential accounting judgment in catalog accounting — it affects
earnings from the acquisition date forward and anchors all subsequent impairment
assessment.

**The test (ASC 350-30-35):** an intangible has an indefinite useful life if
there is no foreseeable limit on the period over which it is expected to
contribute to the entity's cash flows. The test is not whether the intangible
could theoretically last forever; it is whether known legal, regulatory,
competitive, contractual, or economic factors set a foreseeable limit on the
period of cash-flow contribution.

**Music-specific useful life analysis:**

- **Composition copyrights (publishing rights).** In most major jurisdictions,
  copyright in a composition subsists for the life of the author plus 70 years.
  For a living songwriter or a recently deceased writer, there is no foreseeable
  legal limit within any reasonable planning horizon — indefinite useful life is
  supportable and typical. For a copyright in the final decade of its term, the
  remaining term is a defined finite useful life. *The controller verifies that
  a legal-term analysis was performed and that the indefinite-vs.-finite
  determination is consistent with it; copyright terms by jurisdiction belong in
  the current-period reference layer.*

- **Master recording copyrights.** Copyright terms for sound recordings vary
  substantially by jurisdiction. A recently released catalog is typically
  indefinite-lived under accounting standards for major commercial territories;
  a catalog approaching its copyright expiry date has a defined remaining finite
  useful life. *Jurisdiction-specific copyright terms must be verified in the
  current-period reference layer before making or confirming this determination.*

- **Distribution agreements.** Fixed-term contracts with defined expiration
  dates — even if renewable — are finite-lived over the stated term unless the
  entity has a contractual renewal right it both intends to exercise and that
  requires no significant cost to renew. A five-year distribution agreement is
  a five-year finite intangible absent documented renewal assurance.

- **Non-compete agreements.** Finite-lived over their contractual period
  without exception. A three-year non-compete is amortized straight-line over
  three years; no indefinite-life argument is available.

- **Artist service agreements.** Finite-lived over the remaining contractual
  term. Renewal rights, if present, are assessed separately; absent documented
  renewal assurance, amortization runs to the contractual end date.

**Consistency across the portfolio.** Useful life determinations must be
consistent across similar asset classes within the same acquisition. Treating
two comparable composition copyrights differently — one indefinite, one finite —
requires documented justification for the distinction. An internally inconsistent
allocation is a methodology failure, not a permissible exercise of judgment, and
will be flagged in any audit.

---

### Amortization: method and period

Finite-lived intangibles are amortized on the method that best reflects the
pattern in which economic benefits are consumed. Straight-line amortization is
the default in the absence of evidence that another pattern better reflects
consumption.

**Revenue-based amortization.** For music IP, a revenue-based method —
amortizing in proportion to the period's royalty income relative to expected
total royalty income over the asset's useful life — may better reflect
consumption when the income profile is front-loaded (newly released catalog
with declining revenue trajectory) rather than stable. Where a revenue-based
method is adopted:

- The projected income curve is documented with its source (Finance &
  Royalties), including key assumptions.
- The revision policy is stated: what events trigger a re-projection, and what
  is the process for controller approval of a change.
- The method is applied consistently; switching to straight-line to increase
  current-period amortization (and thus reduce taxable income) or to reduce
  it (and thus inflate reported earnings) without a documented change in
  consumption pattern is a manipulation signal.

**The amortization schedule** is a required documentation deliverable for every
finite-lived catalog intangible: starting gross carrying value; useful life;
method; annual amortization amount; accumulated amortization to date; net
carrying value at each period end. A close that does not include a current
amortization schedule for each finite-lived intangible leaves the balance sheet
unreconciled for that asset class.

---

### Impairment: the annual test and interim indicators

**Indefinite-lived intangibles (ASC 350-30):** tested for impairment annually
and whenever events or changed circumstances indicate fair value may have
declined below carrying amount. The test compares carrying amount to fair value;
when carrying amount exceeds fair value, an impairment loss is recognized for
the difference. The annual test is conducted using the royalty-relief method or
the income approach (discounted projected royalty cash flows), typically
performed by or with the external valuation specialist, and signed off by the
controller before the close in which the test date falls.

**Finite-lived intangibles (ASC 360):** tested for recoverability only when
events or circumstances indicate the carrying amount may not be recoverable.
The two-step test: Step 1 — can the asset's undiscounted projected cash flows
cover the carrying amount? If yes, no impairment. If no, Step 2 — measure the
impairment loss as the excess of carrying value over fair value.

**Music-specific impairment indicators:**

| Indicator | Assessment approach |
|---|---|
| Declining streaming trend — material, multi-period, and unexplained by seasonal pattern | Quantify the trend; revise the income projection; test against carrying value |
| Artist departure from label or material change in artist-brand trajectory | Assess impact on future cash flows; distinguish artist-branded from artist-independent catalog |
| Platform de-listing or exclusion of catalog | Identify affected income streams; estimate revenue exposure; quantify recovery path |
| Genre-level demand decline or format obsolescence | Assess whether decline is permanent or cyclical; benchmark against comparable catalogs |
| Territorial risk (currency devaluation, regulatory change, CMO solvency concerns) | Quantify territorial exposure; assess hedging position |
| Artist controversy or reputational event affecting consumption | Assess whether sync demand and streaming impact are structural or transient |
| Change in copyright interpretation or statutory royalty rate applicable to the catalog | Assess impact on projected mechanical or streaming income; re-project with revised rate |
| Significant adverse change in the business climate generally | Trigger an interim test; document the basis for assessing whether impairment exists |

**The controller's impairment role:** confirm the annual test was performed on
schedule; the methodology is documented; valuation assumptions are consistent
with prior-period tests or differences are explained; the result is a supportable
fair-value conclusion; and the conclusion is signed off by the controller before
close. The controller does not independently construct the fair-value estimate —
that belongs to the valuation function or external specialist. The controller
verifies the process, the documentation, and the accounting conclusion.

---

### The royalty-relief method: what the controller needs to know

The royalty-relief method (a form of the income approach) is the most widely
used technique for valuing acquired music IP. It calculates the fair value of
the IP as the present value of the royalty payments the entity would otherwise
have to pay to license the IP from a third party — the "relief" from that
hypothetical royalty obligation is the economic benefit of owning the IP outright.

**Controller's review of a royalty-relief valuation:**

The controller does not construct the valuation but reviews it for documentation
adequacy and internal consistency before accepting the purchase price allocation
entry:

1. **Projected income base.** Is it documented with its source (Finance's
   trailing actuals plus growth assumptions) and consistent with the accrual
   basis used in the entity's royalty receivable reconciliation? A valuation
   using income projections inconsistent with the entity's own royalty-accounting
   data is a process-disconnect signal.

2. **Royalty rate.** Is the rate sourced from observable market transactions,
   documented, and applied consistently across comparable asset classes? A rate
   without a documented market source, or with different rates for similar assets
   in the same allocation, is an unexplained methodology inconsistency requiring
   resolution before the entry is posted.

3. **Discount rate.** Is it documented as a risk-appropriate rate for the
   specific asset class? The rate for a stable back-catalog differs from the
   rate for a newly released, single-release catalog with limited track record;
   using a single rate for assets with materially different risk profiles is a
   methodology question to answer, not a silent assumption.

4. **Terminal value or finite horizon.** Does the model use a terminal value,
   a finite cash-flow window, or a declining-tail structure? Does the choice
   align with the useful-life determination? An indefinite-useful-life conclusion
   paired with a short finite cash-flow model and no terminal value understates
   fair value and should be resolved before the allocation entry is posted.

5. **Consistency with prior tests.** If the entity performed impairment tests
   on comparable catalog in the previous period, are the methodology and key
   assumptions consistent? Unexplained changes in key assumptions between
   periods are a documentation gap and an audit inquiry.

---

## MUSIC MODULES

### Post-acquisition integration into the close process

Acquired catalog assets enter the normal close process from the acquisition date.
The controller's Day 1 accounting checklist:

1. **Opening entry.** Records each acquired intangible at fair value (or cost
   in an asset acquisition), with each intangible class in its designated COA
   account; goodwill (if any) in the goodwill account. The entry traces to the
   purchase price allocation schedule, which is a signed, dated controller
   deliverable.

2. **Amortization schedule entered.** For each finite-lived intangible, the
   amortization schedule is prepared, approved, and entered into the
   fixed-asset / intangible-asset system before the first post-acquisition
   close. A close that runs before the schedule is established will either
   omit amortization (misstatement) or post an estimated amount without a
   documented basis (documentation gap).

3. **Royalty stream mapping.** Each acquired royalty stream is mapped to the
   entity's royalty receivable and income accounts. Legacy accounts from the
   acquired entity's COA (if it had its own), or from the prior administrator's
   reporting format, are rationalized into the acquiring entity's account
   structure before the first statement arrives.

4. **Cutover date confirmed.** The acquisition closing date is confirmed in
   writing with the acquiree and the successor administrator; transition-period
   royalty statements covering periods straddling the closing date are
   pre-allocated: the pre-close portion to a payable to the seller (or as a
   purchase price adjustment), the post-close portion to the acquiring entity's
   income.

5. **Assumed advance balances recorded.** If the acquired catalog includes
   existing recoupable advance balances (prior obligations to artists), these
   are recorded as assumed liabilities (if obligations to pay) or as acquired
   recoupable assets (if amounts recoverable), at their fair values as of the
   acquisition date. Their subsequent accounting follows the recoupable advance
   protocol in the recoupable-advance reconciliation framework.

**Recurring close obligations post-acquisition:**

- *Monthly:* amortization entries for all finite-lived catalog intangibles;
  reviewed and approved against the amortization schedule.
- *Quarterly:* review of any interim impairment indicators for material catalog
  assets; documented conclusion (no indicator identified, or indicator
  identified and further tested).
- *Annually:* formal impairment test for indefinite-lived intangibles;
  valuation specialist engaged or methodology run internally; results documented
  and signed off by controller.

---

### Common controller findings in catalog acquisitions

- **Assumed advance balances not identified.** The acquisition of a catalog
  with existing artist advance balances means the buyer assumed recoupment
  obligations to future royalty recipients — a liability, or a future offset
  against royalty payables. If the assumed balance is not identified and
  recorded at the acquisition date, the purchase price allocation and the
  opening royalty payable position are both misstated.

- **Royalty streams not mapped before the first post-acquisition close.** The
  first close after acquisition is the highest-risk: royalty statements may
  arrive from the prior administrator on the acquiree's historical timetable;
  the acquiring entity's systems may not yet have the rights registered. If
  mapping is incomplete before close, royalty income is either unaccrued
  (understated) or posted to the wrong account.

- **Pre-closing royalty income included in the buyer's income.** Royalties
  earned before the acquisition closing date belong to the seller. A royalty
  statement covering a period straddling the closing date must be split: the
  pre-close portion is credited to a payable to the seller (or applied as a
  purchase price adjustment); the post-close portion flows to the acquiring
  entity's income.

- **Goodwill allocated to the wrong reporting unit.** If acquired goodwill is
  allocated to a reporting unit that includes other goodwill-generating assets,
  impairment of the catalog-related goodwill may be masked by performance
  elsewhere in the reporting unit. The unit-of-account decision is documented
  and defensible before the first goodwill impairment test.

- **No interim impairment review when indicators arise.** Annual testing is
  the minimum; when a streaming decline, reputational event, or platform
  change occurs mid-year for a material indefinite-lived catalog, the controller
  triggers an interim analysis and documents the conclusion (including a
  conclusion that no impairment exists and why). An annual test that post-dates
  a known indicator by up to 12 months is not a clean audit posture.

- **Amortization method change without documentation.** Switching from
  revenue-based to straight-line amortization (or vice versa) is an accounting
  policy change requiring prospective application, a documented rationale, and
  disclosure in the financial statements. An undocumented method change is a
  consistency violation regardless of whether the new method is more appropriate.
