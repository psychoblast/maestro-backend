"""
R-22 — 422 and HTTPException responses need explicit handlers.

FastAPI already routes RequestValidationError and HTTPException before the
generic Exception handler fires, so 422/4xx formats are structurally correct.
The gap: those responses don't carry a request_id for tracing, while 500s do.

Fix: add explicit @app.exception_handler(RequestValidationError) and
@app.exception_handler(HTTPException) that preserve native formats and
attach request_id, matching what the generic handler does for 500s.

Tests assert:
  - 422 response has {detail: [...], request_id: str}
  - HTTPException response has {detail: ..., request_id: str}
  - 500 response still has {error, detail, request_id} (no regression)
  - 422 detail is a list (native FastAPI format preserved)

Run with: python3 -m pytest tests/test_r22_422_passthrough.py -v
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH",           str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",      "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("AUDIO_CACHE_DIR",   str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",       str(tmp_path / "artists"))


@pytest.fixture()
def client():
    import main as m
    return TestClient(m.app, raise_server_exceptions=False)


# ── 422 carries request_id ────────────────────────────────────────────────────

def test_422_carries_request_id(client):
    """Pydantic validation failure → 422 with request_id for tracing."""
    resp = client.post("/api/chat_stream", json={})
    assert resp.status_code == 422
    data = resp.json()
    assert "request_id" in data, (
        f"422 response missing request_id — add explicit RequestValidationError handler. Got: {data}"
    )
    assert isinstance(data["request_id"], str)


def test_422_preserves_native_detail_list(client):
    """422 detail must still be a list of validation error objects (native format)."""
    resp = client.post("/api/chat_stream", json={})
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data
    assert isinstance(data["detail"], list), (
        f"422 detail should be a list, got {type(data['detail'])}: {data}"
    )
    first = data["detail"][0]
    assert "loc" in first and "msg" in first and "type" in first


# ── HTTPException carries request_id ─────────────────────────────────────────

def test_404_carries_request_id(client):
    """HTTPException(404) → response has request_id for tracing.
    Uses /api/greet with non-existent agent_id which raises HTTPException(404)."""
    resp = client.post("/api/greet", data={"agent_id": "does-not-exist-xyz", "tts": "false"})
    assert resp.status_code == 404
    data = resp.json()
    assert "request_id" in data, (
        f"404 response missing request_id — add explicit HTTPException handler. Got: {data}"
    )


def test_httpexception_preserves_status_and_detail(client):
    """HTTPException detail is preserved as-is (not re-wrapped)."""
    resp = client.post("/api/greet", data={"agent_id": "does-not-exist-xyz", "tts": "false"})
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert data["detail"] == "Agent not found", f"Expected 'Agent not found', got: {data}"
    assert "error" not in data or data["error"] != "HTTPException", (
        "HTTPException wrapped by generic handler — check handler priority"
    )


# ── 500 generic handler still works ──────────────────────────────────────────

def test_500_still_has_error_envelope(client):
    """Genuinely unhandled RuntimeError → 500 with {error, detail, request_id}."""
    import main as m

    @m.app.get("/test_r22_boom")
    async def _boom():
        raise RuntimeError("boom test")

    resp = client.get("/test_r22_boom")
    assert resp.status_code == 500
    data = resp.json()
    assert "error" in data
    assert "detail" in data
    assert "request_id" in data
