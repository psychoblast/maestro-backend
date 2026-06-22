"""
Phase 3f — deepened playlist_dsp domain knowledge tests.

Verifies that the 'playlist_dsp' domain loads via the bank's normal path
(registry), is non-trivially sized, includes required sections from both
pre-existing and new knowledge files, and contains no forbidden entity strings.

New knowledge files added in phase 3f:
  - algorithmic-optimization-mechanics.md
  - playlist-health-vetting-playbook.md
  - release-campaign-sequencing.md

Covers (algorithmic-optimization-mechanics): algorithmic vs editorial access
distinction; signal hierarchy (save rate, completion, early-skip, user-playlist
adds, follow conversion, re-listen rate); source diversity as signal quality
modifier; editorial-to-algorithmic amplification chain; pre-save mechanics and
algorithmic value; release velocity and follower-reach gap requirements;
discovery-enrollment royalty-reduction decision framework; cross-platform signal
spillover sequence (video trend -> audio radio/autoplay lift -> editorial); and
algorithm-hostile patterns including mismatched editorial lists, long intros, and
discovery-program enrollment on active-royalty releases.

Covers (playlist-health-vetting-playbook): why vetting is non-negotiable (account
risk, analytics corpus damage, enforcement asymmetry); publicly observable vs
tool-gated signals; evidence hierarchy in vetting; seven-step vetting process
(identity/association check, fee-for-add check, follower-to-stream ratio, growth
trajectory, add-removal churn, geographic distribution, genre fit confirmation);
vetting outcome states and pitch-permission consequences (CLEARED, SOFT BLOCK,
DISQUALIFIED — three hard-block categories); target record maintenance and
re-vetting cadence; submission-review-fee nuanced case.

Covers (release-campaign-sequencing): campaign arc phases; cross-economy
sequencing logic (independent first, editorial next, algorithmic at release);
pre-release calendar from T-8 to T-1 weeks with per-milestone actions; release
week mechanics T+0 to T+7 including the algorithmic signal window; post-release
management T+8 to T+90; fast starter / slow starter / no-data protocols; multi-
release catalog campaign management (shared send ceiling, staggered release dates,
per-release prediction logs); campaign completion and prediction-log closure as a
named discipline.

Mock mode / in-process only. No network or LLM calls.
"""
import os
import json
from knowledge_bank import registry
from entity_wall_terms import assert_no_forbidden_terms


# ── helpers ──────────────────────────────────────────────────────────────────────

def _load() -> str:
    return registry.load_domain("playlist_dsp")


def _lower() -> str:
    return _load().lower()


# ── minimum-size gate ─────────────────────────────────────────────────────────────

def test_assembled_knowledge_minimum_size():
    """11 files: the assembled blob must be meaningfully large."""
    text = _load()
    assert len(text) >= 30_000, (
        f"playlist_dsp assembled text is only {len(text)} chars — expected >= 30 000"
    )


def test_assembled_knowledge_section_count():
    """11 files joined by the standard separator → at least 10 separators."""
    text = _load()
    assert text.count("\n\n---\n\n") >= 10, (
        "Expected at least 10 section separators (11 files) in assembled knowledge"
    )


# ── MANIFEST integrity ────────────────────────────────────────────────────────────

def test_manifest_includes_new_files():
    manifest_path = os.path.join(
        "knowledge_bank", "domains", "playlist_dsp", "MANIFEST.json"
    )
    with open(manifest_path) as f:
        manifest = json.load(f)
    ids = {entry["id"] for entry in manifest["files"]}
    assert "algorithmic-optimization-mechanics" in ids
    assert "playlist-health-vetting-playbook" in ids
    assert "release-campaign-sequencing" in ids


def test_manifest_load_order_contains_new_files():
    manifest_path = os.path.join(
        "knowledge_bank", "domains", "playlist_dsp", "MANIFEST.json"
    )
    with open(manifest_path) as f:
        manifest = json.load(f)
    order = manifest["load_order"]
    assert "algorithmic-optimization-mechanics" in order
    assert "playlist-health-vetting-playbook" in order
    assert "release-campaign-sequencing" in order


def test_manifest_has_eleven_files():
    manifest_path = os.path.join(
        "knowledge_bank", "domains", "playlist_dsp", "MANIFEST.json"
    )
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert len(manifest["files"]) == 11
    assert len(manifest["load_order"]) == 11


# ── algorithmic-optimization-mechanics content gates ─────────────────────────────

def test_algorithmic_mechanics_signal_hierarchy_present():
    text = _lower()
    assert "save rate" in text
    assert "completion rate" in text
    assert "early-skip" in text or "early skip" in text
    assert "user-playlist adds" in text or "user playlist adds" in text
    assert "follow conversion" in text


def test_algorithmic_mechanics_editorial_to_algorithmic_chain():
    text = _lower()
    assert "editorial-to-algorithmic" in text or "editorial to algorithmic" in text
    assert "seeding" in text
    assert "amplification" in text


def test_algorithmic_mechanics_pre_save_content():
    text = _lower()
    assert "pre-save" in text or "pre save" in text
    assert "library add" in text


def test_algorithmic_mechanics_discovery_enrollment_framework():
    text = _lower()
    assert "enrollment" in text or "enrol" in text
    assert "royalty" in text
    # The decision table covers key scenarios
    assert "evergreen" in text


def test_algorithmic_mechanics_source_diversity():
    text = _lower()
    assert "source diversity" in text or "diverse" in text


def test_algorithmic_mechanics_hostile_patterns():
    text = _lower()
    assert "algorithm-hostile" in text or "hostile pattern" in text


def test_algorithmic_mechanics_cross_platform_spillover():
    text = _lower()
    # The spillover sequence: video trend -> audio signals
    assert "spillover" in text
    assert "video" in text


def test_algorithmic_mechanics_release_velocity():
    text = _lower()
    assert "release velocity" in text


# ── playlist-health-vetting-playbook content gates ───────────────────────────────

def test_vetting_playbook_non_negotiable_section():
    text = _lower()
    assert "non-negotiable" in text or "non negotiable" in text


def test_vetting_playbook_fee_for_add_hard_block():
    text = _lower()
    assert "fee-for-add" in text or "fee for add" in text
    assert "hard block" in text


def test_vetting_playbook_follower_to_stream_ratio():
    text = _lower()
    assert "follower-to-stream" in text or "follower to stream" in text


def test_vetting_playbook_growth_trajectory():
    text = _lower()
    assert "growth trajectory" in text
    assert "spike" in text


def test_vetting_playbook_churn_check():
    text = _lower()
    assert "churn" in text


def test_vetting_playbook_geographic_distribution():
    text = _lower()
    assert "geographic" in text or "geographical" in text


def test_vetting_playbook_outcome_states_table():
    text = _lower()
    assert "cleared" in text
    assert "soft block" in text
    assert "disqualified" in text


def test_vetting_playbook_target_record_maintenance():
    text = _lower()
    assert "vetting date" in text or "re-vet" in text


def test_vetting_playbook_submission_review_fee_nuance():
    text = _lower()
    assert "review fee" in text or "submission fee" in text


def test_vetting_playbook_enforcement_risk():
    text = _lower()
    # The file covers enforcement asymmetry as a reason vetting is mandatory
    assert "enforcement" in text


# ── release-campaign-sequencing content gates ────────────────────────────────────

def test_sequencing_cross_economy_logic():
    text = _lower()
    # The default sequencing: independent first, editorial next, algorithmic at release
    assert "independent" in text
    assert "editorial" in text
    assert "algorithmic" in text


def test_sequencing_pre_release_calendar():
    text = _lower()
    # Key calendar milestones
    assert "t-8" in text or "t -8" in text or "8 weeks" in text
    assert "t-4" in text or "t -4" in text or "4 weeks" in text


def test_sequencing_release_week_mechanics():
    text = _lower()
    assert "release day" in text
    assert "t+1" in text or "t +1" in text


def test_sequencing_post_release_management():
    text = _lower()
    assert "t+14" in text or "t +14" in text or "14 days" in text
    assert "t+30" in text or "t +30" in text or "30" in text


def test_sequencing_fast_starter_protocol():
    text = _lower()
    assert "fast starter" in text


def test_sequencing_slow_starter_protocol():
    text = _lower()
    assert "slow starter" in text


def test_sequencing_no_data_protocol():
    text = _lower()
    assert "no data" in text or "no-data" in text or "very small artist" in text


def test_sequencing_multi_release_management():
    text = _lower()
    assert "multi-release" in text or "multiple" in text
    assert "stagger" in text


def test_sequencing_campaign_completion_closure():
    text = _lower()
    assert "prediction log" in text
    assert "campaign" in text and "complet" in text


def test_sequencing_algorithmic_signal_window():
    text = _lower()
    assert "signal window" in text or "72" in text


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_new_algorithmic_file_no_forbidden_terms():
    path = os.path.join(
        "knowledge_bank", "domains", "playlist_dsp",
        "algorithmic-optimization-mechanics.md"
    )
    with open(path) as f:
        content = f.read()
    assert_no_forbidden_terms(content)


def test_new_vetting_file_no_forbidden_terms():
    path = os.path.join(
        "knowledge_bank", "domains", "playlist_dsp",
        "playlist-health-vetting-playbook.md"
    )
    with open(path) as f:
        content = f.read()
    assert_no_forbidden_terms(content)


def test_new_sequencing_file_no_forbidden_terms():
    path = os.path.join(
        "knowledge_bank", "domains", "playlist_dsp",
        "release-campaign-sequencing.md"
    )
    with open(path) as f:
        content = f.read()
    assert_no_forbidden_terms(content)


def test_full_assembled_knowledge_no_forbidden_terms():
    assert_no_forbidden_terms(_load())
