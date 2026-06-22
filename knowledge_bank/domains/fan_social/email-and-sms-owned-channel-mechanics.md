# Email and SMS Owned-Channel Mechanics

PLMKR knowledge bank — Fan and social domain.

The operational mechanics of owned-channel communication — automation flows, deliverability
foundations, SMS compliance, list segmentation, and the specific sequences that drive fan
conversion in a music career.

> Currency note: platform feature sets, compliance regulations, and carrier requirements change
> regularly. Verify compliance specifics (TCPA, GDPR, CAN-SPAM), carrier requirements, and
> platform feature availability against current authoritative sources before advising on any
> specific implementation.

---

## General Frameworks

### Named frameworks

**1. Core automation sequence architecture.** Music fan communications should run four primary
automated sequences, each triggered by a distinct fan behavior event:

| Sequence | Trigger | Length | Primary objective |
|----------|---------|--------|-------------------|
| Welcome flow | List join | 4–6 emails over 10–14 days | Establish the relationship; deliver the promised incentive; drive first engagement |
| Pre-release flow | New release announced | 3–5 emails over 2–6 weeks | Build anticipation; capture pre-save; drive release-week action |
| Post-purchase flow | Any D2C transaction | 2–4 emails over 7–14 days | Thank; invite community; cross-sell at the moment of peak identity investment |
| Win-back flow | 90+ days of inactivity | 2–3 emails over 2 weeks | Re-establish contact; suppress if non-responsive |

**The 72-hour trigger rule.** All triggered sequences should fire within 72 hours of the
triggering event. A welcome email that arrives four days after sign-up reaches a fan whose
excitement has cooled to the baseline. Welcome emails sent within one hour of sign-up
consistently outperform delayed sends on open rate, click rate, and downstream conversion.
The higher the fan's emotional state at the triggering moment, the more critical the delivery
timing.

**2. Welcome sequence structure.** The welcome flow is the highest-leverage automation sequence
because it sets expectations and captures first engagement before the fan goes dormant:

| Email # | Timing | Content | Call-to-action |
|---------|--------|---------|----------------|
| 1 | Immediately at sign-up | Deliver the promised incentive; brief artist-voice introduction | Access the incentive; follow on primary platform |
| 2 | Day 2–3 | Best single piece of existing content (most-shared song, most-viewed video) | Stream / watch / share |
| 3 | Day 5–6 | Story-forward content: artist backstory, origin, the moment this became real | Follow on a second platform or join the community |
| 4 | Day 9–10 | Community and membership context: what the list means and what members get; early access offer | Join the community (if applicable); reply to this email with a genuine question |
| 5 | Day 13–14 | First ask: low-friction action (pre-save an upcoming track, add to playlist, share to a friend) | Specific, single, low-cost action |

**The reply-to-email signal test.** Sending email 4 with a genuine artist-voice question ("What
was the first song of mine you listened to twice?") and reading replies — even at small list
sizes — produces a powerful parasocial signal: the artist actually reads this. The critical
constraint: only use this approach if genuine reading is operationally possible at current list
size. Faking two-way engagement is worse than none — a fan who writes back and receives no
response at a small list size has had a worse experience than one who never expected a reply.

**3. Email deliverability mechanics.** Deliverability determines whether emails reach the inbox
at all — a technically correct campaign that lands in spam reaches no one. Primary mechanics:

| Factor | What it is | How to maintain it |
|--------|------------|-------------------|
| Sender reputation | ISP and mailbox-provider score for the sending domain | Never purchase lists; remove hard bounces same-day; maintain low complaint rates |
| Spam complaint rate | Percentage of recipients who report as spam | Keep below 0.1% per send; above 0.3% triggers inbox suppression at major providers |
| List hygiene | Removing invalid, unengaged, or unsubscribed addresses | Hard-bounce removal is immediate; soft-bounce monitoring over 3–5 sends; prune 180-day non-openers regularly |
| Domain authentication | SPF, DKIM, DMARC records on the sending domain | Configure all three; DMARC at p=none to start; advance to p=quarantine once authentication is stable |
| Warm-up for new domains | Gradual volume increase when a new sending domain is established | Begin with the most-engaged subscribers; increase volume over 4–8 weeks before sending to the full list |
| Engagement weighting | ISPs use engagement as a reputation signal | Send to engaged subscribers first; expand to less-engaged segments only when initial engagement rate is strong |

**Domain authentication explained.** SPF (Sender Policy Framework) specifies which mail servers
are authorized to send on behalf of the domain. DKIM (DomainKeys Identified Mail) adds a
cryptographic signature that confirms the message has not been altered in transit and originates
from the authorized sender. DMARC (Domain-based Message Authentication, Reporting and
Conformance) instructs receiving mail servers what to do when a message fails SPF or DKIM
verification. All three are deliverability prerequisites; missing any one will degrade inbox
placement at major providers over time.

**4. SMS compliance framework.** SMS marketing operates under strict regulatory and carrier
rules that vary by jurisdiction and must be verified before any campaign deployment:

| Jurisdiction | Primary regulation | Consent requirement | Opt-out mechanism |
|-------------|-------------------|---------------------|-------------------|
| United States | TCPA (Telephone Consumer Protection Act) | Express written consent required before sending marketing SMS | Immediate opt-out on reply of STOP, UNSUBSCRIBE, CANCEL, or QUIT; confirmation message required |
| United States (carriers) | A2P 10DLC system | Brand and campaign registration required via The Campaign Registry before messages deliver | Same as TCPA |
| European Union | GDPR + ePrivacy Directive | Explicit, specific, informed, unambiguous consent; pre-ticked boxes are not valid consent | Right to withdraw consent at any time with immediate effect |
| United Kingdom | UK GDPR + PECR | Same standard as EU but under UK-specific post-Brexit regulation | Same as EU |

**10DLC vs. short codes in the US.** 10DLC (10-digit long codes) are standard phone numbers
registered for application-to-person messaging through carrier registration with The Campaign
Registry. They are the standard infrastructure for most artist SMS programs: lower cost than
short codes, adequate throughput for most send volumes, but require brand registration and
individual campaign registration before messages will reliably deliver. Short codes (5–6 digit
numbers) have higher throughput, better consistent deliverability, and no per-campaign
registration — but carry meaningfully higher monthly costs. Short codes become cost-effective
at high send volumes (broadly 100,000+ messages per month); 10DLC is appropriate below that
threshold.

**Double opt-in as a best practice.** Single opt-in (a checkbox at list signup) meets minimum
legal requirements in most jurisdictions but produces lists with higher rates of invalid numbers,
bots, and mistyped entries. Double opt-in (checkbox plus a confirmation reply from the subscriber)
produces a cleaner list: higher engagement rates per subscriber, lower complaint rates, and
near-zero deliverability risk from invalid entries. Double opt-in reduces list growth rate by
approximately 15–30% but improves per-subscriber engagement substantially. In EU and UK markets
where explicit consent is required under GDPR, double opt-in is the recommended default because
it creates an auditable confirmation record.

**5. SMS message design constraints.** SMS operates under technical and behavioral constraints
that differ fundamentally from email:

- **Character limit per segment:** 160 characters for standard SMS using GSM-7 character encoding.
  Messages longer than 160 characters automatically split into multiple segments billed
  independently. Messages using non-standard characters — including emoji, curly quotation marks,
  and certain punctuation — switch to Unicode encoding, which reduces the per-segment character
  limit to 70 characters. An unnoticed emoji in a 150-character message can produce two-segment
  billing on the full send.
- **No subject line — opening characters are everything.** Email has a subject preview visible
  before the recipient opens. SMS shows the first few characters in the lock-screen notification.
  The message hook must land in the first 30 characters.
- **One call-to-action per SMS.** Multiple links or asks consistently reduce response rates.
  A single, explicit action ("Presale opens in 2 hours — link: [URL]. Reply STOP to opt out.")
  outperforms a multi-link message on every response metric.
- **Frequency cap.** For most artist audiences, 2–4 SMS messages per month is the practical
  ceiling before unsubscribe rate meaningfully increases. Release-cycle peaks can sustain 2 per
  week for 1–2 weeks; sustained high-frequency sending destroys the channel's effectiveness.
  Unlike email, where dormant subscribers are merely silent, high-frequency SMS drives active
  opt-outs that permanently remove subscribers from the list.

**6. List segmentation strategy.** Sending identical messages to the full list at all stages is
the most common owned-channel mistake. Behavioral segmentation is the operational baseline:

| Segment | Definition | Send strategy |
|---------|------------|--------------|
| Active (60-day openers) | Opened or clicked within the last 60 days | Full communication volume; test new content with this segment first |
| At-risk (61–180 day non-openers) | Not opened in 61–180 days | Reduced frequency; higher-urgency subject lines; validate the offer on Active first |
| Dormant (181+ day non-openers) | Not opened in 181+ days | Win-back sequence only; do not include in regular sends |
| Purchasers | Made at least one D2C transaction | Highest-LTV segment; first access to drops and pre-orders; VIP path |
| Superfan cohort | Three or more purchases or active community members | Early access to everything; personal tone; artist-direct voice; first to know |

**Segment-first deployment protocol.** Before any major send — release announcement, tour
on-sale, major campaign — send to the Active segment only in the first 2–4 hours. If the
initial open rate matches the Active segment's historical average, expand to the At-Risk
segment. This protects sender reputation and provides real performance data before the message
reaches the full list, allowing a subject-line adjustment if the initial performance is weak.

### Decision branching logic

**Channel selection for a major announcement:**
```
Is this time-sensitive (presale opens in hours, merch drop, on-sale window)?
→ Yes → SMS first; email simultaneously or slightly delayed by 30–60 minutes
→ No  → Email first; SMS only if the SMS list is healthy (ideally ≥5% of email volume)

How often has the artist sent in the past 30 days?
→ 0–2 sends → Email appropriate; list is not fatigued
→ 3–5 sends → Check open rate trend; if declining, hold the next non-critical send
→ 5+ sends  → Risk of deliverability impact on small lists; send only to Active segment
              and pause non-critical communication until engagement recovers
```

**When to invest in segmentation infrastructure:**
```
Email list ≥ 5,000 subscribers?
→ No  → Basic full-list sends are operationally fine; build the Active/Dormant distinction
        when the list reaches 5,000
→ Yes → Segmentation is required before the next major campaign

Is the unsubscribe rate trending up across the last 3 sends?
→ No  → Segmentation is a growth investment
→ Yes → Segmentation is a retention emergency; pause all full-list sends immediately and
        suppress Dormant subscribers before the next send; an unsubscribe trend signals
        the list is receiving communication at a rate or relevance level it cannot absorb
```

**Win-back sequence decision:**
```
Has the subscriber been inactive for 180+ days?
→ Yes → Run win-back sequence: maximum 3 emails over 2 weeks
        Subject lines: curiosity-driven and artist-voice ("we haven't heard from you")
        outperform promotional ("20% off") for win-back — the relationship is the offer
        No open after the win-back sequence → suppress from all future sends permanently
→ No  → Continue regular sends; monitor open rate quarterly and run win-back at 180 days
```

### Domain anti-patterns

1. **Sending to purchased or scraped lists.** Purchased lists produce spam complaint rates that
   destroy sender reputation within 1–2 sends. The damage is structural: the sending domain's
   reputation degrades across all future sends, including to legitimate subscribers. Purchased
   lists are never appropriate and do not become appropriate at any scale.
2. **Sending at high frequency to the full list without segmentation.** Three or more emails per
   week to the full list — including dormant subscribers — compounds complaint rates and triggers
   inbox suppression. Dormant subscribers generate complaint rates disproportionate to their
   engagement; they should be suppressed from regular sends, not included.
3. **SMS without proper A2P registration in the US.** Sending marketing SMS without 10DLC
   registration results in carrier filtering and message blocking. This is not a technical
   edge-case risk — unregistered A2P SMS is actively filtered by major US carriers, and messages
   silently do not deliver. Registration through The Campaign Registry is a prerequisite, not
   an optional compliance step.
4. **Delayed or inconsistent opt-out processing.** TCPA and GDPR both require immediate
   opt-out effect on receipt of a STOP or unsubscribe request. A processing delay of even one
   business day is a compliance failure. Platform-based SMS tools automate this; any manual
   process requires same-session processing.
5. **Welcome email in brand voice, not artist voice.** The welcome email is the first message
   in the fan relationship; a corporate tone signals that the subscriber signed up for a brand
   newsletter rather than a connection. At minimum the opening of the welcome email must read
   as artist voice — first-person, specific, personal — even if subsequent emails in the
   sequence involve team assistance in production.

### Practitioner insight

**The 90-day engagement cliff.** The most reliable predictor of whether an email subscriber
becomes a long-term asset is whether they engage — open or click — within the first 90 days.
Subscribers who engage in the first 90 days show substantially higher long-term open rates than
those who never engage in that window. Subscribers who never engage in the first 90 days rarely
start. The welcome sequence is not optional polish — it is the infrastructure that determines
which side of this cliff each new subscriber lands on. Treat welcome-sequence open rate as the
single primary health metric for the email list: if it declines, the welcome sequence is the
first thing to fix.

---

## Music Modules

### Release-cycle email sequence

The standard release-cycle email sequence should begin at the announcement and run through the
post-release period:

```
Week −8 to −6  : announcement email — "you're the first to know"; artist voice;
                  pre-save link with plain-language explanation of what pre-saving does
Week −4 to −3  : single or campaign-content support — new track + creative context +
                  brief personal story; ask for streams and playlist adds
Week −2 to −1  : album-context content — tracklist reveal, artwork story, or audio
                  snippet; frame this as a community participation moment, not just content
Release week   : day-before countdown; release-day email with all listening links and
                  one primary CTA; post-release fan-reaction acknowledgment within 3–5 days
Post-release   : fan milestone email (streaming milestone, chart position); first tour
                  announcement if applicable; merch drop announcement linked to the release
```

**Pre-save email as data-capture leverage.** The pre-save email arrives at the highest
excitement moment in the release cycle — the announcement of new music. Pre-save campaigns that
include email capture (fans enter email to access the pre-save, or the pre-save is sent to
existing list subscribers) convert at high rates because intent is at its peak. On release day,
pre-saves convert to automatic library adds — giving the release an organic save-rate signal
that streaming analytics read as genuine listener intent. This is one of the highest-efficiency
data-capture moments in a music career and one of the most commonly under-executed.

### SMS cadence for a tour on-sale

The highest-performing SMS cadence for a tour announcement and on-sale sequence:

```
Day 1 (announcement) : "Tour dates just dropped — [fan-club presale link] opens in 24
                        hours. Check your city at [link]. Reply STOP to opt out."
Day 2 (fan presale)  : "Fan presale is LIVE now — [link]. Limited access. Ends [time].
                        Reply STOP to unsubscribe."
Day 5–7 (general)    : "General on-sale is [date] at [time]. Don't wait — [link].
                        Reply STOP to opt out."
Show week            : "[City] show is [X] days away. Last chance: [D2C merch link].
                        Reply STOP to opt out."
```

The gap between the announcement SMS and the fan-presale SMS should be 24 hours or less — a
longer gap means some subscribers miss the presale because they did not see the announcement
before it opened. The fan-presale SMS must state exact open time and close time; urgency framing
outperforms descriptive framing on response rate when inventory is genuinely limited.

### Email A/B testing framework

A/B testing at the right sample size prevents optimizing for statistical noise:

| List size | Minimum per test variant | Maximum variants | Hold time before deploy |
|-----------|------------------------|-----------------|------------------------|
| Under 2,000 | Not statistically meaningful — use editorial instinct | None | N/A |
| 2,000–10,000 | 500 per variant | 2 | 4 hours |
| 10,000–50,000 | 1,000 per variant | 2–3 | 2–4 hours |
| 50,000+ | 2,500 per variant | 3–4 | 2 hours |

**Subject-line variables that produce consistent interpretable results:** personalization token
(first name vs. no name); question form vs. statement form; urgency / scarcity framing vs.
neutral framing; emoji as the first character vs. no emoji; length under 40 characters vs.
40–70 characters. **Variable isolation rule:** never change both the subject line and the preview
text in the same A/B test. Changes must be isolated to one variable per test to produce
interpretable data. Changing multiple elements simultaneously produces a result with no
actionable learning.

### List growth mechanics for music

**Highest-converting email capture touchpoints, ranked:**

| Touchpoint | Intent level | Why it converts |
|-----------|-------------|----------------|
| Venue show sign-up (in-queue or at table) | Highest | Fan is present and emotionally activated; willing to give anything |
| Pre-save with email gate | Very high | Fan discovered new music and wants early access; intent is declared |
| Merch-checkout capture | High | Fan is in a purchase state; email is the receipt address |
| Social bio link with exclusive incentive | Medium | Fan navigated to bio deliberately; incentive completes the ask |
| Website pop-up with incentive | Medium-low | Fan is browsing; intent is not declared unless incentive is specific |

**Incentive quality by audience type:** an exclusive unreleased track or demo works for
music-first fans (zero cost, high perceived value for fans who want access to music); a presale
code works for live-attending fans (highest intent, most durable list entry); a discount code
works for merch-focused fans; a community invite or server role works for community-native
audiences. Match the incentive to the audience's primary motivation rather than defaulting to
a discount, which signals to music-first fans that the list is a commerce channel.

> Where the artist's historical email and SMS performance data — open rates, CTR by segment and
> sequence, unsubscribe trends, complaint rates — is available, use it to calibrate all thresholds
> and timing above to the artist's specific list dynamics. Generic benchmarks are starting points;
> artist-specific data supersedes every default in this file.
