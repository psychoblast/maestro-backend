# PLMKR — Manual Session Runbook
## Railway Production Deploy: First-Time Setup

**Branch this runbook targets:** `main` (commit `7e41a2a`)  
**Date written:** 2026-05-10  
**Scope:** Everything a human operator must do manually — GCP OAuth console setup,
Railway env vars, persistent volume, Gmail OAuth authorization, first test pitch send,
and scheduler activation. The app itself auto-deploys from `main` via GitHub Actions.

---

## Prerequisites

- Railway project already exists with a service named `maestro-backend`
- GitHub repository connected to Railway for auto-deploy
- A GCP project already created (or ability to create one)
- Google account that owns the artist's Gmail inbox
- Stripe account (can use test mode for initial deploy)
- Anthropic API key

---

## Part A — GCP OAuth App Setup (One-Time)

These steps create the OAuth credentials that authorize PLMKR to send Gmail on the
artist's behalf. Do this before setting env vars in Railway.

### A.1 Enable the Gmail API

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Select (or create) your project
3. Navigation menu → **APIs & Services** → **Library**
4. Search `Gmail API` → click **Enable**

### A.2 Configure the OAuth Consent Screen

1. **APIs & Services** → **OAuth consent screen**
2. **User Type:** External (unless your GCP org supports Internal)
3. Fill in:
   - **App name:** PLMKR (or your platform name)
   - **User support email:** your email
   - **Developer contact:** your email
4. **Scopes** → Add scopes:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.readonly`
5. **Test users** → Add the Gmail address that will authorize (the artist's Gmail)
6. Save and continue through all screens

> **Why test users?** While the app is in "Testing" mode (not verified by Google), only
> listed test users can authorize. This is fine for early-stage use. Full verification
> is needed if > 100 users authorize.

### A.3 Create OAuth Credentials

1. **APIs & Services** → **Credentials** → **+ Create Credentials** → **OAuth client ID**
2. **Application type:** Web application
3. **Name:** PLMKR Backend (Railway)
4. **Authorized redirect URIs:** Add exactly:
   ```
   https://<your-railway-url>/api/gmail/callback
   ```
   - Get `<your-railway-url>` from Railway dashboard → service → **Settings** → **Domains**
   - Must match `GMAIL_OAUTH_REDIRECT_URI` env var exactly — including scheme, no trailing slash
5. Click **Create**
6. Download or copy:
   - **Client ID** → becomes `GMAIL_OAUTH_CLIENT_ID`
   - **Client secret** → becomes `GMAIL_OAUTH_CLIENT_SECRET`

---

## Part B — Railway Environment Variables

Set ALL variables below before triggering the first deploy. Variables with no default
in the code will silently degrade (soft guards) or crash on boot (hard guards).

Navigate to: Railway Dashboard → `maestro-backend` service → **Variables** tab

### B.1 Required — Will Crash or Degrade Without These

| Variable | Source | Notes |
|----------|--------|-------|
| `ANTHROPIC_API_KEY` | Anthropic console | Soft guard: AI routes return 503 if absent; app boots (`main.py:28`) |
| `GMAIL_OAUTH_CLIENT_ID` | GCP Credentials (Part A) | 503 on `/api/gmail/auth` if absent (`pitch_service.py:36`) |
| `GMAIL_OAUTH_CLIENT_SECRET` | GCP Credentials (Part A) | 503 on `/api/gmail/auth` if absent (`pitch_service.py:37`) |
| `GMAIL_OAUTH_REDIRECT_URI` | Your Railway URL + `/api/gmail/callback` | Must exactly match GCP console registration (`pitch_service.py:38`) |
| `PLMKR_API_KEY` | Generate: `openssl rand -hex 32` | If unset, API is dev-permissive (no auth enforcement) (`main.py:51`) |

### B.2 Required for Billing (Stripe)

| Variable | Source | Notes |
|----------|--------|-------|
| `STRIPE_SECRET_KEY` | Stripe dashboard → Developers → API keys | Use `sk_test_...` for initial deploy |
| `STRIPE_WEBHOOK_SECRET` | Stripe dashboard → Webhooks → signing secret | Set after adding webhook endpoint (Part D) |

> **Hard guard:** If `RAILWAY_ENVIRONMENT` is set AND `STRIPE_DEV_ALLOW_UNSIGNED=true`,
> the app crashes at boot with `sys.exit(1)` (`main.py` startup guard). Never set
> `STRIPE_DEV_ALLOW_UNSIGNED=true` in production. Leave it unset entirely.

### B.3 Optional but Recommended

| Variable | Default in code | Notes |
|----------|----------------|-------|
| `DB_PATH` | `/data/memory.db` | Leave as default — matches volume mount path |
| `AUDIO_CACHE_DIR` | `/data/audio_cache` | Leave as default — inside the volume |
| `MAX_UPLOAD_SIZE` | `26214400` (25 MB) | Override only if uploads routinely larger |
| `ALLOWED_ORIGINS` | 6 hardcoded defaults | Comma-separated; override if you have a custom domain (`main.py:63`) |
| `APP_BASE_URL` | `http://192.168.18.59:8765` | **MUST set** for production (`main.py:~1828`); set to your Railway HTTPS URL |
| `DAILY_PITCH_QUOTA` | `50` | Max emails per artist per day (`pitch_service.py:46`) |
| `SCHEDULER_ENABLED` | `false` | Set `true` after manual Gmail OAuth works (Part G) |
| `REPLY_POLL_HOURS` | `6` | How often scheduler scans inbox |

### B.4 TTS / Voice (Set If Using Voice Features)

| Variable | Notes |
|----------|-------|
| `ELEVENLABS_API_KEY` | Paid Starter account — free tier flagged by Railway |
| `CLOUDINARY_CLOUD_NAME` | Optional CDN for audio/avatar assets |

### B.5 Twilio SMS OTP (Optional)

| Variable | Notes |
|----------|-------|
| `TWILIO_ACCOUNT_SID` | |
| `TWILIO_AUTH_TOKEN` | **Must be exactly 32 lowercase hex characters** — app logs a warning if wrong format (`main.py:820`) |
| `TWILIO_PHONE_NUMBER` | E.164 format: `+1XXXXXXXXXX` |

### B.6 Postgres (Optional — Scale Path)

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | If set, app connects to Postgres instead of SQLite |
| `DB_FAILOVER_TO_SQLITE` | Set `true` to allow fallback to SQLite if Postgres fails |

> **Hard guard (R-06):** If `DATABASE_URL` is set and Postgres init fails and
> `DB_FAILOVER_TO_SQLITE != "true"`, the app crashes with `sys.exit(1)`.
> During initial deploy, leave `DATABASE_URL` unset (use SQLite volume).

---

## Part C — Persistent Volume Setup (Railway Dashboard Only)

**Why:** Without a volume, every Railway redeploy wipes `/data`, destroying the SQLite
database and all Gmail OAuth tokens. This step cannot be automated — Railway does not
support declarative volume creation via config files.

**`railway.toml` already declares the mount point** — it just needs a volume to attach to:
```toml
[[mounts]]
mountPath = "/data"
```

### Steps

1. Railway Dashboard → `maestro-backend` service → **Settings** tab
2. Scroll to **Volumes** section
3. Click **Add Volume**
4. Set:
   - **Volume name:** `plmkr-data`
   - **Mount path:** `/data`  ← must be exactly this
   - **Size:** `1 GB` (increase if audio cache grows)
5. Click **Create** — Railway auto-redeploys

### Verify Volume Is Mounted

After redeploy, check startup logs for:
```
✓  /data is writable — volume mount OK
```
If you see:
```
WARNING: /data is NOT writable
```
The volume is not mounted. Return to step 3.

---

## Part D — Stripe Webhook Registration (If Using Billing)

1. Stripe Dashboard → **Developers** → **Webhooks** → **Add endpoint**
2. **Endpoint URL:** `https://<your-railway-url>/api/billing/webhook`
3. **Events to send:**
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Click **Add endpoint** → copy **Signing secret** → paste into Railway as `STRIPE_WEBHOOK_SECRET`
5. Redeploy or save — env var changes take effect without a full rebuild

---

## Part E — Deploy and Smoke Test

After Parts A–D are complete:

### E.1 Trigger Deploy

Push a commit to `main` or click **Redeploy** in Railway dashboard.

### E.2 Check Startup Logs

In Railway dashboard → **Deployments** → latest → **Logs**. Look for these in order:

```
✓  /data is writable — volume mount OK
[DB] SQLite initialized at /data/memory.db
[Pitch] Daily quota: 50
```

**Red flags in logs:**
- `WARNING: /data is NOT writable` → volume not mounted (Part C)
- `[ENV] ANTHROPIC_API_KEY missing — AI features disabled` → set the key (Part B.1)
- `sys.exit(1)` + Stripe message → `STRIPE_DEV_ALLOW_UNSIGNED=true` is set on Railway — remove it
- `sys.exit(1)` + Postgres message → `DATABASE_URL` set but Postgres unreachable — check connection or set `DB_FAILOVER_TO_SQLITE=true`

### E.3 Smoke Test: Basic Health

```bash
# Simple health (no auth required)
curl https://<your-railway-url>/health

# Deep health (requires X-API-Key if PLMKR_API_KEY is set)
curl -H "X-API-Key: <PLMKR_API_KEY>" https://<your-railway-url>/api/admin/health/deep
```

Expected deep health response shape (all fields from `admin_service.py:197`):
```json
{
  "timestamp": "2026-05-10T12:00:00+00:00",
  "db_connected": true,
  "scheduler_running": false,
  "gmail_token_valid_for_artists": 0,
  "buffer_token_valid_for_artists": 0,
  "disk_usage_pct": 12.4,
  "auth_enabled": true,
  "auth_mode": "enforced",
  "anthropic_available": true,
  "stripe_signed_webhooks_required": true,
  "stripe_dev_allow_unsigned": false,
  "cors_origins": "*"
}
```

Key fields to verify:
- `db_connected: true` — SQLite volume is mounted and accessible
- `auth_enabled: true` — `PLMKR_API_KEY` is set (good for prod)
- `anthropic_available: true` — key is loaded
- `stripe_dev_allow_unsigned: false` — CRITICAL, must be false in prod
- `scheduler_running: false` — expected until Part G

---

## Part F — Gmail OAuth Authorization Per Artist

Each artist whose Gmail inbox PLMKR will use to send pitches must authorize once.
This cannot be automated — it requires browser interaction with Google's consent screen.

### F.1 Prerequisites

- Part A (GCP setup) complete
- `GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET`, `GMAIL_OAUTH_REDIRECT_URI` set in Railway
- Artist record exists in the database (create via `POST /api/artist/save`)
- Artist's Gmail address is listed as a **test user** in GCP OAuth consent screen (Part A.2)

### F.2 Authorization Flow

**Step 1** — Trigger the OAuth redirect:
```bash
# Open this URL in a browser — do NOT curl it (it redirects to Google)
https://<your-railway-url>/api/gmail/auth?artist_id=<ARTIST_ID>
```

Code path: `pitch_service.py:217` — `gmail_auth()`:
- Validates `GMAIL_OAUTH_CLIENT_ID/SECRET/REDIRECT_URI` are set (503 if any missing)
- Builds Google OAuth URL with scopes `gmail.send` + `gmail.readonly`
- Passes `artist_id` as OAuth `state` parameter
- Redirects browser to Google's consent screen

**Step 2** — Google consent screen:
- Artist logs in to their Google account
- Grants permission to PLMKR to send email and read inbox
- Google redirects back to `GMAIL_OAUTH_REDIRECT_URI` with `?code=...&state=<ARTIST_ID>`

**Step 3** — Callback (automatic, no action needed):
- `GET /api/gmail/callback` (`pitch_service.py:240`): exchanges code for tokens,
  saves `gmail_tokens` dict to artist's profile in SQLite

**Step 4** — Verify authorization succeeded:
```bash
curl -H "X-API-Key: <PLMKR_API_KEY>" \
  "https://<your-railway-url>/api/gmail/status?artist_id=<ARTIST_ID>"
```
Expected: `{"connected": true, "artist_id": "<ARTIST_ID>"}`

Also verify via deep health — `gmail_token_valid_for_artists` should be `>= 1`.

### F.3 Troubleshooting Gmail OAuth

| Symptom | Cause | Fix |
|---------|-------|-----|
| `503` on `/api/gmail/auth` | OAuth env vars missing | Set all three in Railway (Part B.1) |
| `redirect_uri_mismatch` (Google error) | URI doesn't match GCP console | Must match exactly including `https://` and no trailing slash |
| `403 access_denied` (Google error) | Artist email not in test users | Add to GCP OAuth consent screen → Test users (Part A.2) |
| `{"connected": false}` after callback | Callback failed silently | Check Railway logs for Python exception during token exchange |
| `403 Gmail auth expired` on send | Refresh token expired | Artist must re-authorize via `/api/gmail/auth?artist_id=...` |
| Data lost after redeploy | Volume not mounted | Part C — tokens stored in SQLite on `/data` |

---

## Part G — First Pitch Send (Manual Verification)

Before enabling the scheduler, verify the full pitch pipeline manually with one curator.

### G.1 Seed a Test Curator

```bash
curl -X POST "https://<your-railway-url>/api/curators/seed" \
  -H "X-API-Key: <PLMKR_API_KEY>" \
  -H "Content-Type: application/json"
```
This populates the database with sample curators.

Or create a real curator:
```bash
curl -X POST "https://<your-railway-url>/api/curators" \
  -H "X-API-Key: <PLMKR_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Curator",
    "outlet": "Test Blog",
    "contact_email": "your-test-email@example.com",
    "genres": ["indie", "pop"],
    "tier": "C"
  }'
```
Save the returned `id` as `<CURATOR_ID>`.

### G.2 Generate a Pitch (No Send)

```bash
curl -X POST "https://<your-railway-url>/api/pitches/generate" \
  -H "X-API-Key: <PLMKR_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_id": "<ARTIST_ID>",
    "curator_id": "<CURATOR_ID>",
    "track_metadata": {"name": "Test Track", "genre": "indie"}
  }'
```
Expected: `{"subject": "...", "body": "...", "suggested_followup_days": 5, "artist_id": "...", "curator_id": "..."}`

If you get `503` here, `ANTHROPIC_API_KEY` is not set.

### G.3 Send the Batch (One Curator)

```bash
curl -X POST "https://<your-railway-url>/api/pitches/batch" \
  -H "X-API-Key: <PLMKR_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_id": "<ARTIST_ID>",
    "curator_ids": ["<CURATOR_ID>"],
    "track_metadata": {"name": "Test Track", "genre": "indie"}
  }'
```

Expected success response (`pitch_service.py:782`):
```json
{"sent": 1, "failed": 0, "errors": [], "pitch_ids": ["<UUID>"]}
```

**Error responses to diagnose:**
- `{"sent": 0, "failed": 1, "errors": ["Gmail auth error..."]}` → Gmail not connected (Part F)
- `429` → daily quota hit (`DAILY_PITCH_QUOTA` default 50)
- `"Already pitched curator ... today — skipped"` → idempotency key duplicate (expected if called twice same day)
- `500 Pitch generation failed` → Anthropic API error — check key

### G.4 Verify Email Arrived

Check the curator's inbox (`your-test-email@example.com`). Email comes from the artist's
Gmail address that was authorized in Part F.

---

## Part H — Scheduler Activation

Only enable after Part G (manual pitch send) succeeds and Gmail OAuth is confirmed working.

### H.1 Enable the Scheduler

In Railway → Variables → set:
```
SCHEDULER_ENABLED=true
REPLY_POLL_HOURS=6
```

Save (Railway redeploys automatically).

### H.2 Verify Scheduler Started

After redeploy, check startup logs for:
```
[Pitch] APScheduler started — inbox poll every 6 hours
```

Then confirm via deep health:
```bash
curl -H "X-API-Key: <PLMKR_API_KEY>" \
  https://<your-railway-url>/api/admin/health/deep
```
`scheduler_running` should be `true`.

### H.3 Manual Inbox Scan (Test Scheduler Logic)

Without waiting 6 hours, trigger a scan manually:
```bash
curl -X POST "https://<your-railway-url>/api/inbox/scan?artist_id=<ARTIST_ID>" \
  -H "X-API-Key: <PLMKR_API_KEY>"
```
Expected: `{"scanned": N, "matched": M, "classified": [...]}`

---

## Failure Modes and Recovery

### Volume Missing After Redeploy

**Symptom:** Startup log shows `WARNING: /data is NOT writable`. All artist data and
Gmail tokens are gone.

**Recovery:**
1. Follow Part C to create and attach the volume
2. After volume is mounted, all artists must re-authorize Gmail (Part F)
3. Pitch history is lost — cannot be recovered without a backup

**Prevention:** Always verify volume in Railway dashboard before deploying.

### Gmail Token Expired

**Symptom:** Batch send returns `403 Gmail auth expired — re-connect`.

**Recovery:** Have artist re-authorize: open
`https://<your-railway-url>/api/gmail/auth?artist_id=<ARTIST_ID>` in browser.
Tokens are refreshed automatically during normal operation (`_get_gmail_service()` in
`pitch_service.py` calls `creds.refresh()` if token is expired and refresh_token is present),
but if refresh_token itself is invalid, full re-auth is needed.

### Anthropic API Unavailable

**Symptom:** `POST /api/pitches/generate` returns `503`.

**Cause:** `ANTHROPIC_API_KEY` absent or expired. Code: `pitch_service.py` reads
`_ANTHROPIC_KEY` from env; if empty, Anthropic client throws during API call.

**Recovery:** Set/rotate key in Railway Variables → save (no rebuild needed).

### Stripe Webhook Signature Failure

**Symptom:** Billing webhooks return `400 Stripe signature verification failed`.

**Recovery:** Regenerate webhook signing secret in Stripe dashboard → update
`STRIPE_WEBHOOK_SECRET` in Railway → save.

### Database Lock (SQLite Concurrent Write)

**Symptom:** `sqlite3.OperationalError: database is locked` in logs.

**Cause:** SQLite on a volume is single-writer. Under concurrent load this surfaces.

**Recovery (short-term):** Redeploy clears in-flight connections.
**Recovery (long-term):** Add Railway Postgres add-on, set `DATABASE_URL`.

---

## API Auth Reference

The `_APIKeyMiddleware` (`main.py:912`) enforces auth on all routes **except**:
- `GET /health` — always public
- `GET /docs`, `GET /redoc`, `GET /openapi.json` — always public
- `OPTIONS *` — CORS preflight, always allowed

All other routes require `X-API-Key: <PLMKR_API_KEY>` header when `PLMKR_API_KEY` is set.
If `PLMKR_API_KEY` is not set in Railway, all routes are dev-permissive (no auth enforced).

---

## End-to-End Sequence Summary

```
Part A: GCP OAuth setup (one-time)
Part B: Set Railway env vars
Part C: Create Railway persistent volume
Part D: Register Stripe webhook (if billing)
Part E: Deploy + smoke test /health + /api/admin/health/deep
Part F: Artist authorizes Gmail (per-artist, browser required)
Part G: Manual pitch send to verify full pipeline
Part H: Enable scheduler (SCHEDULER_ENABLED=true)
```

**Do not skip steps.** Each part depends on the previous one being correct.
Setting `SCHEDULER_ENABLED=true` before Gmail is authorized will cause the scheduler
to fail silently on every poll cycle.
