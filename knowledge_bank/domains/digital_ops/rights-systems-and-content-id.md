# Rights Systems & Content Recognition

This file covers the user-generated-content (UGC) rights layer: the YouTube
content-recognition system, the TikTok rights layer, and the Meta rights manager.
These are distinct from delivery to streaming platforms and from composition-rights
registration (which routes to Publishing).

## 1. Content-Recognition System Architecture (YouTube Layer)

The content-recognition system is an audio/video fingerprinting and rights-
management platform. It lets rights-holders automatically identify, manage, and
monetize user-generated content containing their owned audio or video.

How it works:
1. **Reference file upload** — the rights-holder (or authorized distributor)
   uploads a reference audio/video file: the fingerprinted original.
2. **Fingerprint database** — the platform generates an acoustic fingerprint and
   stores it.
3. **Continuous matching** — every uploaded video is compared against the
   fingerprint database.
4. **Claim generation** — when a match is detected, a claim is generated on the
   matched video.
5. **Claim action** — the rights-holder has pre-configured the action: Monetize
   (run ads and collect revenue), Track (analytics only, no revenue action), or
   Block (prevent playback in specific territories or globally).

**Who can access the system directly:**
- **Rights-management partners:** large labels, distributors, and networks that meet
  the platform's volume/eligibility requirements and hold a direct agreement. They
  upload reference files directly and receive rights-management reports.
- **Through a distributor:** most independent labels and artists access the system
  through their distributor (who holds the partner agreement) or through a publishing
  administrator with access.
- **Via a network or sub-publisher** with a partner agreement.

**Claim types and operational implications:**

| Claim type | Action on matched video | Revenue routing | When appropriate |
|-----------|------------------------|----------------|-----------------|
| Monetize | Ads run; ad revenue collected | To the claimant (rights-holder) | Standard use for commercially released music |
| Track | Analytics only | None | Research; not revenue-maximizing |
| Block | Video prevented from playing | None | Unauthorized use of exclusive content; rights conflict |

Anti-pattern: defaulting to Block for all claims on original content. Block removes
the video, which can hurt promotional interest when the video is fan content with
promotional value. Monetize captures revenue while leaving the video live. The
correct default for most commercially released music is Monetize; Block should be
selective.

## 2. Claim Evaluation Protocol

When a claim appears on owned content:

**Step 1 — Identify the claimant type:**
- **Own account claim** — the rights-holder's own distributor or partner account;
  likely correct. Verify the reference file maps to the correct recording and the
  action is set correctly.
- **Third-party label/publisher** — a recognizable rights-holder who may have a
  legitimate partial or full claim (e.g., a sample in the recording; a composition
  right in a cover).
- **Unrecognizable claimant** — an entity with no obvious connection; potential
  fraudulent claiming.

**Step 2 — Evaluate legitimacy:**
- Does the claimant control the master recording? (Then they can claim master rights.)
- Does the claimant control the composition? (Composition rights allow claims on
  performances of the composition.)
- Is the claim on the full video or a segment? (A segment claim identifies a portion
  matching their reference file.)
- Is the claim correct even if the claimant is unfamiliar? (A legitimate sub-
  publisher or licensing agent may appear under a different name from the ultimate
  rights-holder.)

**Step 3 — Common legitimate scenarios:** sampled content (the sampled recording's
holder claims); a cover song (the composition publisher claims — not the master, as
the recording is new); licensed content; distributor sub-licensing in the claim
portfolio.

**Step 4 — Common erroneous scenarios:** a composition publisher sets Block rather
than Monetize, harming the artist without a blocking basis; a false-positive match
on a superficially similar reference file; a claim that fired because of an ISRC
conflict (see below).

**The ISRC conflict → wrongful claim chain:** an ISRC shared by two different
recordings can cause claims from the other recording's rights-holder to fire against
the correctly-delivered recording. Fixing the ISRC conflict upstream eliminates these
downstream claim problems.

**Practitioner insight:** claim volume is an unreliable indicator of claim accuracy.
A large catalog with an aggressive configuration can generate thousands of erroneous
claims per month. Claim volume reflects fingerprint-database breadth, not rights-
position accuracy. Every claim still requires individual rights evaluation — there is
no shortcut.

## 3. Claim Dispute Decision Tree

```
Claim received on owned content
→ Step 1: Identify claimant rights basis
    → Verified rights basis (master or composition) → accept; verify revenue routing
    → Basis unclear → Step 2
    → No identifiable basis → dispute immediately

Step 2: Evaluate specifics
    → Claim for the full recording? → likely erroneous if no obvious rights
    → Claim for a segment? → identify the segment
        → Segment is original content → dispute
        → Segment may contain a sample/licensed element → verify clearance first

Step 3: Dispute decision
    → Confirmed erroneous → file dispute; provide ownership documentation
    → Partial rights basis → negotiate via the rights partner; consider a custom deal
    → Unclear basis → file dispute; request the claimant's rights documentation

Step 4: Post-dispute
    → Claimant releases → monitor for re-claim (recurs if the reference file remains)
    → Claimant upholds → escalate via the distributor/partner process
    → Pattern of bad-faith re-claiming → escalate to Legal
```

**Time sensitivity:** dispute windows are time-limited and vary by context. Do not
delay evaluation — an unresolved accepted claim may divert revenue that is difficult
to recover retroactively.

## 4. TikTok Rights Layer

- Most label music reaches the platform through the same distributors used for
  streaming delivery.
- A separate commercial-music-library tier exists for creators using music in
  sponsored/commercial content, and an enterprise advertising-licensing tier.
- A direct-to-artist distribution option exists in select markets — verify current
  availability and status.
- When a distributor delivers music, it is registered in the platform's rights
  system; user-created videos using registered tracks are monetized via a revenue-
  sharing program whose terms vary by distributor agreement.
- Unlike the YouTube layer, this rights management is generally not directly
  accessible to most rights-holders — it operates through distributor agreements,
  with disputes routed through the distributor and less granular reporting.

Anti-pattern: assuming revenue from user-created videos is automatically collected
and reported at the same granularity as the YouTube layer. Reporting granularity,
payout rates, and claim mechanics differ materially. Verify the distributor's
specific reporting and payout structure.

## 5. Meta Rights Manager

- A rights-management system covering both of Meta's primary social platforms,
  letting rights-holders identify, manage, and monetize (or remove) content using
  their assets.
- **Access:** available through a partnership-application process — not automatic for
  all rights-holders or all distributors. Eligibility depends on content volume,
  catalog size, and legal-entity status. Verify current criteria.
- **Claim types:** similar to the YouTube layer (block or monetize), but
  monetization on UGC is more limited and region-dependent.
- **Reporting:** less granular than the YouTube layer.
- **Distributor access:** most major distributors offer registration as part of
  their services; the rights-holder may need to explicitly opt in — it is not
  automatic in all agreements.

**Practical significance:** these platforms carry a large volume of UGC using music.
An artist or label not registered is not collecting this income. It is often the most
overlooked of the three major UGC rights systems — operators sophisticated about the
YouTube layer frequently have no registration here because the process is less
accessible and the reporting less transparent.

## 6. Common Abuse Patterns and Responses

| Pattern | Description | Response |
|---------|-------------|----------|
| **False third-party claim** | An entity with no rights claims original content via a superficial match | Dispute; provide ownership docs; escalate if upheld; Legal if the pattern persists |
| **Over-broad composition claim** | A publisher claims full master revenue on a cover, when entitled to composition royalties only | Dispute the master claim; confirm composition royalties flow through the correct channel |
| **ISRC-conflict-triggered claim** | A wrong claim fires because the ISRC was shared with another recording's reference file | Dispute; fix the ISRC conflict upstream; redeliver with the correct ISRC |
| **Fraudulent claiming** | An unknown entity claims content with no basis, attempting to monetize popular content | Dispute immediately; report to the rights partner; Legal if upheld |
| **Distribution conflict** | Two distributors both delivered the same recording; two reference files exist | Remove the duplicate delivery; dispute with the distributor not controlling current rights |

## Domain Anti-Patterns

- Defaulting to Block for all claims on original commercially released content.
- Treating delivery to a platform as activation of its rights system.
- Assuming UGC revenue is collected and reported uniformly across platforms.
- Leaving one or more UGC rights systems unregistered for an active catalog.
- Fixing a wrongful claim without fixing the underlying ISRC conflict that caused it.
