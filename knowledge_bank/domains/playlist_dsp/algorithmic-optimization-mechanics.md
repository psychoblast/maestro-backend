# Playlist and DSP — Algorithmic Optimization Mechanics

Two-layer file: GENERAL FRAMEWORKS (domain-neutral) + MUSIC MODULES (music-specific).
All benchmark figures (save-rate targets, completion thresholds, window lengths) are ESTIMATES
unless confirmed against measured campaign data. Algorithmic mechanics are opaque by design
and change without announcement; re-verify assumptions against observed outcomes each cycle.

---

## LAYER 1 — GENERAL FRAMEWORKS

### Algorithmic access vs. editorial access — the distinction that matters

Algorithmic surfaces have **no submission channel, no curator to persuade, and no calendar
window**. The only programmable lever is the quality of the behavioral signals the algorithm
observes from real listeners. This is a fundamentally different discipline from editorial
pitching, and the two are too often conflated:

- **Editorial:** a pitch persuades a human to make a placement decision. Relationship, timing,
  and pitch quality are the levers.
- **Algorithmic:** observed listener behavior signals quality and fit to a ranking system.
  Engagement quality, source diversity, and early-window signals are the levers.

The common error is attempting to "pitch" algorithmic surfaces, or assuming that an editorial
add automatically triggers algorithmic lift. The editorial-to-algorithmic chain is real but
specific: the editorial add exposes the song to a new listener cohort; that cohort's behavior
then signals to the algorithm. If the cohort engages well, algorithmic lift follows. If not —
or if the editorial placement is onto a mismatched list — the algorithm learns from the bad
engagement and suppresses push. A mismatched editorial add can damage algorithmic prospects,
not just waste the slot.

### Signal hierarchy — what algorithms measure

Across platforms, the behavioral signal stack follows a rough priority order (specifics differ
by platform and surface; verify against observed outcomes):

1. **Save / library add** — the highest-value intent signal available to listeners. A save
   says "I want to hear this again without searching for it." On platforms where the save-rate
   signal is heavily weighted, an ESTIMATE working target for strong algorithmic seeding is
   north of ~12% of streams in the first ~72 hours — but validate this against measured
   campaigns before treating it as a threshold. Save rate is the single metric most worth
   monitoring in the first post-release window.

2. **Completion rate vs. genre baseline** — finishing a track signals a satisfying listen.
   Completion rate is meaningful relative to a genre baseline (not absolute), because genre
   conventions differ (a 6-minute jazz track has a different completion expectation than a 3-
   minute pop track). Completion materially below the inferred genre baseline suggests either
   a fit problem (the audience reached is not the right one) or a structural problem with the
   track itself (a weak outro, a drawn-out instrumental passage). The algorithm has no sympathy
   for the artist's intent — it reads behavior.

3. **Early-skip rate (opening-seconds problem)** — on most algorithmic surfaces, a skip in
   the first 15–30 seconds is treated as a stronger negative signal than a skip at 90 seconds.
   This is because the first seconds test whether the algorithm's contextual prediction was
   correct; an early skip means the match was wrong. The practical consequence: the opening
   seconds are not just a creative choice — they are an algorithmic targeting signal. Slow
   intros, dead air, and genre mismatch before the hook arrive are optimization errors as much
   as creative ones. The specific penalty window varies by platform; "opening 30 seconds" is
   a reasonable working assumption to re-verify.

4. **User-playlist adds** — organic adds to personal playlists by listeners signal sustained
   personal affinity (not just a one-time listen). These adds compound over time and indicate
   a listener is building a habit around the song. They are distinct from editorial-playlist
   adds and are harder to manufacture; they come from genuine fit and listener affinity.

5. **Follow conversion from discovery surfaces** — when a listener who finds the song on a
   discovery surface then follows the artist, it signals the song was both a fit for that
   listener and an effective artist introduction. Follow conversion from algorithmic-discovery
   placements is a stronger signal than follows from editorial adds (the editorial add delivers
   a more heterogeneous audience).

6. **Re-listen rate** — repeat plays from the same user within a session or across sessions.
   This is a meaningful signal on platforms where it is observable; an unusually high re-listen
   rate can compensate for a modest first-listen completion rate because it signals the listen
   was active, not passive.

**Negative signals (suppress algorithmic push):**
- High early-skip rate in the first ~30 seconds.
- Low completion rate relative to genre baseline.
- Below-baseline save rate in the critical early window.
- Sources with non-diverse listener behavior (e.g., bot-pattern play clusters, a single repeat
  listener generating an outsized share of streams).

### Source diversity as a signal quality modifier

Algorithms are not just tracking behavior — they are tracking *who* is behaving. Signals from
a diverse, independently-originating listener pool are weighted more heavily than the same
signals from a concentrated source. This means:

- A small editorial add that reaches the right audience cohort can seed better algorithmic
  signals than a large add that reaches a mismatched one.
- Organic saves and adds from genuinely different listener sources (different devices, different
  accounts, different geographic origins) are more valuable than equivalent volume from a
  concentrated source — even an organic one.
- An artist whose first listeners are all from one social platform's referral carry a source
  concentration risk: if that pipeline pauses, the algorithm sees a sudden signal change.

The implication is that a multi-channel release strategy (independent playlists, social, DSP
editorial, and direct fan outreach all driving to the same track in the early window) generates
stronger algorithmic seeding than a single-channel push, *even at equal total volume*.

---

## LAYER 2 — MUSIC MODULES

### The editorial-to-algorithmic amplification chain (the full model)

An editorial playlist add is a **seeding event** for algorithmic surfaces, not a guaranteed
lift. The chain runs as follows:

1. **The editorial add** exposes the song to the list's listener cohort for as long as the
   song occupies a position on the list.
2. **That cohort's behavior** — save rate, completion, early skips — is now observable by the
   platform algorithm. If the cohort engages well, the algorithm infers: "this song worked
   well with listeners who share properties of this cohort."
3. **Personalized surfaces** then begin to expose the song to listeners who share those
   cohort properties, even without a pitch or further editorial action.
4. **The chain breaks** if: the editorial placement is onto a list whose listeners are a poor
   fit for the song (engagement is bad → algorithm suppresses push), the editorial slot is
   brief (too few behavioral data points collected), or the track has already accumulated
   negative signals from prior placements.

Practical consequences:
- Pitch onto well-fit editorial lists, not big lists. A top-200 list with engaged, fit
  listeners seeding better algorithmic signals than a top-50 list whose listeners skip early.
- Monitor save rate by source, broken out by the editorial-placement cohort specifically.
  A high-aggregate save rate masking a poor-save-rate from the editorial cohort is a fit
  problem on that list.
- If the goal is algorithmic seeding, a position in the first half of a list (earlier in
  the listening session, before listener attention wanes) matters. A position near the back
  of a long list has lower effective exposure than a mid-list position. This is not pitchable
  — it is a post-add optimization context.

### Pre-save mechanics and their algorithmic value

A pre-save (sometimes called a "pre-add") is a listener action taken before a release goes
live that automatically adds the track to the listener's library or "liked" songs on release
day. Pre-save mechanics vary by platform; not all platforms natively support them from the
editorial pitch tool — some require third-party pre-save landing pages aggregating cross-
platform actions.

**Algorithmic value of pre-saves:**
- A pre-save converts to an automatic library add on release day. This means the save signal
  fires without any additional listener decision at release — the listener already expressed
  intent. Where save rate is a primary early-window signal, pre-saves can give a track a
  statistical head start in the first 24–72 hours.
- Pre-save count is a data point for tracking fan intent pre-release; it does not directly
  appear as a platform-facing signal in the same form as a post-release save.
- The gap between pre-save count and post-release engagement (listeners who pre-saved but
  then did not complete or re-listen) is diagnostic data for the marketing team, not a
  playlist signal.

**Operational requirements:** pre-save campaigns require the release to exist in the
distributor's system with a confirmed release date and working catalog links. Broken pre-
save links (from metadata changes, distributor delays, or date shifts) generate friction
exactly when artist-fan momentum should be highest. A pre-save link quality check is a
standard pre-release checklist item.

### Release velocity and its interaction with algorithmic surfaces

**Release velocity** refers to how frequently an artist releases new material. Its
interaction with algorithmic surfaces is complex:

- **High release velocity** keeps an artist's name appearing in follower-facing new-release
  feeds (where these exist). It also feeds the algorithm more recent behavioral data about
  what this artist's listeners do. For artists building a streaming-first catalog, regular
  releases compound over time.
- **Low release velocity** concentrates listener expectations into fewer events; each release
  carries more weight and risk. A single release after a long gap needs a stronger algorithmic
  seeding campaign because there are fewer recent data points for the algorithm to extrapolate
  from.
- **Lead-time between releases** affects the follower-reach surface: some platforms require a
  minimum gap between releases to qualify for the follower-facing new-release feed. Releasing
  too frequently can exclude a track from this surface. The working assumption is a gap of
  several weeks, but this is a platform-specific rule to verify against the live platform
  documentation each cycle.

### Discovery-enrollment programs (the royalty-reduction tradeoff)

Several platforms offer **catalog enrollment programs** that increase the likelihood of a
track appearing in radio/autoplay and personalized discovery surfaces, in exchange for a
reduced royalty rate on streams generated through those surfaces. The decision framework:

| Scenario | Enrollment verdict |
|---|---|
| Evergreen catalog track, not currently generating significant royalty income | Consider: the discoverability lift has a low opportunity cost |
| New release in the first royalty window | Do NOT enroll: you trade full-rate streams at peak for discoverability you may not need |
| Track with active sync or editorial placement activity | Evaluate: enrollment may conflict with royalty maximization in the active window |
| Track with a significant fan base still actively streaming at full rate | Do NOT enroll: you reduce royalties for listeners who were already finding the song |
| Artist early in their career, catalog-building, prioritizing discovery | Strong candidate: the discoverability lift may outweigh the per-stream rate reduction |

**The core principle: enrollment trades royalty rate on enrolled streams for higher
probability of appearing in non-pitch surfaces.** It is not cold-audience acquisition; it
amplifies within the platform's existing recommendation engine. It is best for evergreen
catalog, not active releases. Never enroll a track where the full royalty rate matters — and
confirm the specific royalty reduction percentage against the current platform terms before
recommending, as these change.

### Cross-platform signal spillover (the sequencing argument)

Algorithmic surfaces on one platform cannot read behavioral signals from another — each
platform's algorithm is isolated. However, **attention spillover** creates indirect coupling:

- A song trending on the video-first platform (completion, shares, comments) generates social
  currency (shares, user-generated clips, comment culture) that drives direct search and
  organic streams on audio platforms. Audio-platform algorithms then see a sudden,
  organically-sourced listen cluster — which looks like strong early-window engagement.
- This is the documented "video trend → audio radio/autoplay lift → editorial consideration"
  sequence referenced in platform mechanics. The mechanism is: video creates attention →
  attention drives organic search/play on audio → organic audio signals are high-quality
  algorithmic inputs.
- The practical implication: a video-first platform promotional push, timed to coincide with
  an audio platform release window, creates better algorithmic seeding conditions than either
  channel alone — not because the algorithms talk to each other, but because organic attention
  translates into high-quality behavioral signals on the audio platform.

### Algorithm-hostile patterns (common errors)

These behaviors degrade algorithmic performance and are not always obvious to artists:

| Pattern | Why it harms algorithmic performance |
|---|---|
| Pitching a mismatched editorial list for the size | Bad cohort fit → poor early engagement → algorithm suppresses |
| Releasing too many singles with no gap between them | May block follower-reach surface eligibility on platforms with gap requirements |
| Long, atmospheric intros before the hook | Early-skip signal fires before the track establishes itself |
| Streaming incentive programs (fan contests for streaming) | Concentrated, artificial listening patterns are distinguishable from organic behavior |
| Enrolling in discovery programs on an active-royalty release | Trades full-rate streams at peak revenue moment |
| Over-relying on one source channel (e.g., a single social referral) | Source concentration reduces signal value; diversity is a signal quality modifier |
| Pre-saves linked to a catalog entry with a pending metadata change | Broken links at launch erode listener intent conversion |

None of these are recoverable from after the early window closes. The algorithm has already
scored the first-72-hour signal cluster. Algorithmic optimization is not a post-launch fix —
it is a pre-launch preparation discipline.
