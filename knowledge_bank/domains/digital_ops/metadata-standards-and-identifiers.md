# Metadata Standards & Identifier Lifecycle

## 1. Metadata Standards Overview

**DDEX ERN (Electronic Release Notification):** the dominant industry standard for
communicating release metadata and delivery instructions between distributors and
platforms. Each ERN file is a structured set of routing instructions — every field
is consequential. Delivery types include the standard content delivery and the
takedown. New ERN versions can add mandatory fields, deprecate fields, or change
acceptable values; a label needs to know when its distributor upgrades versions.

**ID3:** the embedded tag standard for audio files (title, artist, album, year,
genre, and extended frames). ID3 tags travel with the file and are distinct from
the delivery-level metadata sent in the ERN.

**Recognition/reference databases:** music recognition services and open metadata
databases match recordings to canonical metadata. Correct, consistent metadata at
delivery improves how a recording is matched and displayed across these systems.

**Required vs. optional fields:** every delivery has a mandatory core (see the
completeness threshold in the core doctrine) and an optional layer (extended
credits, editorial tags) that can usually be supplemented after delivery. The
discipline is knowing which is which before submission.

**Character and format conventions:**
- Character encoding: UTF-8 for all metadata fields — critical for non-Latin script.
- Release-date format: ISO 8601 (YYYY-MM-DD).
- Language codes: ISO 639 two-letter (or three-letter) codes for title/lyrics.

## 2. ISRC Anatomy

The ISRC (International Standard Recording Code, ISO 3901) is a 12-character
alphanumeric code that permanently identifies a specific sound recording or music
video.

```
CC-XXX-YY-NNNNN
│   │   │  └── Designation code: 5-digit sequence assigned by the registrant
│   │   └───── Year of reference: 2-digit year the code was assigned
│   └───────── Registrant code: 3-character code assigned to the registrant
└───────────── Country code: 2-letter ISO 3166-1 alpha-2 of the registrant
```

Who assigns each part:
- **Country code** — determined by the national ISRC agency.
- **Registrant code** — assigned by the national agency to the label, distributor,
  or individual registrant.
- **Year of reference** — the year the ISRC is assigned (not the year the recording
  was made).
- **Designation code** — assigned sequentially by the registrant; unique within the
  registrant/year combination.

**Registrant code acquisition:** most artists and independent labels use their
distributor's registrant code rather than obtaining their own. Consequence: the
ISRC is technically controlled by the registrant (the distributor) rather than the
artist/label. When changing distributors, ISRCs registered under the previous
distributor's code remain valid for the recording but are tied to the previous
distributor's registrant record — a practical concern for catalog transfers.

## 3. ISRC Assignment Protocol

- **When to assign:** before delivery — ideally at the recording stage. An ISRC
  assigned before mixing/mastering avoids the common error of assigning to a rough
  mix and then needing a new ISRC when the final master differs materially.
- **Sequential assignment:** ISRCs are assigned sequentially within the
  registrant's year. Gaps are permissible but should be documented.
- **Multi-track releases:** every track receives a separate ISRC. A 12-track album
  needs 12 ISRCs. The UPC/EAN identifies the release; the ISRCs identify each
  recording.

**Pre-delivery ISRC validation checklist:**
1. Is the ISRC in the correct 12-character format (CC-XXX-YY-NNNNN)?
2. Does the country code match the registrant's registration country?
3. Is the registrant code valid for this registrant?
4. Is the ISRC unique — not previously assigned to a different recording in this
   registrant's catalog?
5. Has it been searched in a global ISRC registry to confirm it is not already in
   use by another registrant?

## 4. ISRC Reuse Rules (Summary)

The full decision tree lives in the core doctrine. Key rules:
- Same recording → same ISRC, regardless of new package, rights-holder, or
  distributor.
- New recording of the same song (cover, re-record, new version) → new ISRC.
- Re-edited recording with structural changes → new ISRC.
- Remaster → same ISRC for normalization/EQ-only masters; new ISRC for sonically
  materially different remasters (convention varies — consult registry guidance).
- Clean/explicit versions → same ISRC preferred (convention); distributor
  requirements may differ.

**Common scenario — re-release on a new label:** a recording released on Label A
(ISRC `XX-AB1-20-00001`) is now released by Label B. Correct action: Label B
delivers using the existing ISRC. The ISRC belongs to the recording, not the
label. Common error: Label B assigns a new ISRC "because this is a new release on
our label," creating two ISRCs for one recording — royalties split across two
records, streaming counts fragmented, and a deduplication job across every platform
where both exist.

## 5. UPC/EAN Anatomy

- **UPC** is the 12-digit barcode standard; **EAN-13** is the 13-digit
  international extension. In music distribution they are used interchangeably — a
  12-digit UPC becomes a 13-digit EAN-13 by prepending a zero.
- **What it identifies:** the commercial release — the album, EP, single, or
  bundle as a product. One UPC per release configuration (a deluxe edition is a
  different product from the standard edition; each needs its own UPC).
- **Who assigns it:** typically the distributor. Labels can obtain their own UPC
  company prefix from the global standards body, but most independents use
  distributor-assigned UPCs.

**A new UPC is required for:** any new release; deluxe/expanded editions; different
configurations (a physical edition gets a separate UPC from the digital release).

**A UPC does NOT change for:** new artwork on the same release; metadata correction
on the same release (same distributor); price changes.

Anti-pattern: using a physical product's UPC for the digital release. Physical and
digital UPCs are tracked separately at point-of-sale and streaming systems; reusing
one creates reporting conflicts between digital and physical sales data.

## 6. Common ISRC Errors and Remediation Cost

**Error 1 — Duplicate ISRC (same ISRC on two different recordings).**
Cause: assignment without checking existing use; system error; copy-paste in manual
entry. Consequence: royalties from both recordings merge under one ISRC; matched
revenue may flow entirely to one rights-holder; both recordings misidentified;
streaming counts intermingled. Remediation: deduplication — one recording gets a
new ISRC; affected platforms get corrected deliveries; retroactive recovery may be
required. Time to resolve: weeks to months depending on distributor and platform.

**Error 2 — Split ISRC (same recording with two or more ISRCs).**
Cause: ISRC assigned at two points (original release + re-release); different
distributors each assigned their own. Consequence: streaming counts split across
ISRCs; neither gets the complete count; royalty data fragmented; chart eligibility
may be affected. Remediation: consolidation — a target ISRC is identified and
platforms redirect streams to it; some platforms do not support consolidation and
require full redelivery. Time to resolve: typically several weeks per platform.

**Error 3 — ISRC assigned before the recording is final.**
Cause: assignment at demo/rough-mix stage; the final master differs materially but
the ISRC is not updated. Consequence: the ISRC may refer to a different version; if
the draft was delivered, the wrong file may be live. Remediation: if the draft was
never delivered, simply reassign the ISRC to the final recording; if delivered,
redeliver with corrected audio and ISRC.

**Error 4 — Invalid ISRC format.**
Cause: system error; manual entry without validation. Consequence: delivery rejects
at the distributor or platform; release blocked. Remediation: immediate format
correction and redelivery — low cost if caught pre-delivery.

**Remediation cost framework:**
- Caught in pre-delivery QC → correction time only (minutes to hours).
- Discovered after delivery but before processing → redelivery cost; minor delay.
- Discovered on live content → multi-week remediation per platform; potential
  retroactive royalty recovery; distributor support required at each platform.

**Practitioner insight:** the most expensive ISRC error is not the format error
(caught immediately) — it is the "same recording, two ISRCs" case that lives
undetected for years across a large catalog. A back catalog acquired without ISRC
deduplication verification has an unknown number of these conflicts embedded in it.
A deduplication audit is a standard catalog-acquisition due-diligence step that is
frequently skipped, with ongoing royalty fragmentation as the consequence.

## 7. Identifier Interoperability

- **ISRC** identifies the master recording.
- **ISWC** identifies the underlying composition.
- Performer- and party-level identifiers, release-level grouping identifiers, and
  party interested-party codes interoperate across the rights ecosystem.

Never conflate the ISRC (master) with the ISWC (composition). They are separate
identifiers for separate rights, and conflating them produces incorrect matching
across both performance and mechanical collection. Composition-rights registration
itself routes to Publishing — this domain ensures the digital identifiers are
correct and correctly linked.

## Domain Anti-Patterns

- Treating metadata as a clerical task rather than a routing table.
- Assigning a new ISRC because the release got a new UPC, label, or distributor.
- Using a physical UPC for a digital release.
- Skipping the ISRC-deduplication step during catalog-acquisition due diligence.
- Conflating the master identifier (ISRC) with the composition identifier (ISWC).
