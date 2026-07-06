"""
PLMKR Creative-Director — structured creative-copy conventions data (Cree's real knowledge base).

Unit 1 (data-only): the conventions that govern the copy documents an artist
campaign runs on — bios (three lengths), press releases, one-sheets, EPK
outlines, and caption sets — encoded as structured records, plus the honesty
rules Cree's scaffold engine (later units) applies. This corpus encodes
DOCUMENT STRUCTURE AND CONVENTIONS ONLY — never an artist fact.

RELATIONSHIP TO THE OTHER CORPORA (grant_data / publishing_data / royalties_data):
  - Same discipline, different domain: those corpora encode verified external
    facts (societies, rules, splits); THIS corpus deliberately contains no
    external facts at all — copy conventions are structural doctrine, and the
    facts that fill a copy document (streams, quotes, collabs, milestones)
    exist only at run time as artist-supplied inputs. Nothing here overlaps
    with or references another corpus.

WHAT THIS MODULE IS (and is NOT):
  - DATA ONLY. No functions, no classes, no imports, no I/O, no network, no
    secrets. ``creative_director_service`` consumption of these records lands
    in LATER units — NOT here. Nothing in this module executes or enforces
    anything.
  - Every record is a plain, JSON-serializable dict; list-valued fields are
    tuples (no sets/frozensets) so ``json.dumps`` flows every field untouched.

HARD RULES honored here (CREE-SPECIFIC):
  - This domain is made of facts (streams, quotes, collabs, milestones) — NO
    fact, stat, press quote, or comparison is ever invented or synthesized
    anywhere. Every fact slot at run time is a supplied input verbatim, a
    [NEEDS:<fact>] gap, or an [ARTIST-SUPPLIED:<confirm>] reminder (see
    HONESTY_RULES: facts_supplied_or_marked).
  - ZERO example stats live in this corpus. The only numeric values anywhere
    are the bio word-range bounds — a numeric scan in the tests enforces this.
  - bio_long's upper word bound is None — genuinely open-ended, never guessed
    (the unknown = None discipline carried over from the other corpora).
  - skip_unimpressive_stats is a structural choice OFFERED to the artist —
    never a silent edit (ONE_SHEET_SPEC doctrine encodes offered_to_artist).
  - Free-text run-time inputs surface as notes ONLY — never parsed into a
    filter or rule (HONESTY_RULES apply at the service layer; nothing here
    executes).

SCHEMA (per constant):
  Vocabulary (reference only; nothing enforces it):
    COPY_DOC_TYPES
  Bio length specs + shared conventions (section A):
    BIO_SPECS        dict[id] -> {id, word_range, typical_uses,
                                  content_expectations}
    BIO_CONVENTIONS  dict[id] -> {id, text}
  Press-release ordered sections + conventions (section B):
    PRESS_RELEASE_SPEC {sections: (ordered records), conventions: (records)}
  One-sheet ordered elements + doctrine (section C):
    ONE_SHEET_SPEC     {elements: (ordered records), doctrine: (records)}
  EPK outline core/optional components + doctrine (section D):
    EPK_OUTLINE_SPEC   {core_components, optional_components, doctrine}
  Caption-set elements + rules (section E):
    CAPTION_SET_SPEC   {elements: (ordered records), rules: (records)}
  Discipline (stable ids later units cite in outputs — section F):
    HONESTY_RULES
"""

# ── Controlled vocabulary (reference constant — data only, no logic) ───────────

COPY_DOC_TYPES = (
    "bio_short", "bio_medium", "bio_long",
    "press_release", "one_sheet", "epk_outline", "caption_set",
)


# ── Bio length specs (section A) ───────────────────────────────────────────────
# word_range is (lower_bound, upper_bound) in words. bio_long's upper bound is
# None — genuinely open-ended, NEVER guessed (unknown = None discipline). These
# bounds are the ONLY numeric values anywhere in this corpus (test-enforced) —
# a copy corpus with example stats would be a fabrication vector.
BIO_SPECS = {
    "bio_short": {
        "id": "bio_short",
        "word_range": (50, 100),
        "typical_uses": ("playlist pitches", "social profiles",
                         "program blurbs", "one-sheet bio slot"),
        "content_expectations": "The elevator pitch: who the artist is, what "
                                "they sound like, and the single most "
                                "distinctive hook — every fact artist-supplied.",
    },
    "bio_medium": {
        "id": "bio_medium",
        "word_range": (200, 300),
        "typical_uses": ("press outreach", "EPK bio slot",
                         "festival and venue programs", "website about page"),
        "content_expectations": "The press standard: distinctive hook up top, "
                                "the current project, key achievements woven "
                                "into the narrative, a closing line that lands "
                                "the artist's direction — every fact "
                                "artist-supplied.",
    },
    "bio_long": {
        "id": "bio_long",
        "word_range": (500, None),
        "typical_uses": ("website full bio", "feature-writer background",
                         "EPK long-form bio slot"),
        "content_expectations": "The full narrative: origin, artistic "
                                "development, project-by-project arc, "
                                "achievements in context, where the artist is "
                                "headed — open-ended length (upper bound None, "
                                "never guessed); every fact artist-supplied.",
    },
}

# Shared bio conventions — structural doctrine, cited by id in later units.
BIO_CONVENTIONS = {
    "third_person": {
        "id": "third_person",
        "text": "Bios are written in the third person — first person reads "
                "less legit in press and programming contexts.",
    },
    "avoid_generic_cliches": {
        "id": "avoid_generic_cliches",
        "text": "Avoid generic cliches ('unique sound', 'one of a kind', "
                "'hotly tipped') — they say nothing and read as filler.",
    },
    "lead_with_distinctive_hook": {
        "id": "lead_with_distinctive_hook",
        "text": "Lead with the single most distinctive, artist-supplied hook "
                "— not birthplace boilerplate.",
    },
    "achievements_woven_not_listed": {
        "id": "achievements_woven_not_listed",
        "text": "Achievements are woven into the narrative, not stacked as a "
                "trophy list.",
    },
    "press_quote_opener_optional_only_if_real": {
        "id": "press_quote_opener_optional_only_if_real",
        "text": "Opening with a press quote is optional and allowed ONLY when "
                "the quote is real, supplied verbatim, and attributed to its "
                "source — a quote is never synthesized.",
    },
    "every_fact_artist_supplied": {
        "id": "every_fact_artist_supplied",
        "text": "Every fact in a bio is artist-supplied or explicitly marked "
                "as missing — never synthesized, never assumed.",
    },
}


# ── Press-release spec (section B) ─────────────────────────────────────────────
# The section order is FIXED — encoded as an ordered tuple so later units emit
# sections in exactly this sequence.
PRESS_RELEASE_SPEC = {
    "sections": (
        {"key": "for_immediate_release_line",
         "title": "For Immediate Release",
         "guidance": "The standing 'FOR IMMEDIATE RELEASE' line at the very "
                     "top — convention, not content."},
        {"key": "headline",
         "title": "Headline",
         "guidance": "The news in one line — what happened, stated plainly; "
                     "no hype adjectives doing the work of a missing fact."},
        {"key": "dateline",
         "title": "Dateline",
         "guidance": "City plus date opening the first paragraph — both are "
                     "supplied inputs, never assumed."},
        {"key": "para_1_pitch",
         "title": "Paragraph One — The Pitch",
         "guidance": "The news in one to two sentences: who, what, when. A "
                     "reader who stops here has the whole story."},
        {"key": "para_2_supporting_context",
         "title": "Paragraph Two — Supporting Context",
         "guidance": "The story behind the news: context, process, "
                     "collaborators. Quotes live here ONLY when real, "
                     "supplied verbatim, and attributed with a source."},
        {"key": "para_3_short_bio",
         "title": "Paragraph Three — Short Bio",
         "guidance": "A short-bio paragraph (bio_short territory) grounding "
                     "who the artist is — every fact artist-supplied."},
        {"key": "boilerplate",
         "title": "Boilerplate",
         "guidance": "The standing 'About the artist' paragraph reused across "
                     "releases — supplied or built from supplied facts."},
        {"key": "contact",
         "title": "Contact",
         "guidance": "Name, role, and email of the person press should reach "
                     "— all three supplied inputs."},
        {"key": "links",
         "title": "Links",
         "guidance": "Music and press photos as LINKS, not attachments — the "
                     "delivery convention journalists expect."},
    ),
    "conventions": (
        {"id": "front_load_for_skimming",
         "text": "Front-load everything — journalists skim; the news must "
                 "survive a reader who stops after the headline and first "
                 "paragraph."},
        {"id": "quotes_only_real_and_attributed",
         "text": "Quotes appear ONLY when real, supplied verbatim, and "
                 "attributed to a named source — a quote without a source is "
                 "a gap, never a quote."},
        {"id": "one_release_one_news_item",
         "text": "One press release carries ONE news item — stacking "
                 "announcements buries all of them."},
    ),
}


# ── One-sheet spec (section C) ─────────────────────────────────────────────────
# Ordered elements of the single-page artist summary, plus its doctrine.
# skip_unimpressive_stats is a structural choice OFFERED to the artist — the
# engine never silently drops or edits a stats block on its own.
ONE_SHEET_SPEC = {
    "elements": (
        {"key": "artist_name_prominent",
         "title": "Artist Name",
         "guidance": "The artist name, prominent — the page is scannable and "
                     "the name is what must stick."},
        {"key": "genre_2_to_3_words",
         "title": "Genre",
         "guidance": "Genre in two to three words — a positioning label, not "
                     "a paragraph."},
        {"key": "press_photo_slot",
         "title": "Press Photo",
         "guidance": "One press photo slot — the supplied photo, linked or "
                     "placed, never a stand-in image."},
        {"key": "short_bio",
         "title": "Short Bio",
         "guidance": "The bio_short — every fact artist-supplied."},
        {"key": "highlights_stats_block",
         "title": "Highlights / Stats",
         "guidance": "Supplied stats and highlights VERBATIM. When this block "
                     "is empty, skipping it entirely is a structural choice "
                     "OFFERED to the artist (skip_unimpressive_stats) — never "
                     "decided silently, and a stat is never invented to fill "
                     "it."},
        {"key": "press_quotes_with_citation",
         "title": "Press Quotes",
         "guidance": "Real press quotes with their citation (outlet and/or "
                     "writer) — verbatim and attributed, or omitted."},
        {"key": "release_block_optional",
         "title": "Current Release (optional)",
         "guidance": "Optional current-release block.",
         "fields": ("title", "date", "one_sentence")},
        {"key": "social_streaming_links",
         "title": "Social & Streaming Links",
         "guidance": "The supplied social and streaming links."},
        {"key": "contact_with_role",
         "title": "Contact",
         "guidance": "Contact with their role — who to reach and in what "
                     "capacity."},
    ),
    "doctrine": (
        {"id": "scannable_under_30_seconds",
         "text": "A one-sheet earns its keep in under thirty seconds of "
                 "scanning — dense pages get skipped."},
        {"id": "skip_unimpressive_stats",
         "text": "When the numbers do not sell the artist yet, skipping the "
                 "stats block entirely is often the stronger page — but that "
                 "is a structural choice OFFERED to the artist, never a "
                 "silent edit by the engine.",
         "choice_type": "offered_to_artist",
         "never": "silent_edit"},
        {"id": "every_element_earns_its_place",
         "text": "Every element on the page earns its place — anything that "
                 "does not sell the artist to THIS reader comes off."},
        {"id": "pdf_delivery_convention",
         "text": "One-sheets travel as a single PDF page — the format venues "
                 "and press expect to forward internally."},
    ),
}


# ── EPK outline spec (section D) ───────────────────────────────────────────────
EPK_OUTLINE_SPEC = {
    "core_components": (
        {"key": "bio_all_lengths",
         "title": "Bios (all lengths)",
         "guidance": "All three bio lengths (bio_short / bio_medium / "
                     "bio_long) so every recipient finds the size they need."},
        {"key": "artist_brief_3_to_5_sentences",
         "title": "Artist Brief",
         "guidance": "A three-to-five-sentence brief — the fastest possible "
                     "read on who the artist is."},
        {"key": "promo_photos_list",
         "title": "Promo Photos",
         "guidance": "The supplied promo photos, listed/linked with credits "
                     "where supplied."},
        {"key": "music_3_to_5_tracks",
         "title": "Music",
         "guidance": "Three to five tracks — the strongest material, linked "
                     "not attached."},
        {"key": "video",
         "title": "Video",
         "guidance": "Video links where supplied — live footage and music "
                     "videos read differently; label which is which."},
        {"key": "press_and_reviews",
         "title": "Press & Reviews",
         "guidance": "Real coverage with citations — verbatim quotes with "
                     "their source, or omitted."},
        {"key": "highlights",
         "title": "Highlights",
         "guidance": "Supplied career highlights verbatim — never padded, "
                     "never invented."},
        {"key": "social_streaming_links",
         "title": "Social & Streaming Links",
         "guidance": "The supplied social and streaming links."},
        {"key": "contact",
         "title": "Contact",
         "guidance": "Who to reach, in what role, at what address."},
    ),
    "optional_components": (
        {"key": "fact_sheet",
         "title": "Fact Sheet",
         "guidance": "A skimmable fact sheet — supplied facts only.",
         "fields": ("location", "members", "genre", "key_points")},
        {"key": "tour_dates",
         "title": "Tour Dates",
         "guidance": "Upcoming supplied dates — stale dates hurt more than "
                     "no dates."},
        {"key": "artwork",
         "title": "Artwork",
         "guidance": "Release artwork where supplied."},
        {"key": "rider",
         "title": "Rider",
         "guidance": "Technical/hospitality rider when the audience is "
                     "booking."},
        {"key": "lyrics_liner_notes",
         "title": "Lyrics & Liner Notes",
         "guidance": "Lyrics or liner notes when the audience wants depth "
                     "(press features, sync)."},
    ),
    "doctrine": (
        {"id": "decision_tool_not_scrapbook",
         "text": "An EPK is a decision tool, not a scrapbook — it exists so a "
                 "gatekeeper can say yes quickly, not to archive everything "
                 "the artist has done."},
        {"id": "tailor_per_audience",
         "text": "Tailor the assembly per audience — booking, media, and "
                 "radio each read for different things; the outline flexes, "
                 "the honesty rules do not.",
         "audiences": ("booking", "media", "radio")},
    ),
}


# ── Caption-set spec (section E) ───────────────────────────────────────────────
CAPTION_SET_SPEC = {
    "elements": (
        {"key": "hook_line",
         "title": "Hook Line",
         "guidance": "The scroll-stopping first line — built from a supplied "
                     "fact or angle, never an invented claim."},
        {"key": "context_line",
         "title": "Context Line",
         "guidance": "One line of context — what this post is about, in the "
                     "artist's actual situation."},
        {"key": "cta",
         "title": "Call to Action",
         "guidance": "What the reader should do — listen, save, share, "
                     "pre-save — tied to a real, supplied link or event."},
        {"key": "tag_link_placeholders",
         "title": "Tags & Links",
         "guidance": "Placeholders for tags and links — filled with supplied "
                     "handles/URLs only, never guessed."},
    ),
    "rules": (
        {"id": "no_invented_urgency_or_milestones",
         "text": "No invented urgency or milestones — no fake 'almost sold "
                 "out', no round-number stream counts the artist never "
                 "supplied. A caption's claims are supplied facts or nothing."},
    ),
}


# ── Honesty rules (section F — Jade/Reed/Nadia discipline, Cree-hardened) ──────
# Structured records with stable ids so later units can cite a rule_id in
# their outputs. Data only — nothing here enforces anything. This domain is
# MADE of facts (streams, quotes, collabs, milestones), so the fabrication
# rules are the corpus's spine.
HONESTY_RULES = (
    {"id": "facts_supplied_or_marked",
     "statement": "Every fact in any copy document is one of exactly three "
                  "things: the supplied input VERBATIM, an explicit "
                  "[NEEDS:<fact>] gap, or an [ARTIST-SUPPLIED:<confirm>] "
                  "reminder. There is no fourth state.",
     "allowed": "Carrying a supplied fact verbatim; surfacing a missing fact "
                "as [NEEDS:<fact>]; flagging a confirm-with-artist item as "
                "[ARTIST-SUPPLIED:<confirm>].",
     "forbidden": "Inventing, estimating, rounding, or synthesizing any fact, "
                  "stat, quote, collab, or milestone."},
    {"id": "quotes_verbatim_with_source_or_omitted",
     "statement": "A press quote appears ONLY verbatim and with its source. "
                  "A quote whose source is missing is a gap, not a quote — "
                  "and a quote is NEVER synthesized.",
     "allowed": "Quoting supplied text verbatim with its supplied attribution.",
     "forbidden": "Paraphrasing a quote, inventing a quote, or including a "
                  "supplied quote without its source."},
    {"id": "stats_supplied_only",
     "statement": "Stats (streams, followers, sales, chart positions) appear "
                  "ONLY as supplied — passed through verbatim, never "
                  "computed, never estimated, never refreshed from memory.",
     "allowed": "Passing a supplied stat through verbatim.",
     "forbidden": "Inventing, estimating, updating, or 'rounding' any metric."},
    {"id": "comparisons_only_if_supplied",
     "statement": "Artist comparisons ('for fans of X') appear ONLY when the "
                  "artist supplied them.",
     "allowed": "Using a comparison the artist explicitly supplied.",
     "forbidden": "Generating a comparison — and note the convention: "
                  "unsupplied comparisons age badly and invite dismissal, so "
                  "even supplied ones are worth a second look with the "
                  "artist.",
     "convention_note": "Comparisons are a liability convention-wise — lean "
                        "on the artist's own distinctive hook instead; if a "
                        "comparison is used at all, it is the artist's "
                        "choice."},
    {"id": "drafts_not_publish_ready",
     "statement": "Every generated copy document is a DRAFT for the artist's "
                  "review — never publish-ready, never sent or posted on the "
                  "engine's say-so.",
     "allowed": "Producing a clearly-framed draft for review.",
     "forbidden": "Presenting any generated copy as final or publish-ready."},
)
