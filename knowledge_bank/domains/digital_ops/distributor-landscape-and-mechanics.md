# Distributor Landscape & Mechanics

## Currency Warning

Distributor pricing, platform coverage, feature sets, and payout structures change
frequently. All specifics in this file are illustrative reference points, not current
facts. Verify directly with each distributor before advising on distributor selection
or catalog transfer.

## 1. Distributor Model Taxonomy

Digital distributors operate under five distinct commercial models. Understanding the
model is essential before evaluating any distributor for a client.

**Model A — Revenue-share, unlimited releases (subscription):**
Flat annual fee; artist keeps a percentage of net revenue (commonly 100% after the
subscription covers overhead); unlimited release volume. Best suited to high-cadence
releasing artists. Risk: the annual fee is a sunk cost whether you release one track
or one hundred.

**Model B — Per-release flat fee:**
One-time charge per release; no annual subscription; ongoing revenue ownership
percentage varies by tier. Best suited to low-volume catalogs with significant
streaming income. Risk: cost per release is high for frequent releasers.

**Model C — Revenue-share percentage:**
No upfront cost; distributor retains a percentage of gross revenue in perpetuity or
for a defined term. Common at the entry and early-career tiers. Risk: high gross
revenue to the distributor as income scales — the free-tier percentage is expensive
in dollar terms once streams are material.

**Model D — Label services / white-glove distribution:**
Revenue-share structure with curated access — the distributor selects clients. Typical
for artists with demonstrated commercial traction. Often includes marketing support,
DSP editorial relationship access, and priority platform communications. Higher
revenue-share rate to the distributor (25–30% range common), but pitch access and
visibility from the distributor's A&R/editorial relationships can have material revenue
value.

**Model E — Aggregator (B2B, label-facing):**
The label or distributor pays a per-delivery fee or negotiates a bulk rate. The
aggregator's client is the label, not the artist. Most independent artists never
interact directly with an aggregator — their distributor (Model A–D) uses an
aggregator as their upstream delivery partner.

**Model selection framework:**
```
Releasing frequency    |  Revenue maturity     |  Model fit
-----------------------|-----------------------|----------------------------------
<5 releases/year       |  Low (<$1K/month)     |  Model A or B (low volume)
>10 releases/year      |  Low (<$1K/month)     |  Model A (unlimited subscription)
<5 releases/year       |  Mid ($1K–$20K/month) |  Model B or D (per-release or label services)
>10 releases/year      |  Mid-high (>$5K/month)|  Model D (label services) — earn-back ratio
Any volume             |  High (>$50K/month)   |  Direct distributor or label services;
                       |                       |  percentage model becomes expensive
```

## 2. Rights Implications of Distributor Choice

**The ISRC registrant code problem:**
Most distributors assign ISRCs using their own registrant code (the middle three
characters). The ISRC is valid, permanent, and follows the recording — but the
registrant record belongs to the distributor, not the artist or label. Operational
implications:

- When the artist leaves the distributor, the ISRCs assigned under the distributor's
  registrant code remain valid identifiers for the recordings.
- The distributor retains the registrant record. If a rights dispute or retroactive
  royalty inquiry involves a specific ISRC, the artist must work through the
  original distributor (or the national agency) to verify registrant history.
- Some distributors will "release" the registrant-record documentation to the label
  on request; others will not — verify before signing.

**Resolution:** artists or labels with significant catalog benefit from obtaining their
own registrant code from their national ISRC agency. ISRCs assigned under the label's
own code are under the label's control permanently, regardless of distributor. This
is a one-time registration cost and a permanent operational advantage.

**UPC assignment:**
UPCs assigned by the distributor are similarly controlled by the distributor. A label
with its own GS1 company prefix (acquired from GS1 in the label's country) assigns
its own UPCs. For most independents, distributor-assigned UPCs are functionally
adequate — there is no portability problem because a new release gets a new UPC
regardless. The issue is principally cosmetic (whose prefix appears in the barcode).

**Rights-system access dependency:**
Most independent artists access YouTube content-recognition and Meta rights manager
through their distributor's partner agreement. If they leave the distributor:
- Reference files uploaded through the previous distributor's account may be removed.
- Claims in the previous distributor's account may need to be re-registered through
  the new distributor.
- There is a risk of a gap period where content-recognition is inactive — an income-
  interruption risk on active catalog. Verify the distributor's offboarding process
  for reference files before initiating a transfer.

**Territory and platform coverage:**
Not all distributors deliver to all platforms in all territories. Specific gaps to
verify before signing:
- China (NetEase Cloud Music, QQ Music, Kuaishou) — not universally covered.
- India (JioSaavn, Gaana) — coverage varies.
- Korea (Melon, Genie, Bugs, Vibe) — specialist required for some.
- Russia/CIS — coverage and sanctions compliance vary by distributor.
- Niche fitness/workout platforms — requires specialist distributor relationships.

An artist whose music is unavailable on a relevant platform in a relevant market
because the distributor lacks that relationship is experiencing a distribution gap
that has a royalty cost.

## 3. Split Payment Mechanics

Some distributors offer split-payment systems that automatically route portions of
revenue to collaborators (producers, co-writers, featured artists) based on
configured splits. Key mechanical facts:

- **Splits are configured at the release (or track) level** — not at the platform
  level. A 70/30 split applies uniformly across all revenue from that track unless
  the system supports platform-specific overrides (uncommon).
- **Splits apply to net revenue after the distributor's fee** — the percentage
  is not on gross. The dollar amount each party receives depends on the net-to-gross
  deduction in the distributor's payout model.
- **Splits are not contracts** — configuring a split in a distributor portal is not
  a substitute for a legally documented co-ownership or royalty-share agreement. The
  split is an operational instruction, not an enforceable rights document.
- **Minimum payout thresholds apply to each recipient** — if a collaborator is owed
  $1.50 but the threshold is $25, the payout is held until the threshold is reached.
  For low-streaming catalog with many small splits, this can create long unpaid
  accumulation periods.
- **The artist of record must own or control the split configuration** — a co-writer
  or producer cannot change a split unilaterally. Disputes over split configurations
  are not resolved by the distributor; they route to Legal.
- **Split payment does not constitute a mechanical royalty payment to writers** —
  this routes to Publishing administration, not to the distributor's split system.
  A producer receiving a revenue split from the distributor is receiving a share of
  master income, not a separate composition payment.

Anti-pattern: treating a distributor split as the full royalty obligation to a
collaborator. It covers master income only. Composition income (mechanical, performance)
flows separately and requires separate publishing administration.

## 4. Catalog Transfer Workflow

Moving a catalog from Distributor A to Distributor B is the highest-risk standard
operation in digital distribution. The risk is not technical — it is the "dark
window": the period when content has been taken down from Distributor A but is not
yet live through Distributor B.

**Phases of a catalog transfer:**

```
Phase 1 — Pre-transfer preparation (do before issuing any takedown instruction)
→ Full catalog manifest export from Distributor A: ISRC, UPC, territory config,
  rights-system registration status, all current metadata, platform availability.
→ Verify which platforms Distributor A delivers to vs. which Distributor B covers.
→ Confirm content-recognition and UGC rights reference files — will they be preserved,
  transferred, or need re-upload?
→ Confirm ISRC records: are they under Distributor A's registrant code or the label's?
→ Obtain a copy of all ISRC-to-recording mappings — this is the most critical
  document in any catalog transfer.

Phase 2 — New delivery setup (complete before takedown, where the platform allows)
→ Set up the full catalog in Distributor B's system: ISRCs, UPCs, metadata, territory
  configuration, audio files, artwork.
→ Initiate delivery to Distributor B BEFORE issuing any takedown instruction.
→ Confirm Distributor B has received and processed all releases before proceeding.
→ Confirm content-recognition reference files are uploaded and active in
  Distributor B's system.

Phase 3 — Takedown from Distributor A
→ Issue takedown instruction for the full catalog.
→ Distributor A processing: typically 24–72h; platform propagation: 24–72h per
  platform — but some platforms can take longer.
→ The "dark window": the period between a track going offline from Distributor A and
  going live through Distributor B. Even with best-practice sequencing, a short dark
  window (hours to a few days) is typical.
→ Monitor dark-window duration per platform — not simultaneous.

Phase 4 — Verification and stabilization
→ Verify live status on each platform through Distributor B.
→ Confirm streaming data is appearing in Distributor B's analytics.
→ Verify content-recognition claims have resumed through Distributor B.
→ Confirm territory configuration matches the pre-transfer manifest.
→ Run an ISRC audit: confirm the ISRCs on the live releases match the manifest.
```

**Dark-window revenue impact:**
A release streaming significant volume at the time of transfer will lose revenue
for every day it is offline. The revenue lost during the dark window is rarely
recoverable. Transfers of commercially active catalog must be timed carefully —
avoid a transfer during high-activity periods (album cycle, active campaign, recent
release). The optimal transfer timing for active catalog is a low-activity period
(3–6 months after peak release activity).

**Dark-window streaming-count implications:**
Streams delivered through Distributor A's system (before the transfer) and streams
delivered through Distributor B's system (after) are separate stream records. Some
platforms merge them correctly via the ISRC; others produce split-count records that
are never consolidated. This means total-platform stream counts for a transferred
release may appear artificially lower than the true cumulative count on some platforms.
Document the transfer date for every release to support future analytics reconciliation.

**ISRC continuity during transfer:**
The existing ISRCs follow the recordings — Distributor B must use the same ISRCs, not
assign new ones. A distributor that insists on new ISRCs for transferred recordings is
making an error. Enforce ISRC continuity as a non-negotiable condition of transfer.
New ISRCs on the same recordings split streaming history and fragment royalty records.

## 5. Distributor Selection Decision Framework

Before recommending or executing a distributor selection, verify each of these:

**Coverage audit:**
- [ ] Delivers to every platform where the artist's audience is active (verify per
      market — not just the major six platforms).
- [ ] Coverage in the artist's top territories (check analytics for current territory
      mix before advising).
- [ ] Any non-standard platform needs covered (fitness platforms, gaming platforms,
      social video).

**Rights and data access:**
- [ ] ISRC registrant code: distributor's or label's own? Obtain documentation.
- [ ] Full analytics data access: per-track, per-territory, per-platform download in
      usable format.
- [ ] Content-recognition and UGC rights access: direct or through the distributor?
      What happens on departure?
- [ ] Pitch tools for editorial submission: available or not? For which platforms?

**Commercial terms:**
- [ ] Fee model vs. expected release volume (calculate expected cost over 3 years).
- [ ] Revenue percentage — net or gross? After which deductions?
- [ ] Minimum payout threshold: how long until small catalogs receive anything?
- [ ] Contract term and exit clause: fixed term, rolling, or at-will?

**Transfer risk:**
- [ ] Offboarding process: what does the distributor do when you leave?
- [ ] Content-recognition reference files: retained, transferred, or deleted?
- [ ] ISRC records: will they provide a full ISRC manifest on departure?

## Domain Anti-Patterns

- Assuming all distributors deliver to the same set of platforms with equal processing
  priority — coverage gaps are real and market-specific.
- Treating a distributor's split-payment configuration as a substitute for a rights
  agreement or publishing administration.
- Beginning a catalog transfer by issuing a takedown before confirming the new
  delivery is processed — this maximizes the dark window.
- Assigning new ISRCs to transferred recordings at the instruction of the new
  distributor — a non-recoverable error that fragments streaming history.
- Treating the distributor's portal data as the historical record of the catalog
  rather than maintaining an independent catalog manifest.
- Selecting a distributor based on price alone without verifying territory and
  platform coverage against the artist's actual audience geography.
