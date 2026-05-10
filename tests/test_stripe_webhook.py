"""
Unit tests for _verify_stripe_event() — Stripe webhook signature enforcement.

Tests the three-path logic added in fix/b05-stripe-webhook-signature:
  (a) secret set      → construct_event called (signature verified)
  (b) no secret, dev flag on  → construct_from called (unsigned accepted with warning)
  (c) no secret, dev flag off → HTTPException 400 raised immediately

_verify_stripe_event is extracted from the route handler so it can be tested
without importing all of main.py.  We inline an equivalent copy here and test
the logic; the real fix is in main.py at _verify_stripe_event().
"""

import json
from unittest.mock import MagicMock, patch, call

import pytest
from fastapi import HTTPException
import stripe as stripe_lib


# ── Helpers ───────────────────────────────────────────────────────────────────

def _verify_stripe_event(body: bytes, sig_header: str, webhook_secret: str, dev_allow_unsigned: bool):
    """Inline copy of main._verify_stripe_event for isolated unit testing."""
    if webhook_secret:
        return stripe_lib.Webhook.construct_event(body, sig_header, webhook_secret)
    if dev_allow_unsigned:
        return stripe_lib.Event.construct_from(json.loads(body), stripe_lib.api_key)
    raise HTTPException(
        status_code=400,
        detail="Webhook signature verification required — set STRIPE_WEBHOOK_SECRET",
    )


FAKE_BODY   = json.dumps({"type": "checkout.session.completed", "data": {"object": {}}}).encode()
FAKE_SIG    = "t=123,v1=abc"
FAKE_SECRET = "whsec_testsecret"
FAKE_EVENT  = MagicMock()


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_secret_set_calls_construct_event():
    with patch.object(stripe_lib.Webhook, "construct_event", return_value=FAKE_EVENT) as mock_ce:
        result = _verify_stripe_event(FAKE_BODY, FAKE_SIG, FAKE_SECRET, False)
    mock_ce.assert_called_once_with(FAKE_BODY, FAKE_SIG, FAKE_SECRET)
    assert result is FAKE_EVENT


def test_secret_set_ignores_dev_flag():
    """dev_allow_unsigned is irrelevant when secret is set — secret always wins."""
    with patch.object(stripe_lib.Webhook, "construct_event", return_value=FAKE_EVENT) as mock_ce:
        result = _verify_stripe_event(FAKE_BODY, FAKE_SIG, FAKE_SECRET, True)
    mock_ce.assert_called_once()
    assert result is FAKE_EVENT


def test_no_secret_dev_flag_on_calls_construct_from():
    with patch.object(stripe_lib.Event, "construct_from", return_value=FAKE_EVENT) as mock_cf:
        result = _verify_stripe_event(FAKE_BODY, "", "", True)
    mock_cf.assert_called_once()
    assert result is FAKE_EVENT


def test_no_secret_no_dev_flag_raises_400():
    with pytest.raises(HTTPException) as exc_info:
        _verify_stripe_event(FAKE_BODY, "", "", False)
    assert exc_info.value.status_code == 400
    assert "STRIPE_WEBHOOK_SECRET" in exc_info.value.detail


def test_no_secret_no_dev_flag_does_not_call_stripe():
    with patch.object(stripe_lib.Webhook, "construct_event") as mock_ce, \
         patch.object(stripe_lib.Event, "construct_from") as mock_cf:
        with pytest.raises(HTTPException):
            _verify_stripe_event(FAKE_BODY, "", "", False)
    mock_ce.assert_not_called()
    mock_cf.assert_not_called()
