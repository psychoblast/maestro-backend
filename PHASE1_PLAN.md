# Phase 1 — Core Action Layer
Planning doc only. No code. Created: 2026-05-08.

---

## Prerequisite
Phase 0 must be signed off by Tommy before Phase 1 begins.
Remaining Phase 0 blockers: 0.D (OTP), 0.E (first call failure), 0.1/0.2/0.3 (frontend).

---

## Phase 1 Scope

Phase 1 makes PLMKR agents take **real-world action**. The first action is pitching curators via Gmail.
Currently agents only give advice. Phase 1 ends when Marcus can draft and send a real pitch email.

---

## Unit 1.1 — Gmail OAuth Routes

### What it does
Adds two backend endpoints to initiate and complete the Gmail OAuth Authorization Code flow.

### Endpoints
```
GET  /api/gmail/auth?artist_id=xxx      → redirect to Google OAuth consent screen
GET  /api/gmail/callback?code=xxx&state=artist_id  → exchange code for tokens, store, return success
```

### Token storage
Store access_token + refresh_token in artist profile (in existing Postgres/SQLite).
Field: `artist["gmail_tokens"] = {"access_token": ..., "refresh_token": ..., "expires_at": ...}`
No separate table needed — artist profile already persists correctly.

### Required env vars
```
GMAIL_CLIENT_ID
GMAIL_CLIENT_SECRET
GMAIL_REDIRECT_URI  (e.g. https://plmkr.up.railway.app/api/gmail/callback)
```

### Scope
`https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly`

### Libraries
`google-auth`, `google-auth-oauthlib`, `google-api-python-client` — add to requirements.txt

---

## Unit 1.2 — Gmail Token Refresh

### What it does
A helper function `get_gmail_service(artist_id)` that:
1. Loads tokens from artist profile
2. Checks `expires_at` — if expired, uses `refresh_token` to get new `access_token`
3. Saves updated tokens back to artist profile
4. Returns authenticated `googleapiclient.discovery.Resource` object

### Error handling
- If no tokens: raise `GmailNotConnected` (HTTP 403 with `"gmail_not_connected": true` in response)
- If refresh fails (revoked): raise `GmailAuthExpired` (same pattern — prompt re-auth)

---

## Unit 1.3 — sendEmail() Core Function

### What it does
```python
async def send_email(artist_id: str, to: str, subject: str, body: str) -> dict
```
- Uses `get_gmail_service(artist_id)` from 1.2
- Composes MIME message
- Sends via `gmail.users().messages().send()`
- Returns `{"message_id": ..., "thread_id": ..., "status": "sent"}`

### Endpoint
```
POST /api/gmail/send
Body: {artist_id, to, subject, body}
```

### Verification
curl with real Gmail credentials, confirm email arrives in inbox.

---

## Unit 1.4 — Curator Data Model

### Schema
New table `curators` in existing SQLite/Postgres DB.

```sql
CREATE TABLE IF NOT EXISTS curators (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL,
    playlist    TEXT,
    genre       TEXT,
    followers   INTEGER DEFAULT 0,
    platform    TEXT DEFAULT 'spotify',
    notes       TEXT,
    last_pitched TIMESTAMP,
    pitch_count  INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Pattern match
Same init-on-startup pattern as existing SQLite tables (see `_sqlite_init()` at line ~820).

### Endpoints
```
GET  /api/curators?genre=xxx&platform=xxx   → list/search curators
POST /api/curators                           → add curator
GET  /api/curators/{id}                     → get single curator
```

---

## Unit 1.5 — Curator Seed Data

### What it does
Seed script (run once) that populates the `curators` table with an initial list.
~50 curators: mix of Spotify, Apple Music, YouTube — variety of genres.

### Data source
Public curator databases + manual research. Tommy to review before merge.

### Format
JSON seed file at `data/curators_seed.json` — loaded by a `/api/curators/seed` endpoint (admin-only, one-time).

---

## Unit 1.6 — Inbox Parsing

### What it does
```
GET /api/gmail/inbox?artist_id=xxx&max_results=20
```
- Fetches recent emails via Gmail API
- Categorizes each: `curator_reply | press_reply | venue_reply | fan | unknown`
- Returns structured list: `[{id, from, subject, category, snippet, date}]`

### Categorization logic
- Check sender domain against known curator/press/venue lists
- Check subject for keywords: "playlist", "feature", "booking", "review"
- If match → set category; else `unknown`

### No polling, no background threads
This is on-demand only. Called when artist opens inbox view in app.

---

## Unit 1.7 — Marcus Pitching Agent (Function Calling)

### What it does
Marcus (`puppet-master` agent) gains two tools via Anthropic `tool_use`:

**Tool 1: `search_curators`**
```json
{
  "name": "search_curators",
  "description": "Search curator database by genre, platform, or follower count",
  "input_schema": {
    "type": "object",
    "properties": {
      "genre": {"type": "string"},
      "platform": {"type": "string", "enum": ["spotify", "apple_music", "youtube"]},
      "min_followers": {"type": "integer"}
    }
  }
}
```

**Tool 2: `send_pitch_email`**
```json
{
  "name": "send_pitch_email",
  "description": "Draft and send a pitch email to a curator on behalf of the artist",
  "input_schema": {
    "type": "object",
    "properties": {
      "curator_id": {"type": "string"},
      "subject": {"type": "string"},
      "body": {"type": "string"}
    },
    "required": ["curator_id", "subject", "body"]
  }
}
```

### Integration pattern
- Modify `/api/chat` endpoint to pass tools to Marcus agent only (check `agent["id"] == "puppet-master"`)
- Add tool result handling loop (standard Anthropic tool_use pattern)
- Tool calls hit internal functions, not external APIs directly
- Response includes `"actions_taken": [...]` for frontend to display

### Gmail prerequisite
Artist must have connected Gmail (1.1/1.2) before Marcus can send. If not connected, return `"gmail_not_connected": true` and guide artist to connect.

---

## Unit 1.8 — Press Database

Same pattern as curators (1.4). Table: `press_contacts`.
Fields: id, name, email, publication, beat (music genre focus), region, notes, last_pitched, pitch_count.

---

## Unit 1.9 — Venue Database

Same pattern as curators (1.4). Table: `venues`.
Fields: id, name, email, city, country, capacity, genre_focus, booking_contact, notes, last_pitched.

---

## Required Env Vars for Phase 1

```
GMAIL_CLIENT_ID          # Google Cloud Console → OAuth 2.0 client
GMAIL_CLIENT_SECRET      # Google Cloud Console
GMAIL_REDIRECT_URI       # Must match Railway URL exactly
```

Tommy to create Google Cloud project + OAuth credentials before 1.1 begins.

---

## Unit Breakdown (Estimated)

| Unit | Description | Commit tag |
|------|-------------|------------|
| 1.1 | Gmail OAuth routes | [1.1] |
| 1.2 | Token refresh helper | [1.2] |
| 1.3 | sendEmail() + endpoint | [1.3] |
| 1.4 | Curator data model + endpoints | [1.4] |
| 1.5 | Curator seed data | [1.5] |
| 1.6 | Inbox parsing | [1.6] |
| 1.7 | Marcus function calling | [1.7] |
| 1.8 | Press database | [1.8] |
| 1.9 | Venue database | [1.9] |

Each unit: implement → grep verify → curl verify → commit → next unit.

---

## Open Questions for Tommy Before Phase 1

1. **Google Cloud project** — does one exist? Or create new?
2. **DATABASE_URL** — activate Railway Postgres add-on now? (Cleaner for Phase 1 with multiple tables)
3. **Curator data source** — any existing list? Or start from scratch?
4. **Marcus scope** — should Marcus also handle press pitching, or just curators in Phase 1?
5. **Inbox view** — is there a frontend screen planned for inbox? Or just backend for now?
