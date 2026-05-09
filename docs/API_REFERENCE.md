# PLMKR API Reference

Base URL: `https://YOUR-RAILWAY-URL` (replace with your Railway deployment URL)

All write endpoints accept and return `application/json`. Timestamps are ISO 8601 UTC.

---

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check — returns `{"status": "ok"}` |

---

## Phase 1 — Gmail OAuth

| Method | Path | Query Params | Description |
|--------|------|--------------|-------------|
| GET | `/api/gmail/auth` | `artist_id` | Redirect to Google OAuth consent screen |
| GET | `/api/gmail/callback` | `code`, `state` | OAuth callback — exchanges code for tokens |
| GET | `/api/gmail/status` | `artist_id` | Check whether Gmail is connected |
| POST | `/api/gmail/send` | — | Send an email from the artist's Gmail account |

### POST /api/gmail/send
```json
{
  "artist_id": "string",
  "to": "recipient@example.com",
  "subject": "Email subject",
  "body": "Plain text body"
}
```
Returns: `{"message_id": "...", "thread_id": "..."}`

---

## Phase 1 — Curators

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/curators` | List curators (query: `genre`, `tier`) |
| GET | `/api/curators/{id}` | Get single curator |
| POST | `/api/curators` | Create curator (returns 201) |
| PATCH | `/api/curators/{id}` | Update curator fields |
| POST | `/api/curators/seed` | Seed all curators from `data/curators_seed.json` |

### POST /api/curators
```json
{
  "name": "Jordan Lee",
  "outlet": "Indie Discovery Playlist",
  "genres": ["indie", "pop"],
  "tier": "A|B|C",
  "contact_email": "jordan@example.com",
  "notes": "optional"
}
```

---

## Phase 1 — Pitch Lifecycle

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/pitches` | List pitches (query: `artist_id`, `status`) |
| GET | `/api/pitches/{id}` | Get pitch + interactions |
| PATCH | `/api/pitches/{id}` | Update pitch fields |
| POST | `/api/pitches/generate` | Generate pitch email via Claude (dry run) |
| POST | `/api/pitches/batch` | Generate + send pitches to multiple curators |
| POST | `/api/inbox/scan` | Scan Gmail inbox for curator replies |
| POST | `/api/pitches/followups/queue` | Queue follow-up emails for unanswered pitches |

### POST /api/pitches/generate
```json
{ "artist_id": "string", "curator_id": "string" }
```
Returns: `{"subject": "...", "body": "..."}`

### POST /api/pitches/batch
```json
{
  "artist_id": "string",
  "curator_ids": ["uuid1", "uuid2"]
}
```
Returns: `{"sent": 2, "failed": 0, "errors": [], "pitch_ids": ["uuid1", "uuid2"]}`

### POST /api/inbox/scan
Query param: `artist_id`

Returns:
```json
{
  "scanned": 10,
  "matched": 2,
  "classified": [
    { "pitch_id": "uuid", "from": "curator@example.com", "sentiment": "positive", "summary": "..." }
  ]
}
```

**Pitch statuses:** `draft` → `sent` → `replied` | `passed` | `failed`

---

## Phase 2 — PR Contacts & Outreach

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/pr-contacts` | List PR contacts (query: `tier`, `outlet_type`) |
| GET | `/api/pr-contacts/{id}` | Get single PR contact |
| POST | `/api/pr-contacts` | Create PR contact (returns 201) |
| PATCH | `/api/pr-contacts/{id}` | Update PR contact |
| POST | `/api/pr-contacts/seed` | Seed from `data/pr_contacts_seed.json` |
| GET | `/api/pr-outreach` | List outreach records (query: `artist_id`, `status`) |
| GET | `/api/pr-outreach/{id}` | Get outreach + interactions |
| PATCH | `/api/pr-outreach/{id}` | Update outreach fields |
| POST | `/api/pr-outreach/generate` | Generate PR email via Claude (dry run) |
| POST | `/api/pr-outreach/batch` | Generate + send PR emails to multiple contacts |
| POST | `/api/pr-outreach/scan` | Scan Gmail inbox for PR replies |
| POST | `/api/pr-outreach/followups/queue` | Queue follow-up emails |

### POST /api/pr-contacts
```json
{
  "name": "Alex Rivera",
  "outlet_type": "blog|magazine|podcast|newsletter",
  "outlet_name": "Indie Pulse Blog",
  "genres": ["indie"],
  "tier": "A|B|C",
  "contact_email": "alex@indiepulse.example.com",
  "beat": "emerging artists"
}
```

### POST /api/pr-outreach/batch
```json
{
  "artist_id": "string",
  "contact_ids": ["uuid1", "uuid2"],
  "release_context": { "release_name": "New EP", "release_date": "2026-06-01" }
}
```
Returns: `{"sent": 2, "failed": 0, "errors": [], "outreach_ids": ["uuid1", "uuid2"]}`

**Outreach statuses:** `draft` → `sent` → `replied` | `featured` | `passed` | `failed`

---

## Phase 2 — Booking Contacts & Inquiries

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/booking-contacts` | List booking contacts (query: `tier`, `venue_type`) |
| GET | `/api/booking-contacts/{id}` | Get single booking contact |
| POST | `/api/booking-contacts` | Create booking contact (returns 201) |
| PATCH | `/api/booking-contacts/{id}` | Update booking contact |
| POST | `/api/booking-contacts/seed` | Seed from `data/booking_contacts_seed.json` |
| GET | `/api/booking-inquiries` | List inquiries (query: `artist_id`, `status`) |
| GET | `/api/booking-inquiries/{id}` | Get inquiry + interactions |
| PATCH | `/api/booking-inquiries/{id}` | Update inquiry fields |
| POST | `/api/booking-inquiries/generate` | Generate booking email via Claude (dry run) |
| POST | `/api/booking-inquiries/batch` | Generate + send booking emails |
| POST | `/api/booking-inquiries/scan` | Scan Gmail for booking replies |
| POST | `/api/booking-inquiries/followups/queue` | Queue follow-up emails |
| POST | `/api/inbox/scan-all` | Unified scan: pitches + PR + booking in one call |

### POST /api/booking-contacts
```json
{
  "name": "Sam Torres",
  "venue_name": "The Local Spot",
  "venue_type": "club|festival|theater|arena|bar",
  "city": "Brooklyn",
  "capacity": 500,
  "genres": ["indie"],
  "tier": "A|B|C",
  "contact_email": "sam@venue.example.com"
}
```

### POST /api/booking-inquiries/batch
```json
{
  "artist_id": "string",
  "contact_ids": ["uuid1", "uuid2"],
  "show_context": { "preferred_dates": "June 2026", "set_length_minutes": 45 }
}
```
Returns: `{"sent": 2, "failed": 0, "errors": [], "inquiry_ids": ["uuid1", "uuid2"]}`

**Inquiry statuses:** `draft` → `sent` → `replied` | `booked` | `passed` | `failed`

### POST /api/inbox/scan-all
Query param: `artist_id`

Returns:
```json
{
  "artist_id": "string",
  "pitch": { "scanned": 10, "matched": 1, "classified": [...] },
  "pr": { "scanned": 10, "matched": 0, "classified": [] },
  "booking": { "scanned": 10, "matched": 1, "classified": [...] },
  "total_matched": 2
}
```

---

## Phase 3 — Social Posts

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/social/posts` | List posts (query: `artist_id`, `platform`, `status`) |
| GET | `/api/social/posts/{id}` | Get single post |
| POST | `/api/social/posts` | Create post manually (returns 201) |
| PATCH | `/api/social/posts/{id}` | Update post (status, posted_at, post_url) |
| DELETE | `/api/social/posts/{id}` | Delete post (returns 204) |
| POST | `/api/social/posts/generate` | Generate post via Claude (dry run) |
| POST | `/api/social/posts/batch` | Generate + schedule posts for multiple platforms |

### POST /api/social/posts/generate
```json
{
  "artist_id": "string",
  "platform": "twitter|instagram|tiktok|facebook",
  "context": { "release": "new single" },
  "tone": "authentic|hype|reflective|promotional"
}
```
Returns: `{"content": "...", "hashtags": ["..."], "best_time": "18:00", "artist_id": "...", "platform": "..."}`

**Platform character limits:** Twitter: 280 · Instagram/TikTok: 2200 · Facebook: 1000

### POST /api/social/posts/batch
```json
{
  "artist_id": "string",
  "platforms": ["twitter", "instagram"],
  "context": { "release": "new EP" },
  "tone": "authentic",
  "posts_per_platform": 3,
  "schedule_buffer": false,
  "buffer_profile_ids": [],
  "start_date": "2026-05-15"
}
```
Returns: `{"generated": 6, "scheduled_via_buffer": 0, "errors": [], "post_ids": [...]}`

**Post statuses:** `draft` → `scheduled` → `posted`

---

## Phase 3 — Buffer OAuth

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/buffer/auth` | Redirect to Buffer OAuth consent screen |
| GET | `/api/buffer/callback` | Buffer OAuth callback (exchange code for tokens) |
| GET | `/api/buffer/status` | Check whether Buffer is connected |

---

## Phase 3 — Weekly Reports

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/reports/weekly` | List reports (query: `artist_id`, `limit`) |
| GET | `/api/reports/weekly/{id}` | Get single report |
| POST | `/api/reports/weekly/generate` | Generate weekly report via Claude Sonnet |

### POST /api/reports/weekly/generate
```json
{
  "artist_id": "string",
  "week_start": "2026-05-04T00:00:00",
  "week_end": "2026-05-10T23:59:59"
}
```
If `week_start`/`week_end` are omitted, defaults to the previous Mon–Sun.

Returns:
```json
{
  "id": "uuid",
  "artist_id": "string",
  "week_start": "2026-05-04T00:00:00",
  "week_end": "2026-05-10T23:59:59",
  "headline": "Strong week across all channels",
  "highlights": ["3 pitches sent", "1 PR reply", "4 social posts"],
  "insights": "...",
  "recommendations": "...",
  "momentum_score": 7,
  "summary": {
    "pitches":     { "sent": 2, "replied": 1, "reply_rate": 0.33 },
    "pr_outreach": { "sent": 2, "replied": 0, "featured": 0 },
    "booking":     { "sent": 2, "replied": 1, "booked": 0 },
    "social":      { "posted": 0, "scheduled": 4 }
  },
  "generated_at": "2026-05-10T18:00:00+00:00"
}
```

`momentum_score`: 1 (stalled) → 5 (steady) → 10 (breakthrough week)

---

---

## Phase 4 — Release Campaign Orchestration

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/releases` | Create a release |
| GET | `/api/releases` | List releases (`?artist_id=`) |
| GET | `/api/releases/{id}` | Get one release |
| PATCH | `/api/releases/{id}` | Update release fields |
| POST | `/api/releases/{id}/generate-campaign` | Generate campaign actions from release date |
| GET | `/api/releases/{id}/campaign` | List campaign actions with status |
| POST | `/api/releases/{id}/campaign/execute-due` | Execute all actions due now |

### POST /api/releases
```json
{
  "artist_id":    "string",
  "title":        "Album Title",
  "release_date": "2026-06-01",
  "genre":        "indie",
  "mood":         "melancholic"
}
```

### POST /api/releases/{id}/generate-campaign — Response
```json
{
  "release_id":       "uuid",
  "actions_created":  21,
  "status":           "active"
}
```

### GET /api/releases/{id}/campaign — Response
```json
{
  "release_id": "uuid",
  "actions": [
    {
      "id":            "uuid",
      "action_type":   "pitch_curators",
      "scheduled_for": "2026-05-18T00:00:00+00:00",
      "status":        "pending",
      "payload":       { "artist_id": "...", "tier_filter": ["A","B"] }
    }
  ],
  "counts": { "total": 21, "pending": 21, "done": 0, "failed": 0 }
}
```

**Action types:**
- `pitch_curators` — sends curator pitch batch (Phase 1)
- `pr_outreach` — sends PR outreach batch (Phase 2)
- `booking_inquiry` — sends venue booking batch (Phase 2)
- `social_post_schedule` — generates social posts (Phase 3)

**Campaign schedule relative to release_date:**
- `-21d` booking_inquiry (venue advance booking)
- `-14d` pitch_curators wave 1
- `-10d` pr_outreach wave 1
- `-7d` pitch_curators wave 2 + social ramp begins
- `-3d` pr_outreach wave 2
- `0d` pitch_curators release day + social release day post
- `+1d` through `+7d` social posts daily

---

## Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/stats` | Activity stats for an artist (`?artist_id=`, `?since=ISO_DATE`) |
| GET | `/api/admin/health/deep` | DB, scheduler, OAuth token counts, disk usage |

### GET /api/admin/stats — Response
```json
{
  "artist_id":              "string",
  "since":                  "1970-01-01T00:00:00",
  "pitches_sent":           12,
  "pitches_replied":        3,
  "reply_rate":             0.25,
  "pr_sent":                8,
  "pr_replied":             2,
  "pr_reply_rate":          0.25,
  "booking_sent":           5,
  "booking_replied":        1,
  "booking_reply_rate":     0.20,
  "social_posts_published": 14,
  "last_report_date":       "2026-05-10T18:00:00"
}
```

### GET /api/admin/health/deep — Response
```json
{
  "timestamp":                     "2026-05-09T21:00:00+00:00",
  "db_connected":                  true,
  "scheduler_running":             true,
  "gmail_token_valid_for_artists": 3,
  "buffer_token_valid_for_artists": 1,
  "disk_usage_pct":                34.2
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Invalid request body or missing required field |
| 404 | Resource not found |
| 503 | Gmail or Buffer OAuth not configured (env vars missing) |
| 500 | Generation failed (Claude error) or internal error |

All errors return a structured envelope:
```json
{ "error": "ExceptionType", "detail": "human readable message", "request_id": "uuid" }
```

Gmail-specific errors returned in batch `errors[]` array:
- `GmailNotConnected` — artist has not completed Gmail OAuth
- `GmailAuthExpired` — access token expired and refresh failed

---

## Interactive Docs

FastAPI auto-generates Swagger UI at `/docs` and ReDoc at `/redoc`.

## For Frontend Developers

OpenAPI spec is exported to `docs/openapi.json`. Run `python3 scripts/export_openapi.py` to regenerate after adding endpoints.
