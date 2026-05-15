# PLMKR — Deployment Runbook (May 14, 2026)

**Entity:** Marquis Holdings LLC (NM)
**Operator:** Tommy Lam <mypsychoblast@gmail.com>
**Main branch:** `main` (commit `2762b88`)
**Platform:** Railway (auto-deploys on push to `main` via GitHub integration)
**Replaces:** `RUNBOOK_MANUAL_SESSION.md` (see that file for historical context)

---

## Pre-Deploy Checklist

Before triggering any Railway deploy, confirm:

- [ ] Full test suite passes locally: `python3 -m pytest` → all green
- [ ] No uncommitted changes: `git status` → clean
- [ ] Correct branch: currently on a feature branch, not `main`
- [ ] Code merged to `main` with `--no-ff`: `git merge --no-ff <branch>`

---

## Required vs Optional Env Vars

Railway automatically injects `RAILWAY_ENVIRONMENT=production`. Everything else must be set manually in Railway → Variables.

### Hard requirements — app crashes without these configured correctly

| Variable | What breaks | Guard |
|----------|-------------|-------|
| `DATABASE_URL` (if set) | Must be a reachable Postgres URL. If set but unreachable and `DB_FAILOVER_TO_SQLITE` ≠ `true` → `sys.exit(1)` at boot | Hard exit |
| `STRIPE_DEV_ALLOW_UNSIGNED` | Must NOT be `true` on Railway (`RAILWAY_ENVIRONMENT` is auto-set) → `sys.exit(1)` | Hard exit |

### Required for production use

| Variable | Where to get it | Effect if missing |
|----------|----------------|-------------------|
| `PLMKR_API_KEY` | `openssl rand -hex 32` | All routes unauthenticated — startup WARNING. Never skip in prod. |
| `ANTHROPIC_API_KEY` | Anthropic console | AI routes return 503. Core feature unavailable. |
| `APP_BASE_URL` | Your Railway HTTPS URL | Stripe redirects and OAuth callbacks broken. |

### Required when enabling Gmail outreach

| Variable | Where to get it |
|----------|----------------|
| `GMAIL_OAUTH_CLIENT_ID` | GCP Console → APIs & Services → Credentials |
| `GMAIL_OAUTH_CLIENT_SECRET` | Same |
| `GMAIL_OAUTH_REDIRECT_URI` | Must be `https://<railway-url>/api/gmail/callback` exactly |

### Optional — features degrade gracefully when unset

| Variable | Feature disabled when unset |
|----------|-----------------------------|
| `STRIPE_SECRET_KEY` | Billing checkout + webhook routes return 503 |
| `STRIPE_WEBHOOK_SECRET` | Webhook signature verification fails — all webhooks rejected |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_PHONE_NUMBER` | SMS OTP bypassed (dev mode) |
| `ELEVENLABS_API_KEY` | TTS routes 503; Kokoro (local) also unavailable on Railway |
| `BUFFER_CLIENT_ID` / `BUFFER_CLIENT_SECRET` / `BUFFER_REDIRECT_URI` | Social scheduling via Buffer disabled |
| `D_ID_API_KEY` | Avatar video routes return 503 |
| `CLOUDINARY_CLOUD_NAME` | Files served from local static/ — no CDN |
| `SENTRY_DSN` | Error tracking disabled (no-op — no error at boot) |
| `SCHEDULER_ENABLED` | Default `false` — inbox polling + weekly reports disabled |
| `SCHEDULER_BATCH_LIMIT` | Default `10` — campaign action batch size |
| `DAILY_PITCH_QUOTA` | Default `50` — outreach emails per artist per day |

Reference: see `.env.example` for complete descriptions and guard levels.

---

## Part A — GCP OAuth Setup (one-time per project)

Required for Gmail outreach. Skip if outreach is not yet in scope.

1. Go to [GCP Console](https://console.cloud.google.com) → Select or create project `plmkr-prod`
2. **Enable Gmail API:** APIs & Services → Library → "Gmail API" → Enable
3. **OAuth Consent Screen:** APIs & Services → OAuth consent screen
   - User Type: External
   - App name: `PLMKR — Marquis Holdings LLC`
   - Support email: `getnexusai@gmail.com`
   - Authorized domains: your Railway domain
   - Scopes: `gmail.send`, `gmail.readonly`
   - Test users: add all artist Gmail accounts
4. **Create OAuth credentials:** Credentials → Create Credentials → OAuth 2.0 Client ID
   - Application type: Web application
   - Authorized redirect URI: `https://<railway-url>/api/gmail/callback`
   - Copy Client ID and Secret
5. Set in Railway Variables:
   ```
   GMAIL_OAUTH_CLIENT_ID=<client-id>.apps.googleusercontent.com
   GMAIL_OAUTH_CLIENT_SECRET=<client-secret>
   GMAIL_OAUTH_REDIRECT_URI=https://<railway-url>/api/gmail/callback
   ```

---

## Part B — Railway Env Vars

1. Railway dashboard → Your service → Variables
2. Add each required variable from the table above
3. Click **Save** — Railway auto-redeploys when variables are saved
4. Verify the new deploy shows up in Railway → Deployments

**Order matters:** Set `PLMKR_API_KEY` and `ANTHROPIC_API_KEY` before any other testing. Without `PLMKR_API_KEY`, all routes are unauthenticated.

---

## Part C — Railway Persistent Volume

**Required before first deploy that stores data.** Without this, the SQLite DB is wiped on every redeploy.

1. Railway dashboard → Service → Settings → Volumes
2. Click **Add Volume**
   - Name: `plmkr-data`
   - Mount path: `/data`
   - Size: 1 GB
3. Save → Railway auto-redeploys with the volume attached
4. Verify: boot log must show `✓  /data is writable — volume mount OK`

The `/data` mount also appears in `railway.toml` as the declared mount path.

---

## Part D — Stripe Webhook Registration

Defer until billing is ready for production use. The hard guard (`sys.exit` on `STRIPE_DEV_ALLOW_UNSIGNED + RAILWAY_ENVIRONMENT`) prevents silent unsigned-webhook acceptance on Railway.

When ready:
1. Stripe dashboard → Developers → Webhooks → Add endpoint
   - URL: `https://<railway-url>/api/billing/webhook`
   - Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`
2. Copy signing secret → set `STRIPE_WEBHOOK_SECRET` in Railway Variables

---

## Part E — Deploy + Verify

After Railway deploys the new image, verify:

### E1 — Boot logs (check in Railway → Deployments → View Logs)

```
✓  /data is writable — volume mount OK        ← volume attached
[DB] memory.db ready                            ← SQLite initialized at /data/memory.db
[TTS] Kokoro loaded OK  OR  [Kokoro] WARNING   ← Kokoro absent on Railway is expected
[PITCH] SQLite pitch tables ready
[PR] SQLite PR tables ready
[Booking] SQLite booking tables ready
[Social] SQLite social + report tables ready
[Release] SQLite release + campaign tables ready
[INIT] DB ready, ...
```

### E2 — Liveness check

```bash
curl https://<railway-url>/health
# Expected: {"status":"ok"}
```

### E3 — Deep readiness check (requires API key)

```bash
curl -H "X-API-Key: $PLMKR_API_KEY" https://<railway-url>/api/admin/health/deep
# Expected: {"db_connected":true, "auth_enabled":true, "anthropic_available":true, ...}
# If db_connected=false: Railway restarts the container (configured in railway.json)
```

### E4 — Full diagnostics

```bash
curl -H "X-API-Key: $PLMKR_API_KEY" https://<railway-url>/api/admin/diagnostics
# Expected: env_snapshot shows SET/MISSING for all vars (never actual values)
#           service_status shows which integrations are wired
#           recent_errors: [] on a clean deploy
```

---

## Part F — Gmail OAuth Per Artist

Run once per artist after Part A is complete.

```
1. Open in browser:
   https://<railway-url>/api/gmail/auth?artist_id=<ARTIST_ID>

2. Artist logs in with their Google account → grants consent

3. Browser redirects to /api/gmail/callback — automatic, no action needed

4. Verify:
   curl -H "X-API-Key: $PLMKR_API_KEY" \
        "https://<railway-url>/api/gmail/status?artist_id=<ARTIST_ID>"
   # Expected: {"connected": true}
```

**Error reference:**

| Error | Fix |
|-------|-----|
| `503` on `/api/gmail/auth` | Set all three `GMAIL_OAUTH_*` vars in Railway |
| `redirect_uri_mismatch` | URI in GCP must exactly match `GMAIL_OAUTH_REDIRECT_URI` |
| `403 access_denied` | Add artist email to GCP Test Users |
| `403 Gmail auth expired` (on send) | Re-run step 1 |

---

## Part G — First Pitch Send Verification

```bash
curl -X POST https://<railway-url>/api/pitches/batch \
  -H "X-API-Key: $PLMKR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "artist_id": "<ARTIST_ID>",
    "curator_ids": ["<CURATOR_ID>"],
    "track_metadata": {"name": "Test Track", "genre": "indie"}
  }'

# Success:   {"sent":1,"failed":0,"errors":[],"pitch_ids":["..."]}
# Gmail err: {"sent":0,"failed":1,"errors":["Gmail auth error..."]}  → Part F first
# 503:       ANTHROPIC_API_KEY missing → set it in Railway
# 429:       Daily quota hit (default 50) → wait until midnight UTC or adjust DAILY_PITCH_QUOTA
```

---

## Part H — Scheduler Activation

Only enable after Part G confirms email sending works end-to-end.

1. Railway Variables → add `SCHEDULER_ENABLED=true`
2. Save → Railway redeploys
3. Boot log must show `[SCHEDULER] Running — inbox polling every 6h`
4. Verify: `GET /api/admin/health/deep` → `scheduler_running: true`

Risk: `SCHEDULER_ENABLED=true` without working Gmail OAuth causes silent failures in the inbox poll. Verify Gmail is connected before enabling.

---

## Post-Deploy Observability Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/admin/diagnostics` | Full env snapshot, service status, runtime, volume, errors |
| `GET /api/admin/diagnostics/performance` | Per-route p50/p95/p99 latency after traffic |
| `GET /api/admin/diagnostics/anthropic-stats` | Anthropic API call counters by model |
| `GET /api/admin/diagnostics/gmail-stats` | Gmail API call counters by artist |

All require `X-API-Key: $PLMKR_API_KEY`.

---

## Rollback Procedure

If a deploy breaks production:

```bash
# 1. Find the last working merge commit
git log --oneline main | head -10

# 2. Revert the broken merge
git revert -m 1 <bad-merge-commit-hash>

# 3. Push — Railway auto-deploys the reverted code
git push origin main

# 4. Verify boot logs confirm the revert is live
```

For emergency: Railway also supports one-click rollback in the Deployments panel (select previous deployment → Redeploy).

---

## Part I — Running DB Seeds Against Railway (one-time per deployment)

Seed scripts populate the curator, PR-contact, and booking-contact databases. They are baked
into the Docker image at `/app/` (covered by R-31 fix). To run them against the live Railway DB
after a fresh deploy:

**Preferred approach — API endpoints (no shell access required):**

```bash
# Seed curators from the bundled JSON (data/curators_seed.json is in the image)
curl -X POST https://<railway-url>/api/curators/seed \
  -H "X-API-Key: $PLMKR_API_KEY"

# Seed PR contacts (if endpoint exists)
curl -X POST https://<railway-url>/api/pr-contacts/seed \
  -H "X-API-Key: $PLMKR_API_KEY"

# Seed booking contacts (if endpoint exists)
curl -X POST https://<railway-url>/api/booking-contacts/seed \
  -H "X-API-Key: $PLMKR_API_KEY"
```

**Alternative — Railway shell (requires seed scripts at /app):**

If the API endpoint does not yet exist for a given seed type, you can run the scripts directly
via Railway's shell. Open Railway → Service → Settings → Shell, then:

```bash
# All seed scripts are at /app/ in the image
cd /app
python3 seed_curators.py
python3 seed_pr_contacts.py
python3 seed_booking_contacts.py
```

**Verification:**

```bash
# Confirm curators were seeded (returns list)
curl -H "X-API-Key: $PLMKR_API_KEY" https://<railway-url>/api/curators
```

**Notes:**

- Seeds are idempotent via UNIQUE constraints — re-running them is safe.
- The `/data` Railway volume must be attached (Part C) before seeding; otherwise the SQLite DB
  is ephemeral and seeds are lost on the next redeploy.
- Local verification: `make build-test && make verify-seeds-in-image` confirms seed scripts are
  present in the image before deploying.

---

## Auth Bypass Paths (No X-API-Key Required)

```
GET  /health
GET  /api/admin/health/deep
GET  /docs
GET  /redoc
GET  /openapi.json
OPTIONS  *
```

All other routes require `X-API-Key` header when `PLMKR_API_KEY` is set.
