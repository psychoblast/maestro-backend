# DSP Product Configuration & Store Mechanics

## Currency Warning

Platform product types, pre-order/pre-save mechanics, correction workflows, and
editorial submission processes change on platform timelines. All specifics below
are reference points — verify against current distributor and platform documentation
before delivery.

## 1. Product Type Classification

A "product type" determines how a release is categorized on DSPs — as a single, EP,
or album. The classification affects editorial eligibility, charting rules, chart-
category placement, and in some cases royalty-rate calculations.

**Standard classification rules (widely used convention — verify per distributor/platform):**

| Type | Track count | Total duration | Notes |
|------|-------------|----------------|-------|
| Single | 1–3 tracks | Any | A single with 2–3 tracks is called a double or triple single |
| EP | 4–6 tracks | Typically <30 min | Some distributors enforce: if ≥7 tracks or ≥30 min → album |
| Album | 7+ tracks | Any | Some platforms: ≥6 tracks if total duration ≥30 min |

**Important caveat:** these rules are not a single, universal industry standard.
They are practical conventions, and different distributors enforce slightly different
thresholds. Some platforms apply their own classification independently of what the
label submits. The correct action: check the specific distributor's product-type
definition and the specific platform's classification rules for the territory and
charting system in question.

**Operational consequence of wrong product type:**
- Delivering an EP as an album or vice versa can affect chart eligibility (some chart
  methodologies count albums and EPs separately or apply different track-count
  weighting).
- Editorial pitch eligibility may differ for singles vs. albums at some platforms.
- Revenue-per-stream rates are not affected by product type — this is a DSP reporting
  and chart-eligibility issue, not a financial one.

## 2. Release Version Types and When New UPCs Are Required

Each release variant is a separate commercial product that requires a new UPC:

| Variant | New UPC required? | New ISRC required? | Notes |
|---------|-------------------|-------------------|-------|
| Deluxe edition (adds tracks to the original) | Yes | Yes for new tracks only | Existing tracks keep their ISRCs |
| Expanded edition (adds previously unreleased tracks) | Yes | Yes for new tracks only | Same as deluxe |
| Anniversary reissue (same track list, new artwork) | Yes | No (same recordings) | New product, same recordings |
| International edition (track list differs by territory) | Yes (per variant) | Same ISRCs where same recordings | Territory-specific product configurations |
| Clean/explicit pair | Typically yes (separate products) | No (same or per-distributor convention) | Some distributors link; others treat as separate |
| Remaster (significant sonic changes) | Yes | New ISRC per the doctrine | New recording; new product |
| Digital-only edition of a physical release | Yes | Same ISRCs | Physical and digital are separate products |
| Karaoke/instrumental version | Yes | New ISRC (different recording) | A new performance without vocals is a different recording |

**Common error:** releasing a deluxe edition under the original UPC. The original
release and the deluxe edition are separate commercial products. Reusing the UPC
causes the original product to be overwritten or creates a conflicted state at the
platform — the original's chart history and editorial associations are disrupted.

## 3. Pre-Order Mechanics

A pre-order allows listeners to purchase (in the download/purchase market) or follow
a release before its availability date. A pre-order on a purchase platform works as
follows:

- The release is delivered with a future release date. The distributor submits the
  pre-order configuration to purchase platforms.
- Platforms make the release available for purchase/follow at a date before the
  release date (the pre-order start date).
- Listeners who purchase during the pre-order period receive the purchased tracks
  when the release date arrives.
- **Instant gratification tracks:** the distributor can designate one or more tracks
  as instantly available on pre-order purchase — the listener receives the designated
  track immediately on purchase. These tracks must be delivered in advance of the
  pre-order start date with the instant-gratification flag set in the metadata.

**Operational requirements for pre-orders:**
- The distributor needs the release and instant-gratification tracks delivered with
  enough lead time to process the pre-order submission before the pre-order start
  date (typically 1–2+ weeks before the pre-order start — verify current distributor
  lead times).
- Changes to pre-order pricing or instant-gratification track designation after
  submission may not be possible on all platforms without a full redelivery.

**Pre-order vs. streaming:**
Pre-orders are a download-market mechanism. Most streaming platforms do not have
pre-order purchase mechanics — they have pre-save. The two are separate systems with
different audiences (streaming listeners vs. download purchasers). Both require
separate setup and typically different lead-time management.

## 4. Pre-Save Mechanics

A pre-save allows a listener to add a future release to their streaming library
before the release date. When the release goes live, it appears in the listener's
library automatically on release day.

**How pre-save works operationally:**

```
Step 1 — Delivery and processing:
→ The release is delivered to the distributor with a future release date.
→ The distributor processes and delivers to the streaming platform.
→ The platform generates a pre-release landing page or makes the album
  available for pre-saving once it is in their system.

Step 2 — Pre-save link activation:
→ The release must be in the platform's system (processed) before a
  pre-save link is valid. An unprocessed release has no pre-save URL.
→ Typical time from delivery submission to pre-save availability:
  3–7 business days (varies by distributor and platform load).
→ The artist or label generates/distributes the pre-save link after confirming
  the release is in the platform system.

Step 3 — Release day:
→ All listeners who pre-saved the release have it added to their library
  automatically on the release date.
→ Library adds from pre-saves are counted in the platform's analytics as
  library saves from release day.
```

**Analytics significance of pre-saves:**
A large pre-save count converts directly to a spike of "saves from release day" in
the analytics. This matters for algorithmic surfaces that use saves from new
listeners as a candidacy signal. Pre-saves on Apple Music specifically convert to
library adds, which trigger Shazam-adjacent signals and can influence the New Music
Friday editorial shortlist consideration (library add velocity is observable to
editorial teams).

**Common pre-save error:**
Distributing a pre-save link before confirming the release is in the platform's
system creates broken links and fan frustration. Verify the pre-save URL works in
an incognito window before distributing.

## 5. Canonical Artist Pages and Name Management

**What a canonical artist page is:**
Each major DSP maintains a database of artists with a canonical identifier — an
internal ID (e.g., an Apple Music Artist ID, a Spotify Artist URI). All releases
attributed to a given artist should resolve to the same canonical page. When they
do not, the artist has fragmented pages.

**Causes of fragmented pages:**
- Name spelling variations across releases ("Firstname Lastname" vs "First Name Last
  Name" vs "Firstname LastName").
- Different capitalization conventions across distributors.
- A release delivered under an alias or collective name without a primary-artist
  credit link.
- A distributor-side error mapping a new release to the wrong artist ID.

**Consequences of fragmented pages:**
- Streaming counts split across multiple pages — algorithmic systems see each page
  as a smaller catalog.
- Follower counts split — social-proof signal fragmented.
- Editorial teams at the platform see a smaller artist; it can affect their
  willingness to pitch the artist for playlist placement.
- Platform verification (blue/check marks) applies to the verified page only —
  the fragmented pages do not inherit verification.

**Remediation:**
- At Spotify: through the Spotify for Artists portal, an artist can claim their
  profile and request a merge if they identify a fragmented page.
- At Apple Music: through Apple Music for Artists; also via distributor and platform
  support for merges.
- At other platforms: through the distributor or platform's artist-support process.
- Timeline: page merges can take weeks and are not guaranteed. The most effective
  prevention is a strict naming standard enforced before every delivery.

**Naming standard discipline:**
The artist name as it appears in delivery metadata is the most important determinant
of page attribution. The name must be exactly consistent — character-by-character,
including capitalization, spacing, and punctuation — across every release from
the same artist. Maintain a canonical artist-name register as part of the
catalog's metadata standard (see Catalog Metadata Governance).

## 6. Platform Verification and Artist Dashboard Access

**Platform verification:**
Each major streaming platform offers a verified artist status (Spotify for Artists,
Apple Music for Artists, Amazon Music for Artists, etc.). Verification provides:
- Access to analytics (full per-track, per-territory streaming data).
- Profile management (bio, header image, artist pick, recommended playlists).
- Direct contact for editorial pitch submission (on some platforms).
- Claim-and-protect from unauthorized profile edits.

**Verification is not automatic** — it requires an application through the platform's
artist portal, typically requiring proof of identity (artist's distributor-linked
profile, social media confirmation). For labels managing multiple artists, each
artist requires a separate verification.

**Artist pick mechanics:**
Verified artists on some platforms can designate a specific track or playlist as
their "artist pick" — featured at the top of the artist page. This is a promotional
tool with no algorithmic amplification — it affects what is visible on the page, not
what the platform's algorithm recommends. It is most effective when timed to an
active promotional campaign on a priority release.

## 7. Correction Mechanics — What Requires Redelivery vs. Portal Update

One of the most operationally impactful decisions in digital ops is knowing what
can be corrected in the distributor portal (no new delivery, platform propagates
within days) vs. what requires a full redelivery (new file package, takes days to
weeks to propagate across all platforms).

**Changes that typically do NOT require redelivery (portal/metadata update only):**

| Change | Mechanism | Timeline |
|--------|-----------|----------|
| Artwork update (same release) | Metadata-only update or portal edit | 3–7 business days typical |
| Marketing description / bio text | Platform portal direct | 24–72h |
| Pre-order pricing adjustment | Portal edit | Depends on platform |
| Territory availability expansion (adding territories) | Metadata-only update | 3–7 business days |
| Credit additions (producer, songwriter) | Metadata update at some distributors | Varies |
| Track price tier (purchase market) | Portal edit | 24–72h |

**Changes that typically DO require redelivery (new audio or corrected package):**

| Change | Why redelivery is needed | Notes |
|--------|--------------------------|-------|
| ISRC correction | Core identifier change; platform links to the ISRC | Full redelivery; some platforms support correction tickets |
| Primary artist name change | Core search/matching field | Redelivery at most platforms |
| Track title change (major) | Core metadata field | Minor capitalization: distributor-dependent; material title change: redelivery |
| Audio file replacement | New content | Typically requires a new delivery package |
| Release date correction | Core release record | Requires distributor ticket or redelivery |
| Territory availability reduction (removing territories) | Takedown instruction + redelivery | The original version is withdrawn; a new version is sent |
| Product type reclassification (EP → album) | Structural change | Distributor/platform-dependent; often requires redelivery |

**Anti-pattern — the "just update the portal" assumption:**
Practitioners new to digital ops sometimes assume that any error can be corrected by
editing the distributor portal. Some corrections do propagate via a metadata-only
update; others require a full redelivery to take effect at the platform level. The
distributor's documentation specifies which is which — treat it as the authoritative
source. When in doubt, ask the distributor support team before making a correction
attempt.

**Redelivery implications for live content:**
Redelivering a live release replaces the existing release in the distribution system.
Depending on the platform:
- Streaming counts may remain intact (the ISRC record continues).
- Or the release may experience a brief offline period during platform re-ingestion.
- Always confirm with the distributor whether a redelivery will cause any offline
  window before proceeding on commercially active catalog.

## 8. Editorial Pitch Submission Mechanics

Most major streaming platforms accept direct editorial pitch submissions from artists
and labels for potential playlist placement on programmed editorial playlists. Key
mechanics:

**Submission access:**
- Spotify: through Spotify for Artists — the artist submits a track; must be
  delivered and in the platform's system; the platform recommends submission at
  least 7 days before release (practitioner best practice: 3–4 weeks).
- Apple Music: no direct self-serve submission tool in most cases; submissions are
  routed through distributor relationships or directly through the platform's label-
  liaison / A&R contacts. Some distributors have formal Apple Music pitch pipelines.
- Amazon Music: through Amazon Music for Artists or label/distributor relationship.

**What happens after pitch submission:**
- Editorial teams do not confirm receipt or acceptance. A track being pitched does
  not guarantee review.
- Pitch outcome is typically communicated via the appearance of the track on a
  playlist; there is no rejection notification.
- Editorial placement on a playlist is decided independently of the pitch — the pitch
  informs the editorial team of the release, but placement depends on the editorial
  team's assessment of fit, timing, and listener data signals.

**The pitch window is a hard constraint:**
On platforms with a submission window (like Spotify for Artists), submitting after
the window closes (typically after the release date, or within a day or two of it)
means the submission is ignored for editorial consideration on that cycle. The pitch
must happen before the window closes, which requires the release to already be
delivered and processed. This makes the editorial pitch window one of the most
operationally constrained timelines in digital ops — and the most frequently missed.

**Pitch quality factors (within the digital-ops domain):**
- Only released or imminent tracks can be pitched — unreleased tracks with no
  delivery confirmation cannot be submitted.
- Genre, mood, and language metadata on the delivered track affect how the
  editorial team categorizes and routes the submission.
- A track with missing or incorrect genre metadata is harder to route to the right
  editorial team.

## Domain Anti-Patterns

- Releasing a deluxe edition under the original release's UPC, overwriting the
  original product's chart history.
- Distributing a pre-save link before confirming the release is in the platform's
  system.
- Allowing artist name spelling variations across releases, causing fragmented
  artist pages.
- Assuming that any metadata correction can be applied via a portal edit without
  checking whether the specific change type requires redelivery.
- Missing the editorial pitch window by confusing delivery lead time with the pitch
  submission deadline.
- Treating platform verification as automatic — verification requires an application
  per artist per platform.
