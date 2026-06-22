"""
Phase 3f — deepened production domain knowledge tests.

Verifies that the 'production' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and new knowledge files, and contains no forbidden entity strings.

New knowledge file added in phase 3f:
  - production-workflow-and-craft.md

Covers: pre-production workflow (arrangement map, production-ready gate,
pre-production session protocol), tracking session management (take types,
safety-take protocol, vocal direction discipline), vocal production (comp
session workflow, pitch correction approach and disclosure rule, double-track
and vocal layering), mixing workflow and discipline (bus structure, low-end
management, revision discipline), mastering essentials (what mastering
does/doesn't do, mastering brief, stem mastering, Dolby Atmos/spatial audio),
genre-specific production conventions (hip-hop/trap, R&B, Afrobeats, UK drill,
pop, reggaeton), multi-song production arc (cohesion tools, EP vs album scope,
inter-track level matching), and sync-ready production (split mix
specification, dialogue-friendly TV track, music-to-picture timing).

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "find the right producer for this track, set up the recording session, "
    "and get the master delivered to the streaming spec"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_production():
    assert "production" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("production").display_name == "Production"


def test_get_domain_slug():
    assert registry.get_domain("production").slug == "producer-connect"


def test_load_domain_returns_string():
    text = registry.load_domain("production")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("production")
    assert text.strip(), "production domain loaded empty knowledge"


def test_load_domain_minimum_size():
    # 6 knowledge files (5 existing + new workflow-and-craft file)
    # total assembled content expected >= 90 000 chars
    text = registry.load_domain("production")
    assert len(text) >= 90_000, (
        f"production knowledge too small: {len(text)} chars — expected ≥90 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    # 6 files joined by section separators → at least 5 separators
    text = registry.load_domain("production")
    assert text.count("\n\n---\n\n") >= 5, (
        "Expected ≥5 section separators (6 knowledge files) in production domain"
    )


# ── pre-existing doctrine presence ───────────────────────────────────────────

def test_doctrine_master_is_the_asset_present():
    text = registry.load_domain("production").lower()
    assert "the master is the asset" in text or "master is the asset" in text


def test_doctrine_eight_principles_present():
    text = registry.load_domain("production").lower()
    assert "qc-cleared" in text or "qc cleared" in text or "done" in text and "qc" in text


def test_scope_fences_present():
    text = registry.load_domain("production").lower()
    assert "a&r" in text
    assert "sync" in text
    assert "publishing" in text
    assert "flag" in text and "defer" in text


def test_evidence_classification_present():
    text = registry.load_domain("production").lower()
    assert "measured" in text
    assert "sourced" in text
    assert "judged" in text
    assert "absent" in text


def test_technical_antifabrication_present():
    text = registry.load_domain("production").lower()
    assert "fabricated" in text or "fabrication" in text
    assert "measurement" in text


def test_beat_licensing_tiers_present():
    text = registry.load_domain("production").lower()
    assert "non-exclusive" in text or "non exclusive" in text
    assert "exclusive" in text
    assert "buyout" in text


def test_sample_clearance_present():
    text = registry.load_domain("production").lower()
    assert "sample clearance" in text or "sample-clearance" in text
    assert "uncleared" in text


def test_producer_economics_present():
    text = registry.load_domain("production").lower()
    assert "recoupment" in text
    assert "advance" in text
    assert "work-for-hire" in text or "work for hire" in text


def test_studio_budget_constraint_map_present():
    text = registry.load_domain("production").lower()
    assert "constraint map" in text
    assert "contingency" in text
    assert "change-order" in text or "change order" in text


def test_readiness_rubric_dimensions_present():
    text = registry.load_domain("production").lower()
    assert "creative direction clarity" in text
    assert "producer / team fit" in text or "producer team fit" in text or "producer/team fit" in text
    assert "technical quality" in text
    assert "delivery & qc" in text or "delivery and qc" in text


def test_hard_gates_present():
    text = registry.load_domain("production").lower()
    assert "not deliverable" in text
    assert "release blocked" in text


def test_lufs_true_peak_present():
    text = registry.load_domain("production").lower()
    assert "lufs" in text
    assert "true-peak" in text or "true peak" in text


def test_output_templates_present():
    text = registry.load_domain("production").lower()
    assert "production plan" in text
    assert "production readiness scorecard" in text
    assert "delivery & qc checklist" in text or "delivery and qc checklist" in text


# ── new production-workflow-and-craft knowledge (phase 3f) ───────────────────

def test_workflow_file_loaded():
    """production-workflow-and-craft.md content must appear."""
    text = registry.load_domain("production").lower()
    assert "arrangement map" in text, (
        "production-workflow-and-craft.md content not found in assembled knowledge"
    )


def test_pre_production_workflow_present():
    text = registry.load_domain("production").lower()
    assert "pre-production" in text
    assert "arrangement map" in text
    assert "energy arc" in text


def test_preproduction_session_protocol_present():
    text = registry.load_domain("production").lower()
    # Three-session protocol for a single
    assert "reference and concept" in text
    assert "structure and arrangement" in text
    assert "pre-production demo" in text


def test_production_ready_gate_present():
    text = registry.load_domain("production").lower()
    assert "production-ready" in text or "production ready" in text
    assert "booking tracking" in text or "book tracking" in text or "book a tracking" in text


def test_key_verification_present():
    """Checking vocalist range before booking is a non-obvious, important recommendation."""
    text = registry.load_domain("production").lower()
    assert "vocalist's range" in text or "vocalist range" in text or "vocal" in text and "range" in text and "key" in text


def test_tracking_session_take_types_present():
    text = registry.load_domain("production").lower()
    assert "tracking take" in text
    assert "safety take" in text
    assert "punch take" in text
    assert "alt-arrangement" in text or "alt arrangement" in text


def test_session_signoff_protocol_present():
    text = registry.load_domain("production").lower()
    assert "session sign-off" in text or "session signoff" in text or "sign-off protocol" in text
    assert "backup" in text or "backed up" in text


def test_vocal_direction_discipline_present():
    text = registry.load_domain("production").lower()
    assert "vocal direction" in text
    assert "feeling" in text or "image" in text
    assert "technical instruction" in text


def test_comp_session_workflow_present():
    text = registry.load_domain("production").lower()
    assert "comp session" in text
    assert "comp" in text and "take" in text


def test_pitch_correction_approach_present():
    text = registry.load_domain("production").lower()
    assert "pitch correction" in text
    assert "transparent" in text
    assert "stylized" in text


def test_pitch_correction_disclosure_rule_present():
    text = registry.load_domain("production").lower()
    assert "disclosure" in text
    assert "extent" in text
    assert "approve" in text or "approved" in text


def test_pitch_correction_order_of_operations_present():
    text = registry.load_domain("production").lower()
    assert "timing" in text and "pitch" in text
    assert "order" in text or "step" in text


def test_double_track_present():
    text = registry.load_domain("production").lower()
    assert "double-track" in text or "double track" in text
    assert "micro" in text  # micro-timing / micro-pitch deviation


def test_vocal_stack_layers_present():
    text = registry.load_domain("production").lower()
    assert "lead" in text
    assert "harmony" in text or "harmonies" in text
    assert "ad lib" in text or "ad libs" in text


def test_mix_session_setup_present():
    text = registry.load_domain("production").lower()
    assert "mix reference" in text
    assert "gain" in text and "staging" in text or "gain structure" in text


def test_low_end_management_present():
    text = registry.load_domain("production").lower()
    assert "low-end" in text or "low end" in text
    assert "high-pass" in text or "high pass" in text
    assert "mono" in text and "sub" in text


def test_bus_structure_present():
    text = registry.load_domain("production").lower()
    assert "bus structure" in text or "bus architecture" in text
    assert "master bus" in text or "master fader" in text


def test_mix_revision_discipline_present():
    text = registry.load_domain("production").lower()
    assert "revision" in text and ("round" in text or "rounds" in text)
    assert "documented" in text or "in writing" in text


def test_mastering_scope_present():
    text = registry.load_domain("production").lower()
    assert "mastering" in text
    assert "tonal balance" in text or "tonal correction" in text
    assert "loudness management" in text or "loudness" in text and "mastering" in text


def test_mastering_cannot_fix_present():
    """Non-obvious but critical: mastering cannot fix fundamental mix problems."""
    text = registry.load_domain("production").lower()
    assert "cannot fix" in text or "cannot be fixed" in text


def test_mastering_brief_present():
    text = registry.load_domain("production").lower()
    assert "mastering brief" in text


def test_mastering_headroom_guidance_present():
    text = registry.load_domain("production").lower()
    assert "headroom" in text and "mastering" in text


def test_stem_mastering_present():
    text = registry.load_domain("production").lower()
    assert "stem mastering" in text
    assert "full-mix mastering" in text or "full mix mastering" in text


def test_stem_mastering_sum_requirement_present():
    """Stems must sum to the stereo mix — non-obvious requirement."""
    text = registry.load_domain("production").lower()
    assert "sum" in text and "stereo" in text


def test_spatial_audio_atmos_present():
    text = registry.load_domain("production").lower()
    assert "atmos" in text or "dolby atmos" in text or "spatial audio" in text
    assert "immersive" in text or "binaural" in text


def test_spatial_audio_separate_workflow_present():
    """Atmos requires a separate workflow — not automatic from stereo master."""
    text = registry.load_domain("production").lower()
    assert ("separate" in text and "atmos" in text) or (
        "separate" in text and "spatial" in text
    ) or "separate" in text and "immersive" in text


def test_genre_conventions_section_present():
    text = registry.load_domain("production").lower()
    assert "genre" in text and "convention" in text


def test_hip_hop_trap_conventions_present():
    text = registry.load_domain("production").lower()
    assert "trap" in text
    assert "808" in text
    assert "sub-bass" in text or "sub bass" in text


def test_808_melodic_instrument_present():
    """808 as a melodic instrument, not just texture — non-obvious."""
    text = registry.load_domain("production").lower()
    assert "808" in text and ("melodic" in text or "note choice" in text or "pitch" in text)


def test_rnb_conventions_present():
    text = registry.load_domain("production").lower()
    assert "r&b" in text or "rnb" in text or "r and b" in text
    assert "humanized" in text or "humanised" in text


def test_afrobeats_conventions_present():
    text = registry.load_domain("production").lower()
    assert "afrobeats" in text or "afropop" in text
    assert "percussion" in text and ("co-equal" in text or "co equal" in text or "equal" in text)


def test_amapiano_present():
    text = registry.load_domain("production").lower()
    assert "amapiano" in text
    assert "log drum" in text or "log-drum" in text


def test_uk_drill_conventions_present():
    text = registry.load_domain("production").lower()
    assert "drill" in text
    assert "sliding" in text or "slide" in text
    assert "808" in text and "glide" in text


def test_pop_conventions_present():
    text = registry.load_domain("production").lower()
    assert "pop" in text
    assert "hook" in text
    assert "radio edit" in text or "radio-edit" in text


def test_reggaeton_dembow_present():
    text = registry.load_domain("production").lower()
    assert "reggaeton" in text
    assert "dembow" in text


def test_multi_song_cohesion_present():
    text = registry.load_domain("production").lower()
    assert "cohesion" in text
    assert "sonic thread" in text


def test_ep_album_scope_present():
    text = registry.load_domain("production").lower()
    assert "ep" in text
    assert "album" in text
    assert "sequencing" in text


def test_inter_track_level_matching_present():
    """Inter-track level matching is a distinct deliverable — non-obvious."""
    text = registry.load_domain("production").lower()
    assert "inter-track" in text or "inter track" in text
    assert "level" in text


def test_sync_ready_production_present():
    text = registry.load_domain("production").lower()
    assert "sync" in text
    assert "split mix" in text


def test_sync_clean_session_present():
    text = registry.load_domain("production").lower()
    assert "clean session" in text or "uncleared" in text and "sync" in text


def test_split_mix_versions_present():
    text = registry.load_domain("production").lower()
    assert "instrumental" in text
    assert "vocal up" in text or "vocal +3" in text or "+3 db" in text
    assert "dialogue-friendly" in text or "dialogue friendly" in text or "tv track" in text


def test_music_to_picture_timing_present():
    text = registry.load_domain("production").lower()
    assert "music-to-picture" in text or "music to picture" in text or "picture timing" in text
    assert "structural" in text and "boundary" in text or "downbeat" in text


def test_loop_version_for_sync_present():
    text = registry.load_domain("production").lower()
    assert "loop" in text and "sync" in text


# ── brain routing ─────────────────────────────────────────────────────────────

def test_route_production_query():
    assert "production" in brain.route(IN_DOMAIN_QUERY)


def test_route_producer_search_to_production():
    assert "production" in brain.route(
        "find a producer who can make this beat for the track"
    )


def test_route_mixing_query_to_production():
    assert "production" in brain.route(
        "hire a mixing engineer for the album and deliver the stems"
    )


def test_route_mastering_query_to_production():
    assert "production" in brain.route(
        "book the mastering session and deliver to the streaming spec"
    )


def test_route_vocal_production_to_production():
    assert "production" in brain.route(
        "set up the vocal production workflow for the recording session"
    )


def test_route_loudness_query_to_production():
    assert "production" in brain.route(
        "what are the lufs and loudness requirements for this streaming release"
    )


def test_route_tour_booking_excludes_production():
    assert "production" not in brain.route(
        "book the arena tour and negotiate the guarantee with the promoter"
    )


def test_route_publishing_registration_excludes_production():
    assert "production" not in brain.route(
        "register this composition with our publishing entity and file the split sheet"
    )


def test_route_irrelevant_query_returns_empty():
    assert brain.route("what should i eat for lunch") == []


# ── consult ───────────────────────────────────────────────────────────────────

def test_consult_returns_production_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "production" in result["domains"]
    assert "# Production (production)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("production"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("find a producer for this track and set up the recording session", "production"),
        ("mix engineer and mastering engineer for the album", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
