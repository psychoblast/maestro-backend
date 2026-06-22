# Marketing Analytics & Attribution
Version: v1.0 — PLMKR Marketing Knowledge
Note: All benchmark figures labeled ESTIMATE / NOT QUOTABLE until confirmed against measured outcomes.

---

## The Measurement Stack

Marketing analytics has four distinct layers. Confusing layers produces wrong decisions.

| Layer | What it measures | Data source |
|-------|-----------------|-------------|
| **Reach layer** | How many people saw or heard the content | DSP impression counts, social platform reach, ad manager delivery |
| **Engagement layer** | How many people responded with a meaningful action | Save rate, completion rate, click-through rate, comment-to-like ratio |
| **Conversion layer** | How many people made a trackable commitment | Pre-save, email/SMS opt-in, ticket purchase, merch purchase |
| **LTV layer** | How much value each converted fan produces over time | Repeat purchase rate, subscription retention, catalog stream count per fan |

**Measurement rule:** never evaluate a channel using the wrong layer's metrics. Judging a TikTok discovery campaign on ticket-purchase conversions is a layer error — TikTok is a Reach/Engagement channel, not a Conversion channel without a proper mid-funnel bridge.

---

## UTM Taxonomy for Music Campaigns

UTM parameters track which link sources drove measurable downstream action. Without a consistent taxonomy, attribution is impossible — analytics dashboards become random noise.

**Standard UTM structure:**
`?utm_source=[platform]&utm_medium=[channel-type]&utm_campaign=[release-or-campaign-slug]&utm_content=[asset-id]`

**Source conventions (mandatory, consistent across team):**

| Source value | When to use |
|-------------|------------|
| `instagram` | Any link from Instagram profile, bio, or Stories |
| `tiktok` | Any link from TikTok bio, Spark Ad, or post |
| `meta_paid` | Meta Ads Manager-served placements |
| `tiktok_paid` | TikTok Ads Manager-served placements |
| `email` | Any link in an email campaign |
| `sms` | Any link in an SMS message |
| `spotify` | Spotify for Artists profile link, Canvas link |
| `youtube` | YouTube video description or end-card link |
| `press` | Any PR placement or editorial embed |
| `partner` | Co-promotion, playlist curator, or brand partner link |

**Medium conventions:**

| Medium value | Meaning |
|-------------|---------|
| `social` | Organic social post |
| `paid_social` | Paid placement on a social platform |
| `email` | Email campaign |
| `sms` | SMS campaign |
| `pr` | Press or editorial placement |
| `direct` | No referral; typed URL or bookmark |

**Campaign slug convention:** `[year]-[release-slug]-[phase]`
Example: `2026-debut-ep-prerelease`, `2026-tour-announce`

**Content ID convention:** `[format]-[variant]`
Example: `video-hook-a`, `static-presave-cta`, `story-swipeup`

**Anti-pattern:** using different UTM values for the same placement type across different campaigns. One team member using `ig` and another using `instagram` as the source value splits the data and makes cross-campaign analysis impossible.

**Mandatory: short-link layer.** Raw UTM URLs are unmanageable in social bios and text messages. Use a URL shortener with click tracking (bit.ly, Linktree, or a custom domain) as the outward-facing URL, with UTM parameters appended to the destination. Document the short link → UTM destination mapping in campaign records.

---

## Attribution Models: What They Are and When Each Is Wrong

An attribution model assigns credit for a conversion to one or more touchpoints in the path to that conversion. Every model has structural biases. Knowing the bias prevents wrong conclusions.

| Model | How credit is assigned | Best use | Structural bias |
|-------|----------------------|---------|----------------|
| **Last-click** | 100% credit to the last touchpoint before conversion | Simple campaign tracking; single-channel campaigns | Over-credits conversion channels; under-credits awareness channels that drove discovery |
| **First-click** | 100% credit to the first touchpoint | Evaluating which awareness channel introduced the fan | Over-credits awareness; under-credits the content that actually closed the conversion |
| **Linear** | Credit spread equally across all touchpoints | Understanding full-path contribution | Treats every touchpoint as equally important, which is rarely true |
| **Time-decay** | More credit to touchpoints closer to conversion | Campaigns with long consideration windows | Systematically under-credits early awareness that set the purchase condition |
| **Data-driven** | Credit weighted by statistical conversion contribution | High-volume, well-instrumented campaigns (>1,000 conversions/month) | Requires volume most music campaigns never reach; black-box bias |

**Music campaign attribution reality:** most music campaigns operate below the volume threshold needed for data-driven models. Last-click is the default because it is what ad platforms report by default — but it produces a systematic bias: paid retargeting and email (which touch warm audiences already created by organic content) appear to be the drivers, while the TikTok or press placement that created the warm audience appears to contribute nothing.

**Practical correction:** run two parallel views:
1. **Last-click (platform-reported):** what each paid channel contributed as the conversion touch.
2. **First-click (UTM analysis in web analytics):** what introduced the fan to the ecosystem. Pull this from your website analytics UTM source report, not from ad platform native attribution.

The gap between the two reports shows the awareness-to-conversion contribution you would miss if you relied on last-click only.

---

## Pixel and Tracking Architecture Setup

Before any paid campaign runs, the tracking infrastructure must be verified. Running paid spend without functioning pixels is spending budget you cannot attribute or optimize.

**Meta Pixel (Facebook/Instagram) setup checklist:**
- [ ] Pixel installed and firing on artist website (verify with Meta Pixel Helper browser extension before campaign launch)
- [ ] Standard events configured: `ViewContent` (any page view), `AddToCart` (merch), `Purchase` (completed order), `Lead` (email/SMS opt-in)
- [ ] Conversion API (server-side) implemented alongside browser pixel — reduces signal loss from iOS 14+ privacy changes (ESTIMATE: server-side events recover 15–30% of signal lost from iOS blocking; Tier C consensus)
- [ ] Custom audiences created: website visitors (30-day, 90-day), email list upload, social video viewers (25%+ watch time), purchasers

**TikTok Pixel setup checklist:**
- [ ] TikTok pixel installed and firing on artist website
- [ ] Same standard events as Meta configured
- [ ] Events API (server-side) implemented for the same iOS signal-loss reason
- [ ] Custom audiences: website visitors, video viewers, music app event triggers

**Streaming attribution limitation:** DSP platforms (Spotify, Apple Music) do not expose individual user data for attribution purposes. You cannot close the loop from an ad click to a Spotify stream or follow at the individual level. This is a structural gap in music marketing analytics. Practical workarounds:
- Pre-save/smart-link landing page with email capture as the conversion event (attributable)
- Correlate paid spend timing with Spotify for Artists follower growth and listener uplift in geographic windows (directional, not precise)
- Spotify for Artists "Source of Streams" report: shows what portion of streams originated from the artist's profile vs. playlist discovery vs. algorithmic — not individual attribution, but useful for understanding how listeners are arriving

---

## Streaming Attribution Windows

The Spotify editorial algorithm evaluates a new release in its first 7 days. Paid campaign timing must align with this window.

**Streaming attribution windows by signal type:**

| Signal | Attribution window | Why it matters |
|--------|-------------------|---------------|
| **Editorial algorithmic consideration** | Days 1–7 post-release | The algorithm's decision to include the track in Release Radar, Radio, and algorithmic playlists is largely set in the first week. Streaming velocity in Days 1–7 is the primary input. |
| **Discover Weekly eligibility** | Day 28+ of streaming history | A track needs at least one month of streaming history and a minimum save threshold before it becomes eligible for Discover Weekly recommendations. |
| **Spotify for Artists pitch window** | 7–28 days pre-release | The editorial pitch must be submitted during this window to be considered for editorial playlist placement on release day. Pitches submitted after release day are ineligible for the release-day editorial cycle. |
| **Release Radar inclusion** | Active during the week of release | Release Radar (Spotify's algorithmic new-music Friday playlist) serves a track only in the release week. Post-release, the track moves to non-dated algorithmic channels. |

**Campaign timing implication:** the paid campaign spend schedule should be heaviest in Days 1–3 post-release to drive save-rate signals to the algorithm. Budget deployed in Week 3 is amplifying catalog discovery mechanics, not editorial mechanics — different objective, different creative, different KPI.

---

## The Music Campaign KPIs That Matter vs. Vanity Metrics

Not all numbers are useful. The distinction between decision-grade metrics and vanity metrics is whether the number predicts future outcomes or just describes past activity.

### Decision-grade metrics (act on these)

| Metric | Why it is decision-grade |
|--------|------------------------|
| **Save rate (saves ÷ streams, Day 1)** | Primary algorithmic signal. Above 12% (ESTIMATE) signals listener intent and feeds the Spotify algorithm. Below 8% in a promoted release indicates the audience is not converting to intent. |
| **Completion rate vs. genre average** | Tracks with below-average completion are structurally penalized in algorithmic feeds. A track with 70% completion in a genre where 85% is average is losing algorithm distribution over time. |
| **Email/SMS opt-in rate** | The owned-channel conversion rate. Benchmarks vary by creative type; any rate below 2% on a dedicated pre-save/opt-in page deserves creative testing. |
| **Cost-per-email-opt-in (CPE)** | The actual cost of acquiring a fan you can re-engage without paying again. The single most important paid efficiency metric for long-term artist economics. |
| **Ticket conversion rate from email list** | What % of your email list buys tickets for a given show. Tracks the quality of the list; low conversion against list size indicates list decay or poor segmentation. |
| **Revenue per email subscriber per year** | LTV proxy. Average annual revenue (merch + tickets + D2C subscriptions) divided by list size. Tells you what each email subscriber is worth in dollars. |

### Vanity metrics (monitor, don't act on alone)

| Metric | Why it is insufficient alone |
|--------|------------------------------|
| **Total stream count** | Does not distinguish paid-from-fake from organic from algorithmic. Absolute numbers without save rate, completion rate, and source breakdown are uninterpretable. |
| **Total follower count** | Follower count tells you historical accumulation, not current audience health. A 500K-follower account with 0.5% engagement rate is weaker than a 50K-follower account with 8% engagement rate. |
| **Impressions / reach** | Reach is only meaningful in relation to the next downstream metric (engagement rate, click-through rate). High reach with low engagement is paid waste. |
| **Press mentions** | Quantity of press mentions without a conversion hook (email CTA, DSP link, ticket link) does not produce measurable fan conversion. |
| **Website traffic** | Unqualified. Traffic without an email opt-in, purchase, or DSP follow is a lost opportunity. The metric is meaningless unless the page has a conversion mechanism. |

---

## Campaign Post-Mortem Framework

Every significant campaign (release cycle, tour announcement, brand activation) should produce a structured post-mortem. Without a post-mortem, each campaign is a one-time spend with no learnings captured for the next one.

**The 5-section post-mortem structure:**

**Section 1 — Pre-campaign baseline**
What were the starting metrics? Follower count, monthly listeners, email list size, average engagement rate. Without a baseline, you cannot measure lift.

**Section 2 — Actual vs. projected performance by KPI**
For each KPI set at campaign start, document actual result vs. projection. The gap is the diagnosis. An artist who projected 50K streams in week 1 and hit 12K must understand which segment of the funnel underperformed — not just note that the number was low.

**Section 3 — Channel attribution summary**
By UTM source, which channels drove the most email opt-ins, pre-saves, and streaming links clicked? Were the high-spend paid channels producing the best CPA, or was organic outperforming paid on cost-per-acquisition?

**Section 4 — Decision points and what drove them**
What creative variants won? What audience segments performed? What budget shifts were made mid-campaign and what was the result?

**Section 5 — Carry-forward decisions**
Three specific things that will change in the next campaign based on this campaign's data. Without explicit carry-forward decisions, post-mortems are retrospective description rather than operational learning.

**Anti-pattern:** post-mortems conducted only when a campaign underperformed. The highest-value post-mortems are on campaigns that overperformed — they reveal which conditions produced the result so those conditions can be engineered again.

---

## Dashboard Architecture for an Artist Campaign

A campaign dashboard has three views with different audiences and cadences.

**View 1 — Daily operations (checked every 24–48h during campaign)**
- Paid ad spend vs. daily budget (are we pacing correctly?)
- Cost-per-result by ad set (is any ad set burning budget without results?)
- Save rate and completion rate from DSP (is the music converting?)
- Email opt-ins (day-by-day: is the list growing at projected rate?)
- Any anomaly flag: an ad account with sudden CPM spike, a creative with sudden engagement collapse

**View 2 — Weekly strategic (checked at end of each campaign week)**
- Total streaming performance: streams, listeners, saves, weekly trend
- Follower growth by platform (where is the audience building?)
- Paid campaign performance by channel: CPE, CPA by channel, ROAS on ticket/merch campaigns
- Email list size and week-over-week growth rate
- Any press pickups: tier, outlet, coverage type

**View 3 — Campaign close (assembled at end of campaign window)**
- All metrics vs. pre-campaign baseline (percentage lift)
- Full attribution summary by UTM source
- Post-mortem output (5-section framework above)
- Carry-forward decisions for next campaign

**Tool stack note:** the minimum viable dashboard for an independent artist campaign is: Spotify for Artists (streaming + audience data), Meta Ads Manager (paid social performance), website analytics (UTM attribution), and an email platform analytics view (list growth, open rate, click rate). No expensive custom stack required; the gap is not tools — it is a consistent measurement discipline.

---

## Structural Anti-Patterns in Music Marketing Analytics

**1. Comparing absolute numbers across artists without normalizing for catalog size**
An artist with 500 catalog tracks will always show higher total streams than an artist with 10 tracks. Compare monthly listeners, save rate, and engagement rate — not raw stream count — when benchmarking performance across different artists.

**2. Attributing streaming growth to the last action taken**
If streams spike the week after a press feature, the temptation is to attribute the spike to the feature. The spike may actually reflect a Discover Weekly add that resulted from the prior month's save rate accumulation. Correlation without looking at Spotify for Artists "Source of Streams" is not attribution.

**3. Abandoning a channel after one test**
One ad campaign that underperforms does not prove a channel is wrong. The most common failure is: testing a channel with insufficient budget to exit the algorithm's learning phase (Meta's learning phase requires roughly 50 conversion events before the algorithm optimizes — most music campaigns never hit this threshold on a single ad set).

**4. Optimizing for platform metrics rather than owned-channel conversions**
Platform follows, likes, and views are rented metrics — the platform owns the relationship. The decision-grade output of every campaign is growth in owned channels: email list, SMS list, and direct ticket/merch buyer database. Campaigns optimized only for social engagement produce platform dependency with no durable asset.

**5. No pre-campaign baseline**
The single most common analytics failure in music marketing. Without a documented starting point — followers, monthly listeners, email list size, engagement rate — there is no way to measure whether the campaign produced any lift. The baseline must be recorded the day the campaign begins, not reconstructed afterward from platform analytics history.
