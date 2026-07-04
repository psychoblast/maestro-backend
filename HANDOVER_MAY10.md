# PLMKR HANDOVER — May 10, 2026

## 1. WHERE WE ARE

PLMKR backend is **feature-complete for v1**. As of May 9 autonomous CC run,
all 5 phases are built, tested, and committed to main:

- Phase 0 — Foundation (backend done; frontend + device items still open)
- Phase 1 — Curator Pitching
- Phase 2 — PR & Booking Outreach
- Phase 3 — Social Scheduling + Weekly Reports
- Phase 4 — Release Campaign Orchestration (NEW May 9)

**Tests:** 78/78 passing on main
**Last commit on main:** merge of `phase-4-autonomous` (merge commit `fecbeec`)
**API spend last session:** ~$0 (all tests use mocked Anthropic client)

The remaining gap to launch is **manual configuration + device testing**, NOT
more code. Resist the urge to keep building until config is done.

---

## 2. WHAT SHIPPED MAY 9 (autonomous CC run)

9 commits on `phase-4-autonomous` branch, merged to main:

- 55825ae [docs] Session report May 9 — autonomous build session complete
- 27a9374 [docs] OpenAPI spec export for frontend integration
- dacadf5 [phase-4] Release campaign orchestration — release_service + Sage agent
- 5419fe9 [admin] Stats and deep health endpoints
- b16e251 [harden] Structured logging across outreach services
- f4cbea9 [harden] Gmail 429 retry with exponential backoff
- 8ed0073 [harden] Idempotency keys on outreach sends
- 5f0b69e [test] Repair 7 pre-existing pitch service test failures
- 7bab81e [fix] Persist momentum_score/headline/highlights in weekly_reports DB

**New files:**
- release_service.py (550 lines, Phase 4)
- admin_service.py (183 lines)
- PHASE4_PLAN.md (Phase 4 design doc)
- SESSION_REPORT_MAY9.md (full session detail)
- docs/openapi.json (5068 lines, full OpenAPI 3 spec)
- scripts/export_openapi.py
- skills/maestro-release-strategist/SKILL.md (Sage agent)
- tests/integration/test_release_lifecycle.py
- tests/test_admin_service.py (6 tests)
- tests/test_release_service.py (13 tests)

**Phase 4 (Release Campaign Orchestration) — what it does:**
Artist creates a Release (title, release_date, genre, mood). System auto-schedules
campaign actions across Phases 1–3:
- Curator pitches: release_date -14d, -7d, day-of
- PR outreach: -10d, -3d
- Booking inquiries: -21d
- Social posts: daily ramp -7d through +7d

Sage agent orchestrates. Scheduler scans campaign_actions hourly for due actions.

**New endpoints:**
- POST  /api/releases
- GET   /api/releases?artist_id=...
- GET   /api/releases/{id}
- PATCH /api/releases/{id}
- POST  /api/releases/{id}/generate-campaign
- GET   /api/releases/{id}/campaign
- POST  /api/releases/{id}/campaign/execute-due
- GET   /api/admin/stats?artist_id=...&since=ISO_DATE
- GET   /api/admin/health/deep

---

## 3. PRIORITY MANUAL QUEUE — DO NOT BUILD MORE UNTIL THESE DONE

In execution order:

### A. Google Cloud OAuth setup (30 min)
- console.cloud.google.com → APIs & Services → Credentials
- Create OAuth 2.0 Client ID, Web Application
- Authorized redirect URI: https://maestro-backend-production-6d9c.up.railway.app/api/gmail/callback
- Set on Railway env vars: GMAIL_OAUTH_CLIENT_ID, GMAIL_OAUTH_CLIENT_SECRET, GMAIL_OAUTH_REDIRECT_URI
- Redeploy from Railway dashboard

### B. Replace 3–5 curator emails with real ones (NOT all 50)
File: data/curators_seed.json
Why only 3–5: bouncing 50 emails from a fresh Gmail address is a fast way
to get sender reputation flagged. Send to a small known-good list first.
After clean delivery confirmed, expand.

### C. Bug 1 deploy verification on Railway
The momentum_score/headline/highlights persistence fix needs the SQLite
migration to run on the live Railway DB. Verify via GET /api/reports/weekly/{id}
and confirm response contains momentum_score, headline, highlights.

### D. End-to-end Phase 1 test with real Gmail (30 min)
- Visit GET /api/gmail/auth?artist_id=TOMMY_ARTIST_ID in browser
- Complete OAuth
- POST /api/pitches/generate — verify Claude output looks reasonable
- POST /api/pitches/batch to ONE real curator
- Verify email lands in your Sent folder
- Wait for reply or manually inject test reply
- POST /api/inbox/scan — verify status changes to "replied"

### E. Phase 0 device-bound items (separate session — physical device required)
- 0.D — Twilio SMS OTP test on real Android device
- 0.E — first call failure: capture logcat from real device
- 0.1/0.2/0.3 — frontend CallScreen.js voice mapping fixes
  (these live in the frontend repo, separate directory, NOT ~/maestro/ — separate session, separate concern)

### F. Buffer OAuth (deferrable until Phase 3 social scheduling actually used)
- buffer.com/developers/apps
- Set BUFFER_CLIENT_ID, BUFFER_CLIENT_SECRET, BUFFER_REDIRECT_URI

### G. Enable scheduler when ready
Set SCHEDULER_ENABLED=true on Railway. Triggers:
- Inbox poll every 6h (pitches + PR + booking)
- Weekly report Sundays 18:00 UTC
- Release campaign execute-due hourly

---

## 4. KNOWN ISSUES / TECH DEBT

None new from May 9 run. Bug 1 fixed. Pre-existing 7 test failures resolved.
Bug 2 (batch send identical thread_id) was confirmed to be a test infra
issue, not a production bug — already mitigated in integration tests via
AsyncMock(side_effect=...).

---

## 5. KEY FILES TO READ FIRST NEXT SESSION

- CLAUDE.md                       — Build protocol — every session
- HANDOVER_MAY10.md                — This file
- SESSION_REPORT_MAY9.md           — Full detail of May 9 autonomous run
- PHASE4_PLAN.md                   — Release Campaign Orchestration design
- TODOS.md                         — Current task list
- docs/API_REFERENCE.md            — Endpoint inventory
- docs/DEPLOYMENT_CHECKLIST.md     — Railway deploy steps + smoke tests
- docs/openapi.json                — Full OpenAPI 3 spec (76 endpoints)

---

## 6. RECOMMENDED NEXT SESSION SCOPE

**Do NOT start with more building.** PLMKR has more code than configuration
can support. The next PLMKR session should be entirely manual:

1. Google Cloud OAuth setup (A above)
2. Replace 3–5 curator emails with real targets (B)
3. Verify Bug 1 fix on live Railway (C)
4. End-to-end Phase 1 send + scan with real Gmail (D)

If those four are done in one session, PLMKR Phase 1 hits true production-ready.
Phase 2, 3, 4 can be similarly verified in subsequent sessions using the same
real OAuth credentials.

If you have remaining time/energy, Phase 0 device items (E) are the next
unblock. Frontend CallScreen.js fixes are in a separate codebase
(the frontend repo, separate directory) — DO NOT touch from a ~/maestro/ session.

---

## 7. BUILD PROTOCOL REMINDERS

- ALWAYS read CLAUDE.md first, every session
- ONE unit at a time; verify before moving on
- Never patch forward on failure — git stash, revert, re-diagnose
- Never exceed $10 without verified working result in Railway logs
- Never work on main directly — create a branch; merge only when verified
- Commit after every working change; never batch units
- Test with real data once OAuth is live
- Verify Railway is serving new code after every push
- Frontend lives in a separate repo (separate directory) — separate session, separate concern
