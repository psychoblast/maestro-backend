"""
Phase 3c-wiring PROOF tests.

These prove the knowledge bank is LIVE in the agents' real response path:

  (a) a PAIRED agent's response path consults the bank and includes its home domain;
  (b) an ORIGINALLY-UNPAIRED agent now has a home domain AND pulls cross-domain on a
      question that touches another domain;
  (c) AGENT_HOME covers the FULL agent roster (assert the full set), every home is a
      valid catalog domain, and the 9 original paired mappings are unchanged.

The "real response path" is ``build_system_blocks`` in main.py — the single shared
handler both /api/chat_stream and /api/handoff use to assemble every agent's system
prompt. Wiring the bank there makes ONE central change cover all agents.

All in-process. NO network / LLM calls (BANK_CONSULT_MOCK_MODE deterministic path).
"""
import importlib
from unittest.mock import MagicMock, patch

import pytest

from knowledge_bank import registry
from knowledge_bank.agent_home import AGENT_HOME

# The 9 originally paired agents — these mappings MUST stay exactly as authored.
PAIRED = {
    "ar-scout":         "ar",
    "grid-prophet":     "marketing",
    "sync-agent":       "sync",
    "brand-connect":    "bizdev",
    "lex-cipher":       "legal",
    "tour-commander":   "live_touring",
    "ink-and-air":      "publishing",
    "royalty-doctor":   "finance_royalties",
    "producer-connect": "production",
}


def _load_main(monkeypatch, tmp_path):
    """Import main.py with a hermetic env (no real keys, no whisper model)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY",      "sk-ant-test")
    monkeypatch.setenv("BANK_CONSULT_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",                str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",           "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",        str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",            str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",     "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        return m


def _blocks_text(blocks: list) -> str:
    """Flatten system blocks into one searchable string."""
    return "\n".join(b.get("text", "") for b in blocks)


# ── (a) paired agent's response path consults the bank, includes its home ─────────

def test_paired_agent_response_path_consults_bank_includes_home(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    agent = m.AGENTS_BY_ID["ar-scout"]            # paired → home "ar"
    blocks = m.build_system_blocks(agent, question="just a general check-in, nothing specific")
    text = _blocks_text(blocks)

    # The bank was consulted in the real response path...
    assert "KNOWLEDGE BANK CONSULTATION" in text
    # ...and the home domain (ar) is present even without keyword triggers.
    assert "A&R Scouting (ar)" in text


# ── (b) originally-unpaired agent: now homed AND reaches cross-domain ──────────────

def test_unpaired_origin_agent_now_homed_and_cross_domain(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # merch-empire was NOT in the original 9 paired agents.
    assert "merch-empire" not in PAIRED
    assert AGENT_HOME["merch-empire"] == "bizdev"   # now has a home

    agent = m.AGENTS_BY_ID["merch-empire"]
    # A question touching finance/publishing — domains that are NOT its home.
    blocks = m.build_system_blocks(
        agent,
        question="how do mechanical royalties and publishing splits work for a merch bundle",
    )
    text = _blocks_text(blocks)

    assert "KNOWLEDGE BANK CONSULTATION" in text
    assert "Brand & Business Development (bizdev)" in text         # home domain
    assert "Finance & Royalties (finance_royalties)" in text       # cross-domain
    assert "Publishing (publishing)" in text                       # cross-domain


def test_bank_block_lands_in_uncached_dynamic_block(monkeypatch, tmp_path):
    """The bank consultation depends on the question, so it must NOT pollute the
    cached static block (block 0) — it belongs in the live dynamic block (block 1)."""
    m = _load_main(monkeypatch, tmp_path)
    agent = m.AGENTS_BY_ID["ar-scout"]
    blocks = m.build_system_blocks(agent, question="sync licensing for a tv placement")

    assert blocks[0].get("cache_control") == {"type": "ephemeral"}
    assert "KNOWLEDGE BANK CONSULTATION" not in blocks[0]["text"]   # not cached
    assert "KNOWLEDGE BANK CONSULTATION" in blocks[1]["text"]       # live block
    assert "cache_control" not in blocks[1]


# ── (c) AGENT_HOME covers the full roster, valid domains, paired unchanged ─────────

def test_agent_home_covers_full_roster(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    roster = {a["id"] for a in m.AGENTS}

    # Every agent in the roster has a home, and there are no stray slugs.
    assert set(AGENT_HOME.keys()) == roster, (
        f"missing homes: {roster - set(AGENT_HOME)}; "
        f"stray slugs: {set(AGENT_HOME) - roster}"
    )


def test_every_home_is_a_valid_catalog_domain():
    valid = set(registry.list_domains())
    bad = {slug: dom for slug, dom in AGENT_HOME.items() if dom not in valid}
    assert not bad, f"agents mapped to unknown domains: {bad}"


def test_original_paired_mappings_unchanged():
    for slug, dom in PAIRED.items():
        assert AGENT_HOME[slug] == dom, f"{slug} paired home changed to {AGENT_HOME.get(slug)}"
