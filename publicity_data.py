"""
PLMKR Zara — publicity / press doctrine corpus (data only).

A data-only sibling of grant_data.py / booking_data.py / brand_partnerships_data.py:
the mechanism anatomy of a press campaign — the pitch mechanism types (standard /
embargo / exclusive), the embargo hard-rules, the lead-time / campaign-shape
doctrine, list & personalization discipline, the pitch-package spec, integrity
rules, and the department boundaries Zara works inside. Source map:
ZARA_PUBLICITY_MAP_v1 (researched in chat, July 6 2026, web-sourced).

MOCK-FIRST / CORPUS CONTRACT (hard rules for this module):
  - Data only: no def / class / import / call anywhere. Pure literals.
  - JSON-serializable throughout; ``None`` for an unknown, paired with a
    "verify live" note — never a guessed value.
  - Free text is a NOTE (a convention to convey), never a hard rule the code
    branches on. Timing figures are ranges expressed as notes; the one structured
    ``campaign_timeline`` carries small representative week offsets so a plan tool
    can reason about compression — no other numbers are load-bearing.
  - ZERO currency amounts anywhere (a numeric scan enforces it).
  - NEVER encodes an outlet name, a journalist name, or a coverage claim — media
    targets are ALWAYS artist-supplied or an explicit gap. There is no live
    list-building integration; if one is ever built it is a Railway-gated seam.
"""

# ── PITCH_MECHANISM_TYPES — standard vs embargo vs exclusive (never conflated). ─
PITCH_MECHANISM_TYPES = {
    "standard": {
        "id": "standard",
        "note": ("the outlet may publish anytime after receiving it; pitchable to "
                 "many outlets at once."),
    },
    "embargo": {
        "id": "embargo",
        "note": ("information is shared but WITHHELD from publication until an agreed "
                 "date/time; pitchable to many outlets who all hold to the same "
                 "lift."),
    },
    "exclusive": {
        "id": "exclusive",
        "note": ("ONE outlet alone publishes at an agreed time; other outlets are "
                 "pitched only AFTER the exclusive has run."),
    },
    "selection_doctrine": {
        "max_impressions": ("when the goal is maximum impressions, do NOT go "
                            "exclusive — spread the story."),
        "feature_or_relationship": ("a top-tier feature or relationship-building play "
                                    "favours exclusive or embargo."),
        "embargo_suits": "news that affects many outlets at once (a dated announcement).",
        "exclusive_suits": "a human-interest or feature angle that one outlet can own.",
        "not_interchangeable": ("the three are NOT interchangeable — never conflate an "
                                "embargo with an exclusive."),
    },
}


# ── EMBARGO_DOCTRINE — hard rules. Getting these wrong burns relationships. ─────
EMBARGO_DOCTRINE = {
    "id": "embargo",
    "explicit_agreement_first": ("get explicit agreement to the embargo BEFORE sharing "
                                 "any embargoed detail — absent agreement a reporter "
                                 "assumes publish-now."),
    "state_timezone_always": ("state the lift date AND time WITH the time zone in "
                              "every communication — an unzoned time is a broken "
                              "embargo waiting to happen."),
    "owned_channels_negate": ("posting the news to the artist's own channels NEGATES "
                              "the embargo — do not self-publish before the lift."),
    "moving_the_date_damages": ("moving an embargo date damages the relationship and "
                                "the reporter is NOT bound to the new date."),
    "reserve_for_newsworthy": ("reserve embargoes for genuinely newsworthy "
                               "announcements — not routine updates."),
}


# ── LEAD_TIME_DOCTRINE — timing ranges as notes + a structured campaign_timeline. ─
# Ranges are "varies by outlet" notes. The campaign_timeline list carries small
# representative week offsets (weeks_before_release) purely so a plan tool can flag
# a compressed schedule — the range note is the real guidance.
LEAD_TIME_DOCTRINE = {
    "id": "lead_time",
    "varies_note": "every window below VARIES BY OUTLET — verify against the specific target.",
    "embargo_pitch_window": "embargo pitches commonly go out ~2-3 weeks ahead (note).",
    "long_lead_setup": ("long-lead outlets (print monthlies) historically need ~3-4 "
                        "months of setup (note)."),
    "advance_copies": ("advance copies for an EP/album review go out at least ~1 month "
                       "out, ideally ~6-8 weeks (note)."),
    "sustained_not_release_week_only": ("a successful campaign is SUSTAINED — tour "
                                        "press and content continue AFTER release; it "
                                        "is never release-week-only."),
    # Ordered by weeks_before_release (largest lead first). Representative offsets;
    # the note carries the real range. weeks_before_release=0 means "around release".
    "campaign_timeline": (
        {"slot": "long_lead_setup", "weeks_before_release": 14,
         "note": "reach long-lead print monthlies ~3-4 months out."},
        {"slot": "lead_single", "weeks_before_release": 8,
         "note": "lead single ~2 months out — the campaign's test run."},
        {"slot": "press_kit_final", "weeks_before_release": 6,
         "note": "press kit finished ~6 weeks out."},
        {"slot": "advance_review_copies", "weeks_before_release": 6,
         "note": "advance copies out ~6-8 weeks out, at least ~1 month."},
        {"slot": "album_announcement", "weeks_before_release": 4,
         "note": "announce title/date/cover/tracklist together ~1 month out."},
        {"slot": "embargo_pitches", "weeks_before_release": 3,
         "note": "embargo pitches out ~2-3 weeks ahead of the lift."},
        {"slot": "full_album_stream_premiere", "weeks_before_release": 1,
         "note": "full-album stream premiere ~1 week before release."},
        {"slot": "features_and_reviews_land", "weeks_before_release": 0,
         "note": "print features / reviews land around release; sustain after."},
    ),
}


# ── LIST_AND_PERSONALIZATION_DOCTRINE — the leading rejection cause is generic. ─
LIST_AND_PERSONALIZATION_DOCTRINE = {
    "id": "list_and_personalization",
    "personalize_or_rejected": ("lack of personalization is a leading cause of "
                                "rejection — every pitch is personalized."),
    "check_current_beat": ("check what the journalist covers NOW, not a stale beat — "
                           "a writer's focus moves."),
    "match_artist_level": ("target writers who cover artists at the user's level — not "
                           "only the biggest names."),
    "focused_beats_generic": ("a focused, relevant list beats a huge generic blast."),
    "timing_note": ("mid-week mornings tend to perform best — a note, not a rule; "
                    "verify against the outlet."),
}


# ── PITCH_PACKAGE_SPEC — what a complete pitch package carries. ─────────────────
PITCH_PACKAGE_SPEC = {
    "id": "pitch_package",
    "components": (
        "final_audio_private_link",
        "artwork",
        "photos",
        "bio",
        "credits",
        "story_angle",
        "release_date",
    ),
    "press_release_ref": ("the press release is REFERENCED from the creative "
                          "department's build_copy_scaffold — it is NEVER drafted in "
                          "this agent's tool layer."),
    "follow_up_doctrine": ("ONE follow-up with USEFUL context (release date, a direct "
                           "link, one sentence on outlet fit, a new proof point) — "
                           "never repeated bumps or nagging."),
}


# ── INTEGRITY_DOCTRINE — earned media is earned. ───────────────────────────────
INTEGRITY_DOCTRINE = {
    "id": "integrity",
    "earned_never_paid": ("earned media is never paid for; pay-for-editorial is a red "
                          "flag, not a tactic."),
    "broken_embargo": ("a broken embargo is DOCUMENTED and escalated — do not litigate "
                       "it with the reporter in the moment."),
}


# ── OUT_OF_SCOPE — department boundaries. Zara sends; these belong elsewhere. ───
OUT_OF_SCOPE = {
    "press_release_drafting": {
        "owner": "creative-director",
        "tool": "build_copy_scaffold",
        "reason": ("press-release / bio / EPK DRAFTING belongs to the creative "
                   "department (Cree writes, Zara sends) — route drafting to "
                   "creative-director's build_copy_scaffold; never draft it here."),
    },
    "curator_outreach": {
        "owner": "puppet-master",
        "reason": ("playlist / curator outreach belongs to the management department "
                   "(puppet-master), not publicity."),
    },
    "radio_dsp_promotion": {
        "owner": "airwave",
        "reason": ("radio and DSP editorial promotion belong to airwave, not "
                   "publicity."),
    },
    "brand_deals": {
        "owner": "brand-connect",
        "reason": ("brand / endorsement / sponsorship deals belong to brand-connect, "
                   "not publicity."),
    },
}


# ── HONESTY_RULES — the guardrails, stable ids. ────────────────────────────────
HONESTY_RULES = (
    {
        "id": "never_fabricate_media_targets",
        "statement": ("Outlet names, journalist names, and coverage claims are NEVER "
                      "invented. Media targets are artist-supplied or an explicit "
                      "gap — there is no live outlet directory here."),
        "allowed": "Filtering an artist-supplied media list by beat or level.",
        "forbidden": "Producing an outlet name, a writer name, or a claim of past/likely coverage.",
    },
    {
        "id": "drafting_belongs_to_creative",
        "statement": ("Press releases, bios, and EPKs are DRAFTED by the creative "
                      "department (build_copy_scaffold); Zara references and SENDS "
                      "them, and never drafts copy in this tool layer."),
        "allowed": "Routing a drafting request to creative-director's build_copy_scaffold.",
        "forbidden": "Writing or 'finalizing' a press release, bio, or EPK in this agent.",
    },
    {
        "id": "embargo_needs_zoned_lift",
        "statement": ("An embargo requires explicit agreement and a lift date/time "
                      "WITH time zone stated in every communication; without a zoned "
                      "lift it is a [NEEDS:embargo_lift_datetime] gap, never guessed."),
        "allowed": "Surfacing a missing zoned lift as a gap and holding the send.",
        "forbidden": "Sending an embargo pitch with an unzoned or invented lift time.",
    },
    {
        "id": "earned_media_never_paid",
        "statement": ("Earned media is never paid for; pay-for-editorial is a red flag. "
                      "Timelines and windows vary by outlet and are verify-live, never "
                      "asserted as guarantees of coverage."),
        "allowed": "Noting that coverage is never guaranteed and windows vary by outlet.",
        "forbidden": "Promising placement, or arranging paid editorial as if it were earned.",
    },
)
