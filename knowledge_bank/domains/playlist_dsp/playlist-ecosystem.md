# Playlist and DSP — Playlist Ecosystem

Two-layer file: GENERAL FRAMEWORKS (domain-neutral) + MUSIC MODULES (music-specific).

---

## LAYER 1 — GENERAL FRAMEWORKS

### Marketplace and algorithm reasoning

1. **Two-sided market.** Curation surfaces broker scarce listener attention against an
   oversupplied catalog. Value flows to whoever reliably matches the two; strategies that
   degrade match quality (mismatched placements, gamed signals) get repriced out by the
   platform sooner or later.
2. **Algorithms are engagement-feedback amplifiers.** They have no taste; they extrapolate
   observed behavior. The lever is therefore never "the algorithm" — it is the behavior of the
   first audiences the algorithm watches. Optimize the inputs (fit, early engagement), not the
   black box.
3. **Gamed signals get repriced.** Any signal that becomes purchasable loses ranking weight and
   gains enforcement attention. Schemes have negative expected value *before* penalties: they
   spend money teaching the platform to ignore the very signal bought, and the artist's account
   carries the enforcement risk.
4. **Placement value = exposure × conversion − decay.** A slot's worth is its real engaged
   reach, times how well the matched audience converts to owned audience, minus how fast its
   effect evaporates on removal. Valuing slots on follower counts alone fails all three terms.
5. **Surface concentration is fragility.** A catalog whose listening is dominated by one
   curation surface is one programming decision from a cliff; portfolio thinking applies to
   placements as to anything else.

### The matching logic (fit gate, then outcomes)

Target matching runs as a **necessary-not-sufficient token gate first, ranking second.** Genre
is tokenized (compound genres decomposed), and an *all-tokens-must-match* rule excludes any
target missing a required token *before* any pitch prose is written. Surviving targets are then
ranked by tier and by **observed response rate** — fit gates, outcomes rank. The judged
playlist-fit dimension sits on top of the token gate; passing the gate is the floor, not the
verdict.

---

## LAYER 2 — MUSIC MODULES

### The three playlist economies (never aggregated)

- **Editorial (platform-curated):** human gatekeepers, calendar-driven, pitch-tool access only.
  Adds are high-reach, position-sensitive, and removable at refresh; post-removal volume goes
  with the slot. Programming logic favors fit with the list's audience contract, freshness, and
  platform priorities.
- **Algorithmic (personalized):** no gatekeeper to pitch; "access" = eligibility + engagement
  signals (saves, completion, source diversity). Compounding and durable when earned; collapses
  when early engagement is bad — which is exactly why pitching an unfit song onto a big list
  damages the *algorithmic* future too.
- **Independent / user (third-party curated):** human curators of wildly varying health and
  honesty; the vetting burden is on us (bot-farm detection protects the artist's account and
  data). Reach is smaller, but conversion can beat editorial when fit is tight.
- **Strategy memos must name which economy each move targets** and what the cross-economy
  sequence is. A reasonable default sequence: independent/user traction first (fast feedback,
  cheap fit-test), an editorial case built on demonstrated engagement, and algorithmic
  compounding protected throughout by refusing unfit placements. Sequence claims are logged
  predictions, not certainties — the outcome corpus re-prices them over time.

### The editorial decision model (what the gatekeeper is actually risking)

Editorial teams across platforms share a core question: *"Will adding this song to this
playlist make listeners more likely to complete, save, and return to the list?"* Their risk is
not missing a great song — it is adding a song that degrades playlist engagement and erodes
listener trust. Decision drivers, in rough priority:

1. **Fit with the list's audience contract** — the emotional/genre/occasion promise the list
   makes its listeners; a mismatch is an immediate pass regardless of quality.
2. **Artist trajectory signals** — any momentum, engagement anomaly, press, or social activity
   that reduces the team's risk in betting on this artist.
3. **Timing** — editorial calendars, format refresh cycles, genre release density in the window.
4. **Pitch quality** — does the submission communicate fit clearly, quickly, without oversell?

What editorial teams do *not* weight heavily: follower count (weak signal), promotional budget
plans (irrelevant to fit), and promises of future performance (invalid).

### Post-placement analytics (the placement verdict)

- **The add is a hypothesis test.** Read after placement: save rate by source, skip/completion
  behavior, follow conversion from the placement cohort, position and time-on-list, and the
  removal pattern. Metric definitions and cohort discipline are consumed from the data and
  analytics discipline rather than redefined here.
- **Retention is the second KPI.** A placement that converts none of its exposure to owned
  audience scores as exposure *rented*, not won.
- **Removal post-mortems route differently:** list refresh (neutral), under-performance (our
  fit call was wrong — log the miss), or list death (their problem, not ours).
- **No invented benchmark bands.** Until enough tracked placements resolve to anchor "good" by
  economy and list size, post-placement reads use cohort discipline with verdicts and named
  caps — never fabricated retention numbers. The numeric bands unlock only once a sufficient
  corpus of resolved placements exists per economy.
