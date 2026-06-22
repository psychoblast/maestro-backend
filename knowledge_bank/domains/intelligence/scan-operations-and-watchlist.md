# Scan Operations & Watchlist Mechanics

The frameworks that follow govern HOW to run a scan — the operational layer beneath
the editorial principles in [[intelligence-doctrine]], [[decision-change-methodology]],
and [[triage-and-routing]]. Good doctrine without an operating rhythm produces
inconsistent output; a watch list without editorial discipline produces noise. Both
are required.

---

## 1. The Three-Tier Scan Cadence

Not every source warrants daily attention. The cadence tier determines monitoring
frequency; elevation between tiers is triggered by a watch-list flag.

| Tier | Frequency | Purpose | Typical sources |
|------|-----------|---------|-----------------|
| **Signal check** | Daily (~15 min) | Catch rule-change events before they age | Alert feeds from Tier A sources; regulatory agency update pages; platform policy announcement channels |
| **Structured scan** | Weekly (~2–3 h) | Full Four-Filter pass on a defined source list | Complete Tier A–B watch list, including rights bodies, chart authorities, trade publications |
| **Deep scan** | Monthly (~4–6 h) | Emerging-market coverage; source-list audit; watch-list review | Tier C sources; territory-specialist outlets; developing-story resolution review |

**Cadence discipline:** daily signal checks look only at alert-grade events —
confirmed rule-changes and strategy-invalidators. They do not replace the structured
scan. A scan cycle that catches a rule-change on day 5 instead of day 1 because the
signal check was skipped has failed the function of the cadence.

**Calibration signal:** if the structured scan consistently runs over three hours,
the source list has grown too large or the classification discipline has drifted.
Either audit the watch list for sources that yield zero CDM-1/2 items in six months
or review why classification is consuming excessive time.

---

## 2. Source Watch List Structure

The watch list is a living document, not a static catalog. Each entry carries:

| Field | Content | Notes |
|-------|---------|-------|
| Source name | Name as the source presents itself | |
| Tier | A / B / C / D (per STAR Protocol) | Provisional flag if assigned within 6 weeks |
| Tier assigned date | YYYY-MM | Triggers automatic review at 6 weeks |
| Cadence tier | Daily / Weekly / Monthly | Driven by source's history of CDM-1/2 items |
| Coverage focus | Territory, category, or domain this source leads on | |
| Last reviewed | YYYY-MM-DD of most recent check | Flag if outside cadence window |
| Source-specific notes | Access method, paywall status, filing schedule | |

**Cadence elevation rule:** if a Tier B or C source yields two or more CDM-1 or CDM-2
items in a rolling three-month window, elevate its cadence tier by one level. Elevation
is logged with reason and date.

**Cadence demotion rule:** if a source in the daily or weekly tier yields no items
above CDM-4 in six consecutive months, demote one tier. Demotion is logged; reinstate
on first CDM-1/2 hit.

**Anti-pattern:** adding sources because they are prominent rather than because they
have a history of primary-tier or CDM-relevant output. Source list bloat is one of the
two most common causes of scan-time overruns. Apply the STAR Protocol to every
proposed addition and require it to meet the tier floor before adding it to the
watch list.

---

## 3. Open-Item and Developing-Story Tracking

Not all developments resolve in one scan cycle. A developing story is an item that has
entered the system but not yet reached a final status. The open-item log is maintained
separately from the published intelligence feed.

### 3.1 Open-Item Status Field

Every open item carries exactly one of four statuses:

| Status | Meaning | Trigger for next action |
|--------|---------|-------------------------|
| **DEVELOPING** | Confirmed as potentially significant; not yet at classification source floor | Re-check trigger event, or 30-day maximum elapsed |
| **CONFIRMED** | Source floor cleared; classified and routed; watching for updates | Material factual change or rule update |
| **NOT EVALUABLE** | Insufficient primary/strong-trade coverage to assess | Named source publishes, or 60-day maximum elapsed |
| **CLOSED** | Resolved: shipped, dropped on re-evaluation, or superseded | — |

**Anti-pattern:** leaving items in DEVELOPING status indefinitely. A DEVELOPING item
older than 30 days without a re-check trigger must be reviewed at the next structured
scan: either escalate to CONFIRMED, demote to NOT EVALUABLE, or close with a reason.

### 3.2 Developing-Story Log Format

```
ITEM ID: [YYYYMMDD-NNN]
Status: [DEVELOPING / CONFIRMED / NOT EVALUABLE / CLOSED]
Development summary: [one sentence — the claim]
Current best source: [name, Tier, date]
Consequence class (provisional): [CDM-1 through CDM-5 / NOT CLASSIFIED]
Re-check trigger: [specific event — named source filing, platform announcement, decision date]
Opened: [YYYY-MM-DD]
Last reviewed: [YYYY-MM-DD]
Closed: [YYYY-MM-DD and reason, if closed]
```

---

## 4. Standard Weekly Scan Workflow

A structured, step-by-step procedure for the weekly scan. Deviating from step order
introduces the most common failure mode: classifying consequence before sourcing is
confirmed.

**Step 1 — Source coverage check (10 min)**
Pull updates from all weekly-cadence sources. Note any that have not updated since the
last cycle — coverage gaps are reportable. Flag sources that appear to have reduced
their publication frequency for STAR Protocol re-review.

**Step 2 — Triage pass — Filter 1 only (30 min)**
For each item encountered: does it have a primary or strong-trade source? If yes, carry
forward. If useful-signal only, carry forward with a provisional flag. If rumor only,
apply the rumor handling protocol from [[source-trust-and-assessment]]. At this stage,
do NOT classify consequence — sourcing must be confirmed first.

**Step 3 — Filter 2 and 3 (20 min)**
For each Filter-1 survivor: name the decision it changes and determine whether it is
durable. Items failing either filter are dropped silently. Items surviving both are
carried to classification.

**Step 4 — Classification (20 min)**
Apply the CDM matrix from [[consequential-development-matrix]] to each survivor.
Assign CDM-1 through CDM-5. CDM-1/2 items trigger the timing protocol; check the
alert-timing decision tree in [[triage-and-routing]] before proceeding.

**Step 5 — Open-item review (15 min)**
Review every DEVELOPING and NOT EVALUABLE item in the open-item log. Has the re-check
trigger been met? Are any items past their 30- or 60-day review deadline? Update
statuses; close items that have resolved.

**Step 6 — Entry drafting and routing (30 min)**
Write entries for Filter-4 survivors. Apply the standard entry format from
[[output-templates-and-handoffs]]. Assign routing per the routing map. For trigger-grade
items, fire alerts per the timing protocol. For quiet scans, produce the quiet-cycle
report.

**Step 7 — Scan log update (5 min)**
Complete the scan log entry. Total time should be 90–120 min for a full cycle; scans
running over 3 hours indicate source list bloat or classification discipline problems.

---

## 5. Scan Log Format

The scan log creates an auditable history of every cycle — not just what shipped but
what was seen and why it was dropped. One entry per cycle.

```
SCAN LOG — [YYYY-MM-DD]
Cadence: [weekly / monthly / signal-check]
Sources checked: Tier A [n] · Tier B [n] · Tier C [n]
Items at triage entry: [n]
Filter 1 drops: [n]   Filter 2 drops: [n]   Filter 3 drops: [n]   Filter 4 drops: [n]
Items classified: CDM-1 [n] · CDM-2 [n] · CDM-3 [n] · CDM-4 [n] · CDM-5 [n]
Alerts triggered: [n]
Regular-cycle entries published: [n]
Open items reviewed: [n]   Status changes: [list of item IDs and new status]
New watch-list additions: [n]
Scan duration: [h:mm]
Notes: [structural observations — source went dark, cadence adjustment, territory gap]
```

**Anti-pattern:** scan logs that record only what shipped. A log without drop counts
cannot support quality audits or calibration. An analyst who cannot point to how many
items they dropped and at which filter cannot demonstrate that the Four-Filter Method
is being applied.

---

## 6. Closing a Developing Story

Three legitimate close conditions:

1. **Published** — the item reached the required source floor, was classified, and
   shipped as an entry or alert. Close with the published entry reference.
2. **Dropped on re-evaluation** — on re-check, the item fails a filter that it
   provisionally passed, or new sourcing contradicts the initial reading. Close with
   the reason and the contradicting source.
3. **Superseded** — a larger or more recent development covers the same ground; this
   item adds nothing incremental. Close with a reference to the superseding item.

**Never close an item simply because it aged.** A development that remains
unconfirmed after 60 days transitions to NOT EVALUABLE with a named re-check trigger —
it does not close unless the development itself has been demonstrably overtaken.
Aging without resolution is a data point about source coverage, not a reason to drop
the underlying claim.

---

## 7. Watch-List Audit Protocol (Monthly)

The monthly deep scan includes a full watch-list audit:

1. **Zero-yield sources:** sources that produced no CDM-1/2/3 items in the prior three
   months. Flag for cadence demotion or removal from the watch list.
2. **Stale provisional tiers:** sources assigned a provisional tier more than six weeks
   ago that have not been reviewed. Complete the STAR Protocol re-assessment and confirm
   or revise the tier.
3. **Territory coverage gaps:** territories for which no Tier A or B source is on the
   watch list. Flag as a structural gap; evaluate whether a NOT EVALUABLE declaration
   is warranted for that territory going forward.
4. **Developing-story age review:** all DEVELOPING and NOT EVALUABLE items older than
   30 days. Resolve or formally extend with a documented re-check trigger.

The output of the monthly audit is a brief watch-list health note appended to the
monthly deep-scan log: sources added, sources removed, tier changes, and territory
gaps identified.
