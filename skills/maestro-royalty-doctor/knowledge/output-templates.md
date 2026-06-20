# Royalty Recovery — Output Templates

Structured output formats for the recovery specialist. Every template enforces the
same discipline: verify before asserting, rule out lag before claiming loss, label
recoverable amounts NOT ESTIMABLE unless evidence supports them, and route execution
out. NOT EVALUABLE, NOT ESTIMABLE, and NOT QUOTABLE markers are mandatory where they
apply.

---

## Template 1 — Royalty Recovery Audit (full)

Use for a catalog-wide recovery assessment scored against the Seven-Dimension
Royalty Recovery Readiness Rubric.

```
ROYALTY RECOVERY AUDIT — {artist name}
Catalog: {catalog name} · Works: {count} · Territory: {home territory}

HARD GATES
- HG-1 No statement/registration data: CLEAR | TRIGGERED — {reason}
- HG-2 Fabricated recovery figure: CLEAR | TRIGGERED — {reason}
- HG-3 Lag misdiagnosed as underpayment: CLEAR | TRIGGERED — {reason}
- HG-4 Expired audit window: CLEAR | TRIGGERED (TIME-CRITICAL) — {reason}

DIMENSION SCORES (grade · numeric · weight · confidence)
1. Registration Integrity       {grade} · {n} · 0.20 · {conf} — {1–3 sentence rationale; sub-signals MEASURED/SOURCED/JUDGED/AMBIGUOUS}
2. Statement Verification        {grade} · {n} · 0.18 · {conf} — {rationale}
3. Black-Box Recovery Readiness  {grade} · {n} · 0.16 · {conf} — {rationale}
4. Pipeline Coverage             {grade} · {n} · 0.14 · {conf} — {rationale}
5. Audit Readiness               {grade} · {n} · 0.12 · {conf} — {rationale}
6. Collection-Timing Discipline  {grade} · {n} · 0.10 · {conf} — {rationale}
7. Recovery Documentation        {grade} · {n} · 0.10 · {conf} — {rationale}

PROVISIONAL COMPOSITE: {value}/10
  Formula: (D1×0.20)+…+(D7×0.10)
  Label: PROVISIONAL — unlock condition: ≥30 outcome-checked recovery audits.

RECOVERY POSTURE: {FULLY_COLLECTING | MINOR_LEAKAGE | NOTABLE_LEAKAGE | SIGNIFICANT_LEAKAGE | SEVERE_LEAKAGE}
  (descriptive severity — not a recommendation to sign, sell, or litigate)

LEAK MAP — where money is most likely going missing, ranked, each with its evidence
basis and whether the amount is ESTIMATE (with basis) or NOT ESTIMABLE.

RECOVERY PLAN
- IMMEDIATE: {time-critical actions — window expiry, claims aging toward redistribution}
- PRIORITY: {highest-value recovery — file claims, close registration gaps}
- OPTIMIZE: {reduce future leakage — systematize verification, add coverage}
- MAINTAIN: {dimensions already closed}

NOT EVALUABLE: {items that cannot be assessed + the minimum data required}

NEXT BEST ACTION (24–72h): {single highest-value step}

{advisory footer}
```

---

## Template 2 — Statement Anomaly Report

Use when a specific statement is under review.

```
STATEMENT ANOMALY REPORT — {artist} · {payer} · period {dates}

VERIFICATION BASIS: {data cross-referenced — DSP dashboard, prior statements, society portal} | NONE AVAILABLE → confidence capped
LAG CHECK: every questioned line classified IN TRANSIT / STUCK / UNDERPAID before any loss claim (HG-3 discipline)

ANOMALIES FOUND (by checklist category)
| # | Category | Line item | Finding | Classification | Recoverable? |
|---|----------|-----------|---------|----------------|--------------|
| … | {1–12}   | {item}    | {finding} | IN TRANSIT / STUCK / UNDERPAID | ESTIMATE (basis) / NOT ESTIMABLE |

RESERVE & DEDUCTION REVIEW: {reserve rate vs. ceiling; release schedule; CC clause validity}
SOFT-AUDIT RECOMMENDATION: {specific line items to query in a written inquiry, with the contractual basis}
ESCALATION: {route to counsel for a formal audit demand only if stonewalled / systematic / window-expiring}

{advisory footer}
```

---

## Template 3 — Registration Gap Report

Use when the focus is missing registrations causing money not to be matched.

```
REGISTRATION GAP REPORT — {artist} · {works in scope}

COLLECTOR-BY-COLLECTOR STATUS
- PRO (performance): {complete | gaps on which works}
- Mechanical: {complete | gaps}
- Neighboring rights: {registered with which collectors | not registered}
- Identifiers (ISWC / ISRC / IPI): {coverage; any active-revenue works without identifiers → HG-1}

UNMATCHED-POOL EXPOSURE: {streams earning into an unmatched pool because of the gaps above}
  Time-sensitivity: unmatched mechanicals are subject to market-share redistribution after a retention period (industry convention) — closing the gap is time-critical.

RECOVERY PATH PER GAP
- {gap} → {register with X} → {then file the unmatched/historical claim with proof of ownership} → {retroactive window: tracked / closing}

RECOVERABLE AMOUNT: ESTIMATE (with basis) only where statement history + a dated gap range exist; otherwise NOT ESTIMABLE — name the data required.

{advisory footer}
```

---

## Template 4 — Black-Box / Historical Recovery Plan

Use when pursuing unmatched-pool and retroactive money.

```
BLACK-BOX RECOVERY PLAN — {artist}

HOLDING COLLECTORS IN SCOPE: {societies/collectors likely holding unmatched money}
OWNERSHIP PACKAGE STATUS: {proof of ownership, splits, identifiers — ready / missing items}
CLAIM SEQUENCE
1. Close the registration gap that makes the money unmatchable.
2. File the unmatched/historical claim with proof of ownership.
3. Track the retroactive recovery window against its deadline.
RETROACTIVE WINDOWS: {open / approaching / foreclosed per collector}
RECOVERABLE AMOUNT: NOT ESTIMABLE without statement/distribution history and a dated gap range — qualitative recoverability only unless evidence supports a figure.

{advisory footer}
```

---

## Standard Advisory Footer

End every recovery output with the routing footer (paraphrasable, substance fixed):

> This is a royalty-recovery analysis — it identifies and documents where income is
> uncollected or underpaid and builds the recovery case. It is not a legal opinion,
> a contract interpretation, or a catalog valuation. Route formal audit demands and
> any legal action to qualified entertainment counsel, deal/valuation modeling to
> the Finance/Royalties function, copyright-law and publishing-deal questions to the
> Publishing function, and sync pursuit to the Sync function.

---

## Discipline Reminders (apply to every template)

- **NOT EVALUABLE** when the minimum data set is absent → stop and name the data.
- **NOT ESTIMABLE** for any recoverable amount lacking statement history + a dated
  gap/anomaly range.
- **NOT QUOTABLE** for client-specific deal terms — never echoed as market
  benchmarks.
- **Lag before loss** — classify IN TRANSIT / STUCK / UNDERPAID before asserting any
  money is missing (HG-3).
- **Tier every figure** — no rate, retention, or multiple as "market standard"
  without a Tier A/B source.
