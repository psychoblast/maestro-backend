# PLMKR — Seed Data Guide

All seed data is for local development and staging only. Production guard blocks
both scripts if `RAILWAY_ENVIRONMENT=production`.

---

## Scripts

### `scripts/seed_curators.py`

Loads `data/curators_seed.json` (50 placeholder curators, tiers A/B/C) and inserts
them into the `curators` table. Idempotent — existing IDs are skipped.

```bash
DB_PATH=./dev.db python3 scripts/seed_curators.py
```

**Before going live:** every `contact_email` in the seed file is a placeholder
(`curator-a-001@example.com`). Replace with real addresses before sending any pitches.

### `scripts/seed_test_pitch_data.py`

Seeds 3 test artists, 3 test curators, 4 test pitches (draft/sent/replied states),
and 2 pitch interactions. All IDs are prefixed `test-` for easy identification.

```bash
DB_PATH=./dev.db python3 scripts/seed_test_pitch_data.py
```

Use this after a fresh DB init to populate realistic state for local UI testing
without running the full pipeline.

**Purge test records:**
```sql
DELETE FROM pitch_interactions WHERE pitch_id LIKE 'test-%';
DELETE FROM pitches   WHERE id LIKE 'test-%';
DELETE FROM curators  WHERE id LIKE 'test-%';
DELETE FROM artists   WHERE artist_id LIKE 'test-%';
```

---

## Seed file: `data/curators_seed.json`

50 entries. Schema:

| Field | Type | Notes |
|-------|------|-------|
| id | string | `cur-a-001` … `cur-c-020` |
| name | string | Fake name |
| outlet | string | Spotify Editorial, blog, newsletter, etc. |
| genres | array | e.g. `["indie pop", "alternative"]` |
| tier | string | A (premium), B (mid), C (emerging) |
| contact_email | string | Placeholder — replace before going live |
| notes | string | Curator preferences / focus |
| response_rate | float | 0.0 at seed time; updated by `detect_replies()` |

Tier distribution: 10 × A, 20 × B, 20 × C.

---

## Production guard

Both scripts check `RAILWAY_ENVIRONMENT` at startup:

```python
if os.environ.get("RAILWAY_ENVIRONMENT", "").lower() == "production":
    sys.exit(1)
```

Railway automatically sets `RAILWAY_ENVIRONMENT=production` in production deployments.
The guard prevents accidental data corruption when running scripts via Railway shell.

---

## Other data files

| File | Purpose |
|------|---------|
| `data/booking_contacts_seed.json` | Venue contacts for booking_service |
| `data/pr_contacts_seed.json` | Press contacts for pr_service |

These use the same format and should be seeded via equivalent scripts when
booking/PR seed scripts are built (Phase 2).
