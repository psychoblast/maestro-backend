# Decision-Change Methodology

The core scan methodology: how a raw candidate item becomes (or fails to become) a
published intelligence entry. Every threshold here is an encoded default — a starting
position to be tuned on evidence, not an immutable law.

> Standard for every framework below: named framework · quantified claim with a
> source tier · decision-branching logic · domain anti-pattern · practitioner-layer
> insight.

---

## 1. The Unit of Intelligence (Framework: "Decision-Change Test")

Intelligence is measured in changed decisions, not events. An item enters the system
only if it can complete:

> "Because of this, [a named specialist] should now [do / stop / modify]
> [a specific action]."

Three tiers of decision change:

| Change Tier | Definition | Illustration |
|-------------|-----------|--------------|
| **Structural** | Changes the rules of the game — invalidates an active framework or strategy | A streaming platform changes its royalty model; a collection society merges with a competitor |
| **Cyclical** | Changes the current recommendation while leaving the framework intact | Streaming growth slows in one territory this quarter |
| **Noise** | No decision changes for anyone | A single act's chart position; an earnings call with no operational implication |

Classify before triage. Structural items move toward an immediate alert. Cyclical
items enter the regular cycle. Noise is dropped silently — not logged, not explained.

---

## 2. Signal vs. Noise (Framework: "Four-Filter Method")

Each candidate passes four sequential filters. A "no" before filter 4 drops the item.

**Filter 1 — Source reality check.** Is the claim supported by a primary or strong-
trade source, or is it a weaker claim requiring escalation?
- Primary / strong trade: proceed.
- Useful-signal tier with primary/strong-trade corroboration: proceed.
- Rumor tier alone: proceed only if structurally significant enough to flag as rumor;
  otherwise drop.

**Filter 2 — Decision impact.** Name the decision it changes for at least one
specialist. Cannot name one → drop. *Anti-pattern:* "this is interesting" is not a
decision. The question is "interesting to whom, and what should they do differently?"

**Filter 3 — Durability.** Durable development or temporary noise?
- Durable: rule changes, market-structure shifts, policy changes, confirmed mergers
  or acquisitions.
- Noise: short-lived chart fluctuation, act-specific publicity, an earnings beat or
  miss without operational implication, an isolated micro-trend with no structural
  cause.
- Edge case: a single-territory micro-trend that is a leading indicator of a
  structural shift → assign a provisional useful-signal tier and flag for monitoring.

**Filter 4 — Routing clarity.** Is there at least one named specialist to route to
with a specific action? None → drop.

An item surviving all four filters receives a consequence classification (see
[[consequential-development-matrix]]). Items failing any filter are dropped silently.

---

## 3. Editorial Judgment Protocols

### 3.1 The "So What?" Enforcement Protocol

Before writing any entry, the specialist must be able to complete this template. If it
cannot, the item is dropped:

```
"Because [development] happened (source: [name], Tier [A/B/C/D]),
 [named specialist] should now [specific action] —
 specifically: [concrete implication at practitioner level]."
```

Entries that can only produce a generic "so what" ("specialists should monitor this")
are dropped. The implication must be specialist-specific and concrete.

### 3.2 Source Triangulation Protocol

When a development is high-consequence and the initial source is strong-trade or
below:
1. Run a second-source check against at least one other strong-trade or one primary
   source.
2. Corroborated → proceed, stronger source cited first, secondary noted.
3. Contradicted → apply the contradictory-source protocol in
   [[source-trust-and-assessment]].
4. Uncorroborated after search → downgrade the consequence class, flag explicitly, do
   not trigger an alert.

### 3.3 Recency Weighting Protocol

Intelligence has an expiration gradient. These are default half-lives, not guarantees:

| Claim type | Meaningful-change horizon | Treatment past horizon |
|------------|---------------------------|------------------------|
| Platform algorithm / editorial policy | ~90 days | Context only |
| Rights / royalty rate changes | One regulatory cycle (~1–5 years) | Remains valid |
| Market-share / streaming-volume data | ~6 months | Stale without refresh |
| Legislation / legal rulings | Until superseded | Remains valid until overturned |

Items past their threshold may be cited as context but not as current intelligence,
and are tagged with the original date plus "STALE — monitor for update."

---

## 4. The Three Practitioner Failure Modes

### Failure Mode 1 — Too Much Noise ("Completeness Trap")
Including everything because exclusion feels like missing something. Consequence:
specialists learn to skim, alert fatigue sets in, and the feed loses credibility.
**Discipline:** a weekly scan of a major territory that yields 25 items is almost
certainly miscalibrated; a well-triaged scan yields roughly 5–12, fewer on quiet
weeks. Report quiet weeks explicitly. *Practitioner insight:* the instinct toward
over-inclusion is near-universal among new analysts; the discipline of under-inclusion
takes months to internalize.

### Failure Mode 2 — Too Little Signal ("Conservative Overcorrection")
Setting thresholds so high that strong-trade developments are routinely dropped while
waiting for primary confirmation that may arrive weeks later. Consequence: the early-
warning value is lost; by the time items are "confirmed enough," the window has
closed. **Balance rule:** two independent strong-trade sources proceed as provisional
fact, labeled as such. The wait-for-primary discipline applies to trigger-grade items,
not to lower-consequence items where strong-trade sourcing is sufficient.

### Failure Mode 3 — Wrong Routing ("Routing Approximation")
Routing to one specialist when the correct route is two, because the item spans
domains. Consequence: a specialist misses relevant intelligence and routing
credibility erodes. **Discipline:** routing is a falsifiable prediction; log it on
high-consequence items and check on the review cycle whether the routed specialist
acted and whether any unrouted specialist needed it. Both are tuning signals.

---

## 5. Worked Distinctions (Decision Tree)

```
Candidate item received
→ Filter 1: source tier confirmed?
    → No (rumor alone, not structural): DROP silently
    → Yes: continue
→ Filter 2: can you name the decision it changes?
    → No: DROP silently
    → Yes: continue
→ Filter 3: durable or noise?
    → Noise: DROP silently
    → Durable: continue
→ Filter 4: at least one specialist to route to?
    → No: DROP silently
    → Yes: classify consequence level (see consequential-development-matrix)
→ Rule-changer / strategy-invalidator: immediate-alert pathway
    → Primary confirmed? → alert immediately
    → Not primary: second-source check → corroborated → alert → else downgrade
→ Lower consequence: regular-cycle pathway → write entry → route to tagged specialists
```
