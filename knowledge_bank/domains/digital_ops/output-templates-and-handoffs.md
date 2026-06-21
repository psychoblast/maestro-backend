# Output Templates & Handoffs

Every output carries a mandatory core; conditional modules attach only when relevant.

**Mandatory core (every output):**
- **Work Product** — the substantive analysis.
- **Decision Summary** — answers why / why now / what data / what assumptions / what
  would change the answer.
- **Confidence Assessment** — level, supporting reasons, risks/unknowns, and the
  named weakest-link cap.

**Decision-type fields (all four templates are decisions):** Alternatives · Next Best
Action (24–72h).

**Conditional modules (attach only when the matrix says so):** Scores · Risk Register
· Memory Update.

**Anti-bloat rule:** a quick ISRC check does not ship with a risk register. Attaching
an irrelevant module is a violation equal to omitting a relevant one.

**Anti-fabrication rule:** no platform specification, identifier fee, or platform-
policy figure is stated without a currency-verification note.

**NOT EVALUABLE rule:** every template using grades must name NOT EVALUABLE sub-
signals explicitly.

**Scope-fence rule:** every template names its handoffs and never absorbs adjacent
specialties.

## Module Matrix

| Template | Scores | Risk Register | Memory Update | Alternatives | Next Best Action |
|----------|--------|---------------|---------------|--------------|-----------------|
| 1 — Digital Release QC Report | ✓ (8-dimension scorecard) | ✓ (5 categories) | ✓ | ✓ | ✓ |
| 2 — Metadata Error Remediation Plan | ✗ | ✓ (severity + remediation risk) | ✓ | ✓ | ✓ |
| 3 — Rights Hygiene Audit Report | ✗ | ✓ (coverage-gap risk) | ✓ | ✓ | ✓ |
| 4 — Content Recognition Claim Evaluation | ✗ | ✓ (claim-risk categories) | ✓ | ✓ | ✓ |

## Template 1 — Digital Release QC Report (Flagship)

**When to use:** any formal release-quality assessment — pre-delivery QC, post-
delivery review, periodic health check, or acquisition due diligence on a specific
release. Not required for single-field quick checks (use a brief inline advisory).

```
# DIGITAL RELEASE QC REPORT — [release / context]
Date: [YYYY-MM-DD]
Scope: [pre-delivery QC / post-delivery review / health check / acquisition due diligence]

## WORK PRODUCT
### Eight-Dimension Assessment (release-quality scorecard)
| Dimension | Weight | Grade | Evidence type | NOT EVALUABLE (+ data required) | Confidence | Hard Gate |
| D1 Metadata Completeness | 0.22 | [A+–F] | [MEASURED/SOURCED/JUDGED] | [...] | [FULL/PARTIAL/LOW] | — |
| D2 Identifier Integrity | 0.20 | [...] | [...] | [...] | [...] | HG-1: [CLEAR/TRIGGERED] |
| D3 Audio/Artwork Spec | 0.15 | [...] | [...] | [...] | [...] | HG-2: [CLEAR/TRIGGERED] |
| D4 Rights-System Coverage | 0.18 | [...] | [...] | [...] | [...] | HG-3: [CLEAR/TRIGGERED] |
| D5 Delivery Timeline | 0.10 | [...] | [...] | [...] | [...] | — |
| D6 Territory Configuration | 0.08 | [...] | [...] | [...] | [...] | HG-4: [CLEAR/TRIGGERED] |
| D7 Error History | 0.04 | [...] | [...] | [...] | [...] | — |
| D8 Post-Release Monitoring | 0.03 | [...] | [...] | [...] | [...] | — |

PROVISIONAL COMPOSITE: [X.XX] — secondary to per-dimension grades; not comparable across releases.
Composite confidence cap: [FULL/PARTIAL/LOW] — capped by [named weakest dimension + sub-signal].

### Action Profile
IMMEDIATE (D+ or below, or any hard gate): [dimension · grade · gap · required action · daily impact]
PRIORITY (C/C− in a dimension weighted ≥0.15): [...]
OPTIMIZE (C+/B− in a dimension weighted ≥0.15): [...]
MAINTAIN (B or above): [...]

### Owner Input Gaps
[NOT EVALUABLE sub-signals that would change a grade or tier if resolved; name the data required.]

## DECISION SUMMARY
Verdict / Why / Why now / What data supports this / Assumptions / What would change this answer

## CONFIDENCE ASSESSMENT
Level / Supporting reasons / Risks and unknowns / Weakest-link cap

## ALTERNATIVES
[at least one credible alternative, or "none credible — [reason]"]

## NEXT BEST ACTION (24–72h)
[one concrete step targeting the highest-priority gap]

## RISK REGISTER
| Metadata routing risk | H/M/L | [...] |
| Identifier conflict risk | H/M/L | [...] |
| Rights-system gap risk | H/M/L | [...] |
| Territory rights risk | H/M/L | [...] |
| Delivery rejection risk | H/M/L | [...] |

## MEMORY UPDATE
[delivery state / identifier state / rights-system registration state] — observed/told/inferred, H/M/L
```

## Template 2 — Metadata Error Remediation Plan

**When to use:** a specific metadata error (or group) has been identified in a
delivered release and a structured remediation plan is required.

**NOT ESTIMABLE rule:** revenue-impact estimates are produced only where evidence
supports them (streaming analytics, a confirmed ISRC conflict with known
fragmentation, or documented revenue diversion). Otherwise state NOT ESTIMABLE with
the reason.

```
# METADATA ERROR REMEDIATION PLAN — [release / context]
Date / Error source / Affected release(s)

## WORK PRODUCT
### Error Inventory (per error)
- Severity: [Tier 1 blocking / Tier 2 routing-critical / Tier 3 discovery / Tier 4 cosmetic]
- Evidence: [MEASURED/SOURCED/JUDGED]
- Affected recordings/releases / Current impact
- Revenue impact: [ESTIMATE with basis | NOT ESTIMABLE — reason]

### Remediation Sequence (Tier 1 first)
| Priority | Error | Severity | Required action | Distributor action? | Est. time | Dependencies |

### Propagation Timeline
- Correction submitted by / expected distributor processing / expected platform propagation / verification check
- Currency note: propagation timelines are estimates; verify with current distributor documentation.

## DECISION SUMMARY / CONFIDENCE ASSESSMENT / ALTERNATIVES / NEXT BEST ACTION (24–72h)

## RISK REGISTER
| Correction failure risk | H/M/L | [...] |
| Platform propagation delay risk | H/M/L | [...] |
| Retroactive royalty recovery risk | H/M/L | [...] |
| Recurrence risk | H/M/L | [...] |

## MEMORY UPDATE
[error types in this release's delivery history / distributor-specific correction behavior]
```

## Template 3 — Rights Hygiene Audit Report

**When to use:** a catalog-level rights-hygiene audit across multiple releases.
**Scope:** the digital delivery and UGC rights layer only. Composition-rights
registration routes to Publishing.

```
# RIGHTS HYGIENE AUDIT REPORT — [catalog / context]
Date / Catalog scope / Audit methodology (name all data sources)

## WORK PRODUCT — Seven-Coverage-Area Audit
For each area — 1 ISRC Coverage · 2 UPC Coverage · 3 Platform Availability ·
4 Content-Recognition & UGC Rights · 5 Territory Configuration · 6 Metadata
Consistency · 7 Error Status — record:
- Status [CONFIRMED / GAPS IDENTIFIED / NOT EVALUABLE]
- Evidence [MEASURED/SOURCED] / Gap summary / Priority [IMMEDIATE/PRIORITY/SCHEDULE]
- Revenue impact where applicable [ESTIMATE with basis | NOT ESTIMABLE — reason]

For a rights-liability territory block, document three timestamps — (a) submission to
distributor, (b) distributor confirmation, (c) platform-level propagation — and state
explicitly that submission to the distributor is not the same as blocked at the platform.

### Coverage Summary Table
| Coverage Area | Status | Priority | Gap Count | Revenue Risk | Action |

Priority logic: IMMEDIATE = active income loss/liability; PRIORITY = quantifiable but
not-yet-active; SCHEDULE = minimal immediate impact.

## DECISION SUMMARY / CONFIDENCE ASSESSMENT / ALTERNATIVES / NEXT BEST ACTION (24–72h)

## RISK REGISTER
| ISRC conflict risk | CID/UGC income loss risk | Territory liability risk | Dark-catalog risk | Audit completeness risk |

## MEMORY UPDATE
[catalog rights-coverage state / dark-catalog segments / portal data quality]
```

## Template 4 — Content Recognition Claim Evaluation

**When to use:** a content-recognition claim (or a TikTok-layer/Meta claim) has been
received on owned content and a rights evaluation with a dispute/accept recommendation
is required.

**NOT QUOTABLE rule:** specific claim revenue amounts are proprietary platform data —
no specific revenue figures from named releases in externally shared output without
owner authorization.

```
# CONTENT RECOGNITION CLAIM EVALUATION — [release / context]
Date / Platform / Claim type [Monetize/Block/Track] / Claimant / Claim scope [full or segment]

## WORK PRODUCT
### Rights Basis Assessment
Step 1 — Claimant identification: | Claimant | Type | Known rights basis | Contact status |
Step 2 — Rights basis: controls master? controls composition? full or segment? prior licensing relationship?
Step 3 — Classification: [ ] VALID  [ ] OVER-BROAD  [ ] ERRONEOUS  [ ] FRAUDULENT  [ ] ISRC-CONFLICT
Step 4 — Current revenue impact: [Monetize→routing / Block→unavailable / Track→none]; daily impact [ESTIMATE | NOT ESTIMABLE]

### Recommendation — ACCEPT / DISPUTE / NOT EVALUABLE
- ACCEPT: confirm revenue routing
- DISPUTE: dispute basis; evidence to submit; dispute timeline; escalation path if upheld
- NOT EVALUABLE: data required; interim action (do not accept or dispute; note any window clock)

## DECISION SUMMARY / CONFIDENCE ASSESSMENT / ALTERNATIVES / NEXT BEST ACTION (24–72h)

## RISK REGISTER
| Dispute window risk | Fraudulent-claim escalation risk | ISRC-conflict underlying risk | Revenue diversion risk |

## MEMORY UPDATE
[claim type & claimant classification / claim history — first or recurring]
```

## Handoff Boundaries (Scope Fences)

This domain names the handoff and never absorbs the adjacent specialty:

| Topic | Routes to |
|-------|-----------|
| Collection-society and mechanical-agency registration; ISWC assignment | Publishing |
| Financial royalty modeling and income projections | Finance & Royalties |
| Legal rights analysis, contract execution, dispute litigation | Legal |
| Distribution-partner selection strategy | Label/Production operations |
| Sync pitch strategy and music-supervisor relationships | Sync |
| Marketing and release-campaign strategy | Marketing |
| Playlist strategy and editorial relationships | Marketing/Playlist |

## Escalation Flags

- A confirmed ISRC conflict with active royalty misrouting → IMMEDIATE remediation;
  notify the rights/finance owner.
- A claim upheld after dispute, or a pattern of bad-faith claiming → Legal.
- Content live in a territory without cleared rights → IMMEDIATE remediation; rights
  liability.
- A platform spec that cannot be currency-verified → flag as NOT VERIFIABLE; do not
  present as current fact.

## Hard Refusals

- No delivery approval without all mandatory metadata fields complete.
- No ISRC reuse across materially different recordings.
- No acceptance of a content-recognition claim without a rights-basis check.
- No treating delivery confirmation as rights-system activation.
- No specification figure without a source and verification date.
- No advice on collection-society/mechanical registration — that routes to Publishing.
