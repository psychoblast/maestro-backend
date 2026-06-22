# Data Reconciliation & Attribution

PLMKR knowledge base. How to reconcile streaming data across sources, attribute
performance changes to causes, and measure campaign effectiveness without over-
claiming. Distinct from anomaly detection (which governs when to escalate) and
cohort analysis (which governs how to segment): this file governs the data
quality and causal-inference layer an analyst applies before reporting any
performance finding.

---

## SOURCE HIERARCHY AND TRUST TIERS

Four tiers. Never blend tiers without labeling the downgrade; confidence is
capped by the lowest tier used in any claim.

### Tier 1 — Primary Measured (highest trust)

Direct DSP artist dashboards: Spotify for Artists, Apple Music for Artists,
Amazon Music for Artists, TIDAL for Artists, YouTube Studio (for music content).

- These are what the DSP actually counts for royalty settlement purposes.
- Reporting lag: 24–72 hours depending on metric and platform (per-platform
  details in cohort-and-retention.md).
- Limitation: access is gated to the claiming artist, manager, or label. Not
  available for competitor research or non-claimed catalog.
- Use for: all primary performance reads, cohort analysis, anomaly triage.

### Tier 2 — Licensed and Processed (high trust, with settlement-timing caveats)

Distributor dashboards and monthly / quarterly statements: DistroKid, TuneCore,
CD Baby, Amuse, Stem, LANDR, label distribution arms (major and independent).

- Based on DSP census data passed through the distributor's settlement and
  accounting layer.
- **Settlement lag:** distributors settle on a monthly or quarterly cycle with
  a 1–3 month accounting lag. A stream in January may appear in a March or
  April statement. This is a timing difference, NOT a discrepancy — do not
  escalate until confirming the settlement window.
- **Definition risk:** some distributors apply their own threshold or bucketing
  logic. Confirm whether the distributor's "stream" definition matches the DSP's
  30-second minimum before reconciling.
- Use for: royalty accounting, statement audit, annual revenue reporting,
  multi-platform portfolio views.

### Tier 3 — Estimated, Third-Party (directional only)

Aggregators that ingest public APIs and produce proprietary estimates:
Chartmetric-class tools, third-party playlist trackers, social listening
platforms.

- NOT licensed data partners. NOT the primary source for any high-stakes claim.
- Appropriate for: trend-direction confirmation, playlist-velocity monitoring,
  cross-platform reach comparison when direct access is unavailable.
- Trust level: estimated. Always label as "third-party estimate, not DSP-
  measured" in any deliverable. Confidence cap applies — a claim resting only on
  Tier 3 input is at most medium confidence.
- Procurement note: paid aggregator tiers require leadership sign-off; until
  approved, any figure behind a paid paywall is inaccessible — do not estimate
  from it.

### Tier 4 — Self-Reported or Unverified (context only)

Chart-monitoring services (radio airplay), national trade-body certifications
(RIAA, BPI, IFPI), social-platform creator analytics (Instagram Insights, TikTok
Creator Center, YouTube Studio for non-music-streaming use cases).

- Radio monitoring uses audio fingerprinting — reliable for airplay detection
  but not log-precision.
- Certification thresholds are definitional (the pass/fail is high trust; the
  attached market-sizing figure is lower trust and self-reported by member labels).
- Social analytics are measured for that platform but do not map cleanly to
  streaming intent and are never used as streaming proxies.

---

## COMMON RECONCILIATION GAPS AND THEIR CAUSES

Understanding why numbers diverge prevents mislabeling a timing difference as
a data error and prevents genuine errors from being dismissed as timing.

### Settlement lag — the most common apparent discrepancy

A DSP dashboard stream in January may appear in a March distributor statement.
Settlement cycles:
- Monthly (most distributors): streams close end-of-month; artist is paid 30–90
  days after month-end depending on the distributor contract.
- Quarterly (some legacy contracts): a Q1 stream may not reach an artist statement
  until a Q2 or Q3 payment run.

**Operational rule:** never compare a real-time DSP dashboard figure directly
against a distributor statement figure without confirming both cover the same
completed and settled calendar window.

### Threshold definition differences

- Spotify's 30-second threshold is the dominant standard, but distributors vary:
  some report plays at a 15-second threshold if their ingestion layer does not
  apply a DSP-specific filter. This is uncommon but produces a distributor total
  materially higher than the DSP dashboard.
- YouTube monetizable views use a different threshold from YouTube Music audio
  streams. When reconciling YouTube-delivered content, separate video views from
  audio streams explicitly.
- Always confirm the threshold definition before concluding there is a data error.

### Territory bucketing differences

- DSP dashboards report using ISO 3166-1 territory codes; distributors may
  aggregate (DACH as a single entry vs. Germany + Austria + Switzerland
  separately).
- "Rest of World" bucket definitions differ: one source may include or exclude
  specific markets that another classifies differently.
- **Reconciliation discipline:** work at the individual-territory level when a
  geographic gap is suspected; aggregated comparisons hide the source of the
  discrepancy.

### Currency conversion timing

- International streams are converted to the settlement currency (USD, GBP, or
  EUR) at the exchange rate in effect at the time of settlement, not the time
  of the stream.
- A stream in Q3 at one exchange rate settles in Q4 at a different rate; the
  royalty dollar amount will differ legitimately even on an identical stream count.
- **Reconciliation discipline:** stream-count reconciliation and dollar-amount
  reconciliation are separate steps. A stream-count match with a dollar-amount
  mismatch may indicate only a currency-timing effect — verify the exchange rate
  in effect at settlement before escalating.

### Bundle and compilation accounting

- When a track appears on a compilation or multi-track bundle, the distributor
  may report the royalty under the compilation's ISRC/UPC, not the original
  track's. This creates a gap between the track's dashboard count and its
  distributor statement count.
- Identify by checking whether the distributor statement carries a separate line
  item for compilation or bundle plays of the same track.

### Per-stream rate variation by listener tier

- Paid-premium streams, ad-supported (free-tier) streams, and Spotify-bundled
  streams (family plan sub-accounts, student plans) carry different per-stream
  royalty rates. The stream count from a DSP dashboard does not break out these
  listener tiers; the royalty amount from a distributor statement reflects the
  blended rate.
- If the effective per-stream rate (royalties ÷ streams) has shifted materially
  quarter-over-quarter, it may indicate a shift in the listener-tier mix (more
  free-tier listeners vs. premium), not an accounting error.

---

## RECONCILIATION WORKFLOW (STEP BY STEP)

Apply this six-step process before escalating any apparent discrepancy:

**Step 1 — Align windows.**
Confirm both sources cover the same completed calendar period (same UTC start
and end dates, fully settled on both sides). Do not compare a partial current-
month dashboard figure against a prior-month settled statement.

**Step 2 — Strip non-audio streams.**
Identify and exclude video streams from sources where the distributor separates
them but the DSP dashboard does not (or vice versa). Align both figures to
audio-stream-only counts before comparing.

**Step 3 — Confirm threshold consistency.**
Verify both sources apply the 30-second minimum-play-duration threshold (or the
same alternative threshold). Request the distributor's documentation if in doubt.

**Step 4 — Compare stream counts, track by track.**
Acceptable tolerance for same-window, same-threshold comparison: ±5%. Below
±5% is rounding and definition micro-differences — investigate but do not
escalate. Outside ±5%, flag and move to Step 5.

**Step 5 — Compare royalty amounts on matched stream counts.**
A dollar-amount mismatch on a matched stream count means one of: (a) per-stream
rate difference (listener-tier mix shift), (b) currency-conversion timing
difference, or (c) minimum guarantee or advance recoupment affecting payout.
Identify which of these applies before escalating.

**Step 6 — Document and escalate.**
Any unresolved stream-count discrepancy > ±10% gets a formal discrepancy log
entry: gap amount, both source figures, window definition, and escalation status.
Do not resolve by averaging the two figures — escalate to the distributor with
the log entry and specific evidence.

**Tolerance summary:**
- ±5%: investigate; often rounding or threshold definition
- 5–10%: investigate; likely threshold, bundling, or territory bucketing
- > 10%: escalate to distributor with formal log entry

---

## ATTRIBUTION METHODOLOGY

Attribution in music streaming is structurally harder than in e-commerce:
1. Listeners can arrive via multiple parallel paths simultaneously (editorial
   playlist + Release Radar + social share + direct search) with no cross-channel
   tracking at the listener level.
2. DSPs provide channel-level source data, not campaign-level tracking codes.
3. Paid campaign analytics (Meta Ads Manager, TikTok Ads) measure in-platform
   behavior; what the listener did afterward on the DSP (saved, returned,
   followed) is inferred, not measured.

Any attribution claim must state its method, the tier of evidence it rests on,
and the confounds it cannot rule out.

### Source-of-stream breakdown (primary attribution tool)

The source-of-stream split (editorial, algorithmic, library, search, other) is
the closest available proxy for channel attribution. It is channel-level, not
campaign-level.

- A spike in search-source streams correlated with a press mention is correlated
  attribution — not causal evidence. Report it as correlated, not caused.
- A spike in editorial-source streams on the day of a confirmed editorial
  placement is strong correlated evidence — the mechanism is specific and
  confirmed (editorial placement is known; its streaming impact is the observed
  change). This is the strongest attributable signal available in source data.
- A spike in algorithmic-source streams with no identifiable external trigger
  (no editorial add, no paid campaign, no press) is the clearest organic
  algorithmic pick-up signal.

### Territory-time correlation

If streams from a specific territory spike at the time a campaign ran in that
territory, the correlation is the attribution evidence. Strength: moderate.
Confounds to name: other events in the same territory and window; organic
discovery patterns; DSP reporting lag creating a time-shifted appearance.

### Pre/post design

Compare a pre-campaign baseline period to the active campaign period. Validity
requirement: same release-age bracket for both periods (week 3 vs. week 4 is
comparable; week 1 vs. week 6 is not — decay effects dominate). Use the decay
curve's expected trajectory as the counterfactual, not the raw most-recent
single-period figure.

### Lift methodology (most resource-intensive, highest causal validity available)

Compare the subject artist against a matched control artist (similar scale,
genre, release timing, with no campaign running) during the campaign window.
The observed difference is the estimated lift.

Requirement: a genuinely comparable control is rare. Most lift estimates in
music marketing rest on weak control matching and must label confidence
accordingly — "moderate confidence, limited by control comparability."

### In-campaign conversion rates (highest precision, in-platform only)

Click-through rate, swipe-up rate, link-to-stream conversion — measured in
the ad platform (Meta, TikTok Ads). These are the only cleanly causal metrics:
a listener who clicked an ad and streamed is a confirmed conversion.

What they did after (saved, returned, followed) is on the DSP side and is
inferred via source-of-stream correlation, not measured.

---

## A/B TESTING DISCIPLINE IN MUSIC MARKETING

DSPs do not permit listener-level randomization. Two viable experimental
substitutes exist; each has specific confounds that must be named.

### Territory-based A/B

**Setup:** Run the intervention (paid campaign, regional editorial pitch) in
Market A; hold Market B with no intervention as control.

**Validity requirement:** Market A and Market B must show similar organic
trajectory in the pre-period. Check: same genre fit, similar DSP editorial
infrastructure per capita, similar release-age trajectory, similar premium
subscriber penetration. A UK/Australia split on an English-language pop release
is often stronger than UK/Japan (structurally different market mechanics).

**Named confounds:**
- Differences in editorial playlist coverage between markets (Market A has a
  stronger regional NMF footprint; Market B does not).
- Different release-timing norms (Friday UK launch is Friday; some Asian markets
  have mid-week conventions that shift volume distribution patterns).
- Revenue asymmetry even on matched stream counts (high-ARPU vs. lower-ARPU
  market comparison does not translate to equivalent revenue lift).

**Reading the result:** Stream lift in Market A vs. Market B during the campaign
window, adjusted for pre-period baseline differences between markets. State the
adjustment method and its assumptions. The lift estimate is approximate.

### Time-based A/B

**Setup:** Run the campaign in weeks 2–3 of the release cycle; use a pre-release
baseline period or weeks 4–5 as control.

**Core confound:** Release decay is time-dependent. Weeks 4–5 are structurally
lower-traffic than weeks 2–3 on any normal decay curve, regardless of whether
a campaign ran. Comparing campaign-window volume directly to post-campaign volume
attributes natural decay to the campaign ending — an artifact, not a real effect.

**Validity requirement:** Apply a decay-adjusted baseline (expected decay
trajectory modeled from pre-campaign data) as the counterfactual. The relevant
question is: did the campaign slow the decay curve relative to the expected
trajectory? Not: were weeks 2–3 higher than weeks 4–5?

### What cannot be cleanly measured with available tools

- Whether a listener who arrived via a TikTok sound link went on to save, return,
  and follow — the TikTok → DSP handoff breaks the tracking chain. The in-platform
  data (TikTok: the video was watched) and the DSP data (Spotify: a stream
  occurred) are two separate events connected by inference, not tracking.
- Whether an editorial placement caused a streaming increase vs. coincided with
  organic discovery already building — unless a matched control territory had no
  editorial access and did not show the same ramp, the causal inference is
  incomplete.
- Long-term audience quality differences across acquisition channels — whether
  paid-social-acquired listeners have lower lifetime save and return rates than
  editorial-acquired listeners — requires a 90+ day cohort study with source-
  segmented retention tracking.

---

## ATTRIBUTION ANTI-PATTERNS

- **Correlation-to-causation error.** "TikTok sound uses spiked the same week
  streams spiked — TikTok drove it." This is correlation. The causal chain
  (TikTok listen → search → DSP stream → save) is plausible but requires
  supporting evidence: territory match (same geography where the TikTok use was
  concentrated), search-source stream increase in that territory, and a save
  rate increase alongside the stream spike. All three together are strong
  correlated evidence. One alone is noise.

- **Same-window contamination.** A playlist add AND a paid campaign both ran in
  the same week. It is impossible to cleanly attribute the lift to either without
  isolation. Protocol: label both as co-occurring events, present both as
  candidate causes with equal standing, and make no attribution split. Do not
  "split the attribution 50/50" — that number has no basis in the data.

- **Press and sync attribution omission.** A TV sync placement or a major press
  mention generates organic spikes that are frequently labeled "unexplained
  organic" in dashboards. Always check the sync and press calendar against the
  anomaly timeline before declaring an increase as genuinely organic. Press
  coverage generates search-source and direct-source stream spikes; sync
  placements generate spikes timed to broadcast windows (check air dates against
  streaming date).

- **Fan-campaign misread as organic discovery.** In fandom-driven markets,
  organized fan streaming produces signals that superficially resemble organic
  discovery — all source categories active, broad territory distribution — because
  experienced fan communities deliberately vary their streaming behavior. The
  discriminating check is listener-to-stream ratio across the full catalog, not
  just the new release. Fan campaigns produce anomalously high stream-per-listener
  ratios across the catalog (fans stream full discographies, not just one track);
  genuine organic discovery concentrates on the new release.

- **Baseline recency bias.** Choosing the pre-campaign baseline as the most
  recent single week before the campaign biases toward a low baseline if a
  natural dip preceded the campaign window. Use the decay curve's expected
  trajectory (from multiple pre-campaign periods) as the counterfactual, not
  the closest single-period value.

- **Campaign total vs. campaign lift confusion.** "The campaign generated 500K
  streams" is only valid as an ROI statement if the baseline without the campaign
  is quantified and subtracted. Attributing the full campaign-window stream count
  to the campaign ignores the organic baseline — a category error in any ROI
  calculation.

- **Multi-touch platform attribution error.** When a listener heard an ad on
  Meta, saw a TikTok, and then searched and streamed, each platform's analytics
  will claim the conversion. In-platform attribution models (last-touch, first-
  touch, linear) each overcount because the same conversion appears in multiple
  platforms' reports. Treat in-platform conversion claims as directional inputs,
  never as additive totals.
