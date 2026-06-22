# Audio Mastering & Loudness Standards for Digital Delivery

## Currency Warning

Loudness targets, normalization implementations, format acceptance rules, and
hi-res tier requirements change on platform timelines. Every specific value below
is a reference point — verify against current platform documentation before
advising on mastering targets or delivery specifications.

## 1. Loudness Normalization — Core Mechanics

**What loudness normalization is:**
Every major streaming platform measures the integrated loudness of a delivered audio
file on ingest and normalizes playback to a target loudness level. The measurement
standard is the ITU-R BS.1770 algorithm, and the unit is LUFS (Loudness Units
relative to Full Scale) — also written LKFS (Loudness K-weighted, Full Scale). The
two units are numerically identical.

**How it works in practice:**
- The platform measures integrated LUFS of the delivered file.
- If the file is louder than the target (e.g., −11 LUFS vs. a −14 LUFS target), the
  platform turns the playback level *down* to reach the target.
- If the file is quieter than the target (e.g., −18 LUFS vs. a −14 LUFS target),
  the platform may turn playback *up* — behavior varies by platform; some platforms
  only normalize down, not up.
- The delivered file is not altered — normalization is applied at the playback layer
  only.

**Reference loudness targets by platform (illustrative — verify before use):**

| Platform | Reference target | Applies to |
|----------|-----------------|------------|
| Spotify | −14 LUFS | All tiers |
| Apple Music | −16 LUFS (Sound Check) | When Sound Check is enabled |
| YouTube | −14 LUFS (integrated) | Music and video |
| Amazon Music | −14 LUFS | Standard tier |
| Tidal | −14 LUFS | All tiers |
| Deezer | −15 LUFS | All tiers |

Note: Apple Music's Sound Check can be disabled by the listener. Files are also
played at the delivered loudness by listeners with normalization disabled — the most
common scenario on high-end listening setups. For Apple Music, −16 LUFS is the
normalization target, but many practitioners recommend mastering at a more moderate
−14 to −13 LUFS to sound competitive on systems where normalization is off.

## 2. True Peak Limits

**True peak (dBTP)** measures the peak level of the audio signal between samples
after digital-to-analog conversion — a more accurate peak measurement than standard
sample-peak dBFS, because inter-sample peaks can exceed 0 dBFS even when individual
samples do not.

**Standard true-peak limit: −1 dBTP** (widely recommended; some platforms enforce
−2 dBTP as their limit). Exceeding the true-peak limit:
- Can cause clipping in certain playback contexts (especially compressed/transcoded
  copies of the file, which the platform generates for delivery to different
  connection speeds and devices).
- May trigger a rejection or a "loudness concern" flag from the distributor.
- Is most common in masters that clip near 0 dBFS and were not checked with a
  true-peak-aware limiter.

**Measurement tool requirement:** true peak measurement requires a meter that
implements the ITU-R BS.1770 standard. Standard peak meters in most DAWs do not
measure true peak — they measure sample peak, which will not detect inter-sample
peaks. A true-peak-compliant limiter (and a true-peak meter in the mastering chain)
is an operational requirement, not a preference.

## 3. Why Over-Limiting Is a Practitioner Error

**The over-limiting trap:**
A mastering engineer or label owner who believes louder masters will "win" on
streaming platforms applies heavy limiting to achieve a high integrated LUFS (e.g.,
−8 LUFS). The platform then turns the master *down* to its target (e.g., −14 LUFS)
— a 6 LUFS downward gain reduction.

The result: the listener hears a louder-than-intended master that has been digitally
compressed, then turned down — with reduced dynamic range, transient detail, and
stereo width compared to what a properly-mastered −14 LUFS master would have
delivered at the same playback level.

An appropriately mastered −14 LUFS file and a heavily limited −8 LUFS file both play
back at −14 LUFS after normalization — but the properly mastered file has 6 dB more
headroom, better transient response, and more stereo imaging. The over-limited file
costs dynamic range without gaining loudness.

**Digital-ops consequence:**
- Over-limited masters are not a delivery error — they pass QC and deliver
  successfully.
- They are a quality error with no technical rejection signal.
- The correct advice to a client whose master sounds crushed on streaming platforms:
  the issue is the master, not the delivery. Remasters can be redelivered with a
  metadata-only or audio-file update depending on the distributor.

## 4. Dynamic Range and DR Ratings

**Dynamic range (DR)** measures the crest factor — the difference between the peak
level and the RMS (average) level of the audio. Higher DR = more peak-to-average
contrast = perceived punch and dynamics. Heavy limiting reduces DR.

**DR ratings** (from the TT Dynamic Range database framework, a widely used reference):
- DR > 14: high dynamic range (common in classical, acoustic, early catalog)
- DR 8–13: moderate (acceptable for most modern genres)
- DR 6–7: limited (common in heavily compressed modern pop/rock masters)
- DR < 6: hyper-limited (audible pumping and fatigue artifacts common)

**Digital-ops relevance:** DR ratings are not a delivery specification — no platform
requires a minimum DR. But when a master is criticized for sounding poor on streaming
platforms, the DR rating is one of the first diagnostic data points. A DR4 master is
not a delivery problem; it is a mastering problem that cannot be resolved without
a new master.

## 5. Hi-Res and Lossless Delivery Tiers

**What hi-res delivery is:**
Standard digital audio delivery is 16-bit/44.1 kHz (CD quality). Hi-res delivery
means delivering audio at higher bit depth (24-bit) and/or higher sample rates
(48, 88.2, 96, 176.4, or 192 kHz). The platforms that support hi-res use the
higher-resolution file for their lossless and hi-res lossless tiers.

**Platform hi-res tiers (illustrative — verify current availability):**

| Platform | Hi-res tier | Format accepted for delivery | Output to listener |
|----------|------------|------------------------------|-------------------|
| Apple Music | Lossless (ALAC) | WAV or FLAC up to 24-bit/192 kHz | ALAC at matching or lower resolution |
| Apple Music | Hi-Res Lossless | WAV or FLAC 24-bit/192 kHz preferred | ALAC 24-bit/192 kHz |
| Tidal | HiFi/Master | FLAC 24-bit/96 kHz | FLAC or MQA |
| Amazon Music | HD / Ultra HD | WAV or FLAC 24-bit/192 kHz | FLAC at matching resolution |
| Qobuz | Studio / Sublime | FLAC 24-bit/192 kHz | FLAC at delivery resolution |

**Delivery logistics:**
- Most distributors accept a single WAV or FLAC file per track and generate lossless
  and hi-res versions internally; a few require separate hi-res file delivery.
- For platforms with a hi-res tier, the standard 16-bit/44.1 kHz file is accepted and
  delivered to all tiers; a hi-res source file enables hi-res playback on the hi-res
  tiers.
- Upsampling a 16-bit/44.1 kHz master to 24-bit/192 kHz does not create hi-res content
  — it creates a larger file with identical audio content. Upload the original high-
  resolution source; if it does not exist, deliver the standard-resolution master.

**When hi-res delivery matters operationally:**
- Catalog recorded at 24-bit and archived correctly should be delivered at 24-bit —
  the source information is available and its absence at delivery is a revenue and
  quality gap.
- Catalog originally recorded at 16-bit/44.1 kHz does not benefit from upsampled
  delivery.
- New recordings at a label with a commercially active audience on hi-res platforms
  should be tracked, mixed, and mastered at 24-bit to enable hi-res delivery.

## 6. Spatial Audio (Dolby Atmos)

**What it is:**
Dolby Atmos is an object-based spatial audio format that delivers music as a
three-dimensional mix (height channels included, not just left-right stereo).
Listeners on compatible devices (AirPods with Apple Music, headphones with supported
apps) experience an immersive, headphone-based spatial rendering.

**Platform support:**
Apple Music, Tidal, and Amazon Music HD support Dolby Atmos delivery.

**Delivery requirements (illustrative — verify with distributor before delivery):**
- A separate Dolby Atmos mix from the mixing engineer, rendered in Atmos format.
- Typically delivered as an ADM BWF (Audio Definition Model Broadcast Wave Format)
  file — a multi-channel mix file with the spatial metadata embedded.
- The Atmos mix is a separate deliverable from the stereo master; both are needed.
- Not all distributors accept Atmos delivery; confirm before commissioning a mix.

**Operational reality:**
- The spatial audio mix must be commissioned from a mixing engineer with Dolby
  Atmos certification or from a studio with an Atmos suite. It is a separate
  creative and production cost.
- An Atmos mix has its own loudness target (typically −18 LUFS integrated for the
  immersive mix) — distinct from the stereo target.
- Delivery timeline: Atmos delivery adds distributor-processing time; budget
  additional lead time.

**When spatial audio matters operationally:**
- Major-label catalog releases and artist albums with above-average Apple Music or
  Tidal audience share benefit most — these platforms' hi-res subscribers are the
  primary audience.
- For catalog with strong Apple Music metrics and without an Atmos mix, commissioning
  a spatial audio version is a catalog-enhancement option with a one-time cost.

## 7. Audio Format Acceptance — Common Errors

| Error | Cause | Consequence | Remediation |
|-------|-------|-------------|-------------|
| Delivering a 320 kbps MP3 | Treating the end format as the deliverable | Rejection or downgraded quality (if accepted, the platform transcodes from a lossy source) | Deliver WAV or FLAC from the original session |
| Sample-rate mismatch | Exporting at 48 kHz instead of 44.1 kHz | May pass; some platforms transcode; quality loss possible | Re-export at 44.1 kHz from the original session |
| Bit-depth downgrade | Exporting 24-bit session at 16-bit with dithering not applied | Dithering noise artifacts audible in quiet passages | Re-export with proper 16-bit dithering; or deliver 24-bit where accepted |
| Upsampled hi-res delivery | Converting 16-bit/44.1 kHz to 24-bit/192 kHz | Larger file size with no quality gain; editorial teams at platforms recognize this | Deliver the true-resolution source |
| Missing dithering | Bit depth reduction without dithering | Quantization noise in quiet passages | Re-export with TPDF dithering at the bit-depth conversion step |
| Clipped render | Output level exceeding 0 dBFS during bounce | Audible digital clipping; may or may not trigger rejection | Identify and fix the clipping source; re-render |

## 8. Loudness and Format in the Pre-Delivery QC Checklist

This section extends the pre-delivery QC checklist from dsp-delivery-and-qc.md with
loudness and format specifics:

**Audio loudness/format QC:**
- [ ] Measure integrated LUFS with a BS.1770-compliant meter — note the value
- [ ] Confirm integrated LUFS is in the appropriate range for the target platforms
      (commonly −14 to −10 LUFS for normalization-era delivery)
- [ ] Measure true peak with a TP-compliant limiter/meter — confirm ≤ −1 dBTP
- [ ] Confirm bit depth: 16-bit minimum; 24-bit if source supports it
- [ ] Confirm sample rate: 44.1 kHz minimum; original session rate preferred
- [ ] No clipping anywhere in the file (visual waveform check + limiter)
- [ ] No unintended DC offset
- [ ] Stereo correlation positive (no phase inversion issues that collapse in mono)
- [ ] Mono compatibility check (some playback contexts are mono — AirPlay, some smart
      speakers)

**Practitioner insight:** a single-pass listening QC on a DAW speaker at normal
volume will miss most of the format and loudness issues in this checklist. The QC
must be meter-based — LUFS measurement, true-peak check, and a spectrum analyzer for
the render. Ears are for the mix; meters are for delivery compliance.

## Domain Anti-Patterns

- Over-limiting a master to achieve a higher delivery LUFS, then delivering a
  dynamically compromised file that platforms turn down to the normalization target.
- Upsampling a standard-resolution master to 24-bit/192 kHz and presenting it as
  hi-res delivery.
- Assuming that if a file passes the distributor's portal upload, its loudness and
  format are within spec — the portal checks format, not optimal loudness.
- Measuring only sample peak (dBFS) rather than true peak (dBTP) and missing
  inter-sample peaks that cause clipping in transcoded delivery files.
- Treating the stereo master as the spatial audio deliverable — Atmos is a separate
  mix requiring separate production.
- Stating a specific loudness target as fact without a verification date.
