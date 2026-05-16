# PLMKR — Phase 4 Frontend Deferred

**Last updated:** 2026-05-15 (S8)

---

## What Phase 4 is

Phase 4 is iOS / App Store — the native mobile app that artists use to interact with their
Playmaker agents (Marcus, Quinn, Avery, Riley, and 16 others), manage outreach, review reports,
and receive push notifications about pitch replies, PR interest, and booking confirmations.

---

## What was built tonight (S8 Unit 4 — backend-only)

The backend foundation for Phase 4 is complete. All endpoints are in `phase4_service.py`:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/devices/register` | Artist registers iOS/Android device token |
| `GET  /api/devices` | List registered tokens for an artist |
| `POST /api/notifications/send` | Internal — other services call this to push alerts |
| `GET  /api/app/config` | Returns version requirements, feature flags, kill-switches, support URLs |
| `POST /api/app/version-check` | App sends its version; backend replies: ok / soft_update / hard_update_required |
| `POST /api/iap/validate-receipt` | Apple receipt validation stub for App Store compliance |

**Feature flags (all default false):**
- `APNS_LIVE=false` — APNs stub enabled; set to `true` + `APNS_CERT_PATH` when cert available
- `FCM_LIVE=false` — FCM stub enabled; set to `true` + `FCM_SERVER_KEY` when key available
- `IAP_LIVE=false` — Apple receipt validation stub; Stripe remains primary billing rail

**17 backend tests** — all passing. Backend is ready when the frontend session resumes.

---

## Why frontend work is NOT done tonight

Frontend work lives in `~/Desktop/ReveNation/` — a **separate repository**, separate product
(RÊVE NATION / React Native), separate entity (Mind Vision LLC), and requires a separate Claude
Code session with different rules. Do not conflate with PLMKR (Marquis Holdings LLC, `~/maestro/`).

Tonight's session scope: PLMKR backend `~/maestro/` only.

---

## What the frontend session needs to cover

When a dedicated frontend session opens for Phase 4:

### 1. Device token capture + registration
- Install a push notification library (e.g., `react-native-push-notification` or Expo's `expo-notifications`)
- Request push notification permission on app launch (iOS: must request explicitly)
- On permission granted: capture device token and POST to `/api/devices/register`
- Handle token refresh (tokens can change; re-register on each app launch)

### 2. Push notification handling
- Handle foreground notifications: display in-app alert with title + body
- Handle background notifications: navigate to relevant screen on tap
- Handle notification data payload: route to pitch reply, PR reply, or booking update screen

### 3. App config consumption
- On app launch: fetch `GET /api/app/config`
- Respect `feature_flags` — disable UI elements for features with `false` flags
- Respect `kill_switches` — emergency disable of specific features without a release
- Cache config locally with a TTL (e.g., 1 hour) to reduce cold-start latency

### 4. Version check integration
- On app launch (after config fetch): POST to `/api/app/version-check` with current app version
- `ok` → proceed normally
- `soft_update` → show non-blocking "Update available" banner
- `hard_update_required` → show blocking modal with link to App Store; disable all features

### 5. IAP integration (if applicable)
- If subscription tiers are sold via the App Store (vs. Stripe web billing): integrate StoreKit 2
- On purchase: POST receipt to `/api/iap/validate-receipt`
- Apple takes 15-30% cut — compare with Stripe's 2.9% + 30¢ before enabling
- Stripe web billing path (current): user pays via browser checkout, no App Store cut

### 6. App Store assets
- Screenshots for each device size (iPhone 6.7", 6.5", 5.5"; iPad 12.9")
- App name, subtitle, description, keywords (ASO)
- Privacy policy URL: `https://playmaker.app/privacy` (already in app config)
- Data safety form (Google Play) and privacy labels (Apple App Store)
- Age rating questionnaire

### 7. TestFlight setup
- Create App Store Connect app record
- Upload first build via Xcode or `fastlane`
- Invite internal testers (Tommy + QA)
- External TestFlight group after first internal green

### 8. App Store submission
- Complete review information (demo account, notes to reviewer)
- Select release type (manual vs. automatic after approval)
- Plan review timeline (Apple: 1-3 business days, sometimes longer for new apps)

---

## Estimated frontend sessions to App Store submission

| Phase | Estimated sessions | Notes |
|-------|--------------------|-------|
| Device token + push integration | 1-2 | React Native push library + permission flow |
| App config + version check | 0.5 | Straightforward API consumption |
| IAP (if needed) | 1-2 | StoreKit 2 is complex; skip if Stripe-only |
| App Store assets + metadata | 1 | Screenshots, descriptions, privacy labels |
| TestFlight + submission | 1 | Build upload, reviewer notes, submission |
| **Total** | **4-7 sessions** | TBD once scope is confirmed |

These are rough estimates. The actual count depends on:
- Whether existing ReveNation codebase is used as the base or a fresh RN project
- Whether IAP is required (adds 2 sessions)
- App review feedback cycles

---

## Session entry point for frontend work

When the frontend session opens, read these first:
1. `docs/PHASE_4_FRONTEND_DEFERRED.md` — this file
2. `docs/API_REFERENCE.md` — all backend endpoints including Phase 4
3. `phase4_service.py` — Phase 4 backend implementation (stubs + flags)
4. `.env.example` — APNS_LIVE, FCM_LIVE, IAP_LIVE flag docs

The backend is production-ready for Phase 4. No code changes to `~/maestro/` should be
necessary before App Store submission.
