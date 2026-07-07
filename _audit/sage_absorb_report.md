# Sage absorb-check — read-first report (Unit 2, no code changed)

**Agent under review:** Sage (`release-strategist`) — Release Strategist, "Release planning,
campaign orchestration, cross-phase launch strategy"
**Candidate absorber:** Tommy (`label-services`) — Label Services, "Distribution, release
planning, label setup, delivery to DSPs"
**Branch:** `fix/consult-honesty-sweep` (this unit made NO code changes — report only)
**Base:** `origin/main` tip `c5d400a`, unmoved
**Verified directly against current code** — `main.py`, `release_service.py`,
`label_services_service.py` — not against any stale audit snapshot.

---

## What Sage actually is

`_release_automation_state()` / `RELEASE_AUTOMATION_CONNECTED` are at `main.py:7734-7739`
(shifted from the `~7578` line number in the prior note, confirmed by grep, not assumed).
`RELEASE_STRATEGIST_TOOLS` (`main.py:7742`) has exactly 3 tools:

- `list_releases` — reads `release_service._db_list_releases(artist_id)`.
- `create_release` — writes a real row via `release_service._db_create_release(...)`.
- `schedule_campaign` — gated on `_release_automation_state()`
  (`RELEASE_AUTOMATION_CONNECTED` env flag, connected/expired/not_connected states,
  identical shape to the Unit-1 gate pattern). When connected, it calls
  `release_service._build_campaign_actions(release)` and persists each action via
  `release_service._db_create_action(a)`.

Backing `release_service.py` (583 lines) is a full DB-backed campaign-orchestration engine,
**not** a mock-first sha1-reference module:

- Two real SQLite tables (`releases`, `campaign_actions`) with a proper schema, indexes, and
  crash-recovery (`UPDATE campaign_actions SET status='pending' WHERE status='running'` on
  boot, for actions stuck mid-execution by a prior crash).
- `_CAMPAIGN_SCHEDULE`: a 21-entry, day-offset-from-release-date campaign calendar spanning
  venue-advance booking (-21d), two pitch waves, two PR waves, and a daily social cadence from
  -7d to +7d around the release date.
- `_execute_action()` dispatches each due action to **real, already-integrated services** —
  `pitch_service.send_pitch_emails`, `pr_service.send_pr_emails`,
  `booking_service.send_booking_emails`, `social_service.schedule_posts` — i.e. once
  `schedule_campaign` is connected and actions come due, Sage's system sends real pitch/PR/
  booking outreach and schedules real social posts. This is categorically different from the
  Unit-1 retirement pattern (every Unit-1 tool's *only* effect was a `hashlib.sha1`-derived
  fake reference string with zero downstream effect, regardless of gate state).
- `execute_all_due_campaign_actions()` is a scheduler hook (called from `main.py` on an
  interval) that sweeps and fires due actions in capped batches — genuine background
  automation, not a per-request mock.
- A parallel REST surface (`/api/releases`, `/api/releases/{id}/generate-campaign`,
  `/api/releases/{id}/campaign`, `/api/releases/{id}/campaign/execute-due`) exists
  independently of the agent tool_use loop.

**Conclusion: `RELEASE_AUTOMATION_CONNECTED` is not a mock-retirement candidate.** It gates a
real automation surface, not a fake one. This item was correctly out of scope for Unit 1's
sweep (Unit 1's scope was tools whose *only* effect was a deterministic fake reference string).

## What Tommy (label-services) actually is

`LABEL_SERVICES_TOOLS` (`main.py:6322`) has 6 tools: `search_distribution_requirements`,
`validate_release_metadata`, `deliver_to_dsps` (Tommy's own mock-first sha1 action, gated on
`LABEL_SERVICES_CONNECTED`, untouched — Tommy is not in the Tommy-15 excluded-by-name list),
`lookup_release_requirements`, `build_release_checklist`, `build_release_doc_scaffold`. These
were shipped in the overnight build (`_audit/overnight_final_report.md`, Agent A) on top of a
`release_data.py` data corpus: `IDENTIFIER_RULES`, `METADATA_FIELDS`, `ARTWORK_SPEC`,
`TIMELINE_DOCTRINE`, `RELEASE_RECORD_SPEC`, `DISTRIBUTOR_SWITCH_MECHANISM`, `HONESTY_RULES`.

Tommy's whole domain is **delivery-side compliance**: identifier conventions (ISRC/UPC/ISWC),
ordered metadata fields, artwork specs, work-backwards upload lead times, and getting a release
correctly delivered to DSPs (Spotify/Apple/Beatport/Bandcamp). Nothing in Tommy's surface
touches pitching curators, PR outreach, booking inquiries, or social scheduling — Tommy never
imports `pitch_service`, `pr_service`, `booking_service`, or `social_service`.

The overnight report itself flags this boundary explicitly (`_audit/overnight_final_report.md`,
"Flagged but untouched"): *"`RELEASE_AUTOMATION_CONNECTED` @ `main.py:7578` resolves to
release-strategist (Sage), NOT Tommy (label-services)... Tommy's real surface is
`label_services_service.py` / `LABEL_SERVICES_TOOLS`."* That prior-session finding is
reconfirmed here against current code.

## Why this does not fold cleanly

1. **Different domains, only superficially overlapping wording.** Both roster entries mention
   "release planning," but Sage's actual mechanics are cross-phase *marketing/outreach
   orchestration* (pitch/PR/booking/social scheduling around a release date), while
   label-services' actual mechanics are *distribution/delivery compliance* (identifiers,
   metadata, artwork, DSP delivery). Folding Sage's `releases` + `campaign_actions` tables and
   its 21-entry campaign calendar into `label_services_service.py` would bolt an entire
   marketing-automation subsystem onto a service whose only other action is `deliver_to_dsps`.
2. **No duplicate tools to retire.** Sage's 3 tools (`list_releases`, `create_release`,
   `schedule_campaign`) share no name, no shape, and no backing function with any of Tommy's 6
   tools. There is nothing "genuinely duplicate" between the two agents to retire — the
   Unit-1-style question ("keep the real persistence, retire the duplicate mock wrapper") does
   not apply because Sage has no duplicate wrapper around a Tommy capability; it has a whole
   independent capability.
3. **Sage's gate is a real feature gate, not a fake-action mask.** Unlike the 14 Unit-1
   retirements, disconnecting `RELEASE_AUTOMATION_CONNECTED` blocks a real automation from
   firing (rather than merely blocking a fake reference string from being minted). Removing or
   silently folding this gate would be a functional regression, not an honesty fix — out of
   scope for a mock-retirement sweep regardless of which agent owns it.
4. **REST surface is independent of the agent layer.** `release_service.py`'s `/api/releases/*`
   endpoints and its scheduler hook (`execute_all_due_campaign_actions`, called from `main.py`
   on an interval) exist and run independently of which agent's tool_use loop calls into it.
   Moving this module under `label_services_service.py`'s ownership would require touching a
   scheduler wiring point and REST routes that have nothing to do with Tommy's DSP-delivery
   domain — a much larger, riskier refactor than "fold a duplicate wrapper."

## Decision needed from Tommy (the human)

This is a **product boundary decision**, not a code-quality one — the two plausible resolutions:

- **(a) Keep separate (recommended by this read).** Sage owns cross-phase campaign
  orchestration (the real `release_service.py` engine); label-services owns DSP-delivery
  compliance (the `release_data.py`-backed doc/checklist tools). Both are real, both are
  distinct, and the roster copy for Sage ("release planning, campaign orchestration,
  cross-phase launch strategy") already reflects this; only the word "release planning"
  overlaps with Tommy's "release planning" — consider trimming Sage's roster blurb to remove
  that overlapping phrase so the two agents' one-line descriptions stop reading as duplicates,
  without touching either agent's actual tools.
- **(b) Split differently.** If Tommy wants a single "release" agent, the split would need to
  be: label-services keeps identifiers/metadata/artwork/DSP-delivery; release-strategist keeps
  campaign scheduling/outreach dispatch — which is already the current split. The only
  remaining ambiguity is the shared word "release planning" in both roster blurbs, not an
  actual code overlap.

No code was changed for this unit. `schedule_campaign`'s `RELEASE_AUTOMATION_CONNECTED` gate is
untouched and remains a legitimate (non-mock) feature gate. Full suite confirmed unaffected
(0 code changes ⇒ 0 risk) — see final report for the shared post-Unit-2 suite run.

**SAGE_ABSORB_ENTANGLED**
