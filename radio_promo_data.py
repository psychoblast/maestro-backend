"""
PLMKR Solo — radio + DSP-editorial promo doctrine corpus (data only).

A data-only sibling of grant_data.py / royalties_data.py / copy_data.py covering
Solo's lane: college/community radio (US + Canada), the Canadian-content (CanCon)
and MAPL rules, the honest limits of commercial radio, DSP editorial pitching,
the delivery-layer servicing platforms, satellite/public radio, and the section
honesty rules. Solo's lane is RADIO + DSP EDITORIAL only.

BOUNDARY (Tommy-decided, absolute): playlist-CURATOR outreach belongs to the
management department (Marcus), NOT Solo. It is encoded in OUT_OF_SCOPE and Solo
defines NO curator tools.

CORPUS CONTRACT (hard rules for this module):
  - Data only: no def / class / import / call anywhere. Pure literals.
  - JSON-serializable throughout; ``None`` for an unknown (a cost, a panel size,
    a submission process), paired with a "verify live" note — never a guess.
  - Free text is a NOTE (a convention to convey), never a hard rule the code
    branches on.
  - NEVER assert or compute a song's CanCon / MAPL status — that risks the
    STATION's licence; only the artist's DECLARED letters pass through.
  - No placement guarantee: a pitch is CONSIDERATION, never a placement.
  - The only quota percentages that appear anywhere are 35 (commercial) and 50
    (CBC); no currency amount appears at all (platform costs are None).
"""

# ── COLLEGE_RADIO (US + Canada) — the reachable, relationship-driven lane ───────
COLLEGE_RADIO = {
    "nacc": {
        "name": "North American College & Community Chart",
        "mechanics": ("a weekly Top 200 built from reporting stations' own Top 30 "
                      "charts; stations carry weights (heaviest for the majors like "
                      "KEXP / KCRW)."),
        "station_weight_note": "reporting-station weights run 1-5 (5 = heaviest).",
        "panel_size_note": ("roughly 200-400 reporting stations at any time — "
                            "verify live."),
        "adds_db": "the Going For Adds database is where new servicing is listed.",
        "servicing": "serviced through digital servicing platforms.",
        "access_note": ("a free tier is limited; paid tiers exist — costs verify "
                        "live."),
    },
    "earshot": {
        "name": "Earshot / !Earshot",
        "scope": "the Canadian campus + community radio charts.",
        "note": "the Canadian counterpart to the NACC panel.",
    },
    "campaign_shape": {
        "typical_length": "about 4+ weeks — airplay builds slowly.",
        "followup": ("email servicing plus weekly phone calls to music directors — "
                     "the phone is the relationship channel."),
        "momentum_doctrine": ("a consistent flow of new information is what convinces "
                              "a station to add — momentum, not a single blast."),
    },
}


# ── CANCON — encode carefully; misdeclaration risks the STATION's licence ───────
CANCON = {
    "rule": {
        "commercial_popular_music": ("35% of musical selections weekly AND 35% "
                                     "between 6am-6pm Mon-Fri (CRTC)."),
        "cbc": "50% (CBC).",
        "specialty": "specialty services carry lower / different quotas — verify live.",
    },
    "mapl": {
        "qualifies": "a selection qualifies as CanCon on any 2 of the 4 MAPL points per SONG.",
        "m": "M — the Music is composed entirely by a Canadian (half-point provisions exist).",
        "a": "A — the Artist performs the music/lyrics principally by a Canadian.",
        "p": "P — the Performance is recorded, or performed live, wholly in Canada.",
        "l": "L — the Lyrics are written entirely by a Canadian.",
        "declaration": ("the artist DECLARES which letters apply (e.g. 'MAL') when "
                        "servicing — the declaration is theirs, never computed here."),
    },
    "honesty": {
        "rule": ("NEVER assert or compute a song's CanCon / MAPL status. "
                 "Misdeclaration risks the STATION's licence; only pass through the "
                 "artist's declared letters, or mark [NEEDS:mapl_declaration]."),
    },
}


# ── COMMERCIAL_RADIO — honest context, not a service Solo performs ──────────────
COMMERCIAL_RADIO = {
    "barrier_note": ("national commercial airplay generally requires established "
                     "promo infrastructure (paid radio promoters, label relationships) "
                     "— encoded as honest context, NOT a service Solo performs."),
    "formats_note": "formats and reporting panels vary by market — verify live.",
}


# ── DSP_EDITORIAL — the pitch is consideration, never a placement ───────────────
DSP_EDITORIAL = {
    "spotify": {
        "window": ("pitch at least 7 days before release (the minimum), ideally 3-4 "
                   "weeks ahead."),
        "via": "Spotify for Artists — unreleased music only.",
        "copy": ("specific genre, mood, story, instruments, and cultural context — "
                 "'Pop' tells an editor nothing."),
    },
    "apple_amazon": {
        "via": "pitched through their respective artist dashboards.",
    },
    "doctrine": {
        "no_guarantees": "a pitch is CONSIDERATION, never a guaranteed placement.",
        "one_pitch_per_release_focus": ("focus the one editorial pitch per release on "
                                        "the single that best fits editorial."),
    },
}


# ── SERVICING_PLATFORMS (ADDENDUM) — the delivery layer. They DELIVER; they ─────
# guarantee nothing and do no follow-up. Named platforms are real and current as
# of July 2026; prices/packages/processes change — verify live. Naming is never
# an endorsement of a specific paid package. All costs are None + verify live.
SERVICING_PLATFORMS = {
    "yangaroo_dmds": {
        "scope": ("industry-standard secure delivery to commercial radio + media "
                  "across Canada / US (plus SiriusXM channels)."),
        "model": "format-based destination packages.",
        "tracking": "delivery only — with an optional Nielsen BDS airplay add-on.",
        "costs": None,
        "costs_note": "verify live.",
    },
    "play_mpe": {
        "company": "Destiny Media Technologies (Vancouver).",
        "scope": ("major-label-grade promotional delivery to radio PDs, press, and "
                  "A&R — Warner / Sony / Universal use it; global reach."),
        "model": "genre / market destination lists.",
        "costs": None,
        "costs_note": "varies widely by genre / market — verify live.",
    },
    "earshot_distro": {
        "org": "NCRA / ANREC (a non-profit).",
        "scope": "roughly 115-125 Canadian campus / community stations.",
        "costs": None,
        "costs_note": "low per-song / album upload fees — verify live.",
        "charting": ("the earshot-online national top 50 (about 20 reporting "
                     "stations); airplay on about 5+ stations a week can chart."),
        "factor_link": ("earshot charting feeds FACTOR ratings, which improves grant "
                        "eligibility — CROSS-REF the grants / funding department "
                        "(Jade)."),
    },
    "mmd_note": {
        "name": "musicmeeting.directory",
        "scope": "used in NACC-panel servicing.",
        "detail": None,
        "detail_note": "verify live.",
    },
}


# ── DELIVERY_VS_OUTREACH_DOCTRINE (ADDENDUM) — the line Solo never blurs ────────
DELIVERY_VS_OUTREACH_DOCTRINE = {
    "rule": ("Servicing platforms DELIVER the music; they guarantee nothing and do "
             "no follow-up. The tracker / promoter relationship layer — pitching, "
             "add-date follow-up, weekly MD calls — is exactly THIS department's "
             "outreach role. Solo recommends the delivery platform AND runs the "
             "relationship rail; he never claims delivery = airplay."),
}


# ── SATELLITE_AND_PUBLIC (ADDENDUM) ────────────────────────────────────────────
SATELLITE_AND_PUBLIC = {
    "siriusxm": {
        "note": ("satellite; Canadian channels exist; CanCon is applied in aggregate "
                 "across the package; serviced via DMDS."),
        "detail": None,
        "detail_note": "verify live.",
    },
    "cbc": {
        "note": ("50% CanCon quota (CRTC); CBC Music / Radio is a major Canadian "
                 "discovery channel for domestic artists."),
        "submission_mechanism": None,
        "submission_note": "verify live.",
    },
}


# ── OUT_OF_SCOPE — the org boundary, encoded. Solo defines NO curator tools. ────
OUT_OF_SCOPE = {
    "playlist_curator_outreach": {
        "owner": "management department (Marcus)",
        "reason": ("org boundary — Tommy-decided. Playlist-CURATOR outreach is run by "
                   "management; Solo covers radio + DSP editorial only and defines no "
                   "curator tools."),
    },
}


# ── HONESTY_RULES — the guardrails, with stable ids ─────────────────────────────
HONESTY_RULES = (
    {
        "id": "never_assert_mapl",
        "statement": ("Never assert or compute a song's CanCon / MAPL status — "
                      "misdeclaration risks the STATION's licence. Only the artist's "
                      "declared letters pass through, or [NEEDS:mapl_declaration]."),
        "allowed": "Passing through the artist's declared MAPL letters.",
        "forbidden": "Deciding or computing whether a song 'is' CanCon / MAPL.",
    },
    {
        "id": "no_placement_guarantees",
        "statement": ("A pitch — radio or DSP editorial — is CONSIDERATION, never a "
                      "placement. No add, spin, or playlist slot is ever promised."),
        "allowed": "Framing a pitch as putting the track in front of the gatekeeper.",
        "forbidden": "Promising or implying a guaranteed add, spin, or placement.",
    },
    {
        "id": "costs_and_panel_sizes_verify_live",
        "statement": ("Panel sizes, tier costs, and chart mechanics are current "
                      "conventions — surfaced with a verify-live reminder, never as "
                      "fixed facts."),
        "allowed": "Stating a panel size or cost as an approximate, verify-live figure.",
        "forbidden": "Quoting a panel size or cost as an exact, guaranteed number.",
    },
    {
        "id": "platform_costs_and_processes_verify_live",
        "statement": ("Named platforms (Yangaroo/DMDS, Play MPE, earshot, DMDS, CBC) "
                      "are real and current as of July 2026; prices, packages, and "
                      "submission processes change — always verify live. Naming a "
                      "platform is never an endorsement of a specific paid package."),
        "allowed": "Naming a platform as the current delivery route with verify-live.",
        "forbidden": "Quoting a platform's price/package or endorsing a paid tier.",
    },
    {
        "id": "facts_supplied_or_marked",
        "statement": ("Any fact a campaign depends on — the track, the declared MAPL "
                      "letters, the release date — is the artist's supplied input or an "
                      "explicit gap; nothing is fabricated."),
        "allowed": "Marking an unknown as a [NEEDS:] gap or verify live.",
        "forbidden": "Filling an unknown declaration, date, or cost with an invented value.",
    },
)
