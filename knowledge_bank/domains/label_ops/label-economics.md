# Label Economics

All P&L benchmarks below are directional estimates unless tied to a named
authority. Actual deal economics are private and vary significantly by label size,
artist leverage, and catalog performance.

## The Label P&L Structure

A label's P&L runs across five cost centers and several revenue lines.

**Revenue lines**

| Revenue line | Description | Margin profile |
|--------------|-------------|----------------|
| Streaming royalties | Label share of DSP net receipts after the distributor payout | Thin: ~10–20% net after artist royalties and overhead |
| Sync licensing | Fees for use in film, TV, advertising, games | High: ~30–60% margin; smaller volume |
| Physical / download | Declining; physical carries production + fulfillment overhead | Variable |
| Neighboring rights | Performance royalties for master broadcast/non-interactive use | High margin; near-zero incremental cost |
| Catalog licensing / third-party | Compilation, sample, re-licensing revenue | High margin; no production cost |

Streaming represents the majority of recorded-music revenue for most labels;
actual share depends on catalog profile and DSP terms.

**Cost center taxonomy**

| Cost center | Contents | Recoupable against artist royalties? |
|-------------|----------|--------------------------------------|
| Recording costs | Studio, producer, mixing, mastering, session musicians | Often YES — typically fully recoupable in standard deals |
| Marketing & promotion | Digital advertising, radio promo, PR, video, content | Contractually variable |
| Tour support | Advances covering touring deficits | Typically YES |
| Distribution fees | Payments to distributor/aggregator | NO — label operating cost |
| Overhead / G&A | Staff, office, legal, accounting | NO |
| Royalty payments | Artist, mechanical, producer royalties | NOT recoupable — these *are* the payment |

**Critical distinction:** recoupable costs are a loan against the artist's future
royalty share, not a profit center. The label recovers its invested cost before
the artist receives post-advance royalties; it does not profit from recoupment
itself.

## Margin Benchmarks by Tier (directional)

| Label tier | Artist tier | Approx. net margin | Key driver |
|------------|-------------|--------------------|------------|
| Major | Superstar / catalog | 25–35%+ | Catalog leverage; overhead amortized across roster |
| Major | Developing / new | -20% to +5% | Front-loaded investment; long recoupment horizon |
| Mid-size independent | Active artist | 12–20% | Leaner overhead; mid-tier distribution costs |
| Small independent | Active artist | 3–15% if profitable | High per-release overhead as % of revenue |
| Small independent | Start-up phase | -30% to -10% | Pre-catalog; heavy investment before steady revenue |

**The concentration rule:** roughly the top fifth of signed artists generate the
large majority of a label's revenue. Label P&L is structurally biased toward
catalog performance on a small number of successful projects — the reality of a
hit-driven business.

## Advance Sizing

An advance is priced as a function of four variables:
1. **Projected 12-month forward streaming revenue** — from comparable artist
   performance at the same stage.
2. **Artist royalty rate** — determines how much streaming revenue credits against
   the recoupable balance.
3. **Recoupable cost floor** — recording, tour support, and marketing costs
   charged against the advance; sets the total recoupable balance.
4. **Recoupment timeline target** — months/years to drive the balance to zero on
   the streaming projection.

**Directional advance ranges by stage** (estimates; actual terms private and
negotiated): emerging/unsigned ~$10K–$50K; developing with streaming history
~$50K–$150K; established independent ~$100K–$350K; major artist with chart history
$350K–$1M+.

**Advance-sizing gate**
```
IF projected annual net streaming revenue × royalty rate × 3 years < proposed advance:
  → advance exceeds the 3-year recoupment horizon at the current trajectory
  → reduce advance, add escalated royalty triggers, or flag: above comfort zone
IF projected annual net streaming revenue × royalty rate × 5 years < proposed advance:
  → advance is unlikely to recoup; treat as a marketing investment, not a
    recoverable advance, with explicit owner sign-off
```
Specific advance multiples from any particular label's deal terms are NOT
QUOTABLE.

## Royalty Waterfall Mechanics

```
Tier 1 — DSP revenue (gross): DSP pays the distributor
Tier 2 — Distribution fee: distributor deducts its fee; net to label = gross − fee
Tier 3 — Label gross receipt: label receives net from distributor
Tier 4 — Mechanical royalties: label pays mechanicals to publisher/collective
Tier 5 — Artist royalty calculation: rate × net receipts → credited to balance
Tier 6 — Recoupment application: credit applied to the unrecouped balance;
         artist receives cash only once the balance is zero
Tier 7 — Producer royalties: typically 3–5 points; carved from artist royalty or
         paid directly by the label, per contract structure
Tier 8 — Label net income: gross receipts − distribution fee − mechanicals −
         post-recoupment artist royalties − marketing and overhead
```

**Producer-royalty structure detail:** producer royalties are typically 3–4
points. In many major deals the producer royalty is carved out of the artist's
royalty (the artist pays the producer from their share); in some independent deals
the label pays the producer directly and deducts from the artist's royalty. This
distinction matters for recoupment modeling.

## Recoupment Projection Modeling

**The recoupment clock** requires five inputs: total recoupable balance (advance +
all recoupable costs); contracted royalty rate; projected annual net receipts;
royalty-rate adjustment factors (escalators, packaging/free-goods deductions);
and cross-collateralization scope.

```
Annual royalty credit = projected annual net receipts × contracted royalty rate
                        (adjusted for any contractual deductions)
Recoupment years      = total recoupable balance ÷ annual royalty credit
```

**Illustrative worked example (hypothetical, mid-size independent):** total
recoupable balance $120,000 (advance $80,000 + recording costs $40,000); royalty
rate 18%; projected Year-1 net receipts $300,000 → annual credit $54,000 →
recoupment projection 2.2 years.

**Anti-pattern:** that projection assumes flat revenue across the period. In
practice streaming front-loads: the release month and the following few months
typically generate the bulk of a song's first-year streaming, and later years are
materially lower unless catalog momentum sustains. A conservative projection
should discount Years 2–3 revenue by 30–50% unless the artist has documented
catalog longevity.

## Recoupable vs. Non-Recoupable Costs (industry convention)

| Cost type | Convention | Risk if undefined |
|-----------|-----------|-------------------|
| Advance | Recoupable | Always |
| Recording (studio, producer, mixing, mastering) | Recoupable (standard) | Label will claim recoupable |
| Video production | 50–100% recoupable per contract | Common negotiation point; set the % explicitly |
| Tour support | Recoupable (standard) | Negotiate a cap; uncapped recoupment is a major liability |
| Independent radio promotion | Recoupable in many major deals; varies | High-risk if undefined; campaigns can cost six figures |
| Marketing / advertising | Sometimes recoupable; varies widely | Vague language favors the label; define it |
| A&R staff costs | NOT recoupable (overhead) | Standard |
| Distribution fees | NOT recoupable | Label cost |
| Legal & accounting | NOT recoupable | Overhead |

## Practitioner-Layer Insight

- **The "net receipts" definition is the most important line in the royalty
  clause.** Packaging deductions, free-goods deductions, and promotional-use
  deductions — largely vestigial but still present as legacy language in many
  streaming-era contracts — can reduce the effective royalty rate by 30–40% off the
  nominal headline rate unless explicitly excluded. A nominal "20% royalty" without
  those exclusions may yield an effective 12–14% on streaming income.
- **Tour support as a recoupment trap.** "Unlimited tour support" creates a
  recoupable cost with no ceiling; a single multi-city run can cost six figures and,
  if fully recoupable, can permanently prevent recoupment regardless of streaming
  performance. The correct structure is a defined per-cycle cap and a partial
  recoupment rate (e.g., 50% recoupable rather than 100%).
- **The sync-margin insight.** Sync licensing on existing catalog is the
  highest-margin revenue line — near-100% gross margin before overhead, with no
  incremental production or marketing cost. Active catalog sync management is one of
  the highest-ROI activities in label operations.
- **Ignoring the distribution fee distorts royalty math.** Distribution fees reduce
  net receipts before the royalty rate is applied; quoting a royalty rate without
  specifying the base (gross vs. net-of-distribution) is either confused or
  obscuring the real economics.

See also: [[label-ops-deal-structures-and-recoupment]],
[[label-ops-catalog-management]], [[label-operations-doctrine]].
