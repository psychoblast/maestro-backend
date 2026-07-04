"""
PLMKR Fund-Phantom — grants & funding action service (mock-first).

Backs the Fund-Phantom (Jade — Grants & Funding) agent's tool_use loop in
/api/chat_stream (see FUND_PHANTOM_TOOLS in main.py). Jade does not just advise —
these functions let the agent take real funding actions: search open grant
programs, screen a project for eligibility against a program's rules, and submit
a grant application on the artist's behalf.

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live grant portals, no submission APIs, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_portal_connected``) driven by an env flag so tests can
    toggle the connected / not-connected / expired states deterministically —
    mirroring lex_cipher_service.RegistryNotConnected without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os

from grant_data import GRANT_PROGRAMS


class FundingPortalNotConnected(Exception):
    """Raised when the artist has not connected a funding-portal submission account.

    Mirrors lex_cipher_service.RegistryNotConnected: the tool loop catches this
    and degrades gracefully into a structured 'connect your account first' result
    instead of crashing the stream.
    """


class FundingPortalAuthExpired(Exception):
    """Raised when a previously connected funding-portal account's auth expired."""


class DeadlineLookupUnavailable(Exception):
    """Raised when the live deadline-lookup mechanism isn't connected / enabled.

    Analogous to FundingPortalNotConnected but for the read-only deadline lookup:
    the tool loop / public wrapper catches this and degrades gracefully into a
    'check the official page directly' result instead of crashing — and, crucially,
    instead of inventing a date.
    """


# ── Grant program library ─────────────────────────────────────────────────────
# The real structured grant data now lives in grant_data.GRANT_PROGRAMS (Unit 1b),
# replacing the old hand-invented inline list. The internal name the rest of this
# module uses is kept, so search / _get_program / check_eligibility / submit are
# untouched — the new record fields flow through automatically via dict(p).
_GRANT_PROGRAMS = GRANT_PROGRAMS


async def search_grant_programs(
    genre: str = "",
    region: str = "",
    max_award: int = 0,
    country: str = "",
    track: str = "",
) -> dict:
    """Search open grant programs by country, track, genre, region, and/or ceiling.

    All filters are optional and combine with AND. Pure — no I/O.

    Real (Unit-2) filters, over the structured axes in grant_data:
      - ``country``: exact ISO-ish code match, case-insensitive (e.g. "CA", "UK").
        Records whose ``country`` differs are excluded. (Geography is filtered on
        the structured ``country`` field only — ``residency`` is free text and is
        NEVER parsed as a filter; it rides along as a human-readable note.)
      - ``track``: exact match on ``track`` (industry / arts_council /
        crowdfunding).

    Crowdfunding is situational and is EXCLUDED from normal grant searches: a
    record with track=="crowdfunding" only appears when the caller explicitly
    passes track="crowdfunding".

    Back-compat filters (kept working for existing callers):
      - ``genre`` / ``region`` matched case-insensitively as substrings (programs
        marked "any"/"national" always match).
      - ``max_award`` floors on the legacy ``max_award`` int.

    Returns {"programs": [...], "count": int} with full records via dict(p).
    """
    g = (genre or "").strip().lower()
    r = (region or "").strip().lower()
    c = (country or "").strip().lower()
    t = (track or "").strip().lower()
    try:
        floor = int(max_award or 0)
    except (TypeError, ValueError):
        floor = 0
    matches = []
    for p in _GRANT_PROGRAMS:
        # Crowdfunding stays out of normal searches unless explicitly requested.
        if p.get("track") == "crowdfunding" and t != "crowdfunding":
            continue
        if c and (p.get("country") or "").lower() != c:
            continue
        if t and (p.get("track") or "").lower() != t:
            continue
        if g and g not in p["genre"] and p["genre"] != "any":
            continue
        if r and r not in p["region"] and p["region"] != "national":
            continue
        if floor and p["max_award"] < floor:
            continue
        matches.append(dict(p))
    return {"programs": matches, "count": len(matches)}


def _get_program(program_id: str) -> dict | None:
    pid = (program_id or "").strip()
    for p in _GRANT_PROGRAMS:
        if p["id"] == pid:
            return p
    return None


async def check_eligibility(
    artist_id: str,
    program_id: str = "",
    requested_amount: int = 0,
    project_type: str = "",
) -> dict:
    """Screen a project against a grant program's rules and return an assessment.

    Deterministic keyword/threshold screen — never contacts a wire. Looks the
    program up by id and judges two things against the structured record:

      1. Purpose (project_type): eligible on purpose if no project_type is given,
         OR the project_type is in the program's ``funds`` list. ``focus`` is used
         only as a fallback when a record has no ``funds`` (permissive "any").
      2. Amount: compared against the structured ``amount_max`` when it is known.
         When ``amount_max`` is None (a stub with no listed ceiling) the amount is
         NON-BLOCKING — we cannot judge a cap we do not have — and the result is
         flagged ``amount_unlisted=True`` (verify live) rather than rejected.

    Currency-aware but FX-free: the program's ``currency`` is surfaced so the
    caller never implies cross-currency equivalence; NO conversion is performed.

    Returns a structured eligibility result with a recommendation of
    "apply" / "adjust" / "ineligible".
    """
    program = _get_program(program_id)
    if program is None:
        return {
            "eligible": False,
            "reasons": ["program_not_found"],
            "program_id": (program_id or "").strip(),
            "recommendation": "ineligible",
        }

    try:
        amount = int(requested_amount or 0)
    except (TypeError, ValueError):
        amount = 0
    ptype = (project_type or "").strip().lower()
    currency = program.get("currency", "") or ""

    reasons = []

    # ── Purpose: membership in funds; focus is fallback only when funds absent ──
    funds = program.get("funds") or ()
    if not ptype:
        purpose_mismatch = False
    elif funds:
        purpose_mismatch = ptype not in funds
    else:
        focus = program.get("focus", "any")
        purpose_mismatch = focus != "any" and ptype != focus
    if purpose_mismatch:
        target = list(funds) if funds else program.get("focus", "any")
        reasons.append(
            f"project type '{ptype}' is not in program funds {target}"
        )

    # ── Amount: use structured amount_max; None => unlisted, non-blocking ──
    if "amount_max" in program:
        amount_max = program["amount_max"]
    else:
        amount_max = program.get("max_award")  # legacy fallback only
    amount_unlisted = amount_max is None
    over_cap = (amount_max is not None) and (amount > amount_max)
    if over_cap:
        reasons.append(
            f"requested {amount} exceeds max award {amount_max} {currency}".strip()
        )
    if amount_unlisted and amount:
        reasons.append("amount_unlisted_verify_live")

    # amount_unlisted alone never makes a program ineligible.
    eligible = not (over_cap or purpose_mismatch)
    if eligible:
        recommendation = "apply"
    elif over_cap and not purpose_mismatch:
        recommendation = "adjust"
    else:
        recommendation = "ineligible"

    return {
        "eligible": eligible,
        "reasons": reasons,
        "program_id": program["id"],
        "program_name": program["name"],
        "max_award": program["max_award"],
        "focus": program.get("focus", "any"),
        "recommendation": recommendation,
        # ── additive (Unit 2) — structured axes surfaced for the model ──
        "funds": list(funds),
        "track": program.get("track", ""),
        "country": program.get("country", ""),
        "currency": currency,
        "language": program.get("language", ""),
        "residency": program.get("residency", ""),
        "amount_max": amount_max,
        "amount_unlisted": amount_unlisted,
    }


def _portal_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's funding-portal submission account.

    In production this would look up a stored portal link for the artist. Here it
    is driven purely by the ``FUNDING_PORTAL_CONNECTED`` env flag so tests can
    toggle connected / expired / not-connected with ZERO network calls and NO
    real secret. Values:
      - "expired"                     → raise FundingPortalAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("FUNDING_PORTAL_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise FundingPortalAuthExpired("funding portal authorization expired")
    return val in ("1", "true", "yes", "connected")


async def submit_grant_application(
    artist_id: str,
    program_id: str,
    project_title: str,
    requested_amount: int = 0,
) -> dict:
    """Submit a grant application to a program on behalf of the artist.

    Raises FundingPortalNotConnected / FundingPortalAuthExpired when no submission
    account is linked so the caller can surface a 'connect your account' message
    instead of a hard failure. On success returns a deterministic mock submission
    reference — NO network call is ever made.
    """
    if not _portal_connected(artist_id):
        raise FundingPortalNotConnected(
            "artist has not connected a funding-portal submission account"
        )
    pid   = (program_id or "").strip()
    title = (project_title or "").strip()
    try:
        amount = int(requested_amount or 0)
    except (TypeError, ValueError):
        amount = 0
    digest = hashlib.sha1(f"{artist_id}:{pid}:{title}:{amount}".encode("utf-8")).hexdigest()
    reference = "GA-" + digest[:10].upper()
    return {
        "status": "submitted",
        "reference": reference,
        "program_id": pid,
        "project_title": title,
        "requested_amount": amount,
    }


def suggest_crowdfunding(qualifies_for_grants: bool, complements_grant: bool = False) -> dict:
    """Situational crowdfunding decision (pure, no I/O, no tool wiring).

    Encodes the grant map's rule: crowdfunding is a SECONDARY option, not a
    default. Raise it when the artist does NOT qualify for the available grants
    (a real alternative rather than a dead end), OR when it complements a grant
    (e.g. income that counts toward a matched-funding requirement, or a campaign
    that proves fan demand in an application). Stay quiet when the artist clearly
    qualifies for grants and just needs help landing one — offering crowdfunding
    there is noise.

    Returns {"raise": bool, "reason": str, "platforms": [...]}. The platform list
    (the six crowdfunding records from grant_data) is included only when this
    recommends raising crowdfunding; otherwise it is empty.
    """
    should_raise = (not qualifies_for_grants) or complements_grant
    if not qualifies_for_grants:
        reason = ("artist does not qualify for the available grants — crowdfunding "
                  "is a real alternative")
    elif complements_grant:
        reason = ("crowdfunding complements a grant (matched-funding income / proof "
                  "of fan demand)")
    else:
        reason = ("artist clearly qualifies for grants and just needs to land one — "
                  "raising crowdfunding would be noise")
    platforms = (
        [dict(p) for p in _GRANT_PROGRAMS if p.get("track") == "crowdfunding"]
        if should_raise else []
    )
    return {"raise": should_raise, "reason": reason, "platforms": platforms}


# ══════════════════════════════════════════════════════════════════════════════
# Unit 3 — live deadline lookup (mock-first; real fetch DEFERRED behind the seam)
# ══════════════════════════════════════════════════════════════════════════════
# Grant deadlines shift constantly and are NOT safely storable in grant_data —
# a stale stored date is worse than none. Jade needs to consult the CURRENT
# deadline for a specific fund at ask-time. This unit builds the whole tool
# surface + graceful degradation on MOCKS. The single point where a real lookup
# (web_search vs fetch-and-parse vs a curated deadline URL) will later plug in is
# ``_fetch_deadline_raw`` — nothing else in the code path touches a wire, so the
# real mechanism can be swapped in behind that one signature without changing the
# public contract or the tool loop.


def _deadline_lookup_enabled() -> bool:
    """Env gate for the deadline-lookup mechanism (mirrors ``_portal_connected``).

    Driven purely by ``DEADLINE_LOOKUP_CONNECTED`` so tests toggle enabled /
    disabled with ZERO network calls and NO real secret:
      - "1"/"true"/"yes"/"connected" → enabled
      - anything else / unset         → disabled
    """
    val = (os.environ.get("DEADLINE_LOOKUP_CONNECTED", "") or "").strip().lower()
    return val in ("1", "true", "yes", "connected")


# Deterministic canned fixtures for the SEAM, keyed by program_id. A program_id
# present here resolves to a found=True deadline; any other enabled program
# resolves to found=False ("round not announced") — NEVER a synthesized date.
# When the real mechanism lands it replaces this table; the wrapper is unchanged.
_CANNED_DEADLINES = {
    "factor-canada-music-fund": "Next intake window closes Fri, Sep 5 (5:00 PM ET)",
}
# Static provenance label for canned found=True results (no clock is ever read).
_CANNED_AS_OF = "last published program calendar"


async def _fetch_deadline_raw(program_id: str, official_url: str) -> dict | None:
    """SEAM. The single point where a real deadline lookup (web search or
    fetch-and-parse) will later plug in. In THIS unit it is a MOCK: gated by env
    ``DEADLINE_LOOKUP_CONNECTED``, it returns deterministic canned data and makes
    NO network call. The real mechanism is deferred and swapped in behind this
    exact signature later.

    Returns:
      - {"found": True, "deadline_text": str, "source_url": str, "as_of": str}
        for a program with a canned deadline;
      - {"found": False, "source_url": str} for a program with no announced round.
    Raises:
      - DeadlineLookupUnavailable when the mechanism is not enabled/connected.
    """
    if not _deadline_lookup_enabled():
        raise DeadlineLookupUnavailable("deadline-lookup mechanism is not connected/enabled")

    pid = (program_id or "").strip()
    if pid in _CANNED_DEADLINES:
        return {
            "found":        True,
            "deadline_text": _CANNED_DEADLINES[pid],
            "source_url":    official_url,
            "as_of":         _CANNED_AS_OF,
        }
    # Every other enabled program: no round announced. We do NOT invent a date.
    return {"found": False, "source_url": official_url}


async def lookup_grant_deadline(artist_id: str, program_id: str) -> dict:
    """Look up the current/upcoming deadline for a specific fund.

    Always returns a structured result the model can relay verbatim — and NEVER
    invents a date. The HARD invariant: a date reaches the output only when
    ``_fetch_deadline_raw`` returns found=True with an explicit ``deadline_text``;
    this function never synthesizes or formats a date from nothing.

    The return dict ALWAYS carries: program_id, program_name, official_url,
    status, and a human-readable ``message``. Status is one of:
      - "program_not_found"   — no program matches program_id (no lookup fired)
      - "no_official_source"  — program has no usable URL on file (no lookup fired)
      - "lookup_unavailable"  — mechanism disabled/unreachable (check page directly)
      - "deadline_found"      — a concrete deadline_text was returned
      - "round_not_announced" — mechanism ran but no round is published yet
    """
    program = _get_program(program_id)
    if program is None:
        return {
            "status":       "program_not_found",
            "program_id":   (program_id or "").strip(),
            "program_name": None,
            "official_url": None,
            "message": (
                f"No grant program on file matches id '{(program_id or '').strip()}'. "
                "Confirm the program with the artist before looking up its deadline."
            ),
        }

    pid          = program["id"]
    name         = program.get("name", pid)
    funder       = program.get("funder") or "the funder"
    official_url = (program.get("url") or "").strip()

    base = {"program_id": pid, "program_name": name, "official_url": official_url}

    if not official_url:
        return {
            **base,
            "status": "no_official_source",
            "message": (
                f"{name} has no official application page on file, so I can't look up its "
                f"deadline. This fund's deadlines are normally posted by {funder} directly — "
                f"check with {funder} rather than relying on any stored date."
            ),
        }

    try:
        raw = await _fetch_deadline_raw(pid, official_url)
    except DeadlineLookupUnavailable:
        return {
            **base,
            "status": "lookup_unavailable",
            "message": (
                f"I couldn't run a live deadline check for {name} right now. Check the official "
                f"page directly: {official_url}. I won't guess a date."
            ),
        }

    if raw and raw.get("found") is True and raw.get("deadline_text"):
        return {
            **base,
            "status":        "deadline_found",
            "deadline_text": raw["deadline_text"],
            "source_url":    raw.get("source_url", official_url),
            "as_of":         raw.get("as_of", ""),
            "message": (
                f"Current deadline for {name}: {raw['deadline_text']}. Always confirm on the "
                f"official page ({official_url}) before you rely on it — deadlines shift and "
                "this isn't the authoritative source."
            ),
        }

    # found=False (or any non-found shape) → round not announced; NEVER a date.
    return {
        **base,
        "status": "round_not_announced",
        "message": (
            f"The current round for {name} hasn't been published yet. When it opens it will be "
            f"posted on the official page: {official_url}. I won't guess a date."
        ),
    }
