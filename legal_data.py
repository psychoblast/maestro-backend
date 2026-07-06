"""
PLMKR Lex-Cipher — structured legal data (Lex's real knowledge base).

Unit 1 (data-only): the researched legal-education map, encoded as structured
records, replacing the old hand-invented ``_CLAUSE_LIBRARY`` / ``_RED_FLAGS``
lists that lived inline in ``lex_cipher_service.py``.
Source of truth: LEX_LEGAL_MAP_v1 (researched in chat July 6 2026, web-sourced:
US and Canadian copyright/termination doctrine, moral-rights regimes across
US/Canada/UK/Europe, music-industry agreement structures, and standard
red-flag/negotiation education for independent artists).

THE ONE RULE ABOVE ALL (encoded here as data, enforced in the service + tests):
Lex NEVER gives legal advice and NEVER produces a signable contract. Every record
in this module is EDUCATION for the artist to take to THEIR OWN LAWYER. Nothing
here asserts that any clause, deal, or contract is safe, fine, or standard to
sign. Red flags say "ask counsel about this here", never "walk away" or "accept".
Jurisdiction-specific content lives ONLY in JURISDICTION_DIVERGENCE and every
entry there ends with the counsel string — the service withholds it unless the
artist supplies a jurisdiction.

WHAT THIS MODULE IS (and is NOT):
  - DATA ONLY. No functions, no filtering logic, no I/O, no network, no secrets.
    ``lex_cipher_service`` imports these constants and does all the lookup /
    scaffold assembly. No legal reasoning is encoded as logic here.
  - Every record is a plain, JSON-serializable dict so ``dict(r)`` in the service
    flows all fields through untouched.

HARD RULES honored here:
  - ZERO currency amounts anywhere. No figures, no symbols — not for advances,
    not for commissions, not even for lawyer fees (encoded as "a few hours of
    attorney time", never a number). Mechanisms over numbers throughout.
  - NO percentage is asserted as a "standard". Where proportion matters it is
    described as a mechanism ("net not gross", "commission stacks across the
    team"), never a number an artist could mistake for a safe position.
  - Unknowns are ``None`` + a "verify live" note, never a guess. Free text is a
    NOTE for counsel, never a rule the artist can act on unadvised.
  - Every JURISDICTION_DIVERGENCE entry ends with "confirm with local counsel".
  - BOUNDARIES routes drafting to the owning department: Lex explains what a
    document IS; building it lives elsewhere.

SCHEMA:
  AGREEMENT_TYPES[key] -> key, display_name, parties, purpose, core_questions,
    typical_key_clauses, owning_department (None or a cross-ref agent id)
  CLAUSE_GLOSSARY[term] -> term, mechanism, why_it_matters, ask_counsel
  RED_FLAG_DOCTRINE[flag] -> flag, pattern, why_it_matters, counsel_levers
  JURISDICTION_DIVERGENCE[topic] -> topic, mechanism, note (ends with the
    counsel string)
  LAWYER_DOCTRINE -> list of counsel-engagement principles
  OUT_OF_SCOPE[key] -> what, owning_department, lex_role
"""

# ── Standing framing strings (data, not logic) ────────────────────────────────
# Every scaffold header and section heading the service builds carries this.
FOR_YOUR_LAWYER = "FOR YOUR LAWYER"

# The counsel string every jurisdiction-divergence note must end with.
CONFIRM_WITH_LOCAL_COUNSEL = "confirm with local counsel"

# What Lex is and is not — surfaced verbatim by the service so no output can be
# mistaken for advice or a signable document.
LEX_DOCTRINE = {
    "not_legal_advice": (
        "Lex prepares education and organized questions FOR YOUR LAWYER. Nothing "
        "Lex produces is legal advice, and nothing Lex produces is a contract you "
        "can sign. Everything here is preparation material for independent counsel."
    ),
    "never_signable": (
        "Lex never drafts a signable agreement and never assures you that a "
        "contract is safe, sound, or acceptable to put your name to. A scaffold is "
        "a briefing document you hand to your own lawyer — not an instrument."
    ),
    "jurisdiction_gated": (
        "Anything that depends on where you live or where the deal is governed is "
        "withheld until you supply a jurisdiction, and even then it ends by telling "
        "you to " + CONFIRM_WITH_LOCAL_COUNSEL + "."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# AGREEMENT_TYPES — what each music agreement IS, so the artist walks into
# counsel already understanding the document. Education, never advice.
# ═══════════════════════════════════════════════════════════════════════════════
AGREEMENT_TYPES = {
    "band_partnership": {
        "key": "band_partnership",
        "display_name": "Band Partnership Agreement",
        "parties": "the members of a band or group, with each other",
        "purpose": (
            "Sets out, in writing, how a group shares ownership, income, decisions, "
            "and — critically — what happens when someone leaves or the band splits."
        ),
        "core_questions": [
            "Who owns the band name if the band breaks up?",
            "How are songwriting splits decided versus performance/recording income?",
            "How are decisions made, and what needs a unanimous vote?",
            "What happens to a departing member's share of past and future income?",
        ],
        "typical_key_clauses": [
            "name ownership and control on departure or dissolution",
            "income splits (writing vs recording vs live vs merch)",
            "decision-making and voting thresholds",
            "leaver / buy-out mechanics",
        ],
        "owning_department": None,
    },
    "recording_contract": {
        "key": "recording_contract",
        "display_name": "Recording Contract (Record Deal)",
        "parties": "a recording artist and a record label",
        "purpose": (
            "The label funds and/or releases recordings; in exchange it typically "
            "takes ownership of the master recordings and a share of income. Trades "
            "control for backing — see the record-vs-distribution doctrine."
        ),
        "core_questions": [
            "Who owns the master recordings, and does ownership ever revert to me?",
            "What is recoupable against my royalties before I see income?",
            "How many albums am I committed to, and who controls the options?",
            "What are my rights to audit the label's accounting?",
        ],
        "typical_key_clauses": [
            "grant / ownership of masters",
            "advance and recoupment",
            "term and option periods",
            "royalty basis and audit rights",
            "reversion",
        ],
        "owning_department": None,
    },
    "distribution_deal": {
        "key": "distribution_deal",
        "display_name": "Distribution Deal",
        "parties": "an artist (or their label) and a distributor",
        "purpose": (
            "The distributor gets recordings onto stores and streaming platforms and "
            "collects income for a fee — WITHOUT (in the typical case) taking "
            "ownership of the masters. Distribution moves the music; it does not, by "
            "itself, buy the music."
        ),
        "core_questions": [
            "Do I keep ownership of my masters under this deal?",
            "How does the distributor get paid, and out of what?",
            "How long is the term, and how do I exit and take my catalog?",
            "Is anything here made recoupable, and against what income?",
        ],
        "typical_key_clauses": [
            "grant limited to distribution (not ownership)",
            "distribution fee mechanism",
            "term and exit / catalog take-down",
            "accounting and audit rights",
        ],
        "owning_department": None,
    },
    "publishing_agreement": {
        "key": "publishing_agreement",
        "display_name": "Publishing Agreement",
        "parties": "a songwriter and a music publisher",
        "purpose": (
            "Covers the songs (compositions), not the recordings. A publisher "
            "administers, exploits, and collects on the writer's compositions. Note "
            "the co-publishing vs full-publishing distinction: co-publishing leaves "
            "the writer owning a share of the publishing; a full transfer does not."
        ),
        "core_questions": [
            "Am I keeping a share of my publishing (co-pub) or transferring it all?",
            "Which of my songs are captured — past catalog, or only new writing?",
            "When do my copyrights revert to me?",
            "What is recoupable before I am paid?",
        ],
        "typical_key_clauses": [
            "co-publishing vs full assignment of copyright",
            "scope (catalog captured vs new works)",
            "advance and recoupment",
            "reversion",
            "controlled composition (cross-ref)",
        ],
        "owning_department": "ink-and-air",
    },
    "management_contract": {
        "key": "management_contract",
        "display_name": "Management Contract",
        "parties": "an artist and a personal manager",
        "purpose": (
            "The manager guides the artist's career and, in exchange, commissions a "
            "share of the artist's income. The big questions are what income is "
            "commissioned and for how long after the manager is gone."
        ),
        "core_questions": [
            "What income is commissionable — and is anything carved out?",
            "How long does the manager keep commissioning after we part (post-term / sunset)?",
            "How and when can either side end this, and on what notice?",
            "Does the manager have any conflict of interest in deals they bring me?",
        ],
        "typical_key_clauses": [
            "commission scope and carve-outs",
            "term and post-term (sunset) commission",
            "key-person / termination",
            "conflict of interest",
        ],
        "owning_department": None,
    },
    "booking_agent_agreement": {
        "key": "booking_agent_agreement",
        "display_name": "Booking Agent Agreement",
        "parties": "an artist and a booking / live agent",
        "purpose": (
            "The agent secures live performances and commissions live income. Sits "
            "alongside management — both can commission, which is where team-wide "
            "commission math matters."
        ),
        "core_questions": [
            "What live income is commissioned, and is it gross or net?",
            "Is this exclusive, and over what territory?",
            "How does commission interact with what my manager already takes?",
            "How do I exit, and what happens to shows already booked?",
        ],
        "typical_key_clauses": [
            "commission scope (live income)",
            "exclusivity and territory",
            "term and exit",
            "treatment of pre-booked dates",
        ],
        "owning_department": "venue-hawk",
    },
    "producer_agreement": {
        "key": "producer_agreement",
        "display_name": "Producer Agreement",
        "parties": "an artist and a record producer",
        "purpose": (
            "Sets what the producer is paid and — often overlooked — what the "
            "producer OWNS or shares in the master and the underlying composition."
        ),
        "core_questions": [
            "Does the producer get a share of the master, the song, or both?",
            "Is the producer's fee an advance recoupable against their points?",
            "Who owns the session files and stems?",
            "Is there a producer royalty, and how is it accounted?",
        ],
        "typical_key_clauses": [
            "producer fee / advance",
            "producer points (master royalty)",
            "any songwriting split",
            "ownership of stems / session materials",
        ],
        "owning_department": None,
    },
    "sync_license": {
        "key": "sync_license",
        "display_name": "Sync License",
        "parties": "a rights holder (composition and/or master) and a media producer",
        "purpose": (
            "Permits music to be synchronized to picture (film, TV, ad, game). A "
            "license — not a sale — so scope and duration are everything."
        ),
        "core_questions": [
            "Exactly what use is licensed — which production, which media, how long?",
            "Is it exclusive, and does it lock up other opportunities?",
            "Am I licensing the composition, the master, or both?",
            "Does anything here assign rights rather than license them?",
        ],
        "typical_key_clauses": [
            "scope of use (production / media / term)",
            "exclusivity",
            "composition vs master rights",
            "grant is a license, not an assignment",
        ],
        "owning_department": None,
    },
    "three_sixty_deal": {
        "key": "three_sixty_deal",
        "display_name": "360 Deal",
        "parties": "an artist and a label (or label-services company)",
        "purpose": (
            "A deal in which the company participates in income streams BEYOND "
            "recordings — touring, merch, brand, publishing. The central question is "
            "whether the company actively works those streams or merely takes from them."
        ),
        "core_questions": [
            "Which income streams does the company participate in?",
            "For each stream, does the company actively work it or just passively take a share?",
            "Are any streams carved out entirely?",
            "Is the participation on gross or on net, and is there any double-dipping?",
        ],
        "typical_key_clauses": [
            "which streams are captured",
            "active-vs-passive participation per stream",
            "carve-outs",
            "gross vs net basis",
        ],
        "owning_department": None,
    },
    "work_for_hire_side_artist_session": {
        "key": "work_for_hire_side_artist_session",
        "display_name": "Work-for-Hire / Side-Artist / Session Agreement",
        "parties": "a hiring party and a session or featured performer",
        "purpose": (
            "Engages a performer for a session or feature. The pivotal question is "
            "whether the performer's contribution is treated as work-for-hire (US "
            "doctrine) and what rights, if any, the performer keeps. Jurisdiction "
            "changes what 'work for hire' even means."
        ),
        "core_questions": [
            "Am I assigning or licensing my contribution, and is 'work for hire' being invoked?",
            "Do I keep any credit, royalty, or reuse rights?",
            "Does the work-for-hire language even have legal effect in my jurisdiction?",
            "Is there a fallback assignment if work-for-hire does not apply?",
        ],
        "typical_key_clauses": [
            "work-for-hire designation",
            "fallback assignment language",
            "credit and any royalty",
            "reuse / re-record scope",
        ],
        "owning_department": None,
    },
    "beat_license": {
        "key": "beat_license",
        "display_name": "Beat License",
        "parties": "a producer / beatmaker and a recording artist",
        "purpose": (
            "Licenses an instrumental for a recording. Turns on the exclusive vs "
            "non-exclusive distinction: a non-exclusive lease leaves the beat "
            "available to others; an exclusive removes it from sale but rarely "
            "transfers full ownership unless it says so."
        ),
        "core_questions": [
            "Is this exclusive or non-exclusive — can the beat still be sold to others?",
            "What uses, formats, and distribution counts are permitted?",
            "Does the license convert to, or stop short of, ownership?",
            "What are the credit and split obligations to the producer?",
        ],
        "typical_key_clauses": [
            "exclusive vs non-exclusive grant",
            "permitted uses / distribution limits",
            "whether ownership transfers",
            "producer credit and split",
        ],
        "owning_department": None,
    },
    "letter_of_direction": {
        "key": "letter_of_direction",
        "display_name": "Letter of Direction (LOD)",
        "parties": "a payee instructing a payor to route income to a third party",
        "purpose": (
            "A standing instruction telling whoever pays out income to send a defined "
            "share directly to someone else (a collaborator, producer, or lender). "
            "Lex explains what an LOD does; drafting the actual LOD is ledger-lock's job."
        ),
        "core_questions": [
            "Exactly what share of what income is being redirected, and to whom?",
            "Is it revocable, and under what conditions?",
            "Which payor(s) does it bind, and have they acknowledged it?",
        ],
        "typical_key_clauses": [
            "defined share and income source",
            "payee and payor identification",
            "revocability",
        ],
        "owning_department": "ledger-lock",
    },
    "release_agreement": {
        "key": "release_agreement",
        "display_name": "Release Agreement (Mutual Release)",
        "parties": "two parties ending an existing contract between them",
        "purpose": (
            "Cleanly ends a prior contract and, ideally mutually, releases each side "
            "from further claims under it. The question is what is actually being "
            "released and what survives."
        ),
        "core_questions": [
            "Which prior agreement is being ended, and does the release run both ways?",
            "What obligations or rights survive the release (e.g. accrued royalties)?",
            "Are there any lingering restrictions after the release?",
        ],
        "typical_key_clauses": [
            "identification of the released agreement",
            "mutual vs one-way release",
            "survival of accrued rights",
        ],
        "owning_department": None,
    },
    "minor_parental_consent_guarantee": {
        "key": "minor_parental_consent_guarantee",
        "display_name": "Minor's Parental Consent / Guarantee",
        "parties": "a minor artist, their parent/guardian, and a counterparty",
        "purpose": (
            "Because a minor generally cannot be bound the way an adult can, deals "
            "with minors use consent and guarantee mechanisms whose validity varies "
            "sharply by jurisdiction. Always requires local counsel and a jurisdiction."
        ),
        "core_questions": [
            "Does this jurisdiction require court approval for a minor's contract?",
            "What does the parental guarantee actually obligate the parent to?",
            "Can the minor disaffirm the contract, and until when?",
        ],
        "typical_key_clauses": [
            "parental consent / guarantee",
            "jurisdiction-specific approval mechanism",
            "disaffirmance window",
        ],
        "owning_department": None,
    },
    "nda": {
        "key": "nda",
        "display_name": "Non-Disclosure Agreement (NDA)",
        "parties": "two (or more) parties sharing confidential information",
        "purpose": (
            "Protects confidential information shared while exploring or doing a deal. "
            "Turns on what counts as confidential, how long the duty lasts, and "
            "whether it quietly restricts more than confidentiality."
        ),
        "core_questions": [
            "What exactly is defined as confidential, and what is carved out?",
            "How long does the confidentiality obligation last?",
            "Does it sneak in non-compete or IP-assignment terms beyond confidentiality?",
        ],
        "typical_key_clauses": [
            "definition of confidential information",
            "duration of the obligation",
            "carve-outs (public / independently known)",
        ],
        "owning_department": None,
    },
}

# Doctrine: the distinction artists most often miss.
AGREEMENT_DOCTRINE = {
    "record_deal_vs_distribution_deal": (
        "The core difference between a record deal and a distribution deal is "
        "ownership and control. A record deal typically trades master ownership (and "
        "control) in exchange for the label's backing; a distribution deal typically "
        "moves your music to market for a fee WITHOUT taking ownership of your "
        "masters. Which one you are looking at changes almost every other question."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# CLAUSE_GLOSSARY — mechanism definitions. What a term DOES, why it matters, and
# what an artist typically brings to counsel about it. No number is a "standard".
# ═══════════════════════════════════════════════════════════════════════════════
CLAUSE_GLOSSARY = {
    "assignment_vs_license": {
        "term": "assignment_vs_license",
        "mechanism": (
            "An assignment permanently transfers ownership of a right; a license "
            "grants permission to use it for a defined scope and time, after which it "
            "expires and the right stays with you."
        ),
        "why_it_matters": (
            "This is the single most valuable distinction in any music contract: an "
            "assignment can be forever, a license comes back. Language that says "
            "'assign' where you expected 'license' changes who owns your work."
        ),
        "ask_counsel": (
            "Is this clause an assignment or a license — and if assignment, is there "
            "any path for the right to return to me?"
        ),
    },
    "advance": {
        "term": "advance",
        "mechanism": (
            "An advance is money paid up front that is a LOAN against your future "
            "income — it is recovered out of what you earn before you see royalties."
        ),
        "why_it_matters": (
            "An advance is not a gift or a bonus; treating it as free money hides that "
            "you are paying it back out of your own earnings first."
        ),
        "ask_counsel": (
            "What income is this advance recovered from, and could I owe it back if "
            "the project underperforms?"
        ),
    },
    "recoupment_scope": {
        "term": "recoupment_scope",
        "mechanism": (
            "Recoupment is the company recovering its costs out of your income before "
            "paying you. The scope is WHICH costs are recoupable — recording costs are "
            "typical, but watch for marketing, video, and tour support being made "
            "recoupable too."
        ),
        "why_it_matters": (
            "The wider the recoupment scope, the longer before you are paid. Costs you "
            "did not expect to repay can quietly be added to the pile."
        ),
        "ask_counsel": (
            "Exactly which categories of cost are recoupable here — and are marketing, "
            "video, or tour support among them?"
        ),
    },
    "cross_collateralization": {
        "term": "cross_collateralization",
        "mechanism": (
            "Cross-collateralization lumps separate projects (or agreements) together "
            "for accounting, so a success on one pays down debts owed on another "
            "before you are paid."
        ),
        "why_it_matters": (
            "A hit record can be used to first pay off an earlier failed project, so "
            "you see nothing from the hit until the older debt is cleared."
        ),
        "ask_counsel": (
            "Are my projects or agreements cross-collateralized, and can each be "
            "accounted for on its own instead?"
        ),
    },
    "term_and_options": {
        "term": "term_and_options",
        "mechanism": (
            "The term is how long you are committed; options are the company's right "
            "to extend it. One-sided options are dropped on failure and locked in on "
            "success — the company keeps you when you win and releases you when you "
            "lose. Mutual options and performance minimums are the counter-mechanisms."
        ),
        "why_it_matters": (
            "One-sided options mean the upside of your success accrues to the company "
            "while the risk of failure stays with you."
        ),
        "ask_counsel": (
            "Who controls the options — and can we add mutual options or performance "
            "minimums the company must meet to renew?"
        ),
    },
    "exclusivity_and_carveouts": {
        "term": "exclusivity_and_carveouts",
        "mechanism": (
            "Exclusivity binds you to work only through this counterparty; carve-outs "
            "are the exceptions — side projects, pre-existing recordings, and the "
            "duration of any re-record restriction."
        ),
        "why_it_matters": (
            "Without carve-outs, exclusivity can sweep in work you never meant to "
            "commit and freeze you from re-recording your own catalog for a long time."
        ),
        "ask_counsel": (
            "What carve-outs exist for side projects and prior recordings, and how "
            "long does any re-record restriction last?"
        ),
    },
    "reversion": {
        "term": "reversion",
        "mechanism": (
            "A reversion returns rights to you after a set period or on the "
            "counterparty's failure to release or exploit the work."
        ),
        "why_it_matters": (
            "Without a reversion, rights you granted may never come back even if the "
            "counterparty does nothing with them."
        ),
        "ask_counsel": (
            "Is there a reversion here — and if not, can we add one triggered by time "
            "or by failure to release? (Always worth asking for.)"
        ),
    },
    "audit_rights": {
        "term": "audit_rights",
        "mechanism": (
            "Audit rights let you (or your accountant) inspect the counterparty's "
            "books to check that what you were paid matches what you were owed."
        ),
        "why_it_matters": (
            "Without audit rights you have to take the accounting on trust, with no "
            "mechanism to verify or challenge it."
        ),
        "ask_counsel": (
            "Do I have the right to audit the accounting, and are the notice and cost "
            "conditions on that right reasonable?"
        ),
    },
    "discretion_language": {
        "term": "discretion_language",
        "mechanism": (
            "Phrases like 'commercially satisfactory' or 'in its sole discretion' give "
            "the counterparty a subjective power to accept, reject, or decide — a "
            "rejection power dressed as a standard."
        ),
        "why_it_matters": (
            "Discretion language can let the counterparty refuse your work or withhold "
            "action for reasons you cannot challenge."
        ),
        "ask_counsel": (
            "Can we replace subjective 'satisfactory' / 'sole discretion' language "
            "with an objective standard or a defined process?"
        ),
    },
    "assignment_of_contract": {
        "term": "assignment_of_contract",
        "mechanism": (
            "An assignment-of-contract clause lets the counterparty sell or transfer "
            "the whole agreement — and you along with it — to another company, "
            "sometimes without your consent."
        ),
        "why_it_matters": (
            "You could end up bound to a company you never chose and would never have "
            "signed with."
        ),
        "ask_counsel": (
            "Can the counterparty assign this contract without my consent — and can we "
            "require my written consent to any transfer?"
        ),
    },
    "controlled_composition": {
        "term": "controlled_composition",
        "mechanism": (
            "A controlled-composition clause changes how the songs you write and "
            "control are paid on your own recordings, typically reducing the "
            "mechanical income on compositions you 'control'."
        ),
        "why_it_matters": (
            "It quietly ties your songwriting income to your recording deal, so the "
            "two have to be read together — this is where publishing and royalty "
            "administration overlap."
        ),
        "ask_counsel": (
            "How does this controlled-composition clause affect my mechanical income, "
            "and how does it interact with my publishing?  (Split-sheet mechanics sit "
            "with ink-and-air; royalty registration and LODs sit with ledger-lock.)"
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# RED_FLAG_DOCTRINE — patterns to spot and the QUESTIONS to raise with counsel.
# Levers are framed as questions, never as positions asserted as safe.
# ═══════════════════════════════════════════════════════════════════════════════
RED_FLAG_DOCTRINE = {
    "perpetual_master_ownership": {
        "flag": "perpetual_master_ownership",
        "pattern": (
            "Language granting rights 'in perpetuity' and 'throughout the universe' — "
            "ownership that never ends and never comes back."
        ),
        "why_it_matters": (
            "Perpetual ownership means your masters may never revert to you, in any "
            "territory, for the life of the copyright."
        ),
        "counsel_levers": [
            "Can the grant be made for a defined term instead of in perpetuity?",
            "Can we add a reversion after a period or on failure to exploit?",
            "Can the territory be narrowed from 'the universe' to something defined?",
        ],
    },
    "unsupported_360": {
        "flag": "unsupported_360",
        "pattern": (
            "A 360 clause taking a share of income streams (touring, merch, brand) "
            "that the company does not actually support or work."
        ),
        "why_it_matters": (
            "You end up paying the company out of income it did nothing to build."
        ),
        "counsel_levers": [
            "Is the participation tied to streams the company actively works, not passively takes?",
            "Can unsupported streams be carved out entirely?",
            "Is participation on net rather than gross?",
            "Is there anti-double-dipping language, so they cannot charge for a service AND commission it?",
        ],
    },
    "commission_stacking": {
        "flag": "commission_stacking",
        "pattern": (
            "A 360 company, a manager, and an agent all commissioning the same income "
            "at once — the takes stack on top of each other."
        ),
        "why_it_matters": (
            "Stacked commissions across the whole team can leave the artist with "
            "roughly half of their own income before other costs — the individual "
            "numbers look fine until you add them together."
        ),
        "counsel_levers": [
            "Have we run the whole-team math — every commission stacked on the same income at once?",
            "Are there streams where more than one party is commissioning the same money?",
            "Can overlapping commissions be reduced or carved out where they double up?",
        ],
    },
    "work_for_hire_on_own_artistry": {
        "flag": "work_for_hire_on_own_artistry",
        "pattern": (
            "Work-for-hire language applied to an artist's OWN creative output, "
            "treating their artistry as if it were made-for-hire employment work."
        ),
        "why_it_matters": (
            "Work-for-hire can strip you of authorship of your own art and of the "
            "termination/reversion rights that authorship carries."
        ),
        "counsel_levers": [
            "Is my own artistry really being cast as work-for-hire, and is that even valid here?",
            "Can this be a license or a limited assignment with reversion instead?",
            "What termination or reversion rights am I giving up by accepting work-for-hire?",
        ],
    },
    "missing_audit_rights": {
        "flag": "missing_audit_rights",
        "pattern": "No clause giving you any right to inspect the counterparty's accounting.",
        "why_it_matters": (
            "You would have to trust the payments with no way to verify or challenge them."
        ),
        "counsel_levers": [
            "Can we add an audit right with reasonable notice and cost terms?",
            "How long do I have to raise a discrepancy before it is deemed accepted?",
        ],
    },
    "long_rerecord_restrictions": {
        "flag": "long_rerecord_restrictions",
        "pattern": (
            "A restriction barring you from re-recording your own compositions for a "
            "long period after the term."
        ),
        "why_it_matters": (
            "A long re-record restriction can keep you from re-recording your catalog "
            "well after you have otherwise moved on."
        ),
        "counsel_levers": [
            "How long does the re-record restriction run, and can it be shortened?",
            "Which specific works does it cover, and can the scope be narrowed?",
        ],
    },
    "automatic_renewal": {
        "flag": "automatic_renewal",
        "pattern": "A term that automatically renews unless you take action to opt out.",
        "why_it_matters": (
            "You can be locked into another term simply by missing a notice window."
        ),
        "counsel_levers": [
            "Can renewal require my affirmative opt-in rather than auto-renew?",
            "If it stays auto-renew, is the opt-out notice window workable?",
        ],
    },
    "cross_collateralization_broad": {
        "flag": "cross_collateralization_broad",
        "pattern": (
            "Broad cross-collateralization lumping unrelated projects or agreements "
            "together for accounting."
        ),
        "why_it_matters": (
            "A success on one project can be swallowed paying down debts on another "
            "before you are paid anything."
        ),
        "counsel_levers": [
            "Can each project or agreement be accounted for on its own?",
            "If some cross-collateralization stays, can its scope be narrowed?",
        ],
    },
    "sign_now_pressure": {
        "flag": "sign_now_pressure",
        "pattern": (
            "Pressure to sign immediately — 'this offer expires', 'everyone else has "
            "signed', 'no time for a lawyer'."
        ),
        "why_it_matters": (
            "Urgency to sign is itself a red flag: a genuinely good deal survives a "
            "two-week review by your own lawyer. Pressure exists to get you past the "
            "review."
        ),
        "counsel_levers": [
            "Will the counterparty hold the deal open for a proper independent review?",
            "What specifically changes if I take two weeks to have counsel read it?",
        ],
    },
    "conflicted_counsel": {
        "flag": "conflicted_counsel",
        "pattern": (
            "The other side offering, recommending, or paying for 'your' lawyer."
        ),
        "why_it_matters": (
            "A lawyer the other side recommends may effectively be the other side's "
            "lawyer; you would not have truly independent advice."
        ),
        "counsel_levers": [
            "Is my lawyer genuinely independent of, and not referred by, the other side?",
            "Have I run a conflict check before relying on any recommended counsel?",
        ],
    },
}

# Doctrine notes on how to READ red flags — themselves education, not advice.
RED_FLAG_DOCTRINE_NOTES = {
    "negotiate_not_walk": (
        "A red flag means 'negotiate here', not automatically 'walk away'. It marks a "
        "place to bring questions to counsel — most are negotiable."
    ),
    "refusal_is_its_own_flag": (
        "A counterparty's flat refusal to negotiate any of these is itself a red flag."
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# JURISDICTION_DIVERGENCE — mechanisms only, jurisdiction-gated by the service.
# EVERY note ends with the counsel string.
# ═══════════════════════════════════════════════════════════════════════════════
JURISDICTION_DIVERGENCE = {
    "work_for_hire": {
        "topic": "work_for_hire",
        "mechanism": (
            "Work-for-hire is a US copyright doctrine that is valid only through "
            "actual employment or one of the specific commissioned categories with "
            "explicit written language. The phrase has no legal significance in "
            "Canadian law — there the creator is always the first author, and a "
            "contractor's copyright must be explicitly assigned to pass. This is why "
            "US contracts use a belt-and-suspenders pattern ('if this is not a work "
            "made for hire, you hereby assign it'): a pure work-for-hire, unlike an "
            "assignment, blocks the US ~35-year termination right, so the company "
            "wants work-for-hire first and assignment only as a fallback."
        ),
        "note": (
            "Whether 'work for hire' has any effect on your contribution depends "
            "entirely on jurisdiction and the exact facts of the engagement — "
            + CONFIRM_WITH_LOCAL_COUNSEL + "."
        ),
    },
    "statutory_termination": {
        "topic": "statutory_termination",
        "mechanism": (
            "The US and Canada return rights to creators by different mechanisms. In "
            "the US, grants (that are not valid works made for hire) can be terminable "
            "by the author roughly 35 years after execution, independent of what the "
            "contract says. In Canada, an assignment ends 25 years after the author's "
            "death, with the reverted rights passing to the author's estate."
        ),
        "note": (
            "The existence, timing, and formalities of any termination or reversion "
            "right turn on jurisdiction and precise dates — " + CONFIRM_WITH_LOCAL_COUNSEL + "."
        ),
    },
    "moral_rights": {
        "topic": "moral_rights",
        "mechanism": (
            "Moral rights (attribution and integrity) vary sharply by country. Canada "
            "recognizes them for all works; they cannot be assigned but CAN be "
            "explicitly waived (a common ask is to waive integrity while keeping "
            "attribution). The US recognizes moral rights for visual art only, which "
            "is why US music contracts still contain moral-rights waivers at all. The "
            "UK's moral rights are narrower than much of Europe's and do NOT apply to "
            "sound recordings — only to the underlying music and lyrics. Parts of "
            "Europe treat moral rights as perpetual and unwaivable."
        ),
        "note": (
            "Which moral rights exist, and whether they can be waived, depends on the "
            "governing jurisdiction and the type of work — " + CONFIRM_WITH_LOCAL_COUNSEL + "."
        ),
    },
    "minors": {
        "topic": "minors",
        "mechanism": (
            "How a minor can be bound — the consent, guarantee, court-approval, and "
            "disaffirmance mechanisms — varies sharply between jurisdictions, and a "
            "mechanism valid in one place may be void in another."
        ),
        "note": (
            "Any agreement involving a minor is [NEEDS:jurisdiction] and must go to "
            "counsel in that jurisdiction — " + CONFIRM_WITH_LOCAL_COUNSEL + "."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# LAWYER_DOCTRINE — how to engage counsel. Education about getting advice, never
# advice itself. No fee figures — only "a few hours of attorney time".
# ═══════════════════════════════════════════════════════════════════════════════
LAWYER_DOCTRINE = [
    {
        "id": "independent_counsel_only",
        "principle": (
            "Use your OWN independent lawyer, and run a conflict check before relying "
            "on anyone referred to you — especially anyone the other side recommends."
        ),
    },
    {
        "id": "read_the_actual_contract",
        "principle": (
            "Have counsel read the actual contract, not a summary of it. The terms "
            "that bind you live in the document, not in the pitch."
        ),
    },
    {
        "id": "redlines_in_writing",
        "principle": (
            "Keep redlines and changes in writing so the negotiation history is "
            "tracked and nothing agreed verbally is quietly lost."
        ),
    },
    {
        "id": "never_sign_under_pressure",
        "principle": (
            "Never sign under time pressure. A good deal survives a proper review; "
            "the pressure to skip one is a reason to slow down, not speed up."
        ),
    },
    {
        "id": "low_cost_routes_exist",
        "principle": (
            "Low-cost routes to review exist — for example volunteer arts-lawyer "
            "organizations — and asking the other side to cover a review that costs "
            "them only a few hours of attorney time is a legitimate request."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# OUT_OF_SCOPE — Lex explains what these documents ARE; DRAFTING lives with the
# owning department. The boundary is doctrine, encoded as data.
# ═══════════════════════════════════════════════════════════════════════════════
OUT_OF_SCOPE = {
    "split_sheet": {
        "key": "split_sheet",
        "what": "building or validating a songwriting split sheet",
        "owning_department": "ink-and-air",
        "lex_role": (
            "Lex can explain what a split sheet is and why it matters; building and "
            "validating one is ink-and-air's job."
        ),
    },
    "royalty_registration": {
        "key": "royalty_registration",
        "what": "registering works with royalty collection societies",
        "owning_department": "ledger-lock",
        "lex_role": (
            "Lex can explain what royalty registration accomplishes; performing the "
            "registration is ledger-lock's job."
        ),
    },
    "lod_drafting": {
        "key": "lod_drafting",
        "what": "drafting a Letter of Direction",
        "owning_department": "ledger-lock",
        "lex_role": (
            "Lex can explain what an LOD does; drafting the actual LOD is "
            "ledger-lock's job."
        ),
    },
    "booking_deal_memo": {
        "key": "booking_deal_memo",
        "what": "preparing a booking / live deal memo",
        "owning_department": "venue-hawk",
        "lex_role": (
            "Lex can explain what a booking deal memo covers; preparing one is "
            "venue-hawk's job."
        ),
    },
    "grant_application": {
        "key": "grant_application",
        "what": "preparing or submitting a grant application",
        "owning_department": "fund-phantom",
        "lex_role": (
            "Lex can explain the legal terms attached to a grant; preparing the grant "
            "application itself is fund-phantom's job."
        ),
    },
}
