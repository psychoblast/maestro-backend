# Community Architecture: Owned vs. Rented

PLMKR knowledge bank — Fan and social domain.

How to structure fan community across platforms — what the artist controls, what they rent,
and how to migrate fans from one to the other.

---

## General Frameworks

### Named frameworks

**1. Owned vs. rented community media.** An extension of the paid/owned/earned taxonomy applied
to community infrastructure:
- **Owned:** channels the artist controls — email lists, SMS lists, website, community servers,
  artist-run forums. The artist reaches the fan directly, without intermediary, at near-zero
  marginal distribution cost once the relationship exists.
- **Rented:** social platforms where fans live but the artist does not control — short-video
  apps, social feeds, video platforms, streaming DSPs. Algorithms determine reach. Platform
  policy can revoke access, de-prioritize content, or disappear entirely. Fan relationships
  built entirely on rented platforms are equity held in a third party's hands.

The strategic imperative: use rented platforms for discovery and acquisition; migrate fans to
owned channels as the relationship deepens. This migration is the core mechanic of sustainable
community building.

**Migration economics:** a follower on a rented platform has near-zero direct-contact value —
the artist cannot reach them without the algorithm's permission. Email subscribers open at a
modest but meaningful rate; SMS opens are very high and usually read within minutes; an opted-in
community member is reachable daily at near-zero marginal cost. Cost-per-owned-contact is
highest at acquisition; value-per-contact compounds over the channel's lifetime. (Verify
specific open-rate figures against current platform data before citing.)

**2. Hub-and-spoke model.** One owned hub (email list, community server, or proprietary
platform) connected to multiple rented-platform spokes that continuously feed fans into the hub.
Each spoke serves discovery; the hub is where the relationship deepens. Hub selection:
- **Email list:** best for broad communication, merch/ticket conversion, and announcements.
  Lowest infrastructure cost; most universal. Not community (one-to-many) but an excellent
  conversion layer.
- **Community server:** best for community-oriented audiences (gaming, niche genre, highly
  engaged existing fanbase). Role architecture creates superfan layers; low barrier for
  internet-native audiences.
- **SMS:** best for maximum open rate and a direct, personal feel; supports two-way messaging at
  scale. Higher cost per subscriber than email.
- **Proprietary / regional superfan platform:** best for established artists with large superfan
  bases willing to install dedicated software. Highest friction for casual fans; highest depth
  for superfans.

```
Is the artist established (large monthly listenership) AND has a passionate core fanbase?
→ Yes → Consider proprietary/regional tier + community server + email
→ No  → Start with email + one social platform done well; community server only if
        community signals are already organically forming
```

**3. Community lifecycle model.**

| Stage | Characteristics | Management priority |
|-------|-----------------|---------------------|
| Inception | Core fans from early releases; self-organizing; high energy, low structure | Establish norms and leadership; don't over-structure; let culture form |
| Establishment | Norms solidifying; roles emerging; growth accelerating | Codify norms, establish a moderation team, create regular events |
| Maturity | Stable membership, predictable engagement, internal leadership layer | Prevent calcification; onboard new fans; stop old guard from gatekeeping |
| Mitosis or decline | Splits into sub-communities or loses energy | Split is healthy if managed; decline requires artist-direct re-engagement |

Most fan communities never leave Inception because the artist abandons them or moderation
challenges overwhelm them at the Establishment stage.

**4. Social capital.** Communities need both *bonding capital* (ties within the close-knit core
that drive depth and resilience) and *bridging capital* (connections across fan types that drive
growth and inclusion). All-bonding communities become exclusive cliques that repel new fans;
all-bridging communities lack the depth core that makes belonging meaningful. Design goal:
strong bonding capital in a visible core (superfans who create, organize, represent) with
accessible bridging infrastructure (welcome channels, intro prompts, casual content access).

**5. Community health indicators (non-vanity).**

| Indicator | Healthy range | Warning signal |
|-----------|---------------|----------------|
| Messages per member per month (server) | 15–40 for active servers | <5 (dead air); >80 (potential toxicity spike) |
| New-member activation rate | 30–60% post within 7 days | <15% (onboarding failure) |
| Mod-escalation rate | <2% of interactions | >5% (toxicity problem) |
| Superfan-identification ratio | 1–5% consistently active | <0.5% (engagement desert) |
| 30-day retention | 40–70% of new members still active | <25% (poor onboarding or irrelevant content) |

These are industry heuristics; replace them with the artist's observed values once available.

### Moderation framework

**Tier structure:** soft moderation (norms, sticky posts, welcome messages, role-model behavior)
handles ~80% of friction; formal moderation (documented warnings, temp mutes/bans) ~15%; hard
moderation (permanent bans, channel lockdowns, platform reports) ~4%; nuclear options
(community pause, server lock, artist direct address) for existential threats (<1%).

```
Is the crisis contained to one channel/thread?
→ Yes → Soft/formal mod response; no artist involvement needed
→ No  → Is it affecting fan perception of the artist or community identity?
   → No  → Formal mod escalation; increase mod presence
   → Yes → Artist-direct acknowledgment of community impact (NOT PR language)
           + formal moderation of the specific offending content/actors
```

**Staffing:** community managers are not moderators. Community managers build engagement and
culture; moderators enforce norms. Confusing the roles produces both under-moderation
(managers reluctant to ban) and over-moderation (moderators killing organic culture).

### Domain anti-patterns

1. **Single-platform community.** Building entirely on any one rented platform creates a single
   point of failure. Correct architecture always includes an owned channel (email minimum)
   running in parallel.
2. **Premature monetization.** Introducing paid tiers before community trust is established
   converts fans' perception from "belonging" to "product." Community health first,
   monetization second.
3. **Under-moderation in the growth phase.** Establishment-stage communities are fragile;
   unaddressed toxicity becomes normalized. Fixing a toxic culture later costs far more than
   establishing norms early.
4. **Platform migration without a migration plan.** Every transition loses a portion of the
   community. Never close a community channel without a migration offer; treat the migration
   itself as a community event, not a logistical move. The fans who follow are the most committed.
5. **Community managed entirely by team with zero artist presence.** Communities can tell.
   Without periodic genuine artist presence, they calcify into echo chambers or collapse — they
   are missing the parasocial centerpiece.

### Practitioner insight

**The 10/1/0.1 rule.** In any fan community, roughly 10% of members create most of the positive
culture, 1% are true leaders (moderators, organizers, top contributors), and 0.1% are chronic
disruptors. Almost all management energy goes to the 0.1% while the 10% who create value are
neglected. The leverage is the opposite direction: empower and recognize the 10% who create
culture; remove the 0.1% quickly. The community builds itself when positive culture has
structure and recognition.

---

## Music Modules

### Community-server architecture for artists

A community-first channel structure maps onto the engagement spectrum:

```
WELCOME / INFO    → arrival message + rules; self-assign roles; artist-controlled announcements
COMMUNITY         → general chat; fan-creations showcase; coordinated listen-parties; fan playlists
EXCLUSIVE (tier)  → early access to new music; behind-the-scenes; periodic artist Q&A; inner circle
MODERATION        → private reporting channel; staff-only comms
```

Role architecture should map to the engagement spectrum (Listener → Fan → Superfan → Founding
Member → Moderator → Team), each role carrying different channel access. Server subscription
programs let artists add a paid tier inside the same server — best for artists with an existing
community who want to avoid forcing fans onto a new platform. (Verify current creator-keep rates
and price ranges before citing.)

### SMS and email architecture

- **SMS:** one-to-many broadcast with two-way capability; very high open rate, usually within
  minutes. Best for release drops, exclusive announcements, presale codes, and artist-direct
  messages. Per-subscriber cost model.
- **Email:** the core owned asset — fully owned, portable, permanent. Capture at every campaign,
  pre-save, and owned touchpoint. Frequency should be release-cycle-driven, not weekly (fan
  fatigue is real); segment by engagement level before major sends.

### Platform-migration pattern (historical)

Fan communities form on the dominant platform of their era → the platform declines or changes
rules → the community partially migrates → the migration cohort is the most committed fans. The
durable lesson: communities that survive migrations are the ones with an owned-channel backbone
(email, SMS) that does not migrate — fans receive the migration offer directly, regardless of any
platform's algorithm.

### Membership-hub model (organized-fandom reference)

The most developed official fan-club systems link community membership directly to concert-ticket
access — the most powerful community incentive in music. Tiered membership (free lurker →
grade-based → paid official club) bundles pre-sale priority, exclusive content, and physical
welcome packs. The transportable element for any artist: a fan club that grants genuine early
ticket access generates genuine enrollment demand. The structural difference from most Western
practice: these systems build community as a product feature, not a marketing byproduct.

### Listening-party architecture

| Format | Best for |
|--------|----------|
| Community-server listening party (coordinated time + discussion + artist presence) | Established server communities; coordinate 48h+ ahead for time-zone-distributed fans |
| Video-platform premiere (scheduled release with live chat) | Visual content (video, short film, visualizer); creates a watercooler moment |
| Synchronized small-group listening | Intimate creator/superfan activations only — not a mass event tool |
| Live-stream countdown + reveal | Artists with a strong live following; highest discovery potential among casual fans |

Rule: the listening-party platform should match where the community is most active, not where the
artist wants to grow.
