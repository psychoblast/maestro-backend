# Three-Band Scorecard

PLMKR knowledge base. The scoring architecture for every Data & Analytics
evaluation. Three labeled epistemic classes — **MEASURED**, **CHECKED**,
**JUDGED** — that are never blended into one number that hides which is which. No
composite single score is produced before its unlock condition is met (see §5).

---

## §1 RECONCILIATION PRINCIPLES

The scoring philosophy, adopted as this scorecard's law:

1. **Data-first, scores last.** A score never substitutes for the underlying
   facts; facts ship with the score.
2. **No predictive number until it is earned from real outcome data** — and then
   as ranges + sample size, never a point estimate.
3. **Measured / checked / judged are different epistemic classes** and are never
   blended into one number that hides which is which.
4. **Closed vocabularies + hard validation** wherever a dimension is categorical.
5. **Unmeasurable ≠ zero.** A dimension that can't be evaluated returns "not
   evaluable + why," never a silently imputed score.
6. **Omission over invention**, and opinion is attributed prose, never a
   fabricated measurement.

---

## §2 SCORING ARCHITECTURE: THREE BANDS

Band A and B contain no judgment; Band C contains nothing *but* judgment, clearly
attributed.

### Band A — MEASURED (facts)

Reported with method, source, window, territory. Examples: streams, saves,
listener counts, loudness (LUFS), tempo, chart positions. Third-party
**estimates** (aggregator-class) never appear in Band A — they are inputs to
Band C with their estimated status declared. Social-platform metrics sourced
directly from the platform's own creator analytics are Band A when reported with
source, window, and territory; sourced via a third-party aggregator, they are
estimated inputs to Band C.

### Band B — CHECKED (pass / fail / flag against documented norms)

Each check cites its norm and the norm's source. Three states: pass / fail /
not-evaluable(reason).

| Check set | Checks | Source basis |
|---|---|---|
| **Delivery readiness** | sample rate ≥ 44.1 kHz; bit depth ∈ {16, 24, 32}; format ∈ {WAV, FLAC, AIFF}; loudness in the platform-acceptable LUFS band (target around −14); duration within the deliverable range | DSP delivery specifications |
| **Metadata completeness** | ISRC; contributor credits; title / artist / genre / release date / label present | distribution metadata spec |
| **Structural norms** | intro within the genre-typical ceiling; chorus arrival within the genre-typical window; duration in the streaming-optimized range; a strong moment early enough for short-form discovery | published editorial / structural norms |
| **Loudness characterization** | LUFS bands with documented labels | loudness measurement standard |

New Band B checks may be added **only** with a documented external source.
Thresholds are never invented.

### Band C — JUDGED (rubric dimensions)

Qualitative verdicts on a closed scale, each with stated evidence and confidence
(reasons + risks). **No composite single number** is produced before the unlock
condition (§5).

Verdict scale (closed vocabulary, hard-validated):
`STRONG` / `PROMISING` / `MIXED` / `WEAK` / `NOT_EVALUABLE(reason)`.

| # | Dimension | What it judges |
|---|---|---|
| C1 | **Trajectory shape** | Decay/build pattern vs. cohort: front-loaded, building, or flat; organic share vs. playlist-dependent (rented) volume |
| C2 | **Engagement depth** | Save rate, listener-to-stream ratio, completion vs. genre + source-mix cohort |
| C3 | **Structural & format fit** | Aggregate read of Band B structural checks in context (genre norms differ) |
| C4 | **Sonic & production state** | Mix/master state read from measured facts (LUFS, dynamic range, crest factor where available) |
| C5 | **Positioning clarity** | Mood/genre legibility for editorial and algorithmic placement: closed-vocabulary mood candidates, genre-cohort fit |
| C6 | **Data readiness** | Can this release be analyzed and pitched? Metadata gaps, missing baselines, unclaimed profiles |

---

## §3 SCORE ANCHORS (Band C reproducibility)

Generic anchors; per-dimension specifics live in the dimension files they govern.

- **STRONG** — evidence is measured (Band A), multi-point, cohort-beating; no
  failed critical Band B check; the verdict would survive a hostile analyst's
  review.
- **PROMISING** — direction is favorable but evidence is thin (short window,
  single territory) or one critical input is estimated rather than measured;
  named conditions would confirm.
- **MIXED** — credible evidence points both ways; the tension is named, not
  averaged away.
- **WEAK** — evidence is measured and adverse, or there are multiple critical
  Band B failures; "weak with a fix path" is stated as such.
- **NOT_EVALUABLE(reason)** — inputs missing or unmeasurable; never silently
  scored.

---

## §4 CONFIDENCE & UNCERTAINTY PROPAGATION

Every Band C verdict carries confidence (high / medium / low) **with reasons and
risks**. Confidence is capped by the weakest critical input, weak link named
("confidence capped at medium: the source-of-stream split is inferred from
partial dashboard data, not reported"). Numeric probabilities appear only where
§5 permits.

---

## §5 COMPOSITE SCORING & NUMERIC FORECASTS — DEFERRED, WITH THE UNLOCK CONDITION

- The scorecard produces **no composite number** and **no point-estimate
  forecasts** before the unlock condition. Forecasts ship as ranges + the sample
  size behind them.
- **Unlock condition** for any composite or calibrated numeric layer: a real
  outcome corpus sufficient to validate weights — a floor of at least ~30
  outcome-checked predictions per dimension — plus an evidence-cited change-log
  entry recording the calibration.
- **Pre-score narrative mode:** qualitative trajectory language only ("building,
  fragile, stalling"), zero numeric scores — available before the unlock
  threshold is reached, so users get direction without fake precision.
- Until then, anyone asking for "the score out of 100" gets Band A facts, Band B
  checks, and Band C verdicts — by design. Repeat user pressure does not unlock a
  composite.

---

## §6 VERSIONING & PREDICTION HOOKS

- Every dimension, anchor, or check change after the baseline version requires a
  change-log entry citing outcome evidence; counterfactuals never count as
  evidence.
- Every Band C verdict and every forecast range is logged with its falsifiability
  condition, so scorecard accuracy is measurable from day one and per-dimension
  accuracy can be tracked over time.
