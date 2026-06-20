# Brand Connect — Output Templates
Version: v1.0 — PLMKR Brand Connect

---

## Usage Rules (apply to all templates)

- **DQS scorecard required on every deal assessment.** A deal evaluation without the 8-dimension DQS scorecard is incomplete output.
- **Dim-1 / Dim-2 independence is structural.** Strategic Value, Fit & Leverage (Dim-1) is scored and reported INDEPENDENTLY of Economic Value & Deal Economics (Dim-2). The Strategic Leverage Statement is always presented BEFORE the Economic Assessment.
- **Estimates labeled.** Every deal figure, market rate, or leverage valuation carries ESTIMATE / NOT QUOTABLE with stated comparable basis and vintage inline.
- **Confidence tagging mandatory.** Every scored dimension carries: evidence type (observed / told / inferred), confidence level (high / medium / low), and the assumption whose failure would change the score by ≥1 point.
- **Told-absence vs. INFERRED.** Told-absence of a required input — no kill fee confirmed, no exit right included, no diligence conducted — is evidence scored on its anchor. NOT defaulted to 3, NOT labeled INFERRED. INFERRED applies only when no observed or told signal bears on a dimension.
- **PROVISIONAL.** When any dimension is scored INFERRED (defaults to 3), the composite is labeled PROVISIONAL — [X] dimension(s) inferred.
- **Opportunity cost always named.** Every GO recommendation names what is forgone.
- **Handoffs flagged.** When a section touches legal review, complex deal papering, or equity deal analysis, route to LEX-CIPHER and name the specific question or provision requiring review.

---

## Template 1 — Deal Quality Assessment Memo

*The primary deliverable for any brand partnership deal evaluation or go/no-go recommendation. The DQS scorecard is embedded here.*

---

### MEMO HEADER

```
Subject:     [ONE-LINE DESCRIPTION — e.g., "DQS ASSESSMENT: [DEAL TYPE] with [BRAND CATEGORY]"]
Deal ID:     [unique identifier for tracking]
Date:        [YYYY-MM-DD]
Artist tier: [GOLD / PLATINUM / DIAMOND]
Deal owner:  [role responsible for this recommendation]
```

---

### DQS SCORECARD — SUMMARY

| Dim | Dimension | Weight | Score (1–10) | Evidence type | Confidence | Key assumption (score changes ≥1 pt if wrong) |
|-----|-----------|--------|--------------|---------------|------------|------------------------------------------------|
| 1 | Strategic Value, Fit & Leverage | 0.18 | [ ] | observed / told / inferred | high / medium / low | [ASSUMPTION] |
| 2 | Economic Value & Deal Economics | 0.16 | [ ] | observed / told / inferred | high / medium / low | [ASSUMPTION] |
| 3 | Partner Quality & Credibility | 0.14 | [ ] | observed / told / inferred | high / medium / low | [ASSUMPTION] |
| 4 | Deal Structure & Terms | 0.14 | [ ] | observed / told / inferred | high / medium / low | [ASSUMPTION] |
| 5 | Risk & Downside Exposure | 0.14 | [ ] | observed / told / inferred | high / medium / low | [ASSUMPTION] |
| 6 | Execution Feasibility & Capacity | 0.10 | [ ] | observed / told / inferred | high / medium / low | [ASSUMPTION] |
| 7 | Opportunity Cost & Alternatives | 0.08 | [ ] | observed / told / inferred | high / medium / low | [ASSUMPTION] |
| 8 | Reversibility & Optionality | 0.06 | [ ] | observed / told / inferred | high / medium / low | [ASSUMPTION] |

```
DQS = (SV×0.18) + (EV×0.16) + (PQ×0.14) + (DS×0.14) + (RE×0.14) + (EF×0.10) + (OC×0.08) + (RO×0.06)
    = [CALCULATED VALUE]

Band:
  [ ] Green  — RECOMMEND   (8.0–10.0) — deal is sound; proceed to documentation
  [ ] Yellow — CONDITIONAL (6.0–7.9)  — resolve 1–2 named gap dimensions before commit
  [ ] Amber  — NOT READY   (4.0–5.9)  — material gaps require resolution before committing
  [ ] Red    — NOT VIABLE  (1.0–3.9)  — hard gaps require remediation before re-evaluation

Partner Quality Gate (Dim-3):  [ ] CLEAR  [ ] TRIGGERED — RECOMMEND BLOCKED
Risk & Exposure Gate (Dim-5):  [ ] CLEAR  [ ] TRIGGERED — RECOMMEND BLOCKED

Composite label: PROVISIONAL (until 30+ outcome-checked evaluations logged)
Composite confidence: [high / medium / low] — capped by: [name dimension if applicable]
```

---

### SECTION 1 — RECOMMENDATION

```
VERDICT:  [ ] RECOMMEND   — deal is sound; proceed to LEX-CIPHER review and documentation
          [ ] CONDITIONAL — proceed, resolving named conditions before commitment
          [ ] NOT READY   — material gaps require resolution before any commitment
          [ ] NOT VIABLE  — hard gate triggered or Red band; do not proceed in current form

Precise scope:
  [State exactly what is recommended: deal type, structure framework, terms basis, and any
   conditions or reservations. "We should move forward" is not a recommendation.]

Conditions (for CONDITIONAL):
  [State precisely with timelines.]

Hard gate statement — REQUIRED; state regardless of whether gate fires:

  Partner Quality Gate (Dim-3):
    [ ] CLEAR — Dim-3 = [SCORE]; brand assessed credible for this deal type
    [ ] TRIGGERED — (1) Gate: PARTNER QUALITY GATE TRIGGERED (2) Disqualifying condition: [SPECIFIC — evidence type stated]
        (3) No composite score overrides this gate. (4) Remediation: [SPECIFIC CONDITION + EVIDENCE NEEDED]

  Risk & Exposure Gate (Dim-5):
    [ ] CLEAR — Dim-5 = [SCORE]; no fatal, unmitigated exposure confirmed
    [ ] TRIGGERED — (1) Gate: RISK & EXPOSURE GATE TRIGGERED (2) Fatal exposure: [SPECIFIC — evidence type stated]
        (3) No composite score overrides this gate. (4) Remediation: [SPECIFIC CONDITION + EVIDENCE NEEDED]

Opportunity cost statement:
  [Specific: "Committing to this deal forecloses [NAMED ALTERNATIVE / CATEGORY] during
   [WINDOW], at an estimated opportunity cost of ESTIMATE [RANGE]. This cost is accepted
   because [REASON]."]
```

---

### SECTION 2 — STRATEGIC LEVERAGE STATEMENT

*Dim-1 analysis — reported INDEPENDENTLY of and BEFORE deal economics.*

```
Leverage tests:
  Leverage-transfer test:
    [ ] PASSED — brand provides access/audience the artist cannot reach efficiently elsewhere
    [ ] FAILED — leverage is marginal or replicable; reason: [STATED]

  Credibility-transfer test:
    [ ] PASSED — brand's cultural positioning meaningfully elevates artist perception
    [ ] FAILED / REVERSED — credibility flow is FROM artist TO brand; this is not leverage
    [ ] NOT APPLICABLE

  Commercial-infrastructure test:
    [ ] PASSED — brand's marketing spend/reach demonstrably amplifies artist commercial outcomes
    [ ] FAILED — claimed infrastructure lacks specificity; breadth asserted without demonstrable delivery
    [ ] NOT APPLICABLE

Named leverage types identified:
  [ ] Audience access leverage — [SPECIFIC: what audience, otherwise unavailable or costly]
  [ ] Credibility leverage — [DIRECTION: TO artist — note if reversed]
  [ ] Distribution / co-marketing leverage — [SPECIFIC: committed spend, confirmed channels]
  [ ] Data leverage — [THREE-CONDITION TEST: proprietary? current? decision-differentiating?]
  [ ] Exclusivity / preferred commercial position
  [ ] None identified — this deal is evaluated as a pure transaction on Dim-2 alone

Strategic fit:
  [ ] Direct and specific — advances [NAMED CAREER PRIORITY] in a documented way
  [ ] Adjacent — touches relevant category without directly advancing a documented priority
  [ ] Absent — no identifiable fit

Dim-1 score: [SCORE] — evidence: [STATED] — confidence: [h/m/l]
  Key assumption: [what, if wrong, changes Dim-1 by ≥1 point]
```

---

### SECTION 3 — ECONOMIC ASSESSMENT

*Dim-2 analysis — reported INDEPENDENTLY of and AFTER Strategic Leverage Statement.*

```
Deal economic structure:
  Total consideration:
    Cash: ESTIMATE [AMOUNT OR RANGE] / [CONFIRMED if told/observed]
    In-kind: [DESCRIBED — valued at artist's utility, not brand's retail value]
    Co-marketing: ESTIMATE [CHARACTERIZE — committed vs. aspirational; channels named]
    Revenue participation: [DESCRIBED — model range if applicable]

  Net consideration after production obligations:
    Production cost obligations: [BOUNDED / UNBOUNDED — describe]
    Estimated net: ESTIMATE [RANGE]

  Payment schedule:
    Front-loaded (≥50% at signing): [ ] YES  [ ] NO
    Kill fee: [ ] CONFIRMED — [AMOUNT OR PERCENTAGE]  [ ] ABSENT — flag

  Market-rate assessment:
    Deal class: [DEAL TYPE, ARTIST REACH TIER, TERRITORY SCOPE]
    Market rate characterization: ESTIMATE [above / at / below] — comparable basis: [STATED]

Dim-2 score: [SCORE] — evidence: [STATED] — confidence: [h/m/l]
  Key assumption: [what, if wrong, changes Dim-2 by ≥1 point]
```

---

### SECTION 4 — PARTNER ASSESSMENT

*Backs Dim-3 (Partner Quality & Credibility).*

```
Brand category: [DESCRIPTIVE — consumer category, scale, market tier]

Track record:
  Prior artist partnerships documented: [NUMBER]
  Outcome quality: [ ] Positive  [ ] Mixed  [ ] Negative  [ ] Unknown / INFERRED at 3
  Payment reliability: [CONFIRMED / UNCONFIRMED]

Brand reputation:
  Values alignment with artist: [ ] Strong  [ ] Adequate  [ ] Tension present: [DESCRIBE]
  Known controversies: [ ] None  [ ] Present: [NAME — assess materiality]

Delivery infrastructure:
  Creative approval process: [CHARACTERIZED — rounds, timeline, organizational complexity]
  Named brand deal owner: [ ] Confirmed  [ ] Unconfirmed

Dim-3 score: [SCORE] — hard gate: [ ] CLEAR  [ ] TRIGGERED
```

---

### SECTION 5 — DEAL STRUCTURE ASSESSMENT

*Backs Dim-4 and Dim-8.*

```
Exclusivity:
  Category: [NAMED SPECIFICALLY]
  Scope: [ ] Precisely scoped  [ ] Over-broad — flag: [CATEGORIES BEYOND DEAL SCOPE]
  Duration: [STATED — relative to active deal period]
  Carve-outs: [ ] Adequate  [ ] Absent or inadequate — flag

Creative approval:
  Approval rounds defined: [ ] YES — [NUMBER]  [ ] NO — flag
  Turnaround SLA: [ ] DEFINED — [DAYS]  [ ] UNDEFINED — flag
  Content created for deal IP: [ ] Vests in artist  [ ] Shared  [ ] Vests in brand — flag

Exit and kill fee:
  Artist-exercisable exit right: [ ] Present  [ ] Absent — flag
  Kill fee: [ ] Confirmed  [ ] Absent — flag

Foreclosing terms:
  [ ] None identified
  [ ] Present: [CLAUSE — why it forecloses — mitigation status — route to LEX-CIPHER if unmitigated]

Dim-4 score: [SCORE] | Dim-8 score: [SCORE]
```

---

### SECTION 6 — RISK REGISTER

*Backs Dim-5 (Risk & Downside Exposure).*

```
| # | Risk (named specifically) | Likelihood | Severity | Mitigation | Residual |
|---|--------------------------|------------|----------|------------|---------|
| 1 | [e.g., "brand values crisis during deal term"] | h/m/l | h/m/l | [MITIGATION or NONE] | [RESIDUAL] |

Dim-5 hard gate check:
  Fatal, unmitigated exposure present?
  [ ] YES — RISK & EXPOSURE GATE TRIGGERED
  [ ] NO  — Dim-5 gate clear

Morality clause assessment:
  [ ] Specifically scoped with cure period — acceptable
  [ ] Vague or undefined trigger — flag; route to LEX-CIPHER
  [ ] Absent — flag if deal term exceeds 6 months

Dim-5 score: [SCORE] — hard gate: [ ] CLEAR  [ ] TRIGGERED
```

---

## Template 2 — Partnership Brief

*Early-stage deal vetting — for inbound brand inquiries, initial screening, or when full DQS is premature because deal terms are not yet available.*

---

### BRIEF HEADER

```
Brand / deal type: [BRAND CATEGORY with DEAL TYPE — no specific brand names]
Date:             [YYYY-MM-DD]
Input basis:      [What is available — verbal pitch / term sheet / introductory email]
Disposition:      [ ] PROCEED — initiate full DQS assessment
                  [ ] INFORMATION REQUEST — [WHAT / FROM WHOM / BY WHEN]
                  [ ] DECLINE — reason: [STATED; not "not a fit" without content]
```

---

### PART 1 — PRELIMINARY SIGNAL

```
Dim-1 (Strategic Value):
  [ ] Plausible leverage case — [NAMED LEVERAGE TYPES — preliminary]
  [ ] Unclear — requires investigation
  [ ] No identifiable leverage — evaluate as pure transaction on Dim-2

Dim-3 (Partner Quality):
  [ ] Appears credible — full diligence required before commitment
  [ ] Red flags: [NAMED — requires resolution before proceeding]
  [ ] Potential disqualifying condition — DO NOT PROCEED pending gate assessment

Dim-5 (Risk Exposure):
  [ ] No apparent fatal exposure at this stage
  [ ] Potential exposure: [NAMED]
  [ ] Apparent fatal exposure — DO NOT PROCEED pending gate assessment

NOTE: A disqualifying partner condition (Dim-3) or fatal exposure (Dim-5) identified at preliminary
stage terminates further assessment until resolved. Do not proceed to full DQS with a known gate
trigger unresolved.
```

---

### PART 2 — GAPS AND NEXT STEPS

```
Critical inputs missing before full DQS:
  [ ] Brand track record and payment history — due diligence required
  [ ] Deal term sheet or draft agreement — required before Dim-4 or Dim-5 assessment
  [ ] Deal economics detail — required for Dim-2
  [ ] Category exclusivity scope — required for Dim-7 and Dim-8

Disposition basis: [Specific reason for stated disposition]

If PROCEED — priority inputs to request: [NAMED; from whom; by when]
```

---

## Template 3 — Contract Red Flag Checklist

*Use when reviewing draft or executed brand partnership agreements for common artist-adverse terms. This template supports LEX-CIPHER routing by identifying the provisions requiring legal review.*

---

### RED FLAGS — REJECT OR NEGOTIATE

| Provision | Status | Priority |
|-----------|--------|----------|
| Category exclusivity too broad — covers adjacent revenue streams | [ ] Present  [ ] Absent | High if present |
| Unlimited usage rights on name and likeness — scope/territory/term undefined | [ ] Present  [ ] Absent | High if present |
| Morality clause with vague termination triggers — no defined behaviors | [ ] Present  [ ] Absent | High if present |
| Morality clause with no cure period | [ ] Present  [ ] Absent | High if present |
| Payment entirely backend-weighted — no upfront component | [ ] Present  [ ] Absent | Medium |
| No kill fee if brand cancels — all cancellation risk on artist | [ ] Present  [ ] Absent | High if present |
| Unlimited approval rights on all content — no turnaround SLA | [ ] Present  [ ] Absent | Medium |
| Perpetual rights on content created for campaign | [ ] Present  [ ] Absent | High if present |
| Social media follower minimums triggering consideration clawbacks | [ ] Present  [ ] Absent | Medium |
| Brand veto on all artist content (beyond brand-related content) | [ ] Present  [ ] Absent | High if present |
| Non-compete provisions beyond deal's direct product category | [ ] Present  [ ] Absent | High if present |
| Automatic renewal without artist's affirmative election | [ ] Present  [ ] Absent | Medium |

**Route to LEX-CIPHER for review:** Any High-priority finding should be reviewed by LEX-CIPHER before any commitment or counter-signature. Provide LEX-CIPHER with the specific clause language and the requested modification.
