# Label Operations Systems & QC

Label operations infrastructure decomposes into four functional layers. No single
platform covers all four; labels assemble a stack from multiple tools — either by
vendor selection or by relying on their distributor's infrastructure.

## The Four-Layer Label Tech Stack

**Layer 1 — Rights management** (ownership, licensing, contract tracking): tracks
ownership of recordings and compositions, manages licensing agreements, handles
contract terms (territory, term, exclusivity, option periods), and maintains chain
of title for acquisitions.

**Layer 2 — Metadata management** (catalog data governance, DSP delivery
metadata): maintains canonical metadata for every recording, governs how metadata
flows from label to DSPs and collection societies, and enforces completeness and
consistency standards.

**Layer 3 — Royalty accounting** (calculation, statement generation, payment):
ingests royalty data from distributors and societies, applies each artist deal's
contractual terms, generates statements, and processes payments.

**Layer 4 — Release tracking** (project management, delivery status, QC workflow):
manages the deliverables, deadlines, owners, and status across the
A&R-to-delivery sequence.

Enterprise labels run dedicated, purpose-built tools in each layer (and the
largest majors run proprietary content-management and royalty systems with direct
DSP API integrations). The DIY/indie stack typically collapses layers 1–3 into the
distributor's platform with minimal dedicated tooling.

**Rights-management tool selection rule**
```
IF catalog > 500 recordings OR operating in 5+ territories with sub-licensing:
  → a purpose-built rights-management system is required
IF catalog < 500 recordings AND primarily one territory:
  → the distributor's built-in catalog management may suffice for rights tracking
  → limitation: distributor tools rarely handle sub-licensing, option tracking,
    or cross-deal rights management
```

## How Metadata Flows from Label to DSP

```
Label / A&R → master recording + metadata (title, artist, ISRC, credits)
  → label's metadata system (or the distributor's CMS)
  → distributor aggregates metadata into the standard music-data-exchange format
  → standardized delivery message to the DSP (electronic data interchange)
  → DSP ingests, processes, and publishes
  → DSP returns usage data in the standard reporting format to the distributor
  → distributor aggregates usage → royalty calculation → statement to the label
```

The industry uses a standardized XML messaging framework for metadata delivery;
all major DSPs receive content via standardized electronic release-notification
messages, and usage is returned in a corresponding reporting format. A
distributor's implementation version governs which metadata fields can be
transmitted and in what format. Newer versions of the standard added fields for
spatial-audio deliveries, enhanced contributor credits, and improved rights-scope
definitions absent from older versions — relevant when planning a spatial-audio
release strategy.

## Metadata Error Cost Model

A metadata error at delivery is not a quality nicety — it has a quantifiable cost.

| Error type | Immediate cost | Long-term cost |
|------------|----------------|----------------|
| Missing ISRC on a track | Track may not collect performance royalties | Royalty gap from release date; unrecoverable for that period |
| Artist-name variant (wrong format) | Split artist profile; weaker algorithmic recommendation | Permanent history fragmentation; may need DSP support to merge |
| Wrong genre tag | Served to the wrong editorial/algorithmic audience in weeks 1–2 | Reduced playlist consideration until re-delivery or admin update |
| Missing explicit flag | Parental-advisory trigger; possible restriction | Restricted availability in clean modes; complaint pipeline |
| Featured artist in main field | DSP linking failure; streams not attributed to the feature | Incorrect attribution; affects the feature's performance matching |
| Missing producer credits | Performance registration may be incomplete | Long-term performance-royalty gap; relationship risk |

**What it costs in real terms (illustrative):** for a track at ~1M streams/year,
streaming income to the rights holder is in the low single-digit thousands of
dollars per year on one platform (per-stream rates vary by territory, tier, and
agreement and are not quotable as a precise figure). An ISRC error that leaves
three months unmatched costs a proportional fraction of that across all platforms.
Scaled across a catalog with even a small metadata-error rate, the unmatched
royalties from metadata failures alone become a material recurring loss.

## Royalty Statement Anatomy

A compliant royalty statement includes: the statement period; per-release,
per-territory revenue breakdown; the artist royalty rate applied and the royalty
base (net-receipts definition); recoupable costs charged in the period; the
opening balance + costs charged + royalties credited = closing recoupable balance;
the net payment (if recouped) or net unrecouped balance; mechanicals paid to the
publisher/collective; and distribution fees deducted.

**Royalty-accounting failure modes:** missing revenue lines (a territory's
distributor data not ingested — reconcile statement totals against the distributor
dashboard); wrong royalty rate applied (contract terms misconfigured); mechanicals
underpaid (statutory rate not updated after a rate adjustment); cross-
collateralization applied incorrectly (wrong albums pooled); currency-conversion
errors (wrong rate or date).

## Delivery QC Workflow (every release, every time)

```
Step 1 — Audio QC: WAV/FLAC (not lossy); 44.1/48kHz; 24-bit minimum; integrated
  loudness ~-14 LUFS (±1), true peak ≤ -1 dBTP; length confirmed against the
  approved timing; no artifacts; clean version noted if an explicit version exists
Step 2 — Metadata QC: title matches publishing registration exactly; main artist
  matches the verified DSP page; featured artists in the correct field; all
  producer and songwriter credits present; ISRC (12-char, unique, registered);
  UPC (12-digit, unique); primary and secondary genre; explicit flag verified
  against lyrics; language confirmed; release date correct (Friday if pitching)
Step 3 — Artwork QC: JPEG/PNG; sRGB (NOT CMYK); ≥3000×3000px square; no prohibited
  content (phone numbers, URLs, misleading text, non-square crop); artist approval
  in writing
Step 4 — Rights QC: sample clearances confirmed by legal; publishing splits
  documented; master ownership confirmed with no pending disputes; distribution
  rights confirmed for all intended territories
Step 5 — Delivery confirmation: submitted with all assets; distributor receipt
  received; DSP delivery confirmations received; editorial pitch filed; all DSPs
  live and streamable confirmed on release day
```

## Where Systemic Failures Occur

1. **The "good enough" metadata standard decays over time.** Quality maintained at
   launch degrades over 3–5 years as staff turns over and style guides are lost.
   Governance requires a living standard document and an audit cycle, not just
   initial setup.
2. **Royalty systems are configured once and rarely audited.** Escalators trigger,
   option periods expire, and rate amendments are negotiated, but a system
   configured to the original terms keeps computing at those terms unless updated.
   A label with 5+ years of roster history and any amendments should audit its
   configurations annually.
3. **DSP artist-page management is nobody's job.** Editorial profile updates,
   images, bios, and verified status degrade silently when unassigned, reducing
   editorial consideration without triggering any alarm.
4. **Neighboring-rights registration is treated as optional.** For labels owning
   masters, registration for broadcast/non-interactive performance royalties is
   mandatory for collection; unregistered catalog leaves recurring annual income
   uncollected. Assign ownership of the standing process.

## Critical Integration Points

- **Metadata → royalty accounting.** Metadata errors at delivery become royalty
  errors at accounting. A wrong ISRC means DSP usage is reported under the wrong
  identifier; the accounting system cannot match it to the correct contract,
  producing unmatched or misallocated revenue that propagates silently until a
  reconciliation surfaces it.
- **Distributor royalty data → label accounting.** Distributors report in
  proprietary formats; labels must transform that data for their accounting system
  or use a direct integration. Manual export-transform introduces errors and
  delays; labels above ~$100K annual streaming revenue should prioritize a direct
  integration.

## DIY vs. Enterprise Stack — The Key Failure Point

The most common operational failure for labels on distributor-only infrastructure
is **royalty accounting**. Distributor statements list revenue but do not apply
artist deal terms. A label with multiple artists on different rates, advances, and
recoupment structures cannot correctly generate artist statements from raw
distributor data without a purpose-built accounting system or a qualified royalty
accountant. Labels that "do it in a spreadsheet" are almost always making
calculation errors — usually, unintentionally, in the label's favor.

## Practitioner-Layer Insight

- **System configuration matters as much as the system.** A well-configured
  accounting instance with correct contract terms, royalty bases, and recoupable-
  cost classifications produces accurate statements; a poorly configured one
  produces plausible-looking numbers that are wrong, and the errors stay silent
  until an audit. The initial configuration needs genuine label-accounting
  expertise, not just software training. For small labels that cannot afford this,
  a one-time configuration review by a music royalty accountant is far cheaper than
  years of quiet errors.
- **Maintain a master ISRC registry.** Allowing multiple team members to issue
  ISRCs without a central registry creates conflicts — the same ISRC on two
  recordings — triggering DSP rejection that can take weeks to resolve across all
  registrations.

See also: [[label-ops-distribution-and-delivery]],
[[label-ops-catalog-management]], [[label-ops-judgment-and-triage]].
