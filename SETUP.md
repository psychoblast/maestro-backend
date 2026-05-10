# PLMKR Backend — Fresh Machine Setup

## Repository

This repo is owned by the **psychoblast** GitHub account — NOT mindvisionllc.

- Repo: `psychoblast/maestro-backend`
- Working directory: `~/maestro/`

---

## SSH Configuration (Required)

This repo requires a dedicated SSH key and host alias. Cloning or pushing
without this config will fail, or silently authenticate as the wrong account.

### 1. Key location

```
~/.ssh/id_ed25519_psychoblast      # private key — never share or commit
~/.ssh/id_ed25519_psychoblast.pub  # public key — registered on psychoblast GitHub
```

If the key does not exist on the new machine, copy it from a trusted source
or generate a new one and register the public key (see step 3).

### 2. Add the host alias to `~/.ssh/config`

Open `~/.ssh/config` and add this block exactly (2-space indent, no tabs):

```
Host github-psychoblast
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_psychoblast
  IdentitiesOnly yes
```

`IdentitiesOnly yes` is mandatory — it prevents SSH from offering other
loaded keys (e.g. a mindvisionllc key from ssh-agent) before the right one.

### 3. Register the public key on GitHub

The SSH public key **must** be registered on the **psychoblast** GitHub
account. If it is on mindvisionllc instead, pushes will either be denied
or land on the wrong account.

1. Print the public key (not the private key — `.pub` suffix):
   ```bash
   cat ~/.ssh/id_ed25519_psychoblast.pub
   ```
2. Log in to GitHub as **psychoblast**.
3. Settings → SSH and GPG keys → New SSH key.
4. Paste the public key string and save.

### 4. Test the connection

```bash
ssh -T git@github-psychoblast
```

Expected output:
```
Hi psychoblast! You've successfully authenticated, but GitHub does not
provide shell access.
```

If it says `Hi mindvisionllc!` instead — stop. See the Recovery section below.

---

## Clone

```bash
git clone git@github-psychoblast:psychoblast/maestro-backend.git ~/maestro
```

The remote URL **must** use the alias `github-psychoblast`, not `github.com`.
Using `github.com` bypasses the alias and will authenticate as whatever key
SSH offers first — usually the wrong one.

---

## Verify remote after clone

```bash
git -C ~/maestro remote -v
```

Expected output:
```
origin  git@github-psychoblast:psychoblast/maestro-backend.git (fetch)
origin  git@github-psychoblast:psychoblast/maestro-backend.git (push)
```

If `github.com` appears instead of `github-psychoblast`, fix it before pushing:

```bash
git -C ~/maestro remote set-url origin git@github-psychoblast:psychoblast/maestro-backend.git
```

---

## Recovery — "Permission denied" or "Hi mindvisionllc!"

These are the two failure modes on a fresh or re-imaged machine.

### Symptom A: `git push` returns "Permission denied (publickey)"

SSH cannot find or use the key. Work through these in order:

1. Confirm the key file exists:
   ```bash
   ls -la ~/.ssh/id_ed25519_psychoblast
   ```
   If missing: copy the key from a trusted backup. Do not regenerate unless
   you also re-register the new public key on GitHub.

2. Confirm `~/.ssh/config` has the `Host github-psychoblast` block:
   ```bash
   grep -A 5 "Host github-psychoblast" ~/.ssh/config
   ```
   If missing or different: add/correct the block (see step 2 above).

3. Test the connection in verbose mode to see which key is being tried:
   ```bash
   ssh -Tv git@github-psychoblast 2>&1 | grep -E "Offering|Authenticated|denied"
   ```

4. If the right key is offered but still denied: the public key is not
   registered on the psychoblast GitHub account. Re-do step 3 of
   SSH Configuration above.

### Symptom B: `ssh -T git@github-psychoblast` says "Hi mindvisionllc!"

The alias resolved correctly but the wrong key was used (e.g. a
mindvisionllc key is registered on psychoblast, or `IdentitiesOnly yes`
is missing from the config block).

1. Confirm `IdentitiesOnly yes` is present in `~/.ssh/config`:
   ```bash
   grep -A 6 "Host github-psychoblast" ~/.ssh/config
   ```
   If missing: add it and re-test.

2. If `IdentitiesOnly yes` is present and the key file is correct, the
   mindvisionllc key may also be registered on the psychoblast account.
   Remove it from psychoblast GitHub → Settings → SSH keys.

3. After fixing, re-run:
   ```bash
   ssh -T git@github-psychoblast
   ```
   Must say "Hi psychoblast!" before any push.

---

## Notes

- The SSH alias is load-bearing. Every push/pull in this repo depends on it.
- Do not switch to HTTPS remotes — Personal Access Token auth is not
  configured for this repo.
- The frontend lives at `~/Desktop/ReveNation/` — separate repo, separate
  SSH config concern, separate session.
