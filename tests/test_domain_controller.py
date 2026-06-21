"""
Tests for the re-homed "controller" domain (Financial controller).

In-process only. NO network / LLM calls. The bank reads knowledge files already
present in the repo (under knowledge_bank/domains/controller/).
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


# A query that is unambiguously in the financial-controller domain.
IN_DOMAIN_QUERY = (
    "can the controller certify the period close — are all balance sheet accounts "
    "reconciled and is the audit trail documented"
)


# ── registry ─────────────────────────────────────────────────────────────────────

def test_list_domains_includes_controller():
    assert "controller" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("controller").display_name == "Financial controller"


def test_load_domain_non_empty():
    text = registry.load_domain("controller")
    assert isinstance(text, str)
    assert text.strip(), "controller loaded empty knowledge"


def test_load_domain_assembles_core_doctrine():
    text = registry.load_domain("controller").lower()
    # Core, domain-defining concepts must be present in the assembled knowledge.
    assert "reconciliation" in text
    assert "audit trail" in text
    assert "revenue recognition" in text
    assert "segregation of duties" in text
    assert "ledger integrity & controls scorecard" in text


def test_load_domain_assembles_all_manifest_sections():
    # Eight knowledge files → eight sections joined by the standard separator.
    text = registry.load_domain("controller")
    assert text.count("\n\n---\n\n") >= 7


# ── brain routing ─────────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_controller():
    assert "controller" in brain.route(IN_DOMAIN_QUERY)


def test_route_revrec_query_to_controller():
    assert "controller" in brain.route(
        "what is the correct revenue recognition and deferred revenue treatment under asc 606"
    )


def test_route_controls_query_to_controller():
    assert "controller" in brain.route(
        "assess our internal controls and segregation of duties for the journal entry process"
    )


def test_route_unrelated_query_excludes_controller():
    # Guard against keyword over-reach: a pure royalties query must not pull in controller.
    assert "controller" not in brain.route("how do mechanical royalties and recoup work")


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────────

def test_consult_returns_controller_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "controller" in result["domains"]
    domain = registry.get_domain("controller")
    assert f"# {domain.display_name} (controller)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("controller"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("period close reconciliation and misstatement exposure review", "controller"),
        ("revenue recognition memo for a sync licensing advance", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
