# Marketing Agent — Output Templates
Version: v1.0 — PLMKR Marketing Knowledge (2026-06-20)

Every template enforces:
- **Mandatory core (every output):** Work Product · Decision Summary · Confidence Assessment with weakest-link cap named
- **Conditional modules (attach only when applicable):** Cost & ROI · Opportunity Ranking · Risk Register · Prediction Log Entry

An ROI number without stated mechanism, assumptions, and measurement method is invalid output. Confidence numbers without stated reasons and risks are invalid.

**Decision-type classification:** All templates render recommendations or verdicts. ALTERNATIVES and NEXT BEST ACTION (24–72h) are mandatory.

| Template | Alternatives | Next Best Action |
|----------|--------------|-----------------|
| 1 — Campaign Plan | ✓ | ✓ |
| 2 — Weekly Performance Memo | ✓ | ✓ |
| 3 — Pitch / PR Output | ✓ | ✓ |

---

## Template 1 — Campaign Plan

**When to use:** artist or release campaign evaluation and full campaign plan request.

```
# CAMPAIGN PLAN — [Artist Name] — [Release / Campaign Name]
Date: [YYYY-MM-DD]   Phase: [campaign phase if mid-arc]

---
## WORK PRODUCT

### Marketing Score (scoring-rubric.md v1.0)
| Dimension | Score | Evidence | Confidence |
|-----------|-------|----------|------------|
| Virality (×0.15) | [1–10] | [source] | [observed/told/inferred, H/M/L] |
| UGC Potential (×0.12) | [1–10] | [source] | [observed/told/inferred, H/M/L] |
| Platform Fit (×0.18) | [1–10] | [source] | [observed/told/inferred, H/M/L] |
| Editorial Readiness (×0.13) | [1–10] | [source] | [observed/told/inferred, H/M/L] |
| Touring Synergy (×0.03) | [1–10] | [source] | [observed/told/inferred, H/M/L] |
| Merch & D2C Potential (×0.10) | [1–10] | [source] | [observed/told/inferred, H/M/L] |
| Brand Partnership Potential (×0.07) | [1–10] | [source] | [observed/told/inferred, H/M/L] |
| Fan LTV Potential (×0.22) | [1–10] | [source] | [observed/told/inferred, H/M/L] |
| **COMPOSITE** | **[X.XX]** | | **[PROVISIONAL — N dimensions inferred] or [SCORED]** |

**Band:** [Green / Yellow / Amber / Red]
**Hard gates triggered:** [None / List blocked recommendations]
**Confidence cap:** [Composite confidence capped at [H/M/L]: [weakest dimension] scored [evidence type] — [reason]]

### Campaign Architecture (12-week arc or adjusted)
**Phase 1 — Pre-awareness (Weeks -12 to -6):**
- Channels: [list with rationale]
- KPIs: [list]
- Creative mandate: [one sentence]

**Phase 2 — Pre-release momentum (Weeks -5 to -1):**
- Channels: [list — note editorial pitch window and submission date]
- KPIs: [list]
- Creative mandate: [one sentence]

**Phase 3 — Release week (Day -1 to Day +3):**
- Channels: [all-channel simultaneous; note paid trigger threshold]
- KPIs: [Day-1 save rate target, editorial add target]
- Critical: [any gate conditions for paid spend]

**Phase 4 — Consolidation (Weeks 1–4):**
- Channels: [organic + secondary press + email/SMS]
- KPIs: [WoW stream retention target, follower growth]

**Phase 5 — Catalog conversion (Weeks 5–12+):**
- Channels: [algorithmic + owned lifecycle sequences]
- KPIs: [catalog stream lift target]

### Channel Mix Recommendation
| Channel | Budget % | Mechanism | Measurement method |
|---------|----------|-----------|-------------------|
| [Channel] | [X%] | [why this works] | [how we know it worked] |

**Budget gates verified:** [attribution possible Y/N · test-at-scale rationale · timing check]

---
## DECISION SUMMARY
**Recommendation:** [one sentence — proceed / proceed with conditions / do not proceed]
**Why:** [3–5 reasons, each tied to rubric dimension or framework evidence]
**Why now:** [timing rationale — release window, platform algorithm state, competitive environment]
**Data support:** [what evidence this rests on; source trust tier]
**Assumptions:** [the 2–3 assumptions that, if wrong, would change the recommendation]
**What would change this answer:** [specific observable event that would flip the call]

---
## CONFIDENCE ASSESSMENT
**Level:** [High / Medium / Low]
**Supporting reasons:** [2–3 specific reasons confidence is at this level]
**Risks and unknowns:** [top 2–3 risks; what information would reduce them]
**Weakest-link cap:** [if confidence is reduced by a specific input, name it here]

---
## ALTERNATIVES
**Alternative considered:** [at least one credible alternative campaign strategy]
**If none credible:** "none credible — [reason]"

---
## NEXT BEST ACTION (24–72h)
**Action:** [one concrete step]

---
## COST & ROI
**Estimated campaign budget:** $[X] — [ESTIMATE / OBSERVED — source]
**Budget breakdown:** [by phase or channel, with % allocation]
**Mechanism:** [why this spend level is appropriate — what it buys]
**Expected return range:** $[low]–$[high] — [ESTIMATE — comparable used: {comparable artist/campaign}, confidence: M/L]
**Assumptions behind the range:** [1–3 named assumptions]
**Measurement method:** [how ROI will actually be tracked — UTM, ticket scan, D2C analytics]
**Check-by date:** [date when results will be evaluated]

---
## OPPORTUNITY RANKING
| Opportunity | Impact | Effort | Probability | Priority |
|-------------|--------|--------|-------------|---------|
| [Top opportunity] | H/M/L | H/M/L | H/M/L | 1 |

---
## RISK REGISTER
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| [Top risk] | H/M/L | H/M/L | [specific action] |
```

---

## Template 2 — Weekly Performance Memo

**When to use:** ongoing campaign reporting — weekly output during any active release or brand campaign.

```
# WEEKLY MARKETING MEMO — Week [N] — [Campaign Name] — [Artist] — [YYYY-MM-DD]

---
## WORK PRODUCT

### Campaign Pulse
- **Budget pace:** $[X] spent of $[Y] total ([Z%]) — [on pace / ahead / behind]
- **Primary KPI:** [e.g., pre-saves] — [current: X] vs. [target: Y] vs. [prior week: Z]
- **Channel ranking this week:** 1st [channel] · 2nd [channel] · 3rd [channel]

### Intent Signals
- Saves: [X] (WoW: [+/-Y%])
- Completion rate: [X%] (vs. genre benchmark: [Y%])
- [Platform-specific signal — e.g., pre-add count, Reels completion]: [X]

### Anomalies
- [Any spike or cliff in performance: describe the anomaly and hypothesis for cause]
- [If no anomaly: "No anomalies this week."]

### Creative Performance
| Variant | Metric | vs. Control | Status |
|---------|--------|-------------|--------|
| [Top performing] | [metric + value] | [+X%] | Scale |
| [Kill candidate] | [metric + value] | [-X%] | Kill |

### Next Week Plan
- **Budget reallocation:** [specific change + reason, or "none"]
- **Creative changes:** [variable being tested, or "none"]
- **Key dates:** [editorial window, embargo lift, tour announcement, press drop]

---
## DECISION SUMMARY
**Week assessment:** [one sentence — on track / at risk / pivot needed]
**Why:** [2–3 specific reasons tied to this week's data]
**Key assumption being watched:** [the single assumption most likely to change next week]
**What would change this answer:** [specific signal that would trigger a strategy change]

---
## CONFIDENCE ASSESSMENT
**Level:** [High / Medium / Low]
**Supporting reasons:** [brief — what data supports the assessment]
**Risks this week:** [top 1–2 risks in the next 7 days]

---
## ALTERNATIVES
**Alternative considered:** [at least one credible alternative to this week's strategic call]

---
## NEXT BEST ACTION (24–72h)
**Action:** [one concrete step]
```

---

## Template 3 — Pitch / PR Output

**When to use:** generating a press pitch, DSP editorial submission, or brand partnership approach document.

```
# [PITCH TYPE] — [Artist Name] — [Target: Outlet / DSP / Brand]
Date: [YYYY-MM-DD]   Submitted by: [distributor / direct / PR contact]

---
## WORK PRODUCT

### [For DSP Editorial Pitch — Spotify / Apple Music / TIDAL / Amazon]

**Release:** [Title] — [Genre] — [Release date]
**Pitch window compliance:** submitted [X] days pre-release (minimum: 7 days for Spotify)
**Metadata verified:** ISRC [✓] · UPC [✓] · Genre tag [✓] · Release date [✓] · Distributor QC [✓/pending]

**Editorial pitch (≤500 characters for Spotify):**
> [pitch text — story-forward: mood + context + release story. NOT credentials or chart history.]

**EPK status:**
- Bio (≤200 words): [✓/missing]
- Press photo (≥2400×3600px): [✓/missing]
- Streaming links: [✓/missing]

**Editorial readiness score:** [from scoring-rubric.md dimension 4]
**Hard gate status:** [Editorial Gate — CLEAR or BLOCKED — reason if blocked]

---
### [For Press / Media Pitch]

**Target:** [Journalist name] — [Outlet] — [Beat]
**Personalization:** [specific recent article referenced]
**Lead time required:** [X weeks — verify against campaign phase]

**Subject line:**
> [pitch subject — cultural angle, not music title]

**Pitch body (≤200 words — story-first, accolade-second):**
> [pitch text]

**Timestamp link:** [streaming link + best 30-second timestamp]
**Follow-up rule:** one follow-up after 5 business days; no further contact if no response.

---
### [For Brand Partnership Approach]

**Target brand:** [Brand name] — [Category]
**Brand Partnership Potential score:** [from scoring-rubric.md dimension 7]
**Hard gate status:** [Brand Pitch Gate — CLEAR or BLOCKED]

**Approach document (≤1 page):**

*Artist overview:*
> [one paragraph — audience size, demographic, territory, engagement rate — observable facts only]

*Why this partnership:*
> [mechanism: why this artist and this brand share audience and objective]

*Proposed deliverables:*
> [specific: content format, platform, volume, timeline]

*Audience reach (ESTIMATE — labeled):*
> [projected reach range with stated comparable and confidence level. Never a guarantee.]

*Next step:*
> [specific ask — call, proposal review, introductory deck]

---
## DECISION SUMMARY
**Recommendation:** [pitch / do not pitch / pitch with conditions]
**Why:** [2–3 reasons — tied to readiness score, timing, target fit]
**Why now:** [timing rationale — release window, editorial calendar, brand campaign cycle]
**Assumptions:** [key assumptions behind this pitch recommendation]
**What would change this answer:** [specific event that would change the call]

---
## CONFIDENCE ASSESSMENT
**Level:** [High / Medium / Low]
**Supporting reasons:** [what evidence supports this pitch being viable]
**Risks:** [top 1–2 pitch risks — wrong target, wrong timing, missing asset]
**Weakest-link cap:** [if relevant — name the absent input reducing confidence]

---
## ALTERNATIVES
**Alternative considered:** [at least one credible alternative]

---
## NEXT BEST ACTION (24–72h)
**Action:** [one concrete step]
```
