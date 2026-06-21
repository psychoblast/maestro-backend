# Digital Release Quality Scorecard

A structured assessment model for a digital release's operational readiness and
revenue-capture completeness. Use it for pre-delivery QC, post-delivery review,
periodic catalog-health checks, and acquisition due diligence on a specific release.

## Scoring Architecture

Each dimension receives a letter grade (A+ through F) anchored to evidence. Grades
are primary; the weighted composite is secondary and explicitly non-comparable
across releases until calibrated. Every dimension states its evidence basis
(MEASURED from data, SOURCED from documentation, or JUDGED from inference) and its
confidence (FULL / PARTIAL / LOW). Confidence is capped by the weakest sub-signal.

## Eight Dimensions

| # | Dimension | Indicative weight | What it measures |
|---|-----------|-------------------|------------------|
| D1 | Metadata Completeness | 0.22 | Every mandatory field present and correct; supplemental fields populated where they affect discovery |
| D2 | Identifier Integrity | 0.20 | ISRC and UPC validity, uniqueness, and conflict-free status; ISRC↔ISWC linkage correctness |
| D3 | Audio/Artwork Spec Compliance | 0.15 | Audio and artwork meet current platform specifications |
| D4 | Rights-System Coverage | 0.18 | Content-recognition and UGC rights systems activated where activity exists |
| D5 | Delivery Timeline | 0.10 | Delivery and editorial windows met; pre-save/pre-order set where intended |
| D6 | Territory Configuration | 0.08 | Availability matches the rights position; no over-broad or under-broad config |
| D7 | Error History | 0.04 | Open errors, prior rejections, and recurrence patterns |
| D8 | Post-Release Monitoring | 0.03 | Verification that delivery and rights state remain correct after going live |

Weights are working defaults, not calibrated values. They orient attention; they do
not produce a cross-release-comparable number.

## Grade Anchors

- **A+ / A** — complete and verified; no gaps; evidence is MEASURED or SOURCED.
- **B** — substantially complete; only cosmetic or low-impact gaps.
- **C** — material gaps that reduce discovery or income but do not block delivery or
  misroute royalties.
- **D** — a gap that misroutes royalties, blocks delivery, or creates active rights
  liability; remediation required.
- **F** — multiple critical gaps; the release is not fit for delivery or is actively
  losing income.

## Hard Gates

A hard gate forces the relevant dimension to D (or lower) regardless of other
signals, because the condition represents active loss or liability:

- **HG-1 — Active ISRC conflict.** A confirmed ISRC conflict forces D on Identifier
  Integrity; active royalty misrouting; IMMEDIATE remediation.
- **HG-2 — Delivery rejection.** A current rejection forces D on Audio/Artwork Spec
  Compliance until the rejection is corrected and delivery accepted.
- **HG-3 — Active erroneous content-recognition claim.** A confirmed erroneous third-
  party claim caps Rights-System Coverage; revenue diversion is active.
- **HG-4 — Active territory rights liability.** Content live in a territory without
  cleared rights caps Territory Configuration; IMMEDIATE remediation.

## Action Tiers

The scorecard drives action, not just a number:

- **IMMEDIATE** — any dimension at D+ or below, or any hard gate triggered. State the
  gap, the required action, and the daily revenue impact or rights risk.
- **PRIORITY** — C or C− in a dimension weighted ≥0.15. Structured remediation with a
  timeline.
- **OPTIMIZE** — C+ or B− in a dimension weighted ≥0.15. Available improvement and
  expected qualitative outcome.
- **MAINTAIN** — B or above. No action beyond monitoring.

## Composite and Calibration Discipline

State the composite as PROVISIONAL until a sufficient body of outcome-checked
evaluations exists. The composite is secondary to per-dimension grades in every use,
and is not comparable across releases while weights are uncalibrated. Always name the
weakest-link cap that constrains composite confidence.

## Operational-Excellence Frame

A useful framing question for any assessment: *"If a platform's label-relations team
audited this release today, what would they find incomplete, incorrect, or
unoptimized — and what is it costing per day?"* Answer with evidence from the
dimension grades: which dimensions create active cost (IMMEDIATE), which create
opportunity cost (PRIORITY/OPTIMIZE), and which are genuinely strong (MAINTAIN).

## NOT EVALUABLE Discipline

Every dimension that cannot be graded from the provided data is marked NOT EVALUABLE
with the minimum data required to grade it. Omitting NOT EVALUABLE sub-signals is a
precision violation — a dimension graded on partial data must say so.
