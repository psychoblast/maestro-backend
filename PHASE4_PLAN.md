# Phase 4 — Release Campaign Orchestration

**Decided scope:** Release Campaign Orchestration  
**Decision date:** 2026-05-09 (autonomous session)  
**Reason:** Cohesive, no new API keys required, directly monetisable — wraps Phases 1-3 into  
a single "launch a release" workflow that gives artists one button to coordinate all outreach.

---

## What It Does

An artist creates a **Release** (title, release date, genre, mood). The system auto-generates  
a **campaign** of time-stamped actions drawn from Phases 1–3:

| Action type          | When (relative to release_date) | Service called          |
|----------------------|----------------------------------|-------------------------|
| pitch_curators       | -14d, -7d, day-of               | pitch_service.send_pitch_emails() |
| pr_outreach          | -10d, -3d                        | pr_service.send_pr_emails()        |
| booking_inquiry      | -21d                             | booking_service.send_booking_emails() |
| social_post_schedule | -7d through +7d daily            | social_service (batch generate)   |

The **execute-due** endpoint fires any actions whose `scheduled_for` has passed and  
whose status is `pending`. A scheduler hook (every 1h) calls this automatically  
when `SCHEDULER_ENABLED=true`.

---

## New Agent

**Sage** — Release Strategist  
Sage guides artists through creating releases, understanding campaign timelines, and  
reading campaign status. Wired into `main.py` as agent ID `release-strategist`.

---

## DB Schema

```sql
CREATE TABLE IF NOT EXISTS releases (
    id           TEXT PRIMARY KEY,
    artist_id    TEXT NOT NULL,
    title        TEXT NOT NULL,
    release_date TEXT NOT NULL,       -- ISO date YYYY-MM-DD
    genre        TEXT DEFAULT '',
    mood         TEXT DEFAULT '',
    status       TEXT DEFAULT 'draft', -- draft | active | complete
    created_at   TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

CREATE TABLE IF NOT EXISTS campaign_actions (
    id             TEXT PRIMARY KEY,
    release_id     TEXT NOT NULL,
    action_type    TEXT NOT NULL,     -- pitch_curators | pr_outreach | booking_inquiry | social_post_schedule
    scheduled_for  TEXT NOT NULL,     -- ISO datetime
    status         TEXT DEFAULT 'pending', -- pending | running | done | failed
    payload_json   TEXT DEFAULT '{}',
    executed_at    TEXT,
    result_json    TEXT DEFAULT '{}',
    created_at     TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);
```

---

## Endpoints

```
POST /api/releases                        Create a release
GET  /api/releases?artist_id=...          List releases for artist
GET  /api/releases/{id}                   Get one release
PATCH /api/releases/{id}                  Update release (title, date, status)
POST /api/releases/{id}/generate-campaign Generate campaign_actions from schedule
GET  /api/releases/{id}/campaign          List campaign actions with status
POST /api/releases/{id}/campaign/execute-due  Run all actions due now
```

---

## Campaign Action Generation Logic

Given `release_date`, generate actions at these offsets (skipping past dates):

| Action              | Offsets from release_date |
|---------------------|---------------------------|
| booking_inquiry     | -21d                      |
| pitch_curators (1)  | -14d                      |
| pr_outreach (1)     | -10d                      |
| pitch_curators (2)  | -7d                        |
| pr_outreach (2)     | -3d                        |
| social_post_schedule| -7d, -6d, -5d, -4d, -3d, -2d, -1d, 0d (release day), +1d … +7d |
| pitch_curators (3)  | 0d (release day)           |

Payload includes artist_id, release_id, tier hints (A+B curators for curator pitches,  
top-tier PR contacts for PR outreach, top-tier booking contacts for booking).

---

## No New External APIs

All execution delegates to existing Phase 1/2/3 service functions. Sage uses the  
existing Anthropic client (same model routing as other agents). No new OAuth flows.
