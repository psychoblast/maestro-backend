# DSP Delivery Specifications & Quality Control

## Currency Warning (Read Before Using This File)

Platform audio specs, artwork requirements, metadata field requirements, and lead
times change frequently and without notice. Every specification in this file is a
starting reference, not a current fact. Verify against the platform's current
developer/delivery documentation and the distributor's documentation before any
delivery. State the verification date with any spec you communicate.

## 1. Universal Delivery Requirements

These apply to virtually all major platforms; individual platforms may have higher
requirements.

**Audio:**
- Format: WAV (preferred) or FLAC. Lossy formats are generally rejected for
  ingestion — they are what platforms generate internally, not accept as input.
- Bit depth: 16-bit minimum; 24-bit preferred where hi-res tiers accept it.
- Sample rate: 44.1 kHz minimum; higher rates accepted by hi-res tiers; standard
  delivery is 44.1 kHz.
- Loudness: integrated-loudness normalization targets vary by platform (commonly in
  the −14 to −16 LUFS range). Louder files are turned down; quieter files are
  turned up. Over-limiting during mastering to "beat" normalization is a common
  practitioner error. Verify current targets before mastering.
- Duration: no universal maximum; very long files may need special handling.

**Artwork:**
- Minimum dimensions: commonly 3000×3000 px square — verify current minimum.
- Maximum file size: typically capped (often ≤25 MB); varies by distributor and
  platform.
- Colorspace: RGB only. Print-intended CMYK artwork displays incorrectly and may be
  rejected.
- Format: JPEG (preferred) or PNG; other formats rarely accepted.
- Embedded text/promotional elements: prohibited in the primary artwork for many
  submission types (no website addresses, social handles, or "out now" text).
- Explicit imagery: requires correct explicit-rating metadata; some platforms
  reject non-rated explicit artwork.

**Metadata:**
- UTF-8 encoding for all fields.
- ISO 8601 release dates.
- ISO 639 language codes for title/lyrics.

## 2. Platform Comparison (Reference Only — Verify Before Delivery)

| Requirement | Streaming-standard platforms | Hi-res / lossless tiers |
|-------------|------------------------------|--------------------------|
| Audio format accepted | WAV, FLAC (some accept AIFF) | WAV, FLAC |
| Minimum bit depth | 16-bit | 16-bit standard; 24-bit for hi-res |
| Sample rate | 44.1 kHz | 44.1 kHz up to high rates for hi-res |
| Artwork minimum | square, high-resolution (commonly 3000×3000) | same |
| Artwork colorspace | RGB | RGB |
| ISRC required | Yes | Yes |
| UPC required | Yes | Yes |
| Explicit tag | Required if applicable | Required if applicable |
| Lyrics | via partnership/portal | optional embed |

Treat every cell as a starting reference. Confirm the exact requirement for the
specific platform and the specific release with current documentation; note the
verification date.

## 3. Delivery vs. Editorial Timeline (Two Different Clocks)

**Standard delivery (music goes live):**
- Distributor processing: commonly 1–3 business days after submission.
- Platform processing after receipt: commonly 24–72 hours for major platforms.
- Total minimum submission-to-live: roughly 3–7 business days for major platforms
  (conservative; varies by distributor and platform load).

**Editorial pitch eligibility (required for editorial-playlist consideration):**
- The leading streaming platform has a documented minimum lead time to submit a
  track for editorial consideration; the widely recommended best practice is
  substantially earlier (multiple weeks) because earlier submissions get more
  consideration time. The minimum is the platform floor, not the operational
  recommendation.
- Other platforms manage editorial submission through distributor relationships or
  dedicated emerging-artist programs; multiple weeks of lead time is generally
  recommended.

**Practical implication — the most common timeline error:** conflating "enough time
to deliver" (a few business days) with "enough time for editorial consideration"
(weeks). A release scheduled a few weeks out may be live in time but already past
the editorial pitch window. The track must be delivered to and processed by the
distributor *before* the pitch window opens.

**Pre-save / pre-order timing:** pre-save links typically activate once the release
is in the platform's system with a future release date; pre-add setups generally
require delivery a couple of weeks before release. Verify current requirements.

## 4. Rejection Cause Taxonomy

Ranked from most to least common (practitioner estimate — no public per-category
rejection-rate data):

1. **Metadata errors (most frequent):** missing mandatory field; invalid ISRC
   format; ISRC conflict; non-UTF-8 characters; release date in the past without an
   explicit past-release delivery type.
2. **Artwork specification violations:** below minimum dimensions (often a
   scaled-up low-resolution image); wrong colorspace (CMYK); prohibited text or
   promotional elements; file size over limit; background issues where an opaque
   background is required.
3. **Audio format failures (less frequent, higher cost):** wrong format; bit depth
   too low; corrupted file; loudness far out of range (rarely a hard rejection —
   usually normalized silently).
4. **Content policy violations (case-by-case):** explicit content without the flag;
   prohibited title content; prohibited artwork imagery not flagged; duplicate-
   release conflict.

Anti-pattern: resubmitting a rejected delivery without diagnosing the cause. A
rejection without an identified root cause will repeat. Every rejection requires a
specific identified reason before resubmission.

## 5. Pre-Delivery QC Checklist

A systematic check before submission prevents the majority of rejection-causing
errors.

**Audio QC:**
- [ ] Format: WAV or FLAC (not a lossy or unsupported format)
- [ ] Bit depth: 16-bit minimum (confirm in file properties / DAW export settings)
- [ ] Sample rate: 44.1 kHz minimum (confirm in file properties)
- [ ] No clipping: integrated loudness measured; true peak within a safe margin
- [ ] No excessive leading silence (DSPs trim or reject long leading silence)
- [ ] No unintended trailing silence (track length matches intended duration)
- [ ] Correct number of tracks delivered (matches the metadata track count)
- [ ] Files correctly named and ordered

**Artwork QC:**
- [ ] Dimensions meet the current minimum (check pixel dimensions, not file size)
- [ ] Colorspace: RGB (not CMYK — check in image software)
- [ ] File size within the platform limit
- [ ] No prohibited text or promotional elements
- [ ] Correct artwork associated with the correct release (not a placeholder/draft)

**Metadata QC:**
- [ ] ISRC present and correctly formatted for every track
- [ ] UPC/EAN present and correctly formatted
- [ ] Track title matches the final recording (not "Demo" or "Rough Mix")
- [ ] Primary artist name consistent with existing platform presence
- [ ] Release date correct and in ISO 8601 format
- [ ] At least one genre assigned
- [ ] Territory availability configured to match the rights position
- [ ] Explicit flag set correctly (or absent if not applicable)
- [ ] Language code for title/lyrics set
- [ ] Production-rights and copyright lines present and correct

**Practitioner insight:** the QC checklist is most valuable as an institutionalized
process, not a one-time list. Every recurring error that makes it past QC should
add a new explicit check at the category where the error occurred. Over time the
checklist captures the real failure modes of that specific label's workflow — which
differ from every other label's.

## Domain Anti-Patterns

- Submitting CMYK (print) artwork to digital platforms.
- Resubmitting a rejected delivery without diagnosing the rejection.
- Treating delivery lead time as if it were the editorial pitch window.
- Over-limiting a master to compensate for loudness normalization.
- Stating a platform spec without a source and verification date.
