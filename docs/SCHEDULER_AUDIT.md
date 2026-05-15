# PLMKR — Scheduler Audit

**Produced:** 2026-05-15 S3 Unit 2  
**Method:** Static code audit — no jobs fired, no scheduler started, all findings from source reading only  
**Branch at audit time:** feat/deferred-risks-may15-s3-unit2-r27-scheduler-audit (base: main 2e59156)  
**Risk R-27 reference:** Scheduler not enabled — all timed jobs inactive

---

## Summary

| Job ID | Schedule | Risk Level |
|--------|----------|------------|
| `inbox_poll` | interval every 6h (configurable) | MEDIUM |
| `weekly_reports` | cron configurable (default Sun 18:00 UTC) | MEDIUM |
| `campaign_executor` | interval every 1h | HIGH |

**STOP-SHIP jobs found: 0** — Unit 3 (enable mechanism) is cleared to proceed.

---

## Job 1 — `inbox_poll`

**Job ID:** `inbox_poll`  
**Registered in:** `pitch_service.py:1148-1151`  
**Trigger:** interval, every `_REPLY_POLL_HOURS` hours  
**Schedule:** Default 6h; configurable via `REPLY_POLL_HOURS` env var  
**Misfire grace:** 300s  
**coalesce:** true

**Function called:** `_poll_all()` (defined inline at `pitch_service.py:1138`)

**Callgraph:**
```
_poll_all()
  └─ _get_artists_with_sent_pitches()   — SQLite read (pitches table)
  └─ for each artist_id:
       └─ detect_replies(artist_id)     — pitch_service.py:1010
            ├─ _get_gmail_service(artist_id)        — loads OAuth tokens from artist profile
            ├─ Gmail API: messages.list() — reads up to 50 inbox messages (EXTERNAL READ)
            ├─ for each message:
            │    └─ Gmail API: messages.get()        (EXTERNAL READ — up to 50 round-trips)
            ├─ for each matched reply:
            │    ├─ _classify_reply(body_text)       — pitch_service.py:941
            │    │    └─ _anthropic_call_with_retry() (EXTERNAL API CALL — Anthropic)
            │    ├─ _db_update_pitch()                — SQLite write (pitch status)
            │    └─ _db_upsert_curator()              — SQLite write (response_rate)
            └─ returns {"scanned", "matched", "classified"}
```

**Side effects:**
- Gmail API reads (up to 50 messages per artist per poll) — **external read, no cost in isolation**
- Anthropic API calls — **consumes API credits**, one call per matched reply
- SQLite writes: pitch status updated, curator response_rate updated, PitchInteraction appended
- No emails sent, no SMS, no social posts, no DB deletes

**Risk level: MEDIUM**
- External API reads (Gmail, Anthropic) — failures are retried or logged; no data loss
- Credit consumption proportional to reply volume; bounded by inbox size (50 msgs per artist per tick)
- Fully recoverable if it fails — pitches stay at prior status; next poll re-evaluates
- If Gmail auth expired: `detect_replies` returns error; caught by try/except in `_poll_all`

**Notes before enabling:**
- Gmail OAuth must be connected per artist (R-16). If unconnected, `_get_gmail_service` raises `HTTPException`; `_poll_all` logs the error and continues to the next artist.
- `ANTHROPIC_API_KEY` must be set or reply classification returns a neutral/fallback result.
- No risk of duplicate emails or side effects to external parties from this job.

---

## Job 2 — `weekly_reports`

**Job ID:** `weekly_reports`  
**Registered in:** `social_service.py:998-1007` (via `init_report_scheduler()`)  
**Trigger:** cron  
**Schedule:** day=`_WEEKLY_REPORT_DAY`, hour=`_WEEKLY_REPORT_HOUR`, minute=`_WEEKLY_REPORT_MINUTE`  
  — Default: Sunday 18:00 UTC (configurable via `WEEKLY_REPORT_DAY`, `WEEKLY_REPORT_HOUR_UTC`, `WEEKLY_REPORT_MINUTE`)  
**Misfire grace:** 120s  
**coalesce:** true

**Shares scheduler instance with** `inbox_poll` (adds job to `pitch_service._scheduler`).

**Function called:** `_generate_all_weekly_reports()` (`social_service.py:971`)

**Callgraph:**
```
_generate_all_weekly_reports()
  └─ _get_artists_with_any_activity()   — SQLite read (pitches + pr_outreach + booking_inquiries + social_posts)
  └─ for each artist_id:
       └─ generate_weekly_report(artist_id)   — social_service.py:887
            ├─ _get_artist_timezone()          — reads artist profile
            ├─ _week_boundaries_in_tz()        — pure computation
            ├─ _load_artist_data()             — reads artist profile file
            ├─ _aggregate_week_data()          — SQLite reads across multiple tables
            ├─ _anthropic_call_with_retry()    (EXTERNAL API CALL — Anthropic Sonnet, 1200 tokens)
            └─ _db_save_report()              — SQLite write (weekly_reports table)
```

**Side effects:**
- Anthropic API call per artist with any activity — **consumes API credits**
- SQLite write per artist (weekly_reports table)
- No emails sent, no SMS, no external services beyond Anthropic
- No deletes, no irreversible actions

**Risk level: MEDIUM**
- Bounded by number of active artists in DB
- Reports are readable via `GET /api/reports/weekly/{id}` — visible, auditable
- Fully reversible: delete report rows from weekly_reports table; re-run generates fresh report
- Failed Anthropic call: `generate_weekly_report` raises; caught in `_generate_all_weekly_reports`; error logged; other artists continue

**Notes before enabling:**
- No Gmail OAuth required for this job — purely Anthropic + SQLite.
- Run on a small artist set (1-2 artists with activity) to verify credit consumption is reasonable.
- If `_WEEKLY_REPORT_HOUR` is 18 and `_WEEKLY_REPORT_DAY` is sun, first real fire is the coming Sunday at 18:00 UTC.

---

## Job 3 — `campaign_executor`

**Job ID:** `campaign_executor`  
**Registered in:** `main.py:1269-1277`  
**Trigger:** interval, every 1 hour  
**Misfire grace:** 120s  
**coalesce:** true

**Function called:** `execute_all_due_campaign_actions()` (`release_service.py:555`)

**Callgraph:**
```
execute_all_due_campaign_actions()
  └─ _db_list_due_actions()             — SQLite read (campaign_actions WHERE status='pending' AND scheduled_for <= now)
  └─ batch = due_actions[:SCHEDULER_BATCH_LIMIT]    (default cap: 10)
  └─ for each action in batch:
       ├─ _db_update_action(status='running')         — SQLite write
       └─ _execute_action(action)        — release_service.py:306
            ├─ ACTION_PITCH:
            │    ├─ _db_list_curators()               — SQLite read
            │    ├─ BatchPitchRequest(artist_id, curator_ids[:10], ...)
            │    └─ send_pitch_emails(req)             — pitch_service
            │         ├─ _check_and_increment_quota() — SQLite read+write (daily quota)
            │         ├─ _anthropic_call_with_retry() (EXTERNAL — Anthropic Haiku)
            │         └─ Gmail API: send message       (EXTERNAL — sends real email)  ⚠️
            │
            ├─ ACTION_PR:
            │    ├─ _db_list_pr_contacts()             — SQLite read
            │    ├─ BatchPRRequest(artist_id, contact_ids[:8], ...)
            │    └─ send_pr_emails(req)                — pr_service
            │         ├─ _anthropic_call_with_retry() (EXTERNAL — Anthropic Haiku)
            │         └─ Gmail API: send message       (EXTERNAL — sends real email)  ⚠️
            │
            ├─ ACTION_BOOKING:
            │    ├─ _db_list_booking_contacts()        — SQLite read
            │    ├─ BatchBookingRequest(artist_id, contact_ids[:5], ...)
            │    └─ send_booking_emails(req)           — booking_service
            │         ├─ _anthropic_call_with_retry() (EXTERNAL — Anthropic Haiku)
            │         └─ Gmail API: send message       (EXTERNAL — sends real email)  ⚠️
            │
            └─ ACTION_SOCIAL:
                 └─ batch_social_posts(req)            — social_service
                      └─ _buffer_schedule_post()       (MOCKED — no real Buffer call)  ✓
```

**Side effects:**
- **Real emails sent via Gmail** to curators, PR contacts, booking contacts — **irreversible** ⚠️
- Anthropic API calls (Haiku) — consumes API credits per pitch/PR/booking email generated
- SQLite writes: campaign_action status, pitch/PR/booking records created with idempotency keys
- Social posts: MOCKED — no real Buffer calls in current implementation
- Daily quota enforced: `_check_and_increment_quota()` caps pitch emails at `DAILY_PITCH_QUOTA` (default 50) per artist per day

**Bounds on first enable:**
- Batch cap: `SCHEDULER_BATCH_LIMIT` (default 10) campaign actions per hourly tick
- Per-action email caps: pitch ≤ 10 curators, PR ≤ 8 contacts, booking ≤ 5 contacts
- Idempotency: deterministic keys by `(artist_id, curator_id)` — duplicate calls skip existing records
- First-run behavior: if existing releases have past-due pending actions, up to 10 fire immediately. Next tick processes the next 10, and so on.

**Risk level: HIGH**
- Sends **real emails to external curators, press, and venues** — cannot be recalled once sent
- Email content is AI-generated (Anthropic) — inspect generated pitches before enabling at scale
- If curator/PR/booking DB has seed data only (not real contacts), emails go to seed email addresses (which may or may not be real)
- Irreversible from a sender-reputation standpoint
- **Not STOP-SHIP** because: bounded by SCHEDULER_BATCH_LIMIT; idempotent; operates only on releases already in DB; sender reputation risk is proportional to DB size

**Critical notes before enabling:**
1. Verify `GMAIL_OAUTH_CLIENT_ID/SECRET/REDIRECT_URI` are set and at least one artist has authorized Gmail (R-16).
2. Verify curator/PR/booking seed data contains email addresses you're prepared to send to.
3. Set `SCHEDULER_BATCH_LIMIT=1` on first enable to send one action per tick; observe; raise gradually.
4. Review first generated email text before scheduler sends bulk (use `POST /api/pitches/preview` or similar).
5. Ensure `DAILY_PITCH_QUOTA` is set appropriately (default 50 may be too high for initial testing).

---

## What Was NOT Found

- No scheduler job that mass-emails all artists simultaneously (only contacts in DB)
- No scheduler job that charges payment methods
- No scheduler job that posts to social media without Buffer OAuth (all mocked)
- No scheduler job that sends SMS
- No scheduler job that deletes or overwrites production data

---

## Flip-the-Switch Checklist (Safe Scheduler Activation Order)

Use this checklist in order. Do NOT skip steps.

### Phase 1 — Verify audit findings
- [ ] Re-read `SCHEDULER_AUDIT.md` Job 3 notes. Confirm no STOP-SHIP condition applies.
- [ ] Confirm Railway persistent volume is attached (`/data` mount) — R-02. Without it, DB is wiped on redeploy.
- [ ] Confirm `APP_BASE_URL` is set on Railway — R-11. App will crash without it.
- [ ] Confirm `GMAIL_OAUTH_CLIENT_ID/SECRET/REDIRECT_URI` are set — R-16.
- [ ] Authorize Gmail for at least one test artist (`GET /api/gmail/auth?artist_id=<id>`).
- [ ] Review curator/PR/booking seed data — confirm email addresses are real and you're prepared to contact them.

### Phase 2 — Set SCHEDULER_ENABLED=dry_run (safe observation)
- [ ] In Railway Variables: set `SCHEDULER_ENABLED=dry_run`
- [ ] Save → Railway redeploys
- [ ] Boot log must show: `scheduler_started` event with `dry_run` context
- [ ] Observe Railway logs for 24h — confirm `would_have_fired` events appear on schedule
- [ ] Confirm no real Gmail sends appear in Gmail Sent folder
- [ ] Confirm no real Anthropic credit is consumed (check Anthropic dashboard)

### Phase 3 — Set SCHEDULER_ENABLED=true (live)
- [ ] In Railway Variables: change `SCHEDULER_ENABLED=dry_run` → `SCHEDULER_ENABLED=true`
- [ ] Set `SCHEDULER_BATCH_LIMIT=1` for the first 24h (safest ramp)
- [ ] Save → Railway redeploys
- [ ] Check first scheduled tick in Railway logs — confirm one action fires
- [ ] Check Gmail Sent folder — confirm one pitch email was generated and sent
- [ ] If all looks correct: raise `SCHEDULER_BATCH_LIMIT` to 3, then 5, then 10 over successive days
- [ ] Monitor `GET /api/admin/diagnostics/scheduler` for queue depth and errors

### Rollback
- [ ] Set `SCHEDULER_ENABLED=false` → Railway redeploys → scheduler stops immediately
- [ ] No data rollback needed (emails already sent cannot be recalled; DB records can be inspected)
