# Release Planning & Workflow

The release campaign is built backward from the target release date, never forward
from "when we're ready." Working forward creates deadline compression that
degrades campaign quality.

## Release Types Taxonomy

| Type | Definition | Typical campaign arc | Operational complexity |
|------|-----------|----------------------|------------------------|
| Single | 1–3 tracks, primary promotional unit | 4–8 weeks pre-release; ~6 weeks post | Low — one delivery, one pitch window |
| EP | 4–6 tracks, cohesive collection | 6–10 weeks pre-release | Medium — multi-track delivery, sequencing |
| Album | 7+ tracks, full-length | 10–16 weeks pre-release; 12+ post | High — full arc, multiple singles, phased delivery |
| Deluxe | Album reissue with added tracks | 4–6 weeks, riding existing momentum | Medium — metadata conflict risk with original |
| Mixtape / Loosie | Informal, typically distribution-only | 2–4 weeks | Low–medium — editorial pitch optional |
| Live album | Recorded live performance | 4–8 weeks | Medium — audio QC critical; credits complexity |
| Compilation | Multi-artist or retrospective | 8–12 weeks | High — per-track clearance and rights verification |
| Re-release / Remaster | Existing release, updated audio/packaging | 4–8 weeks | Medium — ISRC decisions, deduplication risk |

**Decision rule:** Release type determines campaign arc length, which sets the
operational start date working backward from the target release date.

## The Release Campaign Arc (Single / Standard Release)

**Phase 1 — Operational foundation (Weeks -8 to -6)**
- Assign project lead; confirm internal team responsibilities.
- Confirm distribution partner and delivery timeline.
- Register ISRC (per track) and UPC (per release) if not already issued.
- Confirm publishing splits and rights-society registration for all tracks.
- Confirm sample clearances if applicable (must be complete before delivery).
- Commission artwork to spec (JPEG/PNG, minimum 3000×3000px square, sRGB).
- Collect audio masters (WAV or FLAC, 44.1kHz / 24-bit minimum).
- Confirm release date (Friday remains the global editorial-consideration standard).
- File release metadata: title, artist, featured artists, producers, writers,
  genre, explicit flag, language, ISRC, UPC.

**Phase 2 — Delivery & pitch (Weeks -6 to -4)**
- Deliver audio + metadata + artwork to distributor/aggregator.
- Minimum DSP processing lead time is 1–3 business days after submission on the
  major platforms; this is a stated minimum, not a guarantee.
- **Optimal delivery: four weeks before release** — provides editorial pitch
  window, pre-save runway, and buffer for delivery rejections needing correction.
- File the Spotify editorial pitch at minimum 7 days pre-release; optimal 14+
  days. Earlier pitches receive materially higher editorial consideration than
  last-minute ones (directional industry observation). Pitch content: artist
  description (≤500 chars); song description (mood, genre, story); 3–5 playlist
  suggestions; context for why the editorial team should care.
- File the Apple Music editorial submission via the artist portal or distributor.
- Queue the pre-save / pre-add campaign to begin once delivery is confirmed.

**Phase 3 — Pre-release activation (Weeks -4 to -1)**
- Monitor delivery confirmation at all DSPs (expect 24–72h on the majors).
- Activate the pre-save link; pre-saves seed the listener's new-release queue and
  generate day-one save signals that influence algorithmic inclusion in weeks 2–3.
- Coordinate creative-asset delivery and the content schedule with marketing.
- Brief the artist on release-day protocol (first-48-hour engagement is
  algorithmically significant).
- Confirm the press/editorial coverage schedule with PR.

**Phase 4 — Release week (Day -1 to Day +7)**
- Confirm the release is live at all DSPs by local midnight on release day.
- **The first-48-hour window is the primary algorithmic signal period.** Early
  saves, completions, and a high listener-to-save ratio drive new-release radar
  distribution and downstream exposure. A few hundred highly engaged listeners
  (saves + completions) outperform several thousand passive streams algorithmically.
- Monitor DSP dashboards; flag anomalies immediately.
- Confirm editorial coverage is live; thank editors post-placement.

**Phase 5 — Post-release (Weeks +1 to +6)**
- Week +1: assess algorithmic placement signal; adjust spend and content cadence.
- Weeks +2–4: secondary pitching to curators not targeted initially; trigger
  independent and third-party playlist pitching.
- Weeks +4–6: catalog-conversion targeting — pitch the artist's existing tracks;
  refresh bio and artist picks on DSP profiles.
- Document a post-mortem: outcome vs. projection, operational failures, response.

## Friday Release Convention

Friday is the coordinated global standard release day.
- DSP editorial playlists refresh Friday; releases delivered and pitched early
  enough are considered for that cycle. Miss the window, miss the cycle.
- The new-release radar refreshes Friday morning; a non-Friday release may wait
  until the following Friday for inclusion.
- **Tactical exception:** a mid-week (Tuesday/Wednesday) release can seed
  algorithmic signals for 3–4 days before the Friday spike, sometimes matching
  Friday algorithmic performance for artists without editorial ambitions. This is
  an active decision, not a default.

**Decision rule — release day:**
- Editorial ambitions or a DSP campaign → Friday.
- Algorithmic performance without editorial ambitions → Tuesday/Wednesday acceptable.
- Re-releases and catalog reissues → any day; editorial consideration unlikely.

## Milestone Timeline — Single (8-week arc)

| Week | Milestone |
|------|-----------|
| -8 | Project kickoff; team assigned; sample clearances confirmed |
| -7 | ISRC/UPC registered; artwork briefed; publishing splits confirmed |
| -6 | Artwork delivered to spec; master received and QC'd |
| -5 | Delivery to distributor; editorial pitch filed |
| -4 | Delivery confirmed at DSPs; pre-save link live |
| -3 | Pre-save campaign active; social content schedule confirmed |
| -2 | Press/editorial coverage confirmed; release email to list |
| -1 | Final DSP check; artist first-48h protocol briefed |
| 0 | RELEASE DAY |
| +1 | First-48h performance review; algorithmic signal assessment |
| +3 | Secondary playlist pitching launched |
| +6 | Post-mortem documented |

## DSP Delivery Requirements

**Spotify:** ISRC, track title, artist name, release date, genre, UPC, contributor
credits. Audio WAV/FLAC, 44.1kHz or 48kHz, 24-bit minimum. Artwork JPEG/PNG,
3000×3000px minimum, square. Processing 1–3 business days. Editorial pitch minimum
7 days pre-release, optimal 14+. Explicit content must be flagged; cover art may
not contain phone numbers, URLs, or misleading text.

**Apple Music:** primary artist, featuring artists, song titles, release date,
track numbers, ISRC. Clean metadata reduces automated QC flags. Processing 1–3
business days. Artist images minimum 3000×4000px (portrait) for editorial.

**Amazon Music:** delivery via distributor; requirements parallel Spotify. Spatial
audio delivered as a separate Atmos (ADM BWF) mix per distributor spec.

**YouTube Music / Content ID:** delivery via distributor or direct Content ID
registration; confirm the Content ID policy (monetize / track / block) per catalog
strategy at delivery.

## Pre-Delivery QC Checklist

| Item | Spec | Common failure |
|------|------|----------------|
| ISRC | 12-character, unique per recording | Reusing ISRCs across versions; missing on bonus tracks |
| UPC | 12-digit, unique per release | Absent on compilations; reused on digital reissues |
| Track title | Matches publishing registration exactly | Title-case inconsistency splitting royalty attribution |
| Featured artist | Separate field from main artist | Featured artist in main field breaks DSP linking |
| Producer / writer credits | All contributors in correct fields | Missing producer credits block performance registration |
| Explicit flag | E / C / not applicable, correct per lyrics | Missing flag → parental-advisory complaints, restrictions |
| Artwork | 3000×3000px, JPEG/PNG, sRGB | CMYK (print) color space → DSP rejection |
| Audio | WAV 44.1kHz/24-bit or better | 16-bit files; lossy master degrades quality, may be rejected |
| Release date | Friday confirmed for editorial track | Mid-week release with simultaneous pitch wastes the pitch |

## Practitioner-Layer Insight

- **Automated QC flags at Apple.** A release with several content-QC flags can be
  delayed or pulled from new-music recommendations. Most common triggers: a main
  artist name format differing from prior releases, incorrect ISRC linkage, and a
  featured artist placed in the main field. Pre-register a new distributor-label
  relationship in a territory to avoid first-release processing delays.
- **The editorial pitch is not a vanity submission.** Even for emerging artists,
  pitches are read and can yield tastemaker or new-music inclusion in smaller
  territories. Filing consistently also feeds the recommendation system genre and
  mood signals beyond what the metadata provides.
- **The pre-save's real function** is algorithmic seeding, not just a day-one
  spike. Pre-saves populate the listener's release-radar queue and confirm intent
  to the recommendation engine; the durable benefit is week-2–3 discovery
  inclusion, not only the launch-day bump.
- **Compression is a risk multiplier.** Every week of compressed timeline raises
  the probability of at least one failure — artwork rejected, ISRC missing, pitch
  not filed, delivery unconfirmed, pre-save link broken. Each is individually
  recoverable; compound failures in the final two weeks are not, without either a
  date move (brand risk) or a suboptimal release (commercial cost).

See also: [[label-ops-distribution-and-delivery]],
[[label-ops-roster-coordination]], [[label-ops-judgment-and-triage]].
