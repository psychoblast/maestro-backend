# PLMKR Admin Dashboard

## What it is

A server-rendered, single-page HTML monitoring console served at `GET /admin/dashboard`.
It consumes the 6 existing admin diagnostic endpoints via in-page vanilla JS with no build step,
no npm, and no external JS framework.

---

## How to access

### In a browser (development — no `PLMKR_API_KEY` set)

Navigate directly: `http://localhost:8000/admin/dashboard`

When `PLMKR_API_KEY` is not set the `_APIKeyMiddleware` runs in dev-permissive mode — all
routes are open without a key.

### In a browser (production — `PLMKR_API_KEY` set)

The route itself returns 401 without a valid `X-API-Key` header. Two options:

1. **Browser extension** (e.g. ModHeader for Chrome) — add `X-API-Key: <your-key>` as a
   permanent header, then navigate to the URL. The page loads and the JS key-prompt modal
   pre-fills from `sessionStorage`.

2. **Key prompt modal** — on first load the page shows a modal asking for the API key.
   Enter the key; the JS stores it in `sessionStorage` (cleared on tab close) and uses it
   as the `X-API-Key` header on all subsequent in-page API fetches. The browser still needed
   a valid key to serve the HTML — that's handled by the extension or a direct curl → browser
   workflow.

---

## What each section shows

| Section | Endpoint consumed | Refresh |
|---------|------------------|---------|
| **Diagnostics** | `GET /api/admin/diagnostics` | every 30 s |
| **Performance** | `GET /api/admin/diagnostics/performance` | every 30 s |
| **Anthropic API Usage** | `GET /api/admin/diagnostics/anthropic-stats` | every 30 s |
| **Gmail API Usage** | `GET /api/admin/diagnostics/gmail-stats` | every 30 s |
| **Scheduler Queue** | `GET /api/admin/diagnostics/scheduler` | every 30 s |
| **Deep Health** | `GET /api/admin/health/deep` | every 30 s |

### Diagnostics
Full runtime snapshot: env-var SET/MISSING status (never values), service integration flags,
Python/SQLite/FastAPI versions, `/data` volume writability + free space, scheduler running state,
and the last 20 error log entries from the in-memory ring buffer.

### Performance
Per-route p50/p95/p99 latency percentiles (rolling last 1 000 requests per route). Table headers
are click-sortable.

### Anthropic API Usage
Per-model call counters: total, success, retry, fail. Sum row at the bottom for the session total.

### Gmail API Usage
Per-artist Gmail call counters: total, success, retry, fail. Sum row at the bottom.

### Scheduler Queue
- Next 10 pending `campaign_actions` (action type, scheduled time)
- Last 20 completed actions (status, executed at, result JSON)
- 24-hour status counts by status value

### Deep Health
DB connected, scheduler running, Gmail/Buffer token counts, disk usage %, auth mode,
and security-posture flags. Status shown as green OK / red ERR badge.

---

## Controls

| Control | Behaviour |
|---------|-----------|
| **Pause** toggle | Stops the 30-second auto-refresh timer; resume re-arms it immediately |
| **Sign out** | `window.confirm` → clears the key from `sessionStorage` → shows the key-prompt modal |
| **Last refreshed** counter | Updates every second showing "Xs ago" |

---

## Auth flow (JS side)

1. On page load, JS checks `sessionStorage.getItem('plmkr_admin_key')`.
2. If absent → shows the key-prompt modal.
3. Every `apiFetch()` call sends the stored key as `X-API-Key`.
4. On 401 or 403 response → `clearKey()` + `showModal()` — user must re-enter the key.

`/api/admin/health/deep` is in `_SKIP_AUTH_PATHS` and requires no key; `loadHealth()` uses
bare `fetch()` not `apiFetch()`.

---

## Known limitations

- **Browser navigation barrier**: the route requires `X-API-Key` on the page-load GET request,
  so a browser extension (ModHeader) or a Cloudflare Access tunnel (mTLS) is needed in
  production. A future `/admin/login` HTML form POST could exchange a password for a
  session cookie and remove this friction (tracked in RISK_REGISTER.md R-31).
- **No WebSocket push**: data is polled every 30 s. High-frequency events may be missed in
  the between-poll window.
- **Version hardcoded**: footer reads `v0.1`. Update when a `PLMKR_VERSION` env var or
  build-time injection exists.
- **No chart rendering**: metrics are shown as plain numbers/tables. A future unit could add
  a lightweight charting library (Chart.js CDN, no build step required).

---

## File locations

| File | Purpose |
|------|---------|
| `static/admin_dashboard.html` | Full dashboard HTML + CSS + JS (single file, ~600 lines) |
| `admin_service.py` | FastAPI route `GET /admin/dashboard` serving the static file |
| `tests/test_admin_dashboard.py` | 40 tests covering auth, structure, JS behaviour, and accessibility |
| `docs/API_REFERENCE.md` | Route documented under the `admin` tag |

---

## Future ideas

- `/admin/login` form → session cookie (removes browser-extension requirement)
- WebSocket push for real-time error log streaming
- Chart.js latency sparklines (CDN import, no build step)
- Dark/light mode toggle
- PLMKR_VERSION env var wired into footer at boot
