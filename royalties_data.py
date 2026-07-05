"""
PLMKR Ledger-Lock — structured recording-royalty & registration data (Nadia's real knowledge base).

Unit 1 (data-only): the recording-side royalty map — who collects the money a
recording earns, in which country, in which capacity — encoded as structured
records, plus the registration-situation axes and rules Nadia's checklist
engine (later units) applies. Coverage matches Reed's publishing corpus:
CA / US / UK / AU / NZ / DE / FR / SE / DK / NO / FI.

RELATIONSHIP TO publishing_data (Reed's corpus):
  - The COMPOSITION side of every royalty stream is Reed's domain. This module
    NEVER duplicates a composition-side society record — COUNTRY_ROYALTY_TABLE
    references publishing_data.SOCIETIES ids (socan, ascap, the_mlc, prs, ...)
    verbatim, and a cross-module test enforces that every referenced id
    resolves there. Corpora stay import-free; only the service/test layer
    resolves the references.
  - The RECORDING side (neighbouring rights / performance royalties on the
    sound recording itself) lives HERE, in RECORDING_SOCIETIES.

WHAT THIS MODULE IS (and is NOT):
  - DATA ONLY. No functions, no classes, no imports, no I/O, no network, no
    secrets. ``ledger_lock_service`` consumption of these records lands in
    LATER units — NOT here. Nothing in this module executes or enforces
    anything.
  - Every record is a plain, JSON-serializable dict; list-valued fields are
    tuples (no sets/frozensets) so ``json.dumps`` flows every field untouched.

HARD RULES honored here:
  - NEVER invent a rate, a %, or a society rule. Unknown values are None
    (not a guess) with a verify-live note where relevant — the NZ recording
    side is exactly that: no verified body in the map, so the value is None.
  - The ONLY hard-coded split anywhere in this corpus is the US STATUTORY
    SoundExchange split: 50% rights owner / 45% featured performer /
    5% non-featured performers. Every other split is
    "varies_verify_with_society" — never stated as fact (see HONESTY_RULES:
    only_statutory_split_hardcoded).
  - Situation flags (self_published, owns_masters, ...) require EXPLICIT
    artist confirmation at run time — never inferred, never defaulted (see
    REGISTRATION_SITUATION_SPEC and HONESTY_RULES: situation_flags_explicit_only).
  - Free-text fields (``notes``, ``scope_notes``, ``registration_notes``)
    surface as notes ONLY — they are never parsed into a filter or rule.
  - gramex_dk (Denmark) and gramex_fi (Finland) are DISTINCT organizations
    despite the shared name — encoded as two separate records.

SCHEMA (per constant):
  Vocabularies (reference only; nothing enforces them):
    REPRESENTS_VALUES, STREAM_SIDES, COLLECTED_BY_REFS, ROYALTY_COUNTRIES
  Recording-side society library (each body's facts live in ONE place):
    RECORDING_SOCIETIES dict[id] -> {id, name, country, represents,
                                     scope_notes, registration_notes}
                        (+ statutory_split on soundexchange ONLY)
  The four royalty streams a released song generates:
    STREAMS          dict[id] -> {id, side, collected_by_ref, description, notes}
  Per-country routing (composition ids resolve in publishing_data.SOCIETIES;
  recording ids resolve in RECORDING_SOCIETIES):
    COUNTRY_ROYALTY_TABLE dict[country] -> {country,
                                            composition_performance_ids,
                                            composition_mechanical_ids,
                                            recording_performance_ids,
                                            notes}
  Registration checklist axes + rules (later units apply as data):
    REGISTRATION_SITUATION_SPEC, REGISTRATION_RULES
  Letter-of-direction canonical field set:
    LOD_SPEC
  Discipline (stable ids later units cite in outputs):
    METADATA_DOCTRINE, HONESTY_RULES
"""

# ── Controlled vocabularies (reference constants — data only, no logic) ───────

REPRESENTS_VALUES = ("performers", "rights_owners", "both")

STREAM_SIDES = ("composition", "recording")

# Which corpus holds the collecting bodies for a stream.
COLLECTED_BY_REFS = ("publishing_data", "royalties_data")

# "UK" (not "GB") matches the grant_data.py / publishing_data.py convention.
ROYALTY_COUNTRIES = ("CA", "US", "UK", "AU", "NZ", "DE", "FR", "SE", "DK", "NO", "FI")

# The sentinel later units emit wherever a non-statutory split would otherwise
# be implied — a split is NEVER stated as fact except the SoundExchange
# statutory one (see HONESTY_RULES: only_statutory_split_hardcoded).
SPLIT_UNKNOWN_SENTINEL = "varies_verify_with_society"


# ── Recording-side society library (section A) ────────────────────────────────
# Each body's facts live here ONCE; COUNTRY_ROYALTY_TABLE references these ids.
# ``represents`` says which capacity a body pays: performers, rights_owners
# (masters/producers), or both. Splits are NEVER encoded here except the US
# statutory SoundExchange split — everywhere else the split is
# varies_verify_with_society.
RECORDING_SOCIETIES = {
    # ── United States ──
    "soundexchange": {
        "id": "soundexchange",
        "name": "SoundExchange",
        "country": "US",
        "represents": "both",
        "scope_notes": "US digital non-interactive ONLY (webcasting, satellite "
                       "radio). The US has NO terrestrial-radio neighbouring "
                       "right — AM/FM radio play of a recording pays the "
                       "composition side only, nothing on the recording side.",
        "registration_notes": "Register in rights-owner capacity, performer "
                              "capacity, or BOTH — each capacity is a separate "
                              "registration. The International Mandate "
                              "authorizes SoundExchange to collect foreign "
                              "recording royalties on your behalf via 90+ "
                              "reciprocal agreements with overseas CMOs.",
        # The ONLY hard-coded split in this corpus: the US STATUTORY split for
        # digital non-interactive recording royalties. Every other split
        # anywhere is varies_verify_with_society.
        "statutory_split": {
            "basis": "US statutory (digital non-interactive)",
            "rights_owner_pct": 50,
            "featured_performer_pct": 45,
            "non_featured_performer_pct": 5,
        },
    },
    # ── Canada ──
    "resound": {
        "id": "resound",
        "name": "Re:Sound",
        "country": "CA",
        "represents": "both",
        "scope_notes": "Canada's neighbouring-rights collective for sound "
                       "recordings — performers and makers (rights owners).",
        "registration_notes": "Register via a member organization in the "
                              "applicable capacity; split between performer and "
                              "maker sides: " + SPLIT_UNKNOWN_SENTINEL + ".",
    },
    # ── United Kingdom ──
    "ppl": {
        "id": "ppl",
        "name": "PPL",
        "country": "UK",
        "represents": "both",
        "scope_notes": "UK recording-side body — collects when recorded music "
                       "is played in public or broadcast; pays performers and "
                       "recording rightsholders.",
        "registration_notes": "Register as performer, rights holder, or both — "
                              "separate capacities. PPL also offers "
                              "international collection via reciprocal "
                              "agreements; performer/rights-holder split: "
                              + SPLIT_UNKNOWN_SENTINEL + ".",
    },
    # ── Australia ──
    "ppca": {
        "id": "ppca",
        "name": "PPCA",
        "country": "AU",
        "represents": "both",
        "scope_notes": "Australia's recording-side collecting body — licenses "
                       "recorded music for broadcast and public playing; pays "
                       "licensors (rights owners) and registered Australian "
                       "recording artists.",
        "registration_notes": "Capacity details and payment mechanics: verify "
                              "live with PPCA; splits: "
                              + SPLIT_UNKNOWN_SENTINEL + ".",
    },
    # ── Germany ──
    "gvl": {
        "id": "gvl",
        "name": "GVL",
        "country": "DE",
        "represents": "both",
        "scope_notes": "Germany's collecting society for performers' and "
                       "producers' neighbouring rights.",
        "registration_notes": "Register in performer and/or producer capacity; "
                              "splits: " + SPLIT_UNKNOWN_SENTINEL + ".",
    },
    # ── France (multi-body, split by ROLE — see FR routing notes) ──
    "adami": {
        "id": "adami",
        "name": "ADAMI",
        "country": "FR",
        "represents": "performers",
        "scope_notes": "France — FEATURED (main) performers. France splits "
                       "recording-side collection across four bodies by role.",
        "registration_notes": "Featured performers register here; session "
                              "musicians belong at SPEDIDAM instead.",
    },
    "spedidam": {
        "id": "spedidam",
        "name": "SPEDIDAM",
        "country": "FR",
        "represents": "performers",
        "scope_notes": "France — SESSION (non-featured) musicians. France "
                       "splits recording-side collection across four bodies "
                       "by role.",
        "registration_notes": "Session musicians register here; featured "
                              "performers belong at ADAMI instead.",
    },
    "scpp": {
        "id": "scpp",
        "name": "SCPP",
        "country": "FR",
        "represents": "rights_owners",
        "scope_notes": "France — producers / master rights owners (one of two "
                       "producer societies).",
        "registration_notes": "Producer-side registration; which of SCPP/SPPF "
                              "fits a given catalog: verify live.",
    },
    "sppf": {
        "id": "sppf",
        "name": "SPPF",
        "country": "FR",
        "represents": "rights_owners",
        "scope_notes": "France — independent producers / master rights owners "
                       "(one of two producer societies).",
        "registration_notes": "Producer-side registration; which of SCPP/SPPF "
                              "fits a given catalog: verify live.",
    },
    # ── Sweden ──
    "sami": {
        "id": "sami",
        "name": "SAMI",
        "country": "SE",
        "represents": "performers",
        "scope_notes": "Sweden — performers ONLY. Master-owner collection in "
                       "Sweden is handled separately: verify live.",
        "registration_notes": "Performer-capacity registration only.",
    },
    # ── Norway ──
    "gramo": {
        "id": "gramo",
        "name": "Gramo",
        "country": "NO",
        "represents": "both",
        "scope_notes": "Norway's recording-side body — performers and "
                       "producers.",
        "registration_notes": "Register in performer and/or producer capacity; "
                              "splits: " + SPLIT_UNKNOWN_SENTINEL + ".",
    },
    # ── Denmark / Finland — DISTINCT bodies despite the shared name ──
    "gramex_dk": {
        "id": "gramex_dk",
        "name": "Gramex (Denmark)",
        "country": "DK",
        "represents": "both",
        "scope_notes": "Denmark's recording-side body — performers and "
                       "producers. DISTINCT organization from Gramex Finland "
                       "despite the shared name.",
        "registration_notes": "Register with the DANISH Gramex for Danish "
                              "collection — a Gramex Finland membership does "
                              "not cover Denmark; splits: "
                              + SPLIT_UNKNOWN_SENTINEL + ".",
    },
    "gramex_fi": {
        "id": "gramex_fi",
        "name": "Gramex (Finland)",
        "country": "FI",
        "represents": "both",
        "scope_notes": "Finland's recording-side body — performers and "
                       "producers. DISTINCT organization from Gramex Denmark "
                       "despite the shared name.",
        "registration_notes": "Register with the FINNISH Gramex for Finnish "
                              "collection — a Gramex Denmark membership does "
                              "not cover Finland; splits: "
                              + SPLIT_UNKNOWN_SENTINEL + ".",
    },
}


# ── The four royalty streams a released song generates (section B) ────────────
# The two composition streams are collected by bodies in Reed's corpus
# (publishing_data.SOCIETIES); the two recording streams by bodies here.
STREAMS = {
    "composition_performance": {
        "id": "composition_performance",
        "side": "composition",
        "collected_by_ref": "publishing_data",
        "description": "Performance royalties on the SONG (composition) — "
                       "radio, live, streaming performance share. Collected "
                       "by the writer's PRO.",
        "notes": "Bodies live in publishing_data.SOCIETIES (Reed's corpus) — "
                 "referenced by id, never duplicated here.",
    },
    "composition_mechanical": {
        "id": "composition_mechanical",
        "side": "composition",
        "collected_by_ref": "publishing_data",
        "description": "Mechanical royalties on the SONG (composition) — "
                       "reproduction/streaming mechanicals. Collected by the "
                       "country's mechanical society/agency.",
        "notes": "Bodies live in publishing_data.SOCIETIES (Reed's corpus) — "
                 "referenced by id, never duplicated here.",
    },
    "recording_performance": {
        "id": "recording_performance",
        "side": "recording",
        "collected_by_ref": "royalties_data",
        "description": "Neighbouring-rights / performance royalties on the "
                       "RECORDING — broadcast and public playing of the master. "
                       "Collected by the country's recording-side body, paid "
                       "in performer and/or rights-owner capacity.",
        "notes": "Does NOT exist as a terrestrial-radio right in the US — see "
                 "the US routing notes and soundexchange scope.",
    },
    "us_digital_recording_performance": {
        "id": "us_digital_recording_performance",
        "side": "recording",
        "collected_by_ref": "royalties_data",
        "description": "US-only statutory stream: digital NON-INTERACTIVE "
                       "recording performance (webcasting, satellite radio), "
                       "collected by SoundExchange under the statutory "
                       "50/45/5 split (rights owner / featured / non-featured).",
        "notes": "The only stream with a hard-coded split in this corpus — it "
                 "is US statutory, not a society policy.",
    },
}


# ── Per-country royalty routing (section C) ───────────────────────────────────
# composition_*_ids reference publishing_data.SOCIETIES (Reed's corpus) — a
# cross-module test enforces every id resolves there. recording_performance_ids
# reference RECORDING_SOCIETIES above. A country with NO verified recording
# body in the map carries None + a verify-live note (NZ) — a body is NEVER
# invented.
COUNTRY_ROYALTY_TABLE = {
    "CA": {
        "country": "CA",
        "composition_performance_ids": ("socan",),
        "composition_mechanical_ids": ("cmrra", "socan_rr"),
        "recording_performance_ids": ("resound",),
        "notes": "Composition side routes per Reed's corpus (SOCAN; two RROs). "
                 "Re:Sound covers the recording side for performers and makers.",
    },
    "US": {
        "country": "US",
        "composition_performance_ids": ("ascap", "bmi", "sesac", "gmr"),
        "composition_mechanical_ids": ("the_mlc", "hfa", "mri"),
        "recording_performance_ids": ("soundexchange",),
        "notes": "NO terrestrial-radio neighbouring right in the US — AM/FM "
                 "play pays the composition side only. The recording side is "
                 "the SoundExchange digital non-interactive statutory stream "
                 "(50/45/5). Writer picks ONE PRO; MLC registration is "
                 "separate and free.",
    },
    "UK": {
        "country": "UK",
        "composition_performance_ids": ("prs",),
        "composition_mechanical_ids": ("mcps",),
        "recording_performance_ids": ("ppl",),
        "notes": "PRS/MCPS on the composition side; PPL on the recording side "
                 "(performer and rights-holder capacities).",
    },
    "AU": {
        "country": "AU",
        "composition_performance_ids": ("apra",),
        "composition_mechanical_ids": ("amcos",),
        "recording_performance_ids": ("ppca",),
        "notes": "APRA AMCOS on the composition side; PPCA on the recording "
                 "side.",
    },
    "NZ": {
        "country": "NZ",
        "composition_performance_ids": ("apra",),
        "composition_mechanical_ids": ("amcos",),
        "recording_performance_ids": None,
        "notes": "APRA AMCOS covers the composition side. Recording side: no "
                 "verified body in this corpus — verify live with a local "
                 "authority before registering; a body is never guessed.",
    },
    "DE": {
        "country": "DE",
        "composition_performance_ids": ("gema",),
        "composition_mechanical_ids": ("gema",),
        "recording_performance_ids": ("gvl",),
        "notes": "GEMA unified on the composition side; GVL on the recording "
                 "side (performers and producers).",
    },
    "FR": {
        "country": "FR",
        "composition_performance_ids": ("sacem",),
        "composition_mechanical_ids": ("sacem",),
        "recording_performance_ids": ("adami", "spedidam", "scpp", "sppf"),
        "notes": "SACEM unified on the composition side. The recording side "
                 "is MULTI-BODY, split by ROLE: ADAMI (featured performers), "
                 "SPEDIDAM (session musicians), SCPP and SPPF (producers / "
                 "master owners). Register with the body matching your role.",
    },
    "SE": {
        "country": "SE",
        "composition_performance_ids": ("stim",),
        "composition_mechanical_ids": ("ncb",),
        "recording_performance_ids": ("sami",),
        "notes": "STIM/NCB on the composition side; SAMI (performers ONLY) on "
                 "the recording side — master-owner collection: verify live.",
    },
    "DK": {
        "country": "DK",
        "composition_performance_ids": ("koda",),
        "composition_mechanical_ids": ("ncb",),
        "recording_performance_ids": ("gramex_dk",),
        "notes": "KODA/NCB on the composition side; Gramex DENMARK on the "
                 "recording side (distinct from Gramex Finland).",
    },
    "NO": {
        "country": "NO",
        "composition_performance_ids": ("tono",),
        "composition_mechanical_ids": ("ncb",),
        "recording_performance_ids": ("gramo",),
        "notes": "TONO/NCB on the composition side; Gramo on the recording "
                 "side.",
    },
    "FI": {
        "country": "FI",
        "composition_performance_ids": ("teosto",),
        "composition_mechanical_ids": ("ncb",),
        "recording_performance_ids": ("gramex_fi",),
        "notes": "Teosto/NCB on the composition side; Gramex FINLAND on the "
                 "recording side (distinct from Gramex Denmark).",
    },
}


# ── Registration-situation axes (section D) ───────────────────────────────────
# The checklist engine (later units) reads a situation object whose flags map
# to these axes. EVERY flag requires explicit artist confirmation — an
# unsupplied flag is a [NEEDS: <flag>] gap, never a default (HONESTY_RULES:
# situation_flags_explicit_only).
_EXPLICIT_ONLY = "explicit confirmation required, never inferred"

REGISTRATION_SITUATION_SPEC = {
    "country_of_residence": {
        "axis": "country_of_residence",
        "type": "country_code",
        "description": "The artist's home country (one of ROYALTY_COUNTRIES) — "
                       "determines which bodies collect each stream.",
        "confirmation": _EXPLICIT_ONLY,
    },
    "self_published": {
        "axis": "self_published",
        "type": "bool",
        "description": "Whether the artist controls their own publishing (no "
                       "publisher/admin deal holds the publisher share).",
        "confirmation": _EXPLICIT_ONLY,
    },
    "owns_masters": {
        "axis": "owns_masters",
        "type": "bool",
        "description": "Whether the artist owns the master recordings "
                       "(rights-owner capacity on the recording side).",
        "confirmation": _EXPLICIT_ONLY,
    },
    "performed_on_recording": {
        "axis": "performed_on_recording",
        "type": "bool",
        "description": "Whether the artist performed on the recordings "
                       "(performer capacity on the recording side).",
        "confirmation": _EXPLICIT_ONLY,
    },
    "has_producers_or_session_players": {
        "axis": "has_producers_or_session_players",
        "type": "bool",
        "description": "Whether producers or session players contributed and "
                       "may be owed a directed share of recording royalties "
                       "(letter-of-direction territory).",
        "confirmation": _EXPLICIT_ONLY,
    },
}

# Registration rules AS DATA: each maps an axis condition to one required
# checklist entry. body_ref names a specific body (corpus given by
# body_ref_corpus); body_lookup "by_country" means the engine resolves the
# body from COUNTRY_ROYALTY_TABLE (or publishing_data) for the artist's
# country. Later units apply these mechanically — no rule lives in code.
REGISTRATION_RULES = (
    {
        "id": "writer_home_pro",
        "condition": {"axis": "country_of_residence", "requires": "supplied"},
        "registration": "home_pro_writer_membership",
        "capacity": "writer",
        "body_ref": None,
        "body_lookup": "by_country",
        "stream_id": "composition_performance",
        "reason": "A writer joins their HOME society once (writer capacity) "
                  "and collects composition performance royalties worldwide "
                  "through reciprocal agreements.",
        "notes": None,
    },
    {
        "id": "self_published_publisher_registration",
        "condition": {"axis": "self_published", "equals": True},
        "registration": "publisher_membership_or_entity_registration",
        "capacity": "publisher",
        "body_ref": None,
        "body_lookup": "by_country",
        "stream_id": "composition_performance",
        "reason": "A self-published writer must ALSO register in publisher "
                  "capacity (publisher member / entity registration) or the "
                  "publisher share of composition royalties goes uncollected.",
        "notes": None,
    },
    {
        "id": "us_catalog_mlc",
        "condition": {"axis": "country_of_residence", "equals": "US"},
        "registration": "mlc_work_registration",
        "capacity": "rights_holder",
        "body_ref": "the_mlc",
        "body_ref_corpus": "publishing_data",
        "body_lookup": None,
        "stream_id": "composition_mechanical",
        "reason": "A US-connected catalog must be registered with The MLC for "
                  "US digital mechanicals — separate from PRO affiliation and "
                  "free.",
        "notes": "separate and free",
    },
    {
        "id": "masters_rights_owner_registration",
        "condition": {"axis": "owns_masters", "equals": True},
        "registration": "recording_body_rights_owner_registration",
        "capacity": "rights_owner",
        "body_ref": None,
        "body_lookup": "by_country",
        "stream_id": "recording_performance",
        "stream_id_us_override": "us_digital_recording_performance",
        "reason": "Owning the masters means recording-side royalties are owed "
                  "in RIGHTS-OWNER capacity — register with the country's "
                  "recording body.",
        "notes": "US-based: register with SoundExchange in rights-owner "
                 "capacity and note the International Mandate (authorizes "
                 "foreign collection via 90+ reciprocal CMOs).",
    },
    {
        "id": "performer_registration",
        "condition": {"axis": "performed_on_recording", "equals": True},
        "registration": "recording_body_performer_registration",
        "capacity": "performer",
        "body_ref": None,
        "body_lookup": "by_country",
        "stream_id": "recording_performance",
        "stream_id_us_override": "us_digital_recording_performance",
        "reason": "Performing on the recording means recording-side royalties "
                  "are owed in PERFORMER capacity — register with the "
                  "country's recording body. Both hats (owner AND performer) "
                  "= BOTH capacities, each its own registration.",
        "notes": None,
    },
    {
        "id": "producers_session_players_lod",
        "condition": {"axis": "has_producers_or_session_players", "equals": True},
        "registration": "letter_of_direction",
        "capacity": "rights_owner",
        "body_ref": "soundexchange",
        "body_ref_corpus": "royalties_data",
        "body_lookup": None,
        "stream_id": "us_digital_recording_performance",
        "reason": "Producers / session players owed a directed share are paid "
                  "via a Letter of Direction lodged with the collecting body "
                  "— the directed percentage is ALWAYS a supplied input, "
                  "never computed or suggested.",
        "notes": "Mechanism named for SoundExchange; a similar mechanism "
                 "exists at PPL — verify live for other bodies.",
    },
)


# ── Letter of Direction — canonical field set (section E) ──────────────────────
# Later scaffold units consume this as data. percentage_directed is a SUPPLIED
# input — never computed, never suggested; absent means a [NEEDS: ...] gap.
LOD_SPEC = {
    "fields": (
        {"field": "artist_legal_name", "required": True,
         "description": "The artist's legal name (the party directing payment)."},
        {"field": "payee_legal_name", "required": True,
         "description": "Legal name of the payee the share is directed to "
                        "(producer / session player)."},
        {"field": "payee_contact", "required": True,
         "description": "Payee contact details."},
        {"field": "recordings_covered", "required": True,
         "description": "The recordings covered, identified WITH their ISRCs."},
        {"field": "percentage_directed", "required": True,
         "description": "The percentage directed to the payee — a SUPPLIED "
                        "input the parties agreed, NEVER computed or "
                        "suggested; unknown surfaces as a [NEEDS: ...] gap."},
        {"field": "effective_date", "required": True,
         "description": "Effective date of the direction."},
        {"field": "signatures_both_parties", "required": True,
         "description": "Signatures of BOTH parties — an unsigned letter "
                        "directs nothing."},
    ),
    "reminders": (
        {"id": "draft_for_review_only",
         "text": "A generated letter is a DRAFT-FOR-REVIEW starting point — "
                 "not submit-ready, not a legal document; agreements route to "
                 "Lex framed draft-for-review."},
        {"id": "percentage_directed_supplied_only",
         "text": "percentage_directed is a supplied input, NEVER computed or "
                 "suggested — a missing percentage is a [NEEDS: ...] gap, not "
                 "a recommendation."},
    ),
}


# ── Metadata doctrine (section F) ──────────────────────────────────────────────
METADATA_DOCTRINE = {
    "consistent_identifiers_everywhere": "ISRC + ISWC + legal names + IPI must "
                                         "be CONSISTENT across every "
                                         "registration, at every body. A "
                                         "mismatch leaves royalties sitting "
                                         "unmatched in the black box.",
    "distributor_does_not_collect_everything": "A distributor pays the "
                                               "streaming master share ONLY — "
                                               "it does NOT collect PRO, "
                                               "mechanical, or recording-side "
                                               "performance royalties. Each "
                                               "stream needs its own "
                                               "registration.",
    "both_hats_us_registration": "A US artist who owns the masters AND "
                                 "performed on them registers with "
                                 "SoundExchange in BOTH capacities — rights "
                                 "owner and performer are separate "
                                 "registrations paying separate statutory "
                                 "shares.",
}


# ── Honesty rules (section G — Jade/Reed discipline carried over) ──────────────
# Structured records with stable ids so later units can cite a rule_id in
# their outputs. Data only — nothing here enforces anything.
HONESTY_RULES = (
    {"id": "unknown_is_none",
     "statement": "Unknown values are None plus a 'verify live' note. Never "
                  "invent a rate, a %, or a society rule.",
     "allowed": "Returning None with an explicit verify-live note.",
     "forbidden": "Guessing or fabricating any value."},
    {"id": "only_statutory_split_hardcoded",
     "statement": "The ONLY split ever stated as fact is the US statutory "
                  "SoundExchange split: 50% rights owner / 45% featured "
                  "performer / 5% non-featured performers.",
     "allowed": "Quoting the SoundExchange statutory 50/45/5 split.",
     "forbidden": "Stating ANY other split as fact — emit "
                  "varies_verify_with_society instead."},
    {"id": "situation_flags_explicit_only",
     "statement": "Registration-situation flags (self_published, owns_masters, "
                  "performed_on_recording, ...) are applied ONLY when the "
                  "artist explicitly supplied them.",
     "allowed": "Applying a rule whose axis flag was explicitly supplied.",
     "forbidden": "Defaulting or inferring a flag — an unsupplied axis is a "
                  "[NEEDS: <flag>] gap and its rule branch does not fire."},
    {"id": "free_text_is_note_only",
     "statement": "Free-text inputs surface as a note — never parsed into a "
                  "filter or rule.",
     "allowed": "Carrying free text through verbatim as a note.",
     "forbidden": "Parsing free text into a filter, flag, or rule."},
    {"id": "no_tax_or_legal_advice",
     "statement": "Registration routing is logistics, not tax or legal advice "
                  "— tax questions route to a qualified professional, and "
                  "agreements (including a Letter of Direction) route to Lex "
                  "framed as a draft-for-review.",
     "allowed": "Explaining which body collects which stream and what a "
                "registration requires.",
     "forbidden": "Advising on tax positions or presenting a generated "
                  "agreement as final/legal."},
)
