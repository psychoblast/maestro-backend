# Campaign Architecture & Fan Acquisition
Note: All benchmark figures labeled ESTIMATE / NOT QUOTABLE until confirmed against measured outcomes.
Source tiers: **Tier A** = platform-disclosed data, regulatory standards, or peer-reviewed; **Tier B** = named industry research firm (Forrester, Gartner, HubSpot annual reports); **Tier C** = established practitioner research with disclosed methodology; **Tier D** = aggregated practitioner consensus. ESTIMATE = practitioner-consensus range; NOT QUOTABLE for external use.

---

## Full-Funnel Campaign Architecture

A marketing campaign is a sequence of audience state transitions, not a set of deliverables. Four stages:

**Awareness (TOFU):** Target has no mental model of the artist. Goal: first qualified impression. Channels: algorithmic discovery (TikTok/Reels, Spotify Radio), paid prospecting (Meta lookalike audiences, YouTube pre-roll), PR/editorial placement. KPI: reach to target-adjacent audiences — impressions to people who consume similar artists in the same genre and territory.

**Consideration (MOFU):** Target has had ≥1 exposure and is being moved toward intent signals. Goal: convert passive exposure to active engagement. Channels: owned social (artist profile, content series), streaming profile engagement (DSP follows, pre-adds), retargeting ads (served only to TOFU-engaged audiences). KPI: saves, pre-adds, profile follows, audio completion rate, link-in-bio clicks.

**Conversion (BOFU):** Intent signal is present. Goal: transaction decision — ticket purchase, merch, D2C subscription, email/SMS opt-in. Channels: direct (email, SMS), D2C storefront, social commerce. KPI: conversion rate, average order value, cart abandonment rate.

**Retention:** Post-first-conversion. Goal: repeat engagement and peer advocacy. Channels: email/SMS lifecycle sequences, fan community platforms (Discord, Patreon, Circle), exclusive-access campaigns, catalog surfacing. KPI: repeat purchase rate, referral rate, fan LTV over 12/24 months.

**Architecture rule:** campaigns that skip MOFU convert poorly because intent was never built. Campaigns that skip Retention convert expensively because every buyer must be acquired cold again. Win-back campaigns are typically 3–5× cheaper per conversion than cold prospecting (ESTIMATE).

## Audience Segmentation Logic

Segment by intent signal proximity, not demographic proxy:

| Segment | Definition | Serve | Paid budget? |
|---------|-----------|-------|-------------|
| **Core fans** | Ticket buyers, merch purchasers, email/SMS subscribers, consistent social engagers | Exclusive access, first-mover offers, community | No — already captured |
| **Warm audience** | DSP savers/followers, playlist adds, story viewers/completers, retargetable | Conversion-focused creative, pre-add CTAs, pre-sale links | Yes — highest ROI |
| **Cold audience** | Algorithmic impressions, cold paid reach | Awareness-only creative; no conversion CTA | Yes — lowest ROI; volume play only |
| **Lapsed fans** | Previously engaged (90+ days inactive) | Win-back sequences, catalog campaigns | Small — 3–5× cheaper than cold (ESTIMATE) |

**Audience research inputs required before channel allocation:**
1. Current audience concentration by platform and territory (DSP analytics, social analytics)
2. Core fan intent signals: save rate, completion rate, DM volume, historic ticket conversion rate
3. Audience overlap with comparable artists (Spotify for Artists "Fans Also Like")
4. Competitive attention environment: what else are target listeners consuming in this release window
5. Platform algorithm state: any recent changes to discovery mechanics in this genre/territory

**Anti-Pattern:** Do not confuse "target audience" with "current audience." Expanding reach to a new demographic requires understanding where that demographic's attention already lives, not where current fans are.

## Budget Allocation Framework

| Campaign Type | Owned + Earned | Paid | Rationale |
|--------------|---------------|------|-----------|
| Catalog campaign | 60% | 40% | Algorithm rewards engagement history |
| New release (indie/emerging) | 40% | 60% (first 2 weeks) | Early-week velocity signals drive editorial |
| Brand or event launch | 30% | 70% | Time-bounded window requires reach at scale |
| Tour announcement | 50% | 50% | PR/earned handles narrative; paid drives ticket conversion |

**Channel-allocation rule:** allocate to the channel where the marginal dollar produces the most measurable progress toward the campaign's primary KPI.

**Diminishing returns rule:** once any single channel exceeds ~40% of total campaign budget, diversify. Diminishing returns is not aesthetic — it is mathematical.

**Budget gates (before any spend recommendation):**
1. Can the spend be attributed to a measurable KPI? If not, do not recommend it.
2. Has the channel been tested at small scale? Cold prospecting deserves 10–15% of total paid budget until it proves CPA.
3. Is the timing correct? Paid spend before earned content exists to amplify wastes budget.

---

## Release-Cycle Marketing Framework (12-Week Arc)

[ESTIMATE / NOT QUOTABLE — typical indie/mid-level release. Marquee releases extend to 16–20 weeks.]

**Phase 1 — Pre-awareness (Weeks -12 to -6)**
Goal: build cultural narrative before the music exists publicly.
KPI: social follower growth rate, press pickup, Spotify pre-add count.
Creative mandate: establish what this release *means*, not what it sounds like.

**Phase 2 — Pre-release momentum (Weeks -5 to -1)**
Goal: convert cultural awareness to intent signals (pre-saves, pre-adds, press placements).
Channels: DSP editorial pitch (7+ days pre-release), social content escalation (15-sec audio hook reveal), email/SMS pre-save push, influencer seeding (organic listeners with high engagement rate, not just follower count).
KPI: pre-save velocity, Spotify for Artists follows added, editorial pitches submitted, influencer pickup rate.

**Phase 3 — Release week (Day -1 to Day +3)**
Goal: first-day streaming velocity for algorithmic pickup; press coverage window.
KPI: saves-to-streams ratio on Day 1 (target >12% ESTIMATE — signals listener intent to algorithmic systems), editorial adds within first 72 hours.
Critical: spend paid budget to drive saves, follows, and playlist adds — not raw stream counts. Stream padding is expensive noise.

**Phase 4 — Consolidation (Weeks 1–4 post-release)**
Goal: sustain streaming velocity; convert new listeners to followers and core fans.
KPI: week-over-week stream rate retention (target >70% of Week 1 ESTIMATE), follower growth, completion rate vs. genre average, user-generated playlist adds.

**Phase 5 — Catalog conversion (Weeks 5–12+)**
Goal: route new listeners into the artist's back catalog.
KPI: catalog stream lift, listener-to-follower conversion rate, user-generated playlist adds on catalog tracks.

## Fan Acquisition Channels for Artists

**Algorithmic — low control, high ceiling for breaking artists:**
- *TikTok/Reels discovery:* highest fan-acquisition ceiling per dollar for sub-10M profiles. Algorithm rewards audio completion rate and reshares, not follower count. Spark Ads only on content with proven organic engagement (>5% engagement rate ESTIMATE). Boosting low-engagement content trains the algorithm to deprioritize the account.
- *Spotify algorithmic (Radio, Autoplay, Release Radar, Discover Weekly):* earned by winning the save-rate and completion-rate race in Phases 2–3. Not a paid channel — the downstream reward for the first-week KPI campaign.
- *YouTube algorithm:* highest catalog monetization channel for established artists.

**Editorial — earned, relationship- and timing-dependent:**
- *Spotify for Artists editorial pitch:* 500 characters; submit 7+ days pre-release. Lead with mood + context + release story, not credits or accolades. Editorial adds in the first 72h are the highest-value outcome of the pre-release phase.
- *Apple Music editorial:* pitched via distributor or direct. Territory-specific editorial teams have distinct format and genre preferences.
- *TikTok Sound Tagging:* submitting tracks for official sounds status; accelerates discovery when the sound trends.

**Paid — controllable, diminishing returns above 40% of budget:**
- *Meta (Instagram/Facebook) conversion ads:* best ROI for warm audience retargeting. Cold prospecting CPC for music is high.
- *Spotify Marquee / Showcase:* fan-retention and catalog-surfacing tool, not a fan-acquisition channel.
- *TikTok Spark Ads:* highest ROI paid channel for music when organic content is working. Zero ROI when boosting content that is not organically engaging.

## Global Release Architecture

**Territory priority framework:**

| Territory Tier | Definition | Strategic role |
|---------------|-----------|----------------|
| **Home territory** | Artist's primary cultural market | Streaming velocity anchor; editorial pitch home base |
| **Anglosphere expansion** | US, UK, Australia/NZ (for Canadian artists) | Higher-reach editorial networks; highest-value sync/brand market |
| **Europe (UK-anchored)** | UK → Germany → France → Netherlands → Scandinavia | BBC Radio 6 Music is most active independent champion |
| **Asia-Pacific** | Korea, Japan, Australia | Distinct DSP editorial teams; requires localized pitching |
| **LatAm** | Mexico, Brazil, Argentina | YouTube-primary; Spotify LatAm editorial separate from US |

**Territory sequencing rules:**
1. Anchor home territory first. Release-week velocity signals must be established before international editorial pitches carry credibility.
2. Anglosphere expansion concurrent with home if PR infrastructure exists.
3. Asia-Pacific and LatAm: algorithmic-first, editorial-second. Invest in correct metadata (genre tagging, mood/energy signals) rather than expensive international PR.

**Anti-pattern:** running a US campaign before a documented home-territory streaming record. US editorial teams at Spotify, Apple Music, and Tidal require evidence of audience resonance in a home territory before investing editorial space on an unknown international artist.
