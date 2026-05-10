# PLMKR Backend — Fresh Machine Setup

## Repository

This repo lives on the **psychoblast** GitHub account.

- Repo: `psychoblast/maestro-backend`
- Working directory: `~/maestro/`

---

## SSH Configuration (Required)

This repo requires a dedicated SSH key and host alias.
Cloning or pushing without this config will fail or push to the wrong account.

### 1. Key location

```
~/.ssh/id_ed25519_psychoblast      # private key
~/.ssh/id_ed25519_psychoblast.pub  # public key
```

If the key does not exist on the new machine, either copy it from a trusted source
or generate a new one and register the public key (see step 3).

### 2. Add the host alias to `~/.ssh/config`

```
Host github-psychoblast
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_psychoblast
    IdentitiesOnly yes
```

### 3. Register the public key on GitHub

The SSH public key **must** be registered on the **psychoblast** GitHub account,
NOT on mindvisionllc or any other account.

1. Copy the public key:
   ```bash
   cat ~/.ssh/id_ed25519_psychoblast.pub
   ```
2. Go to: github.com → (psychoblast account) → Settings → SSH and GPG keys → New SSH key
3. Paste the key and save.

### 4. Test the connection

```bash
ssh -T git@github-psychoblast
```

Expected output: `Hi psychoblast! You've successfully authenticated...`

---

## Clone

```bash
git clone git@github-psychoblast:psychoblast/maestro-backend.git ~/maestro
```

The remote URL must use the alias `github-psychoblast`, not `github.com`.

---

## Verify remote after clone

```bash
git -C ~/maestro remote -v
```

Expected:
```
origin  git@github-psychoblast:psychoblast/maestro-backend.git (fetch)
origin  git@github-psychoblast:psychoblast/maestro-backend.git (push)
```

If the remote shows `github.com` instead of `github-psychoblast`, fix it:

```bash
git remote set-url origin git@github-psychoblast:psychoblast/maestro-backend.git
```

---

## Notes

- The SSH alias is load-bearing. All push/pull commands depend on it.
- Do not use HTTPS remotes — token auth is not configured for this account.
- The frontend lives at `~/Desktop/ReveNation/` — separate repo, separate session.
