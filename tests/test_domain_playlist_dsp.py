"""
Tests for the re-homed "playlist_dsp" domain (Playlist and DSP).

In-process only. NO network / LLM calls. The bank reads knowledge files already
present in the repo (under knowledge_bank/domains/playlist_dsp/).
"""
from knowledge_bank import registry, brain
from entity_wall_terms import assert_no_forbidden_terms


# A query that is unambiguously in the playlist-and-DSP domain.
IN_DOMAIN_QUERY = (
    "land an editorial playlist add for this curator and protect release radar "
    "and discover weekly eligibility"
)


# ── registry ─────────────────────────────────────────────────────────────────────

def test_list_domains_includes_playlist_dsp():
    assert "playlist_dsp" in registry.list_domains()


def test_get_domain_display_name():
    assert registry.get_domain("playlist_dsp").display_name == "Playlist and DSP"


def test_load_domain_non_empty():
    text = registry.load_domain("playlist_dsp")
    assert isinstance(text, str)
    assert text.strip(), "playlist_dsp loaded empty knowledge"


def test_load_domain_assembles_core_doctrine():
    text = registry.load_domain("playlist_dsp").lower()
    # Core, domain-defining concepts must be present in the assembled knowledge.
    assert "placement probability" in text
    assert "three playlist economies" in text
    assert "trust account" in text
    assert "fit gate" in text
    assert "post-placement" in text
    assert "pay-for-play" in text
    assert "not-evaluable" in text


def test_load_domain_assembles_all_manifest_sections():
    # Eight knowledge files → eight sections joined by the standard separator.
    text = registry.load_domain("playlist_dsp")
    assert text.count("\n\n---\n\n") >= 7


# ── brain routing ─────────────────────────────────────────────────────────────────

def test_route_in_domain_query_to_playlist_dsp():
    assert "playlist_dsp" in brain.route(IN_DOMAIN_QUERY)


def test_route_pitch_query_to_playlist_dsp():
    assert "playlist_dsp" in brain.route(
        "draft the editorial pitch package and read the curator relationship state "
        "before we pitch the playlist"
    )


def test_route_platform_query_to_playlist_dsp():
    assert "playlist_dsp" in brain.route(
        "should we enroll the track in discovery mode and run a marquee campaign"
    )


def test_route_international_query_to_playlist_dsp():
    assert "playlist_dsp" in brain.route(
        "plan the editorial playlist strategy for boomplay and anghami in those territories"
    )


def test_route_unrelated_query_excludes_playlist_dsp():
    # Guard against keyword over-reach: a pure royalties query must not pull this in.
    assert "playlist_dsp" not in brain.route("how do mechanical royalties and recoup work")


def test_route_irrelevant_query_still_empty():
    assert brain.route("the weather is nice today") == []


# ── consult ───────────────────────────────────────────────────────────────────────

def test_consult_returns_playlist_dsp_section():
    result = brain.consult(IN_DOMAIN_QUERY)
    assert "playlist_dsp" in result["domains"]
    domain = registry.get_domain("playlist_dsp")
    assert f"# {domain.display_name} (playlist_dsp)" in result["knowledge"]
    assert result["knowledge"].strip()


# ── entity safety ─────────────────────────────────────────────────────────────────

def test_assembled_knowledge_has_no_forbidden_terms():
    assert_no_forbidden_terms(registry.load_domain("playlist_dsp"))


def test_consulted_knowledge_has_no_forbidden_terms():
    for query, home in [
        (IN_DOMAIN_QUERY, None),
        ("editorial pitch timing and curator relationship cadence", "playlist_dsp"),
        ("discovery mode and marquee decision for a catalog release", None),
    ]:
        result = brain.consult(query, home_domain=home)
        assert_no_forbidden_terms(result["knowledge"])
