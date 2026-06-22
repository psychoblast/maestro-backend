# PLMKR Sync Agent — Backend Royalties, Metadata & Territory Mechanics

---

## LAYER 1 — CUE SHEET MECHANICS

### What a cue sheet is and why it matters
A cue sheet is the official record of every piece of music used in a film or television production: title, composer(s), publisher(s), performing rights organization (PRO), use type, duration, and the scene or episode it appears in. The cue sheet is the document that enables performance royalty collection — without a correctly filed cue sheet, the PRO cannot match a broadcast to a registered work, and no performance royalty is paid.

**Critical gotcha:** The production company (studio, network, or independent producer) — not the music owner — is responsible for filing the cue sheet with the relevant PRO(s). Music owners cannot force filing; they can only track whether it happened and follow up when it hasn't.

### Cue sheet fields (mandatory for correct filing)
| Field | What to supply | Common error |
|---|---|---|
| Music title | Exact title as registered with PRO | Alternate title, re-title, or truncated title creates a mismatch |
| Composer(s) | Full legal name(s), share splits | Initials only, missing co-writer |
| Publisher(s) | Publisher name as registered | DBA vs. legal entity name mismatch |
| PRO affiliation | ASCAP / BMI / SESAC / SOCAN / PRS / etc. per party | Missing party's PRO |
| ISRC | International Standard Recording Code for the master used | Using the wrong ISRC (alternate version, re-record) |
| ISWC | International Standard Musical Work Code for the composition | Often omitted — PROs need this for international collection |
| Use type | Background instrumental / Background vocal / Featured / Visual vocal / Theme | "Background" when it's actually "featured" reduces royalty rate |
| Duration | Exact seconds used (not song length) | Rounding to minutes misses fee tier thresholds |
| Episode/scene reference | Episode number and scene or timecode | Missing reference makes audits impossible |

### Use type definitions (determines royalty rate)
- **Theme:** music written for and identified with the production; highest royalty multiplier.
- **Featured:** music is prominently in the foreground; characters respond to it or it drives a scene (a character turns on a radio; a band plays onstage). Featured rates are higher than background.
- **Background vocal:** music with lyrics played at reduced volume in the background of a scene. Lyric content makes it a higher class than background instrumental.
- **Background instrumental:** incidental music in a scene; lowest royalty class but most frequent use.
- **Visual vocal:** music where the performance is seen (e.g., an artist performing on screen). Treated as featured.

**Practical implication:** When a track is used prominently — a character dances to it, the camera holds on a speaker, the climactic scene is built around it — insist on "featured" cue sheet classification in writing, before the cue sheet is filed. Reclassification after filing requires the production company to re-submit, which rarely happens voluntarily.

### Cue sheet verification protocol
1. Request confirmation from the production company's music clearance team that cue sheets have been submitted.
2. If the show airs on a US network or streamer: check ASCAP ACE (search.ascap.com) or BMI Work Search (repertoire.bmi.com) for the work registration, and cross-reference the cue sheet filing status 60 days post-air.
3. For international broadcasts: contact your PRO's international team or a royalty auditing service to verify collection from reciprocal PROs.
4. If a cue sheet is missing after follow-up: the artist's publisher (or self-publishing entity) has standing to contact the production company's music clearance coordinator directly.

---

## LAYER 2 — PRO REGISTRATION & COLLECTION

### US PRO landscape
| PRO | Structure | Key facts |
|---|---|---|
| ASCAP | Member-owned, not-for-profit | Largest by number of members; distribution quarterly |
| BMI | Not-for-profit, broadcaster-founded | Largest by revenue; distribution quarterly |
| SESAC | For-profit, invitation-only | Smaller catalog but known for higher per-performance rates for selected members; real-time data tracking |
| GMR | Global Music Rights; for-profit, invitation-only | Founded by Irving Azoff; focuses on top-tier catalog; aggressive licensing posture |

**Writer/publisher split (US):** Performance royalties are split 50% to the writer's share and 50% to the publisher's share. The PRO pays each share separately. A songwriter who is their own publisher receives 100% of the performance royalty from their PRO. A songwriter with a traditional publishing deal may receive only 25% (50% writer's share × 50% reversion after publisher's cut) — the exact split depends on the publishing contract.

**Affiliation lock:** A writer or publisher can be affiliated with only one US PRO at a time. Switching PROs requires a formal resignation with the current PRO and a waiting period before new registrations are valid. Work registered under an old PRO affiliation continues to generate royalties under that PRO until the work is re-registered with the new one.

### International PRO mechanics
International performance collection flows through a reciprocal agreement network: your US PRO collects on your behalf in the US; the local PRO in each foreign territory collects domestically, then remits your share to your US PRO (or directly to you if you have a direct affiliation).

**Common reciprocal PROs:**
| Territory | Publishing PRO | Master/neighboring rights |
|---|---|---|
| UK | PRS for Music | PPL |
| Germany | GEMA | GVL |
| France | SACEM | SCPP / SPPF |
| Canada | SOCAN | Re:Sound |
| Australia | APRA AMCOS | PPCA |
| Netherlands | Buma/Stemra | SENA |
| Japan | JASRAC | RIAJ / CPRA |

**Neighboring rights (master side):** Performance royalties on the master recording side — when a recording is broadcast on radio, TV, or in public venues — are collected via neighboring rights organizations (PPL in the UK, SoundExchange in the US for digital broadcasts, national neighboring rights societies elsewhere). SoundExchange collects US digital performance royalties (internet radio, satellite) and pays the performer 45%, the featured artist 5%, and the label 50%. This is separate from the sync fee.

**Key gap:** US terrestrial (AM/FM) radio does not pay master-side performance royalties under current law — only the publishing side (ASCAP/BMI) receives royalties from terrestrial broadcast. This is a well-known US anomaly; most other territories pay both sides.

---

## LAYER 3 — ISRC, ISWC & METADATA STANDARDS

### ISRC (International Standard Recording Code)
- Identifies the **master recording** (not the composition).
- Format: `CC-XXX-YY-NNNNN` (Country, Registrant, Year, Designation).
- Assigned by: the label or a self-releasing artist via their ISRC registrant (national agency or distributor).
- Scope: one unique ISRC per unique recording. A re-record, alternate mix, or radio edit each receive their own ISRC, even if the composition is identical.
- Required by: DSPs for streaming ingestion; increasingly required by sync buyers on delivered masters; PROs for digital performance matching.

### ISWC (International Standard Musical Work Code)
- Identifies the **musical composition** (not the recording).
- Format: `T-XXXXXXXXX.C` (T prefix, 9 digits, 1 check digit).
- Assigned by: the writer's or publisher's PRO at the time of work registration.
- Scope: one ISWC per composition. Multiple recordings of the same song (covers, re-records, remixes that don't create a new composition) share the same ISWC. A remix that qualitatively changes the composition may be assigned a new ISWC — PRO practice varies.
- Required by: CISAC (the international PRO confederation) for international royalty matching; cue sheet submission for international distribution.

### The ISRC/ISWC disconnect (most common metadata error)
The ISRC and ISWC identify different things. The most frequent sync metadata error is treating them interchangeably:
- A track with an ISRC on the cue sheet but no ISWC means the PRO can identify the recording but may not link it to a registered composition — publishing royalties go uncollected.
- A track with an ISWC on the cue sheet but the wrong ISRC (e.g., a different version was actually used) means the performance-matching systems can't confirm the recording, slowing or blocking collection.
- **The fix:** supply both ISRC and ISWC for every cue sheet entry. Verify the ISRC against the specific file delivered to the production company — not the album master, if a different version was licensed.

### Delivery metadata requirements
Sync buyers increasingly require embedded metadata on delivered files. The minimum standard delivery for a sync submission:
- ISRC embedded in ID3 tags (MP3) or BWF chunk (WAV/AIFF)
- Composer(s), publisher(s), and PRO affiliation in the ID3/BWF metadata
- BPM, key, and instrumentation in the ID3 comments field (for music library delivery)
- Master sample rate ≥48 kHz, bit depth ≥24-bit WAV for the final delivery file (streaming-quality MP3 for pitching; high-res WAV for contract delivery)
- Stems labeled by instrument group: drums / bass / keys+synths / guitars / lead vocal / background vocals (or as applicable). Stem labeling standard varies by buyer class; confirm before delivery.

---

## LAYER 4 — TERRITORY CLEARANCE SPLITS

### When a "worldwide" license is not one negotiation
Many catalog tracks — especially those that were signed in a pre-streaming era — have territorial ownership splits: Label A controls the master in the US and Canada; Label B controls the master in the UK and Europe; Label C controls the master in Japan. A worldwide sync license requires separate clearance from each territorial controller.

**Common split structures:**
- **US/Canada vs. ROW (Rest of World):** The most frequent split in legacy catalog. Two negotiations, two license agreements.
- **US vs. UK vs. EU vs. RoW:** Four-way splits exist for major catalog titles signed in the major-label era of territorial deal-making.
- **Japan:** Often a separate exclusive distribution arrangement regardless of the US structure.

**Practical traps:**
1. **The one-approval assumption:** An artist who controls their US masters may genuinely believe they can approve a worldwide use — and be correct on the US side while having no authority over UK masters. Confirm territorial scope of authority before representing that worldwide clearance is available.
2. **Streaming platform territory:** When a TV show streams globally on a subscription platform, the sync license must cover all territories where the platform operates. A license that only covers North America leaves the rights-holder exposed everywhere else the show is available.
3. **MFN across territorial controllers:** If the EU master controller grants MFN (most-favored-nations) with the US controller, the higher fee agreed with one propagates to the other. In a multi-territory negotiation, price the deal in order: most-expensive territory last.

### Fee structuring for territorial splits
- **Territory-by-territory quoting:** Each territorial controller quotes their own fee. The buyer pays the aggregate. This is transparent but slow.
- **Lead party coordination:** Designate the controller with the most territory as the lead — they negotiate the blanket fee and sub-distribute the territorial shares internally. Requires existing inter-label relationships.
- **Flat worldwide rate:** If the artist controls worldwide rights (post-reversion or original one-stop deal), quote a single worldwide flat fee. The premium for this convenience over multi-territorial negotiation is typically 20–40% — less than the sum of individual territory quotes but more than any single-territory rate.

### Neighboring rights and territory
Neighboring rights (master-side performance royalties from broadcast) accrue per territory based on where the broadcast occurs. A US TV placement generates US-based neighboring rights (SoundExchange for digital; none for terrestrial AM/FM). The same show airing on BBC in the UK generates UK neighboring rights collected by PPL. The collection only happens if:
1. The master is registered with the relevant neighboring rights society.
2. The label (or self-releasing artist via an aggregator) has a membership or mandate agreement with that society.
3. A cue sheet (or equivalent broadcast data) confirms the use.

**The actionable implication:** For any track with international sync potential, register the master with PPL (UK), SoundExchange (US digital), and via a neighboring rights administrator (e.g., AARC, NovaCab, or a major distributor's neighboring rights service) for EU territories before the placement airs. Retroactive collection is possible but materially harder than pre-registration.

---

## LAYER 5 — BACKEND ROYALTY FLOW SUMMARY

### What a placement generates (complete picture)
| Revenue stream | Triggered by | Collected by | Paid to |
|---|---|---|---|
| Sync fee (publishing side) | License agreement | Directly from buyer | Publisher / writer |
| Sync fee (master side) | License agreement | Directly from buyer | Label / artist |
| Publishing performance royalty | Broadcast / stream of licensed content | PRO (ASCAP/BMI via cue sheet) | Publisher (50%) + Writer (50%) |
| Master neighboring rights | Broadcast of licensed content (international / digital) | Neighboring rights societies | Label / featured artist |
| Streaming royalties on the track itself | Fans discover track via placement → stream it | DSPs → Distributor | Label / artist |

**The discovery multiplier:** A well-placed sync drives streaming of the track directly (the "Shazam effect"). Tracks with no streaming footprint before a prominent placement commonly see 10–100x streaming volume in the week after air. Pre-placement metadata hygiene (correct ISRC, registered composition, complete DSP catalog presence) is required to capture this revenue.

### Quarterly audit checklist
- Verify cue sheets filed for all placements in the quarter.
- Cross-check PRO statements against logged cue sheets — missing placements require PRO filing inquiry.
- Confirm ISRC/ISWC accuracy for any track with a new placement.
- Check neighboring rights statements if the track aired internationally.
- Log closed-deal fees against the fee-tier bands for quarterly band recalibration.
