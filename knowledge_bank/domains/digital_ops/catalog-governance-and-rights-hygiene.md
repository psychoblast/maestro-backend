# Catalog Metadata Governance & Rights Hygiene

## 1. Metadata Governance Framework — Four Pillars

Governance is the organizational infrastructure that ensures metadata is created
correctly, maintained consistently, and updated systematically across a catalog at
scale.

**Pillar 1 — Standards:** documented metadata standards specifying required fields,
acceptable values, format rules, and naming conventions. The standard must include
ISRC-assignment rules, the canonical artist-name form, the genre taxonomy in use,
territory-configuration defaults, and required-vs-optional fields. It must be
versioned and dated — when platforms change requirements, the standard updates with
them.

**Pillar 2 — Processes:** defined workflows for new-release metadata creation,
pre-delivery QC, post-delivery verification, error remediation, and catalog
maintenance cycles. Processes are documented, not assumed — the person who created
the process should not be the only one who understands it. Includes exception
handling (e.g., a legacy release without an ISRC).

**Pillar 3 — Ownership:** named responsible parties for each metadata domain — who
owns ISRC assignment, territory configuration, the catalog manifest, and metadata
approval before delivery. Ownership includes accountability for errors: if an ISRC
conflict is found, who investigates and remediates?

**Pillar 4 — Tools:** the systems used to manage metadata at scale — spreadsheets
for small catalogs, dedicated metadata-management systems for mid-to-large, or
enterprise systems for the largest. Tools should support validation, version
history, bulk updates, and DDEX-compatible export.

Anti-pattern: treating governance as a tool-selection problem. Without standards and
processes, better tools just create better-organized incorrect metadata. Software is
the least valuable pillar without the other three. A label with a spreadsheet and a
documented standard outperforms a label with enterprise software and no standard.

## 2. Version Control for Metadata

The core problem: music metadata changes over time — remasters, evolving artist
names, corrected titles, expanding/contracting territory rights — and there is no
native version control in digital distribution. Each change creates a new state
without preserving the history of what was delivered before.

Why it matters:
- **Dispute resolution:** if a statement shows anomalous data for a period, knowing
  what metadata was delivered then enables diagnosis. Without history, the cause
  cannot be determined.
- **ISRC audit:** determining when an ISRC was assigned, to which recording, and by
  whom requires history.
- **Distributor change:** migrating a catalog requires knowing exactly what was
  delivered to the previous distributor — ISRCs, territory configurations, and
  corrections.

| Catalog scale | Practical version-control approach |
|--------------|-----------------------------------|
| <50 releases | Spreadsheet with a dated entry per release and a dated change-log column; export on each delivery |
| 50–200 releases | Structured spreadsheet/database with row-timestamp history; a separate "delivery history" worksheet |
| 200–1000 releases | Dedicated metadata-management tool with change tracking and DDEX import/export |
| 1000+ releases | Enterprise system with API integration to distributors and a required change audit log |

What to record at each delivery: delivery date/time; distributor and platform
targets; ISRC(s) per track; UPC for the release; territory configuration at the time;
any deviation from the standard (why, approved by whom).

Anti-pattern: treating the distributor portal as the catalog's record of truth. The
portal shows the *current* state, not the history. A change made months ago is
invisible in the current view — and when it causes an anomaly in a past statement,
the lack of history makes diagnosis impossible.

## 3. Metadata Debt

What creates debt at the governance level: releases delivered by different people
without a common standard; catalog acquisitions bringing in legacy metadata without a
normalization audit; historical recordings never assigned ISRCs or normalized
metadata; one-off releases created under deadline pressure; distributing through
multiple distributors over time without a master catalog record.

**The acquisition scenario:** a label acquires 500 releases with a catalog list that
includes ISRCs. But 30% of ISRCs are non-standard or informally assigned; the artist
name appears in four spellings; no territory history exists; content-recognition was
never activated for 60%; and 80 recordings have no ISRC at all. This is significant
metadata debt — the remediation cost is a material factor in the acquisition
economics. A metadata-debt assessment belongs in acquisition due diligence.

**Debt remediation sequencing:**
1. ISRC conflict resolution (highest — active royalty misrouting)
2. Content-recognition activation (daily uncollected income)
3. ISRC assignment for uncovered recordings (delivery capability)
4. Artist-name normalization (discovery and page unification)
5. Territory-configuration audit (rights compliance)
6. Metadata-field completion (genre, language, credits)

## 4. Catalog Scale Thresholds

Illustrative ranges based on practitioner observation; specific thresholds vary by
complexity, staffing, and delivery cadence.

| Tier | Releases | Management approach | Typical resourcing |
|------|----------|---------------------|--------------------|
| DIY artist | 1–20 | Spreadsheet + portal + personal knowledge | Self-managed |
| Small label | 20–100 | Enhanced spreadsheet/database; one person manages metadata | 1 part-time/shared role |
| Mid-size | 100–500 | Dedicated management system; documented standard | 1–2 dedicated roles |
| Established | 500–2000 | Management system with DDEX export; regular audit cycles | Small digital-ops team |
| Major-scale | 2000+ | Enterprise system; API integrations; governance team | Larger digital-ops team |

**The ~100-release inflection point:** spreadsheet-based management becomes
operationally risky around 100 releases. Maintaining consistency, checking for ISRC
conflicts, and tracking delivery history manually across 100+ releases causes errors
to compound faster than they can be corrected. A dedicated tool pays for itself in
error prevention here.

**The ~500-release governance threshold:** at 500+ releases, governance requires
documented policies, named ownership, and systematic audit cycles — not just better
tools. Without formal governance, a small team will accumulate debt faster than the
normal release cycle can remediate it.

## 5. Metadata Standards Maintenance

Standards evolve and governance must track them: ERN version updates may add or
deprecate fields; platform requirement updates change mandatory fields and specs; new
platforms or capabilities add new requirements.

Maintenance protocol:
1. **Periodic review trigger** — review the standard at minimum once per quarter
   against current distributor and platform documentation.
2. **Change tracking** — document every update with a date and a description of what
   changed and why.
3. **Staff notification** — when the standard changes, everyone who creates or
   reviews metadata is notified and understands the change.
4. **Retroactive scope assessment** — when the standard changes, assess whether
   existing catalog entries need updating to meet the new requirement.

Anti-pattern: writing a standard once and relying on it indefinitely. An unmaintained
standard is worse than none — it creates false confidence while drifting from actual
requirements. A standard has a deprecation date (the date after which it has not been
reviewed); anything past its review date is potentially stale.

**Practitioner insight:** the most valuable governance investment for a growing
independent is designating a "metadata owner" — one person accountable for the state
of the catalog's metadata who understands the standards and drives audit cycles. The
role is undervalued because metadata work is invisible when done correctly and very
visible (and expensive) when done incorrectly. One ISRC-conflict remediation on a
commercially significant release typically exceeds the annual cost of a part-time
metadata role.

## 6. Rights Hygiene Audit — Seven Coverage Areas

A catalog-level rights-hygiene audit assesses these areas, each with a status, an
evidence type, and a priority:

1. **ISRC coverage** — every recording has a valid, unique, conflict-free ISRC.
2. **UPC coverage** — every release has a valid UPC/EAN.
3. **Platform availability** — releases present on the platforms where distribution
   rights exist (spot-check or full audit).
4. **Content-recognition and UGC rights status** — content-recognition, the TikTok
   layer, and the Meta rights manager registered where activity exists.
5. **Territory configuration** — content available only where rights are cleared, and
   not blocked where rights exist.
6. **Metadata consistency** — delivered metadata matches the live platform display.
7. **Error status** — open delivery errors or pending corrections in the portal.

**Priority logic:** IMMEDIATE = active income loss or active rights liability;
PRIORITY = a quantifiable but not-yet-active impact; SCHEDULE = minimal immediate
impact.

**The dark-catalog problem:** recordings that exist but were never digitally
distributed, or distributed without content-recognition activation, generate no
income while the rights-holder assumes the catalog is "out there." Quantifying the
dark catalog is part of a complete audit.

**Rights-liability territory remediation:** when blocking content for a rights-
liability territory, the output must document three separate timestamps — (a)
submission to the distributor, (b) distributor confirmation, (c) platform-level
propagation verification — and must state explicitly that submitting the block
instruction to the distributor is not the same as the content being blocked at the
platform.

## Domain Anti-Patterns

- Treating governance as a tool-selection problem instead of standards + process.
- Treating the distributor portal as the catalog's historical record of truth.
- Skipping a metadata-debt assessment during catalog acquisition.
- Writing a metadata standard once and never reviewing it.
- Assuming "submitted to the distributor" equals "live/blocked at the platform."
