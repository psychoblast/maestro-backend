# PLMKR — Local Development Guide

**Project:** PLMKR Backend (`~/maestro/`)
**Language:** Python 3.12
**Owner:** Marquis Holdings LLC (NM) — Tommy Lam <mypsychoblast@gmail.com>

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | **3.12** | Match the Dockerfile `FROM python:3.12-slim`. 3.11 may work but is untested. |
| ffmpeg | system | Required by OpenAI Whisper for audio decoding. |
| libsndfile1 | system | Required by `soundfile` Python package. |
| build-essential | system | C compiler needed for some native extensions. |
| git | any | For branch workflow. |

### Install system deps (Ubuntu/Debian — matches Railway image)

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg libsndfile1 build-essential
```

### Install system deps (macOS — for the Mac Mini dev machine)

```bash
brew install ffmpeg libsndfile
```

---

## Cloning and First Run

```bash
# Clone (SSH — use the configured host alias)
git clone git@github-psychoblast:psychoblast/maestro-backend.git maestro
cd maestro

# Set your git identity for this repo (one-time)
git config --local user.name "tommy"
git config --local user.email "mypsychoblast@gmail.com"

# Create a Python virtual environment
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install --no-cache-dir -r requirements.txt
```

> **Note on sentry-sdk:** `requirements.txt` includes `sentry-sdk[fastapi]`. Without `SENTRY_DSN` set, it is a no-op — no Sentry account needed for local dev.

> **Note on Kokoro TTS:** `requirements.txt` includes `kokoro-onnx`. The model files (`kokoro-v1.0.onnx`, `voices-v1.0.bin`) are large and **not in the repo**. If you don't have them locally, Kokoro silently falls back to ElevenLabs (R-19 fix). No action needed for local dev without Kokoro files.

---

## .env.local Setup

Copy the public template and fill in the values you need:

```bash
cp .env.example .env.local
# Edit .env.local with your editor
```

### Required for local dev (absolute minimum)

```bash
# .env.local
DB_PATH=./memory.db          # local SQLite file (not /data)
DATABASE_URL=                # leave empty to use SQLite
AUDIO_CACHE_DIR=./audio_cache
ARTISTS_DIR=./data/artists
PLMKR_API_KEY=               # leave empty for dev-permissive mode (no auth enforced)
ANTHROPIC_API_KEY=sk-ant-... # required for AI route testing
```

### Optional — enable feature areas

```bash
GMAIL_OAUTH_CLIENT_ID=...
GMAIL_OAUTH_CLIENT_SECRET=...
GMAIL_OAUTH_REDIRECT_URI=http://localhost:8765/api/gmail/callback

ELEVENLABS_API_KEY=...      # TTS; falls back to local Kokoro or 503 if absent
STRIPE_SECRET_KEY=sk_test_... # billing routes
SCHEDULER_ENABLED=false     # keep false locally unless testing scheduler
```

### Vars to leave unset locally

```bash
# DATABASE_URL   — leave empty; triggers SQLite path
# RAILWAY_ENVIRONMENT — Railway injects this; never set locally (changes log format to JSON)
# STRIPE_DEV_ALLOW_UNSIGNED — NEVER set this; Railway guard sys.exit()s on it
# SENTRY_DSN     — leave empty; Sentry no-ops silently
```

Load `.env.local` before starting the server:

```bash
export $(grep -v '^#' .env.local | xargs)
```

Or use `direnv` with a `.envrc` that sources `.env.local`.

---

## Running the Server Locally

```bash
# With hot reload (development)
uvicorn main:app --host 0.0.0.0 --port 8765 --reload

# Without reload (closer to prod)
python -m uvicorn main:app --host 0.0.0.0 --port 8765
```

The server starts at `http://localhost:8765`. Interactive docs at `http://localhost:8765/docs`.

### First-boot log lines to verify

```
✓  /data is writable — volume mount OK    ← if DATA_DIR points to a writable path
[DB] memory.db ready
[TTS] Kokoro loaded OK                    ← or: [Kokoro] WARNING: ...  (fine if no model files)
[PITCH] SQLite pitch tables ready
[INIT] DB ready, Kokoro warmup thread started, ...
```

### Common startup warnings (expected, not errors)

```
WARNING: /data is NOT writable            ← set DB_PATH=./memory.db, DATA_DIR=./data locally
⚠️  TWILIO_AUTH_TOKEN invalid              ← expected if TWILIO_AUTH_TOKEN not set
[AUTH] WARNING: PLMKR_API_KEY is not set  ← expected in dev-permissive mode
[STRIPE] WARNING: STRIPE_WEBHOOK_SECRET not set  ← expected without Stripe
[error_reporting] no DSN; Sentry disabled ← expected without SENTRY_DSN
```

---

## Running Tests

```bash
# Full test suite (takes ~6–8 minutes)
python3 -m pytest

# Single test file
python3 -m pytest tests/test_pitch_service.py

# Single test by name
python3 -m pytest tests/test_pitch_service.py::test_quota_allows_first_batch

# Unit tests only (skip integration, faster)
python3 -m pytest --ignore=tests/integration

# Integration tests only
python3 -m pytest tests/integration/

# With verbose output
python3 -m pytest -v

# Stop on first failure
python3 -m pytest -x

# Show slowest 20 tests
python3 -m pytest --durations=20
```

> **Suite health target:** All tests green at all times. Never merge to main with failing tests.
> **Test isolation:** All tests use `tmp_path` for SQLite DBs and `monkeypatch` for env vars. No shared state between tests.

---

## Common Gotchas

### `/data` not writable

The app defaults to `/data/memory.db`. Set `DB_PATH=./memory.db` and `ARTISTS_DIR=./data/artists` in `.env.local`. Create the local dirs first:

```bash
mkdir -p data/artists audio_cache static/temp_audio
```

### Whisper model download on first transcription

If `WHISPER_MODEL` is not pre-cached, the first `POST /api/transcribe` request downloads ~140 MB (`openai-whisper` base model). This is expected locally. In production, the Dockerfile pre-bakes the model at build time (R-18 fix).

### SQLite DB location

`DB_PATH` controls where the main database lives. Default is `/data/memory.db` (Railway volume). Locally, set it to `./memory.db` to keep it in the project dir. The file is gitignored.

### `kokoro-v1.0.onnx` not found

If you don't have local Kokoro model files, the app prints:

```
[Kokoro] WARNING: Kokoro model files not found at /path/ (kokoro-v1.0.onnx and/or voices-v1.0.bin). TTS will fall back to ElevenLabs.
```

This is the R-19 fix working as intended. Set `ELEVENLABS_API_KEY` for TTS to work without Kokoro.

---

## Adding a New Service Module

When adding e.g. `my_service.py`:

1. **Create the file** — follow the existing pattern: `import logging; log = logging.getLogger("my_service")`, define a FastAPI `router = APIRouter()`, expose `init_my_db()` for table setup.

2. **Register in main.py** — add two lines near the other service imports:
   ```python
   from my_service import router as _my_router, init_my_db
   app.include_router(_my_router)
   ```
   Then call `init_my_db()` in the startup section.

3. **Add to Dockerfile** — update the `COPY` block:
   ```dockerfile
   COPY main.py anthropic_utils.py logging_config.py error_reporting.py \
        performance_metrics.py my_service.py .
   ```

4. **Tests** — add `tests/test_my_service.py`. All DB tests must use `tmp_path` for isolation.

5. **openapi.json** — regenerate after adding routes:
   ```bash
   python3 -c "
   import os; os.environ.update({'DB_PATH':'/tmp/t.db','DATABASE_URL':'','AUDIO_CACHE_DIR':'/tmp/ac','ARTISTS_DIR':'/tmp/art'})
   import unittest.mock, json
   with unittest.mock.patch('whisper.load_model', return_value=unittest.mock.MagicMock()):
       import main
   with open('docs/openapi.json','w') as f:
       json.dump(main.app.openapi(), f, indent=2); f.write('\n')
   print('Wrote docs/openapi.json —', len(main.app.openapi()['paths']), 'paths')
   "
   ```

---

## Standing Rules

- **Never commit directly to `main`.** Create a feature branch, merge with `--no-ff`, push.
- **One unit of work per branch.** Commit working state, merge, then start the next task.
- **Every code change needs a test.** Run the full suite before merging.
- **Never expose secrets in Git.** All keys via env vars. `.env.local` is gitignored.
- **Verify after every change.** If you can't curl it with real data, it isn't done.
- **`--no-cache` for Docker.** Always rebuild without cache when changing `requirements.txt` or `Dockerfile`.
- **Git author.** First-time clone: `git config --local user.email "mypsychoblast@gmail.com"`.

---

## SSH Setup (if port 22 is blocked)

The dev machine uses SSH over port 443 for GitHub:

```
# ~/.ssh/config
Host github-psychoblast
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/id_ed25519_psychoblast
  IdentitiesOnly yes
```

Test: `ssh -T git@github-psychoblast` → "Hi psychoblast! You've successfully authenticated."

Clone: `git clone git@github-psychoblast:psychoblast/maestro-backend.git`
