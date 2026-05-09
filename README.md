# PLMKR — Playmaker

AI-powered artist management platform. Agents take real-world action — no advice-only bots.

## What It Does

Playmaker gives artists a team of AI agents that actually do the work:

- **Marcus** (Artist Manager) — orchestrates strategy and agent handoffs
- **Quinn** (PR Manager) — pitches press contacts, tracks coverage
- **Avery** (Booking Agent) — inquires with venues, tracks replies
- **Riley** (Social Manager) — drafts and schedules social posts
- Plus 39 more specialist agents (legal, royalties, finance, visuals, etc.)

All outreach agents connect to the artist's Gmail account and send real emails. Replies are scanned, classified by Claude, and surfaced in weekly reports.

## Phase Status

| Phase | What's Built | Status |
|-------|-------------|--------|
| Phase 0 | 43 voice agents, TTS, SQLite persistence, ElevenLabs, Stripe billing | Live on Railway |
| Phase 1 | Gmail OAuth, curator pitching, inbox scanning, follow-ups | Local — needs deploy |
| Phase 2 | PR outreach, booking inquiries, unified inbox scan | Local — needs deploy |
| Phase 3 | Social post scheduling (Buffer), weekly AI reports | Local — needs deploy |

## Architecture

```
main.py                   FastAPI app — agent chat, TTS, billing
pitch_service.py          Phase 1: Gmail + curator pitches
pr_service.py             Phase 2a: PR contacts + outreach
booking_service.py        Phase 2b: Booking contacts + inquiries
booking_service.py        /api/inbox/scan-all  (unified scan)
social_service.py         Phase 3: Social posts + weekly reports

data/
  curators_seed.json      50 curator contacts
  pr_contacts_seed.json   40 PR contacts
  booking_contacts_seed.json  30 booking contacts

skills/maestro-*/SKILL.md  Agent skill definitions
tests/
  test_pitch_service.py   Phase 1 unit tests (15 tests)
  test_pr_service.py      Phase 2a unit tests (10 tests)
  test_booking_service.py Phase 2b unit tests (11 tests)
  test_social_service.py  Phase 3 unit tests (8 tests)
  test_reports.py         Weekly report unit tests (6 tests)
  integration/            End-to-end lifecycle tests (6 tests)

docs/
  API_REFERENCE.md        Complete endpoint inventory
  DEPLOYMENT_CHECKLIST.md Railway deploy checklist + smoke tests
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set required env vars
export ANTHROPIC_API_KEY=sk-ant-...
export DB_PATH=/tmp/plmkr_dev.db

# Run the API
uvicorn main:app --reload

# Run tests
python3 -m pytest tests/ -v

# Run integration tests only
python3 -m pytest tests/integration/ -v
```

## Deploy to Railway

See [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) for the full checklist.

Quick path:
1. Push to `main` → Railway auto-deploys
2. Set env vars (Railway → Settings → Variables)
3. Mount `/data` volume for persistence
4. Seed contacts: `POST /api/curators/seed`, `/api/pr-contacts/seed`, `/api/booking-contacts/seed`
5. Artist connects Gmail: `GET /api/gmail/auth?artist_id=ARTIST_ID`

## API Documentation

- Interactive Swagger UI: `https://YOUR-RAILWAY-URL/docs`
- ReDoc: `https://YOUR-RAILWAY-URL/redoc`
- Endpoint inventory: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

## Key Env Vars

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API |
| `ELEVENLABS_API_KEY` | Yes | TTS (paid Starter plan) |
| `DB_PATH` | Yes | SQLite path (set to `/data/memory.db` on Railway) |
| `GMAIL_OAUTH_CLIENT_ID` | Phase 1+ | Google Cloud OAuth |
| `GMAIL_OAUTH_CLIENT_SECRET` | Phase 1+ | Google Cloud OAuth |
| `GMAIL_OAUTH_REDIRECT_URI` | Phase 1+ | `https://YOUR-URL/api/gmail/callback` |
| `SCHEDULER_ENABLED` | Optional | `true` to enable inbox polling + weekly reports |
| `DATABASE_URL` | Optional | Railway PostgreSQL — artist profiles use Postgres |

Full list: [.env.example](.env.example) and [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md).
