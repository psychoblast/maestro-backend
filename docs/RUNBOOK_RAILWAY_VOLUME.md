# Runbook — Railway Persistent Volume Setup (R-02)

**Risk:** Without a persistent volume, every Railway redeploy wipes the `/data` directory,
destroying the SQLite database, Gmail OAuth tokens, and all operational records.

**Applies to:** Production Railway deploys. Local dev uses the host filesystem.

---

## What Is and Isn't Staged Automatically

| Item | Status | Notes |
|------|--------|-------|
| Startup warning when `/data` unwritable | **Staged** (`main.py`) | Fires on every cold start if volume absent |
| `railway.toml` mount path declaration | **Staged** | Tells Railway where to mount once volume exists |
| Volume creation | **Manual** | Dashboard only — Railway does not support declarative volume creation via config files |

---

## Manual Step: Create the Volume in Railway Dashboard

Do this once per deployment environment (production, staging):

1. Log in to [Railway Dashboard](https://railway.app/)
2. Open your project → select the **maestro-backend** service
3. Go to **Settings** tab → scroll to **Volumes**
4. Click **Add Volume**
5. Set:
   - **Volume name:** `plmkr-data`
   - **Mount path:** `/data`
   - **Size:** `1 GB` (increase later if audio cache grows)
6. Click **Create** — Railway will redeploy automatically
7. Verify: check startup logs for `✓  /data is writable — volume mount OK`

---

## Verify the Volume Is Working

After the volume is mounted, test that data survives a redeploy:

```bash
# Write a record, redeploy, read it back
curl -s https://<your-railway-url>/health   # confirm app is live
# Check logs: "✓  /data is writable" must appear
```

Then redeploy (push a trivial commit or use "Redeploy" in dashboard) and confirm:
- The startup log still shows `✓  /data is writable`
- Artist profiles and pitch records are intact (check `/api/admin/health/deep`)

---

## What `railway.toml` Stages

`railway.toml` at the repo root declares the mount path so Railway knows where to attach the
volume once it is created via the dashboard:

```toml
[[mounts]]
mountPath = "/data"
```

This is a declaration of intent, not a creation command. Railway will attach any configured volume
to this path automatically on deploy — but the volume must exist in the dashboard first.

---

## Long-Term Recommendation

SQLite on a Railway volume is fine for early-stage use (< 10k artist records, < 1k concurrent
users). When you scale:

1. Add a **Railway Postgres** add-on — set `DATABASE_URL` env var
2. Migrate `memory.db` artist profiles to Postgres (artist CRUD already checks `DATABASE_URL`)
3. Keep the volume for audio cache only (`AUDIO_CACHE_DIR=/data/audio_cache`)

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Startup log shows `WARNING: /data is NOT writable` | Volume not created or wrong mount path | Follow manual steps above |
| Data disappears after redeploy | Volume exists but wrong mount path | Dashboard: check volume mount path is exactly `/data` |
| `sqlite3.OperationalError: unable to open database` | `/data` unwritable | Volume not mounted — see above |
| Artist re-authorizes Gmail after every deploy | No volume — tokens stored in `/data` DB | Mount volume, then re-authorize once |
