# Terms & Covenant Analysis

A financing's terms can be fatal even when its price and amount look attractive.
This file covers term-sheet anatomy, the fatal-term taxonomy, covenant risk
classification and stress-testing, clawback-trigger mapping, and the
music-specific covenant hazards in grant and label/investor deals. It backs the
**Terms & Covenant Risk** hard gate on the scorecard.

The financing-decision seat identifies and prices term risk; the actual drafting,
covenant papering, and legal opinion belong to legal review. Flag the boundary
and hand off — but never recommend proceeding past a fatal term.

---

## Term-sheet anatomy

A term sheet (offer letter, letter of intent, heads of terms) is a mostly
non-binding summary of proposed material terms — though it typically binds on
exclusivity and confidentiality. It is the cheapest, most actionable gate for
fatal-term identification: before legal costs mount, before diligence completes,
and before commitment creates sunk-cost pressure.

Standard sections:

1. **Amount and instrument** — total capital, instrument form, any tranching.
2. **Price / rate / share** — cost in the instrument's native unit (rate,
   ownership %, revenue-share %, royalty %, or nil for a non-repayable grant).
3. **Use of proceeds** — what the capital may and may **not** fund (restrictions
   matter as much as permissions).
4. **Term and maturity** — duration; when repayment, conversion, or compliance
   obligations come due.
5. **Representations and warranties** — what the recipient asserts is true;
   breach can trigger default.
6. **Conditions precedent** — what must occur before closing (diligence, legal
   opinions, consents, encumbrance releases).
7. **Affirmative covenants** — what the enterprise must maintain (reporting,
   insurance, business continuity, legal compliance).
8. **Negative (restrictive) covenants** — what it may not do without consent
   (additional debt, dividends, acquisitions, asset sales, new security
   interests).
9. **Security and collateral** — assets pledged and in what priority.
10. **Change-of-control provisions** — consequences if ownership/control shifts.
11. **Events of default** — what lets the funder accelerate or enforce.
12. **Remedies on default** — acceleration, enforcement, conversion, clawback.

For **grant agreements**, sections 3–12 have direct analogs: eligible
expenditures (use of proceeds), completion timeline (term), reporting (affirmative
covenants), IP/commercialization limits (restrictive covenants), clawback
triggers (events of default), and clawback mechanics (remedies). Analyze a grant
agreement through this lens — not as administrative paperwork — and the same risks
surface as in a debt term sheet.

---

## Fatal-term taxonomy

A fatal term creates unacceptable risk of loss of control, permanent ownership
transfer, unlimited financial exposure, or operational foreclosure. A structure
containing one is **NOT FUNDABLE** in its current form: the term must be removed
or renegotiated first. This is the terms hard gate.

1. **Unlimited personal guarantee** — an individual personally liable for the
   full obligation with no cap, no carve-out, and no sunset. Capped, asset-
   limited, or time-bounded guarantees are aggressive but not automatically
   fatal; *unlimited recourse* to personal assets is fatal.
2. **Automatic change-of-control trigger on ordinary activity** — acceleration,
   conversion, or repurchase that fires on normal business events (a new minority
   investor, a new key hire with equity, a management transition, a holding-entity
   restructure). Consent requirements for *major* events (>50% transfer, sale)
   are market-standard; triggers on ordinary activity are fatal because they
   freeze normal operation.
3. **IP alienation clause** — permanent transfer of master or composition
   ownership to the funder, or an irrevocable exclusive license functionally
   equivalent to transfer, without ongoing consent. A security interest that
   *releases on repayment* is normal; permanent alienation is fatal.
4. **Uncapped equity ratchet** — automatic increases in the funder's ownership on
   missed targets with no ceiling, allowing 100% takeover through
   underperformance — a foreclosure disguised as an incentive. A *capped* ratchet
   is aggressive but may be acceptable.
5. **Clawback on ordinary course of business** — a trigger firing on normal,
   unavoidable activity (commercial release, standard licensing, distribution).
   Triggers on *avoidable* conditions (misrepresentation, ineligible use, failure
   to complete) are manageable, not fatal.
6. **Commercialization prohibition on funded work** — a grant condition
   preventing commercial release, sync licensing, streaming, or sale of the
   funded music, permanently or for a value-impairing period. Incompatible with
   the premise that funded work is produced and then monetized. Fatal.

The distinction between fatal and merely aggressive is never the *presence* of a
restriction — all financing restricts. It is whether the restriction prevents
normal operation or permanently transfers a core asset without ongoing consent.

---

## Covenant risk classification

Every covenant creates risk even when not fatal. Classify each:

| Factor | Low risk | Moderate risk | High risk |
|--------|----------|---------------|-----------|
| Achievability at base case | Coverage easily ≥1.5× | Positive but constrained | Marginal or negative |
| Achievability at conservative case | Maintained with cushion | At/near threshold | Fails |
| Consequence of breach | Cure period; no immediate acceleration | Acceleration after cure | Immediate acceleration, no cure |
| Funder behavior on breach | Cooperative/workout history | Mixed | Adversarial or unknown |
| Operational constraint | No operational change needed | Modest discipline | Significant restriction on ordinary activity |
| Cross-default risk | None in the stack | One other instrument | Across the entire stack |

Standard financial covenant categories:

- **Coverage covenants** — minimum DSCR, royalty-coverage ratio, or revenue
  floor. Evaluate against base and conservative cash flows.
- **Leverage covenants** — max debt-to-EBITDA, debt-to-revenue, or debt-to-asset.
  Aggregate leverage across the stack is what binds; a new instrument within its
  own limit can push aggregate leverage past an existing instrument's covenant.
- **Liquidity covenants** — minimum cash, current ratio, or working capital. The
  most frequently breached by early-stage enterprises with lumpy cash flows;
  negotiate headroom above the realistic cash trough.
- **Operational covenants** — maintain key personnel, insurance, core activity,
  required licenses. Binary and execution-driven; identify the ones hardest to
  hold (key-person clauses are the common pressure point) and negotiate carve-outs
  or cure periods up front.

---

## Covenant stress-testing

Run projected cash flows and metrics against each covenant threshold under
multiple scenarios:

- **Base case** — performance in line with the operating plan.
- **Conservative case** — revenue meaningfully below plan; an unexpected expense;
  an underperforming stream.
- **Severe case** — revenue sharply below plan with multiple adverse conditions
  at once.

Process: (1) enumerate every covenant in the new instrument **and** existing
stack; (2) map each threshold onto the same model showing all three scenarios;
(3) compute compliance at each covenant measurement date; (4) find the first
scenario and date at risk of breach; (5) for each at-risk covenant, model cure
options — reserve drawdown, waiver request, equity injection, alternative
revenue, or service reduction.

This stress test populates the terms-and-covenant dimension score. A fatal term,
or covenant failure even under optimistic projections, fires the hard gate.

---

## Clawback-trigger mapping

Systematically enumerate every event that would let a funder demand the capital
back, each assessed for probability and magnitude:

| Trigger | Probability (estimate) | Amount at risk | Mitigation | Residual risk |
|---------|------------------------|----------------|------------|---------------|
| [specific term] | Low / Med / High | Full / Partial | [action] | Low / Med / High |

State probability directionally, not as false-precision percentages. When
multiple instruments carry correlated triggers (one revenue shortfall fires both
a grant clawback and a debt covenant breach), model the correlation — do not
treat triggers driven by a shared cause as independent.

---

## Music-specific covenant hazards

**Grant strings** are the most underestimated conditions in a music enterprise's
stack, and are largely non-negotiable (accept or decline):

- **Eligible-expenditure strings**, including the frequent **management-commission
  exclusion** — funded budgets often cannot carry management commissions; absorb
  them from non-grant funds or restructure for the funded period.
- **Content / eligibility-maintenance strings** — content thresholds must hold at
  application *and* delivery; lineup, producer, or collaborator changes can move
  output out of eligibility. Document the basis; pre-confirm anticipated changes.
- **IP / exploitation strings** — qualifying-distributor requirements, mandatory
  credits/attribution, and assignment restrictions; any IP transaction touching
  funded works routes to legal first.
- **Matching-source strings** — no double-counting the same dollar across
  programs; arm's-length match; in-kind eligibility with valuation rules.

**Label and investor deal hazards:**

- **360 / revenue-participation covenants** — participation across touring,
  merch, endorsements, sync, and publishing creates broad disclosure and
  reporting obligations; map them to a reporting discipline before signing, since
  an unreported new revenue stream can breach inadvertently.
- **Cross-collateralization across releases** — a shortfall on one release
  charged against the next keeps the artist "unrecouped" despite real gross
  revenue. Not fatal alone, but it must surface explicitly in the recoupment
  modeling and the effective-cost calculation, or the true cost is obscured.
- **Key-person provisions** — scrutinize what triggers them (departure vs.
  reduced creative involvement vs. rebranding), the counterparty's rights on
  trigger (consent vs. termination/acceleration), whether a cure/transition
  exists, and whether they conflict with planned succession.
- **Audit-obligation covenants** — investor/lender requirements to maintain books
  in specific formats or have them audited by specific firms can burden a small
  enterprise; assess against current accounting infrastructure before accepting.

---

## Covenant-breach monitoring

An unmonitored covenant breaches without warning, losing the cure window most
agreements provide. Assign an internal owner to each obligation and maintain an
active compliance calendar:

| Covenant type | Cadence | Alert threshold |
|---------------|---------|-----------------|
| Coverage ratios (DSCR, royalty coverage) | Monthly vs. reported data | ≤1.3× — escalate to finance and legal |
| Leverage ratios | Quarterly | Approaching limit → immediate review |
| Liquidity / minimum cash | Monthly | Within 15% of floor → escalate |
| Grant reporting obligations | Per-program calendar | 30 days before each deadline |
| Eligible-expenditure compliance | Transactional | Flag any questionable expenditure before committing |
| IP-restriction compliance | Event-triggered | Any IP transaction on funded content → legal first |
| Key-person / personnel covenants | Event-triggered | Any change affecting named individuals → review before announcing |
