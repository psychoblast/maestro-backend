# PLMKR Sync Agent — Scoring Rubric
Version: v1.0 — Four-Dimension Model
Status: SCOREABLE. Composite is PROVISIONAL until unlock condition met.

## Weights

| Dimension | Weight | Reasoning |
|---|---|---|
| Brief fit | **40%** | Placement decisions are made on fit; nothing else makes a supervisor say yes. |
| Clearance complexity | **25%** | The largest post-fit source of lost deals and the dimension carrying reputational risk. |
| Turnaround feasibility | **20%** | Near-binary against the buyer's deadline. |
| Fee tier | **15%** | Fee prices the win; it rarely decides it. Low weight prevents chasing fee-rich/poor-fit pitches — the classic sync-desk failure mode. |

## Scale & composite
Each dimension scored 1–5 against the anchors below. **Composite = Σ(weight × score × 20) → 0–100**. Every composite is reported with per-dimension scores and reasons — a number without reasons is invalid output.

## PROVISIONAL label
The composite is **PROVISIONAL** until an outcome corpus of ≥30 outcome-checked assessments exists in `feedback/outcomes/`. Until that threshold is met, do not present the numeric composite as calibrated or comparable across assessments. State the unlock condition explicitly in every output: *"This composite is PROVISIONAL — unlock condition: ≥30 outcome-checked assessments in feedback/outcomes/"*

## Hard gates (caps, not zeros — a gated score is reported with its gate named)
1. **Clearance status UNKNOWN** → composite capped at **40**, flagged **"map chain first."** An unmapped chain is unpitchable as cleared regardless of fit; a high-fit/unknown-chain track is a clearance work order, not a discard.
2. **Turnaround feasibility = 1** → composite capped at **25**. A yes that arrives after the air date is a no.
3. **Brief fit ≤ 2** → **do not pitch**, regardless of composite (protects the sender score).

## Anchors

### Brief fit (40%) — what the references and scene actually demand
- **5** — Matches the shared properties of the brief's references (tempo, era, energy, vocal type, lyric theme) AND the scene's emotional function; no constraint violations
- **4** — Matches the shared properties with one defensible deviation (e.g., era off but energy/vocal exact)
- **3** — Right genre and mood; wrong era, energy arc, or vocal type
- **2** — Tangential: matches the prose description but not what the references share
- **1** — Off-brief or violates a hard constraint (lyric restriction, sound-alike warning)

### Clearance complexity (25%) — higher = simpler
- **5** — One-stop, papered, instant yes available
- **4** — Two known, responsive parties; both sides quotable inside the buyer's window
- **3** — ≤4 parties, all identified and reachable; no approval-rights landmines known
- **2** — Parties unidentified, estate involvement, or embedded sample/interpolation chain
- **1** — BLOCKED or actively disputed chain

### Fee tier (15%) — buyer budget vs. our band for this use
> Bands are ESTIMATE until owner comparables land — score the *alignment*, never quote the band to the buyer.
- **5** — Buyer's budget at or above the top of our band; headroom for the full ask
- **4** — Budget sits in the upper half of our band
- **3** — Inside the band; standard negotiation
- **2** — At or marginally below our floor; closeable only as a named strategic exception
- **1** — Below floor with no strategic case; decline

### Turnaround feasibility (20%) — buyer deadline minus chain latency
- **5** — Cleared confirmation deliverable same-day
- **4** — Meets the deadline with ≥50% buffer
- **3** — Meets the deadline, no buffer
- **2** — Meets it only if third parties expedite (their speed, not ours)
- **1** — Cannot meet the deadline

**Structural-ineligibility binding:** a major-label / major-publisher master, or an estate / disputed / sample-bearing chain, against a short-deadline buyer class (trailer, rush-ad) scores **T=1 by default** — structurally ineligible regardless of fit. A theoretical or unsourced "they might expedite" does NOT lift the score to 2; only a **confirmed rush quote already in hand** changes the structural status.

## Verdict ladder

| Verdict | Composite threshold | Conditions |
|---|---|---|
| **PASS** | Any | Any hard gate triggered (regardless of composite); OR brief fit ≤ 2 |
| **HOLD** | 40–59 | No hard gate triggered; clearance or turnaround needs work before pitch |
| **PITCH** | 60–100 | All three hard gates clear; brief fit ≥ 3 |

## Standing requirements
- Every rubric score is a logged, falsifiable prediction (brief-fit scores falsified by placement vs. pass; turnaround scores by actual days; fee-tier scores by closed fee vs. band).
- Weight or anchor changes only via the quarterly tuning protocol with cited outcome evidence — never on vibes.
- Per-buyer-class weight variation is explicitly deferred until outcome data argues for it.

## Prediction-Logging Hook
Every scored assessment logs: dimension scores and rationale · composite value · verdict · evidence basis per dimension · date of assessment · outcome check date (90 days default for sync assessments). Log as a falsifiable prediction — the verdict and composite are claims, and they should be checked against placement or pass outcomes.
