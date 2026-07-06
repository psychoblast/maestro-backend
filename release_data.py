"""
PLMKR Tommy — structured release & delivery conventions data (label-services knowledge base).

Unit 1 (data-only): the conventions that govern getting a release out the door
cleanly — the identifiers that must never be mismanaged (ISRC / UPC / ISWC),
the metadata fields a store reads, the artwork spec, the work-backwards
timeline, the permanent per-release record, and the distributor-switch
mechanism — encoded as structured records, plus the honesty rules Tommy's
lookup / checklist / scaffold engine (later units) applies. This corpus encodes
DELIVERY CONVENTIONS AND STRUCTURE ONLY — never an artist's actual identifier,
date, or credit.

RELATIONSHIP TO THE OTHER CORPORA (grant_data / publishing_data / royalties_data
/ copy_data):
  - Same discipline, different domain. Those corpora encode verified external
    facts (societies, rules, splits) or document structure; THIS corpus encodes
    the delivery conventions a release runs on. The values that fill a real
    release — the actual ISRCs, UPC, dates, splits, credits — exist only at run
    time as artist-supplied inputs; NONE live here.
  - Cross-references are named in prose only (split-sheet / sync-pack tools live
    with ink-and-air; sample / cover / split LICENSING lives with the
    publishing + legal departments). Nothing here resolves another domain.

WHAT THIS MODULE IS (and is NOT):
  - DATA ONLY. No functions, no classes, no imports, no I/O, no network, no
    secrets. ``label_services_service`` consumption of these records lands in
    LATER units — NOT here. Nothing in this module executes or enforces
    anything.
  - Every record is a plain, JSON-serializable dict; list-valued fields are
    tuples (no sets/frozensets) so ``json.dumps`` flows every field untouched.

HARD RULES honored here (TOMMY-SPECIFIC):
  - No fact is ever invented. An identifier (ISRC/UPC/ISWC), a date, or a credit
    is NEVER generated — every one is a supplied input verbatim, an explicit
    [NEEDS:<fact>] gap, or an [ARTIST-SUPPLIED:<confirm>] reminder (see
    HONESTY_RULES: never_invent_identifier_date_or_credit).
  - Specs here are CURRENT CONVENTIONS, not guarantees — labeled as such and
    always "verify with the distributor / platform live" (HONESTY_RULES:
    specs_are_current_conventions_verify_live).
  - The ONLY numeric leaf anywhere in this corpus is the artwork minimum
    dimension (3000). Lead times, windows, and digit-lengths live as
    descriptive strings — a delivery corpus with stat-shaped literals would be a
    fabrication vector. A numeric scan in the tests enforces this.
  - artist_name matching is byte-exact: "one character off creates a duplicate
    profile" — later units pass a supplied artist name through VERBATIM and
    never "fix" its casing.
  - Sample / cover / split LICENSING is never resolved here — it routes to the
    publishing + legal framing (HONESTY_RULES: legal_licensing_routes_elsewhere).

SCHEMA (per constant):
  Identifier doctrine (section A):
    IDENTIFIER_RULES  {isrc, upc, iswc, duplicate_doctrine}
  Metadata fields (section B):
    METADATA_FIELDS   {release_level: (ordered records), track_level: (ordered records)}
  Artwork spec (section C):
    ARTWORK_SPEC      {min_dimension_px, formats, color_mode, prohibited, labeled, verify}
  Timeline doctrine (section D):
    TIMELINE_DOCTRINE {upload_to_distributor, editorial_pitch, pre_release,
                       post_release, cross_refs}
  Permanent per-release record (section E):
    RELEASE_RECORD_SPEC {purpose, fields: (ordered records)}
  Distributor-switch mechanism (section F):
    DISTRIBUTOR_SWITCH_MECHANISM {steps: (ordered), step_notes, transition_window, never}
  Discipline (stable ids later units cite in outputs — section G):
    HONESTY_RULES
"""

# ── Identifier doctrine (section A) ────────────────────────────────────────────
# The three standard identifiers and the doctrine that keeps them clean. These
# are the codes an engine must NEVER invent — at run time each is a supplied
# input, a [NEEDS:] gap, or an [ARTIST-SUPPLIED:] confirm, never generated.
IDENTIFIER_RULES = {
    "isrc": {
        "id": "isrc",
        "name": "International Standard Recording Code",
        "follows": "recording",
        "permanence": "forever",
        "new_when": (
            "remix",
            "edit",
            "radio_edit",
            "live",
            "acoustic",
            "clean_version",
            "remaster_with_material_creative_change",
            "own_cover_of_another_song",
        ),
        "same_when": (
            "identical_audio_on_new_release_waterfalling",
            "distributor_switch",
        ),
        "same_when_note": "carrying the SAME ISRC preserves stream counts, "
                          "playlist placements, and algorithmic history — the "
                          "reason a distributor switch must never mint new codes.",
    },
    "upc": {
        "id": "upc",
        "name": "Universal Product Code",
        "follows": "release_container",
        "new_when": (
            "any_configuration_change",
            "deluxe",
            "changed_tracklist",
        ),
        "never": "recycle a UPC across tracklists",
        "same_when": (
            "error_fix_reupload",
            "supported_migration",
        ),
        "formats": "UPC is twelve-digit (North America); EAN is thirteen-digit "
                   "(international); the two are interchangeable.",
    },
    "iswc": {
        "id": "iswc",
        "name": "International Standard Musical Work Code",
        "follows": "composition",
        "via": "PRO work registration",
        "note": "one ISWC maps to many ISRCs (one song, many recordings); link "
                "the work before release to speed royalty matching.",
    },
    "duplicate_doctrine": {
        "id": "duplicate_doctrine",
        "note": "duplicate platform entries almost always trace back to "
                "ISRC/UPC mismanagement; preventing them at delivery beats "
                "months of catalog cleanup afterward.",
    },
}


# ── Metadata fields (section B) ────────────────────────────────────────────────
# Release-level and track-level fields a store reads, in the order an engine
# should surface them. Every ``note`` is a convention, not an artist fact.
METADATA_FIELDS = {
    "release_level": (
        {"field": "release_title",
         "note": "the release name only — no promo text ('out now', 'feat.', "
                 "tour tags)."},
        {"field": "artist_name",
         "note": "EXACT match to the artist's platform profile — one character "
                 "off creates a duplicate profile that splits streams and "
                 "royalties. Passed through verbatim, never re-cased."},
        {"field": "upc",
         "note": "the release container's UPC/EAN — a supplied or issued code, "
                 "never generated by the engine."},
        {"field": "release_date",
         "note": "the single release date all territories work back from — a "
                 "supplied date, never assumed."},
        {"field": "genre_subgenre",
         "note": "specific and honest — never gamed to chase a less-competitive "
                 "chart."},
        {"field": "label_name",
         "note": "the label of record (or the artist's own imprint) as it should "
                 "read on the release."},
        {"field": "p_line",
         "note": "the phonographic-copyright line for the sound recording — the "
                 "owner as supplied."},
        {"field": "c_line",
         "note": "the copyright line for the underlying artwork/composition "
                 "packaging — the owner as supplied."},
        {"field": "year",
         "note": "the copyright year that pairs with the P and C lines — a "
                 "supplied value, never guessed."},
        {"field": "territories",
         "note": "where the release is made available — worldwide or a supplied "
                 "territory list."},
    ),
    "track_level": (
        {"field": "track_title",
         "note": "the song name ONLY — the version and any features go in their "
                 "designated fields, never crammed into the title."},
        {"field": "version_field",
         "note": "the designated place for 'Radio Edit', 'Live', 'Acoustic', "
                 "'Remix' — kept out of the title."},
        {"field": "featured_artists",
         "note": "the designated feature field, each name spelled EXACTLY as "
                 "their own platform profile."},
        {"field": "isrc",
         "note": "the recording's ISRC — supplied or issued, never generated; "
                 "one per unique recording."},
        {"field": "explicit_flag",
         "note": "when in doubt, mark it explicit; a clean version is a SEPARATE "
                 "release with its OWN ISRC, not a re-flag of the same recording."},
        {"field": "songwriter_credits",
         "note": "legal names or registered pseudonyms that MUST match the PRO "
                 "work registration — a mismatch means lost or unmatched "
                 "royalties."},
        {"field": "producer_contributor_roles",
         "note": "producers, mixers, and other contributors with their roles, as "
                 "supplied."},
        {"field": "language",
         "note": "the primary language of the lyrics, as supplied."},
        {"field": "lyrics_optional",
         "note": "lyrics are optional; when supplied they help matching and "
                 "some platform features."},
    ),
}


# ── Artwork spec (section C) ───────────────────────────────────────────────────
# Labeled a CURRENT CONVENTION — always verify with the distributor. The minimum
# dimension (3000) is the ONLY numeric leaf anywhere in this corpus.
ARTWORK_SPEC = {
    "min_dimension_px": 3000,
    "min_dimension_note": "square, at least 3000 on each side (3000 x 3000).",
    "formats": ("JPG", "PNG"),
    "color_mode": "RGB",
    "prohibited": (
        "blur or low resolution",
        "misleading text",
        "social handles or URLs",
    ),
    "labeled": "current_convention",
    "verify": "verify with the distributor / platform live — specs change.",
}


# ── Timeline doctrine (section D) ──────────────────────────────────────────────
# Work BACKWARDS from the release date. Lead times are descriptive strings (not
# numeric leaves) on purpose — they are conventions to verify, not hard facts.
TIMELINE_DOCTRINE = {
    "upload_to_distributor": {
        "lead": "at least four weeks before release date",
        "covers": "distributor processing (two to seven days) + a correction "
                  "buffer + the editorial pitch window.",
    },
    "editorial_pitch": {
        "spotify": "at least seven days before release (minimum), ideally three "
                   "to four weeks, via Spotify for Artists — unreleased music "
                   "only.",
        "others": "Apple Music and Amazon via their own artist dashboards.",
        "copy": "pitch with the specific genre, mood, story, instruments, and "
                "context — a bare genre label tells an editor nothing.",
    },
    # Pre-release checklist items, in order. Two of them CROSS-REFERENCE the
    # ink-and-air department — named in prose, never resolved here.
    "pre_release": (
        "dashboard_access_verified",
        "release_shows_as_upcoming",
        "split_sheet_signed_before_upload",
        "stems_archived_for_sync",
    ),
    "post_release": (
        "verify_live_on_every_platform",
        "save_codes_to_master_record",
        "links_match_metadata",
    ),
    "cross_refs": {
        "split_sheet_signed_before_upload": "sign the split sheet BEFORE upload "
            "— the ink-and-air split sheet tools handle this; the composition "
            "splits are settled there, not here.",
        "stems_archived_for_sync": "archive stems for future sync — the "
            "ink-and-air sync pack handles this.",
    },
}


# ── Permanent per-release record (section E) ───────────────────────────────────
# The record the artist keeps FOREVER for each release. Every field is a
# supplied value at run time — the spec here is the shape, never the contents.
RELEASE_RECORD_SPEC = {
    "purpose": "the permanent record kept per release — the single source of "
               "truth for codes, splits, and ownership when a takedown, "
               "redelivery, or dispute comes up years later.",
    "fields": (
        {"field": "title", "note": "the release title as delivered."},
        {"field": "version", "note": "the version, if any (deluxe, radio edit)."},
        {"field": "artist_spelling",
         "note": "the EXACT artist-name spelling used on delivery — recorded so "
                 "every future release matches it."},
        {"field": "isrc_per_track",
         "note": "the ISRC for each track — supplied/issued, never generated."},
        {"field": "upc", "note": "the release UPC/EAN."},
        {"field": "distributor", "note": "the distributor the release went out through."},
        {"field": "release_date", "note": "the delivered release date."},
        {"field": "platform_uris",
         "note": "the live URIs/links on each platform once verified."},
        {"field": "writer_splits",
         "note": "the composition writer splits as settled (settled with the "
                 "publishing department, recorded here)."},
        {"field": "publisher_info", "note": "publisher / admin info per writer."},
        {"field": "master_owner", "note": "who owns the master recording."},
        {"field": "takedown_redelivery_notes",
         "note": "notes on any takedown or redelivery, so history stays intact."},
    ),
}


# ── Distributor-switch mechanism (section F) ───────────────────────────────────
# Mechanism, not advice — the ORDERED steps to move a catalog to a new
# distributor without losing stream history. The order is load-bearing.
DISTRIBUTOR_SWITCH_MECHANISM = {
    "steps": (
        "export_all_codes_first",
        "upload_to_new_with_same_isrcs",
        "verify_live_via_new",
        "only_then_remove_old",
    ),
    "step_notes": {
        "export_all_codes_first":
            "export EVERY ISRC (and UPC where supported) from the current "
            "distributor BEFORE touching anything else.",
        "upload_to_new_with_same_isrcs":
            "upload to the new distributor carrying the SAME ISRCs (and the same "
            "UPC where the new distributor supports it) — new codes would reset "
            "stream counts and placements.",
        "verify_live_via_new":
            "confirm the releases are live via the new distributor and the codes "
            "carried through.",
        "only_then_remove_old":
            "only AFTER the new delivery is verified live, remove the release "
            "from the old distributor.",
    },
    "transition_window": "roughly two to four weeks — overlap on purpose.",
    "never": "never start a switch without the codes already in hand.",
}


# ── Honesty rules (section G — Jade/Reed/Nadia/Cree discipline, Tommy-hardened) ─
# Structured records with stable ids so later units can cite a rule_id in their
# outputs. Data only — nothing here enforces anything.
HONESTY_RULES = (
    {"id": "specs_are_current_conventions_verify_live",
     "statement": "Every spec here — artwork dimensions, lead times, format "
                  "rules — is a CURRENT CONVENTION, not a guarantee. Present it "
                  "as the current convention and tell the artist to verify it "
                  "with their distributor / platform live.",
     "allowed": "Stating a spec as the current convention with a verify-live "
                "reminder.",
     "forbidden": "Presenting a convention as a fixed, guaranteed rule."},
    {"id": "never_invent_identifier_date_or_credit",
     "statement": "An identifier (ISRC / UPC / ISWC), a release date, or a "
                  "credit is NEVER invented. Every one is exactly one of three "
                  "things: the supplied input VERBATIM, an explicit "
                  "[NEEDS:<fact>] gap, or an [ARTIST-SUPPLIED:<confirm>] "
                  "reminder. There is no fourth state.",
     "markers": ("supplied", "[NEEDS:<fact>]", "[ARTIST-SUPPLIED:<confirm>]"),
     "allowed": "Carrying a supplied code/date/credit verbatim; surfacing a "
                "missing one as [NEEDS:<fact>]; flagging a confirm-item as "
                "[ARTIST-SUPPLIED:<confirm>].",
     "forbidden": "Generating, guessing, or 'fixing' any identifier, date, or "
                  "credit — including re-casing a supplied artist name."},
    {"id": "no_strategy_as_fact",
     "statement": "Release strategy (which single, what date, how to pitch) is "
                  "advice framed as a choice for the artist — never stated as a "
                  "guaranteed outcome or an established fact.",
     "allowed": "Offering a strategy as a reasoned option the artist decides on.",
     "forbidden": "Asserting a strategic call as a fact or a promised result."},
    {"id": "legal_licensing_routes_elsewhere",
     "statement": "Samples, covers, and split agreements are LICENSING matters "
                  "— they route to the publishing + legal framing and are never "
                  "resolved here as if delivery settled them.",
     "allowed": "Naming the licensing/publishing route and handing off.",
     "forbidden": "Treating a sample, cover, or split as cleared just because a "
                  "release was delivered."},
)
