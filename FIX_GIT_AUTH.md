# FIX: git push 403 — psychoblast fine-grained PAT lacks Contents:write

## Root Cause

The `psychoblast` account is authenticated via a fine-grained PAT (`github_pat_11B7DJMRQ0...`).
Fine-grained PATs have SEPARATE permissions for:
- GitHub REST API calls (works — token has Metadata:read)
- Git over HTTPS operations (BROKEN — token lacks Contents:write)

`gh auth status` showing no scopes is the tell — classic tokens list scopes, fine-grained PATs don't.
`gh api repos/psychoblast/maestro-backend` returning `push:true` is misleading — that reflects
the *user's* role on the repo, not what the *token* can actually do via git.

## Fix Options (pick one — Option 1 is fastest)

---

### Option 1 — Create a classic PAT (5 minutes, works immediately)

1. Go to: https://github.com/settings/tokens/new?scopes=repo,workflow&description=maestro-push
2. Token Note: `maestro-backend push`
3. Expiration: 90 days (or No expiration if you prefer)
4. Scopes: check **repo** (this covers repo:status, repo:deployment, public_repo, repo:invite, security_events)
5. Click **Generate token** → copy the token immediately (it won't show again)
6. Run: `gh auth login --with-token -h github.com`
   Then paste your new token when prompted.
7. Run: `git push origin main`

---

### Option 2 — Edit the existing fine-grained PAT (adds Contents:write)

1. Go to: https://github.com/settings/personal-access-tokens
2. Find the token starting with `github_pat_11B7DJMRQ0...`
3. Click **Edit**
4. Under **Repository permissions** → **Contents** → change to **Read and write**
5. Click **Save**
6. Run: `git push origin main` (no credential update needed — same token, new permissions)

> Note: GitHub may not allow editing fine-grained PATs after creation depending on when it was created.
> If the Edit button is greyed out or Contents can't be changed, use Option 1.

---

### Option 3 — Add mindvisionllc as collaborator and push via SSH

mindvisionllc already has a working SSH key and full `repo` scope OAuth token.
This just needs you to grant them write access to the repo.

1. Go to: https://github.com/psychoblast/maestro-backend/settings/access
2. Click **Add people** → search `mindvisionllc` → set role to **Write**
3. Accept the invite from mindvisionllc's GitHub account
4. Run: `git push git@github.com:psychoblast/maestro-backend.git main`

---

## After Fixing — Verify

```bash
git push origin main
git log origin/main --oneline -6
```

Expected output: 6 commits from local main now on origin/main.

## Commits Waiting to Push (6 total)

```
9cd90b6  [docs] Phase 1 complete — TODOS + session notes updated
b46ff4c  [1.4] Seed 50 placeholder curators — A/B/C tier across 10 genres
02e0026  [1.2] pitch_service.py — sendEmail() + token refresh + all units 1.1-1.9
3452271  [1.1] Gmail OAuth routes — auth + callback + token storage
55caf76  [docs] Add push blocker note to session notes
7daa27b  [docs] Ignore *.docx — working docs not for version control
```

## Diagnosis Log (what was tried automatically)

| Attempt | Result |
|---------|--------|
| `gh auth refresh --account psychoblast -s repo` | `--account` flag not in gh 2.67.0 |
| `git push https://psychoblast:TOKEN@github.com/...` | 403 — confirms token lacks Contents:write |
| `gh api PUT repos/.../collaborators/mindvisionllc` | 403 — fine-grained PAT lacks admin:repo |
| `gh auth switch` to mindvisionllc | mindvisionllc not a collaborator — cannot push |
| Check `gh api repos/psychoblast/maestro-backend` | Returns `push:true` but this is user role, not token permission |
