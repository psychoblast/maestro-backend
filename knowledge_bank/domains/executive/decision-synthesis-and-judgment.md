# Decision Synthesis & Judgment

The executive's primary craft is synthesis: taking functional inputs of unequal
quality, depth, and certainty — sometimes contradictory — and producing a single
falsifiable decision. This file covers multi-input architecture, evidence
weighting under conflict, structured decision frameworks, dissent handling,
deciding under incomplete information, and the canonical decision-memo shape.

All directional figures are ESTIMATE / NOT QUOTABLE until confirmed against
measured outcomes.

---

## Multi-Input Decision Architecture

The first job is not to decide — it is to understand what kind of inputs you have
and what weight each deserves. Inputs fall into four categories:

1. **Domain-specialist assessments.** A specialist has mapped a problem from
   inside their function. Their conclusions are authoritative within that scope
   and are not overrideable on executive opinion alone without domain-level
   counter-evidence.
2. **Quantitative evidence.** Financial models, market data, deal economics.
   Quality varies sharply: historical measured data is high-trust; forward
   projections are assumptions formatted as data. Always ask who built the model
   and what assumptions drive it.
3. **Qualitative intelligence.** Market observations, relationship context,
   cultural signal. Valid and often capturing what models cannot — but lower
   evidentiary weight than structured analysis, and labeled as such.
4. **Precedent and comparables.** How similar decisions played out. Internal
   measured history outranks industry anecdote; benchmarks are orientation, not
   decision inputs.

Map every input to its evidence tier (A/B/C/D — see the doctrine file) before
weighting it. A Tier D input never drives a recommendation; if Tier D is the only
basis, flag the gap and decline GO.

---

## Evidence-Quality Weighting for Conflicting Inputs

When two specialists disagree, the most common error is averaging their views into
a false middle that satisfies neither. Weight by evidence quality, then reconcile
the residual disagreement explicitly. The five-step process:

1. **Map each input to its domain.** Provenance of the analysis matters: a
   finance model about market addressability is weaker than a market specialist's
   model of the same thing.
2. **Assess each input's evidence basis.** Measured data, structured analysis,
   comparable precedent, or professional intuition — all valid, none equivalent.
   Label the type before weighting.
3. **Check for conflicts of interest.** A specialist whose team budget depends on
   a GO will tend to produce a more optimistic analysis. This does not invalidate
   the input; it weights it alongside that context.
4. **Identify where the disagreement lives.** Factual disagreements must be
   resolved before synthesis. Interpretive disagreements can coexist — the memo
   names which interpretation the decision rests on and what changes if the other
   is correct.
5. **Weight by evidence quality, not title or volume.** A junior analyst with
   good data outweighs a senior voice with strong intuition.

**Convergence test:** after weighting, check whether the most important drivers of
disagreement are resolvable within the decision timeline. If resolvable, get more
evidence even briefly. If not, decide anyway, document the residual uncertainty as
a labeled assumption, and state what evidence would change the call.

---

## Structured Decision Frameworks

Select the framework that fits the decision architecture; several may apply at
once.

**Pre-Mortem.** Before finalizing a GO, assume it is six to twelve months later
and the decision failed badly. Write the failure backward — what went wrong, why,
and what early warning signs were missed. Surfaces risks that optimistic synthesis
suppresses, while something can still be done about them.

**Driver / Approver / Contributor / Informed.** Name who drives the analysis, who
approves, who contributes specialist input, and who is informed. Confusing
contributor with approver produces decisions that feel collective but have no
single accountable owner — which makes learning impossible.

**Analysis of Competing Hypotheses.** List all plausible hypotheses (GO / NO GO /
alternatives). For each piece of evidence, rate consistency with each hypothesis,
not whether it supports the favored one. The hypothesis with the least
inconsistent evidence wins. Combats confirmation bias.

**Reversibility Assessment.** Classify the decision on reversibility and stakes
(see the quadrant in the doctrine file). Raise the evidence bar in the
irreversible-plus-high-stakes quadrant.

**Inversion.** Instead of "how do we make this succeed," ask "what would guarantee
this fails." List the failure causes; assess which are present. A decision with
three of its top five failure causes active and unmitigated is a poor GO
candidate regardless of how the upside looks.

---

## Dissent Architecture: Surfacing, Not Suppressing

False consensus — a memo presenting a unanimous recommendation when the underlying
inputs were divided — is the most dangerous output an executive can produce. It
eliminates the information value of disagreement and prevents post-mortem learning.

Dissent-handling rules:

1. **Identify all dissenting positions before synthesis.** Absence of enthusiasm
   is a signal. A specialist who declined to strongly support a GO is registering
   doubt. Written objections outweigh in-meeting silence.
2. **State each dissenting position precisely** — which function holds it, what
   evidence underlies it, and why it was or was not dispositive.
3. **Never use hedging to make dissent disappear.** Not "while there are some
   concerns, the assessment is positive," but "Finance raised concern [X]. We
   proceed because [Y]. This is revisited if [trigger]."
4. **The bar to override a domain expert on their own domain is high.** If
   overriding, the justification is explicit, on-record, and falsifiable.
5. **Record dissent even when overriding.** If the dissenter was right, the
   organization must be able to learn from it.

Common false-consensus patterns: editing out the disagreement; consensus under
time pressure (specialists comply rather than contribute); grade-inflating a 3-1
split into "broad alignment with some nuance"; treating in-meeting silence as
agreement when written concerns exist.

---

## Deciding Under Incomplete Information

No major decision has complete information. The question is whether the gap is
acceptable given stakes and reversibility, and what the executive is committing to
by deciding despite it.

1. **Name every known unknown.** An unknown not named is a hidden assumption
   treated as fact — where decisions go wrong silently.
2. **Classify each unknown by decision-sensitivity.** Which unknowns, if resolved
   adversely, flip the recommendation? Those are the load-bearing assumptions.
3. **State the forcing function.** Why must this be decided now? A decision
   without a stated forcing function may be premature.
4. **Name what would change the call.** If the answer to "what would flip this to
   NO GO" is "nothing," the decision is rationalization, not honest engagement.
5. **Set a review trigger.** Identify the observable leading indicator that
   signals the decision is tracking toward or away from intent — making it
   falsifiable and correctable.

| Gap type | Response | Failure mode |
|----------|----------|--------------|
| Fillable within the timeline | Fill before deciding | Deciding without filling fillable gaps |
| Too costly/slow to fill | Decide; label the assumption; set review trigger | Treating unfilled gaps as resolved |
| Structurally unfillable | Accept uncertainty; reduce stakes or increase reversibility | Claiming certainty about the unknowable |

Inaction has an opportunity cost that must also be named. Refusing to decide under
uncertainty is not caution; it passes the cost of delay to the organization.

---

## The 11-Part Decision Memo (Canonical Framework)

The decision memo is the primary output for any major go/no-go, capital
commitment, or strategic commitment. Every section guards against a specific
failure mode; the memo is falsifiable by design.

**Decision → Evidence → Specialist Input → Areas of Agreement → Areas of
Disagreement → Assumptions → Risks → Alternatives Considered → Opportunity Cost →
Confidence Level → Next Actions.**

1. **Decision.** A single, falsifiable statement: GO / NO GO / CONDITIONAL GO /
   DEFERRED, with precise scope. A conditional GO states the condition precisely
   and with a timeline; a vague conditional GO is a disguised NO GO. *Guard:
   decision ambiguity.*
2. **Evidence.** The factual basis, each item labeled with source tier and
   currency. Projections are assumptions, not evidence; absent expected evidence
   is named, not elided. *Guard: fabricated authority.*
3. **Specialist Input.** Each specialist's assessment in their own terms, not the
   executive's paraphrase toward the recommendation. Solicited-but-absent inputs
   are noted; a missing load-bearing input may trigger the Evidence gate. *Guard:
   cherry-picking.*
4. **Areas of Agreement.** Genuine convergence on significant dimensions, stated
   specifically — not manufactured by editing out disagreement first. *Guard:
   false consensus.*
5. **Areas of Disagreement.** MANDATORY. Every conflicting position, with function
   named, the disagreement stated precisely, the underlying evidence, and the
   reason the recommendation proceeds (or is conditional/NO GO). If there is no
   dissent, state so explicitly. *Guard: suppressed dissent.*
6. **Assumptions.** Every claim resting on inference or projection, stated
   precisely, labeled by directional sensitivity, with a watchable indicator.
   Load-bearing assumptions (flip the recommendation if wrong) are marked. When
   two reasonable assumptions exist, name both and which is used. *Guard:
   assumption laundering.*
7. **Risks.** Named risks with likelihood, severity, mitigation, residual risk,
   and an early-warning trigger — not a generic disclaimer. The Risk hard gate is
   checked here. *Guard: risk elision.*
8. **Alternatives Considered.** Genuine alternatives, each with its primary
   advantage and the reason it was not selected. "Do nothing" is always an
   alternative; if do-nothing is not meaningfully worse, reconsider the
   recommendation. *Guard: premature foreclosure.*
9. **Opportunity Cost.** What the organization forgoes — named specifically, not
   gesturally. Capital deployed here is unavailable elsewhere; the cost of
   inaction is also named. *Guard: decision tunnel.*
10. **Confidence Level.** An evidence-derived, calibrated estimate of the
    probability the decision achieves its objectives — by category (financial,
    execution, market-timing). Confidence is capped by the quality of the worst
    load-bearing input. *Guard: confidence inflation.*
11. **Next Actions.** Specific, owned, time-bound actions. The first action is to
    log the decision and its falsifiability conditions. Review triggers are
    listed. *Guard: decision without implementation.*

### Decision Memo Anti-Pattern Index

| Anti-pattern | Section | Guard |
|--------------|---------|-------|
| Decision ambiguity | 1 | Single, falsifiable commitment |
| Evidence fabrication / laundering | 2, 6 | Label projections ESTIMATE; require source tier |
| Cherry-picked specialist input | 3 | All provided inputs appear; absent inputs noted |
| False consensus | 4, 5 | Section 5 mandatory; state "no material dissent" if none |
| Suppressed dissent | 5 | Dissent stated precisely; override justified on-record |
| Assumption laundering | 6 | Load-bearing flagged; adverse impact stated |
| Risk elision | 7 | Named risks with trigger/severity/mitigation |
| Strawman alternatives | 8 | Genuine advantages; do-nothing always included |
| Decision tunnel | 9 | Opportunity cost named specifically; inaction cost named |
| Confidence inflation | 10 | Confidence tied to evidence; capped by worst input |
| Decision without implementation | 11 | Named owner + due date; review trigger listed |

---

## The Music-Company Decision Landscape

Music-company executive decisions cluster into four archetypes. Naming the
primary archetype determines which inputs are load-bearing.

**1. Signing decisions (talent-led).** A GO commits a roster relationship —
advance, royalty commitment, term, exclusivity. Partially irreversible: the
advance is deployed and the relationship formed, but the contractual term defines
an exit horizon. Primary risk: advance non-recoupment and the opportunity cost of
roster capacity. *Load-bearing inputs:* creative/trajectory assessment and the
financial recoupment model (sensitivity to recoupment scenarios is decisive).

**2. Release-strategy decisions (multi-functional).** How, when, and at what
investment to release a piece of content. Reversible to a degree, but the sunk
cost of release preparation creates lock-in before the decision is formalized.
Primary risk: mistimed release, insufficient promotion budget, or over-investment
in under-ready work. *Load-bearing inputs:* the marketing channel plan and the
streaming projection.

**3. Deal-approval decisions (finance- and legal-led).** Publishing, sync,
distribution, licensing, partnership agreements — from fully reversible to highly
binding. Primary risk: economics below hurdle, legal exposure, or rights grants
that foreclose options. *Load-bearing inputs:* deal economics/recoupment modeling
and contract/exposure review.

**4. Market-entry decisions (strategic).** Entering a new territory, genre
vertical, or business line — capital-intensive, long payback, hard to reverse.
Primary risk: market misjudgment, capacity overextension, capital misallocation.
*Load-bearing inputs:* strategy assessment (sizing, entry mode), capital
requirements, jurisdiction risk, and — frequently de-prioritized — organizational
capacity.

---

## The Four Structural Conflict Zones

Every archetype carries a characteristic structural conflict. Synthesis is not
complete until the conflict is named in Areas of Disagreement with the executive's
resolution stated.

**1. Creative optimism vs. finance conservatism (signings).** Creative sees
potential; finance models recoupment against the advance. *Diagnostic:* is the
financial model using the creative specialist's trajectory assumptions as inputs?
If so, the model is a consequence of the creative case, not an independent check
on it. A model that mirrors the creative case with financial formatting is not a
second opinion.

**2. Marketing investment appetite vs. finance budget constraint (releases).**
*Diagnostic:* does the financial model treat marketing spend as a revenue driver
or only as a budget line? If as a driver, the two functions may be arguing the
same thing from different directions — name which model structure governs.

**3. Legal risk-aversion vs. commercial urgency (deals).** *Diagnostic:* is legal
raising a negotiating risk (terms can improve and the risk goes away) or an
absolute exposure (no terms make it acceptable)? These require different responses.
Legal naming a specific irremediable exposure should produce conditional GO or
NO GO; legal naming a negotiable risk triggers a risk assessment, not a veto.

**4. Market-timing signal vs. organizational capacity.** Intelligence may
correctly identify the optimal moment while capacity assessment correctly
identifies that the move would degrade existing operations. *Diagnostic:* what is
the half-life of the opportunity? If the window is indefinite, waiting for
capacity is valid. If it closes within a defined period, quantify the cost of
inaction against the operational risk of action and commit to one.

---

## GO / NO GO / CONDITIONAL / DEFERRED Logic

| Outcome | Conditions |
|---------|-----------|
| **GO** | Load-bearing inputs present and sufficiently high-trust; no fatal unmitigated risk; dissent surfaced and judged non-dispositive; opportunity cost named and acceptable; confidence reflects evidence quality. |
| **NO GO** | A fatal unmitigated risk is present; or a load-bearing input is absent (Evidence gate); or opportunity cost exceeds what the evidence can justify. |
| **CONDITIONAL GO** | GO subject to a specific, time-bound condition — a named risk resolved by a date, final terms within a stated range, a specialist concern addressed before a milestone. Vague conditions are a disguised NO GO. |
| **DEFERRED** | The forcing function is not genuine; or a fillable gap can be filled within the window at acceptable cost; or a load-bearing assumption can be resolved before the window closes. State what is being gathered and the re-decision date. |

---

## Common Music-Decision Synthesis Failures

1. **Creative conviction substituting for evidence.** A passionate creative
   assessment is a high-trust qualitative input, not a financial case. A signing
   built primarily on conviction without a realistic model operates at low
   evidence quality — confidence must reflect this, and the commitment may need to
   be smaller or staged.
2. **Streaming-trajectory extrapolation.** A short upward trend is not a reliable
   predictor; algorithms amplify and decay. Projecting current growth forward for
   a year without a deceleration scenario is assumption-laundering. Mark "growth
   sustains at [X] for [Y] months" as a LOAD-BEARING ASSUMPTION.
3. **Release-timing groupthink.** When all functions agree on timing, check
   whether it is genuine convergence or social compliance — a timing pre-mortem
   often surfaces risks suppressed because the campaign was already in motion.
4. **Deal-terms optimism.** Models often use the terms being sought rather than
   the terms likely to be agreed. Require a sensitivity analysis across the
   realistic negotiation range; state the economics at expected terms, not
   aspirational ones.
5. **Market-entry enthusiasm without capacity modeling.** The capacity assessment
   is the input most likely to be de-prioritized because it creates friction
   against a direction leadership has already emotionally committed to. Confirm it
   is completed and in the memo before any market-entry GO.
