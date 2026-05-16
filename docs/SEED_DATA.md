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

### `scripts/seed_pr_contacts.py`

Loads `data/pr_contacts_seed.json` (40 press contacts, tiers A/B/C) and inserts
them into the `pr_contacts` table. Idempotent — existing IDs are skipped.

```bash
DB_PATH=./dev.db python3 scripts/seed_pr_contacts.py
```

**Before going live:** every `contact_email` is a placeholder (`pr-a-001@example.com`).
Replace with real journalist/editor emails before sending any pitches.

### `scripts/seed_venues.py`

Loads `data/booking_contacts_seed.json` (30 booking contacts — venues, festivals, promoters)
and inserts them into the `booking_contacts` table. Idempotent — existing IDs are skipped.

```bash
DB_PATH=./dev.db python3 scripts/seed_venues.py
```

**Before going live:** every `contact_email` is a placeholder (`bk-a-001@example.com`).
Replace with real booker/promoter emails before sending any inquiries.

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

## Seed file: `data/pr_contacts_seed.json`

40 entries across magazine, blog, podcast, newsletter, and radio outlets. Schema:

| Field | Type | Notes |
|-------|------|-------|
| id | string | `pr-a-001` … `pr-c-010` |
| name | string | Journalist/editor name |
| outlet_type | string | `magazine`, `blog`, `podcast`, `newsletter`, `radio` |
| outlet_name | string | Publication name (Pitchfork, NME, etc.) |
| genres | array | e.g. `["indie", "alternative", "electronic"]` |
| tier | string | A (national/global), B (regional/specialist), C (emerging) |
| contact_email | string | Placeholder — replace before going live |
| beat | string | Editorial focus (e.g. "Best New Music, Reviews, Features") |
| notes | string | Pitch preferences and lead times |
| response_rate | float | 0.0 at seed time; updated by `detect_pr_replies()` |

Tier distribution: 10 × A, 15 × B, 15 × C.

---

## Seed file: `data/booking_contacts_seed.json`

30 entries across venues, festivals, and promoters in major markets. Schema:

| Field | Type | Notes |
|-------|------|-------|
| id | string | `bk-a-001` … `bk-c-010` |
| name | string | Booker/promoter name |
| venue_or_festival | string | Venue or event name |
| type | string | `venue`, `festival`, `promoter` |
| city | string | City |
| country | string | Country code (US, UK, etc.) |
| capacity | integer | Max capacity |
| genres | array | e.g. `["indie", "rock", "electronic"]` |
| tier | string | A (major), B (mid-size), C (emerging) |
| contact_email | string | Placeholder — replace before going live |
| notes | string | Booking window, requirements |
| response_rate | float | 0.0 at seed time; updated by `detect_booking_replies()` |

Tier distribution: 10 × A, 10 × B, 10 × C.

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

| File | Script | Purpose |
|------|--------|---------|
| `data/curators_seed.json` | `seed_curators.py` | Playlist curators for pitch_service |
| `data/pr_contacts_seed.json` | `seed_pr_contacts.py` | Press contacts for pr_service |
| `data/booking_contacts_seed.json` | `seed_venues.py` | Booking contacts for booking_service |
