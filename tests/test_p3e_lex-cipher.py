"""
Phase 3e — Per-agent deep consult test for lex-cipher.

Scope: lex-cipher only. Home domain "legal". Six realistic questions an artist
or their team would ask their entertainment lawyer, covering the agent's core
contract-review and rights-negotiation brief.

For each cross-domain question we assert:
  (a) lex-cipher's home domain "legal" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious cross-domain.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "lex-cipher"
_HOME  = "legal"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "legal" leads; every expected cross-domain is present in domains.

DEEP_CONSULT_MATRIX = [
    (
        # legal: contract, clause (from "clauses"), negotiat
        # management: management contract, management, commission scope,
        #             sunset provision, key-person clause, key-person
        "We need to review a management contract including commission scope, "
        "sunset provisions and key-person clauses before our artist signs",
        ["management"],
    ),
    (
        # legal: negotiat, legal
        # finance_royalties: royalt (royalty), accounting, mechanical
        "We are negotiating an artist agreement with royalty accounting "
        "provisions and mechanical rate calculations that require legal expertise",
        ["finance_royalties"],
    ),
    (
        # legal: licens (licensing/license), negotiat, indemnit, clause
        # sync: sync, licens, master use, cue sheet
        "We received a sync licensing offer and need to negotiate the master "
        "use license, cue sheet terms, and indemnification clause",
        ["sync"],
    ),
    (
        # legal: contract, negotiat, dispute, clause (clauses)
        # live_touring: festival, rider
        "We need to review a festival contract and negotiate performance terms, "
        "rider requirements, and dispute resolution clauses",
        ["live_touring"],
    ),
    (
        # legal: negotiat, rights (rights provisions), indemnit
        # bizdev: brand, endorsement
        "We have a brand endorsement agreement to negotiate covering IP rights "
        "provisions, exclusivity and indemnification requirements",
        ["bizdev"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped contract-law question returning ONLY the home domain "legal".
# Keywords triggered: warrant (in "warranties"), contract — both are legal-only.
# Deliberately avoids:
#   - "breach" — contains substring "reach" which fires marketing
#   - "royalt", "publish", "catalog", "tour", "brand", "sync", "management",
#     "licens", "recording" (fires label_ops), and any other cross-domain trigger.

_NARROW_QUERY = (
    "What are the key warranties and representations that protect the "
    "non-defaulting party in a music contract?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "management-contract-commission-sunset-keyperson",
        "royalty-accounting-mechanical-legal-review",
        "sync-licensing-master-use-cue-sheet-indemnification",
        "festival-contract-rider-dispute-resolution",
        "brand-endorsement-rights-indemnification-bizdev",
    ],
)
def test_lex_cipher_consult_home_leads_and_cross_domains_present(query, cross):
    """
    lex-cipher's home domain 'legal' is always first; every expected
    cross-domain is present. Verifies home-first invariant and legal-specific
    cross-domain routing quality.
    """
    result = _consult(query)

    assert result["home_domain"] == _HOME, (
        f"expected home={_HOME!r}, got {result['home_domain']!r}"
    )
    assert result["domains"], "domains list is empty"
    assert result["domains"][0] == _HOME, (
        f"home domain must be first; got {result['domains']}"
    )
    for d in cross:
        assert d in result["domains"], (
            f"expected cross-domain {d!r} not found in {result['domains']}\n"
            f"Query: {query!r}"
        )
    assert result["knowledge"].strip(), "knowledge text is empty"


def test_lex_cipher_narrow_query_returns_home_domain_only():
    """
    A narrowly-scoped contract-law question (material breach, remedies) must
    return only the home domain 'legal' — no spurious cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
