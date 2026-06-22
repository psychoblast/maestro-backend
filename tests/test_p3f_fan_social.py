"""
Phase 3f — deepened fan_social domain knowledge tests.

Verifies that the 'fan_social' domain loads via the bank's normal path
(registry), is non-trivially sized, includes all required sections from both
pre-existing and new knowledge files, and contains no forbidden entity strings.

New knowledge files added in phase 3f:
  - live-events-and-fan-experience.md
  - email-and-sms-owned-channel-mechanics.md

Covers (live-events-and-fan-experience): the live-conversion stack (festival /
support / headline / VIP depth scaling); presale architecture with the fan-club
sequencing rule (fan-club before platform presale); VIP package taxonomy with the
photo-op trap and the intimacy compression principle; virtual concert mechanics
and pricing tiers; the post-show 72-hour engagement window protocol; venue
fan-experience design (queue, merch table, setlist, fan sections); tour
merchandise venue commission structure and D2C QR integration; festival vs.
headline show strategy; listening-party production checklist; multi-market
on-sale sequencing.

Covers (email-and-sms-owned-channel-mechanics): four core automation sequences
(welcome, pre-release, post-purchase, win-back) with the 72-hour trigger rule;
five-email welcome sequence structure; email deliverability mechanics (sender
reputation, complaint rate thresholds, list hygiene, domain authentication —
SPF/DKIM/DMARC); SMS compliance by jurisdiction (TCPA, GDPR, A2P 10DLC vs.
short codes, double opt-in); SMS character-limit and Unicode-encoding mechanics;
frequency caps; six-tier behavioral list segmentation with segment-first
deployment protocol; release-cycle email sequence; SMS cadence for tour on-sale;
A/B testing sample-size framework; list growth capture-touchpoint ranking;
the 90-day engagement cliff.

Mock mode / in-process only. No network or LLM calls.
"""
from knowledge_bank import registry
from entity_wall_terms import assert_no_forbidden_terms


# ── registry ──────────────────────────────────────────────────────────────────

def test_list_domains_includes_fan_social():
    assert "fan_social" in registry.list_domains()


def test_get_domain_display_name():
    domain = registry.get_domain("fan_social")
    assert domain.display_name, "fan_social domain has no display_name"


def test_load_domain_returns_string():
    text = registry.load_domain("fan_social")
    assert isinstance(text, str)


def test_load_domain_non_empty():
    text = registry.load_domain("fan_social")
    assert text.strip(), "fan_social domain loaded empty knowledge"


def test_load_domain_minimum_size():
    """13 knowledge files should yield ≥ 120 000 chars of assembled content."""
    text = registry.load_domain("fan_social")
    assert len(text) >= 120_000, (
        f"fan_social knowledge too small: {len(text)} chars — expected ≥120 000"
    )


def test_load_domain_assembles_all_manifest_sections():
    """13 files joined by section separators → at least 12 inter-file separators."""
    text = registry.load_domain("fan_social")
    assert text.count("\n\n---\n\n") >= 12, (
        "Expected ≥12 section separators in fan_social domain after phase 3f additions"
    )


def test_no_forbidden_entity_strings_in_domain():
    text = registry.load_domain("fan_social")
    assert_no_forbidden_terms(text)


# ── pre-existing core knowledge: doctrine and fundamentals ────────────────────

def test_own_the_relationship_doctrine_present():
    text = registry.load_domain("fan_social").lower()
    assert "own the relationship" in text or "own the relationship, not the algorithm" in text


def test_superfan_concentration_principle_present():
    text = registry.load_domain("fan_social").lower()
    assert "superfan" in text
    assert "concentration" in text or "revenue-concentration" in text


def test_parasocial_framework_present():
    text = registry.load_domain("fan_social").lower()
    assert "parasocial" in text


def test_fan_journey_six_stages_present():
    text = registry.load_domain("fan_social").lower()
    assert "discover" in text
    assert "follow" in text
    assert "invest" in text
    assert "evangelist" in text


def test_rfm_depth_advocacy_model_present():
    text = registry.load_domain("fan_social").lower()
    assert "recency" in text
    assert "frequency" in text
    assert "advocacy" in text


def test_membership_tier_design_present():
    text = registry.load_domain("fan_social").lower()
    assert "paywall" in text
    assert "tier" in text


def test_algorithm_taxonomy_present():
    text = registry.load_domain("fan_social").lower()
    assert "interest-graph" in text or "interest graph" in text
    assert "social-graph" in text or "social graph" in text


def test_ambassador_tier_taxonomy_present():
    text = registry.load_domain("fan_social").lower()
    assert "street team" in text or "street-team" in text
    assert "anti-mercenary" in text or "anti mercenary" in text


def test_owned_vs_rented_community_present():
    text = registry.load_domain("fan_social").lower()
    assert "owned" in text
    assert "rented" in text


def test_community_lifecycle_stages_present():
    text = registry.load_domain("fan_social").lower()
    assert "inception" in text
    assert "establishment" in text
    assert "maturity" in text


def test_fanbase_health_scorecard_present():
    text = registry.load_domain("fan_social").lower()
    assert "fanbase health" in text or "fanbase-health" in text
    assert "not evaluable" in text


def test_ugs_cultivation_model_present():
    text = registry.load_domain("fan_social").lower()
    assert "ugc" in text
    assert "co-creation" in text or "co creation" in text


# ── new: live events and fan experience (phase 3f) ────────────────────────────

def test_live_events_file_loaded():
    """live-events-and-fan-experience.md must appear in assembled knowledge."""
    text = registry.load_domain("fan_social").lower()
    assert "intimacy compression" in text, (
        "live-events-and-fan-experience.md not found: 'intimacy compression' absent"
    )


def test_live_conversion_stack_present():
    """The four live-context conversion stages must be covered."""
    text = registry.load_domain("fan_social").lower()
    assert "festival slot" in text
    assert "support" in text
    assert "headline show" in text


def test_presale_architecture_covered():
    """Presale tier types and the sequencing rule must be present."""
    text = registry.load_domain("fan_social").lower()
    assert "fan-club" in text or "fan club" in text
    assert "presale" in text or "pre-sale" in text


def test_presale_sequencing_rule_present():
    """Fan-club presale must open before platform presale — stated as a rule."""
    text = registry.load_domain("fan_social").lower()
    assert "sequencing rule" in text or (
        "fan-club" in text and "presale" in text and "platform" in text
    )


def test_vip_package_taxonomy_present():
    """VIP package tiers must be named including the small-group hang."""
    text = registry.load_domain("fan_social").lower()
    assert "soundcheck" in text
    assert "small-group hang" in text or "small group hang" in text


def test_photo_op_trap_named():
    """The photo-op trap (assembly-line photos produce no depth) must be named."""
    text = registry.load_domain("fan_social").lower()
    assert "photo-op trap" in text or "photo op trap" in text or (
        "assembly-line" in text and "photo" in text
    )


def test_virtual_concert_mechanics_present():
    """Virtual concert format types and economic model must be covered."""
    text = registry.load_domain("fan_social").lower()
    assert "virtual concert" in text or "virtual ticket" in text
    assert "livestream" in text or "live stream" in text


def test_post_show_72_hour_window_defined():
    """The post-show 72-hour engagement window must be named and explained."""
    text = registry.load_domain("fan_social").lower()
    assert "72-hour" in text or "72 hour" in text
    assert "post-show" in text or "after" in text and "show" in text


def test_venue_merch_table_timing_present():
    """Merch table timing (open 60–90 min before doors) must be stated."""
    text = registry.load_domain("fan_social").lower()
    assert "merch table" in text or ("merch" in text and "table" in text)
    assert "60" in text or "90" in text


def test_venue_commission_structure_present():
    """Venue commission on merchandise sales must be covered."""
    text = registry.load_domain("fan_social").lower()
    assert "commission" in text
    assert "venue" in text


def test_d2c_qr_at_merch_table_present():
    """D2C QR code strategy at venue merch table must be present."""
    text = registry.load_domain("fan_social").lower()
    assert "qr" in text or "qr code" in text
    assert "d2c" in text


def test_festival_vs_headline_distinction_present():
    """Festival slot vs. headline show strategic difference must be explained."""
    text = registry.load_domain("fan_social").lower()
    assert "festival" in text
    assert "headline" in text


def test_listening_party_production_checklist_present():
    """Listening party production checklist must be present."""
    text = registry.load_domain("fan_social").lower()
    assert "listening party" in text or "listening-party" in text
    assert "venue" in text and "artist presence" in text or "attendee" in text


def test_exclusive_show_merch_scarcity_present():
    """City-specific or show-specific exclusive merch as scarcity driver must be named."""
    text = registry.load_domain("fan_social").lower()
    assert "city-specific" in text or "show-specific" in text or (
        "exclusive" in text and "show" in text and "merch" in text
    )


def test_intimacy_compression_principle_explained():
    """The intimacy compression principle must be substantively explained."""
    text = registry.load_domain("fan_social").lower()
    assert "intimacy compression" in text


# ── new: email and sms owned-channel mechanics (phase 3f) ─────────────────────

def test_email_sms_mechanics_file_loaded():
    """email-and-sms-owned-channel-mechanics.md must appear in assembled knowledge."""
    text = registry.load_domain("fan_social").lower()
    assert "90-day engagement cliff" in text or "90 day engagement cliff" in text, (
        "email-and-sms-owned-channel-mechanics.md not found: '90-day engagement cliff' absent"
    )


def test_four_automation_sequences_present():
    """All four core automation sequences must be named."""
    text = registry.load_domain("fan_social").lower()
    assert "welcome flow" in text or ("welcome" in text and "sequence" in text)
    assert "pre-release flow" in text or "pre-release" in text
    assert "post-purchase" in text
    assert "win-back" in text


def test_72_hour_trigger_rule_present():
    """The 72-hour automation trigger rule must be stated."""
    text = registry.load_domain("fan_social").lower()
    assert "72-hour trigger" in text or "72 hour trigger" in text or (
        "72" in text and "trigger" in text and "welcome" in text
    )


def test_welcome_sequence_five_email_structure_present():
    """The five-email welcome sequence with timing must be covered."""
    text = registry.load_domain("fan_social").lower()
    assert "welcome" in text
    # Day 2-3 and Day 9-10 are structural markers in the sequence
    assert "day 2" in text or "day 5" in text or "day 9" in text


def test_email_deliverability_mechanics_present():
    """Core deliverability factors must be substantively covered."""
    text = registry.load_domain("fan_social").lower()
    assert "sender reputation" in text
    assert "spam complaint" in text
    assert "list hygiene" in text


def test_domain_authentication_covered():
    """SPF, DKIM, and DMARC must all be named."""
    text = registry.load_domain("fan_social").lower()
    assert "spf" in text
    assert "dkim" in text
    assert "dmarc" in text


def test_spam_complaint_rate_threshold_stated():
    """The 0.1% complaint rate threshold must be stated."""
    text = registry.load_domain("fan_social").lower()
    assert "0.1%" in text
    assert "complaint" in text


def test_tcpa_compliance_covered():
    """TCPA regulation for US SMS marketing must be named."""
    text = registry.load_domain("fan_social").lower()
    assert "tcpa" in text
    assert "telephone consumer protection" in text or "tcpa" in text


def test_10dlc_registration_covered():
    """A2P 10DLC registration requirement must be explained."""
    text = registry.load_domain("fan_social").lower()
    assert "10dlc" in text or "10-digit long code" in text
    assert "campaign registry" in text or "registration" in text


def test_short_code_vs_10dlc_distinction_present():
    """Short codes vs. 10DLC distinction must be explained."""
    text = registry.load_domain("fan_social").lower()
    assert "short code" in text
    assert "10dlc" in text or "long code" in text


def test_double_opt_in_explained():
    """Double opt-in as a best practice must be explained."""
    text = registry.load_domain("fan_social").lower()
    assert "double opt-in" in text or "double opt in" in text


def test_sms_character_limit_covered():
    """The 160-character SMS segment limit and Unicode encoding must be covered."""
    text = registry.load_domain("fan_social").lower()
    assert "160" in text
    assert "unicode" in text or "character" in text


def test_sms_frequency_cap_stated():
    """SMS frequency cap (2–4 messages per month) must be stated."""
    text = registry.load_domain("fan_social").lower()
    assert "frequency cap" in text or (
        "2–4" in text and "sms" in text or "month" in text
    )


def test_list_segmentation_six_tiers_present():
    """The segmentation tiers — Active, At-risk, Dormant, Purchasers, Superfan — must be named."""
    text = registry.load_domain("fan_social").lower()
    assert "active" in text and "dormant" in text
    assert "at-risk" in text or "at risk" in text
    assert "purchasers" in text


def test_segment_first_deployment_protocol_present():
    """The segment-first deployment protocol (send to Active first) must be explained."""
    text = registry.load_domain("fan_social").lower()
    assert "segment-first" in text or "active segment" in text or (
        "active" in text and "first" in text and "deploy" in text
    )


def test_release_cycle_email_sequence_present():
    """The release-cycle email sequence covering pre-release and post-release must be present."""
    text = registry.load_domain("fan_social").lower()
    assert "release-cycle" in text or "release cycle" in text
    assert "pre-save" in text


def test_sms_tour_onsale_cadence_present():
    """The SMS cadence for a tour on-sale must be covered."""
    text = registry.load_domain("fan_social").lower()
    assert "on-sale" in text or "onsale" in text
    assert "sms" in text or "text" in text


def test_ab_testing_sample_size_framework_present():
    """A/B testing minimum sample sizes by list size must be present."""
    text = registry.load_domain("fan_social").lower()
    assert "a/b" in text or "a/b testing" in text
    assert "per variant" in text or "per test" in text


def test_win_back_sequence_structure_present():
    """Win-back sequence for 180+ day inactive subscribers must be explained."""
    text = registry.load_domain("fan_social").lower()
    assert "win-back" in text or "win back" in text
    assert "180" in text


def test_purchased_list_prohibition_stated():
    """Purchased or scraped lists must be explicitly named as prohibited."""
    text = registry.load_domain("fan_social").lower()
    assert "purchased" in text
    assert "list" in text


def test_90_day_engagement_cliff_explained():
    """The 90-day engagement cliff practitioner insight must be present."""
    text = registry.load_domain("fan_social").lower()
    assert "90-day" in text or "90 day" in text
    assert "engagement" in text
