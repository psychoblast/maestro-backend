# Source Trust & Assessment

A claim's weight comes from its sourcing, never from its appeal. This file defines the
trust-tier system, how to assign a tier to a new source, how tiers degrade, how to
resolve contradictory sources, and the anti-fabrication rules that gate every
quantified claim.

---

## 1. The Source Trust Tier System

| Tier | Label | Meaning |
|------|-------|---------|
| **A** | High Trust — Primary | Official platform announcements; regulatory filings; rights-body published rate schedules; industry-body data reports; government legislation text |
| **B** | Strong Trade | Established industry trades with editorial standards, named editors, and a correction record |
| **C** | Useful Signal | Specialist blogs, niche newsletters, and territory-specialist outlets with partial standards |
| **D** | Rumor | Forums, social posts, unattributed "sources familiar with the matter," anonymous claims without corroboration |

The tiers are not a ranking of how *interesting* a source is — they encode how much
weight a claim from that source can bear before it must be corroborated.

---

## 2. Assigning a Tier to a New Source (Framework: "STAR Protocol")

Use when a source is encountered that is not already on the standing source list. Four
criteria, each scored 0–2 (2 = strong, 1 = partial, 0 = absent).

**S — Standards.** Published editorial standards, named editors, a documented
correction process?
- 2: formal standards, named editors, documented corrections.
- 1: named editor(s), informal standards, corrections without formal process.
- 0: anonymous, no named editors, corrections absent or undisclosed.

**T — Track Record.** Has the source proven accurate over time?
- 2: documented accuracy history; stories regularly confirmed by primary sources;
  rare, corrected errors.
- 1: mixed record; some accurate scoops; inconsistent correction culture.
- 0: frequent errors, rumor published as fact, no verification observable.

**A — Authority.** Does it have access to primary sources?
- 2: documented primary relationships; on-record quoted sources.
- 1: some primary access; occasional anonymous sourcing; mostly secondary synthesis.
- 0: no primary access evident; aggregates and rewrites other outlets.

**R — Relevance.** Does it cover the music industry specifically?
- 2: music-industry focus with dedicated beat reporters.
- 1: entertainment focus with regular but non-primary music coverage.
- 0: general media; music coverage incidental.

**Score → tier:**
- 7–8 → Tier B (strong trade)
- 5–6 → Tier C (useful signal)
- 3–4 → Tier C (weak — flag for monitoring; do not use as a primary source)
- 0–2 → Tier D (rumor class)

**New-source procedure:** assign a *provisional* tier, record it as provisional with
the date assigned, and review after roughly six weeks of active monitoring. Tier
changes are logged with date and reason — no silent changes.

**Anti-pattern:** assigning Tier B because a source is well-known rather than because
it meets the standards criteria. Fame is not authority.

---

## 3. Tier Degradation & Recency

A tier is not permanent. A strong-trade source that publishes an uncorrected major
error degrades until its correction culture is re-established. A primary data report
ages: see the recency gradient in [[decision-change-methodology]]. The principle: a
high tier is earned continuously, not granted once.

---

## 4. Rumor (Tier D) Handling Protocol

```
Is the rumor structurally significant enough to warrant a flag?
→ No (routine gossip, single-act personal news): DROP silently
→ Yes (e.g., a major platform-policy or consolidation rumor affecting active work):
    → Seek Tier A–C confirmation before writing the entry as fact
    → No confirmation found → enter ONLY as a flagged rumor:
        "RUMOR (Tier D — unconfirmed): [claim]. Source context: [context].
         Monitor for Tier A–C confirmation. DO NOT act on this as fact."
    → Do NOT state an expected confirmation timeline unless a specific filing or
      reporting date is known
    → Do NOT extrapolate implications from an unconfirmed rumor
```

**Anti-pattern:** "this rumor is too significant to ignore, so we'll report it with
mild hedging." Mild hedging of a rumor presents it as near-fact. The correct treatment
is explicit rumor labeling or silence.

---

## 5. Contradictory-Source Resolution Protocol

When two strong-trade sources report contradictory factual claims:

**Step 1 — Check for a definitional contradiction.** Different time windows,
measurement methods, or scope definitions often produce apparent contradictions. If
definitional, report both with scope qualification — there is no real contradiction.

**Step 2 — Seek a primary resolution.** If a primary source resolves it, cite the
primary source and note the conflicting strong-trade reports.

**Step 3 — No primary available.** Report the contradiction explicitly:

> "Contradictory reports: [Source A, Tier B] reports [X]; [Source B, Tier B] reports
> [Y]. No Tier A resolution available. Both noted. Confidence: low. Reclassified to a
> monitoring item pending resolution."

**Anti-pattern:** averaging two contradictory claims or picking the more interesting
one. A midpoint between two possibly-wrong claims is fabrication.

---

## 6. Anti-Fabrication Rules

This domain's fabrication risk is *temporal* — treating a stale claim as current —
more than structural. No market-size, market-share, streaming-volume, royalty-rate, or
growth-rate claim enters an entry without:

- a named primary or strong-trade source, **and**
- a date (year at minimum) the data was published.

Specific rules:

1. "The market leader is X" requires the year the measurement was taken — positions
   change.
2. Regulatory-status claims require the legislative basis and effective date —
   regulations change.
3. Rights / royalty-rate claims require the current contractual period — rates
   renegotiate.
4. If current data is unavailable from a primary or strong-trade source, state "NOT
   CURRENT DATA AVAILABLE" and cite the most recent dated figure as historical context
   only.

**Fabricated currency is worse than admitted ignorance.** Aging a claim by a year —
citing older data this year without flagging it as historical — is temporal
fabrication. Label stale data explicitly or do not use it.
