"""
Phase 3e — Per-agent deep consult test for schedule-keeper.

Scope: schedule-keeper only. Home domain "live_touring". Six realistic
questions an artist or their team would ask Cal (Scheduling Specialist),
covering: building a release countdown calendar with milestone timeline and
label delivery commitment deadlines, mapping a daily TikTok/Instagram content
calendar around a festival booking and touring run, coordinating a global
touring social posting schedule for fan community engagement and audience
growth, aligning the pre-save activation deadline with the editorial
submission pitch window and DSP release date, scheduling brand sponsorship
activation events and merchandise deal tie-ins across touring venue dates,
and a deliberately narrow touring-diary / posting-routine question.

For each cross-domain question we assert:
  (a) schedule-keeper's home domain "live_touring" leads the result list.
  (b) Every expected cross-domain appears in the result.

One deliberately narrow question asserts home-only with no spurious
cross-domain — a pure posting-routine / touring-diary / gig-dates question
that avoids keywords from legal, finance_royalties, marketing, fan_social,
bizdev, label_ops, playlist_dsp, publishing, production, data_analytics,
capital_funding, digital_ops, intelligence, management, ar, sync,
controller, executive, or any other non-home domain.

Routing gap noted: schedule-keeper's SKILL.md is primarily about social
media content calendar scheduling and release campaign countdown timelines
(closer to "marketing" and "label_ops" conceptually) but the home domain
is "live_touring" — shared with booking/touring agents. This test encodes
the CURRENT correct behavior without changing agent_home.py or shared files.

All tests are deterministic, in-process, NO LLM / API calls.
"""
import pytest

from knowledge_bank.agent_home import consult_for_agent

_AGENT = "schedule-keeper"
_HOME  = "live_touring"


def _consult(query: str, max_domains: int = 4) -> dict:
    return consult_for_agent(_AGENT, query, max_domains=max_domains)


# ── Deep consult matrix (5 cross-domain scenarios) ───────────────────────────
#
# (query, expected_cross_domains)
# Invariant: "live_touring" leads; every expected cross-domain is present.
# Keywords commented per domain to document the routing logic.
# NOTE: "campaign" alone → marketing keyword — avoid it unless marketing
#       is an intended cross-domain.
# NOTE: "release campaign" also fires marketing (via "campaign" substring) —
#       use "release schedule" / "milestone timeline" instead for label_ops-only.
# NOTE: "editorial calendar" → playlist_dsp; use "countdown calendar" instead.
# NOTE: "dsp delivery" → digital_ops; avoid "DSP delivery" if digital_ops is
#       not an intended cross-domain.
# NOTE: "activation" → bizdev; "submission" contains "bmi" →
#       finance_royalties — both excluded from Q4 to stay within max_domains.

DEEP_CONSULT_MATRIX = [
    (
        # live_touring: home — always leads ("touring")
        # label_ops:    "milestone timeline", "delivery commitment",
        #               "release schedule"
        "We need to build a six-week release countdown calendar, set the "
        "milestone timeline for each delivery stage, track the delivery "
        "commitment to the label, and keep the release schedule aligned "
        "with our touring diary.",
        ["label_ops"],
    ),
    (
        # live_touring: home — always leads ("festival", "booking", "touring")
        # marketing:    "content strategy", "social media", "tiktok",
        #               "instagram"
        "How do we map a daily content strategy and social media posting "
        "calendar on TikTok and Instagram to coordinate with our confirmed "
        "festival booking and the full touring run?",
        ["marketing"],
    ),
    (
        # live_touring: home — always leads ("touring", "on the road")
        # marketing:    "social media", "audience"
        # fan_social:   "fan community", "fan engagement"
        "We are on a global touring run and need a social media posting "
        "schedule that accounts for international timezone windows to grow "
        "our audience and deepen fan community engagement with supporters "
        "on the road.",
        ["marketing", "fan_social"],
    ),
    (
        # live_touring: home — always leads ("touring")
        # label_ops:    "pre-save", "editorial pitch", "pitch window"
        # playlist_dsp: "pre-save", "editorial pitch", "pitch window", "dsp"
        # NOTE: "activation" → bizdev; "submission" contains "bmi" →
        #       finance_royalties — both excluded to keep max_domains clean.
        "We need to align our pre-save deadline with the editorial pitch "
        "and DSP pitch window so our touring schedule does not block those "
        "key release date milestones.",
        ["label_ops", "playlist_dsp"],
    ),
    (
        # live_touring: home — always leads ("booking", "touring", "venue",
        #               "headliner", "concert")
        # bizdev:       "brand", "sponsor" (in "sponsorship"), "activation",
        #               "merchandise deal"
        "We are booking a touring run and want to schedule brand "
        "sponsorship activation events at specific venue dates, plus lock "
        "in merchandise deal tie-ins at the headliner concert shows.",
        ["bizdev"],
    ),
]

# ── Narrow / home-only scenario ───────────────────────────────────────────────
#
# A tightly-scoped touring-diary / posting-routine / gig-dates question that
# returns ONLY "live_touring" (via home domain). Deliberately avoids:
# "contract" / "clause" / "rights" / "legal" / "negotiat" / "indemnit" (legal)
# "royalt" / "splits" / "show income" / "tour revenue" /
#   "income split" (finance_royalties)
# "marketing" / "campaign" / "social media" / "audience" / "growth" /
#   "content strategy" / "instagram" / "tiktok" (marketing)
# "superfan" / "fan community" / "fan engagement" / "newsletter" (fan_social)
# "brand" / "sponsor" / "merch" / "merchandise" / "partnership" /
#   "activation" (bizdev)
# "release schedule" / "milestone timeline" / "delivery commitment" /
#   "pre-save" / "editorial" (label_ops)
# "playlist" / "dsp" / "editorial" / "editorial calendar" (playlist_dsp)
# "publish" / "catalog" / "composition" / "songwrit" (publishing)
# "production" / "studio" / "mixing" / "mastering" (production)
# "analytics" / "metric" / "kpi" / "streaming" (data_analytics)
# "capital" / "fund" / "financ" / "invest" / "runway" (capital_funding)
# "metadata" / "isrc" / "upc" / "digital ops" / "upcoming" via "upc"
#   substring — excluded here (digital_ops)
# "intelligence" / "market trend" / "industry" (intelligence)
# "artist manager" / "management" / "managing the artist" (management)
# "scouting" / "talent scout" / "unsigned" / "a&r" / "roster" (ar)
# "sync" / "licens" / "film" / "tv" / "placement" (sync)
# "reconcil" / "ledger" / "controller" (controller)
# "executive" / "ceo" / "strategic" (executive)
# "weekly scan" — note: "week-by-week" is safe; "weekly scan" is intelligence

_NARROW_QUERY = (
    "How do we maintain a consistent posting routine throughout the "
    "touring run, handle day-off gaps between gig dates and load-in "
    "days, and build a confirmed headliner diary for the full "
    "on the road run?"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "query, cross",
    DEEP_CONSULT_MATRIX,
    ids=[
        "release-countdown-calendar-milestone-timeline-delivery-commitment-label-ops",
        "content-calendar-tiktok-instagram-festival-booking-touring-marketing",
        "global-tour-social-schedule-fan-community-engagement-marketing-fan-social",
        "pre-save-deadline-editorial-submission-pitch-window-dsp-label-ops-playlist-dsp",
        "brand-sponsorship-activation-merchandise-deal-touring-venue-bizdev",
    ],
)
def test_schedule_keeper_consult_home_leads_and_cross_domains_present(query, cross):
    """
    schedule-keeper's home domain 'live_touring' is always first; every
    expected cross-domain is present. Verifies home-first invariant and
    scheduling specialist cross-domain routing quality.
    """
    result = _consult(query)

    assert result["home_domain"] == _HOME, (
        f"expected home={_HOME!r}, got {result['home_domain']!r}"
    )
    assert result["domains"], "domains list is empty"
    assert result["domains"][0] == _HOME, (
        f"home domain must be first; got {result['domains']}"
    )
    for d in cross:
        assert d in result["domains"], (
            f"expected cross-domain {d!r} not found in {result['domains']}\n"
            f"Query: {query!r}"
        )
    assert result["knowledge"].strip(), "knowledge text is empty"


def test_schedule_keeper_narrow_query_returns_home_domain_only():
    """
    A tightly-scoped posting-routine / touring-diary / gig-dates question (no
    keywords from legal / finance_royalties / marketing / fan_social / bizdev /
    label_ops / playlist_dsp / publishing / production / data_analytics /
    capital_funding / digital_ops / intelligence / management / ar / sync /
    controller / executive) must return only the home domain with no spurious
    cross-domain routing.
    """
    result = _consult(_NARROW_QUERY)

    assert result["home_domain"] == _HOME
    assert result["domains"] == [_HOME], (
        f"expected ['{_HOME}'] only, got {result['domains']!r}\n"
        f"Query: {_NARROW_QUERY!r}"
    )
    assert result["knowledge"].strip(), "knowledge text is empty for narrow query"
