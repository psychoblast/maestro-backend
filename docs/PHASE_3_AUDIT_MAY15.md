# PLMKR — Phase 3 Audit (May 15, 2026, Session 8)

Read-only investigation. Phase 3 was built in prior sessions. This document audits the actual
state against the Phase 3 north-star (artist receives first real weekly report summarizing
their activity) and identifies the gaps to close in this session.

---

## Summary

Phase 3 is **substantially complete** — 1093 lines in `social_service.py`, Riley registered as
social-manager agent, 4 platforms supported, full Buffer integration (mocked behind `BUFFER_LIVE=false`),
full weekly report generation with Claude Sonnet synthesis, cross-phase data aggregation,
scheduler integration, and ~44 tests across 8 test files + 2 integration tests.

Three gaps remain: **LinkedIn platform missing**, **report email delivery absent** (reports stored
in DB only, never emailed to artists), and **empty-state handling untested**.

| Section | Area | Status |
|---------|------|--------|
| A | Riley agent (Social Media Manager) | ✅ COMPLETE |
| B | Social posting infrastructure (Buffer) | ✅ COMPLETE |
| C | Content generation per platform | 🟡 PARTIAL — LinkedIn missing |
| D | Scheduling + batch orchestration | ✅ COMPLETE |
| E | Performance metrics aggregation | ✅ COMPLETE |
| F | Weekly report generation | ✅ COMPLETE |
| G | Report delivery | ❌ MISSING — DB-only, no email delivery |
| H | Test coverage | 🟡 PARTIAL — empty-state not tested |

---

## (A) Riley Agent (Social Media Manager)

**Status: ✅ COMPLETE**

- `main.py:131`: `{"id": "social-manager", "name": "Riley", "title": "Social Media Manager", "skill": "maestro-social-manager", "voice": "af_sky", ...}` — registered in global agent list
- `main.py:374-376`: 3 greeting variants for Riley
- `skills/maestro-social-manager/SKILL.md`: skill file present
- `social_service.py:580`: `_RILEY_SYSTEM` — "You are Riley, Social Media Manager at Playmaker..."
  - Per-platform native voice rules (Twitter = punchy, Instagram = visual + warm, TikTok = energetic)
  - Writes IN the artist's voice, not marketing copy
  - Returns JSON: `{content, suggested_media_prompt, optimal_posting_window}`

Riley's persona is consistent across all three: skill file, greeting variants, and system prompt.

---

## (B) Social Posting Infrastructure

**Status: ✅ COMPLETE**

### Buffer integration (social_service.py:384-559)

- `_buffer_schedule_post()` (L512): routing logic per R-26:
  - `BUFFER_LIVE=false` or `BUFFER_API_KEY` unset → mock response (safe default)
  - `SCHEDULER_ENABLED=dry_run` → logs `would_have_posted`, mock response
  - `BUFFER_LIVE=true` + `BUFFER_API_KEY` set → `_buffer_post_real()` (real HTTP)
- `_buffer_post_real()` (L453): async httpx, 10s timeout, 429 retry (2 retries, exp backoff)
- Buffer OAuth: `/api/buffer/auth` (L399), `/api/buffer/callback` (L413), `/api/buffer/status` (L447)
- `BUFFER_LIVE=false` is the correct default — R-26 mitigated in S3

### SocialPost table (social_service.py:68-84)

```
social_posts: id, artist_id, platform, content, media_url, status, scheduled_at,
              posted_at, post_url, engagement_stats (JSON), buffer_update_id, created_at
```

Full CRUD: `_db_create_post`, `_db_get_post`, `_db_list_posts`, `_db_update_post`, `_db_delete_post`.
REST endpoints: GET/POST/PATCH/DELETE `/api/social/posts`, `/api/social/posts/{post_id}`.

---

## (C) Content Generation Per Platform

**Status: 🟡 PARTIAL — LinkedIn missing**

### Supported platforms (social_service.py:566-578)

```python
_PLATFORM_LIMITS = {
    "twitter":   280,
    "instagram": 2200,
    "tiktok":    2200,
    "facebook":  1000,
}
_PLATFORM_STYLE = {
    "twitter":   "punchy, direct, hook in first 8 words, no hashtag overload (max 2), conversational",
    "instagram": "warm and visual, lead with emotion, use 3-5 relevant hashtags at end, emojis ok",
    "tiktok":    "energetic, trend-aware, speak to Gen Z/Millennial, hook is everything, casual",
    "facebook":  "slightly longer form, storytelling tone, community-focused, less hashtags",
}
```

**Missing: LinkedIn** — not in `_PLATFORM_LIMITS` or `_PLATFORM_STYLE`. LinkedIn is a relevant
platform for music industry networking and artist brand-building.

### Content generation: `generate_social_post()` (L595-650)

- Artist profile fields: `artist_name`, `genre`, `bio[:200]`
- Context fields: `release`, `show`, `news`, `custom`
- Enforces character limit on content field
- Returns: `{content, suggested_media_prompt, optimal_posting_window}`

### Batch: `schedule_posts()` (L685-759)

- Generates `posts_per_platform` posts per platform, spread evenly across 7 days
- Optionally schedules via Buffer (`schedule_buffer=True`)
- Returns: `{generated, scheduled_via_buffer, errors, post_ids}`

---

## (D) Scheduling + Batch Orchestration

**Status: ✅ COMPLETE**

- `POST /api/social/posts/generate` — single post generation
- `POST /api/social/posts/batch` — batch generation + optional Buffer scheduling
- Scheduler integration: `init_report_scheduler()` (L1061) — adds weekly report cron job to
  pitch_service's APScheduler instance; no-op unless `SCHEDULER_ENABLED=true/dry_run`
- `_generate_all_weekly_reports()` (L1045): finds all artists with activity, generates per-artist
  reports; logs `would_have_fired` in dry_run mode
- Schedule configurable via R-28: `WEEKLY_REPORT_DAY`, `WEEKLY_REPORT_HOUR_UTC`, `WEEKLY_REPORT_MINUTE`
- Per-artist timezone: `_week_boundaries_in_tz()` (L151) uses ZoneInfo; falls back to UTC

---

## (E) Performance Metrics Aggregation

**Status: ✅ COMPLETE**

`_aggregate_week_data(artist_id, week_start, week_end)` (L879) queries all Phase 1+2+3 tables:

| Phase | Table | Fields counted |
|-------|-------|----------------|
| Phase 1 | `pitches` | sent, replied, reply_rate |
| Phase 2 | `pr_outreach` | sent, replied, featured |
| Phase 2 | `booking_inquiries` | sent, replied, booked |
| Phase 3 | `social_posts` | posted, scheduled |

Each query wrapped in `try/except` — safe on fresh DBs or when tables don't exist yet.
Returns structured dict with `week_start`, `week_end`, and all four category dicts.

---

## (F) Weekly Report Generation

**Status: ✅ COMPLETE**

- `generate_weekly_report(artist_id, week_start, week_end)` (L961):
  - Aggregates cross-phase metrics
  - Calls Claude Sonnet (`claude-sonnet-4-6`) with `_REPORT_SYSTEM` prompt
  - Returns: `{id, artist_id, week_start, week_end, summary, insights, recommendations, momentum_score, headline, highlights, generated_at}`
  - Saves to `weekly_reports` table
- `weekly_reports` table includes `momentum_score` (1-10), `headline`, `highlights` (JSON array)
- Schema migration handles existing DBs (R-24 mitigation)
- `POST /api/reports/weekly/generate`, `GET /api/reports/weekly/{id}`, `GET /api/reports/weekly`

---

## (G) Report Delivery

**Status: ❌ MISSING**

Reports are generated and saved to the `weekly_reports` SQLite table but are **never delivered
to artists**. The north-star goal is "artist receives first real weekly report" — receiving implies
delivery to a communication channel.

**What exists:** DB storage + API retrieval only. Artist must manually call `GET /api/reports/weekly`
or consume the generated report via the frontend.

**What's missing:**
1. `_email_weekly_report(artist_id, report)` — send the generated report via Gmail (existing
   `send_email()` infrastructure from pitch_service)
2. HTML email template (inline or template string) for the report body
3. Plain-text fallback
4. Wire the email send into `generate_weekly_report()` (after DB save, before return)

The send should be mocked at the Gmail boundary (same pattern as pitch_service, pr_service,
booking_service). `GmailNotConnected` is the expected exception when Gmail is not yet linked;
should log a warning rather than raise — the report should still be saved even if email fails.

---

## (H) Test Coverage

**Status: 🟡 PARTIAL — 44 tests, empty-state uncovered**

| File | Count | Coverage area |
|------|-------|---------------|
| `tests/test_social_service.py` | 8 | Post CRUD, generate_social_post, batch |
| `tests/test_reports.py` | 7 | Report CRUD, aggregate, generate, momentum |
| `tests/test_r26_buffer_live_client.py` | 9 | Buffer real client (R-26) |
| `tests/test_r27_scheduler_dry_run.py` | 6 | Dry-run scheduler mode (R-27) |
| `tests/test_r28_configurable_report_schedule.py` | 5 | Configurable schedule (R-28) |
| `tests/test_f01_per_artist_timezone.py` | 7 | Per-artist timezone (F-01) |
| `tests/integration/test_weekly_report.py` | 1 | Full weekly report lifecycle |
| `tests/integration/test_social_lifecycle.py` | 1 | Social post lifecycle |

**Uncovered:**
- Empty-state: `generate_weekly_report` for artist with zero activity — should not error, should
  produce a "getting started" message rather than a blank/confused report
- LinkedIn platform (if added in gap closure)
- Report email delivery (if added in gap closure)

---

## Gaps ranked for S8 closure

1. **LinkedIn platform** — add to `_PLATFORM_LIMITS` (3000 char) and `_PLATFORM_STYLE`. Minor,
   but the B2B music industry angle makes it genuinely useful for artist professional brand.

2. **Report email delivery** — `_email_weekly_report()` using pitch_service's `send_email()`
   infrastructure. Wire into `generate_weekly_report()`. HTML inline template, plain-text fallback.
   Mock at Gmail boundary in tests.

3. **Empty-state handling test** — verify that an artist with zero activity across all tables
   produces a report with `momentum_score` set, `summary` with all-zero counts, and no exception.
   The aggregator already handles this gracefully (`try/except` + zero defaults); a test confirms it.

---

## Files audited

- `social_service.py` (full, 1093 lines)
- `main.py` (Riley registration L131, greetings L374-376)
- `skills/maestro-social-manager/SKILL.md` (exists)
- `tests/test_social_service.py` (8 tests)
- `tests/test_reports.py` (7 tests)
- `tests/test_r26_buffer_live_client.py` (9 tests)
- `tests/test_r27_scheduler_dry_run.py` (6 tests)
- `tests/test_r28_configurable_report_schedule.py` (5 tests)
- `tests/test_f01_per_artist_timezone.py` (7 tests)
- `tests/integration/test_weekly_report.py` (1 test)
- `tests/integration/test_social_lifecycle.py` (1 test)
