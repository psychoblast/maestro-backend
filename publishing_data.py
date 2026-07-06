"""
PLMKR Ink-and-Air — structured publishing & sync data (Reed's real knowledge base).

Unit 1 (data-only): the real publishing/sync research map, encoded as structured
records. Source of truth: REED_PUBLISHING_SYNC_MAP_v1.md (sections A–E: per-country
society table, identifiers, split-sheet canonical fields, sync metadata pack,
honesty rules). Coverage matches the Jade grant map: CA / US / UK / AU-NZ / DE /
FR / Nordics.

WHAT THIS MODULE IS (and is NOT):
  - DATA ONLY. No functions, no classes, no I/O, no network, no secrets.
    ``ink_and_air_service`` consumption of these records lands in LATER units —
    NOT here. Nothing in this module executes or enforces anything.
  - Every record is a plain, JSON-serializable dict; list-valued fields are
    tuples (no sets/frozensets) so ``json.dumps`` flows every field untouched.

HARD RULES honored here:
  - NEVER invent an IPI, a %, a society rule, or a rate. Unknown values are
    None (not a guess) with a verify-live note where relevant.
  - Free-text fields (``notes``, ``description``, ``residency``-style prose)
    surface as notes ONLY — they are never parsed into a filter or rule.
  - PPL is recording-side and OUT of Reed's composition-side scope: it is
    encoded in OUT_OF_SCOPE_BODIES (so the boundary itself is data) and must
    NEVER be added to SOCIETIES or any COUNTRY_REGISTRATION tuple.
  - One-stop status is never assertable from this data alone — the conditions
    in SYNC_METADATA_SPEC["one_stop_conditions"] each require EXPLICIT artist
    confirmation at run time.
  - Only bodies the map actually names are encoded — no padding records.

SCHEMA (per constant):
  Vocabularies (reference only; nothing enforces them):
    SOCIETY_ROLES, MEMBERSHIP_MODELS, IDENTIFIER_SUBJECTS, RIGHTS_SIDES,
    PUBLISHING_COUNTRIES
  Society library (normalized — each body's facts live in ONE place):
    SOCIETIES        dict[id] -> {id, name, roles, countries, membership_model,
                                  administered_with, registration_fee_notes, notes}
    OUT_OF_SCOPE_BODIES  tuple of {id, name, country, side, reason}
  Per-country routing (references SOCIETIES by id):
    COUNTRY_REGISTRATION dict[country] -> {country, performance, mechanical,
                                           unified_cmo, writer_must_choose_one_pro,
                                           notes}
  Identifiers (CISAC-governed, universal):
    IDENTIFIERS      dict[id] -> {id, name, formerly, identifies, side,
                                  issued_by, required_on, notes}
  Canonical field sets (later validation/scaffold units consume as data):
    SPLIT_SHEET_SPEC, SYNC_METADATA_SPEC
  Discipline (stable ids later units cite in outputs):
    HONESTY_RULES, DOCTRINE
  Deal-type doctrine (honesty pass — structures, never offer evaluations;
  the ONLY numeric range anywhere is the admin fee 10-25% of publisher's
  share, labeled typical/negotiable):
    DEAL_TYPES, DEAL_TRAP_TERMS, DEAL_HONESTY
"""

# ── Controlled vocabularies (reference constants — data only, no logic) ───────

SOCIETY_ROLES = ("performance", "mechanical")

MEMBERSHIP_MODELS = ("open", "invite_only")

IDENTIFIER_SUBJECTS = ("writer", "publisher", "composition", "recording")

# Reed's scope is the composition side; the recording side belongs to Nadia.
RIGHTS_SIDES = ("composition", "recording")

# "UK" (not "GB") matches the grant_data.py country-code convention.
PUBLISHING_COUNTRIES = ("CA", "US", "UK", "AU", "NZ", "DE", "FR", "SE", "DK", "NO", "FI")


# ── Society library (normalized; from map section A) ──────────────────────────
# Each body's facts live here ONCE; COUNTRY_REGISTRATION references these ids.
# membership_model is set ONLY where the map states it (US PROs) — None elsewhere,
# never guessed.
SOCIETIES = {
    # ── Canada ──
    "socan": {
        "id": "socan",
        "name": "SOCAN",
        "roles": ("performance", "mechanical"),
        "countries": ("CA",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Canada's only PRO. Also administers some reproduction rights "
                 "(see socan_rr) alongside its performance role.",
    },
    "socan_rr": {
        "id": "socan_rr",
        "name": "SOCAN RR (Reproduction Rights)",
        "roles": ("mechanical",),
        "countries": ("CA",),
        "membership_model": None,
        "administered_with": "socan",
        "registration_fee_notes": None,
        "notes": "One of Canada's two RROs; the reproduction-rights arm administered "
                 "by SOCAN.",
    },
    "cmrra": {
        "id": "cmrra",
        "name": "CMRRA",
        "roles": ("mechanical",),
        "countries": ("CA",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "One of Canada's two RROs. Owned by SXWorks/SoundExchange.",
    },
    # ── United States ──
    "ascap": {
        "id": "ascap",
        "name": "ASCAP",
        "roles": ("performance",),
        "countries": ("US",),
        "membership_model": "open",
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "One of four US PROs; a writer affiliates with exactly one.",
    },
    "bmi": {
        "id": "bmi",
        "name": "BMI",
        "roles": ("performance",),
        "countries": ("US",),
        "membership_model": "open",
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "One of four US PROs; a writer affiliates with exactly one.",
    },
    "sesac": {
        "id": "sesac",
        "name": "SESAC",
        "roles": ("performance",),
        "countries": ("US",),
        "membership_model": "invite_only",
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Invite-only US PRO.",
    },
    "gmr": {
        "id": "gmr",
        "name": "GMR (Global Music Rights)",
        "roles": ("performance",),
        "countries": ("US",),
        "membership_model": "invite_only",
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Invite-only US PRO.",
    },
    "the_mlc": {
        "id": "the_mlc",
        "name": "The MLC (Mechanical Licensing Collective)",
        "roles": ("mechanical",),
        "countries": ("US",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": "Registration is separate from PRO affiliation and free.",
        "notes": "Handles US digital mechanicals post-MMA. Register works here in "
                 "addition to (not instead of) the writer's PRO.",
    },
    "hfa": {
        "id": "hfa",
        "name": "HFA (Harry Fox Agency)",
        "roles": ("mechanical",),
        "countries": ("US",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Legacy/other US mechanical licensing alongside MRI.",
    },
    "mri": {
        "id": "mri",
        "name": "MRI (Music Reports)",
        "roles": ("mechanical",),
        "countries": ("US",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Legacy/other US mechanical licensing alongside HFA.",
    },
    # ── United Kingdom ──
    "prs": {
        "id": "prs",
        "name": "PRS for Music",
        "roles": ("performance",),
        "countries": ("UK",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "UK performance society; administers MCPS alongside.",
    },
    "mcps": {
        "id": "mcps",
        "name": "MCPS",
        "roles": ("mechanical",),
        "countries": ("UK",),
        "membership_model": None,
        "administered_with": "prs",
        "registration_fee_notes": None,
        "notes": "UK mechanical society, administered with PRS for Music.",
    },
    # ── Australia / New Zealand ──
    "apra": {
        "id": "apra",
        "name": "APRA",
        "roles": ("performance",),
        "countries": ("AU", "NZ"),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Performance side of the joint APRA AMCOS one-stop-shop org for "
                 "Australia and New Zealand.",
    },
    "amcos": {
        "id": "amcos",
        "name": "AMCOS",
        "roles": ("mechanical",),
        "countries": ("AU", "NZ"),
        "membership_model": None,
        "administered_with": "apra",
        "registration_fee_notes": None,
        "notes": "Mechanical side of the joint APRA AMCOS org (one org, both streams).",
    },
    # ── Germany ──
    "gema": {
        "id": "gema",
        "name": "GEMA",
        "roles": ("performance", "mechanical"),
        "countries": ("DE",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Single government-mandated unified CMO for Germany — both streams.",
    },
    # ── France ──
    "sacem": {
        "id": "sacem",
        "name": "SACEM",
        "roles": ("performance", "mechanical"),
        "countries": ("FR",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Single unified CMO for France — both streams; mechanicals via SDRM.",
    },
    # ── Nordics ──
    "stim": {
        "id": "stim",
        "name": "STIM",
        "roles": ("performance",),
        "countries": ("SE",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Sweden's performance society; mechanicals via NCB.",
    },
    "koda": {
        "id": "koda",
        "name": "KODA",
        "roles": ("performance",),
        "countries": ("DK",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Denmark's performance society; mechanicals via NCB.",
    },
    "tono": {
        "id": "tono",
        "name": "TONO",
        "roles": ("performance",),
        "countries": ("NO",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Norway's performance society; mechanicals via NCB.",
    },
    "teosto": {
        "id": "teosto",
        "name": "Teosto",
        "roles": ("performance",),
        "countries": ("FI",),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Finland's performance society; mechanicals via NCB.",
    },
    "ncb": {
        "id": "ncb",
        "name": "NCB (Nordic Copyright Bureau)",
        "roles": ("mechanical",),
        "countries": ("SE", "DK", "NO", "FI"),
        "membership_model": None,
        "administered_with": None,
        "registration_fee_notes": None,
        "notes": "Handles mechanicals for the Nordic region — shared across "
                 "Sweden, Denmark, Norway, and Finland.",
    },
}


# Bodies the map names as explicitly OUTSIDE Reed's composition-side scope.
# Encoded so the boundary survives as data; never merged into SOCIETIES.
OUT_OF_SCOPE_BODIES = (
    {
        "id": "ppl",
        "name": "PPL",
        "country": "UK",
        "side": "recording",
        "reason": "Recording-side body — out of Reed's composition-side scope; "
                  "belongs to Nadia's domain.",
    },
)


# ── Per-country registration routing (map section A rows) ─────────────────────
# References SOCIETIES by id. writer_must_choose_one_pro means "exactly one OF
# SEVERAL available PROs" — True only for the US; everywhere else a single PRO
# (or joint org) exists, so there is no choice to make.
COUNTRY_REGISTRATION = {
    "CA": {
        "country": "CA",
        "performance": ("socan",),
        "mechanical": ("cmrra", "socan_rr"),
        "unified_cmo": False,
        "writer_must_choose_one_pro": False,
        "notes": "SOCAN is the only PRO. Two RROs on the mechanical side: CMRRA "
                 "(owned by SXWorks/SoundExchange) and SOCAN RR.",
    },
    "US": {
        "country": "US",
        "performance": ("ascap", "bmi", "sesac", "gmr"),
        "mechanical": ("the_mlc", "hfa", "mri"),
        "unified_cmo": False,
        "writer_must_choose_one_pro": True,
        "notes": "Writer affiliates with exactly ONE PRO (SESAC and GMR are "
                 "invite-only). The MLC handles post-MMA digital mechanicals — "
                 "registration is separate and free; HFA/MRI cover legacy/other "
                 "mechanical licensing.",
    },
    "UK": {
        "country": "UK",
        "performance": ("prs",),
        "mechanical": ("mcps",),
        "unified_cmo": False,
        "writer_must_choose_one_pro": False,
        "notes": "MCPS is administered with PRS for Music. PPL is recording-side — "
                 "out of Reed's scope (see OUT_OF_SCOPE_BODIES).",
    },
    "AU": {
        "country": "AU",
        "performance": ("apra",),
        "mechanical": ("amcos",),
        "unified_cmo": False,
        "writer_must_choose_one_pro": False,
        "notes": "Joint APRA AMCOS org — one-stop-shop for both streams.",
    },
    "NZ": {
        "country": "NZ",
        "performance": ("apra",),
        "mechanical": ("amcos",),
        "unified_cmo": False,
        "writer_must_choose_one_pro": False,
        "notes": "Joint APRA AMCOS org — one-stop-shop for both streams.",
    },
    "DE": {
        "country": "DE",
        "performance": ("gema",),
        "mechanical": ("gema",),
        "unified_cmo": True,
        "writer_must_choose_one_pro": False,
        "notes": "GEMA is the single government-mandated society for both streams.",
    },
    "FR": {
        "country": "FR",
        "performance": ("sacem",),
        "mechanical": ("sacem",),
        "unified_cmo": True,
        "writer_must_choose_one_pro": False,
        "notes": "SACEM is the single society for both streams (mechanicals via SDRM).",
    },
    "SE": {
        "country": "SE",
        "performance": ("stim",),
        "mechanical": ("ncb",),
        "unified_cmo": False,
        "writer_must_choose_one_pro": False,
        "notes": "NCB handles mechanicals for the Nordic region.",
    },
    "DK": {
        "country": "DK",
        "performance": ("koda",),
        "mechanical": ("ncb",),
        "unified_cmo": False,
        "writer_must_choose_one_pro": False,
        "notes": "NCB handles mechanicals for the Nordic region.",
    },
    "NO": {
        "country": "NO",
        "performance": ("tono",),
        "mechanical": ("ncb",),
        "unified_cmo": False,
        "writer_must_choose_one_pro": False,
        "notes": "NCB handles mechanicals for the Nordic region.",
    },
    "FI": {
        "country": "FI",
        "performance": ("teosto",),
        "mechanical": ("ncb",),
        "unified_cmo": False,
        "writer_must_choose_one_pro": False,
        "notes": "NCB handles mechanicals for the Nordic region.",
    },
}


# ── Identifiers (universal, CISAC-governed; map section B) ────────────────────
IDENTIFIERS = {
    "ipi": {
        "id": "ipi",
        "name": "Interested Parties Information",
        "formerly": "CAE",
        "identifies": ("writer", "publisher"),
        "side": "composition",
        "issued_by": "home society, assigned on joining",
        "required_on": ("split_sheet", "every_registration"),
        "notes": "Unique ID per writer AND per publisher. Required on split sheets "
                 "and every registration.",
    },
    "iswc": {
        "id": "iswc",
        "name": "International Standard Musical Work Code",
        "formerly": None,
        "identifies": ("composition",),
        "side": "composition",
        "issued_by": "home society, obtained via work registration",
        "required_on": ("work_registration", "sync_metadata_pack"),
        "notes": "Identifies the composition — NOT the recording (that is the ISRC). "
                 "Both IDs must stay consistent across all registrations or "
                 "royalties sit unmatched.",
    },
    "isrc": {
        "id": "isrc",
        "name": "International Standard Recording Code",
        "formerly": None,
        "identifies": ("recording",),
        "side": "recording",
        "issued_by": "distributor or national ISRC agency",
        "required_on": ("sync_metadata_pack",),
        "notes": "Identifies the recording — NOT the composition (that is the ISWC). "
                 "Both IDs must stay consistent across all registrations or "
                 "royalties sit unmatched.",
    },
}


# ── Split sheet — canonical field set (map section C) ─────────────────────────
# Later validation units consume this as data. The two 100%-sum invariants are
# arithmetic on SUPPLIED inputs only — filling a missing % is fabrication
# (see HONESTY_RULES: sum_checks_supplied_only). No master-side sum invariant
# is encoded because the map does not state one.
SPLIT_SHEET_SPEC = {
    "signed_when": "on completion day of the song",
    "song_fields": (
        {"field": "song_title", "required": True,
         "description": "Song title."},
        {"field": "alternate_titles", "required": False,
         "description": "Alternate titles, if any."},
        {"field": "date", "required": True,
         "description": "Date the split sheet is signed."},
        {"field": "samples_used", "required": True,
         "description": "Whether samples are used — yes/no."},
        {"field": "sample_sources", "required": False,
         "description": "Source of each sample; required when samples_used is yes."},
    ),
    "contributor_fields": (
        {"field": "legal_name", "required": True,
         "description": "Contributor's legal name."},
        {"field": "contact", "required": True,
         "description": "Contact details."},
        {"field": "role", "required": True,
         "description": "Role on the song (writer, producer, topliner, ...)."},
        {"field": "lyrics_percent", "required": True,
         "description": "Lyrics share % — supplied by the parties, never filled in."},
        {"field": "music_percent", "required": True,
         "description": "Music share % — supplied by the parties, never filled in."},
        {"field": "pro_affiliation", "required": True,
         "description": "Contributor's PRO affiliation."},
        {"field": "writer_ipi", "required": True,
         "description": "Writer IPI — never invented; unknown surfaces as a "
                        "[NEEDS: ...] gap."},
        {"field": "publisher_name", "required": True,
         "description": "Publisher name; 'SELF' if self-published."},
        {"field": "publisher_ipi", "required": True,
         "description": "Publisher IPI — never invented; unknown surfaces as a "
                        "[NEEDS: ...] gap."},
        {"field": "signature", "required": True,
         "description": "Signature — an unsigned split sheet is not enforceable."},
    ),
    "invariants": (
        {"id": "writer_shares_sum_100", "side": "writer", "rule": "sum",
         "fields": ("lyrics_percent", "music_percent"), "target": 100,
         "description": "Writer shares must sum to exactly 100% across all "
                        "contributors (per the lyrics/music split the parties "
                        "supplied)."},
        {"id": "publisher_shares_sum_100", "side": "publisher", "rule": "sum",
         "fields": ("publisher_share_percent",), "target": 100,
         "description": "Publisher shares must sum to exactly 100% across all "
                        "publishers (societies pay 50/50 writer/publisher)."},
    ),
    "master_side_extension": {
        "status": "best_practice",
        "fields": (
            {"field": "recording_info", "required": False,
             "description": "Recording identification details."},
            {"field": "isrc", "required": False,
             "description": "ISRC of the recording, if assigned."},
            {"field": "master_ownership_percent", "required": False,
             "description": "Master ownership % — supplied by the parties, "
                            "never filled in."},
        ),
        "rationale": "Composition split is not the master split — a documented "
                     "dispute source; capturing both on one sheet prevents it.",
    },
    "amendment_rule": {
        "requires_all_party_resignature": True,
        "description": "Amendable only with re-signature by ALL parties.",
    },
}


# ── Sync metadata pack — canonical field set (map section D) ──────────────────
SYNC_METADATA_SPEC = {
    "fields": (
        {"field": "genre_specific", "required": True,
         "description": "Genre — specific, not broad."},
        {"field": "moods", "required": True,
         "description": "Moods the track conveys."},
        {"field": "tempo_bpm", "required": True,
         "description": "Tempo / BPM."},
        {"field": "instrumentation", "required": True,
         "description": "Instrumentation."},
        {"field": "vocals", "required": True,
         "description": "Vocal type, or none."},
        {"field": "similar_artists", "required": True,
         "description": "Similar artists."},
        {"field": "suggested_placements", "required": True,
         "description": "Suggested placement contexts."},
        {"field": "one_stop_status", "required": True,
         "description": "Whether a single party controls master + publishing — "
                        "asserted ONLY under one_stop_conditions; never claimed "
                        "if samples are uncleared or a co-writer sign-off is "
                        "missing."},
        {"field": "rights_breakdown", "required": True,
         "description": "Rights breakdown with a clearance contact per side "
                        "(composition and master)."},
        {"field": "stems_available", "required": True,
         "description": "Stems availability."},
        {"field": "instrumental_available", "required": True,
         "description": "Instrumental version availability."},
        {"field": "clean_version_available", "required": True,
         "description": "Clean version availability."},
        {"field": "samples_cleared_declaration", "required": True,
         "description": "Declaration that all samples are cleared."},
        {"field": "isrc", "required": True,
         "description": "ISRC of the recording."},
        {"field": "iswc", "required": True,
         "description": "ISWC of the composition."},
        {"field": "pro_affiliation", "required": True,
         "description": "PRO affiliation."},
        {"field": "ipi", "required": True,
         "description": "IPI number(s)."},
    ),
    "one_stop_conditions": (
        {"id": "master_control_confirmed",
         "description": "Explicit artist confirmation of master control."},
        {"id": "publishing_control_100_confirmed",
         "description": "Explicit artist confirmation of 100% publishing control."},
        {"id": "no_uncleared_samples",
         "description": "No uncleared samples."},
    ),
    "one_stop_rule": "One-stop status is asserted ONLY when every condition above "
                     "holds via explicit artist confirmation. Never claim it if "
                     "samples are uncleared or a co-writer sign-off is missing. "
                     "Supervisors prefer one-stop — which is exactly why it must "
                     "never be over-claimed.",
}


# ── Honesty rules (map section E — Jade discipline carried over) ──────────────
# Structured records with stable ids so later units can cite a rule_id in their
# outputs (e.g. attached to a [NEEDS: ...] gap marker). Data only — nothing here
# enforces anything.
HONESTY_RULES = (
    {"id": "unknown_is_none",
     "statement": "Unknown values are None plus a 'verify live' note. Never "
                  "invent an IPI, a %, a society rule, or a rate.",
     "allowed": "Returning None with an explicit verify-live note.",
     "forbidden": "Guessing or fabricating any value."},
    {"id": "free_text_is_note_only",
     "statement": "Free-text inputs (e.g. a co-writer's residency, publisher "
                  "deal details) surface as a note — never parsed into a filter "
                  "or rule.",
     "allowed": "Carrying free text through verbatim as a note.",
     "forbidden": "Parsing free text into a filter, flag, or rule."},
    {"id": "sum_checks_supplied_only",
     "statement": "Percentage-sum checks are arithmetic on SUPPLIED inputs — "
                  "allowed. Filling a missing % is fabrication — forbidden.",
     "allowed": "Arithmetic on percentages the parties supplied.",
     "forbidden": "Filling a missing % — emit a [NEEDS: ...] gap instead."},
    {"id": "one_stop_explicit_confirmation_only",
     "statement": "One-stop status is asserted only from explicit artist "
                  "confirmation of both master control and 100% publishing "
                  "control with no uncleared samples.",
     "allowed": "Asserting one-stop when every condition is explicitly confirmed.",
     "forbidden": "Claiming one-stop with uncleared samples, a missing co-writer "
                  "sign-off, or any unconfirmed condition."},
)


# ── Structural doctrine (map section A footer + B) ─────────────────────────────
DOCTRINE = {
    "home_society_once": "A writer joins their HOME society once and collects "
                         "worldwide through the CISAC network of reciprocal "
                         "agreements — never register with multiple PROs.",
    "anglo_split_vs_continental_unified": "Anglo-American territories split "
                                          "performance vs mechanical across "
                                          "separate bodies; most of continental "
                                          "Europe uses one unified CMO for both.",
    "composition_is_not_recording": "The ISWC identifies the composition; the "
                                    "ISRC identifies the recording. Both IDs must "
                                    "stay consistent across all registrations or "
                                    "royalties sit unmatched.",
    "societies_pay_writer_publisher_50_50": "Societies pay 50/50 writer/publisher "
                                            "— why BOTH sides of a split sheet "
                                            "must each sum to 100%.",
}


# ── Deal-type doctrine (honesty pass — replaces the service's invented catalog) ─
# STRUCTURES, not offers: each record describes how a deal TYPE works — who owns
# what, how writer income flows, and the typical (negotiable) shape. The ONLY
# numeric range stated anywhere is the admin-fee 10-25% of publisher's share,
# and it is labeled a typical range — EVERY deal is negotiable; no number here
# is ever a quote for a specific deal. Sub-publishing is the territory-scoped
# cousin of admin/full deals abroad — deliberately NOT a separate type record.
_EVERY_DEAL_NEGOTIABLE = "typical range — every deal negotiable"

DEAL_TYPES = {
    "admin": {
        "id": "admin",
        "name": "Administration Deal",
        "ownership": "writer_retains_100",
        "writer_income_structure": "The writer keeps the full writer's share AND "
                                   "the publisher's share, minus the admin fee — "
                                   "the administrator collects and takes a fee, "
                                   "it does not take ownership.",
        "fee_or_split_typical": {
            "range_pct": (10, 25),
            "of": "publisher's share",
            "label": _EVERY_DEAL_NEGOTIABLE,
            "shape_note": "10-15% domestic / 15-20% foreign is a common shape — "
                          "still " + _EVERY_DEAL_NEGOTIABLE + ".",
        },
        "term_typical": {"deal_term": "~1-3 years — " + _EVERY_DEAL_NEGOTIABLE},
        "advance_norm": "none_or_low",
        "services_norm": "Registration, collection, and licensing administration "
                         "— typically no creative/exploitation obligation.",
        "notes": "Territory-scoped administration abroad is often called "
                 "sub-publishing — the same structure, per territory, not a "
                 "separate deal type here.",
    },
    "co_publishing": {
        "id": "co_publishing",
        "name": "Co-Publishing Deal",
        "ownership": "copyright_co_owned_50_50",
        "writer_income_structure": "100% writer's share + 50% publisher's share "
                                   "= 75% of total publishing income to the "
                                   "writer.",
        "fee_or_split_typical": {
            "structure": "75/25 of total publishing income (writer/publisher) — "
                         "structural, not a fee.",
            "label": _EVERY_DEAL_NEGOTIABLE,
        },
        "term_typical": {
            "deal_term": "~1-3 years with options — " + _EVERY_DEAL_NEGOTIABLE,
            "retention_asymmetry": "The deal TERM and the RETENTION on the "
                                   "assigned copyright share are different "
                                   "clocks: retention can run to life of "
                                   "copyright — a short term does NOT mean the "
                                   "rights come back when the term ends.",
        },
        "advance_norm": "customary_recoupable",
        "services_norm": "Active creative work and pitching are typically part "
                         "of the bargain — that is what the assigned share pays "
                         "for.",
        "notes": None,
    },
    "full_publishing": {
        "id": "full_publishing",
        "name": "Exclusive Publishing Deal (traditional full-service)",
        "ownership": "publisher_owns_publisher_share",
        "writer_income_structure": "The writer's share only — the publisher "
                                   "keeps the entire publisher's share.",
        "fee_or_split_typical": {
            "structure": "Publisher keeps the publisher's share entirely — "
                         "structural, not a fee.",
            "label": _EVERY_DEAL_NEGOTIABLE,
        },
        "term_typical": {
            "deal_term": "varies — " + _EVERY_DEAL_NEGOTIABLE,
            "retention_asymmetry": "Assigned copyrights have historically been "
                                   "retained up to life of copyright — the "
                                   "retention clause is the clause to scrutinize.",
        },
        "advance_norm": "largest",
        "services_norm": "Full-service exploitation is the expectation in "
                         "exchange for the ownership transfer.",
        "notes": None,
    },
    "work_for_hire": {
        "id": "work_for_hire",
        "name": "Work For Hire",
        "ownership": "everything_transferred",
        "writer_income_structure": "A flat fee and NO ongoing income — the "
                                   "commissioning party owns the work outright "
                                   "from creation.",
        "fee_or_split_typical": {
            "structure": "Flat fee — structural, not a fee/split on income.",
            "label": _EVERY_DEAL_NEGOTIABLE,
        },
        "term_typical": {"deal_term": "not a term deal — a transfer at creation."},
        "advance_norm": "flat_fee",
        "services_norm": "Delivery of the commissioned work; no ongoing "
                         "publisher services owed to the writer.",
        "notes": None,
    },
}


# ── Deal trap terms (stable ids — later units cite these in outputs) ───────────
DEAL_TRAP_TERMS = (
    {"id": "recoupment",
     "term": "Recoupment",
     "explanation": "An advance is a LOAN against future royalties — royalties "
                    "pay it back before the writer sees new money. Unrecouped "
                    "balances are typically not repayable out of pocket, but "
                    "they CAN extend the contract until recouped.",
     "writer_note": "Ask what recoups, from which income, and whether an "
                    "unrecouped balance extends the term."},
    {"id": "cross_collateralization",
     "term": "Cross-Collateralization",
     "explanation": "One project's unrecouped advance is recouped from ANOTHER "
                    "project's (or deal's) income — a hit can end up paying for "
                    "an old advance.",
     "writer_note": "Ask whether accounts are cross-collateralized across "
                    "songs, albums, or other agreements."},
    {"id": "retention_period",
     "term": "Retention Period",
     "explanation": "How long the publisher keeps the assigned rights after "
                    "the term: ~2 years to life of copyright — "
                    + _EVERY_DEAL_NEGOTIABLE + ". Shorter favors the writer.",
     "writer_note": "The retention clock, not the deal term, decides when "
                    "rights come home."},
    {"id": "pipeline_songs",
     "term": "Pipeline Songs / Pipeline Income",
     "explanation": "Income earned during the term but paid after it — the "
                    "deal decides whether the publisher keeps collecting it "
                    "after the rights revert.",
     "writer_note": "Ask how pipeline income is defined, capped, and cut off."},
    {"id": "at_source_collection",
     "term": "At-Source Collection",
     "explanation": "Whether the fee/split is computed on income AT SOURCE in "
                    "each territory, or after foreign sub-collectors have each "
                    "taken a cut — 'at source' protects the writer from "
                    "double-dipping.",
     "writer_note": "Ask for at-source language on foreign collection."},
    {"id": "writers_share_untouchable",
     "term": "Writer's Share",
     "explanation": "The writer's share of performance income is conventionally "
                    "untouchable — ANY deal language that touches the writer's "
                    "share is a red flag to surface, not a norm.",
     "red_flag": True,
     "writer_note": "Surface it immediately and route the agreement to a "
                    "lawyer."},
)


# ── Deal honesty doctrine (what Reed does and does NOT do with this data) ──────
DEAL_HONESTY = {
    "explains_never_evaluates": "Reed explains deal STRUCTURES and flags trap "
                                "terms — he NEVER evaluates a specific offer as "
                                "good or bad, and never quotes a number as the "
                                "market rate for a specific deal.",
    "every_number_negotiable": "The only numeric shapes in this doctrine are "
                               "labeled typical ranges — every deal is "
                               "negotiable and real terms come from the paper "
                               "in front of the writer.",
    "real_agreements_to_lawyer": "A real agreement routes to lawyer review — "
                                 "Lex, framed as draft-for-review — before "
                                 "anyone signs anything.",
}
