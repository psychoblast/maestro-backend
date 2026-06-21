# Anomaly Detection

Two layers: **general frameworks** (domain-neutral) and **music modules**
(music-specific). Known methodology and definition changes that drive series
breaks are maintained in the current-period reference layer; this file governs
how an anomaly is detected, classified, and triaged.

---

## LAYER 1 — GENERAL FRAMEWORKS

### Anomaly detection logic

1. **Expected range before anomaly call.** An anomaly exists only relative to a
   stated expectation (seasonal-adjusted band, cohort baseline). "That looks
   high" is not a detection; "outside the band that contains N comparable
   periods" is.
2. **Typology — classify before interpreting:**
   - **Spike** — single-period departure, returns to baseline.
   - **Level shift** — departs and stays; something structural changed.
   - **Drift** — slow divergence; usually composition or decay, not an event.
   - **Series break** — the measurement itself changed (methodology, definition,
     coverage).
3. **Triage order — cheapest explanation first:**
   a. **Data artifact?** (reporting lag, backfill, double-count, timezone/window
      edge)
   b. **Methodology break?** (definition or rule change at the source — check the
      reference layer before blaming the world)
   c. **Known event?** (a release, placement, press, price change)
   d. **Manipulation?** (someone gaming the metric)
   e. **Genuinely new behavior** — the residual category, claimed only after a–d
      are checked and the checks are shown.
4. **An anomaly is a question, not a conclusion.** The output is: classification
   + candidate causes ranked + the observable that would discriminate between
   them.
5. **Absence anomalies count.** A metric that *failed* to move when it should
   have (a release with no save-rate response) is as decision-relevant as a
   spike.

### Named statistical detection frameworks (established)

- **Statistical process control / control charts:** define a process mean and
  upper/lower control limits (typically ±2 SD from the rolling mean); any point
  outside is flagged. The 8-period band rule below is this framework applied to
  weekly streaming data — naming it makes the threshold arguable. Preferred for
  stable series.
- **Z-score / standardized deviation:** express a departure as "how many standard
  deviations from the cohort baseline?" Z > 2.0 is a candidate; Z > 3.0 is a
  strong signal. Advantage over a fixed percentage: a +30% weekly move may be
  Z=1.5 in a volatile catalog (unremarkable) or Z=4.2 in a stable one (definitely
  investigate). Use for cross-series comparison where volatility differs.
- **IQR-based outlier detection (Tukey fence):** bounds = Q1 − 1.5×IQR and
  Q3 + 1.5×IQR. Robust to non-normal distributions — streaming data is heavy-
  tailed (a few breakout weeks dominate), which makes mean ± SD misleading.
  Prefer when the series has a history of large legitimate spikes.
- **Seasonal decomposition:** separate the observed series into trend + seasonal
  + residual; run detection on the residual, not the raw series. A December spike
  on a holiday catalog is expected; the same spike in August is anomalous.
  Without decomposition, seasonal patterns generate false positives and genuine
  off-season anomalies are masked.

### Operating defaults (provisional)

- **Attention threshold:** a metric earns attention when it leaves the band
  containing the last 8 comparable periods (8 weeks for weekly series, 8
  same-weekdays for daily) **and** the move survives the data-artifact check
  (triage step a). One rule, stated with every anomaly call so the user can argue
  with it.
- **Escalation (proactive flag, don't wait for the scheduled read):** (1) a level
  shift ≥ 30% on a revenue-bearing series sustained 3+ periods; (2) any
  suspected-artificial pattern on owned catalog — silence here is a liability,
  not politeness; (3) a methodology break that invalidates benchmarks currently
  in use by other functions; (4) an absence anomaly on a launch — a release whose
  day-1/day-2 signals failed to register at all.

---

## LAYER 2 — MUSIC MODULES

### Stream-spike forensics

Discriminating signatures to check when streams jump, before celebrating or
accusing:

- **Playlist add:** source-of-stream mix shifts toward the playlist source;
  listener-to-stream ratio drops; geography follows the playlist's audience.
  Confirm against actual add data, not inference alone.
- **Viral / UGC-driven:** discovery sources (search, social-linked) rise first;
  territory pattern follows the platform's spread, not the artist's history; save
  rate often *rises* with volume — the inverse of bought traffic.
- **Artificial / bot-driven:** flat listener-to-stream ratios at abnormal depth,
  geographic concentration unconnected to any placement or audience history,
  completion patterns too uniform, off-hours periodicity. **Output discipline:**
  an artificial-streaming call is an allegation with consequences — it ships with
  the signature evidence, a confidence level with reasons, and the checks that
  would falsify it. Never a vibe.
- **Reporting artifact:** check DSP reporting-lag/backfill behavior before any of
  the above.

### Chart anomalies & methodology breaks

- Chart positions move for three reasons: consumption changed, competition
  changed, or the chart changed. Check in reverse order — methodology breaks are
  the cheapest explanation and the most often missed.
- Every known chart-rule or metric-definition change becomes a dated
  **series-break flag** on affected benchmarks: pre/post numbers are never
  compared without the flag. The reference layer is the primary source for these
  breaks; this domain maintains the break log.
- Bundle/variant-driven chart motion (physical variants, direct-to-consumer
  windows) is identified as mechanics-driven before being read as demand.

### Operating defaults (provisional)

- **Signature thresholds:** deliberately not drafted as numbers. False
  artificial-streaming signatures are the highest-cost error this domain can
  make, and no anchoring incident corpus exists yet. Until it does, spike
  classification uses the qualitative signatures above with all evidence shown.
- **Dashboard observability map:** source-of-stream mix, save/follower deltas,
  and territory breakdowns are DSP-reported; listener-depth uniformity, off-hours
  periodicity, and completion-curve shape must usually be inferred from partial
  surfaces — any claim resting on the inferred set says so and is confidence-
  capped by it.
- **Artificial-streaming bar:** name artificial streaming as the *probable* cause
  only when (a) at least two independent signatures point the same way, (b)
  innocent explanations (placement, press, reporting artifact) are checked and
  shown to fail, and (c) confidence is stated with reasons. Below that bar the
  verdict is **"inconclusive — here is what would settle it,"** never a hedged
  accusation. Allegations about specific named third parties always escalate to
  leadership before leaving the system.

---

## TERRITORY-SPECIFIC ANOMALY PATTERNS

Territory context is required before classifying an anomaly — the same numeric
signature has different interpretations depending on origin market.

**Coordinated fan-campaign patterns** (fandom-driven markets)

- Coordinated fandom streaming occurs during award-season voting windows
  (October–November; January) and around a new release, comeback, or streaming
  milestone.
- Discriminating signatures: geographic concentration in the home market on
  domestic DSPs (not the international platform); simultaneous multi-track
  spiking across the same artist's catalog (fans stream full discographies, not
  just the new single); spike duration aligned to the award-window calendar
  (typically 48–72 hours of elevated activity, then rapid return to baseline).
- These are real, counted streams — not artificial — but represent organized fan
  behavior, not organic discovery. Projecting this volume forward as a sustained
  discovery signal overestimates organic reach. Classify as: Spike (fan-campaign-
  driven), then model the baseline return.
- A "reverse entry" event (fans push a catalog track to chart without a release
  trigger) is a recognized pattern; an anomaly on a dormant catalog track
  coinciding with a fan-community milestone is likely this, not algorithmic
  discovery.

**LatAm organic-build pattern**

- LatAm discovery is typically slower-building than US push-driven launches. A
  release with no US-style first-week spike that then shows sustained growth in
  Mexico and Colombia at weeks 3–6 is on a normal LatAm organic trajectory — NOT
  an absence anomaly on launch and NOT a delayed spike.
- Discriminating feature: growth is smooth and building (Drift typology),
  originating in regional playlists or local radio, not concentrated in one day.
  True delayed spikes are sharp (Spike typology) and usually tied to a press
  event or playlist add.
- Outside Mexico and Brazil, editorial infrastructure per capita is lower —
  organic building through algorithmic and user-playlist channels is the primary
  growth mechanism, not editorial push.

**High-growth emerging markets**

- Some markets have rapidly growing premium subscriber bases while the majority
  of listening remains ad-supported (free tier). Streams from these markets count
  in global totals but at a lower per-stream revenue weight.
- A 40% global stream spike driven primarily by one such market has lower
  chart-impact (census coverage skews to established markets) and lower revenue
  impact than an equivalent spike from a high-ARPU market. Scale the significance
  accordingly.
- A sustained ramp from such a market is a positive-trend signal (Drift typology,
  upward) and warrants a territory-specific note, not a spike alert.

---

## DSP REPORTING LAG AND ITS IMPLICATIONS

A "spike" observed on Thursday may be partly backfill from earlier-week data that
arrived late. Triage step (a) requires checking the lag profile before treating
magnitude as real.

- **Primary streaming surfaces:** ~24–48h lag with a daily update; traffic-source
  and demographic breakdowns can lag up to 72h.
- **Secondary surface:** ~48h typical; first-day data for new releases may delay
  further.
- **Weekly tracking services:** the window closes Thursday; reports Friday; chart
  Saturday. A late-Thursday event may not appear until the following week.
- **Practical rule:** a spike that persists across two or more consecutive
  reporting updates is more reliable than a single-update spike of the same
  magnitude. A one-day jump that partially resolves on the next update is a
  reporting-artifact candidate before it is a real spike.
