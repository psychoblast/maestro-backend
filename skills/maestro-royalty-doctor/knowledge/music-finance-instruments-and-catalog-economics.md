# Music Finance Instruments & Catalog Economics

This file covers the financial mechanics that sit adjacent to royalty collection:
how streaming income is actually generated at the platform level, what different
recording and publishing deal structures mean for the artist's actual take-home,
how catalog-backed lending and outright catalog sales work, and the tax basics
that affect how royalty income is kept. The recovery specialist uses this knowledge
to distinguish what the artist is owed under the deal they signed from what the
deal actually delivers — and to route deal-structure and valuation questions to
the Finance/Royalties function with the right framing.

---

## 1. Streaming Economics — How the Per-Stream Rate Is Calculated

The per-stream royalty is not a fixed price. It is a derived rate — the result of
a pool allocation divided by total streams — and it changes every period based on
how much the service earned and how much content was streamed.

### The Streaming Royalty Pool

The DSP's gross revenue (subscription fees + advertising revenue) is divided
between the DSP and rights holders. The rights-holder share is commonly
approximately 70% of gross service revenue (Tier C — specific percentages are
commercially negotiated and not public; treat this as a working approximation,
not a contract term). Of the rights-holder pool, roughly 75% goes to master
recording rights holders and 25% to composition rights holders — again, these
splits are approximate industry convention (Tier C) and vary by service and deal.

### Per-Stream Rate Derivation (Tier C illustration)

```
DSP Gross Revenue in Period
        × ~70% (rights-holder pool)
        ÷ Total Streams on the Service in the Period
        = Approximate blended per-stream rate for the period
```

**Why the rate fluctuates:** The more total streams the service has (denominator
grows), the lower the per-stream rate, even if the pool (numerator) is the same.
Growth in total streams across all content on the service dilutes the per-stream
rate for each individual track.

**Per-stream rate ranges are estimates only (Tier C).** Industry-reported ranges
vary widely by service type and accounting period. Do not state a specific per-
stream rate as fact without the statement data for the period in question.

### Service-Type Pools (Same Service, Different Rates)

Most major DSPs operate multiple service tiers — each with a different royalty pool:

| Service tier | Revenue source | Pool effect |
|--------------|----------------|-------------|
| Paid premium subscription | Monthly subscription fees | Highest pool per stream |
| Ad-supported free tier | Advertising revenue only | Lower pool per stream |
| Family plan | Subscription fee shared across up to 6 accounts | Pool divided across more users |
| Student plan | Discounted subscription | Lower total revenue per account |
| Trial or promotional period | Little or no revenue | Minimal or zero pool contribution |

**Recovery implication:** a statement that does not break out income by service
tier makes it impossible to verify whether the correct pool was applied to each
play type. Separate service-tier accounting is a legitimate statement request,
especially when the payer is a label or distributor passing through streaming
income rather than the DSP paying directly.

### Minimum Guarantees and Major-Label vs. Independent Rate Differences

Major labels commonly negotiate minimum per-stream guarantees directly with
major DSPs in multi-year licensing agreements. Independent artists and labels
without direct deals receive the statutory/non-negotiated rate via the DSP's
arrangements with distributors and aggregators. The result: for the same stream
in the same period, a major-label release may generate a higher effective per-
stream rate than an independent release. This is not an error — it is a
contractual difference. Statement reconstruction must compare the independent
artist's actual per-stream rate to other independently distributed content, not
to major-label benchmark rates.

---

## 2. Recording Deal Structures and What They Mean for Artist Take-Home

### A. Traditional Label Deal (All-In Royalty Rate)

**Structure:** Label pays artist an "all-in" royalty rate on sales/streams (the
rate covers both the artist's mechanical royalty payment to the songwriter, if
applicable, and the artist's recording royalty). Common royalty rate ranges:

| Deal tier | All-in royalty rate (Tier C) |
|-----------|------------------------------|
| Emerging/new artist | 13–16% of royalty base |
| Mid-level / catalog-proven | 16–20% of royalty base |
| Established / superstar | 20%+ of royalty base |

These are industry-convention ranges. Actual deal terms are [CLIENT-SPECIFIC —
NOT QUOTABLE] and must be read from the executed agreement.

**What the royalty base is applied to:** Historically, physical royalties were
calculated on SRLP (suggested retail list price) with packaging deductions.
Digital and streaming royalties commonly apply to net receipts or a percentage
of the statutory mechanical rate per stream. The applicable royalty base varies
by deal and by format — read the actual contract.

**The recoupment mechanics:** The advance is recouped exclusively from the
artist's royalty share. The label earns its 80–87% of revenue regardless of
recoupment status. This means:
- A label can be highly profitable on a release the artist has not yet recouped.
- Unrecouped balance ≠ the label is owed money; it means the artist owes nothing
  and the label has not yet offset the advance from the artist's royalties.
- Cross-collateralization extends recoupment across multiple releases: an artist
  recouped on one album but with a deficit on another may see the profitable
  album's royalties applied to the other album's deficit — effectively delaying
  payment indefinitely if catalog performance is uneven.

### B. Net Receipts Deal (Independent / Modern Distribution Deals)

**Structure:** The label or distributor takes a percentage of "net receipts"
(gross income after agreed deductions, typically transaction fees, collection
costs, or mechanical royalties) rather than computing a royalty on a base price.

**Common net receipts rates (Tier C):**

| Deal type | Artist's net receipts share |
|-----------|-----------------------------|
| Full-service indie label | 50–70% of net receipts |
| Distribution-only with minimal services | 80–100% of net receipts minus flat fee |
| Label services / 360 deal component | 20–50% of net receipts depending on included services |

**Recovery implication:** statement analysis for a net-receipts deal must verify
what deductions were taken before the "net" was calculated. An overly broad
definition of deductions can materially reduce the artist's share without
appearing as an explicit line-item error.

### C. Profit-Split Deal

**Structure:** The label and artist split net profits (gross income minus agreed
production, marketing, and distribution costs) on a negotiated percentage —
commonly 50/50, but deal-specific. More favorable to the artist than an all-in
royalty deal IF costs are controlled and accounted for transparently.

**Key risks:**
- Cost definitions are deal-specific and can include items the artist did not
  approve.
- Without an audit right and a clear cost-cap framework, the profit split can
  be eroded by expansive cost definitions.
- Profit-split deals require more rigorous statement analysis because cost
  accounting is a second variable beyond the royalty rate.

### D. Licensing Deal

**Structure:** The label licenses the master recordings for a defined term and
territory; at the end of the term, ownership reverts to the artist. Common in
catalog reissues, independent label partnerships, and some international
licensing arrangements.

**Artist's income:** a license fee (often a flat advance) plus a royalty or
revenue share on exploitation during the license period. Ownership remains with
the artist after term expiry.

**Recovery focus:** confirm that the license term and territory are both accurate
and that exploitation outside the licensed territory or after the term expiry is
not occurring without additional compensation.

### E. Pass-Through Distribution (Independent Release)

**Structure:** The artist retains full ownership of master recordings and pays
the distributor a flat fee per release or a commission on collected income
(commonly 0–30% depending on the distributor tier, Tier C). The distributor
collects master-use royalties from DSPs and remits directly to the artist.

**Income flow:** Artist receives gross DSP income minus the distributor's
commission and any applicable mechanical royalties (passed through to The MLC).
No advance; no recoupment offset.

**Recovery focus:** verify the distributor's commission rate and that all
applicable territories are covered by the distribution network. Gaps in
distributor territory coverage produce the same "dropped territory" anomaly as
the label-deal gap — income earned but not collected because the distributor
has no arrangement with that territory's DSP.

---

## 3. Publishing Advance and Recoupment Mechanics

Publishing advances are recouped from royalties — but the recoupment scope
differs critically by deal type:

| Deal type | Recoupment source |
|-----------|-------------------|
| Full publishing deal | Advance recouped from the songwriter's entire share (writer's share + publisher's share) |
| Co-publishing deal | Advance recouped from the publisher's portion of income only (the writer's share is protected from recoupment) |
| Administration deal | No advance in most cases; flat admin fee only |

**The co-pub recoupment protection is important:** in a co-publishing deal, the
publisher typically recoups from the publisher's share only, meaning the writer
continues to receive the writer's share even while the advance is unrecouped.
Verify whether the specific deal's recoupment clause matches this convention —
a clause recouping from both shares is more burdensome than co-pub convention
and should be flagged.

**Modeling recoupment timeline:** divide the advance amount by the expected
annual publishing income attributable to the publisher's share. If a catalog
generates $50,000/year in publishing income and the publisher's share is 50%,
the publisher earns $25,000/year against the advance — a $250,000 advance takes
approximately 10 years to recoup in this scenario. Request a publisher pro-forma
model before accepting any advance; route the modeling to the Finance/Royalties
function.

---

## 4. Catalog-Backed Lending — Music Finance Debt

Catalog-backed lending allows an artist or rights holder to raise cash against
the value of an existing royalty stream without selling ownership.

### Mechanics

1. **Valuation:** A lender commissions or accepts a valuation of the royalty-
   generating catalog (typically using the NPS-multiple or cash-flow methodology
   described in Section 5 below).
2. **Advance / loan amount:** Commonly 60–80% of loan-to-value (LTV) against
   the assessed catalog value (Tier C). A catalog valued at $1,000,000 might
   support a loan of $600,000–$800,000.
3. **Debt service:** Monthly or quarterly payments from ongoing royalty income.
   The royalty flows are often directed to a lockbox account controlled by the
   lender; the artist receives the remainder after debt service.
4. **Term:** Typically 3–7 years, with the loan fully repaid at maturity or
   refinanced (Tier C).
5. **Interest rate:** Varies by lender type, market conditions, and catalog
   quality; specialized music-finance lenders commonly quote prime rate plus a
   spread (Tier C — route interest-rate specifics to Finance/Royalties function
   for deal evaluation).

### Use Cases

- Bridge financing while a larger catalog sale is negotiated.
- Funding a recording, touring, or marketing campaign without surrendering
  ownership.
- Estate liquidity for heirs who want to retain catalog ownership.

### Risks

- Royalty income fluctuations can stress debt service if a catalog's performance
  declines during the loan term.
- Lender covenants may restrict certain exploitation decisions (e.g., devaluing
  sync uses) that could affect the security.
- In default, the lender can take possession of the catalog — outcome equivalent
  to a forced sale at a potentially unfavorable time.

**Recovery intersect:** a catalog under a royalty lien may have royalties
redirected to the lender's lockbox. A missing royalty payment that is actually
flowing to the lender is a financial-management issue, not an underpayment —
distinguish before asserting a recovery claim.

---

## 5. Catalog Valuation — The NPS Multiple Methodology

Publishing catalog sales are most commonly priced as a multiple of **Net Publisher's
Share (NPS)** income.

### Calculating NPS

```
Gross publishing income in the period (mechanicals + performance + sync)
        × publisher's ownership percentage of that income
        = NPS for the period
```

**NPS trailing vs. forward:** buyers negotiate on the basis of trailing 12-month
NPS (known income) discounted or supplemented by a forward estimate. Higher-
activity or growing catalogs trade at forward multiples; stable or declining
catalogs at trailing multiples.

### Multiple Ranges (Tier C — industry-reported; not market guarantees)

| Catalog type | Approximate multiple range (Tier C) |
|--------------|--------------------------------------|
| Active modern catalog (writer still releasing, sync-active) | 15–25× NPS |
| Established legacy catalog (stable, well-known, proven) | 12–20× NPS |
| Niche / specialist catalog (limited sync, regional) | 8–14× NPS |
| Emerging / short track record | 6–10× NPS |

**Important:** these are approximate industry-convention ranges (Tier C). Actual
transaction multiples depend on deal structure, payment terms, interest-rate
environment, and buyer appetite. Route catalog valuation to the Finance/Royalties
function — do not quote these as an NPS multiple for a specific catalog without
disclosing the Tier C classification and the basis for the estimate.

### Key Value Drivers

1. **Revenue durability:** Catalogs with diverse income streams (sync, consistent
   performance, covers, TV/film licensing) support higher multiples than catalogs
   dependent on a single platform or format.
2. **Songwriter's ongoing output:** Buyers value the "self-funding" effect — a
   writer who continues releasing increases the catalog's future income
   prospectively.
3. **Catalog age and proven trajectory:** A catalog with 10+ years of consistent
   earnings is more predictable (and more valuable) than a 2-year catalog,
   regardless of current income.
4. **Revenue concentration risk:** If 80% of income comes from one song or one
   sync license, the multiple is discounted for concentration risk. Buyers price
   this by diversification premium.
5. **Clean registration and title:** Buyers heavily discount catalogs with
   incomplete registrations, disputed ownership, or missing split documentation.
   Clean title is a prerequisite for a premium multiple.

### Seller Due-Diligence Package (What Buyers Expect)

A catalog seller should prepare:
- Three years of royalty statements from all income sources (PRO, MLC/mechanical,
  label pass-through, direct sync income)
- Works list with ISWC, ISRC (for related masters), and co-writer splits
- PRO registration export confirming all works are registered
- Mechanical registration confirmation (The MLC portal export or equivalent)
- Existing publishing, administration, or sub-publishing agreements
- Any existing advances or liens against the catalog
- Sync license history and active placements
- Statement of any disputed ownership or claims

**Red flags buyers identify in due diligence:**
- Royalty income concentrated in a single song with declining usage
- Statements showing unexplained year-over-year income declines
- Incomplete or incorrect registrations (reduces confidence in future income)
- Co-writer splits executed informally or missing signed split sheets
- Existing publishing advance not yet recouped (the outstanding advance is a
  liability the buyer inherits or the advance must be repaid at closing)
- Undisclosed third-party claims, samples, or co-authorship disputes

---

## 6. Advance vs. Catalog Sale — Decision Framework

| Factor | Advance (recoupable) | Catalog sale (outright) |
|--------|----------------------|------------------------|
| Immediate cash | Yes | Yes |
| Future royalties retained | Yes — after recoupment | No — transferred to buyer |
| Ownership retained | Yes | No |
| Long-term income impact | Reduced during recoupment period | Permanent loss of sold income |
| Tax treatment | Ordinary income (if advance is advance) | Potentially capital gains on the sale proceeds — route to tax counsel |
| Best use case | Near-term cash need; catalog expected to grow | Monetizing a mature catalog; retirement liquidity; one-time investment |

**Route the modeling and comparison to the Finance/Royalties function.** The
recovery specialist's role is to ensure the catalog is collecting its full
income — the decision of what to do with that income (advance, sale, or hold)
belongs to the Finance/Royalties and legal functions.

---

## 7. Music Income Tax Basics (US Context)

This section provides the recovery-specialist-level awareness needed to flag tax-
related issues and route them correctly. It is NOT a tax opinion — route all tax
filing, treaty, and withholding questions to qualified tax counsel.

### Royalty Income Classification

**Earned royalties** (mechanicals, performance, neighboring rights) are generally
treated as ordinary self-employment income for tax purposes in the US. They are
subject to:
- Federal income tax at the artist's marginal rate.
- Self-employment tax (Social Security + Medicare) on net self-employment income,
  typically 15.3% on the first applicable threshold and reduced rate above it
  (Tier A — confirm current rate and threshold before advising; route to tax
  counsel for filing advice).

**Sale of a catalog** may qualify for capital-gains treatment if the catalog
qualifies as a capital asset under the applicable provisions. The distinction
between ordinary income treatment (for assets held primarily for sale) and
capital-gains treatment (for capital assets) is a legal and tax-law question —
route to tax counsel without opinion.

### Quarterly Estimated Taxes

Artists receiving royalty income are typically self-employed and not subject to
employer withholding. US tax law requires quarterly estimated tax payments to
avoid underpayment penalties. Missing quarterly payments results in penalties
even if the full annual tax liability is paid at filing. Flag this to any artist
who appears to be treating royalty income as lump-sum at year-end.

### International Withholding Taxes

Many countries withhold tax on royalty payments made to non-resident rights
holders — commonly 15–30% at source, reduced by applicable US tax treaty
provisions. The withholding is applied before the net royalty remittance arrives
at the sub-publisher or home PRO.

**Recovery intersect:** an unexpectedly low international royalty amount may
reflect withholding tax deductions rather than an underpayment. Statement analysis
should look for any "withholding tax" or "deducted tax" line in international
statements before asserting a shortfall. Route the question of whether treaty
rates were properly applied to qualified tax counsel.

### 1099 Reporting for Royalty Income

In the US, royalty payments exceeding $10 from a single payer are reportable
on Form 1099-MISC. PRO distributions commonly do not trigger a 1099 below the
threshold and may not be routinely reported. This is an administrative
inconsistency — not a basis for underreporting income. All royalty income is
taxable regardless of whether a 1099 is issued. Artists who receive international
royalties through a home PRO or sub-publisher may need to obtain confirmation of
the gross amounts received for accurate income reporting.

---

## 8. Deal-Economics Reference Checklist (pre-signing)

Before any recording, distribution, or publishing deal is signed, the artist's
advisors should verify these financial terms and their implications:

**Recording / distribution deal:**
- [ ] What is the royalty rate? (All-in? Net receipts percentage? Profit split?)
- [ ] What is the royalty base? (SRLP? Net receipts? Per-stream allocation?)
- [ ] What deductions reduce the royalty base? (Packaging? Free goods? CC reduction?)
- [ ] What is the advance amount, and what costs are recoupable against it?
- [ ] Is the recoupment account cross-collateralized across multiple releases?
- [ ] What is the reserve ceiling and release schedule?
- [ ] What accounting periods and statement delivery windows apply?
- [ ] What is the contractual audit right, and what is the audit window?
- [ ] What happens to streaming mechanicals — are they passed through at 100%?

**Publishing deal:**
- [ ] Is this a full publish, co-pub, or admin deal?
- [ ] What share of income does the publisher retain (publisher's share)?
- [ ] Is the advance recouped from the writer's share or the publisher's share only?
- [ ] What is the expected recoupment timeline (get a publisher pro-forma)?
- [ ] Are all works covered, or only specific titles?
- [ ] What term length and territory coverage applies?
- [ ] What reversion rights exist if the advance is not recouped by a specified date?
- [ ] What sub-publishing arrangements will the publisher make, and at what fee?

**Route any deal-evaluation questions to the Finance/Royalties and legal
functions — this checklist frames the questions, not the answers.**
