# Royalty Statement Analysis

How to read a royalty statement as an accounting claim and detect the anomalies
that indicate uncollected or underpaid income. Statement analysis — not a formal
audit — is the first recovery tool: many errors are correctable through a
documented written inquiry without the cost and friction of a formal audit.

---

## 1. Statement Architecture

Understanding the structure is the prerequisite for detecting anomalies.

**Label / recording statement:**

```
HEADER — artist, label, deal id, accounting period, statement date
PRODUCT SECTION — one row per released product (title, catalog no., UPC/ISRC)
SALES / STREAMS LINE ITEMS — units or streams, royalty base, royalty rate, gross royalty
DEDUCTIONS — packaging, free goods, controlled-composition, promo/free-use
RESERVE — reserve held this period; prior reserves released; net reserve balance
RECOUPMENT — opening unrecouped balance; royalties earned; applied; closing balance
TERRITORY BREAKDOWN — per-territory lines; currency-conversion details
NET PAYABLE — total earned, less deductions/reserves/recoupment offset, net payable
```

**Publisher statement (simplified):**

```
INCOME SECTION — per work, per territory, per stream (performance/mechanical/sync/other):
    work title / ISWC, income stream, territory, gross received, publisher's share retained, net writer's share
DEDUCTIONS — admin fee (admin deals); sub-publishing deduction (where applicable)
RECOUPMENT — advance balance; royalties applied; net to writer or to balance
TERRITORY / INCOME-STREAM SUMMARY
```

---

## 2. Line-Item Interpretation

Common abbreviations on label statements:

| Code | Meaning |
|------|---------|
| ROY RATE | Royalty rate (per contract, %) |
| RB / ROY BASE | Royalty base (price the rate applies to) |
| SRLP | Suggested retail list price (physical royalty base) |
| PPD | Published price to dealer (alternate, lower base) |
| STM / STRM | Streaming |
| DLD | Digital download |
| CC | Controlled composition (mechanical-rate reduction) |
| RES / RESV | Reserve held against returns |
| UNREC | Unrecouped balance |
| CROSS-COL | Cross-collateralized balance from another product |
| MECH | Mechanical royalty pass-through or deduction |
| SYNC FEE | Synchronization license income |
| FX | Foreign-exchange rate used for conversion |

**Streaming-mechanical pass-through rule.** Some label statements include a line
for mechanicals "passed through" from the mechanical collector. Confirm whether the
label passes through 100% of mechanicals or nets a distribution fee first — a common
underpayment point on streaming income.

---

## 3. Anomaly Detection Checklist (twelve categories)

Run this before accepting any statement as correct. Each is a flag to investigate,
not a conclusion of underpayment.

1. **Revenue decline without catalog explanation** — a line item declines >15%
   year-over-year (Tier C threshold) without a matching drop in underlying activity.
   → Request a line-item explanation; cross-reference DSP data.
2. **Missing income stream** — a stream present in prior statements is absent now.
   → Confirm the stream is still active; request its statement separately.
3. **Below-rate mechanical** — implied mechanical per stream is below the applicable
   statutory basis. → Request the computation basis from the collector or label.
4. **Controlled-composition deduction without a CC clause** — a CC deduction appears
   but no CC clause exists in the agreement. → Demand documentation of the CC
   authority; route to counsel if none is produced.
5. **Reserve percentage exceeds the contract ceiling** — the held reserve rate
   exceeds the contractual ceiling. → Compute the implied rate; demand correction.
6. **Reserve not released per schedule** — a reserve held beyond the contractual
   release schedule remains unreleased. → Compute the outstanding release; demand it.
7. **Missing territory** — confirmed DSP activity in a territory has no corresponding
   line item. → Request territory-by-territory accounting.
8. **New revenue stream without a line item** — a new licensing program launched in
   the period has no corresponding line. → Request its inclusion or a separate
   accounting.
9. **Currency-conversion anomaly** — the FX rate used differs materially from
   published mid-market rates for the period without contractual authority.
   → Compare to historical FX; flag as a statement error.
10. **Computation errors** — line-item subtotals do not reconcile to section totals,
    or section totals to net payable. → Spreadsheet reconstruction; demand a
    corrected statement.
11. **Accounting-period mismatch** — the statement period does not match the
    contractual accounting period. → Request explanation; the contractual period is
    binding.
12. **Streams below DSP-reported data** — streams on the statement are materially
    below streams the DSP reports directly. → Request reconciliation; excess
    royalties are owed for the unreported streams.

---

## 4. Accounting-Window Analysis — Normal Lag vs. Suspicious

| Situation | Normal? | Action |
|-----------|---------|--------|
| Q1 streams appear in the Q3 statement | Yes — normal lag | Monitor only; within the expected cycle |
| Q1 of last year still in no statement 18 months later | Possibly anomalous (upper bound of normal) | Investigate the stream; verify distribution history |
| Live-performance royalties from Q1 received in Q4 | Yes — normal for periodic PRO cycles | No action |
| International performance royalties from two years ago still unreceived | Possibly anomalous (upper bound for international) | Investigate the territory; may be a registration gap, not lag |
| Sync fee confirmed in January unreceived by April | Possibly anomalous (sync should arrive in 30–90 days, Tier C) | Request payment status; may be a payment delay, not a pipeline issue |

**Window rule:** establish the expected window for the stream and confirm the usage
date before concluding income is missing. Income within the window is in transit.
This distinction is required before triggering any audit inquiry.

---

## 5. Controlled-Composition Clause Accounting

A controlled-composition clause reduces the mechanical rate for "controlled
compositions" (songs the artist wrote or co-wrote) to a fraction of statutory —
commonly 75% of statutory (Tier C; the specific rate is contract-specific).

**What to look for:** a "CC deduction" or "75% mechanical" line in the mechanical
section. If present, verify that (a) the agreement actually contains a CC clause,
(b) the clause rate matches the rate applied, and (c) the clause applies to the
specific compositions being deducted.

**The failure mode:** a CC clause written broadly to apply to "all compositions"
(rather than only compositions the artist controls) can reduce mechanicals even on
songs the artist did not write. That is a statement anomaly — flag it and route the
contractual question to counsel.

---

## 6. The Soft Audit — First-Response Tool

When statement analysis surfaces anomalies, a formal forensic audit is not the
first move. A **soft audit** — a documented written inquiry citing the specific line
items, the contractual basis for questioning them, and a request for reconciliation
— often triggers correction without the cost and relationship friction of a formal
audit. Reserve a formal audit demand for situations where: soft-audit inquiries are
ignored or stonewalled; the anomaly pattern suggests systematic rather than isolated
underpayment; or the contractual audit window is approaching expiry. Formal-audit
decisions and demand drafting route to counsel.

**Cost-benefit discipline (Tier C):** for very small catalogs, professional
line-by-line statement analysis can cost more than the expected recovery. There,
focus on the highest-signal anomalies (missing income streams, extreme reserve
over-retention) rather than full forensic reconstruction.

---

## 7. Domain Anti-Patterns

1. **Accepting the first statement as correct.** Errors established in the first
   statement of a new relationship tend to persist across later periods.
2. **Auditing before analyzing.** A formal audit is expensive and relationship-
   damaging; statement analysis and a soft audit come first.
3. **Missing the reserve math.** Focusing on the net-payable line while the reserve
   section withholds a meaningful share of earned income on a rolling basis.
4. **Conflating recoupment balance with financial failure.** Unrecouped on paper
   says nothing about market performance — and it is not a recovery claim.
5. **Treating dashboard data as a royalty calculation.** DSP dashboard play counts
   are an approximate activity indicator, not a precise royalty input; the
   computation involves service-revenue allocations, not simple per-stream rates.
6. **Not tracking the audit window.** Once the contractual window closes, the right
   to audit that period expires permanently. Window tracking is proactive calendar
   management.
