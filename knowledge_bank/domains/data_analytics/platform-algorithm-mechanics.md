# Platform Algorithm Mechanics

PLMKR knowledge base. The algorithmic discovery systems that govern whether a
release reaches new listeners automatically — without editorial or paid-campaign
intervention. Understanding these mechanics lets an analyst read whether an
algorithm picked up a release (or did not), separate editorial from algorithmic
performance in source data, and project forward from early signals.

---

## SPOTIFY ALGORITHMIC SURFACES

Spotify operates several distinct algorithmic surfaces, each with different
trigger conditions, refresh cadences, and signal weights. Treating them as a
single undifferentiated "algorithm" produces incorrect reads.

### Release Radar

- **What it is:** A personalized weekly playlist, delivered every Friday,
  containing new music from artists the listener follows or has recently engaged
  with. Capacity: roughly 30 tracks per listener per week.
- **Trigger conditions:** The release must be ≤ 4 weeks old (the conservative
  operational assumption — some sources cite up to 6 weeks, but 4 is safer).
  The listener must either follow the artist OR have streamed the artist within
  a recent lookback window. Saves alone do not guarantee inclusion; follow status
  or recent engagement is the stronger trigger.
- **Cadence:** Refreshes every Friday. A release published on a non-Friday still
  enters the next Friday's Release Radar cycle. A release published on Friday
  earns Release Radar placement that same day — one of the primary reasons
  Friday release is the industry standard.
- **Analytics signature:** Volume from Release Radar concentrates on Fridays
  (the delivery day) and decays through the rest of the week. A sharp Friday
  spike in algorithmic-source streams on release day is expected and is NOT a
  rented-audience anomaly — it is the Release Radar delivery wave. The signature
  distinguishes from DW/Radio by its Friday concentration and its correlation
  with follower count.
- **Ceiling:** Release Radar reaches followers and recent engagers — not cold
  listeners. Its effective ceiling scales with follower count × recent-engagement
  rate. It activates the existing orbit; it does not expand it.
- **Analyst error to avoid:** Attributing Release Radar volume to organic
  discovery of cold listeners. Release Radar is broadcast to the known audience,
  not discovery of a new one. A release that earns 80% of its week-1 algorithmic
  streams from Release Radar has not yet been picked up for expansion.

### Discover Weekly

- **What it is:** A 30-track personalized playlist delivered every Monday, built
  via collaborative filtering — listeners with similar taste profiles to the
  recipient have engaged with the track. Not new-release biased; a track can be
  months or years old and enter Discover Weekly if its engagement signals
  accumulate to threshold.
- **Trigger conditions:** The track must have earned genuine engagement (saves
  and meaningful completes) from accounts that do NOT already follow the artist.
  If the only listeners who have saved the track are existing followers, the
  track lacks the cross-listener collaborative signal that drives DW candidacy.
  The operational assumption: a track with zero cross-follower engagement is
  DW-ineligible regardless of total save count.
- **Cadence:** Refreshes every Monday. DW does not prioritize release freshness.
  A release from three months ago can enter DW if engagement signals accumulate
  past threshold during that window.
- **Analytics signature:** DW placement produces a Monday spike in algorithmic-
  source streams — distinct from the Friday Release Radar spike. DW-driven
  listeners are cold (not followers), so they show: lower initial listener-to-
  stream ratio, higher skip rates in the first session, and — the signal of a
  healthy DW cohort — a save rate that *rises* over days 2–5 as the cohort
  self-selects toward listeners who genuinely engage.
- **What DW success looks like in data:** After the Monday delivery, a 2–5 day
  trickle of new followers and saves accumulates from the DW cohort. A small
  but measurable follow/save accumulation in the days after Monday (not a one-
  day spike) is the DW conversion signature.
- **Analyst error to avoid:** Treating DW as a one-time spike event. A track can
  live in DW for multiple consecutive Monday cycles if engagement signals sustain.
  Projecting DW volume as a single spike underestimates a track that earns
  sustained DW candidacy.

### Radio / Autoplay

- **What it is:** When a listener finishes a track or playlist and Autoplay
  continues, or when a listener starts a "Radio" seeded from an artist or track,
  Spotify selects upcoming tracks based on sonic and behavioral similarity to the
  seed. This is the catalog-lifetime algorithmic surface — a track with strong
  Radio candidacy earns a durable passive stream baseline long after editorial
  and Release Radar traffic fades.
- **Candidacy signal:** A track's Radio/Autoplay candidacy is built from its
  behavioral profile in non-follower, non-playlist listening contexts — what
  completion rate, save rate, and skip rate it earned when heard "raw." Strong
  non-playlist engagement in weeks 1–4 builds the Radio/Autoplay candidacy
  profile. This is the mechanism behind what practitioners call the "catalog tail."
- **Analytics signature:** Radio/Autoplay drives a steady background stream rate
  that does not spike on a specific day of the week. In source-of-stream data it
  appears as "radio," "autoplay," or "other" categories (label differs by
  dashboard version). A track with healthy Radio candidacy sustains a non-zero
  catalog baseline months after release — distinguishable from a track that
  decayed to near-zero in week 6.
- **Practical implication for projection:** Radio candidacy is the engine of
  catalog-phase performance. A release that accumulates strong non-playlist
  engagement in weeks 1–4 should have its catalog-phase projection modeled with
  a non-zero Radio/Autoplay base rate — not pure decay to zero. A release that
  fails to build Radio candidacy (low completion, high skip on discovery sources)
  has no catalog tail to project.

### Daily Mix / Your Mix

- **What it is:** Personalized playlists built from a listener's own listening
  history, refreshed periodically. Tracks the listener has saved or frequently
  played are seeded alongside algorithmically selected companions.
- **Analytics signature:** Streams from Daily Mix / Your Mix appear as library
  or algorithmic sources (dashboard categorization varies by platform version).
  The listener-to-stream ratio for a track earning Daily Mix inclusion will be
  high — multiple streams per listener per week — because Daily Mix drives
  habitual return listening, not first-listen discovery.
- **Analyst interpretation:** Daily Mix inclusion is a late-stage signal
  indicating a track has moved from "new discovery" to "habitual listen" for a
  listener cohort. This is a durable-audience signal. Projecting from this
  baseline is more stable than projecting from an editorial-driven spike because
  the Daily Mix audience has self-selected as repeat listeners.

---

## HOW TO READ WHETHER A RELEASE GOT ALGORITHMIC PICK-UP

The most consequential read an analyst makes in the first 7–14 days: did the
algorithmic engine independently pick up this release, or did all growth come
from distributed sources (editorial, Release Radar, paid)?

### Source-of-stream shift after week 1

- **Week 1:** Algorithmic share is typically dominated by Release Radar delivery
  (existing followers and recent engagers). This is expected and should not be
  labeled as algorithmic discovery.
- **Week 2 onward — the read:** If the algorithmic source share *holds steady or
  increases* while editorial and Release Radar shares decline, the algorithm is
  routing new cold listeners to the track via DW, Radio, and Autoplay. This is
  genuine algorithmic pick-up.
- **Failure signal:** If algorithmic share falls in step with editorial share
  in week 2, the release did not earn independent algorithmic amplification.
  All growth was distributed volume (Release Radar + editorial). The release
  is on the standard post-editorial decay curve.

### Save rate as algorithmic fuel

The algorithm uses saves from cross-listener engagement as its primary intent
signal for DW and Radio candidacy.

- Provisional decision thresholds (no published DSP baseline; calibrate per
  artist cluster as outcome data accrues):
  - < 2% save rate on discovery-source listeners after 7 days → "algo at risk":
    unlikely to accumulate the cross-listener save signal needed for DW candidacy
    or sustained Radio candidacy.
  - 2–5% → neutral: may or may not earn algorithmic amplification; look for
    week-2 source-shift evidence before committing.
  - 5–10% → strong candidacy signal: track is earning the cross-listener intent
    signals the algorithm weights.
  - > 10% → very strong; algorithmic amplification is likely if listener volume
    is also above floor.
- **Critical discipline:** These rates apply to discovery-source listeners ONLY.
  Library-source listeners already saved the track (that is why they are in
  library); their "save rate" is structurally inflated and must be excluded
  from the algorithmic fuel read.

### Skip rate and completion as the distribution gate

- A high skip rate in the first 15–30 seconds on Autoplay/Radio sources signals
  the algorithm to route away from the track in future similar-context
  recommendations.
- A track with a strong save rate but a high discovery-source skip rate presents
  a split signal: listeners who stay long enough to save are fans, but a large
  fraction never reaches that point. The algorithmic projection should model
  reduced Radio/Autoplay candidacy despite the save strength.
- Evaluate completion by source. Completion from library/follower listeners who
  already know the track is not a signal of new-listener retention. Completion
  from search and algorithmic sources is the relevant gate — these are listeners
  hearing the track for the first time.

### The algorithmic half-life

- Algorithmic amplification has a natural half-life: once the track has been
  surfaced to the portion of the listener base with the relevant taste profile,
  the amplification rate declines even if individual-listener engagement remains
  strong.
- Typical trajectory: algorithmic streams ramp in weeks 2–4, peak, then decay
  toward the catalog Radio/Autoplay base rate.
- A new external trigger — an editorial playlist add several weeks after release,
  a viral social moment, a sync placement — can restart the algorithmic cycle
  by introducing the track to a fresh listener cohort with a new engagement signal.
- **Projection discipline:** Model through the ramp to the estimated catalog base
  rate, not off the ramp peak. A projection anchored to week-4 algorithmic peak
  volume without modeling the half-life decline produces a systematic overestimate.

---

## PRE-RELEASE MECHANICS AND ALGORITHMIC PRIMING

### Pre-save campaigns and their analytics implications

- Pre-saves add the track to the listener's library on release day, registering
  as a save event (or library-add equivalent) before any streaming occurs.
- This pool provides an initial save signal to the algorithmic system on day 1,
  ahead of organic engagement accumulation.
- **Follower pre-saves vs. cold pre-saves:** Pre-saves from followers confirm
  depth in the existing audience; pre-saves acquired via paid social from cold
  listeners are less predictive of genuine return listening and may show high
  churn rates in the day-2 and day-7 listening checks. Track the two separately
  when the acquisition source is distinguishable.
- **Measurement gap:** Pre-save count (distributor or pre-save platform report)
  ≠ release-day save count (DSP dashboard). The gap occurs because: not all
  pre-savers have active accounts on the release platform; some pre-savers cancel
  before release; the registration event may differ in definition. Treat the two
  as directionally correlated, not numerically equal.

### The 48-hour algorithmic indexing window

- The primary DSP indexes a new release in the first 24–48 hours post-release.
  Early engagement signals (saves, completion, first-session return rates) from
  non-follower listeners feed the initial algorithmic candidacy assessment.
- A release with very low save rate from non-follower listeners in the first 48
  hours is at risk of receiving a depressed algorithmic priority that persists
  into weeks 2–3. Recovering from a weak 48-hour candidacy signal requires an
  external trigger (editorial add, viral moment) to re-seed the signal.
- **Paid traffic in the first 48 hours — risk:** Paid campaigns that drive
  streams without accompanying saves (high skip rate, low completion) contaminate
  the candidacy signal. The algorithm may assign a poor candidacy score to a
  track that would perform better with organic engagement alone. Paid
  follower/save campaigns (not paid streams) are the lower-risk approach in
  the first 48-hour window.

### Editorial pitch workflow

- **Spotify pitch:** submitted via Spotify for Artists ≥ 7 days before release
  date; one track per submission per release; pitch fields include genre, mood,
  styles, BPM. The editorial team gives NO pre-release confirmation — placement
  outcome is known only from source data on release day.
- **Apple Music pitch:** submitted via Apple Music for Artists with similar
  advance-notice requirement; editorial team is independent of Spotify; a
  placement on one does not predict placement on the other.
- **Pitching ≠ placement:** editorial teams receive thousands of submissions;
  submission is not a signal of outcome. Never present a submitted pitch as a
  "likely placement" in any forecast.

### Editorial-algorithmic interaction effects

- An editorial placement (NMF, A-list editorial playlist) generates a large
  initial listener cohort. If that cohort's engagement (saves, completion) is
  strong, it accelerates DW and Radio candidacy accumulation by feeding the
  cross-listener signal faster than organic growth alone.
- **The mis-matched editorial risk:** A poorly matched editorial playlist (wrong
  genre or mood cohort for the track) generates a large listener pool with low
  engagement — poor save rate and high skip. This can *damage* the algorithmic
  candidacy signal by introducing a wave of low-quality engagement before the
  organic cross-listener signal can build. An artist better served by a smaller,
  well-matched editorial placement than by a large generic list is a real scenario.
- **How to diagnose:** Read save rate and completion by editorial source (not
  aggregate). If the editorial-source save rate is below the discovery-source
  average, the editorial cohort was a poor genre-mood fit.

---

## APPLE MUSIC ALGORITHMIC SURFACES

Apple Music's algorithmic surfaces operate on broadly similar principles to
Spotify's but differ in mechanics and observability.

### New Music Mix

- Weekly refresh (Monday or Tuesday delivery); personalized new music based on
  listening history and follows; new-release biased similarly to Release Radar.
- In Apple Music for Artists data, a Monday/Tuesday bump in "for you" category
  streams is the New Music Mix signature.
- Do not apply Spotify's observed thresholds (save rate floors, DW candidacy
  signals) to Apple Music algorithmic interpretation — the systems are distinct.

### Completion rate as the primary observable signal

- Apple Music for Artists surfaces completion rate in bucketed form
  (25% / 50% / 75% / 100%), directly visible in the dashboard — unlike Spotify
  where skip rate must be estimated from third-party tools.
- Operational reads: > 60% of listeners reaching the 75%+ completion bucket is
  strong performance; < 25% of listeners reaching 50% completion is a retention
  problem that will limit Apple Music algorithmic candidacy. These are working
  benchmarks, not published DSP thresholds.
- Use Apple Music completion buckets as a complement to Spotify save rate when
  assessing multi-platform algorithmic health — together they give a cross-DSP
  picture of whether the track holds listeners past the first 30 seconds.

### Shazam as a discovery signal

- Apple Music for Artists surfaces Shazam count alongside streaming data. Shazam
  registers when a listener hears a track in the real world (radio, retail, film
  or TV playback) and uses Shazam to identify it — a real-world passive-discovery
  signal distinct from in-app algorithmic or editorial discovery.
- A rising Shazam count that precedes a streaming ramp is a "passive discovery
  pipeline" indicator: listeners are encountering the track outside the DSP before
  engaging on-platform. This pattern is structurally different from social-viral
  discovery (TikTok → stream) or editorial discovery (playlist → stream) and
  is often a sync or radio spillover signal.

---

## COMMON ANALYST ERRORS ON ALGORITHMIC READS

- **Treating Release Radar as algorithmic expansion.** Release Radar delivers to
  the existing orbit (followers + recent engagers) — it is audience broadcast,
  not cold-listener discovery. Only streams to non-followers via DW, Radio, and
  Autoplay constitute genuine algorithmic expansion of the audience.

- **Reading aggregate "algorithmic" source share without sub-type breakdown.**
  On Spotify, the algorithmic source category can include Release Radar (existing
  orbit) alongside DW and Radio (new listeners). Where the dashboard permits
  sub-type breakdown, use it. Where it does not, the Release Radar / DW
  distinction must be inferred from the day-of-week spike pattern (Friday = Release
  Radar; Monday = DW; flat distribution = Radio/Autoplay).

- **Single-week classification.** A track that shows no DW/Radio pick-up in week
  2 may still earn it in weeks 3–5 as cross-listener saves accumulate past
  threshold. A week-2-only read is premature unless the save rate is clearly and
  persistently below the candidacy threshold.

- **Assuming algorithmic mechanics are identical across DSPs.** Spotify's Release
  Radar, Discover Weekly, and Radio mechanics are not replicated exactly on Apple
  Music, Amazon Music, TIDAL, or YouTube Music. Each DSP has its own surface
  logic, refresh cadence, and observable metrics. Cross-applying Spotify thresholds
  to Apple Music algorithmic reads is a measurement error.

- **Conflating editorial and algorithmic in blended source labels.** On some
  platform dashboard versions, "editorial playlist" and "algorithmic playlist"
  are separate categories; on others they are bundled as "playlist." Confirm the
  dashboard's source-category definition before interpreting shares.
