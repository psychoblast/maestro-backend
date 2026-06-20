# PLMKR Sync Agent — Output Templates

The sync agent produces five primary output types. Every output enforces the mandatory core: Work Product · Decision Summary · Confidence Assessment with weakest-link cap named.

**Anti-bloat rule:** a draft email does not carry a risk register. A clearance-chain map does not carry ALTERNATIVES. Attaching an irrelevant module is a violation equal to omitting a relevant one.

---

## Template Classification

| Template | Type | Alternatives | Next Best Action |
|---|---|---|---|
| Brief-Fit Scorecard | Decision — verdict (PITCH/HOLD/PASS) | ✓ | ✓ |
| Fee Quote Sheet | Decision — recommendation (what to quote, at what posture) | ✓ | ✓ |
| Pitch Email Draft | Artifact — exempt from decision modules | ✗ | ✗ |
| Clearance Chain Map | Operational status document — exempt | ✗ | ✗ |
| Turnaround Tracker | Operational tracking tool — exempt | ✗ | ✗ |

---

## Brief-Fit Scorecard (decision-type)

Track-against-brief scoring (scoring-rubric.md) leading to a PITCH/HOLD/PASS verdict.

Required fields:
- **Dimensions:** brief_fit · clearance_complexity · turnaround_feasibility · fee_tier — each with score (1–5), weight, rationale (1–3 sentences), confidence (HIGH/PARTIAL/LOW), and NOT EVALUABLE items named
- **Composite:** value (0–100), formula string, PROVISIONAL label, unlock condition verbatim
- **Hard gates:** clearance_unknown_gate · turnaround_gate · brief_fit_gate — each CLEAR or TRIGGERED with reason
- **Verdict:** PITCH / HOLD / PASS with one-paragraph rationale
- **ALTERNATIVES:** if HOLD or PASS, state the specific condition that would change the verdict
- **NEXT BEST ACTION:** single most valuable 24–48h step for the artist/manager
- **Prediction Log Entry:** composite prediction + expected outcome check date (90 days default)

---

## Fee Quote Sheet (decision-type)

Fee quote structure and positioning recommendation per licensing-deal-logic.md.

Required fields:
- **Six-dials definition:** scope · term · territory · media · exclusivity as fixed before price stated
- **Opening quote (per side):** master use · synchronization — with comparable rationale
- **Quote posture:** anchor / quote-to-close / MFN-precision — stated with reason
- **Walk-away floor:** named (even if approximate)
- **ALTERNATIVES:** package vs. itemized, option structures, strategic exception path
- **NEXT BEST ACTION:** specific next step in negotiation
- **Prediction Log Entry:** quote and expected close range; outcome check when deal closes

---

## Pitch Email Draft (artifact — exempt from decision modules)

Pitch email skeleton and honest-pass skeleton. The PITCH/HOLD/PASS decision must be made in the Brief-Fit Scorecard BEFORE this draft is generated.

Pitch email must include:
- Subject line carrying the answer ("3 one-stops for the diner scene — all under $10k")
- Per-track: title · clearance status · why it's on-brief (one line) · fee expectation vs. stated budget
- Stems availability note
- No attachment — streaming link only

Honest-pass email must lead with the honest pass. Never offer below-fit alternates proactively.

---

## Clearance Chain Map (operational — exempt from decision modules)

One map per song per intended use. Records:
- Master side: controller · percentage · status (CLEARED/CLEARABLE/PENDING/BLOCKED/UNKNOWN) · quote deadline
- Publishing side: each controller · percentage · status · quote deadline
- Overall status (weakest link determines overall)
- Complexity flags: samples · interpolations · estates · territorial splits · approval-rights parties

Not a recommendation — a prerequisite for any pitch. UNKNOWN on any line blocks pitching as cleared.

---

## Turnaround Tracker (operational — exempt from decision modules)

Per-brief deadline and milestone tracker:
- Brief received date · buyer deadline · buyer class
- Quote-request dates per rights-holder · quote-received dates
- License paper date · archive date
- Gap tracking: quote → license gap flagged if >5 business days

Anti-pattern: never miss a buyer deadline silently. If a deadline is at risk, notify the buyer immediately with a revised timeline — never go quiet.
