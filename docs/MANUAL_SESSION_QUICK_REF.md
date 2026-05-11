# PLMKR — Manual Session Quick Reference
## Railway Production Deploy (main @ 7e41a2a)

---

## Sequence

| Step | Where | Done? |
|------|-------|-------|
| A. GCP OAuth: enable Gmail API, consent screen, OAuth credentials | GCP Console | ☐ |
| B. Set Railway env vars (table below) | Railway → Variables | ☐ |
| C. Create persistent volume (`plmkr-data`, mount `/data`, 1 GB) | Railway → Settings → Volumes | ☐ |
| D. Register Stripe webhook endpoint | Stripe → Developers → Webhooks | ☐ |
| E. Deploy + smoke test `/health` and `/api/admin/health/deep` | curl | ☐ |
| F. Artist authorizes Gmail (browser: `/api/gmail/auth?artist_id=X`) | Browser | ☐ |
| G. Test first pitch send via `/api/pitches/batch` | curl | ☐ |
| H. Set `SCHEDULER_ENABLED=true` after G passes | Railway → Variables | ☐ |

---

## Required Env Vars

| Variable | Where to get it | Hard/Soft |
|----------|----------------|-----------|
| `ANTHROPIC_API_KEY` | Anthropic console | Soft (503 on AI routes) |
| `GMAIL_OAUTH_CLIENT_ID` | GCP → Credentials | Soft (503 on gmail routes) |
| `GMAIL_OAUTH_CLIENT_SECRET` | GCP → Credentials | Soft (503 on gmail routes) |
| `GMAIL_OAUTH_REDIRECT_URI` | Must be `https://<railway-url>/api/gmail/callback` | Soft (OAuth fails silently) |
| `PLMKR_API_KEY` | `openssl rand -hex 32` | Soft (dev-permissive if unset) |
| `STRIPE_SECRET_KEY` | Stripe → API keys | Soft (billing fails) |
| `STRIPE_WEBHOOK_SECRET` | Stripe → Webhooks | Soft (sig verify fails) |
| `APP_BASE_URL` | Your Railway HTTPS URL | Soft (redirect URLs broken) |

**Hard crash guards — never set these in prod:**

| Variable | Effect if set wrong |
|----------|-------------------|
| `STRIPE_DEV_ALLOW_UNSIGNED=true` + `RAILWAY_ENVIRONMENT` set | `sys.exit(1)` at boot |
| `DATABASE_URL` set + Postgres unreachable + no `DB_FAILOVER_TO_SQLITE=true` | `sys.exit(1)` at boot |

---

## Volume Check

```
Startup log MUST show:   ✓  /data is writable — volume mount OK
If instead you see:      WARNING: /data is NOT writable  →  volume not attached
```

---

## Deep Health Check

```bash
curl -H "X-API-Key: $PLMKR_API_KEY" https://<railway-url>/api/admin/health/deep
```

| Field | Expected in prod |
|-------|-----------------|
| `db_connected` | `true` |
| `auth_enabled` | `true` |
| `anthropic_available` | `true` |
| `stripe_dev_allow_unsigned` | `false` |
| `scheduler_running` | `false` until Part H |
| `gmail_token_valid_for_artists` | `0` until Part F, then `≥ 1` |

---

## Gmail OAuth (Per Artist)

```
1. Open in browser: https://<railway-url>/api/gmail/auth?artist_id=<ARTIST_ID>
2. Artist logs in to Google → grants consent
3. Browser auto-redirects to /api/gmail/callback — no action needed
4. Verify: GET /api/gmail/status?artist_id=<ARTIST_ID>  →  {"connected": true}
```

**Errors:**
| Error | Fix |
|-------|-----|
| `503` on `/api/gmail/auth` | Set all three `GMAIL_OAUTH_*` vars in Railway |
| `redirect_uri_mismatch` | URI in GCP must match `GMAIL_OAUTH_REDIRECT_URI` exactly |
| `403 access_denied` | Add artist email to GCP Test Users |
| `403 Gmail auth expired` (on send) | Re-run step 1 above |

---

## First Pitch Send Test

```bash
# Batch send (1 curator)
curl -X POST https://<railway-url>/api/pitches/batch \
  -H "X-API-Key: $PLMKR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"artist_id":"<ID>","curator_ids":["<CUR_ID>"],"track_metadata":{"name":"Test"}}'

# Success:   {"sent":1,"failed":0,"errors":[],"pitch_ids":["..."]}
# Gmail err: {"sent":0,"failed":1,"errors":["Gmail auth error..."]}  → Part F first
# 503:       Anthropic key missing → set ANTHROPIC_API_KEY
# 429:       Daily quota hit (default 50) → wait until midnight UTC
```

---

## Auth Bypass Paths (No API Key Required)

```
GET  /health
GET  /docs
GET  /redoc
GET  /openapi.json
OPTIONS  *
```
All other routes require `X-API-Key` header when `PLMKR_API_KEY` is set.

---

## Key Code Locations

| Item | File:Line |
|------|-----------|
| PLMKR_API_KEY auth middleware | `main.py:912` |
| Stripe prod guard (sys.exit) | `main.py:~1835` |
| Postgres failover guard | `main.py` — `_init_pg_connection()` |
| /data writable check | `main.py:850` |
| Gmail auth route | `pitch_service.py:217` |
| Gmail callback route | `pitch_service.py:240` |
| Gmail status route | `pitch_service.py:258` |
| Batch pitch send | `pitch_service.py:771` |
| Daily quota check | `pitch_service.py:726` |
| Inbox scan (reply detect) | `pitch_service.py:922` |
| Deep health endpoint | `admin_service.py:190` |
| Security posture dict | `admin_service.py:171` |
