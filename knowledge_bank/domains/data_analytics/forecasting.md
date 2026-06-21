# Forecasting & Projection

Two layers: **general frameworks** (domain-neutral reasoning) and **music
modules** (music-specific application). Current-period figures live in the
separate current-period reference layer; the methodology here governs how a
forecast is built, not the latest numbers it consumes.

---

## LAYER 1 — GENERAL FRAMEWORKS

### Forecasting methodology (every forecast, in order)

1. **Baseline first.** State the no-action trajectory before modeling any
   intervention. A forecast that can't show lift over a baseline can't justify
   spend.
2. **Decompose the series.** Trend / seasonality / events / noise — and name
   which component the forecast actually rides on. A forecast driven by an event
   component is a bet on the event repeating; say so.
3. **Outside view before inside view.** Build the reference class from comparable
   cases and take its base rate as the anchor. Inside-view adjustments ("this
   case is different because…") are listed, justified, and counted — more than a
   few and the reference class was wrong.
4. **Bands, not points.** Low / base / high scenarios, with the specific
   assumption that separates each band named. A single-point forecast is fake
   precision.
5. **Assumption register.** Every forecast ships with its assumptions ranked by
   sensitivity: which one, if wrong, moves the answer most. That assumption is
   the forecast's weakest critical input and caps its confidence.
6. **Falsifiability condition.** Observable metric + threshold + date. A forecast
   that can't be wrong isn't a forecast.

### Named forecasting frameworks (external, established)

- **Reference-class forecasting** (the outside-view tradition): begin with the
  statistical base rate of the reference class before considering the specifics
  of this case. Inside-view adjustments are listed, justified, and counted — a
  long list signals the reference class was wrong, not that the case is special.
  This is the formal foundation of Step 3 above; naming it makes the reasoning
  auditable.
- **Assumption sensitivity analysis:** rank assumptions by how much they move
  the output if wrong. The single assumption that, if false, most changes the
  answer is the forecast's weakest critical input — named explicitly and
  confidence-capped. In release forecasting the dominant sensitivities are
  typically: (1) whether a key editorial playlist add lands; (2) whether
  algorithmic systems pick up the release in the first 48 hours; (3) whether a
  paid campaign audience converts to library/follow at the projected rate.
- **Structured decomposition** (bottom-up estimation): when a direct reference
  class doesn't exist (new territory, format, or channel), break the forecast
  into independent sub-components and estimate each separately. Errors tend to
  partially cancel across components; the resulting band is more reliable than a
  single top-down estimate.

### Pre-ship failure-mode checklist

- Extrapolation window contains an un-flagged event, anomaly, or methodology
  break.
- Output precision exceeds input precision.
- Reference class is survivor-biased (built only from cases reported because
  they succeeded).
- Trend claimed from a single data point.
- Baseline silently assumes current conditions persist through a known upcoming
  change.

### Operating defaults (provisional — calibrate against real outcomes)

- **Default horizons by decision type:** release go/no-go and pitch timing →
  4–8 weeks; campaign reallocation → 2–4 weeks; catalog/valuation-shaped
  questions → 12 months with quarterly re-forecast. Never forecast past one known
  structural event (chart-rule change, platform feature launch) without splitting
  the horizon at that event.
- **Band-width honesty rule:** if the defensible high scenario exceeds ~4× the
  defensible low at the decision horizon, the deliverable is "not forecastable
  yet — here is what narrows it," not a forecast. A forecast nobody can falsify
  is decoration.
- **Ranges + sample size, never point estimates** — the standing north star.
- **Judgment overrides** of the reference class are allowed only as a *named
  adjustment* on the assumption register (direction + reason), are capped at
  moving the base case within the reference class's observed spread, and are
  recorded so override accuracy becomes measurable.

---

## LAYER 2 — MUSIC MODULES

### Release-performance analysis & projection

The questions a release forecast must answer, in priority order:

1. **What does the decay curve say?** First-period performance is shape, not
   size: is the trajectory front-loaded (push-driven), building (discovery-
   driven), or flat (catalog-behaving)? The shape, against the right cohort,
   predicts more than the totals do.
2. **How much of this is rented?** Split playlist-dependent streams from organic
   / search / library-driven streams before projecting. Playlist-driven volume
   disappears with the placement; projecting it forward as owned audience is the
   canonical release-forecast error.
3. **What is the cohort baseline?** A release over- or under-performs only
   relative to comparable releases (artist tier, genre, territory, release type,
   era). New releases targeting younger listeners increasingly compete against a
   resurgent catalog baseline, not just other new releases.
4. **What would change the answer?** The leading indicators (save rate,
   completion, pre-adds, playlist add velocity) that would move the projection
   between bands, stated so the forecast can be re-checked cheaply.

### Operating defaults (provisional — replace with observed cohort data)

- **Decay-curve classification:** week-2/week-1 stream ratio < 0.5 with falling
  listener counts → front-loaded (push-driven); ratio ≥ 0.8 with rising or stable
  listeners → building; in between → flat/catalog-behaving. Guard: when paid
  promotion or a major playlist spike inflated week 1, compare week 2 against the
  non-paid baseline listener cohort where available before classifying —
  otherwise ad-shaped curves get mislabeled as front-loaded failures.
- **Rented-audience flag:** more than ~60% of volume from playlist sources
  (editorial + algorithmic combined) is a **fragile-growth signal**, not a
  verdict. It triggers a mandatory second check: are saves, follows, and listener
  return rates rising? The flag answers "does this collapse when playlists drop
  off?" — not "is this bad?" Projections must model placement loss explicitly as
  the low scenario and never silently extrapolate the blended curve. For new
  artists, playlist dominance is often the only distribution channel available,
  not rented growth.
- **Leading indicators, ranked:** save rate and completion lead; raw stream
  velocity follows; follower counts trail. Which of these has *actually*
  predicted outcomes in a given catalog is an empirical question the prediction
  log exists to answer.
- **Minimum data window before any projection:** 7 full days post-release AND at
  least one source-of-stream breakdown. Earlier than that, the only honest
  deliverables are facts and checks. Early directional reads are permitted after
  48–72 hours but must be explicitly labeled **UNSTABLE — EARLY READ** and never
  as projections. Playlist-led or heavily pre-seeded releases can stabilize in
  48–72h; freezing all reads for 7 days delays real decisions like ad-spend
  adjustments.

**Specificity gate.** A forecastable request is one where minimum data
conditions are met (7-day window AND source-of-stream breakdown). When met, the
analyst must commit to low/base/high ranges with named assumptions. Responding
with a bare "it depends" or refusing the forecast when conditions are met fails
the gate.

---

## DOMAIN ANTI-PATTERNS

How real analysts fail in release and music forecasting — live failure modes
distinct from the hard refusals in the doctrine.

- **Trajectory extrapolation without decay.** Projecting a release's first-week
  slope forward at the same rate, ignoring that all releases decay. A 500K-stream
  week-1 that extrapolates to 26M annual streams is almost always wrong. The
  band-width rule is the defense — a projection that can't state a plausible low
  scenario isn't a forecast.
- **Rented-audience projection.** Projecting playlist-dependent volume forward as
  if it were owned-audience trajectory. The canonical release-forecast error;
  playlist-driven volume disappears with the placement, producing 3–10×
  overestimates at week 8.
- **Anchor-and-adjust contamination.** Starting the reference-class search from a
  memorable comparable (the artist's last hit, a chart-topper from the same
  quarter), anchoring to it, then "adjusting down." The anchor biases toward the
  better case. Defense: state inclusion criteria before looking at the cases.
- **Survivorship reference class.** A comparable-case library populated from
  campaigns discussed in trade press skews toward successes. Explicit correction:
  search for similar releases that did NOT get coverage and include their
  outcomes in the low-scenario band.
- **False narrow band.** Presenting 1.2M–1.4M when the reference class spans
  400K–3.5M. The narrow band signals effort but creates overconfident decisions.
- **Chart forecast without mechanics check.** Projecting a chart position by
  extrapolating consumption without reading the chart's current competitive
  landscape and eligibility rules. The same eligible-stream total may rank #3 in
  a thin week or #47 in a heavy one. Chart forecast and consumption forecast are
  separate deliverables.

---

## TERRITORY-SPECIFIC RELEASE DYNAMICS

A release strategy scoped only to one market forfeits most of the global
opportunity (the US is roughly a third of paid global streams; the top four
markets together under half). Forecasting in a multi-territory context requires
territory-adjusted decay curves and channel assumptions.

- **US:** Friday release. Editorial New-Music-Friday cycle: pitch the Thursday of
  the prior week → decision Monday → add Friday. The first 48 hours of
  algorithmic radio exposure set the discovery trajectory; pre-save campaigns
  influence new-release algorithmic weighting. Front-loaded decay curves typical
  for push-driven releases.
- **UK:** Official-chart window Friday–Thursday. National radio rotation
  materially affects chart position for mainstream acts — a track without UK radio
  support underperforms its US equivalent on the chart relative to streaming-only
  trajectory. UK DSP editorial teams operate independently of US teams.
- **Canada (English):** mirrors US release norms and editorial structure; Friday
  release; behaves as a US-adjacent cohort. Quebec (French-language) is a distinct
  market — francophone editorial and radio formats; treat separately for
  French-language content.
- **Germany / DACH:** Friday release. Streaming skews younger; older demographics
  retain FM radio and physical consumption (stronger physical baseline than UK or
  US). German-language content carries national-radio quota advantages.
- **Korea:** Domestic DSP landscape (Melon/Genie/FLO) primary; lower
  international-platform penetration. Chart window Friday–Thursday. Coordinated
  fan streaming during award-season windows (October–November, January) produces
  spike-and-plateau patterns structurally unlike organic discovery curves;
  forecasting from this catalog requires market-specific cohort references.
- **Japan:** Wednesday (sometimes Tuesday) release convention. Physical chart is
  the prestige metric; physical and digital windows are often staggered.
  Streaming adoption lower than Korea or Western markets; a forecast weighted
  toward physical sales reflects actual market structure.
- **Latin America:** Mexico and Brazil are the anchor markets. LatAm organic
  builds are typically slower than US push-driven launches — a track with no
  US-style first-week spike that shows sustained growth in Mexico and Brazil 3–6
  weeks later is on a normal LatAm discovery trajectory, not an absence anomaly.
  Regional radio remains influential for mainstream crossover. LatAm has been the
  fastest-growing region recently; its benchmark baseline rises each cycle.
