# Cohort & Retention Analysis

Two layers: **general frameworks** (domain-neutral) and **music modules**
(music-specific). Platform reporting conventions and metric definitions change;
the current-period reference layer holds the latest, and a definition change is
treated as a series break (see anomaly-detection).

---

## LAYER 1 — GENERAL FRAMEWORKS

### Cohort analysis

- **Cohorts are defined by shared entry conditions** (same acquisition window,
  same channel, same trigger) — never by convenience of the export. Mixed-entry
  cohorts produce averages that describe nobody.
- **Denominator discipline:** every rate names its denominator explicitly. "Save
  rate up" means nothing until "saves per what, over what window, for which
  listener set" is stated. Most retention illusions are denominator changes.
- **Compare cohorts at the same age**, not the same calendar date. Day-30 of the
  March cohort vs. day-30 of the April cohort — never March's day-60 vs. April's
  day-30.
- **Composition shifts masquerade as behavior shifts.** Before concluding "users
  are retaining better," check whether the mix of who is arriving changed
  (channel, territory, intent). A Simpson's-paradox check is mandatory on any
  aggregate trend claim.

### Retention analysis

- Retention is a curve, not a number: report the shape (where it flattens, if it
  flattens) and the level. A curve that never flattens is churn-to-zero on a
  delay — no flattening point, no durable-audience claim.
- Separate **return behavior** (they came back) from **depth behavior** (what
  they did when back); the two move independently and answer different decisions.
- Early-window retention predicts late-window retention only within a cohort
  family — the mapping is empirical, not assumed, and is re-validated when the
  context changes.

### Operating defaults (provisional)

- **Standard cohort keys:** release-week listener cohort (entered during week 1),
  placement cohort (entered via a named playlist add), and campaign cohort
  (entered during a paid push window) — one entry condition per cohort;
  mixed-entry aggregates refused.
- **Decision-relevant windows:** day-7 return (campaign-adjustment decisions),
  day-28 return (durable-audience claims). Nothing shorter than day-7 supports a
  retention claim; day-1 behavior is engagement, not retention.
- **Minimum cohort size before a rate is reportable:** 100 listeners for
  directional reads, 500 for cohort-vs-cohort comparisons. Below 100, report raw
  counts ONLY (e.g., "5 saves out of 40 listeners") — do NOT compute, state, or
  lead with a rate, not even followed by a correction. A sub-floor rate is
  invalid output.

---

## LAYER 2 — MUSIC MODULES

### Streaming analytics: DSP metrics

Each metric gets: definition as the DSP reports it · window · known reporting
quirks · what it actually predicts · the cohort baseline it must be read against.

- **Save rate** (saves / unique listeners, per DSP definition): the strongest
  commonly available intent signal; meaningful only against a genre +
  source-of-stream cohort. Provisional cross-genre bands (no published DSP
  baseline exists; recalibrate per artist cluster as data accrues): < 2% weak /
  2–5% unremarkable / 5–10% promising / > 10% strong — **for discovery-source
  listeners only**. Library-source save rates are structurally inflated and never
  read against these bands. Save rate behaves very differently by genre and
  geography; a rap track and a cinematic pop track do not share physics.
- **Skip rate / completion:** read by source of stream — skips inside algorithmic
  programming mean something different from skips in owned playlists or library
  plays. The first 15 seconds are the retention cliff; skip analysis starts at
  the intro/hook timestamps before blaming the song. Skip rate is evaluated only
  when the sample exceeds the minimum-cohort floors (100 directional / 500
  comparison); below those floors it stays observational-only.
- **Listener-to-stream ratio:** repeat-listening depth; the fastest separator of
  broad-shallow (playlist exposure) from narrow-deep (real fans) profiles.
- **Source-of-stream mix:** the master key — every other metric is interpreted
  within its source mix, never across it.
- **Follower / pre-save conversion:** owned-audience accumulation; the
  denominator is exposed listeners, not total streams.
- Metric definitions are DSP-versioned: when a DSP changes a definition or
  surface, the series breaks and gets flagged.

### Playlist dynamics

- Adds and removals are a **flow**, not a stock: track add velocity, position
  changes, and time-to-removal — placement quality is position × playlist health
  × fit, not follower count of the list.
- Editorial, algorithmic, and user playlists are three different economies with
  different decay behavior after removal; never aggregated into one "playlist
  streams" number for projection purposes.
- Listener cohorts acquired from playlists are tracked as cohorts: what fraction
  converts to library/follow within the window — that conversion, not the stream
  count, is the placement's value.

### Operating defaults (provisional)

- **Post-removal decay expectations by playlist type:** editorial removal →
  assume the placement's volume goes to near-zero within days and model retained
  listeners only from the conversion rate; algorithmic decay → gradual, follows
  engagement signals, re-test weekly; user-playlist removal → usually negligible
  at the portfolio level. These are modeling defaults, not measurements, and are
  labeled as such in any output that uses them.
- **Placement value = conversion, not volume:** report playlist-cohort →
  library/follow conversion as the placement's headline number.
- Playlist signals feeding the engagement dimension: save rate by source,
  listener-to-stream ratio, playlist-cohort conversion — chosen because they
  survive the rented-audience test. Add velocity and position are context (facts),
  not verdict drivers.

---

## DSP REPORTING QUIRKS — PER PLATFORM

Each DSP's data has distinct reporting conventions. Using metrics across DSPs
without accounting for these differences produces invalid comparisons.

**Spotify for Artists** (primary DSP surface)

- Stream threshold: **30 seconds** = 1 counted stream.
- Reporting lag: **24–48 hours** typical; stats update once daily.
  Traffic-source and demographic breakdowns can lag up to **72 hours**. A "spike"
  visible on Thursday may include backfill from earlier in the week.
- Streaming day: **UTC midnight to midnight** regardless of listener territory.
  An artist at UTC+9 sees their "Monday" streams split across two dashboard days —
  relevant for day-by-day release reads.
- Monthly listeners: **28-day rolling window** of unique accounts that played
  ≥1 track. Not aligned to calendar months; re-measures every day.
- Skip rate: **NOT directly surfaced** in the artist UI; any skip-rate figure
  from a third-party aggregator is an estimate, not a DSP-measured output.
- Save rate: the saves count is available as an absolute number; the rate must be
  computed by the analyst (saves ÷ listeners in the same window).
- Source-of-stream breakdown: available — editorial playlist, algorithmic, owned
  playlist, artist playlist, library, search, other — each with its own cohort
  interpretation.

**Apple Music for Artists** (second primary surface)

- Stream threshold: **30 seconds** = 1 counted play.
- Reporting lag: **~48 hours** typical; first-day data for a new release can
  delay further.
- Unique metrics not on the primary surface: **completion rate** bucketed at
  25/50/75/100% (allows direct drop-off identification); **Shazam count**
  (a real-world discovery signal); **Spatial Audio play share**; radio airplay
  spins where trackable.
- Monthly listeners: **calendar-month window** (not rolling 28-day).
- **Critical comparison warning:** calendar-month listeners ≠ rolling-28-day
  listeners. Presenting these side-by-side as equivalent denominators is a
  measurement error. Use the same reference period and flag the definition
  difference.
- Source breakdown: fewer granular categories; editorial vs. algorithmic within
  playlists not always separated.

**Industry weekly tracking services**

- Tracking window: **Friday–Thursday**; data closes Thursday, processed Friday,
  charts published Saturday.
- A streaming event late Thursday may not fully appear until the following week's
  data — relevant for release-week reads attempting to reconstruct chart
  eligibility.
- These are a census from licensed partners, not a dashboard artists access
  directly; artist teams see the data via distributors and label-level reporting.

---

## DOMAIN ANTI-PATTERNS

How real analysts fail with cohort and retention data in music — distinct from
the doctrine's refusal rules; these are live failure modes.

- **Denominator swap without announcement.** Reporting "save rate improved
  week-over-week" when the listener composition changed (higher-propensity
  editorial listeners replaced lower-propensity algorithmic ones). The rate rose
  but no behavior changed. Always test whether denominator composition shifted
  before concluding behavior shifted.
- **Platform conflation.** Comparing calendar-month listeners directly to
  rolling-28-day listeners as if they were the same denominator. A 200K number on
  each platform may cover different time spans, territory mixes, and intent
  definitions. State which definition is in use and flag cross-platform rate
  comparisons as approximate.
- **Retention theater.** A cohort "retains at 60%" on day 30 because 60% is the
  library-source segment, which has structurally high retention regardless of the
  release. The discovery-source cohort — the actual signal for new audience — may
  have churned to near-zero, hidden in the aggregate. The defense is
  source-segmented cohorts.
- **N-expansion reporting.** "Completion rate improved from week 3 to week 4"
  when the absolute listener count dropped 70%. The improving rate is a survivor
  effect (only the most engaged remain) — it signals shrinkage, not improvement.
  Always report absolute N alongside the rate.
- **Claiming a floor that hasn't appeared.** A retention curve still declining at
  the end of the window has no floor. "We retained X%" when X is the last point on
  a still-declining curve is projecting a floor that hasn't materialized. Report
  the curve shape and trajectory, not a point from an open curve.
- **Library-source save-rate contamination.** Library-source streams come from
  listeners who already saved or added the track — their "save rate" is
  structurally 100% or meaningless. Including them in the denominator inflates the
  rate and hides the discovery-audience signal. The save-rate bands are defined
  for discovery-source listeners only for this reason.
