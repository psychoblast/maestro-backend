"""
Tests for B-05 — Stripe webhook signature enforcement.

Uses FastAPI TestClient against the real /api/billing/webhook route so
regressions where the route stops calling _verify_stripe_event are caught.

Previous version tested an inline copy of _verify_stripe_event (not the
production function) — tests passed whether or not the handler enforced
signatures. This rewrite exercises the actual route.

Run with:  python3 -m pytest tests/test_stripe_webhook.py -v
"""

import json
import importlib
from unittest.mock import MagicMock, patch

import pytest
import stripe as stripe_lib
from fastapi.testclient import TestClient


# ── Constants ─────────────────────────────────────────────────────────────────

FAKE_SECRET = "whsec_testsecret"
FAKE_SIG    = "t=123,v1=abc"
# Minimal event body — type "test.noop" falls through all if/elif branches in
# the handler so no artist file I/O is triggered.
_EVENT_BODY = json.dumps({
    "type": "test.noop",
    "data": {"object": {}},
}).encode()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def _base_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH",            str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",       "")
    monkeypatch.setenv("ANTHROPIC_API_KEY",  "sk-test")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test")
    monkeypatch.setenv("AUDIO_CACHE_DIR",    str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",        str(tmp_path / "artists"))
    # Must be set so STRIPE_AVAILABLE=True; value is never used for real calls.
    monkeypatch.setenv("STRIPE_SECRET_KEY",  "sk_test_fake")


def _make_client(monkeypatch, *, webhook_secret="", dev_allow_unsigned=""):
    """Reload main with chosen Stripe env config and return a TestClient."""
    if webhook_secret:
        monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", webhook_secret)
    else:
        monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    if dev_allow_unsigned:
        monkeypatch.setenv("STRIPE_DEV_ALLOW_UNSIGNED", dev_allow_unsigned)
    else:
        monkeypatch.delenv("STRIPE_DEV_ALLOW_UNSIGNED", raising=False)
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        return TestClient(m.app)


def _fake_event():
    """Minimal event dict the billing_webhook handler will accept."""
    return {"type": "test.noop", "data": {"object": {}}}


# ── Security guarantee ────────────────────────────────────────────────────────

def test_no_secret_no_dev_flag_returns_400(_base_env, monkeypatch):
    """Core security guarantee: unsigned webhook rejected when neither
    STRIPE_WEBHOOK_SECRET nor STRIPE_DEV_ALLOW_UNSIGNED is set.

    This is the regression test for the production route. If billing_webhook
    were changed to accept events without calling _verify_stripe_event, this
    test would receive 200 instead of 400 and fail — catching the regression.
    """
    client = _make_client(monkeypatch)
    resp = client.post(
        "/api/billing/webhook",
        content=_EVENT_BODY,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
    assert "STRIPE_WEBHOOK_SECRET" in resp.json()["detail"]


def test_wrong_signature_returns_400(_base_env, monkeypatch):
    """Bad stripe-signature header → 400, not 500.

    Simulates an attacker replaying a captured event body with a fabricated
    signature, or a webhook delivered to the wrong endpoint.
    """
    client = _make_client(monkeypatch, webhook_secret=FAKE_SECRET)
    sig_err = stripe_lib.error.SignatureVerificationError("sig mismatch", FAKE_SIG)
    with patch.object(stripe_lib.Webhook, "construct_event", side_effect=sig_err):
        resp = client.post(
            "/api/billing/webhook",
            content=_EVENT_BODY,
            headers={
                "Content-Type":     "application/json",
                "stripe-signature": "t=bad,v1=garbage",
            },
        )
    assert resp.status_code == 400


# ── Signature verification path ───────────────────────────────────────────────

def test_secret_set_calls_construct_event(_base_env, monkeypatch):
    """When STRIPE_WEBHOOK_SECRET is set, Webhook.construct_event is called
    with the correct secret.  Proves the route passes the module-level secret
    to the helper and does not fall through to an unsigned path.
    """
    client = _make_client(monkeypatch, webhook_secret=FAKE_SECRET)
    with patch.object(stripe_lib.Webhook, "construct_event",
                      return_value=_fake_event()) as mock_ce:
        client.post(
            "/api/billing/webhook",
            content=_EVENT_BODY,
            headers={
                "Content-Type":     "application/json",
                "stripe-signature": FAKE_SIG,
            },
        )
    mock_ce.assert_called_once()
    _body_arg, _sig_arg, secret_arg = mock_ce.call_args.args
    assert secret_arg == FAKE_SECRET


def test_valid_signature_returns_200(_base_env, monkeypatch):
    """With a valid signature the route returns 200 {"received": True}."""
    client = _make_client(monkeypatch, webhook_secret=FAKE_SECRET)
    with patch.object(stripe_lib.Webhook, "construct_event",
                      return_value=_fake_event()):
        resp = client.post(
            "/api/billing/webhook",
            content=_EVENT_BODY,
            headers={
                "Content-Type":     "application/json",
                "stripe-signature": FAKE_SIG,
            },
        )
    assert resp.status_code == 200
    assert resp.json() == {"received": True}


# ── Dev-unsigned path ─────────────────────────────────────────────────────────

def test_dev_flag_calls_construct_from(_base_env, monkeypatch):
    """No secret + STRIPE_DEV_ALLOW_UNSIGNED=true → Event.construct_from
    is called (not construct_event) and the route accepts the event.
    """
    client = _make_client(monkeypatch, dev_allow_unsigned="true")
    with patch.object(stripe_lib.Event, "construct_from",
                      return_value=_fake_event()) as mock_cf:
        resp = client.post(
            "/api/billing/webhook",
            content=_EVENT_BODY,
            headers={"Content-Type": "application/json"},
        )
    mock_cf.assert_called_once()
    assert resp.status_code == 200


def test_secret_takes_priority_over_dev_flag(_base_env, monkeypatch):
    """When both STRIPE_WEBHOOK_SECRET and STRIPE_DEV_ALLOW_UNSIGNED are set,
    construct_event wins — construct_from is never called.
    """
    client = _make_client(monkeypatch, webhook_secret=FAKE_SECRET,
                          dev_allow_unsigned="true")
    with patch.object(stripe_lib.Webhook, "construct_event",
                      return_value=_fake_event()) as mock_ce, \
         patch.object(stripe_lib.Event, "construct_from") as mock_cf:
        client.post(
            "/api/billing/webhook",
            content=_EVENT_BODY,
            headers={
                "Content-Type":     "application/json",
                "stripe-signature": FAKE_SIG,
            },
        )
    mock_ce.assert_called_once()
    mock_cf.assert_not_called()
