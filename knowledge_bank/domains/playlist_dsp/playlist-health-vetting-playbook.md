# Playlist and DSP — Playlist Health Vetting Playbook

Two-layer file: GENERAL FRAMEWORKS (domain-neutral) + MUSIC MODULES (music-specific).
Follower-to-stream ratio benchmarks and engagement thresholds are ESTIMATES unless confirmed
against a measured set of known-healthy and known-fraudulent playlists. Vetting signals
change as fraud detection and playlist mechanics evolve; re-verify methodology each cycle.

---

## LAYER 1 — GENERAL FRAMEWORKS

### Why vetting is non-negotiable

The artist's streaming account and platform standing are the foundation everything else sits
on. A fraudulent-listener playlist placement damages the artist's account in two ways that
survive removal of the playlist:

1. **Bad listening data permanently enters the artist's analytics corpus.** Bots and farm
   streams inflate total stream counts while contributing zero real engagement signals. This
   distorts the artist's genre-audience profile in platform recommendation engines, routing
   future recommendations to the wrong listeners. The damage is self-reinforcing: the
   algorithm routes to wrong audiences → those audiences engage poorly → the algorithm
   reduces push further.
2. **Enforcement risk is real and asymmetric.** Platforms have increasingly sophisticated
   detection for artificial streaming. When detected, penalties include stream count removal,
   royalty withholding, demotion, and in repeat cases, account suspension. The artist bears
   this risk; the fraudulent playlist curator does not. Association with known fraud-adjacent
   networks can flag the account even when the artist was unaware.

The vetting playbook exists to protect the artist's account before committing to a target —
not as a post-send quality check. **A target that fails the vet is blocked; it is not
subject to artist override.** This is a hard block.

### What is publicly observable vs. tool-gated

Before running any paid analytics tool, establish what is publicly observable from the
platform interface, because this data costs nothing and surfaces the most obvious red flags:

**Publicly observable (no tool required):**
- Playlist follower count (shown on the public playlist page on most platforms)
- Track count and recency of additions (visible from the playlist itself)
- The curator's public identity and cross-platform presence (or absence)
- Whether the curator maintains multiple playlists and their relative sizes
- Submission-fee signals in the curator's public bio, submission form, or social presence
- Presence on community lists of flagged fraudulent curators (maintained in practitioner
  communities and some analytics tool databases)

**Tool-gated (requires a third-party analytics or playlist-tracking service):**
- Historical follower growth trajectory (gradual organic vs. spike-and-plateau from a buy)
- Streams-per-follower ratio at playlist level (ESTIMATE: healthy playlists tend to show
  meaningful monthly stream volume relative to follower count — see thresholds below)
- Add-to-removal churn rate (how many tracks cycle in/out vs. sitting stably)
- Listener-geographic distribution (a playlist with 90%+ listeners from one atypical region
  for the genre is a bot-clustering signal)
- Save-to-stream ratio from placement cohort (observable from the artist's analytics if
  already placed, as a retrospective check)

The publicly-observable signals are sufficient to disqualify most obviously fraudulent
targets. Tool-gated signals are used for borderline cases and for maintaining an ongoing
curated, vetted target list.

### The principle of evidence hierarchy in vetting

Vetting conclusions follow the same evidence hierarchy as all other assessments in this
domain:
- **Observed facts** (actual stream counts, actual growth charts, documented fee-for-add
  offers) carry the most weight.
- **Told facts** (curator's stated submission policies, platform team's stated editorial
  standards) carry next-most weight.
- **Inferred signals** (a suspiciously fast follower growth that *suggests* a follower buy,
  a region-concentration that *suggests* bot farms) are hypotheses that flag for deeper
  investigation — not automatic disqualification on their own, but automatic soft-block
  pending investigation.

A single strong disqualifier overrides all positive signals. A collection of soft concerns
without a hard disqualifier may proceed with explicit flagging.

---

## LAYER 2 — MUSIC MODULES

### The vetting process — step by step

**Step 1: identity and association check**
- Does the curator have a real cross-platform identity (social presence, a public persona,
  a business or blog associated with the playlist)?
- Is the curator associated with any known fraudulent playlist network? (Check any community-
  maintained blocklists available through analytics tools or practitioner forums.) If yes:
  **hard block — do not proceed.**
- For new curators not on any list: a complete absence of any external identity is a soft
  concern. Proceed to Step 2.

**Step 2: fee-for-add check**
- Does the curator publicly advertise a fee for guaranteed playlist placement, offer
  "playlist promo packages" with quantified add guarantees, or solicit payment anywhere in
  their submission flow?
- **If yes: hard block — immediate disqualification.** This is pay-for-play by the curator.
  It violates platform terms, it means the add is not an earned signal, and the playlist
  is likely a fraud vehicle. The disqualification is permanent for that curator.
- If the curator charges a submission *review fee* (payment to receive a considered listen,
  without a guaranteed placement), this is a separate category from pay-for-play guarantees.
  It is still a yellow flag deserving scrutiny — a curator who is primarily monetizing the
  submission process rather than the quality of the playlist is a different risk profile
  than a curator who is primarily monetizing the playlist through legitimate means (editorial
  curation fees from labels, brand partnerships). Note the distinction and flag it; do not
  automatically disqualify.

**Step 3: follower-to-stream ratio assessment**
The ratio of a playlist's monthly streams to its follower count is the primary engagement
plausibility check. ESTIMATES for working ranges (re-verify against confirmed healthy/fraud
examples in your analytics tool):
- **Plausible range:** 0.5x–10x monthly streams per follower for an active, normal genre
  playlist (wide range reflects genre and listener behavior differences). A very active
  editorial-adjacent playlist may run higher; a niche genre playlist may run lower.
- **Suspicious ranges:**
  - Very high (>15x–20x monthly streams per follower) may suggest artificial stream
    inflation (bots generating streams without a listener base), or a featured/viral moment.
    Investigate growth history before deciding.
  - Very low (<0.1x monthly streams per follower) suggests the follower count is inflated
    (bought followers, inactive audience) while streams reflect a small real listenership.
    This is a more common fraud pattern: a high-follower-count, low-stream playlist sold
    for its apparent reach.
- These ranges are **ESTIMATES** — validate them against your analytics tool's flagged-
  fraud database before relying on them as thresholds. Never present them as confirmed
  platform data.

**Step 4: growth trajectory analysis**
- Organic playlist growth is gradual and correlated with the curator's activity, mentions,
  and genre community cycles. It looks like a rising line with realistic fluctuation.
- Purchased-follower injections produce a characteristic spike-then-plateau pattern: rapid
  growth over days or weeks, followed by a flat line with no organic upward drift. This
  pattern is visible in most analytics tools' historical growth charts.
- Multiple spike-plateau cycles indicate repeat purchases — this is a managed fraudulent
  operation, not a one-time mistake.
- **Assessment rule:** one spike-plateau with an explanation (a viral moment, a feature, a
  press mention that can be date-correlated) is inconclusive. Multiple spikes without
  corresponding organic events: **soft block — investigate further before proceeding.**

**Step 5: add-and-removal churn check**
- A healthy playlist evolves — new tracks come in, old ones sometimes cycle out — but has a
  stable core of established tracks and does not wholesale replace its contents.
- A high-churn playlist (most tracks replaced every 2–4 weeks, very few tracks sitting
  longer than a few weeks) suggests the curator is operating a pay-to-play rotation
  (charging multiple rounds of artists) rather than genuine curation.
- A very low-churn, very static playlist that has not refreshed in 6+ months may have an
  inactive or disengaged curator — a soft concern for pitch value, not a fraud signal.
- **Assessment rule:** churn rate above roughly 50% monthly is a soft block. Combined
  with a fee-for-add signal: hard block.

**Step 6: listener geographic distribution check**
- A genre-appropriate playlist should have listeners distributed across the expected
  listener geography for that genre. A hip-hop playlist should have meaningful US/UK/Canada
  listener share; an Afrobeats playlist should have a West African and diaspora footprint.
- A playlist where 80%+ of listeners originate from a single, genre-unexpected country
  (especially common bot-farm locations) indicates artificial listener generation.
- This check is most powerful when combined with a low-engagement signal: a playlist
  claiming a North American audience should show engagement from that geography; if the
  listeners are actually in a bot-farm geography, real-listener engagement will be missing.

**Step 7: genre and audience fit confirmation**
- Even a healthy playlist that passes all vetting checks may not be an appropriate pitch
  target if its audience is not a match for the track. Vetting confirms the *safety* of a
  target; fit confirmation is a separate gate (handled by the token fit gate and P1 judged
  verdict in the scoring rubric). Do not conflate the two.
- A fully vetted, healthy target that fails the genre-token fit gate is a safe target for a
  different track — log it and move on for now.

### Vetting outcome states and their pitch-permission consequences

| Vetting outcome | Evidence basis | Pitch permission |
|---|---|---|
| **CLEARED** | No red flags; plausible engagement; organic growth trajectory | Pitch permitted — fit gate and P1 still run separately |
| **CLEARED (noted)** | No hard disqualifiers; one soft concern acknowledged | Pitch permitted with explicit note in target record; re-vet at next pitch |
| **SOFT BLOCK** | One or more soft concerns without a hard disqualifier | Pitch paused; investigate further before proceeding |
| **DISQUALIFIED — fee-for-add** | Public fee-for-guaranteed-add offer observed | Hard block; do not pitch; mark target as permanently disqualified |
| **DISQUALIFIED — fraud signals** | Bot-growth pattern + atypical geographic distribution + low engagement | Hard block; mark target as permanently disqualified |
| **DISQUALIFIED — network association** | Confirmed membership in a known-fraudulent playlist network | Hard block; mark entire network; do not pitch any curator in the network |

### Target record maintenance after vetting

Every vetted target is logged in the curator/playlist memory with:
- **Vetting date** (vetting results are perishable; re-vet every 3–6 release cycles or after
  any anomalous platform behavior from this target)
- **Vetting outcome state** from the table above
- **Evidence summary** with evidence tags (observed/told/inferred) for each key signal
- **Fee-for-add check result** and any noted fee structure (told or observed)
- **Growth trajectory summary** (gradual organic / spike-plateau / inactive / unclear)
- **Engagement plausibility verdict** (plausible / suspicious-high / suspicious-low)
- **Genre distribution alignment** (aligned / misaligned — flag if the latter)

A vetting record that is more than 6 months old is flagged for re-vetting before the next
pitch. Fraudulent operations evolve; a once-clean target can become compromised.

### Curators who charge submission review fees — the nuanced case

Some legitimate curators charge a non-refundable fee to receive a guaranteed *listen* (not a
guaranteed *placement*). This is distinct from pay-for-play in principle but similar in
appearance. Evaluation framework:

- **Review fee with no placement guarantee, curator publicly stands by their editorial
  independence:** treat as a vetting flag — note the fee, check if the curator's adds appear
  correlated with submissions (suggesting de facto pay-to-play) or genuinely selective
  (adds across fee-paying and non-fee sources). If the adds appear editorially independent,
  the review fee is a business model, not a fraud signal.
- **Review fee combined with "we add the majority of submissions" language:** effectively
  a pay-for-add. Hard block.
- **"Review fee" with no public persona, no observable curation history, no way to verify
  how submissions are handled:** insufficient data — treat as soft block and investigate
  before paying or recommending the spend.

In all cases: **the artist authorizes any spend; this discipline recommends and flags,
it does not authorize payment.** Escalate to the owner before recommending any fee-based
submission route.
