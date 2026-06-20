# PLMKR Audio, Delivery & Creative-Direction Systems

Advanced domain knowledge for PRODUCER-CONNECT: technical delivery standards, the creative-brief discipline, and the technology/AI boundary. PLMKR-owned original. All platform-specific figures (loudness targets, true-peak ceilings, formats, spatial thresholds) are **ESTIMATE / NOT QUOTABLE** — verify against current platform-spec intelligence before any technical assertion. Reasoning frameworks are stable; specific thresholds are not.

---

## Part 1 — Audio Technical Standards & Delivery QC

### A delivery spec is a pass/fail contract

A delivery spec defines the precise technical properties of every file in the package: file format (container/codec), bit depth, sample rate, integrated loudness target, true-peak ceiling, stem naming, metadata fields, and version requirements. A spec is **not a guideline** — delivering a non-conforming file is not partial success, it is a bounce. The spec is maintained by the **recipient** (distributor/platform/label), can change at any time, and is authoritative as the recipient enforces it **today** — not as you learned it on a prior project.

**Target vs. tolerance.** Each item has a target and a tolerance band: pass (within tolerance) / yellow (outside tolerance, small margin — some recipients accept with a note) / red (past the bounce threshold). True-peak and format are binary — no tolerance above the ceiling, no tolerance on codec/bit depth. Target the **center** of the spec, not the tolerance edge.

### Measurement vs. claim (anti-fabrication — hard)

A technical statement is valid only as a **Measurement** ("[value] measured [tool class] on [file]"), a **TARGET** ("TARGET: [value]; verified by [method]"), or an **ESTIMATE** ("~[value]; verify current spec"). Never state a loudness/true-peak value as a measurement without the meter output for that file. "Sounds about as loud as the references" is not a measurement; "the engineer said it was fine" is not a measurement. A fabricated measurement is not a QC pass and underlies the Dim-4 hard gate.

### Loudness, true-peak, format, stems

- **Integrated loudness (LUFS)** is a perceptual average over the full track; platforms **normalize at playback** to a common level. A master louder than target is turned **down** — the loudness investment (heavy limiting, reduced dynamic range) yields no louder result for the listener, only a more compromised master. Deliver at or near the target. *ESTIMATE: streaming ~−14 to −16 LUFS integrated; spatial/immersive ~−18 LUFS; broadcast ~−23 to −24 LUFS — verify current.*
- **True-peak (dBTP)** accounts for inter-sample peaks that clip on playback/transcode even when no sample reaches 0 dBFS — a harder limit than sample-peak. *ESTIMATE: streaming ceiling ~−1.0 to −2.0 dBTP.*
- **Sample rate / bit depth** — deliver 24-bit minimum for mastering handoff at the session's **native** sample rate; **never upsample for delivery** (a 44.1 kHz session exported at 96 kHz is detected and flagged). 32-bit float is internal only.
- **File format** — deliver lossless (WAV/AIFF) for every production handoff and distribution master; the platform generates consumer-format encodes from the lossless master. **Never use a lossy file as source** for any further processing — lossy artifacts compound and cannot be removed.
- **Stems** are built **from the open mix session, not retroactively from the master**; the stem spec (set, naming, format) must be confirmed at mix handoff. A stem package passes only when stems **sum** to the stereo mix. Mis-named or missing stems fail both Dim-4 and Dim-6.

**Alternate versions** (instrumental, radio edit, clean) are each a **separate deliverable with separate QC** — own loudness, true-peak, format, and identifier. Edit clean versions on the vocal track before mastering, not by silencing words in the master.

**Dithering** is applied **exactly once**, at the final bit-depth reduction (e.g., 24→16-bit); for 24-bit delivery it is not required. Stacked dither (mix bounce **and** mastering) raises the noise floor — confirm one party applies it.

**Identifiers & metadata.** Each discrete deliverable needs its own **ISRC** (clean ≠ explicit ISRC); embed it in the file's metadata at mastering. Core metadata (title, artist, featured, release date, genre, songwriter/composer, producer/mixer/master credits, P-line = master owner, C-line = composition owner, explicit flag) must be complete and verified — a wrong identifier or flag propagates to every platform and is expensive to correct after the fact. Missing identifier or incomplete core metadata triggers the Dim-6 gate.

**Mono compatibility & headroom** are Dim-4 mix-accept screen items: check the mix in mono for phase cancellation (lead vocal, bass, widened elements), keep low-end in the mono sum, and hand off to mastering with headroom (mix-bus peaks ~−3 to −6 dBFS, integrated ~−14 to −18 LUFS, true-peak below ~−3 dBTP — ESTIMATE; confirm with the engineer). **Never "hit mastering hot"** — a pre-limited mix gives the mastering engineer no dynamic range to work with and produces a more compromised master, not a louder one.

### The four-layer QC model

Creative approval (producer/artist, by ear) is **not** technical QC. A technical pass requires measurement against the recipient's external spec. Layers: creative approval → mix-stage technical screen (clipping, mono, headroom) → mastering QC (loudness, true-peak, format, identifier) → distributor/platform QC (full spec, metadata, versions). Document the **instrument type and algorithm** in the QC log — not playback through monitors.

---

## Part 2 — Creative Direction & References

### The brief is the cheapest insurance in production

A creative brief is a **written agreement** between artist, producer, and anyone whose work determines the final sound — specific enough that the team makes decisions independently without re-adjudicating with the artist mid-session. A brief is **not** a mood word ("dark, cinematic"), a genre label alone, a recalled conversation, or an unannotated playlist.

**"I'll know it when I hear it"** is the most expensive phrase in a recording budget — it defers the brief into the revision process, where it gets written from what the artist rejects at four-to-ten times the cost of writing it before tracking. The brief does not constrain creative discovery; it channels it within a defined territory so discoveries are additive, and makes "this is better than what we planned" legible by defining what was planned.

### Reference tracks as objective language

A sonic adjective is heard differently by every listener; a reference track heard on the same system has a single shared reality. Cite every reference with three elements: **artist + track title**, the **specific sonic element** targeted, and the **direction** (positive / rejection / partial). A reference is a direction signal, not a replication target — the goal is to inhabit a sonic territory, never to copy a specific master.

**Translate subjective taste** by asking "which reference makes you feel that?" then "what specifically about it?" — converting "big," "intimate," "modern," "hits hard" into a named track + named element. The translation stops where the artist can no longer add specificity; that boundary is what is knowable before the session.

**Five brief components:** (1) ≥3 annotated references, (2) sonic territory (genre, sub-genre, era), (3) arrangement intent (tempo range, key vs. the vocalist's range, instrumentation palette, structure), (4) dynamic/loudness **character** (an arrangement/mix target — *not* a LUFS instruction; perceived energy comes from arrangement density and transient treatment, which survive normalization), and (5) emotional/narrative territory. The brief is owned jointly and **signed by both** before tracking dates are booked — the production equivalent of the technical delivery gate.

**A/B the demo against the references** at matched playback levels with fast switching, annotating departures by dimension (vocal level, low-end, reverb, density, dynamic contrast, tonal balance). An unacknowledged departure that reaches the mix is a creative decision made without authority — the A/B surfaces it at the demo stage, when it is cheapest to resolve. A documented A/B is the best observed evidence for a Dim-1 score above 7.

---

## Part 3 — Production Technology & AI

### The three-prong adoption test

Before adopting any tool, ask only: **does it serve the master?** It must pass at least one of — **quality improvement** (a demonstrably better result toward the sonic target, not just different), **efficiency gain** (real, repeatable time/cost reduction with no quality penalty), or **capability extension** (something otherwise unachievable that the project requires). A tool that passes none is novelty, and novelty has a cost (adoption time, workflow disruption, reproducibility risk) with no return. Adopt within the scope of the prong it passes; expanding scope re-triggers the test.

### Reproducibility is a production asset

A session that cannot be recalled cannot be revised — and revision rights (label notes, artist approvals, sync adaptations, format variations) are often contractual. Full recall requires **signal chain** (hardware settings photographed/transcribed at session end), **creative state** (named, versioned snapshots per deliverable, e.g. `MIX-APPROVAL-2026-06-18`), and **external dependencies** (plugin versions, sample paths). The most common partial-irreproducibility is the analog hardware boundary — settings cannot be recalled from a project file; documenting them costs minutes and prevents full re-work.

### The human-judgment / automation boundary

Automation is appropriate where there is an **objective, verifiable standard** (format conversion, loudness normalization to a target, file renaming, metadata population, sample-rate conversion). **Human judgment** is required for any **aesthetic** evaluation (vocal emotional quality, mix-bus compression character, transition smoothness). Between them is tool-assisted judgment (tuning, quantization, AI-mastering reference, stem separation) — legitimate, but the failure is when the tool's **default becomes the decision** and the engineer stops evaluating.

### AI tools — scope and boundaries

- **AI generation** (beats, melodies, full sketches) — a starting point for fast exploration and structural sketches, **not** finished elements without substantial human curation. **Rights/ownership are a live legal question** — flag to A&R, Publishing, and legal before committing to a release; Beat does not make the rights call.
- **AI workflow assistance** (mix/arrangement suggestions, stem enhancement) — input to human judgment, not directives; evaluate each suggestion against the sonic target like any A/B.
- **Automated mastering** — appropriate for demos, budget-constrained projects, and quick-turn content; **not** a substitute for a human mastering engineer on commercial releases where mastering quality is a competitive factor (it delivers loudness normalization and broad tonal adjustment — a subset of a mastering engineer's value, and no platform-specific judgment).
- **Pitch correction / timing** — standard tools; the **extent** (transparent / stylized / pervasive) is a creative-direction call requiring the artist's consent, not an engineering default. Heavily processing a performance without the artist's knowledge is not serving them.

### Stem separation — uses and hard limits

Legitimate for remix without multitracks, sample isolation, and forensic/arrangement analysis — but it is a **lossy, artifact-introducing** process (frequency bleed, transient degradation, reverb loss, phase anomalies). Separated stems are **not** a substitute for original multitracks; using them as if they were caps the project's quality at the separation quality. When multitracks exist, use them; when they don't, acknowledge the quality ceiling against the project's requirements.

### In-the-box vs. analog/hybrid

Not a quality hierarchy — a set of tradeoffs. **ITB** gives total recall, lower cost, and frictionless collaboration; its ceiling is the software, which has narrowed but not closed the analog harmonic-character gap. **Analog/hybrid** adds harmonic character at the cost of recall complexity, conversion-stage management, and hardware documentation. The best hybrid sessions use analog only where it is sonically significant and default to ITB elsewhere; the worst accept the recall cost without the gain. **Remote production:** the real-time stream is for communication only — the production audio comes from a high-quality **local capture** at the remote location, verified on receipt, under strict file-naming/version discipline.
