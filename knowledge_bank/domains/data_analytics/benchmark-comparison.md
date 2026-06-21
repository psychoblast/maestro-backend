# Benchmark Comparison

Two layers: **general frameworks** (domain-neutral) and **music modules**
(music-specific). Chart formulas and market-size figures change frequently; the
current-period reference layer holds the latest, and every chart-rule change is a
dated series break. This file governs how comparisons are built and defended.

---

## LAYER 1 — GENERAL FRAMEWORKS

### Benchmark comparison reasoning

1. **The comparison set is the analysis.** Choosing what to compare against
   decides the conclusion before any number is read. The set's inclusion criteria
   are stated up front so they can be attacked.
2. **Like-for-like or labeled:** comparisons must match on era (market
   conditions), scale tier, context, and measurement method — or every mismatch
   is explicitly labeled with its expected direction of distortion.
3. **Reference-class checks before use:**
   - Survivor bias — does the set contain only cases visible because they
     succeeded?
   - Selection bias — did cases enter the set because of the outcome being
     measured?
   - Era validity — were the rules of the game the same when the benchmark cases
     ran?
   - N honesty — a "benchmark" of two cases is an anecdote pair and is presented
     as one.
4. **Benchmarks decay.** Every benchmark carries a date and a review trigger;
   comparisons against stale benchmarks state the staleness. Methodology breaks
   invalidate cross-break benchmarks unless adjusted, and the adjustment is shown.
5. **"X resembles A more than B" is a scored claim**, not a vibe: name the
   dimensions on which it resembles A, the dimensions on which it doesn't, and
   what the resemblance predicts.

### Operating defaults (provisional)

- **Minimum comparable-case counts by stakes:** informational read → 3;
  recommendation that moves spend → 5; anything irreversible (signing, deal
  terms) → 8, or the smaller set is presented as anecdotes with the gap named.
  When strict comparables don't exist (emerging genres, hybrid releases),
  adjacent comps are permitted with an explicit, named confidence downgrade —
  analysis may not stall waiting for perfect comparables.
- **Recency vs. similarity:** when they conflict, similarity wins **unless** a
  rules-of-the-game change (chart methodology, platform feature, payout model)
  separates the eras, in which case recency wins and older cases are used only
  with the break flagged.
- **Load-bearing resemblance dimensions:** genre-cohort + territory + audience-
  acquisition channel + release cadence + team/funding context. Sonic similarity
  alone is explicitly insufficient — sonic-only reference matching is unreliable.

---

## LAYER 2 — MUSIC MODULES

### Chart mechanics

Standing rules (all charts): a chart position is an output of mechanics ×
consumption — mechanics first. Cross-chart comparisons are cross-methodology
comparisons and are labeled as such. Platform charts measure platform behavior,
not market behavior. Every known chart-rule change is a dated series-break flag;
pre-break and post-break numbers are never compared without the flag named.

**US singles chart**

- A weighted combination of radio airplay + digital song sales + on-demand
  streaming (audio and video). Relative weighting is not published as fixed
  percentages; streaming's share of the formula has grown substantially over
  time.
- Paid/subscription streams and ad-supported streams are weighted differently;
  the ratio has been revised more than once, and any cross-boundary comparison
  must flag the revision. Video-stream inclusion has also changed; an act's
  exposure to a rule change depends on its video-stream share.
- Tracking window Friday–Thursday; chart published Saturday.
- Known gaming vectors: stream farming on bot networks; bundle/ticket packages
  with album purchase (rules tightened to require separate purchase); playlist
  add-velocity manipulation; chorus-first edits optimized for the 30-second
  completion threshold.

**US albums chart**

- Pure album sales + track-equivalent units + stream-equivalent units. The
  stream-to-unit thresholds differ for paid vs. ad-supported streams and have
  been revised; same series-break discipline applies.
- Known gaming vectors: multiple physical cover variants and exclusive
  direct-to-consumer bundles to inflate the pure-sales window; fan-organized
  streaming campaigns to maximize stream-equivalent units.
- Live-performance grosses are tracked separately and are venue-reported, not
  census-measured.

**UK singles chart**

- On-demand audio streams convert to sale-equivalents at a fixed ratio; paid and
  ad-supported audio both count; video streams count at a lower rate; downloads
  count at face value.
- Tracking window Friday–Thursday; chart published Friday. Streaming is the large
  majority of UK chart consumption. National radio rotation still meaningfully
  affects airplay-weighted position for mainstream acts.
- The stream-equivalency formula has been adjusted multiple times; pre-streaming
  positions are pure sales and not comparable to streaming-inclusive positions.

**Korea domestic chart**

- Tracks domestic on-demand streaming (Melon, Genie, FLO, and peers), download
  sales, physical sales, and short-form background-music usage. Separate charts
  per leg (streaming, download, physical, social, global).
- Physical sales reflect coordinated fan purchasing (multiple editions,
  photocards, signed copies, event-lottery tickets) rather than listening demand;
  the physical chart leg and the streaming leg require separate reads.
- Key gaming vector: coordinated fandom streaming during award-season voting
  windows, producing the structured spikes in the anomaly typology.

**Japan charts**

- Separate physical-singles, physical-albums, streaming, and digital-singles
  charts. Physical formats remain roughly half of Japan's recorded-music revenue,
  so the physical charts carry outsized significance relative to other markets.
- Physical variant strategy (limited editions, regional exclusives, event
  tickets) drives deliberate chart-period sales concentration; distinguish
  variant engineering from listening demand before benchmarking.
- The streaming chart launched later and uses different methodology — physical and
  streaming positions for the same release are independent signals, not a
  combined ranking.

**LatAm radio airplay**

- A radio-only metric across the region; it does not measure streaming
  consumption. A position indicates regional radio relevance, not digital
  consumption. Mexico carries roughly half the regional radio weight.
- Regional format-buying is a documented trade-press topic; cross-reference radio
  position against streaming data before concluding on genuine audience response.

**Germany / DACH chart**

- Streaming + downloads + physical combined into a consumption-unit equivalent;
  separate streaming-only charts available. Strong physical base; older
  demographics skew physical; German-language content has national-radio
  advantages. Austria and Switzerland are tracked separately for DACH reads.

---

## MARKET RESEARCH SOURCES

Measured vs. estimated is a caste line: third-party estimates may inform
direction, never serve as the measured basis of a high-stakes claim. When an
estimate is the only available input, it is the named weakest link capping
confidence.

- **Industry census data** (primary consumption measurement): a direct census
  from licensed partner platforms — not scraped or estimated. Coverage is
  strongest in its home market and weaker elsewhere; a "global" figure from a
  census source is a home-market-anchored estimate with significant non-home
  uncertainty. Appropriate for home-market benchmarks, chart verification, and
  consumption context; not for presenting as globally representative without
  flagging coverage gaps.
- **Annual global revenue reports** (trade-body aggregates): measure global
  recorded-music revenue by format and region; revenue-based, not stream-count
  based; some sub-market figures are self-reported with varying quality;
  publication lags the calendar year. Appropriate for macro market-size framing
  and format-shift evidence; never for benchmarking individual artist or release
  performance (different denominator entirely).
- **Third-party aggregators** (Chartmetric-class): ingest public DSP and social
  APIs and build proprietary estimates for non-public metrics. NOT licensed data
  partners. Appropriate for playlist-velocity monitoring, cross-platform reach
  comparison, and trend-direction confirmation; never as the measured basis of
  high-stakes decisions. Treat as estimated (lower trust tier). Procurement of
  paid aggregator tools is reserved for leadership sign-off; until bought, their
  public numbers are estimated inputs, never measured bases.
- **Radio/chart-monitoring services:** useful for radio-airplay monitoring and
  playlist tracking at scale across markets a census doesn't cover; radio
  monitoring uses audio fingerprinting, not broadcast logs — good but not
  log-precision. Treat as estimated.
- **National trade bodies:** self-reported certification and revenue data; high
  trust for certification thresholds (these are definitional), lower for
  market-sizing (self-reported by member labels).

---

## GLOBAL MARKET ANALYTICS

For calibrating whether a benchmark case or release strategy is over-indexed on
one market:

- Global premium streaming is concentrated — the largest single market is roughly
  a third of paid global streams, and the top four markets together are under
  half. A release strategy that ignores the remaining majority forfeits most of
  the global opportunity. (Current shares live in the reference layer; treat any
  specific percentage as date-stamped.)
- Regional growth is uneven — emerging regions (Latin America, the Middle East
  and North Africa, sub-Saharan Africa, parts of Asia) have been growing
  materially faster than mature markets, so their benchmark baselines rise each
  cycle. A flat year-over-year comparison against a fast-growing region
  understates expectation.
- High-growth, low-ARPU markets: where premium subscribers are growing fast but
  most listening is still ad-supported, a stream spike from that market carries
  lower per-stream revenue and lower chart weight than the same spike from a
  high-ARPU market — weight the revenue projection accordingly.

### Reference-class hygiene

- Comparable-case claims carry evidence tags (observed / told / inferred) and
  confidence; inferred benchmarks are hypotheses, never baselines.
- Comparable cases are characterized on the same judged dimensions used in the
  scorecard (trajectory shape, engagement depth, structural/format fit,
  positioning clarity), so "X resembles A" claims and rubric verdicts speak the
  same dimensions and prediction accuracy is comparable across both.
