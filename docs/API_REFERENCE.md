> **Generated 2026-05-14 from main `a1afbe0`. Source of truth: `app.openapi()` at runtime.**
> This file is regenerated automatically. Do not edit manually.

# PLMKR — Playmaker API Reference

**Version:** 3.0.0 | **Base URL:** Railway deploy root

All authenticated endpoints require the header `X-API-Key: <your-key>`.

---

## Endpoint Index

Sorted alphabetically by path.

| Method | Path | Auth Required | Summary |
|--------|------|---------------|---------|
| GET | `/api/admin/diagnostics` | Yes (X-API-Key) | Admin Diagnostics |
| GET | `/api/admin/diagnostics/anthropic-stats` | Yes (X-API-Key) | Admin Anthropic Stats |
| GET | `/api/admin/diagnostics/gmail-stats` | Yes (X-API-Key) | Admin Gmail Stats |
| GET | `/api/admin/diagnostics/performance` | Yes (X-API-Key) | Admin Diagnostics Performance |
| GET | `/api/admin/health/deep` | No | Admin Health Deep |
| GET | `/api/admin/stats` | Yes (X-API-Key) | Admin Stats |
| GET | `/api/agents` | Yes (X-API-Key) | List Agents |
| GET | `/api/artist` | Yes (X-API-Key) | Get Artist |
| GET | `/api/artist/lookup` | Yes (X-API-Key) | Lookup Artist |
| POST | `/api/artist/save` | Yes (X-API-Key) | Save Artist |
| POST | `/api/auth/send-otp` | Yes (X-API-Key) | Send Otp |
| POST | `/api/auth/verify-otp` | Yes (X-API-Key) | Verify Otp |
| GET | `/api/avatar/status` | Yes (X-API-Key) | Avatar Status |
| POST | `/api/avatar/talk` | Yes (X-API-Key) | Avatar Talk |
| POST | `/api/billing/create-checkout` | Yes (X-API-Key) | Create Checkout |
| GET | `/api/billing/history` | Yes (X-API-Key) | Get Billing History |
| POST | `/api/billing/upgrade` | Yes (X-API-Key) | Billing Upgrade |
| POST | `/api/billing/webhook` | Yes (X-API-Key) | Billing Webhook |
| GET | `/api/booking-contacts` | Yes (X-API-Key) | List Booking Contacts |
| POST | `/api/booking-contacts` | Yes (X-API-Key) | Create Booking Contact |
| GET | `/api/booking-contacts/{contact_id}` | Yes (X-API-Key) | Get Booking Contact |
| PATCH | `/api/booking-contacts/{contact_id}` | Yes (X-API-Key) | Patch Booking Contact |
| POST | `/api/booking-contacts/seed` | Yes (X-API-Key) | Seed Booking Contacts Endpoint |
| GET | `/api/booking-inquiries` | Yes (X-API-Key) | List Booking Inquiries |
| GET | `/api/booking-inquiries/{inquiry_id}` | Yes (X-API-Key) | Get Booking Inquiry |
| PATCH | `/api/booking-inquiries/{inquiry_id}` | Yes (X-API-Key) | Patch Booking Inquiry |
| POST | `/api/booking-inquiries/batch` | Yes (X-API-Key) | Send Booking Emails |
| POST | `/api/booking-inquiries/followups/queue` | Yes (X-API-Key) | Queue Booking Followups |
| POST | `/api/booking-inquiries/generate` | Yes (X-API-Key) | Api Generate Booking |
| POST | `/api/booking-inquiries/scan` | Yes (X-API-Key) | Api Scan Booking Inbox |
| GET | `/api/buffer/auth` | Yes (X-API-Key) | Buffer Auth |
| GET | `/api/buffer/callback` | Yes (X-API-Key) | Buffer Callback |
| GET | `/api/buffer/status` | Yes (X-API-Key) | Buffer Status |
| POST | `/api/chat_stream` | Yes (X-API-Key) | Chat Stream |
| GET | `/api/curators` | Yes (X-API-Key) | List Curators |
| POST | `/api/curators` | Yes (X-API-Key) | Create Curator |
| GET | `/api/curators/{curator_id}` | Yes (X-API-Key) | Get Curator |
| PATCH | `/api/curators/{curator_id}` | Yes (X-API-Key) | Patch Curator |
| POST | `/api/curators/seed` | Yes (X-API-Key) | Seed Curators Endpoint |
| GET | `/api/gmail/auth` | Yes (X-API-Key) | Gmail Auth |
| GET | `/api/gmail/callback` | Yes (X-API-Key) | Gmail Callback |
| POST | `/api/gmail/send` | Yes (X-API-Key) | Api Send Email |
| GET | `/api/gmail/status` | Yes (X-API-Key) | Gmail Status |
| POST | `/api/greet` | Yes (X-API-Key) | Greet |
| POST | `/api/handoff` | Yes (X-API-Key) | Handoff |
| GET | `/api/health` | Yes (X-API-Key) | Api Health |
| GET | `/api/history` | Yes (X-API-Key) | Get History |
| POST | `/api/inbox/scan` | Yes (X-API-Key) | Api Scan Inbox |
| POST | `/api/inbox/scan-all` | Yes (X-API-Key) | Api Scan All Inbox |
| GET | `/api/notifications/{artist_id}` | Yes (X-API-Key) | Get Notifications |
| POST | `/api/notifications/register` | Yes (X-API-Key) | Register Push Token |
| POST | `/api/notifications/send` | Yes (X-API-Key) | Send Notification |
| GET | `/api/pitches` | Yes (X-API-Key) | List Pitches |
| GET | `/api/pitches/{pitch_id}` | Yes (X-API-Key) | Get Pitch |
| PATCH | `/api/pitches/{pitch_id}` | Yes (X-API-Key) | Patch Pitch |
| POST | `/api/pitches/batch` | Yes (X-API-Key) | Send Pitch Emails |
| POST | `/api/pitches/followups/queue` | Yes (X-API-Key) | Queue Followups |
| POST | `/api/pitches/generate` | Yes (X-API-Key) | Api Generate Pitch |
| GET | `/api/pr-contacts` | Yes (X-API-Key) | List Pr Contacts |
| POST | `/api/pr-contacts` | Yes (X-API-Key) | Create Pr Contact |
| GET | `/api/pr-contacts/{contact_id}` | Yes (X-API-Key) | Get Pr Contact |
| PATCH | `/api/pr-contacts/{contact_id}` | Yes (X-API-Key) | Patch Pr Contact |
| POST | `/api/pr-contacts/seed` | Yes (X-API-Key) | Seed Pr Contacts Endpoint |
| GET | `/api/pr-outreach` | Yes (X-API-Key) | List Pr Outreach |
| GET | `/api/pr-outreach/{outreach_id}` | Yes (X-API-Key) | Get Pr Outreach |
| PATCH | `/api/pr-outreach/{outreach_id}` | Yes (X-API-Key) | Patch Pr Outreach |
| POST | `/api/pr-outreach/batch` | Yes (X-API-Key) | Send Pr Emails |
| POST | `/api/pr-outreach/followups/queue` | Yes (X-API-Key) | Queue Pr Followups |
| POST | `/api/pr-outreach/generate` | Yes (X-API-Key) | Api Generate Pr |
| POST | `/api/pr-outreach/scan` | Yes (X-API-Key) | Api Scan Pr Inbox |
| GET | `/api/releases` | Yes (X-API-Key) | List Releases |
| POST | `/api/releases` | Yes (X-API-Key) | Create Release |
| GET | `/api/releases/{release_id}` | Yes (X-API-Key) | Get Release |
| PATCH | `/api/releases/{release_id}` | Yes (X-API-Key) | Patch Release |
| GET | `/api/releases/{release_id}/campaign` | Yes (X-API-Key) | Get Campaign |
| POST | `/api/releases/{release_id}/campaign/execute-due` | Yes (X-API-Key) | Execute Due Actions |
| POST | `/api/releases/{release_id}/generate-campaign` | Yes (X-API-Key) | Generate Campaign |
| GET | `/api/reports/weekly` | Yes (X-API-Key) | List Weekly Reports |
| GET | `/api/reports/weekly/{report_id}` | Yes (X-API-Key) | Get Weekly Report |
| POST | `/api/reports/weekly/generate` | Yes (X-API-Key) | Api Generate Weekly Report |
| GET | `/api/social/posts` | Yes (X-API-Key) | List Posts |
| POST | `/api/social/posts` | Yes (X-API-Key) | Create Post |
| GET | `/api/social/posts/{post_id}` | Yes (X-API-Key) | Get Post |
| PATCH | `/api/social/posts/{post_id}` | Yes (X-API-Key) | Patch Post |
| DELETE | `/api/social/posts/{post_id}` | Yes (X-API-Key) | Delete Post |
| POST | `/api/social/posts/batch` | Yes (X-API-Key) | Schedule Posts |
| POST | `/api/social/posts/generate` | Yes (X-API-Key) | Api Generate Post |
| POST | `/api/transcribe` | Yes (X-API-Key) | Transcribe |
| GET | `/api/tts` | Yes (X-API-Key) | Tts Endpoint |
| POST | `/api/tts/cancel` | Yes (X-API-Key) | Tts Cancel |
| GET | `/api/tts/status` | Yes (X-API-Key) | Tts Status |
| POST | `/api/tts/synth` | Yes (X-API-Key) | Tts Synth |
| GET | `/health` | No | Liveness check |

---

## Endpoint Groups

---

### health — Liveness check

#### GET /health

- **Summary:** Liveness check — returns 200 OK when the service is running
- **Auth:** No
- **Query params:** none
- **Response:** 200 `{}` — service is up

---

### gmail — Gmail OAuth 2.0 connect/disconnect

#### GET /api/gmail/auth

- **Summary:** Gmail Auth — redirect artist to Google OAuth consent screen
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — redirect or OAuth URL

#### GET /api/gmail/callback

- **Summary:** Gmail Callback — exchange OAuth code for tokens and persist in artist profile
- **Auth:** Yes (X-API-Key)
- **Query params:** `code` (string, required), `state` (string, required)
- **Response:** 200 — tokens stored confirmation

#### GET /api/gmail/status

- **Summary:** Gmail Status — return whether artist has active Gmail tokens
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — `{ connected: bool }`

#### POST /api/gmail/send

- **Summary:** Api Send Email — send a one-off email via artist's connected Gmail account
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `to` (string, required)
  - `subject` (string, required)
  - `body` (string, required)
- **Response:** 200 — send confirmation

---

### curators — Curator contact management

#### GET /api/curators

- **Summary:** List Curators — return all curators, optionally filtered
- **Auth:** Yes (X-API-Key)
- **Query params:** `genre` (string, optional), `tier` (string, optional)
- **Response:** 200 — array of curator objects

#### POST /api/curators

- **Summary:** Create Curator — add a new curator to the database
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `name` (string, required)
  - `contact_email` (string, required)
  - `outlet` (string, optional, default `""`)
  - `genres` (array of string, optional, default `[]`)
  - `tier` (string, optional, default `"C"`)
  - `notes` (string, optional)
  - `response_rate` (number, optional, default `0.0`)
- **Response:** 201 — created curator object

#### GET /api/curators/{curator_id}

- **Summary:** Get Curator — fetch a single curator by ID
- **Auth:** Yes (X-API-Key)
- **Path params:** `curator_id` (string, required)
- **Response:** 200 — curator object

#### PATCH /api/curators/{curator_id}

- **Summary:** Patch Curator — update one or more fields on a curator
- **Auth:** Yes (X-API-Key)
- **Path params:** `curator_id` (string, required)
- **Request body:** any subset of `name`, `outlet`, `genres`, `tier`, `contact_email`, `notes`, `response_rate` (all optional/nullable)
- **Response:** 200 — updated curator object

#### POST /api/curators/seed

- **Summary:** Seed Curators Endpoint — load curators from `data/curators_seed.json` (idempotent)
- **Auth:** Yes (X-API-Key)
- **Request body:** none
- **Response:** 200 — seed result summary

---

### pitches — Curator pitch lifecycle — generate, send, scan, follow-up

#### GET /api/pitches

- **Summary:** List Pitches — return all pitches for an artist
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — array of pitch objects

#### GET /api/pitches/{pitch_id}

- **Summary:** Get Pitch — fetch a single pitch by ID
- **Auth:** Yes (X-API-Key)
- **Path params:** `pitch_id` (string, required)
- **Response:** 200 — pitch object

#### PATCH /api/pitches/{pitch_id}

- **Summary:** Patch Pitch — update pitch status
- **Auth:** Yes (X-API-Key)
- **Path params:** `pitch_id` (string, required)
- **Request body:** `status` (string, optional/nullable)
- **Response:** 200 — updated pitch object

#### POST /api/pitches/generate

- **Summary:** Api Generate Pitch — generate (but do not send) a pitch draft for one curator
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `curator_id` (string, required)
  - `track_metadata` (object, optional, default `{}`)
- **Response:** 200 — `{ subject, body, curator_id }`

#### POST /api/pitches/batch

- **Summary:** Send Pitch Emails — generate and send pitches to multiple curators in one call
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `curator_ids` (array of string, required)
  - `track_metadata` (object, optional, default `{}`)
- **Response:** 200 — `{ sent: N, failed: M, errors: [...], pitch_ids: [...] }`

#### POST /api/inbox/scan

- **Summary:** Api Scan Inbox — manually trigger inbox scan for one artist (curator replies)
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — scan results with reply counts

#### POST /api/pitches/followups/queue

- **Summary:** Queue Followups — find sent pitches at follow-up threshold and send follow-up emails
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, optional, default `""` = all artists)
- **Response:** 200 — `{ queued: N, sent: M, failed: K, details: [...] }`

---

### pr — PR contact management and outreach lifecycle

#### GET /api/pr-contacts

- **Summary:** List Pr Contacts — return all PR contacts, optionally filtered
- **Auth:** Yes (X-API-Key)
- **Query params:** `genre` (string, optional), `tier` (string, optional), `outlet_type` (string, optional)
- **Response:** 200 — array of PR contact objects

#### POST /api/pr-contacts

- **Summary:** Create Pr Contact — add a new PR contact
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `name` (string, required)
  - `contact_email` (string, required)
  - `outlet_type` (string, optional, default `"blog"`)
  - `outlet_name` (string, optional)
  - `genres` (array of string, optional)
  - `tier` (string, optional, default `"C"`)
  - `beat` (string, optional)
  - `notes` (string, optional)
  - `response_rate` (number, optional, default `0.0`)
- **Response:** 201 — created PR contact object

#### GET /api/pr-contacts/{contact_id}

- **Summary:** Get Pr Contact — fetch a single PR contact by ID
- **Auth:** Yes (X-API-Key)
- **Path params:** `contact_id` (string, required)
- **Response:** 200 — PR contact object

#### PATCH /api/pr-contacts/{contact_id}

- **Summary:** Patch Pr Contact — update one or more fields on a PR contact
- **Auth:** Yes (X-API-Key)
- **Path params:** `contact_id` (string, required)
- **Request body:** any subset of `name`, `outlet_type`, `outlet_name`, `genres`, `tier`, `contact_email`, `beat`, `notes`, `response_rate` (all optional/nullable)
- **Response:** 200 — updated PR contact object

#### POST /api/pr-contacts/seed

- **Summary:** Seed Pr Contacts Endpoint — load PR contacts from seed file (idempotent)
- **Auth:** Yes (X-API-Key)
- **Request body:** none
- **Response:** 200 — seed result summary

#### GET /api/pr-outreach

- **Summary:** List Pr Outreach — return all PR outreach records for an artist
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — array of PR outreach objects

#### GET /api/pr-outreach/{outreach_id}

- **Summary:** Get Pr Outreach — fetch a single PR outreach record by ID
- **Auth:** Yes (X-API-Key)
- **Path params:** `outreach_id` (string, required)
- **Response:** 200 — PR outreach object

#### PATCH /api/pr-outreach/{outreach_id}

- **Summary:** Patch Pr Outreach — update status or feature URL on a PR outreach record
- **Auth:** Yes (X-API-Key)
- **Path params:** `outreach_id` (string, required)
- **Request body:** `status` (string, optional/nullable), `feature_url` (string, optional/nullable)
- **Response:** 200 — updated PR outreach object

#### POST /api/pr-outreach/generate

- **Summary:** Api Generate Pr — generate (but do not send) a PR email draft for one contact
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `contact_id` (string, required)
  - `release_context` (object, optional, default `{}`)
- **Response:** 200 — `{ subject, body, contact_id }`

#### POST /api/pr-outreach/batch

- **Summary:** Send Pr Emails — generate and send PR emails to multiple contacts in one call
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `contact_ids` (array of string, required)
  - `release_context` (object, optional, default `{}`)
- **Response:** 200 — `{ sent: N, failed: M, errors: [...], outreach_ids: [...] }`

#### POST /api/pr-outreach/scan

- **Summary:** Api Scan Pr Inbox — manually trigger PR inbox scan for one artist
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — scan results with reply counts

#### POST /api/pr-outreach/followups/queue

- **Summary:** Queue Pr Followups — find sent PR outreach on day 3 or 7 and send follow-ups
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, optional, default `""` = all artists)
- **Response:** 200 — `{ queued: N, sent: M, failed: K, details: [...] }`

---

### booking — Booking contact management and inquiry lifecycle

#### GET /api/booking-contacts

- **Summary:** List Booking Contacts — return all booking contacts, optionally filtered
- **Auth:** Yes (X-API-Key)
- **Query params:** `genre` (string, optional), `tier` (string, optional), `type` (string, optional), `city` (string, optional)
- **Response:** 200 — array of booking contact objects

#### POST /api/booking-contacts

- **Summary:** Create Booking Contact — add a new venue/festival booking contact
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `name` (string, required)
  - `contact_email` (string, required)
  - `venue_or_festival` (string, optional)
  - `type` (string, optional, default `"venue"`)
  - `city` (string, optional)
  - `country` (string, optional)
  - `capacity` (integer, optional, default `0`)
  - `genres` (array of string, optional)
  - `tier` (string, optional, default `"C"`)
  - `notes` (string, optional)
  - `response_rate` (number, optional, default `0.0`)
- **Response:** 201 — created booking contact object

#### GET /api/booking-contacts/{contact_id}

- **Summary:** Get Booking Contact — fetch a single booking contact by ID
- **Auth:** Yes (X-API-Key)
- **Path params:** `contact_id` (string, required)
- **Response:** 200 — booking contact object

#### PATCH /api/booking-contacts/{contact_id}

- **Summary:** Patch Booking Contact — update one or more fields on a booking contact
- **Auth:** Yes (X-API-Key)
- **Path params:** `contact_id` (string, required)
- **Request body:** any subset of `name`, `venue_or_festival`, `type`, `city`, `country`, `capacity`, `genres`, `tier`, `contact_email`, `notes`, `response_rate` (all optional/nullable)
- **Response:** 200 — updated booking contact object

#### POST /api/booking-contacts/seed

- **Summary:** Seed Booking Contacts Endpoint — load booking contacts from seed file (idempotent)
- **Auth:** Yes (X-API-Key)
- **Request body:** none
- **Response:** 200 — seed result summary

#### GET /api/booking-inquiries

- **Summary:** List Booking Inquiries — return all booking inquiry records for an artist
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — array of booking inquiry objects

#### GET /api/booking-inquiries/{inquiry_id}

- **Summary:** Get Booking Inquiry — fetch a single booking inquiry by ID
- **Auth:** Yes (X-API-Key)
- **Path params:** `inquiry_id` (string, required)
- **Response:** 200 — booking inquiry object

#### PATCH /api/booking-inquiries/{inquiry_id}

- **Summary:** Patch Booking Inquiry — update status, booking date, or fee on an inquiry
- **Auth:** Yes (X-API-Key)
- **Path params:** `inquiry_id` (string, required)
- **Request body:** `status` (string, optional/nullable), `booking_date` (string, optional/nullable), `booking_fee` (number, optional/nullable)
- **Response:** 200 — updated booking inquiry object

#### POST /api/booking-inquiries/generate

- **Summary:** Api Generate Booking — generate (but do not send) a booking inquiry email draft
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `contact_id` (string, required)
  - `show_context` (object, optional, default `{}`)
- **Response:** 200 — `{ subject, body, contact_id }`

#### POST /api/booking-inquiries/batch

- **Summary:** Send Booking Emails — generate and send booking emails to multiple contacts in one call
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `contact_ids` (array of string, required)
  - `show_context` (object, optional, default `{}`)
- **Response:** 200 — `{ sent: N, failed: M, errors: [...], inquiry_ids: [...] }`

#### POST /api/booking-inquiries/scan

- **Summary:** Api Scan Booking Inbox — manually trigger booking inbox scan for one artist
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — scan results with reply counts

#### POST /api/inbox/scan-all

- **Summary:** Api Scan All Inbox — single Gmail auth round-trip runs pitch + PR + booking reply detection
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — combined scan results for all three channels

#### POST /api/booking-inquiries/followups/queue

- **Summary:** Queue Booking Followups — find sent booking inquiries on day 5 or 14 and send follow-ups
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, optional, default `""` = all artists)
- **Response:** 200 — `{ queued: N, sent: M, failed: K, details: [...] }`

---

### social — Social post generation, scheduling, and Buffer integration

#### GET /api/social/posts

- **Summary:** List Posts — return all social posts for an artist, optionally filtered
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required), `platform` (string, optional), `status` (string, optional)
- **Response:** 200 — array of social post objects

#### POST /api/social/posts

- **Summary:** Create Post — create a new social post record
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `platform` (string, required)
  - `content` (string, required)
  - `media_url` (string, optional, default `""`)
  - `scheduled_at` (string ISO datetime, optional/nullable)
  - `status` (string, optional, default `"draft"`)
- **Response:** 201 — created post object

#### GET /api/social/posts/{post_id}

- **Summary:** Get Post — fetch a single social post by ID
- **Auth:** Yes (X-API-Key)
- **Path params:** `post_id` (string, required)
- **Response:** 200 — social post object

#### PATCH /api/social/posts/{post_id}

- **Summary:** Patch Post — update content, status, schedule time, or engagement stats
- **Auth:** Yes (X-API-Key)
- **Path params:** `post_id` (string, required)
- **Request body:** any subset of `content`, `media_url`, `status`, `scheduled_at`, `posted_at`, `post_url`, `engagement_stats` (all optional/nullable)
- **Response:** 200 — updated social post object

#### DELETE /api/social/posts/{post_id}

- **Summary:** Delete Post — delete a social post record
- **Auth:** Yes (X-API-Key)
- **Path params:** `post_id` (string, required)
- **Response:** 204 — no content

#### POST /api/social/posts/generate

- **Summary:** Api Generate Post — generate a single social post draft with AI
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `platform` (string, required)
  - `context` (object, optional, default `{}`)
  - `tone` (string, optional, default `"authentic"`)
- **Response:** 200 — `{ platform, content, tone }`

#### POST /api/social/posts/batch

- **Summary:** Schedule Posts — generate N posts per platform and optionally push to Buffer
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `platforms` (array of string, required)
  - `context` (object, optional, default `{}`)
  - `tone` (string, optional, default `"authentic"`)
  - `posts_per_platform` (integer, optional, default `3`)
  - `schedule_buffer` (boolean, optional, default `false`)
  - `buffer_profile_ids` (array of string, optional, default `[]`)
  - `start_date` (string ISO date, optional/nullable)
- **Response:** 200 — `{ generated: N, scheduled_via_buffer: M, errors: [...], post_ids: [...] }`

---

### buffer — Buffer OAuth 2.0 connect/disconnect

#### GET /api/buffer/auth

- **Summary:** Buffer Auth — redirect artist to Buffer OAuth consent screen
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — redirect or OAuth URL

#### GET /api/buffer/callback

- **Summary:** Buffer Callback — handle Buffer OAuth callback, exchange code for access token and store it
- **Auth:** Yes (X-API-Key)
- **Query params:** `code` (string, required), `state` (string, required)
- **Response:** 200 — token stored confirmation

#### GET /api/buffer/status

- **Summary:** Buffer Status — check whether artist has an active Buffer token
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — `{ connected: bool }`

---

### reports — Weekly activity reports with AI-generated insights

#### GET /api/reports/weekly

- **Summary:** List Weekly Reports — return recent weekly reports for an artist
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required), `limit` (integer, optional, default `12`)
- **Response:** 200 — array of weekly report objects

#### GET /api/reports/weekly/{report_id}

- **Summary:** Get Weekly Report — fetch a single weekly report by ID
- **Auth:** Yes (X-API-Key)
- **Path params:** `report_id` (string, required)
- **Response:** 200 — weekly report object with AI narrative

#### POST /api/reports/weekly/generate

- **Summary:** Api Generate Weekly Report — generate a new weekly report with AI insights
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `week_start` (string ISO date, optional/nullable)
  - `week_end` (string ISO date, optional/nullable)
- **Response:** 200 — generated weekly report object

---

### releases — Release management and campaign orchestration

#### POST /api/releases

- **Summary:** Create Release — create a new release record
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `title` (string, required)
  - `release_date` (string ISO date, required)
  - `genre` (string, optional/nullable)
  - `mood` (string, optional/nullable)
- **Response:** 200 — created release object

#### GET /api/releases

- **Summary:** List Releases — list all releases for an artist
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — array of release objects

#### GET /api/releases/{release_id}

- **Summary:** Get Release — fetch a single release by ID
- **Auth:** Yes (X-API-Key)
- **Path params:** `release_id` (string, required)
- **Response:** 200 — release object

#### PATCH /api/releases/{release_id}

- **Summary:** Patch Release — update release fields
- **Auth:** Yes (X-API-Key)
- **Path params:** `release_id` (string, required)
- **Request body:** any subset of `title`, `release_date`, `genre`, `mood`, `status` (all optional/nullable)
- **Response:** 200 — updated release object

#### POST /api/releases/{release_id}/generate-campaign

- **Summary:** Generate Campaign — generate campaign_actions for a release (idempotent; clears pending actions and regenerates)
- **Auth:** Yes (X-API-Key)
- **Path params:** `release_id` (string, required)
- **Response:** 200 — array of generated campaign actions

#### GET /api/releases/{release_id}/campaign

- **Summary:** Get Campaign — list all campaign actions for a release
- **Auth:** Yes (X-API-Key)
- **Path params:** `release_id` (string, required)
- **Response:** 200 — array of campaign action objects

#### POST /api/releases/{release_id}/campaign/execute-due

- **Summary:** Execute Due Actions — execute all campaign actions for this release where `scheduled_for <= now`
- **Auth:** Yes (X-API-Key)
- **Path params:** `release_id` (string, required)
- **Response:** 200 — `{ executed: N, failed: M, results: [...] }`

---

### admin — Platform administration and diagnostics

#### GET /api/admin/stats

- **Summary:** Admin Stats — return activity stats for an artist
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required), `since` (string ISO datetime, optional — omit for all-time)
- **Response:** 200 — pitch/PR/booking/post counts and status breakdown

#### GET /api/admin/diagnostics/anthropic-stats

- **Summary:** Admin Anthropic Stats — per-model Anthropic call counters (total, success, retry, fail)
- **Auth:** Yes (X-API-Key)
- **Response:** 200 — model-keyed counters object

#### GET /api/admin/diagnostics/gmail-stats

- **Summary:** Admin Gmail Stats — per-artist Gmail call counters (total, success, retry, fail)
- **Auth:** Yes (X-API-Key)
- **Response:** 200 — artist-keyed counters object

#### GET /api/admin/diagnostics/performance

- **Summary:** Admin Diagnostics Performance — per-route p50/p95/p99 latency percentiles (rolling 1000 requests)
- **Auth:** Yes (X-API-Key)
- **Response:** 200 — route-keyed latency percentile object

#### GET /api/admin/diagnostics

- **Summary:** Admin Diagnostics — full runtime diagnostics; never exposes env var values
- **Auth:** Yes (X-API-Key)
- **Response:** 200 — runtime diagnostics object (versions, uptime, counts)

#### GET /api/admin/health/deep

- **Summary:** Admin Health Deep — readiness check: DB, scheduler, OAuth tokens, disk, security posture
- **Auth:** No
- **Response:** 200 healthy / 503 when `db_connected=False` (triggers Railway restart)

---

### agents — Agent roster, TTS, conversation, and billing

#### GET /api/agents

- **Summary:** List Agents — return the full agent roster with skills and voice assignments
- **Auth:** Yes (X-API-Key)
- **Response:** 200 — array of agent objects

#### GET /api/artist

- **Summary:** Get Artist — fetch artist profile
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, optional, default `""`)
- **Response:** 200 — ArtistProfile object

#### GET /api/artist/lookup

- **Summary:** Lookup Artist — find existing artist profile by name (case-insensitive)
- **Auth:** Yes (X-API-Key)
- **Query params:** `name` (string, required)
- **Response:** 200 — ArtistProfile object or null

#### POST /api/artist/save

- **Summary:** Save Artist — create or overwrite an artist profile
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `name` (string, required)
  - `country` (string, optional)
  - `genres` (array of string, optional)
  - `monthly_listeners` (string, optional)
  - `tier` (string, optional, default `"Gold"`)
  - `onboarded` (boolean, optional, default `false`)
  - `bio` (string, optional)
  - `photo` (string, optional/nullable)
- **Response:** 200 — saved ArtistProfile object

#### POST /api/transcribe

- **Summary:** Transcribe — transcribe an audio file to text via Whisper
- **Auth:** Yes (X-API-Key)
- **Request body:** multipart/form-data with `audio` (binary, required)
- **Response:** 200 — `{ text: "..." }`

#### POST /api/greet

- **Summary:** Greet — return the agent's opening line when an artist starts a chat (uses static rotating greetings, zero API calls)
- **Auth:** Yes (X-API-Key)
- **Request body:** form-encoded: `agent_id` (string, required), `tts_on` (string, optional, default `"true"`)
- **Response:** 200 — `{ greeting: "...", audio_b64: "..." }`

#### POST /api/handoff

- **Summary:** Handoff — new agent delivers a warm personalised greeting after Marcus routes to them, with full conversation context
- **Auth:** Yes (X-API-Key)
- **Request body:** form-encoded:
  - `agent_id` (string, required)
  - `history` (string JSON array, optional, default `"[]"`)
  - `tts_on` (string, optional, default `"true"`)
  - `artist_id` (string, optional, default `""`)
  - `from_agent_id` (string, optional, default `"puppet-master"`)
- **Response:** 200 — `{ greeting: "...", audio_b64: "..." }`

#### POST /api/chat_stream

- **Summary:** Chat Stream — send a message to an agent and receive a streaming response
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `agent_id` (string, required)
  - `message` (string, required)
  - `artist_id` (string, optional, default `""`)
  - `history` (string JSON array, optional, default `"[]"`)
  - `tts` (boolean, optional, default `true`)
- **Response:** 200 — SSE stream of text chunks + optional audio

#### GET /api/tts

- **Summary:** Tts Endpoint — synthesize text to audio (streaming)
- **Auth:** Yes (X-API-Key)
- **Query params:** `text` (string, required), `voice` (string, optional, default `"am_michael"`)
- **Response:** 200 — audio stream

#### POST /api/tts/cancel

- **Summary:** Tts Cancel — mark a call as ended so any in-flight `/api/tts/synth` for that call returns null
- **Auth:** Yes (X-API-Key)
- **Request body:** `call_id` (string, required)
- **Response:** 200 — confirmation

#### POST /api/tts/synth

- **Summary:** Tts Synth — synthesize text to base64 WAV; used by app to bypass SSE buffering
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `text` (string, required)
  - `voice` (string, optional, default `"am_onyx"`)
  - `call_id` (string, optional, default `""`)
- **Response:** 200 — `{ audio_b64: "..." }`

#### GET /api/tts/status

- **Summary:** Tts Status — returns whether TTS is ready (Kokoro loaded OR ElevenLabs key present)
- **Auth:** Yes (X-API-Key)
- **Response:** 200 — `{ ready: bool, provider: "kokoro"|"elevenlabs" }`

#### GET /api/health

- **Summary:** Api Health — secondary health endpoint
- **Auth:** Yes (X-API-Key)
- **Response:** 200 — `{}`

#### GET /api/history

- **Summary:** Get History — retrieve conversation history for an artist/agent pair
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required), `agent_id` (string, required)
- **Response:** 200 — array of conversation turn objects

#### POST /api/auth/send-otp

- **Summary:** Send Otp — send a 6-digit OTP via Twilio SMS
- **Auth:** Yes (X-API-Key)
- **Request body:** `phone` (string, required)
- **Response:** 200 — `{ sent: true }`

#### POST /api/auth/verify-otp

- **Summary:** Verify Otp — verify a 6-digit OTP; consumes the code on success
- **Auth:** Yes (X-API-Key)
- **Request body:** `phone` (string, required), `code` (string, required)
- **Response:** 200 — `{ verified: true }` or error

#### POST /api/notifications/register

- **Summary:** Register Push Token — save Expo push token to the artist's profile
- **Auth:** Yes (X-API-Key)
- **Request body:** `artist_id` (string, required), `push_token` (string, required)
- **Response:** 200 — confirmation

#### POST /api/notifications/send

- **Summary:** Send Notification — send a push notification to an artist via Expo push API and store in history
- **Auth:** Yes (X-API-Key)
- **Request body:**
  - `artist_id` (string, required)
  - `title` (string, required)
  - `body` (string, required)
  - `agent_id` (string, optional, default `""`)
  - `data` (object, optional, default `{}`)
- **Response:** 200 — `{ sent: true, ticket: {...} }`

#### GET /api/notifications/{artist_id}

- **Summary:** Get Notifications — return the artist's notification history
- **Auth:** Yes (X-API-Key)
- **Path params:** `artist_id` (string, required)
- **Response:** 200 — array of notification history objects

#### POST /api/billing/create-checkout

- **Summary:** Create Checkout — create a Stripe checkout session for a tier upgrade
- **Auth:** Yes (X-API-Key)
- **Request body:** `artist_id` (string, required), `tier` (string, required)
- **Response:** 200 — `{ checkout_url: "https://checkout.stripe.com/..." }`

#### POST /api/billing/upgrade

- **Summary:** Billing Upgrade — directly upgrade an artist's billing tier (admin use)
- **Auth:** Yes (X-API-Key)
- **Request body:** `artist_id` (string, required), `tier` (string, required)
- **Response:** 200 — updated billing object

#### POST /api/billing/webhook

- **Summary:** Billing Webhook — Stripe webhook handler for payment events
- **Auth:** Yes (X-API-Key)
- **Request body:** raw Stripe webhook payload (Stripe-Signature header required)
- **Response:** 200 — `{ received: true }`

#### GET /api/billing/history

- **Summary:** Get Billing History — return billing event history for an artist
- **Auth:** Yes (X-API-Key)
- **Query params:** `artist_id` (string, required)
- **Response:** 200 — array of billing event objects

#### POST /api/avatar/talk

- **Summary:** Avatar Talk — send audio chunks to D-ID avatar for lip-sync video generation
- **Auth:** Yes (X-API-Key)
- **Request body:** `agent_id` (string, required), `audio_chunks` (array, required)
- **Response:** 200 — D-ID talk result with video URL

#### GET /api/avatar/status

- **Summary:** Avatar Status — check if D-ID avatar feature is available
- **Auth:** Yes (X-API-Key)
- **Response:** 200 — `{ available: bool }`
