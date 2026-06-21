# Label Ops — Judgment Doctrine & Triage

Encoded defaults governing how label operations makes evaluations and
recommendations. These are operative published-industry defaults; an owner's
calibrations (preferred distribution partners, standard recoupable-cost
definitions, reporting formats) supersede them once supplied.

## 1. Release Timing Decision Logic

```
IF the release has editorial ambitions AND the date is < 6 weeks from master delivery:
  → recommend delay to a minimum 6-week window (8 preferred)
  → state the commercial cost of delay (one cycle) vs. the cost of a compressed
    timeline (editorial consideration forfeited)
IF the release has no editorial ambitions AND operational readiness is confirmed at 4 weeks:
  → proceed; the editorial window is not the binding constraint
IF any hard gate is triggered (legal block, missing identifier, uncleared sample):
  → STOP; the release cannot proceed until the gate resolves
```

## 2. Distribution Partner Selection

```
IF annual streaming revenue < $10K AND < 5 releases:
  → DIY aggregator; cost optimization is the correct primary variable
IF annual streaming revenue $10K–$100K OR 5–30 releases OR editorial ambitions:
  → evaluate a mid-tier partner; editorial relationships are worth the royalty
    concession — but never recommend mid-tier without stating the trade-off
    (royalty % conceded vs. editorial access gained)
IF annual streaming revenue > $100K OR > 30 releases OR an advance is required:
  → evaluate full-service; distribution is a strategic partner, not a utility —
    never recommend a full-service deal for an emerging artist without identifying
    the specific value it delivers
```

## 3. Editorial Pitch Filing Protocol

- File the pitch at every DSP that has a pitch mechanism; always file, never skip.
- Optimal timing: 14+ days before release for the highest consideration rate; 7
  days is the absolute minimum.
- Required content: artist description (≤500 chars); song description (mood, genre,
  story); 3–5 playlist suggestions; context for why the editorial team should care.
- Do not wait for A&R or artist approval to file — the pitch is an ops function.
- Do not present a filed pitch to the artist or management as a commitment to
  placement; the DSP decides.

## 4. Recoupment Calculation Approach

- Always use the contracted recoupable-cost floor for projection, not the
  optimistic version.
- If contract language permits a broad recoupment interpretation (vague "marketing
  costs"), model the broad interpretation as the projection basis.
- Declare cross-collateralization scope to the artist before the first royalty
  statement is issued, not at first statement delivery.
- Use a conservative streaming model: Year 1 at projected peak; Year 2 at 40–60% of
  Year 1; Year 3 at 30–50% of Year 1, unless documented catalog longevity shows a
  flat or growing trajectory.
- State the projection as a range (best case / conservative), not a point estimate.

## 5. NOT EVALUABLE Protocol

When data is insufficient for a label-ops determination:
- Name the specific sub-signal that is NOT EVALUABLE.
- State the minimum data required before a valid assessment is possible.
- Do not estimate a grade for any dimension whose governing sub-signal (ISRC
  status, delivery confirmation, contract royalty rate) is absent — mark that
  dimension NOT EVALUABLE.
- Do not produce an action plan that depends on a NOT EVALUABLE dimension without
  explicitly noting the dependency and what additional data would change the action.

## 6. Anti-Fabrication Symmetry Rule

- Never provide benchmark figures (advance ranges, royalty rates, margin
  benchmarks, streaming projections) without a verifiable source.
- Directional figures are permissible only as directional signal, explicitly
  labeled as such, with the basis named.
- If no verifiable source exists for a claimed benchmark, do not provide it; say
  what can be said (directional, qualitative, contextual) and route the quantified
  claim to the function with real data access.
- Actual comparable deal terms are confidential and not quotable; the grounded
  number is modeled from the artist's own projected revenue × deal structure ×
  royalty rate — never fabricated.
- The rule is symmetric: do not fabricate reassuring benchmarks any more than
  alarming ones.

## 7. Release Delay Trigger Protocol (in order of severity)

1. Any hard gate triggered (legal block, missing ISRC/UPC, uncleared sample) —
   delay is mandatory until resolved.
2. Master not in final approved form at week -6 (single) / week -10 (album) —
   delay recommended; a compressed timeline creates compound failure risk.
3. Artwork not to spec at week -5 (single) / week -8 (album) — delay recommended;
   wrong color space or dimensions will cause delivery rejection.
4. Publishing splits unconfirmed at week -5 — delay recommended; mechanicals
   cannot be configured correctly.
5. Sample clearances verbally confirmed but not legally executed at week -4 —
   delay recommended; verbal clearance is not a clearance.

## 8. Metadata Error Triage

| Severity | Trigger | Response timeline | Action |
|----------|---------|-------------------|--------|
| CRITICAL | Missing ISRC; missing UPC; wrong audio format; artwork causing rejection | Immediate | Pull delivery; correct; re-submit; assess date impact |
| HIGH | Artist-name variant risking a split profile; featured artist in wrong field; explicit flag missing | Before delivery confirmation | Correct in the distributor system before delivery is processed |
| MEDIUM | Missing secondary genre; missing producer credit; minor title-case discrepancy | Within 48h of discovery | Correct via distributor metadata update; may not require re-delivery |
| LOW | Artwork resolution acceptable but below optimal; suboptimal bio text | Before release week | Schedule correction; does not block release |

## Context Assembly Discipline

Before producing any operational determination, confirm that the governing
knowledge is loaded: the core doctrine, the relevant workflow/distribution/
catalog/economics file for the question, and this judgment-and-triage file. If a
governing input is absent, state "CONTEXT INCOMPLETE — [input] not loaded" before
producing output rather than proceeding on partial context.

## Output Discipline

Decision-type outputs (release go/no-go, distribution recommendations, deal-
structure flags, catalog exploitation plans) state status, flags (risk with
likelihood and consequence), and decisions needed (owner + deadline), and include
alternatives and a next-best action within a 24–72h horizon. Every forecastable
claim carries a confidence level and a falsifiability condition — the observable
outcome, by when, that would prove it right or wrong.

See also: [[label-operations-doctrine]], [[label-ops-economics]],
[[label-ops-roster-coordination]].
