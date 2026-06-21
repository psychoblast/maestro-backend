# Capital Stack & Sourcing

Capital and funding doctrine for a music and adjacent media/tech enterprise. The
operating layer here is the **financing decision** — which source, which
instrument, what terms, in what sequence — not cash-flow modeling, deal
negotiation, or legal papering, which belong to other domains.

These frameworks are practitioner-consensus corporate finance applied to the
music sector. All rates, multiples, and benchmarks are illustrative: treat any
specific number as an ESTIMATE to be confirmed against current market data
before it drives a recommendation. Never fabricate a rate, valuation, coverage
ratio, or eligibility determination — state the basis or label it an estimate
with a named comparable and stated assumptions.

---

## The capital stack: structure and ordering

A capital stack is the complete set of financing instruments an enterprise
uses, ordered from most senior (lowest risk, first claim, lowest expected
return) to most junior (highest risk, last claim, highest expected return). The
stack determines who gets paid first in a liquidation, how much control each
provider holds, and what the true blended cost of the whole capital base is.

Canonical ordering by seniority and cost:

| Tier | Source category | Claim priority | Dilution / encumbrance | Expected cost |
|------|-----------------|----------------|------------------------|---------------|
| 0 | Non-repayable grants / subsidies | None | None | Near-zero (matching + compliance overhead only) |
| 0 | Tax credits / refundable incentives | None | None | Processing lag + eligible-expenditure discipline |
| 0 | Sponsorship / partnership capital (non-equity) | None (contractual) | Reputational; possible use restrictions | Activation + licensing costs |
| 1 | Secured senior debt (first-lien) | First claim on named collateral | Lien on pledged assets | Lowest cash cost; covenant-intensive |
| 2 | Secured subordinated debt (second-lien) | Second claim on collateral | Subordinated lien | Higher cash cost; tighter compliance |
| 3 | Revenue-based / royalty financing | First claim on a named revenue stream | Revenue encumbered (not ownership dilution) | Moderate; effective cost needs full modeling |
| 4 | Unsecured / mezzanine debt | General claim; subordinated | Guarantee risk; often PIK or convertible | High; frequently carries an equity kicker |
| 5 | Convertible instruments / preferred equity | Hybrid; priority over common | Conversion dilution; liquidation preference | Variable; conversion dilution must be modeled |
| 6 | Common / venture equity | Last claim; full dilution | Permanent ownership transferred | Highest; paid at the exit event |

The structural principle: every tier prices the risk of being junior to the
tiers above it. A first-lien secured lender bears less risk than a common-equity
holder and expects commensurately less return. This risk-return ordering is not
a preference — it is how all capital markets price risk.

---

## Non-dilutive-first sequencing — the governing principle

Before any dilutive or encumbering source is recommended, the cheapest and
least-constraining sources must be evaluated and dispositioned. The governing
sequence is:

> **grants → tax credits → subsidies → sponsorship/partnership capital → revenue financing → royalty financing → debt → equity**

Each source is dispositioned — **eligible and pursuing / eligible and declined
(with stated reason) / ineligible (with stated basis)** — before the next tier
is recommended. A recommendation that reaches for equity or debt without showing
that earlier tiers were evaluated and found insufficient is structurally
incomplete. This is a binding analytical requirement, not a courtesy check.

**Why it matters economically.** The cost of a structure is not the headline
rate on the chosen instrument — it is the blended weighted-average cost across
every tier deployed, including the implicit cost of cheaper alternatives
foregone. Skipping an available non-dilutive source overstates the enterprise's
cost of capital. The penalty is large: a grant covering a material fraction of a
project at near-zero financial return is a fundamentally different economics
than funding the same amount with equity at a high implied discount rate.

---

## True cost of capital: the all-in calculation

The headline cost (interest rate, dividend preference, grant matching ratio) is
never the true cost. True cost incorporates every economic obligation and
constraint the financing imposes:

1. **Direct financial cost** — the headline rate, dividend, or revenue/royalty
   percentage on the principal or revenue base.
2. **Matching obligations** — grants and some subsidies require the enterprise
   to contribute or raise matching capital. The match is a real cost: it either
   consumes capital available for other uses or requires additional fundraising
   at market rates. Model the total package, grant plus match.
3. **IP and commercialization restrictions** — use restrictions, ownership
   strings, or commercialization limits constrain monetization of the funded
   work. This is an encumbrance on the asset's future value, not a fee.
4. **Reporting, compliance, and administration overhead** — covenant
   monitoring, grant compliance, and investor reporting consume real management
   time and direct cost, especially when several obligations with distinct
   cycles are stacked.
5. **Clawback-risk discount** — any right to demand repayment on a trigger is a
   contingent liability. Its expected cost is *probability of trigger × amount
   subject to clawback*, and it belongs in the cost model.
6. **Dilution cost** — for equity, the true cost is the present value of the
   ownership share transferred, valued at a realistic exit and discounted to
   today. Headline percentages hide the real cost until a liquidation-preference
   waterfall and exit scenario are modeled.
7. **Encumbrance cost** — a lien or revenue pledge constrains the enterprise's
   ability to use that asset as future collateral or to sell it freely. The
   optionality cost is real even if no default occurs.
8. **Time-value of matching timing** — match capital is often spent before or
   alongside grant disbursement. The cash-flow mismatch is a real bridge cost,
   frequently omitted from grant economics.

**Effective-cost framework:**

```
Effective annual cost =
  [ direct return to funder + matching obligation + IP-restriction value cost
    + compliance overhead + clawback-risk discount + dilution present value
    + encumbrance optionality cost + bridge financing cost ]
  ÷ net capital received after all required co-expenditures
```

Expressing this as an IRR over the expected term produces a comparable across
sources — the metric that allows fair ranking between, say, a grant with a heavy
match and subordinated debt at a stated annual rate.

---

## WACC and IRR as comparison tools

**Weighted-average cost of capital (WACC)** is the enterprise-level blended cost
of all capital in the stack, weighted by each source's share of the total
(`WACC = Σ weight_i × cost_i`, by market value, after tax). It is the minimum
return the enterprise must earn on its assets to satisfy every provider; returns
above WACC create value, below it destroy value. Grants and subsidies enter the
base at near-zero cost and lower the blended WACC materially — every grant dollar
displaces a higher-cost equity or debt dollar. That is the structural argument
for maximizing non-dilutive access first.

**Internal rate of return (IRR)** is the correct comparison metric when term
structures, disbursement timing, or cash-flow profiles differ. IRR is the
discount rate that zeroes the NPV of the full cash-flow profile
(`Σ CF_t / (1+IRR)^t = 0`). For royalty financing in particular, the stated
revenue-share percentage is *not* the cost of capital — the IRR requires
modeling the actual payment stream, collection timing, and final settlement, and
is typically materially higher than the headline percentage.

| Source | IRR driver | Key modeling variable |
|--------|-----------|----------------------|
| Non-repayable grant | Cost of raising the required match | Match ratio and match-raising cost |
| Tax credit | Processing lag; advance discount if monetized early | Refundable percentage; timing to receipt |
| Revenue financing | Revenue % × revenue trajectory | Forecast accuracy; early-payoff option value |
| Royalty advance | Total royalty stream relinquished vs. capital received | Royalty trajectory under base/bear/bull |
| Mezzanine debt | Coupon + PIK + equity-kicker value | Equity value at exit |
| Common equity | Ownership % × exit valuation | Exit multiple and timing |

---

## Source-ranking methodology

Evaluate each candidate source across four criteria:

1. **Accessibility** — realistically available to this enterprise at this stage,
   given eligibility, application capacity, funder pipeline, and timing.
2. **Effective cost** — the all-in IRR per the framework above. Cheapest
   realistic option ranks first.
3. **Fit to use** — structurally appropriate to the stated use of proceeds:
   equity for long-duration uncertain returns, debt for cash-flow-positive
   assets, grants for specific eligible activities, royalty financing for
   predictable contracted revenue.
4. **Constraint profile** — operational restrictions, compliance burden,
   dilution, or encumbrance imposed. A cheaper but heavily restrictive source
   may rank below a modestly more expensive, less constraining one.

Required output format for any multi-source comparison:

```
Source A: [type] | Effective cost: [X% IRR, estimate] | Fit: [match/mismatch] | Constraint: [low/med/high] | Disposition: [pursuing/ineligible/declined w/ reason]
Source B: ...
```

Disposition is stated for **every** source evaluated, not just the recommended
one. Omitting the disposition of non-recommended sources is incomplete analysis.

---

## Capital-stack interaction effects

The structure already in place constrains what can be added. These interactions
are a common source of covenant violations and structural failures:

- **Cross-collateralization** — when instruments share collateral, seniority
  decides who is made whole first. A second lien on an already-pledged catalog
  gives the illusion of security, not reliable security. Model the collateral
  coverage ratio under the *full* lien stack, not the new instrument alone.
- **Covenant stacking** — the effective constraint across stacked instruments is
  the *most restrictive* covenant, not any single one. Breaching one covenant
  can trigger cross-default provisions that accelerate every instrument at once.
- **Grant stacking limits** — some programs forbid stacking with named programs
  or cap the aggregate subsidy rate on a project. Verify that stacking is
  permitted and aggregate ratios stay within limits before structuring it.
- **Change-of-control interactions** — debt and grant agreements often
  accelerate or claw back when a new investor crosses an ownership threshold. An
  equity raise can inadvertently trigger a debt acceleration or grant clawback.
  Check change-of-control thresholds across the entire stack before any issuance.

---

## Encumbrance mapping and optionality

Every claim on an asset — a lien, a revenue pledge, an IP string, a grant
condition — reduces that asset's future optionality, and each layer compounds
the reduction. At any decision point you must be able to state: what claims
exist on each major asset, in what seniority, at what outstanding balance, and
for what remaining term. An enterprise that cannot answer this does not know its
own capital-structure risk.

All else equal, prefer structures that preserve optionality:

- shorter term over longer (optionality returns sooner)
- named-asset lien over blanket enterprise lien
- revenue pledge on a named stream over a blanket cash-sweep
- callable / prepayable over non-prepayable
- staged, milestone-linked tranches over a single full-draw commitment

Irreversible commitments — permanent IP transfer, uncapped equity dilution,
unlimited personal guarantee — foreclose options that cannot be restored. The
house rule on reversibility applies with full force: an irreversible financing
commitment requires proportionally stronger evidence than a reversible one.

---

## Music-sector capital characteristics

Music and adjacent media enterprises have access to a non-dilutive tier far
richer than most industries — public cultural-production support,
collective-society distributions, and sector-specific tax regimes. This makes
the non-dilutive-first doctrine *more* consequential here: reaching for equity
or debt while sector grants and credits are available is a larger capital-
allocation error than in a comparable non-cultural business.

Adjustments to standard cost-of-capital thinking for music:

- **Illiquidity premium** — masters, publishing catalogs, and repertoire are not
  instantly liquid; the cost of equity carries a premium over a comparable-risk
  liquid business. Deal- and stage-specific.
- **Catalog-vs-enterprise distinction** — a catalog of owned rights generating
  contractual royalties carries a different (lower, more predictable) cost of
  capital than a music operating company (label, management, publishing admin)
  whose income depends on execution. Applying one blended rate misprices both.
- **Hit-rate volatility premium** — operating enterprises with active A&R or
  publishing pipelines have power-law outcome distributions; a few hits drive
  most returns. Effective volatility exceeds what financial statements suggest,
  so the cost of equity must reflect it.
- **Royalty financing as semi-equity** — it does not dilute ownership but it
  reduces the present value of future free cash flow, the same economic output
  as equity. Include its effective cost as a weighted component of WACC; treating
  it as cost-free because it carries no interest rate understates WACC.
- **Grant subsidy effect** — a non-repayable grant dollar replaces an equity or
  debt dollar at near-zero cost; the WACC benefit is *grant share × displaced
  source's cost*.
