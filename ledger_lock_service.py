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
