# Intelligence Quality Scorecard

How to score an intelligence scan or a single entry for quality before it ships. The
scorecard turns the doctrine into a gradeable rubric so quality is auditable, not a
matter of taste. Scoring is evidence-disciplined: every dimension is rated MEASURED,
SOURCED, or JUDGED, and a dimension that cannot be assessed is marked NOT EVALUABLE
rather than guessed.

---

## 1. Evidence Discipline

Each dimension's score must declare its evidence basis:

- **MEASURED** — verified against the artifact itself (the entry, the source list, the
  routing log).
- **SOURCED** — supported by a named primary or strong-trade source with a date.
- **JUDGED** — an analyst judgment where measurement is unavailable; must state the
  reasoning.

If a dimension cannot be evaluated from available evidence, it is **NOT EVALUABLE** —
and a scan with NOT EVALUABLE on a hard-gate dimension cannot receive a passing
verdict until resolved.

---

## 2. The Eight Dimensions

| # | Dimension | What it measures | Weight |
|---|-----------|------------------|--------|
| 1 | Decision relevance | Does every entry complete the "so what?" for a named specialist? | 20% |
| 2 | Sourcing integrity | Is every claim tied to a tiered, dated source? | 18% |
| 3 | Classification accuracy | Is each item's consequence class defensible (rule-change vs. right-answer-change)? | 14% |
| 4 | Routing precision | Are items routed to the right specialists, each with an independent implication? | 12% |
| 5 | Timing judgment | Are alerts reserved for trigger-grade items; is the regular cycle used otherwise? | 10% |
| 6 | Currency / recency | Is every dated claim within its recency horizon, or labelled stale? | 10% |
| 7 | Selectivity | Is the feed appropriately under-inclusive (no filler, honest quiet cycles)? | 8% |
| 8 | Territory coverage | Are the relevant territory lenses applied, with gaps reported as NOT EVALUABLE? | 8% |

Each dimension scores 0–4 (0 = absent, 2 = adequate, 4 = exemplary). The weighted sum
maps to the verdict ladder below.

---

## 3. The Four Hard Gates

A scan fails outright — regardless of weighted score — if any of these is violated:

1. **No unsourced fact.** Any quantified claim without a tiered, dated source fails the
   scan.
2. **No rumor as fact.** Any rumor-tier claim presented without an explicit rumor flag
   fails the scan.
3. **No "so what?"-less entry.** Any entry that cannot name the decision it changes for
   a named specialist fails the scan.
4. **No silent staleness.** Any claim past its recency horizon presented as current,
   without a stale label, fails the scan.

These gates are non-negotiable. A scan that is excellent on every weighted dimension
but violates one gate does not ship.

---

## 4. The Currency-with-Consequence Test

The single overriding test: of the items that shipped, how many actually changed a
decision? A scan optimizes for **currency with consequence**, not volume. A scan that
ships ten well-sourced items that change no decisions scores worse than one that ships
three that each move a specialist.

---

## 5. Verdict Ladder

| Weighted score | Verdict | Meaning |
|----------------|---------|---------|
| 3.4–4.0 | Ship | Decision-relevant, well-sourced, correctly classified and routed |
| 2.6–3.3 | Ship with fixes | Sound core; specific entries need re-sourcing or re-routing |
| 1.6–2.5 | Rework | Selectivity or sourcing problems; do not ship as-is |
| < 1.6 | Reject | Fails the domain's basic discipline |
| Any hard-gate violation | Reject | Regardless of weighted score |

A quiet-cycle report with no trigger-grade items and an honest accounting of dropped
items is a **Ship** — selectivity is the product, and an honest quiet cycle is a
high-quality output.
