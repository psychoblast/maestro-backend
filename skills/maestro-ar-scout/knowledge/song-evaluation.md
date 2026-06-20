# PLMKR A&R — Song & Repertoire Evaluation
Version: v1.0 — 2026-06-19

---

## GENERAL FRAMEWORKS

### The Three-Axis Evaluation Model

Every song is assessed on three independent axes. These are separate assessments — conflation produces bad decisions.

**Axis 1 — Commercial Viability**
Does this fit a lane that platforms, audiences, and buyers currently reward? This axis depends on format, market context, and current platform behavior, not personal aesthetic preference.
- Assessed by: tempo, loudness profile, structure, duration, current genre/format data
- Judgment type: reasoned from facts + market data
- Principal risk: market timing miscall; genre cycle reversal

**Axis 2 — Artistic Distinctiveness**
Is there a hook, an angle, an artist identity marker that makes this not interchangeable with the thousand other tracks in the same lane?
- Assessed by: unique sonic signature, hook memorability (qualitative assessment, labeled as such), lyric specificity, production identity
- Judgment type: ears-based, confidence-tagged, explicitly labeled as subjective assessment
- Principal risk: A&R personal taste bias masquerading as objective distinctiveness assessment

**Axis 3 — Readiness**
Is the recording, metadata, and release infrastructure actually launch-ready?
- Assessed by: audio delivery specs, loudness profile against DSP normalisation targets, metadata completeness, structural flags (intro length vs. streaming retention benchmarks)
- Judgment type: objective — either specs are met or they are not
- Principal risk: erroneously treating as a quality judgment what is a delivery-technical judgment

**Ceiling assignment** is derived from the combination of all three axes. Axis 1 primarily drives the ceiling tier; Axes 2 and 3 modify it.

### Commercial Ceiling Tier Taxonomy

| Tier | Label | Meaning | Strategy implication |
|------|-------|---------|---------------------|
| 1 | **Fan-development release** | Strengthens existing audience; not an editorial play; algorithmic upside is limited by genre fit or format constraints | Single-to-audience strategy; no editorial pitch; social/community focus |
| 2 | **Emerging-playlist candidate** | Fits smaller editorial/algorithmic lanes if listener signals are strong; ceiling on major editorial consideration without a breakthrough catalyst | Pitch to genre editorial playlists; algorithmic optimization focus; influencer/creator seeding for signal generation |
| 3 | **Editorial target** | Genuinely competitive for major editorial consideration — specific playlist families identified; format, timing, and pitch quality become the differentiating variables | Full editorial pitch campaign; DSP relations engagement; timing-optimized release |
| 4 | **Radio/crossover viable** | Broad commercial reach potential; format-ready; requires radio promotion investment to activate | Radio promo campaign; sync pipeline consideration; national PR |

**Most independent tracks are Tier 1 or Tier 2. Assigning Tier 3 or 4 requires explicit supporting evidence from market data, not enthusiasm.**

**Decision rule:** when evidence supports two adjacent tiers, assign the conservative one and name the specific catalyst that would move it to the higher tier.

### The Grounding Principle for Audio Assessment

Every technical claim about a recording must trace to a measured audio fact. Self-reported or AI-generated mood labels, genre tags, and energy descriptors are hypotheses, not measurements. The governing hierarchy:

1. **Measured audio facts** (BPM, key, LUFS, duration, energy shape/structure timestamps, crest factor, dynamic range, stereo width) — treat as truth
2. **Derived assessments** (intro timing vs. 15-second retention benchmark, loudness vs. DSP normalisation targets, BPM vs. genre tempo norms) — reasoned from measured facts, labeled as derived
3. **Qualitative assessments** (hook memorability, lyric specificity, sonic identity) — labeled as qualitative/ears-based, confidence-tagged
4. **Mood and feel labels** — never trusted as measurements; at most, one input to qualitative assessment

**The LUFS rule:** LUFS is the real loudness signal. For reference, streaming platforms normalise playback (Spotify ≈ −14 LUFS integrated, Apple Music ≈ −16 via Sound Check). A master much louder than −14 (e.g. −9 to −11) is not "intimate" or "low energy" — it is loud, limited, and will be turned down on playback, losing dynamic punch. Never characterize a loud master as sparse or ambient because another data field suggests it; LUFS governs.

### Structural Evaluation Frameworks

**Intro Length and Streaming Retention:**
The 15-second window is the streaming listener's standard decision point (documented across multiple DSP behavioral analyses). Tracks with intro lengths exceeding 15 seconds before the hook or first vocal face a structurally elevated skip risk on cold-listener streams. This is a readiness/format assessment, not an artistic judgment.

- Intro ≤10 seconds before hook/vocal: low skip risk
- Intro 10–15 seconds: moderate; acceptable for many formats
- Intro 15–22 seconds: elevated skip risk for editorial pitches; material concern
- Intro >22 seconds: high skip risk; likely requires edit or arrangement revision before streaming pitch

**Genre-dependency of intro thresholds:**

| Format | Intro threshold | Notes |
|--------|----------------|-------|
| Pop/CHR, R&B, Hip-hop | 15s hard — flag anything over | Elevated skip risk begins here |
| K-pop | 8–12s — stricter norm | Title tracks typically hook in first 10s |
| Electronic/Dance | Genre-based — up to 32–64 bars (1:00+) for club formats | Apply streaming edit standard for DSP release: intro ≤20s for streaming cut |
| Rock/Alternative | Up to 20s more acceptable | Flag beyond 25s |
| Country | 10–15s — similar to pop standard | Country radio formats are format-disciplined |
| Afrobeats | 10–20s | Groove-first structure means slightly longer acceptable; evaluate by momentum, not stopwatch alone |

---

## SONG EVALUATION CHECKLIST

### Axis 1 — Commercial Viability

**Format fit:**
- [ ] Duration: confirm track duration vs. current format norms (pop/R&B: 2:30–3:30 sweet spot; longer requires exceptional content to hold listeners past the 3-minute mark)
- [ ] BPM: confirm BPM vs. active editorial categories in the genre (document the BPM, do not assume)
- [ ] Structure: verse-chorus-verse-chorus-bridge-chorus or identifiable equivalent; note any structural anomalies that reduce format fit
- [ ] Loudness profile: integrated LUFS vs. DSP normalisation targets (Spotify −14 / Apple −16); document the actual measured value

**Market context:**
- [ ] Genre identification: name the specific genre and subgenre
- [ ] Genre trajectory: is this genre growing or contracting in listener share over the last 12 months? (Document source; do not estimate)
- [ ] Competitive comparable: name 2–3 comparable tracks currently charting/receiving editorial attention in the same lane (SOURCED; do not fabricate comparables)
- [ ] Timing assessment: is there a scheduling advantage or disadvantage to releasing this track now?

### Axis 2 — Artistic Distinctiveness

**Hook assessment:**
- [ ] Hook timing: when does the hook arrive (seconds from track start)? Compare to streaming retention benchmarks for the format
- [ ] Hook memorability: would someone hum this hook after one listen? (JUDGED; label as such)
- [ ] Hook singularity: is the hook phrase unique, or is it a construction found in multiple existing tracks?

**Lyric assessment:**
- [ ] Lyric specificity: does the lyric use specific, ownable imagery, or does it rely on genre clichés?
- [ ] Lyric perspective: is there a clear first-person POV that makes this lyric identifiable?
- [ ] Quotable line: is there a single line a listener might reference to a friend?

**Production identity:**
- [ ] Sonic signature: is the production identifiable as this artist's sound, or is it genre-standard?
- [ ] Production quality: LUFS, crest factor, stereo width (MEASURED; document values)
- [ ] Mix quality: is the vocal buried, balanced, or prominent? Is the low end appropriate for the format?

**Artist identity integration:**
- [ ] Does the song reinforce or contradict the artist's established identity?
- [ ] Is the vocal delivery consistent with the artist's identity (authentic) or does it feel imitative?

### Axis 3 — Readiness

**Audio delivery:**
- [ ] Bit depth and sample rate: standard delivery (24-bit / 44.1kHz or 48kHz minimum for DSP submission)
- [ ] Loudness: integrated LUFS measured and within acceptable range (not over-limited)
- [ ] True peak: below −1dBTP to prevent clipping on playback
- [ ] Stereo/mono compatibility: check sum-to-mono for phase issues

**Metadata readiness:**
- [ ] Artist name (as credited — confirm spelling and format)
- [ ] Track title (final version — confirm no demo/version label in title)
- [ ] ISRC: assigned at distribution — not required to be embedded in the audio file (this is the normal state; do not flag absent ISRC in audio file as a problem)
- [ ] Composer and publisher credits: confirm royalty registration plan before distribution
- [ ] Genre and mood tags: confirm correct genre classification for DSP submission

**Release infrastructure:**
- [ ] Cover art: correct dimensions (3000×3000px minimum), correct file format, appropriate for platform guidelines
- [ ] Distribution: distributor selected and account ready
- [ ] Release date: set with adequate advance notice for editorial pitch (minimum 3–4 weeks for Spotify consideration; 6+ weeks preferred for major editorial)
- [ ] Marketing plan: is there a launch strategy or is this a passive release?

---

## OUTPUT TEMPLATE — SONG EVALUATION REPORT

```
## Song Evaluation Report — [Track Title] by [Artist Name]
Date: [YYYY-MM-DD]
Evaluator context: [what materials were available — audio file, link, metadata, none]

---

### Axis 1 — Commercial Viability
- Genre: [specific genre + subgenre]
- Duration: [X:XX] — [Format fit note]
- BPM: [measured value] — [Format fit note]
- LUFS (integrated): [measured value] — [DSP normalisation note]
- Intro to hook/vocal: [X seconds] — [Skip risk classification]
- Genre trajectory: [growing / contracting / stable — source cited]
- Commercial ceiling tier: [1 / 2 / 3 / 4 — with brief rationale]
- Comparable tracks: [2–3 named comparables with brief note]

**Axis 1 assessment:** [1–2 sentences. State ceiling and limiting factor if below Tier 3.]

---

### Axis 2 — Artistic Distinctiveness
- Hook timing: [X seconds]
- Hook memorability: [JUDGED — High / Medium / Low + brief reason]
- Lyric specificity: [JUDGED — Specific / Generic + example from lyric if available]
- Sonic signature: [JUDGED — Distinctive / Generic + brief reason]
- Artist identity integration: [Reinforces / Contradicts / Neutral]

**Axis 2 assessment:** [1–2 sentences. Name the strongest and weakest distinctiveness element.]

---

### Axis 3 — Readiness
- Audio delivery: [PASS / ISSUES NOTED — list specific items]
- Metadata readiness: [PASS / INCOMPLETE — list missing items]
- Release infrastructure: [READY / GAPS IDENTIFIED — list gaps]

**Axis 3 assessment:** [1 sentence. Is this track release-ready as submitted?]

---

### Ceiling Assignment
**Tier [1/2/3/4] — [Label]**
[1–2 sentences: ceiling derived from Axis 1, modified by Axes 2 and 3. Name the specific catalyst that would move this to the next tier if applicable.]

### Remediation Priority (if applicable)
1. [Most impactful fix — with specific, actionable instruction]
2. [Second priority]
3. [Third priority]

[If Tier 3 or Tier 4 assigned: state the explicit market evidence that supports this assignment. "This sounds like an editorial track" is not evidence.]
```
