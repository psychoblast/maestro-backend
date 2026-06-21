# Triage & Routing Protocols

How a classified development reaches the specialists who must act on it, and how the
timing decision (immediate alert vs. regular cycle) is made. Every threshold here is an
encoded default to be tuned on evidence.

---

## 1. Routing Is Additive and Specialist-Specific

A single development may route to several specialists, each with its own "so what?".
Routing is not "tag the closest domain" — it is "name every specialist whose decision
changes, and give each one its own implication."

### Routing Map (by development category)

| Development Category | Primary Specialist(s) | Secondary Specialist(s) |
|----------------------|----------------------|-------------------------|
| Streaming payout / royalty model change | Distribution & platform, Finance & royalties | Marketing, Data & analytics |
| Platform editorial or algorithm policy change | Distribution & platform | Marketing, Data & analytics |
| New platform launch or shutdown | Distribution & platform, Digital operations | Finance & royalties |
| Licensing / copyright / rights-rate change | Publishing & rights, Finance & royalties | Legal & business affairs |
| Major copyright legislation or ruling | Publishing & rights, Legal & business affairs | Finance & royalties |
| Sync-market shift (supervisor budgets, commissioning) | Sync | Marketing |
| Social-platform creator-economy change | Fan & social, Marketing | Digital operations |
| Touring / ticketing / venue structural change | Live & touring | Finance & royalties |
| Signing climate or deal-structure trend | A&R | Legal & business affairs |
| Major label / publisher consolidation | A&R, Executive strategy | Legal & business affairs, Finance & royalties |
| Distribution or metadata standard change | Digital operations | Publishing & rights |
| Chart-methodology change | Data & analytics | Distribution & platform |
| Market-share data (major shift) | Data & analytics | Marketing, Executive strategy |
| Domestic-content / quota legislation (any territory) | Marketing, Distribution & platform | Publishing & rights, Legal & business affairs |
| Capital-market / funding-climate shift | Capital & funding, Executive strategy | Finance & royalties |
| Technology / AI development affecting music | Scope-dependent (see below) | Multiple |

**Technology / AI routing — branch on what the development touches:**

```
AI / technology development received
→ Affects training-data licensing or copyright?  → Publishing & rights + Legal
→ Affects production / generation tools?          → A&R + Production (awareness)
→ Affects platform or distribution policy?        → Distribution & platform + Digital operations
→ Affects marketing / content-creation tools?     → Marketing + Fan & social
→ Affects royalty collection or calculation?      → Finance & royalties + Publishing & rights
→ Spans several of the above?                     → route to all, each with its own framing
```

---

## 2. Territory Overlay

Territory tags combine with category routing. A platform change tagged for one
territory routes to the distribution specialist with that territory's framing; a
development spanning a region and the global market routes with both implications
stated. The general rule for domestic-content/quota legislation supersedes any
narrower territory-specific routing: quotas shape catalog, promotion, and platform
access simultaneously, so they always reach marketing and the distribution specialist
together. Territory market structures are detailed in [[territory-intelligence]].

---

## 3. Timing — Immediate Alert vs. Regular Cycle

The timing decision is among the most consequential in the domain. Alert fatigue is
real: a specialist who is alerted on non-urgent items loses faith faster than one who
occasionally waits a day on a genuinely urgent item.

```
Item has passed consequence classification
→ Rule-changer or strategy-invalidator?
    → Yes: alert pathway
        → Primary source confirmed?                    → alert immediately
        → Two independent strong-trade sources?        → alert immediately
        → One strong-trade source only?                → hold 24–48h for a second; else demote to cycle
        → Useful-signal only?                          → regular cycle, framed as unconfirmed
    → No: regular-cycle pathway
        → Opportunity-creator: cycle, "opportunity" framing, led in its section
        → Contextual-update:   cycle, standard entry
        → Monitoring signal:   cycle, monitoring section, minimum detail
```

**What an alert is NOT:**
- Not "a major news item in music" — it is a development that invalidates an active
  strategy or changes a rule.
- A platform's strong quarterly earnings is not an alert (contextual at most).
- A prominent figure's death is not an alert unless it has direct operational
  consequences (tour cancellations, catalog-licensing changes, estate implications for
  active deals).
- A major release is not an alert unless the release itself changes an industry
  pattern.

**Alert-fatigue anti-pattern:** alerting on opportunity-grade items because "they could
be important." The alert channel's value is its selectivity. When in doubt, use the
regular cycle.

---

## 4. The Decision-Change Test as a Publication Gate (Framework: "DCT")

Every entry passes the DCT before publication. It is the gate, not a sanity check.

- **Step 1 — Name the specialist** the entry routes to.
- **Step 2 — State the decision** that specialist should change: "Because of this,
  [specialist] should now [do / stop / modify] [named action]." The statement must be
  specialist-specific, action-specific (not "should monitor" — *what* monitoring
  action), and falsifiable (an auditor could check whether behavior changed).
- **Step 3 — State the practice implication** in one or two concrete sentences.

| Symptom | Diagnosis | Remedy |
|---------|-----------|--------|
| "Specialists should be aware of this" | No action named — DCT fails | Drop, or name the specific action |
| "This could affect [specialist] in future" | Speculative, not a current change | Classify as monitoring with a re-check date |
| "This is big news in the industry" | Headline excitement, not impact | Reapply Filter 2; drop if no action can be named |
| "All specialists should know this" | No routing specificity | Route to specific specialists; if truly cross-domain, write separate entries |

---

## 5. Competing-Development Prioritization

Multiple trigger-grade developments can arrive in one cycle. Default priority:

| Priority | Condition | Action |
|----------|-----------|--------|
| P1 | Affects an active campaign or deal currently in progress | Alert first, within hours |
| P2 | Affects planned activity within ~90 days | Alert same day |
| P3 | Affects general direction but no active work | Alert within 24h; may batch |

**Batching rule:** several P3 alerts from one cycle may be batched into a single dated
alert. Each item still gets its full entry; batching is a notification-management
decision, not an editorial one.

---

## 6. Routing Confidence

- **One specialist** when there is a clear primary and secondary implications are not
  decision-changing for anyone else right now.
- **Multiple specialists** when each has an independent, decision-relevant "so what?"
  — each gets its own entry. Routing several specialists to one generic entry is a
  routing failure.
- On trigger-grade items, log the routing judgment as a falsifiable prediction:
  "Routed [development] to [specialists]. Falsified if they do not report this as
  decision-relevant within [timeframe]." Lower-consequence routing is not
  prediction-logged — the signal value does not justify the overhead.

---

## 7. Quiet-Cycle Protocol

A scan that finds nothing trigger-grade is a successful scan. The quiet-cycle report
includes: scan date; sources covered by tier count; items collected at triage entry;
items dropped at each filter (count only); any lower-consequence items published; and
an explicit line — "No trigger-grade developments in [territory list] this cycle."

**Anti-pattern:** manufacturing significance when the scan is quiet. A filler item
erodes trust faster than an honest quiet report.

---

## 8. NOT EVALUABLE Protocol

Apply when there is insufficient primary/strong-trade signal to assess a territory's
state or a development's significance:
- no primary/strong-trade coverage exists; or
- contradictory strong-trade sources with no primary resolution; or
- the development is too early-stage to classify (under ~48h, single source).

Format:
```
[Territory / development] — NOT EVALUABLE this cycle
Reason: [insufficient primary/strong-trade data / contradictory sources / too early]
Sources checked: [list]
Resolution trigger: [what would make this evaluable]
Monitoring flag: [specific source / date window]
```

**NOT EVALUABLE is not a failure.** It preserves the system's trust. A fabricated
assessment of an underdeveloped item is the failure; an explicit NOT EVALUABLE is the
correct response.
