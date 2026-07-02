"""
Phase 3c-experts-sse PROOF tests.

Prove the /api/chat_stream SSE stream surfaces the knowledge-bank experts that
were consulted for the turn, so the frontend can display them:

  (a) a PAIRED agent emits an "experts" event with its home_domain and a
      non-empty ordered domains list (home first);
  (b) an originally-unpaired-but-now-homed agent emits its home domain plus a
      cross-domain match on a question that touches another domain.

The "experts" event is emitted BEFORE the "done" event and matches the existing
SSE serialization exactly (a `data: {json}\\n\\n` frame from main.sse()).

All in-process, deterministic. NO network / LLM calls — the Anthropic stream is
faked and BANK_CONSULT_MOCK_MODE keeps bank retrieval pure.
"""
import importlib
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class _FakeStream:
    """Stand-in for async_client.messages.stream(...) — an async context manager
    whose .text_stream yields the canned reply once."""

    def __init__(self, text):
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @property
    def text_stream(self):
        async def _gen():
            yield self._text
        return _gen()


def _load_client(monkeypatch, tmp_path, reply_text):
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
    # Fake the Anthropic stream so no live call happens.
    monkeypatch.setattr(m.async_client.messages, "stream", lambda **kw: _FakeStream(reply_text))
    return m, TestClient(m.app)


def _parse_sse(body: str) -> list:
    events = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:"):].strip()))
    return events


# ── (a) paired agent emits experts with home first ───────────────────────────

def test_paired_agent_stream_emits_experts_event(monkeypatch, tmp_path):
    # Benign reply that does NOT trigger agent routing.
    m, client = _load_client(monkeypatch, tmp_path, "Here is some general guidance for you.")
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "producer-connect",  # paired → home "production"
        "message":   "just a general check-in, nothing specific",
        "artist_id": "test-artist",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types = [e["type"] for e in events]

    assert "experts" in types, f"no experts event in stream: {types}"
    assert "done" in types
    # experts must come BEFORE done
    assert types.index("experts") < types.index("done")

    experts = next(e for e in events if e["type"] == "experts")
    assert experts["home_domain"] == "production"
    assert isinstance(experts["domains"], list) and experts["domains"], "domains empty"
    assert experts["domains"][0] == "production", "home domain must be first"


# ── (b) homed-but-originally-unpaired agent emits home + cross-domain ─────────

def test_unpaired_origin_agent_stream_emits_home_and_cross_domain(monkeypatch, tmp_path):
    m, client = _load_client(monkeypatch, tmp_path, "Happy to help with that.")
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "merch-empire",      # originally unpaired → home "bizdev"
        "message":   "how do mechanical royalties and publishing splits work for a merch bundle",
        "artist_id": "test-artist",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    experts = next((e for e in events if e["type"] == "experts"), None)
    assert experts is not None, f"no experts event: {[e['type'] for e in events]}"

    assert experts["home_domain"] == "bizdev"
    assert experts["domains"][0] == "bizdev", "home domain must be first"
    assert "finance_royalties" in experts["domains"], "cross-domain finance missing"
    assert "publishing" in experts["domains"], "cross-domain publishing missing"
