"""
Phase 3f — deepened sync domain knowledge tests.

Verifies that the 'sync' domain loads via the bank's normal path (registry),
is non-trivially sized, includes all required sections from both pre-existing
and new knowledge files, and contains no forbidden entity strings.

Two new knowledge files were added in phase 3f:
  - pitch-strategy.md  (pitch-doctrine)
  - backend-royalties.md (backend-doctrine)

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "pitch this track for a television sync placement and negotiate "
    "the master use license and synchronization fee"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_sync():
    assert "sync" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("sync").display_name == "Sync Licensing"


def test_load_domain_returns_string():
    text = registry.load_domain("sync")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("sync")
    assert text.strip(), "sync domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 7 knowledge files → expect at least 50 000 chars of assembled content
    text = registry.load_domain("sync")
    assert len(text) >= 50_000, (
        f"sync knowledge too small: {len(text)} chars — expected ≥50 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 7 files joined by section separators → at least 6 separators
    text = registry.load_domain("sync")
    assert text.count("\n\n---\n\n") >= 6, (
        "Expected ≥6 section separators (7 knowledge files) in sync domain"
    )


# ── pre-existing doctrine presence ────────────────────────────────────────────

def test_scoring_rubric_present():
    text = registry.load_domain("sync").lower()
    assert "scoring rubric" in text or "four-dimension" in text or "brief fit" in text
    assert "clearance complexity" in text
    assert "turnaround feasibility" in text
    assert "fee tier" in text


def test_hard_gates_present():
    text = registry.load_domain("sync").lower()
    assert "hard gate" in text
    assert "verdict" in text
    assert "pitch" in text
    assert "hold" in text


def test_buyer_psychology_present():
    text = registry.load_domain("sync").lower()
    assert "music supervisor" in text
    assert "funded" in text
    assert "fishing" in text
    assert "honest-pass" in text or "honest pass" in text


def test_brief_anatomy_present():
    text = registry.load_domain("sync").lower()
    assert "brief" in text
    assert "reference" in text
    assert "scene" in text


def test_clearance_workflow_present():
    text = registry.load_domain("sync").lower()
    assert "clearance" in text
    assert "one-stop" in text
    assert "unknown" in text
    assert "blocked" in text


def test_one_stop_doctrine_present():
    text = registry.load_domain("sync").lower()
    assert "one-stop" in text
    assert "master" in text
    assert "publishing" in text


def test_turnaround_norms_present():
    text = registry.load_domain("sync").lower()
    assert "trailer" in text
    assert "turnaround" in text
    assert "deadline" in text


def test_licensing_deal_logic_present():
    text = registry.load_domain("sync").lower()
    assert "six dials" in text or "six dial" in text
    assert "scope" in text
    assert "term" in text
    assert "territory" in text
    assert "exclusivity" in text


def test_fee_tiering_present():
    text = registry.load_domain("sync").lower()
    assert "fee tier" in text or "fee tiering" in text
    assert "national ad" in text or "national" in text
    assert "indie film" in text


def test_output_templates_present():
    text = registry.load_domain("sync").lower()
    assert "brief-fit scorecard" in text
    assert "fee quote sheet" in text
    assert "pitch email" in text
    assert "clearance chain map" in text
    assert "turnaround tracker" in text


# ── new pitch-strategy knowledge (phase 3f) ───────────────────────────────────

def test_pitch_strategy_file_loaded():
    """pitch-strategy.md content must appear in the assembled knowledge."""
    text = registry.load_domain("sync").lower()
    assert "reference-track" in text or "brief decoding" in text, (
        "pitch-strategy.md content not found in assembled sync knowledge"
    )


def test_reference_track_decoding_present():
    text = registry.load_domain("sync").lower()
    assert "extraction protocol" in text or "reference" in text
    assert "tempo" in text
    assert "energy arc" in text
    assert "production era" in text or "era" in text


def test_pitch_count_discipline_present():
    text = registry.load_domain("sync").lower()
    assert "pitch count" in text or "per-track" in text or "subject line" in text


def test_buyer_ecosystems_present():
    text = registry.load_domain("sync").lower()
    assert "television episodic" in text or "tv episodic" in text or "episodic" in text
    assert "trailer" in text
    assert "advertising" in text or "advertisement" in text or "national ad" in text


def test_trailer_ecosystem_present():
    text = registry.load_domain("sync").lower()
    assert "trailer house" in text
    assert "spec" in text


def test_music_library_mechanics_present():
    text = registry.load_domain("sync").lower()
    assert "music library" in text or "non-exclusive" in text
    assert "re-titling" in text or "re-title" in text or "retitling" in text
    assert "blanket license" in text


def test_supervisor_relationship_management_present():
    text = registry.load_domain("sync").lower()
    assert "relationship" in text
    assert "blacklist" in text
    assert "trust ledger" in text or "trust" in text


# ── new backend-royalties knowledge (phase 3f) ────────────────────────────────

def test_backend_royalties_file_loaded():
    """backend-royalties.md content must appear in the assembled knowledge."""
    text = registry.load_domain("sync").lower()
    assert "cue sheet" in text, (
        "backend-royalties.md content not found in assembled sync knowledge"
    )


def test_cue_sheet_mechanics_present():
    text = registry.load_domain("sync").lower()
    assert "cue sheet" in text
    assert "production company" in text
    assert "use type" in text
    assert "featured" in text
    assert "background" in text


def test_pro_registration_present():
    text = registry.load_domain("sync").lower()
    assert "ascap" in text
    assert "bmi" in text
    assert "sesac" in text
    assert "writer" in text and "publisher" in text


def test_international_pro_mechanics_present():
    text = registry.load_domain("sync").lower()
    assert "prs" in text or "prs for music" in text
    assert "reciprocal" in text
    assert "neighboring rights" in text


def test_isrc_iswc_present():
    text = registry.load_domain("sync").lower()
    assert "isrc" in text
    assert "iswc" in text
    assert "disconnect" in text or "common error" in text or "metadata error" in text


def test_territory_clearance_splits_present():
    text = registry.load_domain("sync").lower()
    assert "territorial split" in text or "territory" in text
    assert "worldwide" in text
    assert "rest of world" in text or "row" in text


def test_neighboring_rights_present():
    text = registry.load_domain("sync").lower()
    assert "neighboring rights" in text
    assert "soundexchange" in text
    assert "ppl" in text


def test_backend_royalty_flow_present():
    text = registry.load_domain("sync").lower()
    assert "performance royalty" in text
    assert "streaming" in text
    assert "discovery" in text or "shazam" in text or "multiplier" in text


def test_cue_sheet_filing_gotcha_present():
    """The critical gotcha that the production company (not the music owner) files."""
    text = registry.load_domain("sync").lower()
    assert "production company" in text
    assert "file" in text or "filing" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_sync_placement_query():
    assert "sync" in brain.route(IN_DOMAIN_QUERY)


def test_route_clearance_query_to_sync():
    assert "sync" in brain.route(
        "what is the clearance status of this track for a film sync"
    )


def test_route_music_supervisor_query_to_sync():
    assert "sync" in brain.route(
        "pitch this to a music supervisor for a television sync placement"
    )


def test_route_licensing_fee_query_to_sync():
    assert "sync" in brain.route(
        "quote a synchronization licensing fee for this placement"
    )


def test_route_unrelated_query_excludes_sync():
    # A pure touring/live query should not pull in sync
    assert "sync" not in brain.route(
        "book the arena tour and negotiate the venue deal for the shows"
    )


def test_route_irrelevant_query_returns_empty():
    assert brain.route("what should i eat for lunch") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_sync_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "sync" in result["domains"]
    assert "# Sync Licensing (sync)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("sync"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("negotiate the master use license for a film sync deal", "sync"),
        ("pitch a track to a music supervisor for a trailer placement", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
