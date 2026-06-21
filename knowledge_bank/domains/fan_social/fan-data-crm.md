# Fan Data, CRM, and Segmentation

PLMKR knowledge bank — Fan and social domain.

Turning scattered platform touchpoints into a unified understanding of who a fan is and how
deeply they are engaged — the intelligence layer beneath every other fan decision.

---

## General Frameworks

### Named frameworks

**1. Fan identity resolution.** Recognizing that a social follower, an email subscriber, a ticket
buyer, and a community member may be the same person — and building that unified profile. Without
resolution, a fan who has interacted across six touchpoints appears in each platform's analytics
as a separate first-time contact. Resolution methods, in order of reliability:
- **Email match** — automatic in CRM systems with multi-source ingestion when the same email is
  used everywhere.
- **Phone-number match** — SMS subscribers cross-referenced with ticket-buyer databases.
- **Social login** — fans who sign in with a social account to a D2C store link social identity
  to purchase identity.
- **Probabilistic matching** — same name, device fingerprint, IP window; less reliable, requires
  a consent framework.

Practical reality for independent/mid-sized artists: full resolution requires CRM investment.
Start with an email list as the primary identity anchor and cross-reference every other touchpoint
against it. A ticket buyer who gives their email is worth more than thousands of anonymous social
followers.

**2. Behavioral fan segmentation.** Segment by behavior, not demographics:

| Cohort | Definition | Action |
|--------|-----------|--------|
| Lurkers | Consume, never interact | Conversion content (interactive, comment-triggering) |
| Engagers | Like/comment/share but don't purchase | Lower-barrier purchase opportunity |
| Purchasers | Made at least one transaction | Membership offer; exclusive content upgrade |
| Community members | Active in an owned channel | Superfan cultivation; ambassador consideration |
| Advocates | Refer others; create UGC; organize | Recognition and empowerment |

The most common error is treating all followers as a homogeneous audience. Advocates who receive
a first-time-listener welcome email churn; lurkers who receive a superfan-tier pitch buy nothing.

**3. Fan RFM model (adapted).** Standard RFM (Recency, Frequency, Monetary) extended for fans:

| Dimension | Fan adaptation |
|-----------|----------------|
| Recency | Last meaningful interaction (purchase, community post, message response, show attendance) |
| Frequency | Interaction frequency across all touchpoints |
| Monetary | Total direct fan spend + estimated lifetime value (including live) |
| Depth (added) | Number of distinct touchpoints — multi-platform depth indicates higher fusion likelihood |
| Advocacy (added) | Has the fan created UGC, referred others, or organized fan activity |

RFM + Depth + Advocacy = a five-dimension fan-health score. Fans high on all five are the top
slice of the superfan cohort. Fans high on Recency and Frequency but low on Monetary and Depth
are engaged non-purchasers — a conversion opportunity via a low-friction first purchase.

**4. First-party data priority.** Cookie deprecation, app-tracking changes, and privacy regulation
have made first-party data (what fans willingly give) the primary competitive advantage. Capture
priority order: (1) **email** — most portable, lowest friction; (2) **phone/SMS** — highest
engagement, higher acquisition friction; (3) **purchase data** — highest signal of commitment;
(4) **platform follow** — least powerful, fully rented, no direct-contact capability.

**5. Analytics hierarchy.** Not all platform analytics are equally useful for fan understanding:
DSP-for-artists data (save rate, playlist source, city distribution) is high-value for superfan
identification and discovery-source tracking; email-platform analytics (open/click/segment
behavior) is high-value for engagement health and churn signals; community-server analytics
(message rate, retention, role distribution) is high-value for community health; short-video and
social-feed insights are medium-value for discovery reach and content-format performance;
ticket-buyer data is the highest-value for highest-intent fan identification and direct contact.

### Decision branching logic

**When to invest in CRM infrastructure:**
```
More than ~10,000 engaged fans on any single platform?
→ No  → A basic owned list is sufficient; focus on building it
→ Yes → Is fan data unified across touchpoints?
   → No  → CRM investment required before the next major campaign or tour
   → Yes → Is campaign personalization in use?
      → No  → Segmentation and automation investment required
      → Yes → Advanced: identity resolution + LTV scoring
```

**What to collect at each stage:** early (email, city, discovery source); developing (+ SMS,
social follow, first-purchase data, show attendance); established (+ membership tier, lifetime
purchase history, community-engagement score, territory clustering).

**Pre-save as data capture:** pre-save campaigns ask fans to pre-save an upcoming release in
exchange for first access or exclusive content. Many require email/social-login consent, creating
a data-capture event at the moment of highest artist excitement (a new-music announcement).

### Domain anti-patterns

1. **Collecting fan data without a communication plan.** Lists that are never used are dormant
   obligations, not assets. Pair every collection effort with a defined cadence.
2. **Platform analytics as fan intelligence.** Platform analytics measure platform-specific
   behavior, not fan depth. An artist who reads DSP demographics but has never captured an email
   has analytics, not fan intelligence.
3. **Playlist-listener data as "our fans."** Streams from algorithmic and editorial playlists are
   discovery exposure, not fan relationship. These listeners are not identifiable, contactable, or
   reliably recurring. Do not treat playlist stream counts as fan counts.
4. **Geography as a proxy for fan depth.** Knowing fans cluster in a city tells you where to tour,
   not who to prioritize for community investment. Behavioral data is the right segmentation axis
   for depth.

### Practitioner insight

**The pre-save data-collection moment is the highest-leverage touchpoint most independent artists
are not using.** It sits exactly when fan intent is highest (they just learned about new music and
want to hear it). A well-executed pre-save with email capture converts a meaningful share of link
clicks into a first-party list of music-intent fans who have raised their hand. The marginal cost
of adding email capture is near-zero; the fan-intelligence value is significant.

---

## Music Modules

### DSP-for-artists fan-intelligence mining

**Save rate as a superfan signal.** Save rate (saves ÷ streams) is the most valuable
streaming metric for fan depth — it measures the share of listeners who chose to add a song to
their library, signaling genuine engagement beyond passive discovery. The strongest signal is
listeners who both save and repeatedly stream in the same session. (Verify save-rate benchmarks
against current platform data before citing.)

**Listener-source breakdown:** editorial playlist → discovery signal (not relationship);
algorithmic playlist → moderate relationship signal (the algorithm has found audience fit); direct
artist-page navigation → highest relationship signal (existing fan behavior); listener's own
playlist → strong engagement signal (the fan chose to curate).

**City data:** city distribution identifies where the organic fanbase concentrates before
tour-routing decisions — the most actionable direct fan-to-live signal in streaming analytics.

### Email-list building for music

**Capture touchpoints, ranked by conversion quality:** show-venue signup (highest intent, often
done poorly); pre-save with email gate; website/bio link with incentive; social bio link with a
persistent offer; merch-checkout capture (highest-intent purchaser).

**Incentive tiers:** exclusive track or demo (works for music-first fans, zero artist cost);
presale ticket access (strongest incentive for touring artists); discount code (works for
merch-heavy artists); community access (works for community-oriented artists).

**List management:** a short welcome sequence within the first week (introduce the artist, share
the best content, state what being on the list means); segment by engagement level before major
sends; run a re-engagement campaign before pruning cold subscribers to protect deliverability.

### Tooling categories

Match the tool to the stage and the operation: starter email CRMs for early lists;
creator-oriented email platforms with automation for content-driven artists; D2C-integrated email
platforms for artists with a merch store; two-way SMS platforms for mid-major and major artists;
show-discovery + notification tools for touring artists; smart-link/pre-save platforms for data
capture; fan-data platforms for unified profiles.

> Where the artist's current data infrastructure is known, read the recommendations above as
> target-state architecture and reconcile against existing tools to avoid duplication; assume no
> existing infrastructure only until that current-state context is supplied.
