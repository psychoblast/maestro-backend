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


# ══════════════════════════════════════════════════════════════════════════════
# Unit 4 — application scaffold (data/scaffold tool; Jade writes the prose)
# ══════════════════════════════════════════════════════════════════════════════
# build_grant_application_scaffold is a DATA tool in the send_pitch_email mould:
# it NEVER calls the model and NEVER generates prose. It returns a compact dict
# of ingredients — section skeleton + guidance, whatever the artist actually
# supplied, explicit [NEEDS: ...] gaps, and an honest cost-share — and Jade
# composes the actual draft as her final-turn text.
#
# HARD INVARIANT (mirrors Unit 3's never-invent-a-date rule): the scaffold never
# contains a fabricated artist fact. Every content field is either something
# artist_inputs actually provided, a "[NEEDS: ...]" gap marker, or an
# "[ARTIST-SUPPLIED: ...]" non-draftable reminder. No invented budget numbers,
# no invented career facts, no invented cost-share percentages.

_GAP = "[NEEDS: {}]"

# ── Track-structure constants (data only, no logic) ──────────────────────────
# The section skeletons grant writing actually uses, keyed by track. Per entry:
#   key              stable section id
#   title            human section title
#   guidance         one line: what this section must accomplish, in the
#                    funder's own logic (answer-first, concrete targets, …)
#   inputs           artist_inputs keys that can cover this section
#   needs            human description of the gap when nothing covers it
#   artist_supplied  True = non-draftable material the artist must supply

# INDUSTRY funders (FACTOR-style): commercial viability logic.
INDUSTRY_SECTIONS = (
    {
        "key": "artist_bio",
        "title": "Artist Bio",
        "guidance": ("Written assuming the reader knows nothing about the artist: who they are, "
                     "career stage, and momentum (releases, streams, press) — key numbers first."),
        "inputs": ("bio", "career_stage", "career_highlights"),
        "needs": "artist bio — career stage, momentum, key numbers",
        "artist_supplied": False,
    },
    {
        "key": "project_description",
        "title": "Project Description",
        "guidance": ("Answer-first: what will be made, by whom, by when — concrete deliverables "
                     "and dates, not vision statements."),
        "inputs": ("project", "project_description", "timeline"),
        "needs": "project description — what is being made, by whom, by when",
        "artist_supplied": False,
    },
    {
        "key": "marketing_release_plan",
        "title": "Marketing / Release Plan",
        "guidance": ("Concrete targets with numbers and dates (playlist adds, press outlets, ad "
                     "spend, tour dates) — industry funders back plans, not hopes."),
        "inputs": ("marketing_plan", "release_plan", "targets"),
        "needs": "marketing/release plan with concrete, dated targets",
        "artist_supplied": False,
    },
    {
        "key": "budget",
        "title": "Budget (with cost share)",
        "guidance": ("Line items that add up, showing the required funder/artist split — e.g. "
                     "FACTOR funds up to 75% of eligible costs and the artist supplies the rest; "
                     "name where the artist's share comes from."),
        "inputs": ("budget_lines", "requested_amount", "match_source"),
        "needs": "budget lines, requested amount, and the source of the artist's cost-share",
        "artist_supplied": False,
    },
    {
        "key": "assessment_materials",
        "title": "Assessment Tracks / Press / Letters",
        "guidance": ("Assessment tracks, press clippings, and letters of support are "
                     "artist-supplied materials — they cannot be drafted; the artist gathers and "
                     "attaches their own."),
        "inputs": (),
        "needs": "",
        "artist_supplied": True,
    },
)

# ARTS-COUNCIL funders (ACE / Canada Council-style): public-benefit logic.
# Order matters — Need → Outcomes → Audience → Activities → Budget → Evaluation.
ARTS_COUNCIL_SECTIONS = (
    {
        "key": "need",
        "title": "The Need",
        "guidance": ("Draft this FIRST: name the artistic/community need this project answers — "
                     "every other section hangs off it."),
        "inputs": ("need",),
        "needs": "the artistic/community need this project answers",
        "artist_supplied": False,
    },
    {
        "key": "outcomes",
        "title": "Outcomes",
        "guidance": ("Public outcomes, not commercial ones — what changes for people if this "
                     "succeeds; draft together with the Need before anything else."),
        "inputs": ("outcomes",),
        "needs": "the public outcomes — what changes for people if this succeeds",
        "artist_supplied": False,
    },
    {
        "key": "audience",
        "title": "Audience",
        "guidance": ("Who benefits and how they will be reached — public-benefit framing, not "
                     "market positioning."),
        "inputs": ("audience",),
        "needs": "who benefits and how they will be reached",
        "artist_supplied": False,
    },
    {
        "key": "activities",
        "title": "Activities",
        "guidance": "Every activity ties to a named outcome — no orphan activities.",
        "inputs": ("activities", "project", "timeline"),
        "needs": "the project activities, each tied to an outcome",
        "artist_supplied": False,
    },
    {
        "key": "budget",
        "title": "Budget",
        "guidance": "Every budget line ties to an activity and, through it, to an outcome.",
        "inputs": ("budget_lines", "requested_amount"),
        "needs": "budget lines and requested amount, each tied to an activity",
        "artist_supplied": False,
    },
    {
        "key": "evaluation",
        "title": "Evaluation",
        "guidance": ("How you will know the outcomes happened — simple, honest measures reported "
                     "back to the funder."),
        "inputs": ("evaluation",),
        "needs": "how the outcomes will be measured and reported",
        "artist_supplied": False,
    },
)

# Fallback for tracks with no dedicated skeleton (crowdfunding / future
# foundation / export tracks): a general project-proposal structure, clearly
# marked GENERIC so Jade never presents it as a fund's own form.
GENERIC_SECTIONS = (
    {
        "key": "summary",
        "title": "Project Summary (generic skeleton)",
        "guidance": ("GENERIC project-proposal structure — this track has no dedicated skeleton. "
                     "Who the artist is and what the project is, answer-first."),
        "inputs": ("summary", "bio", "career_stage"),
        "needs": "a short summary — who the artist is and what the project is",
        "artist_supplied": False,
    },
    {
        "key": "project_description",
        "title": "Project Description (generic skeleton)",
        "guidance": "What will be made, by whom, by when — concrete deliverables and dates.",
        "inputs": ("project", "project_description", "timeline"),
        "needs": "project description — what is being made, by whom, by when",
        "artist_supplied": False,
    },
    {
        "key": "budget",
        "title": "Budget (generic skeleton)",
        "guidance": "Line items that add up; name any co-funding the artist brings.",
        "inputs": ("budget_lines", "requested_amount", "match_source"),
        "needs": "budget lines and requested amount",
        "artist_supplied": False,
    },
    {
        "key": "impact",
        "title": "Impact / Outcomes (generic skeleton)",
        "guidance": "What this project changes for the artist's career or audience — be concrete.",
        "inputs": ("impact", "outcomes", "targets"),
        "needs": "the project's intended impact/outcomes",
        "artist_supplied": False,
    },
)

GRANT_SECTION_SKELETONS = {
    "industry": INDUSTRY_SECTIONS,
    "arts_council": ARTS_COUNCIL_SECTIONS,
}


def compute_cost_share(requested_amount, program) -> dict:
    """Express the funder-vs-artist split HONESTLY from structured amount data.

    Pure, no I/O. Uses ONLY the program's structured ``amount_max`` cap:
      - cap known + amount requested → the funder covers at most
        min(requested, cap); anything above the cap is the artist's minimum
        contribution. That is the whole computation — nothing else is derivable
        from the structured data.
      - cap unlisted (amount_max None / stub) → "verify live — cannot compute
        an exact split", never a made-up number.

    A percentage share is NEVER computed or invented: no record structures one.
    Any share language (e.g. FACTOR's "75% cost share") lives in the
    data-supplied ``amount_notes``, which is passed through verbatim for Jade
    to quote as the program's own wording.
    """
    program = dict(program or {})
    currency = program.get("currency", "") or ""
    amount_max = program.get("amount_max")
    try:
        requested = int(requested_amount or 0)
    except (TypeError, ValueError):
        requested = 0
    base = {
        "currency":         currency,
        "requested_amount": requested,
        "amount_max":       amount_max,
        "amount_notes":     program.get("amount_notes", "") or "",
    }
    if amount_max is None:
        return {
            **base,
            "computable": False,
            "note": ("This program's amount data is unlisted — verify live. I cannot compute an "
                     "exact funder/artist split and will not invent one."),
        }
    if requested <= 0:
        return {
            **base,
            "computable": False,
            "note": (f"No requested amount supplied yet. Funder cap on file: {amount_max} "
                     f"{currency} (approximate — verify live)."),
        }
    funder_max = min(requested, amount_max)
    artist_min = requested - funder_max
    return {
        **base,
        "computable":              True,
        "funder_max_contribution": funder_max,
        "artist_min_contribution": artist_min,
        "note": (f"Derived ONLY from the program's listed cap ({amount_max} {currency}, "
                 f"approximate — verify live): the funder covers at most {funder_max}, leaving at "
                 f"least {artist_min} to the artist. Any percentage cost-share in amount_notes is "
                 "the program's own wording, not a computed figure."),
    }


def _sections_for_track(track) -> tuple[tuple, str]:
    """Pick the section skeleton for a program track (generic fallback)."""
    t = (track or "").strip().lower()
    skeleton = GRANT_SECTION_SKELETONS.get(t)
    if skeleton is not None:
        return skeleton, t
    return GENERIC_SECTIONS, "generic"


async def build_grant_application_scaffold(
    artist_id: str, program_id: str, artist_inputs: dict
) -> dict:
    """Build a compact, section-by-section application scaffold for one fund.

    DATA/SCAFFOLD tool — no model call, no prose generation, no I/O. Jade calls
    this AFTER her Phase-A interview; ``artist_inputs`` is whatever she gathered
    (free-form dict: bio, project, targets, budget_lines, timeline, need,
    outcomes, …). Each skeleton section is filled ONLY from artist_inputs; any
    section/field nothing covers comes back as an explicit "[NEEDS: ...]" gap
    marker for Jade to reproduce verbatim in her draft. Non-draftable material
    (assessment tracks / press / letters) is flagged, never faked.

    Returns a compact dict: {status, program_id, program_name, track, skeleton,
    currency, sections: [{key, title, guidance, artist_supplied_flag,
    content_or_gap}], cost_share, missing, nondraftable_reminders} —
    ingredients, not prose.
    """
    program = _get_program(program_id)
    if program is None:
        return {
            "status":     "program_not_found",
            "program_id": (program_id or "").strip(),
            "message": (
                f"No grant program on file matches id '{(program_id or '').strip()}'. "
                "Confirm the program with the artist before scaffolding an application."
            ),
        }

    inputs = dict(artist_inputs or {})

    def _covered(v) -> bool:
        return v not in (None, "", [], {}, ())

    skeleton, skeleton_name = _sections_for_track(program.get("track"))

    sections, missing, nondraftable, used_keys = [], [], [], set()
    for spec in skeleton:
        entry = {
            "key":                  spec["key"],
            "title":                spec["title"],
            "guidance":             spec["guidance"],
            "artist_supplied_flag": spec["artist_supplied"],
        }
        if spec["artist_supplied"]:
            entry["content_or_gap"] = (
                "[ARTIST-SUPPLIED: cannot be drafted — the artist gathers and attaches "
                "their own materials]"
            )
            nondraftable.append(f"{spec['title']}: {spec['guidance']}")
        else:
            supplied = {k: inputs[k] for k in spec["inputs"] if _covered(inputs.get(k))}
            used_keys |= set(supplied)
            if not supplied:
                gap = _GAP.format(spec["needs"])
                entry["content_or_gap"] = gap
                missing.append(gap)
            else:
                content = {}
                for k in spec["inputs"]:
                    if k in supplied:
                        content[k] = supplied[k]
                    else:
                        gap = _GAP.format(k)
                        content[k] = gap
                        missing.append(gap)
                entry["content_or_gap"] = content
        sections.append(entry)

    # A key can back more than one section (e.g. timeline); report each gap once.
    missing = list(dict.fromkeys(missing))
    # Gathered facts no section claims still ride along verbatim — never dropped,
    # never rewritten (Jade decides where they belong in the draft).
    unmapped = {k: v for k, v in inputs.items() if k not in used_keys and _covered(v)}

    result = {
        "status":       "scaffold_ready",
        "program_id":   program["id"],
        "program_name": program["name"],
        "track":        program.get("track", ""),
        "skeleton":     skeleton_name,
        "currency":     program.get("currency", "") or "",
        "sections":     sections,
        "cost_share":   compute_cost_share(inputs.get("requested_amount"), program),
        "missing":      missing,
        "nondraftable_reminders": nondraftable,
        "note": ("Scaffold only — write the draft yourself from these ingredients, keep every "
                 "[NEEDS: ...] marker verbatim, and never invent a fact. The draft is a starting "
                 "point for the artist and their manager to review — not submit-ready."),
    }
    if unmapped:
        result["unmapped_inputs"] = unmapped
    return result
