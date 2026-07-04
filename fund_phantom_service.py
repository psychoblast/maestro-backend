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
