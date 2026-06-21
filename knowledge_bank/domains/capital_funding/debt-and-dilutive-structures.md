# Debt & Dilutive Structures

After the non-dilutive sequence is exhausted, debt is evaluated before equity.
This file covers debt structure and coverage analysis, catalog/IP-backed
lending, equity and dilution math, the cap-table waterfall, and matching the
instrument to the use. Both debt and equity sit below every non-dilutive source
in the governing sequence — they fund only the gap that cannot be filled more
cheaply.

All thresholds and ratios below are illustrative; confirm market-standard levels
against current data before they drive a recommendation.

---

## Matching the instrument to the use

The first question for any debt or equity recommendation is structural fit, not
price:

- **Equity** suits long-duration, uncertain-return investment where there is no
  contractual cash flow to service near-term obligations.
- **Debt** suits cash-flow-positive, revenue-generating assets that can service
  scheduled payments.
- **Revenue/royalty financing** (non-dilutive but encumbering) suits predictable,
  contracted revenue streams.

A common, costly mismatch is using equity for short-term working capital (the
most expensive possible source for the cheapest possible need), or pledging
catalog-backed debt against royalty streams that should remain unencumbered for a
future, larger raise.

---

## Debt structure and coverage analysis

**Debt service coverage ratio (DSCR)** is the core feasibility metric:

```
DSCR = cash flow available for debt service ÷ scheduled debt service
```

A DSCR above 1.0× means base-case cash flow covers the obligation; lenders
typically want cushion above that. Evaluate DSCR under base **and** conservative
scenarios, not optimistic only — a structure that services only under optimistic
assumptions is a default waiting for a normal-bad quarter.

| DSCR at base case | Reading |
|-------------------|---------|
| ≥ 1.5× | Comfortable cushion |
| 1.2×–1.5× | Serviceable with monitoring |
| 1.0×–1.2× | Thin; conservative case likely breaches |
| < 1.0× | Not serviceable at base — do not recommend |

**Collateral and seniority** — secured debt prices lower because it has first
claim on named assets. Prefer a **named-asset lien** over a **blanket
enterprise lien**: it constrains less of the balance sheet and preserves
collateral for future raises. Always model collateral coverage under the full
lien stack, since a junior lien on already-pledged collateral provides the
illusion of security, not security.

**Mezzanine and hybrid debt** carry the highest cash cost and often an equity
kicker (warrants, PIK conversion). Their effective cost includes the kicker's
value at exit — a mezzanine instrument priced only on its coupon is mispriced.

---

## Catalog and IP-backed financing

Music IP — master recordings and publishing catalogs generating contractual
royalty income — can secure debt. Specifics that matter:

- **Catalog vs. operating-enterprise risk** — catalog income is more predictable
  and more readily encumbered than operating-company income. Lenders advance
  against the predictability of the royalty stream, valued from its history and
  decay profile.
- **Valuation for lending** — catalog lending is sized off a multiple of
  net publisher's share or net label income, discounted for decay, concentration
  (over-reliance on a few works), and collection risk. Treat any specific
  multiple as an estimate to verify.
- **Encumbrance consequence** — pledging the catalog as collateral removes it
  from the menu of future financing and sale options for the term of the loan.
  That foregone optionality is a real cost even if no default occurs, and is
  scored on optionality/reversibility.
- **Security interest is not ownership transfer** — a security interest that
  *releases on repayment* is normal and acceptable; a clause that permanently
  alienates ownership or grants an irrevocable exclusive license is a fatal term
  (see terms-and-covenant analysis).

---

## Equity and dilution math

Equity is the last tier in the sequence and the most expensive — its true cost is
the present value of the ownership share transferred, valued at a realistic exit
and discounted to today. Headline percentages obscure this until the structure is
modeled.

**Basic dilution.** Issuing new shares dilutes existing holders pro rata:

```
post-money valuation = pre-money valuation + new investment
investor ownership   = new investment ÷ post-money valuation
founder/existing dilution = new shares ÷ total shares after issuance
```

Show the cap-table impact **before and after**, not just the headline percentage.
Model dilution under base/bull/bear so the spread of outcomes is visible.

**The option pool shuffle** — when an investor requires a new or enlarged option
pool created *pre-money*, the dilution lands entirely on existing holders, not on
the new investor. Name where the pool is struck; it materially changes effective
dilution.

---

## The liquidation-preference waterfall

What an ownership percentage is *worth* at exit depends on the preference stack,
not the percentage alone:

- **Liquidation preference** — preferred holders are paid back their investment
  (1×, or a multiple) before common sees proceeds. A high multiple can leave
  common with little even at a healthy headline valuation.
- **Participating vs. non-participating** — participating preferred takes its
  preference *and then* shares in the remainder as if converted ("double dip");
  non-participating takes the greater of its preference or its as-converted
  share. Participating preference materially lowers the value of common.
- **Seniority of preferences** — in multi-round stacks, later money is often
  senior; model the waterfall in payment order.

Always run the waterfall at realistic exit values (base/bull/bear) to show what
each class actually receives — that is the real dilution, and it feeds the
true-cost calculation.

---

## Convertible instruments

Convertible notes and SAFEs defer the valuation question to a later priced
round. Watch:

- **Discount and valuation cap** — both set the effective conversion price; the
  cap can produce far more dilution than the headline discount suggests if the
  next round prices well above the cap.
- **Conversion mechanics** — model the fully-diluted cap table *after* conversion
  of all outstanding instruments, not before; a stack of uncapped-looking notes
  can convert into a surprising ownership share.
- **Interest and maturity** — accrued interest converts too; a maturity date that
  arrives before a priced round can force repayment or a distressed conversion.

---

## Cap-table and structure preservation

Two structural checks belong on every dilutive recommendation:

1. **Optionality for the next event** — does this structure preserve the ability
   to raise the next round on reasonable terms, or does it foreclose it (e.g.,
   senior preferences, anti-dilution ratchets, or a pre-emptive over-allocation)?
   Model the cap-table pro forma through the anticipated next round.
2. **Control and ownership boundaries** — does the structure create a hidden
   control transfer (board control, protective provisions, change-of-control
   triggers, an uncapped equity ratchet)? Keep client/entity boundaries and
   IP-ownership lines intact, and verify no covenant or trigger silently moves
   control.

Any structure that would materially alter control or ownership, cross a leverage
limit, or encumber the catalog beyond a governance threshold is escalated for
executive sign-off, flagged in the recommendation header — not buried in the
body.
