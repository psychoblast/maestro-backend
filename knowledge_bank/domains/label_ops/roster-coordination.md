# Artist Roster Coordination

A label is a coordination machine. A release that lands in the market with full
operational support is the product of at least five internal functions operating
in sequence and in parallel. Failures in the handoff between functions are the
primary cause of operational release failures.

## The Five Core Functions and Their Handoffs

| Department | Primary responsibility | Key output for ops |
|------------|------------------------|--------------------|
| A&R | Signing, creative direction, collaborator selection, delivery oversight | Approved masters; session notes; producer agreements; creative brief |
| Marketing | Campaign strategy, content, social, PR, radio, DSP editorial relationships | Campaign plan; content schedule; editorial pitch filed; pre-save live |
| Legal / Business Affairs | Contract negotiation, clearance sign-off, splits documentation | Executed agreement; confirmed sample clearances; confirmed splits |
| Finance | Advance processing, royalty accounting, P&L tracking, reconciliation | Advance paid; royalty config confirmed; budget approved |
| Operations | Distribution, metadata, ISRC/UPC, DSP delivery, QC, release tracking | Release live at all DSPs; metadata validated; identifiers registered |

**The standard handoff sequence:**
```
A&R signs → Legal executes deal → Finance processes advance
  → A&R delivers approved master to Ops → Ops runs audio + metadata QC
  → Legal confirms sample clearances → Ops registers ISRC/UPC
  → A&R briefs Marketing → Marketing builds campaign plan
  → Ops delivers to distributor → Marketing files editorial pitch
  → Delivery confirmed → Pre-save live → Release day
```

**Where handoffs fail:** the most common failure is the A&R-to-Ops handoff — a
master delivered without sample clearance, with incorrect producer credits, or
without confirmed publishing splits, which Ops cannot act on, compressing the
campaign. The second most common is the Legal-to-Ops handoff: sample clearances
verbally confirmed by A&R but not legally executed, with Ops proceeding on the
verbal confirmation and the uncleared sample becoming a post-release problem.

## Project Kickoff Protocol

The kickoff is when a release transitions from A&R decision to operational
execution. Required before a release date is set:

| Item | Owner | Required before date is set? |
|------|-------|------------------------------|
| Artist name confirmed (as it appears on DSPs) | A&R / Legal | YES |
| Recording agreement executed | Legal | YES |
| Master delivered and approved by A&R | A&R | YES — no date on undelivered recordings |
| Publishing splits confirmed and documented | Legal / A&R | YES |
| Sample clearances confirmed (if samples present) | Legal | YES — verbal "it's cleared" is insufficient |
| Producer agreements executed or in final draft | Legal | YES |
| Distribution partner confirmed | Ops | YES |
| Release type confirmed | A&R | YES — determines campaign arc |
| Release format confirmed (streaming / + physical) | A&R / Ops | YES — physical needs separate lead time |
| Marketing budget approved | Finance | YES |
| Internal project lead assigned | Ops | YES |

```
IF all items confirmed:
  → set the release date working backward from operational lead time
  → Single: minimum 6 weeks from master delivery; 8 preferred
  → Album: minimum 10 weeks from master delivery; 12–16 preferred
IF any item unconfirmed:
  → do NOT set the release date; flag the item to the department lead;
    document the flag; set a 48-hour resolution deadline; date-setting is blocked
```

## Release Readiness Gates

Readiness is a formal state — ready or not. "Almost ready" is "not ready."

**Gate 1 — Legal (PASS before ops proceeds):** recording agreement fully executed;
all samples cleared with executed licenses; publishing splits documented with all
co-writers/publishers; producer agreements executed or at minimum a term sheet
with the royalty confirmed; co-publishing/admin agreements confirmed where
applicable.

**Gate 2 — Creative (PASS before delivery begins):** final approved master
delivered; artwork to spec (3000×3000px, JPEG/PNG, sRGB); track listing finalized
(no further additions or resequencing); ISRC assigned per track.

**Gate 3 — Marketing (PASS before the date is announced publicly):** documented and
approved campaign plan; approved and allocated marketing budget; editorial pitch
drafted, reviewed, ready to file at delivery confirmation; pre-save decision made
(and link ready if running); PR/press strategy decided.

**Gate 4 — Operational (final gate before going live):** distribution delivery
confirmed and visible on DSP dashboards; all DSPs live and streamable;
final-metadata audit complete with all fields correct; release date confirmed and
communicated to all parties; post-release monitoring assigned to a named person.

## Artist Communication Frameworks

What the label tells the artist, when, and what it deliberately does not say —
one of the highest-sensitivity areas in artist-label relations.

| Phase | What the artist is told | What the artist is NOT told |
|-------|-------------------------|------------------------------|
| Kickoff | Release plan, timeline, deliverables, marketing ask | Internal budget breakdown; per-channel spend; pitch status |
| Delivery week | Delivery confirmed; DSP-live timeline; pre-save link | Distribution fee structure; internal resource allocation |
| Pre-release | Content calendar; first-48h protocol; confirmed coverage | Editorial-consideration status (editors do not confirm in advance) |
| Release week | Live confirmation; real-time dashboard access | Internal algorithmic signal assessment (creates anxiety w/o context) |
| Post-release | Week-1 streams and playlist adds; next steps | Pitch-decline reasons (rarely known; speculation harms relationships) |

**Protocol for "not ready for editorial":**
```
IF A&R or artist says a track "isn't ready for editorial":
  → ALWAYS pitch regardless; the pitch costs nothing and filing beats skipping
  → do NOT communicate "we're pitching" as a commitment to placement
  → do NOT communicate "we didn't pitch" — it is an operational, not artist, decision
  → if asked directly: "We filed a pitch as part of standard process"
```

**Communication anti-patterns:** telling the artist streaming targets ("we need
50K in week one") drives counterproductive fan-mobilization that can trigger DSP
fraud detection; sharing speculative editorial-decline reasons damages the
label-DSP relationship and artist confidence; overpromising playlist adds or
features before they are confirmed is the single most common cause of post-release
trust breakdown.

## Roster Management Across Concurrent Releases

The same distribution relationship, marketing budget, editorial relationships, and
ops capacity are shared across the roster. The priority stack:

```
Tier 1 — FLAGSHIP: highest-revenue / largest-investment artist this cycle
  → primary ops attention, first editorial-pitch priority, primary budget
  → risk: over-concentration under-serves the rest of the roster
Tier 2 — DEVELOPMENT: high-growth artist, not yet the revenue leader
  → consistent execution; proportional budget; full editorial filing
  → risk: most often under-resourced when flagship demands spike
Tier 3 — CATALOG / MAINTENANCE: active catalog, no major release planned
  → catalog management, rights hygiene, re-release evaluation; minimal campaign cost
  → risk: steady-revenue catalog deprioritized into an unmanaged state
Tier 4 — NEW / EMERGING: freshly signed; first release
  → full operational checklist; modest budget; educational communication cadence
  → risk: needs the most hand-holding, receives the least from a stretched team
```

```
IF two Tier-2 artists have simultaneous deadlines:
  → stagger releases by ≥2 weeks if possible; if not, assign a dedicated ops lead each
IF a Tier-1 and a Tier-2 release compete for the same editorial contact:
  → Tier 1 takes the primary contact; Tier 2 uses a secondary contact or alternative
    timing; document the trade-off and flag it to the label head
IF budget is insufficient for concurrent full campaigns:
  → escalate to the label head and Finance; never silently compress either campaign
```

## Crisis Communication

**Recoverable crises** (resolved without moving the date): artwork rejected
(24–48h correction); metadata error caught pre-release (correct via distributor;
3–5 business days; may shift the date); broken pre-save link (hours); editorial
pitch missed for the optimal window (file anyway — a late pitch still reads).

**Non-recoverable crises** (the date moves or the release proceeds sub-optimally):
uncleared sample discovered after delivery (pull, clear or remove, re-deliver);
rights dispute or injunction filed pre-release (escalate to legal immediately;
release cannot proceed); DSP content-policy removal (pull, revise, re-deliver; 5–10
business-day minimum delay).

```
Step 1 — Assess: recoverable without moving the date?
  YES → resolve internally; update status
  NO  → notify the label head and the artist's manager immediately (not the artist)
        with specific facts, a specific timeline, and specific options; never
        present uncertainty as certainty or estimate faster than is realistic
Step 2 — If the date moves: tell the manager first; give them ~30 minutes with the
  artist before following up; be specific about the new date and the cause; do not
  assign blame to a named team member, the artist, the distributor, or the DSP
  unless truly attributable and verifiable
Step 3 — Document the root cause, the prevention measure and its owner, and confirm
  follow-up with the label head
```

## Internal Approval Chains

| Decision | Who approves |
|----------|--------------|
| Release date confirmed | Label head + Ops lead |
| Marketing budget approved | Label head + Finance |
| Campaign plan approved | Label head + Marketing lead |
| Distribution partner selection | Label head + Ops lead |
| Release delayed | Label head (mandatory); Finance if budget impact; manager notified |
| Advance paid | Finance + Label head |
| Deal terms (new or renegotiated) | Legal + Label head; artist attorney on artist side |
| Sample clearance decision | Legal + A&R + Label head |
| Sync license (incoming offer) | Legal + Label head; A&R if creative fit matters |

**Anti-pattern: ops unilaterally moving release dates.** Even in an obvious
crisis, the label head must be informed and approve. Artists and managers hold
contractual and relationship expectations around release dates; unilateral ops
decisions without leadership sign-off create liability.

## A&R-to-Ops Handoff Failure Modes

1. **The "master is ready" misunderstanding.** A&R marks an approved rough mix as
   "delivered"; Ops sends an unmastered file; rejection returns in 48–72h.
   Prevention: Ops receives the explicitly mastered final and confirms the spec
   before logging "received."
2. **Verbal sample clearance.** A&R says "the sample is cleared; legal is handling
   it"; weeks after release the owner files a takedown. Prevention: legal confirms
   clearance in writing before any sampled release enters delivery.
3. **Publishing splits "to be confirmed."** Splits "being worked out"; Ops delivers
   without complete data; mechanicals cannot be configured; royalties accrue
   unmatched from release day. Prevention: splits are a Gate-1 hard stop.
4. **Artist-name variant on DSPs.** A corrected name format does not link to the
   existing verified page, splitting the artist's streaming history. Prevention:
   Ops searches all major DSPs and confirms the exact name format matching the
   existing verified page before delivery.

## Practitioner-Layer Insight

- **Management is always the proxy for difficult news.** The label delivers hard
  information (date moves, weak performance, budget changes) to the manager, not the
  artist directly; the manager contextualizes it in the way that best serves the
  relationship. Bypassing management — even with good intentions — damages the
  relationship and usually produces a worse artist experience.
- **The "Friday default" damages calendar planning.** Teams that plan backward from
  the next available Friday compress the timeline when Fridays fall awkwardly. The
  correct posture: identify the target 8–10-week ops window, find the Friday within
  it, and work backward from that Friday.
- **End-of-cycle A&R revisions create ops whiplash.** A revision (new ad-lib,
  different mix, last-minute track) after delivery begins triggers a re-delivery
  cycle of 3–5 business days; one revision at week -4 can cause editorial-pitch
  failure. The A&R approval at the point of delivery must be final — "final, except
  for…" does not exist.

See also: [[release-planning-and-workflow]],
[[label-ops-judgment-and-triage]], [[label-operations-doctrine]].
