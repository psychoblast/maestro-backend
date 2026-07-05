"""
PLMKR Ledger-Lock — accountant action service (mock-first).

Backs the Ledger-Lock (Nadia — Accountant) agent's tool_use loop in
/api/chat_stream (see LEDGER_LOCK_TOOLS in main.py). Nadia does not just advise on
tax, bookkeeping, and royalty statements — these functions let the agent take real
accountant actions: look up the royalty income sources an artist earns from (each
carrying the withholding rate typically applied before net pay-out), reconcile an
incoming royalty statement by applying that source's withholding to the gross so
the artist knows the true net they should book, and file a tax document (an
estimate, an annual return, a 1099, etc.) with the artist's connected bookkeeping
account so the filing actually gets lodged on their behalf.

Unit 2: lookup_recording_societies and build_registration_checklist are pure
reads/computations over the royalties_data corpus (Nadia Unit 1) — the corpus
is the single source of truth; no domain fact is invented here. The lookup
resolves composition-side context ids via publishing_data (read-only import in
the SERVICE layer only — corpora stay import-free). The checklist applies
REGISTRATION_RULES to EXPLICITLY supplied situation flags only: an unsupplied
axis is a [NEEDS:<flag>] gap and its rule branch does NOT fire
(HONESTY_RULES.situation_flags_explicit_only). No split is ever stated as fact
except the US statutory SoundExchange 50/45/5 — everything else surfaces as
varies_verify_with_society (HONESTY_RULES.only_statutory_split_hardcoded).

MOCK-FIRST CONTRACT (hard rules for this module):
  - Every function returns a plain, JSON-serializable dict.
  - ZERO network calls. No live tax/bookkeeping APIs, no filing portals, no LLM.
  - NO secrets are read or embedded. The only "credential" surface is a
    connection check (``_ledger_account_connected``) driven by an env flag so
    tests can toggle the connected / not-connected / expired states
    deterministically — mirroring vault_keeper_service._vault_account_connected
    without touching a wire.
  - Deterministic: no timestamps or random values leak into return payloads, so
    tests can assert on exact structure.
"""
import hashlib
import os

import publishing_data
import royalties_data


class LedgerAccountNotConnected(Exception):
    """Raised when the artist has not connected a bookkeeping/tax account.

    Mirrors vault_keeper_service.VaultAccountNotConnected: the tool loop catches
    this and degrades gracefully into a structured 'connect your account first'
    result instead of crashing the stream.
    """


class LedgerAccountAuthExpired(Exception):
    """Raised when a previously connected bookkeeping-account authorization expired."""


# ── Royalty income source library (in-memory reference data) ───────────────────
# A curated set of royalty income sources an artist earns from. Each source carries
# the withholding percentage typically deducted before the net pay-out reaches the
# artist (foreign withholding tax, agency/collection fees, etc.), so the agent can
# reconcile an incoming statement by applying the source's withholding to a gross
# figure. Keyed loosely on source type / region so the agent can surface the right
# reconciliation basis. No I/O.
_SOURCES = [
    {
        "id": "src-streaming-domestic",
        "name": "Domestic Streaming (DSP)",
        "source_type": "streaming",
        "region": "domestic",
        "withholding_pct": 0,
    },
    {
        "id": "src-streaming-foreign",
        "name": "Foreign Streaming (DSP)",
        "source_type": "streaming",
        "region": "foreign",
        "withholding_pct": 30,
    },
    {
        "id": "src-mechanical",
        "name": "Mechanical Royalties",
        "source_type": "mechanical",
        "region": "domestic",
        "withholding_pct": 0,
    },
    {
        "id": "src-performance-domestic",
        "name": "Domestic Performance Royalties (PRO)",
        "source_type": "performance",
        "region": "domestic",
        "withholding_pct": 0,
    },
    {
        "id": "src-performance-foreign",
        "name": "Foreign Performance Royalties (PRO)",
        "source_type": "performance",
        "region": "foreign",
        "withholding_pct": 15,
    },
    {
        "id": "src-sync",
        "name": "Sync Licensing Income",
        "source_type": "sync",
        "region": "domestic",
        "withholding_pct": 0,
    },
    {
        "id": "src-neighbouring-foreign",
        "name": "Foreign Neighbouring Rights",
        "source_type": "neighbouring",
        "region": "foreign",
        "withholding_pct": 20,
    },
]

# Tax filing document types the platform recognises on a filing action.
_VALID_FILING_TYPES = (
    "quarterly_estimate", "annual_return", "1099", "vat_return", "self_assessment",
)


async def search_royalty_sources(source_type: str = "", region: str = "") -> dict:
    """Search royalty income sources by source type and/or region.

    Both filters are optional and matched case-insensitively as substrings.
    ``source_type`` matches the source type (e.g. "streaming", "performance"), and
    ``region`` matches the region (e.g. "domestic", "foreign").
    Returns {"sources": [...], "count": int}. Pure — no I/O.
    """
    st = (source_type or "").strip().lower()
    rg = (region or "").strip().lower()
    matches = [
        dict(s)
        for s in _SOURCES
        if (not st or st in s["source_type"].lower())
        and (not rg or rg in s["region"].lower())
    ]
    return {"sources": matches, "count": len(matches)}


def _get_source(source_id: str) -> dict | None:
    sid = (source_id or "").strip()
    for s in _SOURCES:
        if s["id"] == sid:
            return s
    return None


async def reconcile_royalty_statement(
    artist_id: str,
    source_id: str = "",
    statement_period: str = "",
    gross_amount: float = 0,
) -> dict:
    """Reconcile a royalty statement by applying a source's withholding to the gross.

    Deterministic reconciliation — never contacts a wire. Looks the source up by id,
    checks a statement period and a positive gross figure are present, and computes
    the withholding and net booked amount from the source's withholding percentage.
    Returns a structured reconciliation with line items, net amount, and a
    recommendation of "record" / "adjust" / "blocked".
    """
    source = _get_source(source_id)

    try:
        gross = round(float(gross_amount or 0), 2)
    except (TypeError, ValueError):
        gross = 0.0

    gaps = []
    if not (statement_period or "").strip():
        gaps.append("missing_statement_period")
    if not (source_id or "").strip():
        gaps.append("missing_source")
    elif source is None:
        gaps.append("unknown_source")
    if gross <= 0:
        gaps.append("non_positive_gross")

    line_items = []
    withholding_pct    = source["withholding_pct"] if source else 0
    withholding_amount = 0.0
    net_amount         = gross
    if source is not None and gross > 0:
        withholding_amount = round(gross * withholding_pct / 100.0, 2)
        net_amount = round(gross - withholding_amount, 2)
        line_items = [
            {"label": "gross",       "amount": gross},
            {"label": "withholding", "pct": withholding_pct, "amount": withholding_amount},
            {"label": "net",         "amount": net_amount},
        ]

    if "unknown_source" in gaps or "missing_source" in gaps:
        # Without a valid source target the statement cannot be reconciled at all.
        recommendation = "blocked"
    elif gaps or net_amount < 0:
        recommendation = "adjust"
    else:
        recommendation = "record"
    reconciled = recommendation == "record"

    return {
        "reconciled": reconciled,
        "gaps": gaps,
        "source_id": source["id"] if source else (source_id or "").strip(),
        "source_name": source["name"] if source else None,
        "statement_period": (statement_period or "").strip(),
        "gross_amount": gross,
        "withholding_pct": withholding_pct,
        "withholding_amount": withholding_amount,
        "net_amount": net_amount,
        "line_items": line_items,
        "recommendation": recommendation,
    }


# ── Unit-2 plumbing (pure; corpus-driven) ─────────────────────────────────────
_GAP = "[NEEDS:{}]"


def _resolve_recording_bodies(ids):
    """Resolve recording-society ids to full records; None passes through as None."""
    if ids is None:
        return None
    return [dict(royalties_data.RECORDING_SOCIETIES[sid]) for sid in ids]


async def lookup_recording_societies(country_code: str = "") -> dict:
    """Look up who collects RECORDING-side royalties in one country — pure corpus read.

    Returns the recording-side body records (with capacities via ``represents``
    and their scope/registration notes) plus the composition-side society ids
    for context (resolved read-only via publishing_data — those bodies are
    Reed's domain and are referenced, never duplicated). A country outside the
    11-country corpus returns a structured ``country_not_in_corpus`` result
    listing the supported codes — a body is NEVER guessed
    (HONESTY_RULES.unknown_is_none). A country whose recording side is
    unverified in the corpus (NZ) surfaces None + the verify-live note honestly.
    """
    code = (country_code or "").strip().upper()
    record = royalties_data.COUNTRY_ROYALTY_TABLE.get(code)
    if record is None:
        return {
            "status": "country_not_in_corpus",
            "country": code or "(missing)",
            "supported_countries": list(royalties_data.ROYALTY_COUNTRIES),
            "message": ("No verified royalty-routing data for this country in the "
                        "corpus. Do not guess a body — tell the artist to verify "
                        "with a local authority, or pick from the supported list."),
        }
    recording_bodies = _resolve_recording_bodies(record["recording_performance_ids"])
    result = {
        "status": "ok",
        "country": code,
        "recording_bodies": recording_bodies,
        "composition_context": {
            "performance_ids": list(record["composition_performance_ids"]),
            "mechanical_ids": list(record["composition_mechanical_ids"]),
            "performance_names": [publishing_data.SOCIETIES[sid]["name"]
                                  for sid in record["composition_performance_ids"]],
            "mechanical_names": [publishing_data.SOCIETIES[sid]["name"]
                                 for sid in record["composition_mechanical_ids"]],
            "note": "Composition side is Reed's (ink-and-air) domain — ids "
                    "reference publishing_data verbatim.",
        },
        "notes": record["notes"],
    }
    if recording_bodies is None:
        result["recording_side_status"] = "unverified"
        result["recording_side_note"] = ("No verified recording-side body in the "
                                         "corpus for this country — verify live; "
                                         "a body is never guessed.")
    return result


def _flag_supplied(situation: dict, axis: str) -> bool:
    """A flag counts as supplied ONLY when present and not None — never defaulted."""
    return axis in situation and situation[axis] is not None


def _entry_split(stream_id: str):
    """The split payload for a checklist entry — statutory quote or the sentinel.

    Quoting the SoundExchange statutory 50/45/5 is the ONLY split ever stated
    as fact; every other stream where a split could be implied carries
    varies_verify_with_society (HONESTY_RULES.only_statutory_split_hardcoded).
    """
    if stream_id == "us_digital_recording_performance":
        return dict(royalties_data.RECORDING_SOCIETIES["soundexchange"]["statutory_split"])
    return royalties_data.SPLIT_UNKNOWN_SENTINEL


async def build_registration_checklist(situation: dict = None) -> dict:
    """Apply royalties_data.REGISTRATION_RULES to EXPLICIT situation flags only.

    Pure computation over the Unit-1 corpus — compact structured data, no
    prose, no I/O, no LLM. Every axis a rule needs that was not explicitly
    supplied becomes a [NEEDS:<flag>] gap and that rule branch does NOT fire —
    a flag is never defaulted or inferred
    (HONESTY_RULES.situation_flags_explicit_only). Rule order is preserved from
    the corpus. Bodies resolve per body_ref (specific body) or by_country
    (COUNTRY_ROYALTY_TABLE / publishing_data routing); an unverified recording
    side (NZ) surfaces bodies=None + verify-live. Splits are never stated as
    fact except the statutory SoundExchange 50/45/5.
    """
    situation = dict(situation) if isinstance(situation, dict) else {}
    spec_axes = tuple(royalties_data.REGISTRATION_SITUATION_SPEC)

    country = None
    if _flag_supplied(situation, "country_of_residence"):
        country = str(situation["country_of_residence"]).strip().upper()
    country_record = royalties_data.COUNTRY_ROYALTY_TABLE.get(country) if country else None

    needs, registrations, notes = [], [], []
    if country and country_record is None:
        notes.append({"source": "country_of_residence", "text": country,
                      "note": ("country_not_in_corpus — routing bodies cannot be "
                               "resolved; verify live. Supported: "
                               + ", ".join(royalties_data.ROYALTY_COUNTRIES))})

    for rule in royalties_data.REGISTRATION_RULES:
        condition = rule["condition"]
        axis = condition["axis"]
        if not _flag_supplied(situation, axis):
            needs.append(_GAP.format(axis))
            continue  # explicit-only: the branch does NOT fire on a missing flag
        if "equals" in condition:
            supplied = situation[axis]
            if axis == "country_of_residence":
                supplied = country
            if supplied != condition["equals"]:
                continue

        stream_id = rule["stream_id"]
        if country == "US" and rule.get("stream_id_us_override"):
            stream_id = rule["stream_id_us_override"]

        bodies = None
        if rule["body_ref"] is not None:
            pool = (publishing_data.SOCIETIES
                    if rule["body_ref_corpus"] == "publishing_data"
                    else royalties_data.RECORDING_SOCIETIES)
            bodies = [dict(pool[rule["body_ref"]])]
        elif country_record is not None:
            if royalties_data.STREAMS[stream_id]["side"] == "composition":
                ids = country_record["composition_performance_ids"]
                bodies = [dict(publishing_data.SOCIETIES[sid]) for sid in ids]
            else:
                bodies = _resolve_recording_bodies(
                    country_record["recording_performance_ids"])

        entry = {
            "rule_id": rule["id"],
            "registration": rule["registration"],
            "capacity": rule["capacity"],
            "stream_id": stream_id,
            "bodies": bodies,
            "reason": rule["reason"],
            "notes": rule["notes"],
            "split": _entry_split(stream_id),
        }
        if bodies is None:
            entry["body_status"] = "unverified"
            entry["body_note"] = ("No verified body resolvable for this "
                                  "registration — verify live; a body is never "
                                  "guessed.")
        registrations.append(entry)

    supplied_flags = {axis: situation[axis] for axis in spec_axes
                      if _flag_supplied(situation, axis)}
    unmapped = {k: v for k, v in situation.items() if k not in spec_axes}
    for key, value in unmapped.items():
        notes.append({"source": "situation", "field": key, "text": value,
                      "note": "free text — carried verbatim, never parsed"})

    needs = list(dict.fromkeys(needs))
    return {
        "complete": not needs,
        "situation": supplied_flags,
        "registrations": registrations,
        "needs": needs,
        "notes": notes,
        "metadata_reminders": dict(royalties_data.METADATA_DOCTRINE),
        "split_discipline": ("Only the US statutory SoundExchange 50/45/5 split "
                             "is ever stated as fact; every other split is "
                             + royalties_data.SPLIT_UNKNOWN_SENTINEL + "."),
    }


def _ledger_account_connected(artist_id: str) -> bool:
    """Mock connection check for the artist's bookkeeping/tax account.

    In production this would look up a stored bookkeeping/tax-account link for the
    artist. Here it is driven purely by the ``LEDGER_LOCK_ACCOUNT_CONNECTED`` env
    flag so tests can toggle connected / expired / not-connected with ZERO network
    calls and NO real secret. Values:
      - "expired"                     → raise LedgerAccountAuthExpired
      - "1"/"true"/"yes"/"connected"  → connected
      - anything else / unset         → not connected
    """
    val = (os.environ.get("LEDGER_LOCK_ACCOUNT_CONNECTED", "") or "").strip().lower()
    if val == "expired":
        raise LedgerAccountAuthExpired("bookkeeping-account authorization expired")
    return val in ("1", "true", "yes", "connected")


async def file_tax_document(
    artist_id: str,
    filing_type: str,
    period: str,
    amount: float = 0,
) -> dict:
    """File a tax document with the artist's connected bookkeeping account.

    Raises LedgerAccountNotConnected / LedgerAccountAuthExpired when no bookkeeping
    account is linked so the caller can surface a 'connect your account' message
    instead of a hard failure. On success returns a deterministic mock filing
    reference — NO network call is ever made and nothing is actually lodged.
    """
    if not _ledger_account_connected(artist_id):
        raise LedgerAccountNotConnected(
            "artist has not connected a bookkeeping/tax account"
        )
    ft  = (filing_type or "").strip().lower()
    per = (period or "").strip()
    try:
        amt = round(float(amount or 0), 2)
    except (TypeError, ValueError):
        amt = 0.0
    digest = hashlib.sha1(f"{artist_id}:{ft}:{per}:{amt}".encode("utf-8")).hexdigest()
    reference = "TAX-" + digest[:10].upper()
    return {
        "status": "filed",
        "reference": reference,
        "filing_type": ft,
        "period": per,
        "amount": amt,
    }
