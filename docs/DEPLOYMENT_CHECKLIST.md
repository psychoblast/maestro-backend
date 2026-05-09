# PLMKR Deployment Checklist

Use this checklist before every Railway deployment. Work top-to-bottom.

---

## 1. Environment Variables

Set these on Railway (Settings → Variables). Never commit real values to Git.

### Required (all phases)
| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS (paid Starter) | `sk_...` |
| `DB_PATH` | SQLite DB path on persistent volume | `/data/memory.db` |
| `AUDIO_CACHE_DIR` | TTS audio cache on persistent volume | `/data/audio_cache` |

### Required for Phase 1 (Gmail)
| Variable | Description |
|----------|-------------|
| `GMAIL_OAUTH_CLIENT_ID` | Google Cloud OAuth client ID |
| `GMAIL_OAUTH_CLIENT_SECRET` | Google Cloud OAuth client secret |
| `GMAIL_OAUTH_REDIRECT_URI` | `https://YOUR-RAILWAY-URL/api/gmail/callback` |

### Optional
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Railway PostgreSQL URL — artist profiles use Postgres instead of SQLite |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary for agent photo redirects |
| `TWILIO_ACCOUNT_SID` | Twilio for SMS OTP |
| `TWILIO_AUTH_TOKEN` | Twilio auth token (32 lowercase hex chars) |
| `TWILIO_PHONE_NUMBER` | Twilio phone number |
| `STRIPE_SECRET_KEY` | Stripe billing |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signature verification |
| `OPENAI_API_KEY` | Backup TTS only |
| `BUFFER_CLIENT_ID` | Buffer OAuth client ID |
| `BUFFER_CLIENT_SECRET` | Buffer OAuth client secret |
| `BUFFER_REDIRECT_URI` | `https://YOUR-RAILWAY-URL/api/buffer/callback` |
| `SCHEDULER_ENABLED` | `true` to enable APScheduler (inbox polling + weekly reports) |

---

## 2. Railway Volume

Railway persistent volume must be mounted at `/data`. Without it:
- SQLite DB resets on every deploy (artist profiles lost)
- TTS audio cache lost on every deploy

Verify in Railway Dashboard → your service → Settings → Volumes → `/data`.

---

## 3. Pre-Deploy Checks

```bash
# Run all tests locally before pushing
python3 -m pytest tests/ -v --ignore=tests/integration/
python3 -m pytest tests/integration/ -v

# Confirm no uncommitted changes
git status

# Confirm you're on main
git branch --show-current
```

---

## 4. Deploy

```bash
git push origin main
# Railway auto-deploys if GitHub is connected.
# Watch Railway Logs for startup errors.
```

Expected startup log sequence:
```
[PITCH] SQLite pitch tables ready
[PR] SQLite PR tables ready
[Booking] SQLite booking tables ready
[Social] SQLite social + report tables ready
```

---

## 5. Post-Deploy Smoke Tests

Run these curl commands immediately after deploy. Replace `$BASE` with your Railway URL.

```bash
BASE="https://YOUR-RAILWAY-URL"

# Health check
curl $BASE/health
# Expected: {"status":"ok"}

# Gmail auth status (should be not connected until OAuth flow)
curl "$BASE/api/gmail/status?artist_id=YOUR_ARTIST_ID"
# Expected: {"connected": false}

# List curators (empty on fresh deploy)
curl "$BASE/api/curators"
# Expected: {"curators": []}

# Seed curators
curl -X POST "$BASE/api/curators/seed"
# Expected: {"seeded": 50, "skipped": 0}

# Generate a pitch (requires artist in DB and Gmail connected)
curl -X POST $BASE/api/pitches/generate \
  -H "Content-Type: application/json" \
  -d '{"artist_id":"YOUR_ARTIST_ID","curator_id":"CURATOR_UUID"}'
# Expected: {"subject":"...","body":"..."}
```

---

## 6. First-Time Setup (new Railway instance)

1. **Set all required env vars** (Section 1 above)
2. **Mount `/data` volume** (Section 2 above)
3. **Deploy** (`git push origin main`)
4. **Seed curators**: `POST /api/curators/seed`
5. **Seed PR contacts**: `POST /api/pr-contacts/seed`
6. **Seed booking contacts**: `POST /api/booking-contacts/seed`
7. **Replace placeholder emails**: Update all `@example.com` addresses in the DB with real contacts before sending any email
8. **Connect Gmail**: Artist visits `GET /api/gmail/auth?artist_id=YOUR_ARTIST_ID` in a browser
9. **Test pitch send**: `POST /api/pitches/batch` with one curator
10. **Enable scheduler** (optional): Set `SCHEDULER_ENABLED=true` and redeploy

---

## 7. Rollback Plan

If a deploy breaks production:

```bash
# Find the last good commit
git log --oneline -10

# Revert to it (creates a new commit, safe for main)
git revert HEAD --no-edit
git push origin main

# OR force-reset to a specific commit (destructive — confirm with team first)
git reset --hard <good-commit-sha>
git push origin main --force
```

Railway will auto-redeploy from the push.

---

## 8. Key Things That Can Go Wrong

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `GmailNotConnected` errors | Artist hasn't done OAuth | Artist visits `/api/gmail/auth?artist_id=...` |
| `GmailAuthExpired` errors | Access token expired, refresh failed | Artist re-does OAuth flow |
| `sqlite3.OperationalError: no such table` | DB not initialized or wrong volume mount | Check `/data` volume is mounted; restart service |
| 503 on `/api/gmail/auth` | `GMAIL_OAUTH_*` env vars not set | Add vars on Railway, redeploy |
| `[SCHEDULER] ...` not in logs | `SCHEDULER_ENABLED` not set | Set env var to `true` and redeploy |
| Claude 500 errors | `ANTHROPIC_API_KEY` invalid or rate-limited | Check key; wait and retry |
| Audio cache filling up | `/data/audio_cache` not cleaned | Railway admin: `rm /data/audio_cache/*.mp3` |
