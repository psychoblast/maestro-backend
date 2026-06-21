# Output Templates & Handoffs

PLMKR knowledge base. Four deliverable types. Every one carries the **mandatory
core**; conditional modules attach per the matrix and only per the matrix
(anti-bloat). Any value resting on a provisional default carries that status
through to the output.

---

## MANDATORY CORE (all four types)

1. **Work Product** — the deliverable, in the type's format below.
2. **Decision Summary** — recommendation + 3–5 reasons as an executive memo,
   explicitly answering: *Why? Why now? What data supports this? What assumptions
   am I making? What would change my answer?*
3. **Confidence Assessment** — level (high/medium/low) + reasons + risks/
   unknowns. Uncertainty propagation: confidence is capped by the weakest
   critical input and the cap is named in one sentence ("Confidence capped at
   medium: the playlist-source split is inferred from partial dashboard data, not
   reported").

---

## CONDITIONAL-MODULE MATRIX

| Module | Release Performance Read | Anomaly Investigation | Forecast Memo | Benchmark Comparison |
|---|---|---|---|---|
| Scores (rubric verdicts) | ✅ always (C1–C6) | — | — | ◐ when ranking against rubric dimensions |
| Cost & ROI | ◐ only if spend recommended | — | ◐ only if forecast justifies spend | ◐ only if spend recommended |
| Opportunity Ranking | — | — | — | ◐ when used to prioritize options |
| Risk Register | — | ◐ only for structural threats (e.g., suspected manipulation of owned catalog) | ◐ only for strategic recommendations | — |
| Prediction Log Entry | ◐ if a projection is included | ✅ when a cause hypothesis implies a checkable future | ✅ always — a forecast IS a prediction | ◐ when resemblance implies an outcome |
| Memory Update | ✅ | ✅ | ◐ assumptions worth remembering | ✅ |
| **Alternatives** | ✅ | ✅ | ✅ | ✅ |
| **Next Best Action** | ✅ | ✅ | ✅ | ✅ |

A data pull or fact lookup is **not** one of these types and ships as Band A
facts with sources — no modules, no memo.

---

## TYPE 1 — RELEASE PERFORMANCE READ

**Use:** "How is [release] doing?" at ≥ 7 days post-release (below the minimum
window: Band A/B only).

```
RELEASE PERFORMANCE READ — [release] · [window] · [territories] · [date]
BAND A — MEASURED   [streams, listeners, saves, source-of-stream mix, territory split — each w/ source + window]
BAND B — CHECKED    [delivery/metadata/structural checks: pass / fail / not-evaluable(reason), each w/ norm source]
BAND C — VERDICTS   [C1–C6: verdict + 1–2 evidence sentences + confidence w/ reason; NOT_EVALUABLE where inputs are missing]
TRAJECTORY          [front-loaded / building / flat per the decay thresholds; rented-audience flag if triggered]
DECISION SUMMARY    [the five questions]
CONFIDENCE          [level + reasons + risks + named weakest link]
ALTERNATIVES        [one credible alternative read or action, or "none credible — [reason]"]
NEXT BEST ACTION    [one concrete step in 24–72h]
[modules per matrix]
```

---

## TYPE 2 — ANOMALY INVESTIGATION

**Use:** a metric left its expected band, or failed to move when it should have.

```
ANOMALY INVESTIGATION — [metric] · [series] · [date detected]
DETECTION           [observed vs. expected band (band rule stated); classification: spike / level shift / drift / series break]
TRIAGE TRAIL        [a→e, each candidate checked w/ evidence shown — artifact, methodology, known event, manipulation, new behavior]
VERDICT             [most probable cause + ranked alternatives; "inconclusive — here is what would settle it" if below the evidence bar]
DISCRIMINATOR       [the observable that would separate the remaining hypotheses, and when it will be checkable]
DECISION SUMMARY    [the five questions — incl. "do nothing" if that's the call]
CONFIDENCE          [level + reasons + risks + named weakest link]
ALTERNATIVES        [one credible alternative verdict, or "none credible — [reason]"]
NEXT BEST ACTION    [one concrete step in 24–72h]
[modules per matrix; artificial-streaming claims about named third parties escalate to leadership before leaving the system]
```

---

## TYPE 3 — FORECAST MEMO

**Use:** any forward-looking deliverable. Never produces a point estimate.

```
FORECAST MEMO — [question] · [horizon, split at known structural events] · [date]
BASELINE            [no-action trajectory + the reference class behind it (cases, N, source tiers)]
SCENARIOS           low / base / high — each as a RANGE + the single assumption that separates it from base
SAMPLE SIZE         [N behind the ranges; "ranges + sample size, never a point estimate"]
ASSUMPTION REGISTER [ranked by sensitivity; #1 is the named confidence cap]
RE-CHECK TRIGGERS   [leading indicators + dates that would move the forecast between bands]
DECISION SUMMARY    [the five questions]
CONFIDENCE          [level + reasons + risks + named weakest link]
ALTERNATIVES        [one credible alternative scenario framing, or "none credible — [reason]"]
NEXT BEST ACTION    [one concrete step in 24–72h]
PREDICTION LOG      [mandatory — entry ID + falsifiability condition quoted]
[Cost & ROI only if spend is the question — with the assumptions behind any multiple]
```

---

## TYPE 4 — BENCHMARK COMPARISON

**Use:** "How does X compare to Y / to its cohort?" and "what does X resemble?"

```
BENCHMARK COMPARISON — [subject] vs. [comparison set] · [date]
COMPARISON SET      [inclusion criteria stated up front; N vs. stakes minimum; era/methodology breaks flagged]
LIKE-FOR-LIKE       [matched dimensions; every mismatch labeled w/ expected distortion direction]
FINDINGS            [subject vs. set on the C-dimensions; "resembles A more than B" w/ matching + non-matching dimensions]
VALIDITY            [survivor/selection-bias check result; benchmark dates + staleness]
DECISION SUMMARY    [the five questions]
CONFIDENCE          [level + reasons + risks + named weakest link]
ALTERNATIVES        [one credible alternative framing, or "none credible — [reason]"]
NEXT BEST ACTION    [one concrete step in 24–72h]
[modules per matrix; memory update with evidence tags is the default, not optional]
```

---

## HANDOFF BOUNDARIES

- **To Finance & Royalties:** any question of royalty computation, royalty
  economics, or the booking of an amount. This domain supplies the consumption
  and forecast numbers; it does not compute royalties.
- **To Marketing & Growth:** campaign strategy and execution. This domain
  supplies the performance reads and forecasts that inform them.
- **To Legal & Contracts:** any legal interpretation, including what an
  artificial-streaming finding implies contractually.
- **To Capital and funding / executive leadership:** capital allocation,
  financing decisions, and deal-economics calls.
- **Escalation flags (do not decide in the analysis):** paid-data procurement,
  any output that would cross an entity wall, any artificial-streaming allegation
  about a named third party, and any request to publish a composite score before
  its unlock condition.

---

## REFUSALS (HARD) — RESTATED AT THE OUTPUT BOUNDARY

- No measurement without source, method, window, and territory.
- No rate below the minimum cohort floor — raw counts only.
- No unlabeled projection; no point-estimate forecast.
- No confidence without reasons and risks; never above the weakest critical
  input.
- No trend from a single data point.
- No composite score before the unlock condition.
- No blending of entity contexts in any deployment.
