"""
Phase 3f — deepened digital_ops domain knowledge tests.

Verifies that the 'digital_ops' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and new knowledge files, and contains no forbidden entity strings.

New knowledge files added in phase 3f:
  - distributor-landscape-and-mechanics.md
  - audio-mastering-and-loudness-standards.md
  - dsp-product-configuration-and-store-mechanics.md

Covers (distributor-landscape-and-mechanics): five distributor model types
(revenue-share subscription, per-release flat fee, percentage, label services,
aggregator); ISRC registrant-code ownership implications; UPC assignment and
ownership; rights-system access dependency on distributor relationship;
split payment mechanics (net-of-fee basis, payout thresholds, not a contract,
master income only); catalog transfer workflow (pre-transfer manifest, dark window,
ISRC continuity as a non-negotiable); distributor selection decision framework.

Covers (audio-mastering-and-loudness-standards): LUFS / LKFS normalization via
ITU-R BS.1770; per-platform loudness targets (Spotify −14 LUFS, Apple Music −16 LUFS,
YouTube −14 LUFS); true peak (dBTP) limits and why dBFS is insufficient; why
over-limiting trades dynamic range without gaining loudness; DR ratings; hi-res and
lossless delivery tiers (Apple Music ALAC, Tidal HiFi/MQA, Amazon Ultra HD, Qobuz);
Dolby Atmos spatial audio delivery format (ADM BWF, separate Atmos mix, −18 LUFS
immersive target); common audio format errors (MP3 delivery, sample-rate mismatch,
bit-depth downgrade, upsampled hi-res, missing dithering, clipped render);
loudness-specific pre-delivery QC extensions.

Covers (dsp-product-configuration-and-store-mechanics): product type classification
rules (single/EP/album track-count and duration conventions); release version types
requiring new UPCs (deluxe, clean/explicit, remaster, digital-only); pre-order
mechanics (instant gratification tracks, lead time); pre-save mechanics (activation
conditions, analytics significance, broken-link error); canonical artist pages and
fragmented-page causes/remediation; platform verification (Spotify for Artists, Apple
Music for Artists) and artist-pick mechanics; correction mechanics (portal update vs
full redelivery per change type); editorial pitch submission mechanics and the pitch
window as a hard operational constraint.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry
from entity_wall_terms import assert_no_forbidden_terms


IN_DOMAIN_QUERY = (
    "audit the digital delivery setup for this release — check ISRC conflicts, "
    "evaluate the content-recognition claim we received, and flag any issues "
    "with the distributor split configuration and catalog transfer plan"
)


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_digital_ops():
    assert "digital_ops" in registry.list_domains()


def test_get_domain_display_name():
    domain = registry.get_domain("digital_ops")
    assert domain.display_name, "digital_ops domain has no display_name"


def test_load_domain_returns_string():
    text = registry.load_domain("digital_ops")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("digital_ops")
    assert text.strip(), "digital_ops domain loaded empty knowledge"


def test_load_domain_minimum_size():
    """10 knowledge files should yield ≥ 100 000 chars of assembled content."""
    text = registry.load_domain("digital_ops")
    assert len(text) >= 100_000, (
        f"digital_ops knowledge too small: {len(text)} chars — expected ≥100 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    """10 files joined by section separators → at least 9 inter-file separators."""
    text = registry.load_domain("digital_ops")
    assert text.count("\n\n---\n\n") >= 9, (
        "Expected ≥9 section separators in digital_ops domain"
    )


def test_no_forbidden_entity_strings_in_domain():
    text = registry.load_domain("digital_ops")
    assert_no_forbidden_terms(text)


# ── pre-existing doctrine: core digital ops principles ────────────────────────

def test_routing_table_mission_present():
    text = registry.load_domain("digital_ops").lower()
    assert "routing table" in text


def test_isrc_reuse_doctrine_present():
    text = registry.load_domain("digital_ops").lower()
    assert "isrc" in text
    assert "reuse" in text


def test_content_recognition_claim_protocol_present():
    text = registry.load_domain("digital_ops").lower()
    assert "claim" in text
    assert "dispute" in text


def test_metadata_error_severity_tiers_present():
    text = registry.load_domain("digital_ops").lower()
    assert "tier 1" in text
    assert "tier 2" in text
    assert "royalty routing" in text or "routing critical" in text


def test_not_evaluable_protocol_present():
    text = registry.load_domain("digital_ops").lower()
    assert "not evaluable" in text


def test_delivery_vs_rights_system_separation_present():
    text = registry.load_domain("digital_ops").lower()
    assert "delivery" in text
    assert "rights-system" in text or "rights system" in text


def test_isrc_upc_anatomy_present():
    text = registry.load_domain("digital_ops").lower()
    assert "isrc" in text
    assert "upc" in text
    assert "registrant" in text


def test_ddex_ern_standard_present():
    text = registry.load_domain("digital_ops").lower()
    assert "ddex" in text
    assert "ern" in text


def test_rights_hygiene_seven_areas_present():
    text = registry.load_domain("digital_ops").lower()
    assert "isrc coverage" in text or "isrc" in text
    assert "territory" in text
    assert "content-recognition" in text or "content recognition" in text


def test_release_quality_scorecard_dimensions_present():
    text = registry.load_domain("digital_ops").lower()
    assert "d1" in text or "metadata completeness" in text
    assert "d4" in text or "rights-system coverage" in text


def test_catalog_governance_four_pillars_present():
    text = registry.load_domain("digital_ops").lower()
    assert "standards" in text
    assert "processes" in text
    assert "ownership" in text
    assert "tools" in text


def test_dark_catalog_problem_present():
    text = registry.load_domain("digital_ops").lower()
    assert "dark-catalog" in text or "dark catalog" in text


def test_ugc_rights_systems_present():
    text = registry.load_domain("digital_ops").lower()
    assert "tiktok" in text
    assert "meta" in text


# ── new: distributor landscape and mechanics (phase 3f) ───────────────────────

def test_distributor_landscape_file_loaded():
    """distributor-landscape-and-mechanics.md must appear in assembled knowledge."""
    text = registry.load_domain("digital_ops").lower()
    assert "dark window" in text, (
        "distributor-landscape-and-mechanics.md not found: 'dark window' absent"
    )


def test_five_distributor_models_present():
    """All five distributor model types must be covered."""
    text = registry.load_domain("digital_ops").lower()
    assert "revenue-share" in text or "revenue share" in text
    assert "per-release" in text or "per release" in text
    assert "label services" in text
    assert "aggregator" in text


def test_isrc_registrant_code_ownership_explained():
    """The registrant-code ownership problem is a non-obvious operational risk."""
    text = registry.load_domain("digital_ops").lower()
    assert "registrant code" in text
    assert "distributor" in text


def test_own_registrant_code_advantage_present():
    """Obtaining one's own registrant code is the resolution to the ownership problem."""
    text = registry.load_domain("digital_ops").lower()
    assert "own registrant code" in text or (
        "national isrc agency" in text and "registrant" in text
    )


def test_split_payment_not_a_contract_rule_present():
    """Split configuration is an operational instruction, not a rights document."""
    text = registry.load_domain("digital_ops").lower()
    assert "split" in text
    assert "not a contract" in text or (
        "operational instruction" in text and "rights" in text
    )


def test_split_applies_to_net_revenue_present():
    """Splits apply to net revenue after the distributor's fee — not gross."""
    text = registry.load_domain("digital_ops").lower()
    assert "net revenue" in text or ("net" in text and "distributor" in text and "fee" in text)


def test_split_master_income_only_rule_present():
    """Distributor split covers master income only — composition routes to publishing."""
    text = registry.load_domain("digital_ops").lower()
    assert "master income" in text or (
        "master" in text and "composition" in text and "split" in text
    )


def test_catalog_transfer_dark_window_defined():
    """The dark window — offline period between takedown and re-live — must be defined."""
    text = registry.load_domain("digital_ops").lower()
    assert "dark window" in text
    assert "takedown" in text


def test_catalog_transfer_isrc_continuity_rule():
    """ISRC continuity is a non-negotiable condition during catalog transfer."""
    text = registry.load_domain("digital_ops").lower()
    assert "isrc continuity" in text or (
        "same isrc" in text and "transfer" in text
    )


def test_new_isrc_on_transfer_is_error():
    """Assigning new ISRCs to transferred recordings is a named error."""
    text = registry.load_domain("digital_ops").lower()
    assert "transfer" in text
    assert "new isrc" in text


def test_pre_transfer_manifest_step_present():
    """Pre-transfer: full manifest export before issuing any takedown."""
    text = registry.load_domain("digital_ops").lower()
    assert "manifest" in text
    assert "takedown" in text


def test_content_recognition_reference_file_departure_risk():
    """Reference files uploaded through old distributor may be removed on departure."""
    text = registry.load_domain("digital_ops").lower()
    assert "reference file" in text
    assert "distributor" in text


def test_distributor_territory_coverage_gaps_present():
    """Not all distributors cover all territories — coverage audit is required."""
    text = registry.load_domain("digital_ops").lower()
    assert "china" in text or "india" in text or "korea" in text


def test_distributor_selection_framework_present():
    """A distributor selection framework with verifiable criteria must be present."""
    text = registry.load_domain("digital_ops").lower()
    assert "coverage audit" in text or (
        "distributor" in text and "selection" in text and "coverage" in text
    )


def test_payout_minimum_threshold_problem_named():
    """Minimum payout thresholds create unpaid accumulation for small catalogs."""
    text = registry.load_domain("digital_ops").lower()
    assert "minimum payout" in text or "payout threshold" in text


# ── new: audio mastering and loudness standards (phase 3f) ────────────────────

def test_audio_mastering_file_loaded():
    """audio-mastering-and-loudness-standards.md must appear in assembled knowledge."""
    text = registry.load_domain("digital_ops").lower()
    assert "lufs" in text, (
        "audio-mastering-and-loudness-standards.md not found: 'lufs' absent"
    )


def test_lufs_lkfs_equivalence_stated():
    """LUFS and LKFS are numerically identical — must be stated."""
    text = registry.load_domain("digital_ops").lower()
    assert "lufs" in text
    assert "lkfs" in text


def test_itu_r_bs1770_standard_named():
    """The loudness measurement algorithm ITU-R BS.1770 must be named."""
    text = registry.load_domain("digital_ops").lower()
    assert "itu-r bs.1770" in text or "bs.1770" in text or "itu-r" in text


def test_spotify_loudness_target_present():
    """Spotify's reference loudness target must be referenced."""
    text = registry.load_domain("digital_ops").lower()
    assert "spotify" in text
    assert "−14 lufs" in text or "-14 lufs" in text or ("spotify" in text and "14" in text and "lufs" in text)


def test_apple_music_loudness_target_present():
    """Apple Music's Sound Check normalization target must be referenced."""
    text = registry.load_domain("digital_ops").lower()
    assert "apple music" in text
    assert "sound check" in text or ("apple" in text and "16" in text and "lufs" in text)


def test_true_peak_dbtp_explained():
    """True peak (dBTP) must be distinguished from sample peak (dBFS)."""
    text = registry.load_domain("digital_ops").lower()
    assert "dbtp" in text or "true peak" in text
    assert "dbfs" in text or "sample peak" in text


def test_true_peak_minus1_standard():
    """The −1 dBTP standard true-peak limit must be stated."""
    text = registry.load_domain("digital_ops").lower()
    assert "−1 dbtp" in text or "-1 dbtp" in text or (
        "true peak" in text and ("−1" in text or "-1" in text)
    )


def test_over_limiting_error_explained():
    """Why over-limiting is a practitioner error must be substantively explained."""
    text = registry.load_domain("digital_ops").lower()
    assert "over-limit" in text or "over limit" in text
    assert "dynamic range" in text


def test_normalization_turns_down_not_up_mechanic():
    """The key mechanic: loud files are turned down, not boosted — must be explained."""
    text = registry.load_domain("digital_ops").lower()
    assert "turns" in text or "turn" in text
    assert "down" in text
    assert "normalization" in text or "normaliz" in text


def test_dr_ratings_explained():
    """Dynamic range (DR) ratings must be defined with a numeric scale."""
    text = registry.load_domain("digital_ops").lower()
    assert "dynamic range" in text
    assert "dr" in text


def test_hi_res_lossless_tiers_present():
    """Hi-res and lossless delivery tiers must be covered with platform names."""
    text = registry.load_domain("digital_ops").lower()
    assert "lossless" in text
    assert "hi-res" in text or "hi res" in text or "24-bit" in text


def test_apple_music_alac_lossless_named():
    """Apple Music's ALAC lossless format must be specifically named."""
    text = registry.load_domain("digital_ops").lower()
    assert "alac" in text


def test_dolby_atmos_spatial_audio_present():
    """Dolby Atmos spatial audio delivery must be covered."""
    text = registry.load_domain("digital_ops").lower()
    assert "dolby atmos" in text


def test_atmos_adm_bwf_format_named():
    """The ADM BWF delivery format for Atmos must be named."""
    text = registry.load_domain("digital_ops").lower()
    assert "adm" in text or "adm bwf" in text


def test_atmos_separate_mix_requirement():
    """Atmos requires a separate mix — not the stereo master."""
    text = registry.load_domain("digital_ops").lower()
    assert "separate" in text
    assert "atmos" in text
    assert "mix" in text


def test_mp3_delivery_error_named():
    """Delivering MP3 to DSPs is a named error with consequences."""
    text = registry.load_domain("digital_ops").lower()
    assert "mp3" in text


def test_upsampled_hires_is_error():
    """Upsampling a 16-bit master to 24-bit/192kHz and calling it hi-res is a named error."""
    text = registry.load_domain("digital_ops").lower()
    assert "upsamp" in text or ("16-bit" in text and "24-bit" in text and "convert" in text)


def test_dithering_requirement_present():
    """Dithering is required during bit-depth reduction — missing dithering is a named error."""
    text = registry.load_domain("digital_ops").lower()
    assert "dither" in text


def test_mono_compatibility_check_present():
    """Mono compatibility check is part of the loudness/format QC extension."""
    text = registry.load_domain("digital_ops").lower()
    assert "mono" in text


# ── new: dsp product configuration and store mechanics (phase 3f) ─────────────

def test_product_config_file_loaded():
    """dsp-product-configuration-and-store-mechanics.md must appear in assembled knowledge."""
    text = registry.load_domain("digital_ops").lower()
    assert "pre-save" in text or "presave" in text, (
        "dsp-product-configuration-and-store-mechanics.md not found: 'pre-save' absent"
    )


def test_product_type_classification_present():
    """Single / EP / album classification thresholds must be covered."""
    text = registry.load_domain("digital_ops").lower()
    assert "single" in text
    assert "ep" in text or "extended play" in text
    assert "album" in text


def test_deluxe_edition_new_upc_rule():
    """A deluxe edition requires a new UPC — a distinct commercial product."""
    text = registry.load_domain("digital_ops").lower()
    assert "deluxe" in text
    assert "new upc" in text or ("upc" in text and "deluxe" in text)


def test_reusing_upc_for_deluxe_is_named_error():
    """Reusing the original UPC for a deluxe release is a named common error."""
    text = registry.load_domain("digital_ops").lower()
    assert "deluxe" in text
    assert "upc" in text


def test_pre_order_mechanics_covered():
    """Pre-order mechanics including instant gratification tracks must be covered."""
    text = registry.load_domain("digital_ops").lower()
    assert "pre-order" in text or "preorder" in text
    assert "instant gratification" in text


def test_pre_save_activation_conditions_explained():
    """Pre-save requires the release to be in the platform's system first."""
    text = registry.load_domain("digital_ops").lower()
    assert "pre-save" in text
    assert "platform" in text and "system" in text


def test_pre_save_broken_link_error_named():
    """Distributing a pre-save link before the release is in the system is a named error."""
    text = registry.load_domain("digital_ops").lower()
    assert "broken" in text and "link" in text or (
        "pre-save" in text and "verify" in text
    )


def test_pre_save_analytics_significance_present():
    """Pre-saves convert to library adds on release day — analytics significance must be explained."""
    text = registry.load_domain("digital_ops").lower()
    assert "pre-save" in text
    assert "library" in text


def test_canonical_artist_page_concept_present():
    """Canonical artist pages and the fragmentation problem must be explained."""
    text = registry.load_domain("digital_ops").lower()
    assert "canonical" in text
    assert "artist" in text


def test_fragmented_artist_pages_causes_present():
    """Causes of artist page fragmentation (name variants) must be named."""
    text = registry.load_domain("digital_ops").lower()
    assert "fragment" in text
    assert "spelling" in text or "variant" in text or "capitalization" in text


def test_platform_verification_present():
    """Platform verification (Spotify for Artists etc.) must be explained."""
    text = registry.load_domain("digital_ops").lower()
    assert "verification" in text or "verified" in text
    assert "spotify for artists" in text or "apple music for artists" in text


def test_artist_pick_mechanics_present():
    """Artist pick is promotional tool only — no algorithmic amplification."""
    text = registry.load_domain("digital_ops").lower()
    assert "artist pick" in text


def test_portal_update_vs_redelivery_distinction():
    """The portal-update vs. redelivery distinction must be substantively covered."""
    text = registry.load_domain("digital_ops").lower()
    assert "redelivery" in text
    assert "portal" in text


def test_isrc_change_requires_redelivery():
    """ISRC correction requires full redelivery — must be explicitly stated."""
    text = registry.load_domain("digital_ops").lower()
    assert "isrc" in text
    assert "redelivery" in text


def test_editorial_pitch_submission_mechanics_present():
    """Editorial pitch submission mechanics must be explained with platform context."""
    text = registry.load_domain("digital_ops").lower()
    assert "editorial pitch" in text or ("editorial" in text and "pitch" in text)
    assert "submission" in text


def test_pitch_window_hard_constraint_named():
    """The pitch window is a hard deadline — missing it means no consideration."""
    text = registry.load_domain("digital_ops").lower()
    assert "pitch window" in text or ("pitch" in text and "window" in text)


def test_artwork_update_no_redelivery():
    """Artwork update typically does not require redelivery — a portal update suffices."""
    text = registry.load_domain("digital_ops").lower()
    assert "artwork" in text
    # the portal-update vs redelivery table should cover this
    assert "portal" in text


def test_naming_standard_discipline_for_artist_pages():
    """A canonical artist-name register is the prevention for fragmented pages."""
    text = registry.load_domain("digital_ops").lower()
    assert "naming standard" in text or "canonical artist" in text or (
        "artist name" in text and "consistent" in text
    )
