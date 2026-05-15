"""
A3 — Sentry-ready error hooks.

Tests:
- Empty/unset DSN: init_error_reporting() no-ops silently (is_enabled() False)
- Mock DSN: sentry_sdk.init is called with the DSN
- Module imports cleanly even when sentry-sdk is absent (sys.modules manipulation)
- capture_exception no-ops when disabled
"""

import importlib
import sys
from unittest.mock import MagicMock, patch, call


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_empty_dsn_noop(monkeypatch):
    """init_error_reporting() with empty DSN must leave is_enabled() False."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    import error_reporting
    importlib.reload(error_reporting)
    error_reporting.init_error_reporting()
    assert error_reporting.is_enabled() is False


def test_unset_dsn_noop(monkeypatch):
    """init_error_reporting() with no SENTRY_DSN env var must be a no-op."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    import error_reporting
    importlib.reload(error_reporting)
    error_reporting.init_error_reporting()
    assert not error_reporting.is_enabled()


def test_mock_dsn_calls_sentry_init(monkeypatch):
    """When SENTRY_DSN is set, sentry_sdk.init must be called with the DSN."""
    fake_dsn = "https://fakekey@o0.ingest.sentry.io/12345"
    monkeypatch.setenv("SENTRY_DSN", fake_dsn)

    mock_sdk = MagicMock()
    mock_sdk.integrations = MagicMock()

    with patch.dict("sys.modules", {
        "sentry_sdk": mock_sdk,
        "sentry_sdk.integrations": MagicMock(),
        "sentry_sdk.integrations.fastapi": MagicMock(FastApiIntegration=MagicMock()),
        "sentry_sdk.integrations.starlette": MagicMock(StarletteIntegration=MagicMock()),
    }):
        import error_reporting
        importlib.reload(error_reporting)
        error_reporting.init_error_reporting()

    mock_sdk.init.assert_called_once()
    init_call_kwargs = mock_sdk.init.call_args[1]
    assert init_call_kwargs.get("dsn") == fake_dsn


def test_module_import_without_sentry_sdk(monkeypatch):
    """Module must import and init cleanly even when sentry-sdk is not installed."""
    monkeypatch.setenv("SENTRY_DSN", "https://fake@o0.ingest.sentry.io/0")

    # Setting sys.modules[name] = None forces ImportError on `import name`
    with patch.dict("sys.modules", {
        "sentry_sdk": None,
        "sentry_sdk.integrations": None,
        "sentry_sdk.integrations.fastapi": None,
        "sentry_sdk.integrations.starlette": None,
    }):
        import error_reporting
        importlib.reload(error_reporting)
        # Must not raise — should log a warning and set _enabled = False
        error_reporting.init_error_reporting()
        assert not error_reporting.is_enabled()


def test_capture_exception_noop_when_disabled(monkeypatch):
    """capture_exception must not raise when Sentry is disabled."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    import error_reporting
    importlib.reload(error_reporting)
    error_reporting.init_error_reporting()
    # Must not raise
    error_reporting.capture_exception(ValueError("test error"), context="test")


def test_capture_exception_calls_sentry_when_enabled(monkeypatch):
    """capture_exception must call sentry_sdk.capture_exception when enabled."""
    fake_dsn = "https://fakekey@o0.ingest.sentry.io/99999"
    monkeypatch.setenv("SENTRY_DSN", fake_dsn)

    mock_sdk = MagicMock()
    mock_scope = MagicMock()
    mock_sdk.push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
    mock_sdk.push_scope.return_value.__exit__ = MagicMock(return_value=False)

    with patch.dict("sys.modules", {
        "sentry_sdk": mock_sdk,
        "sentry_sdk.integrations": MagicMock(),
        "sentry_sdk.integrations.fastapi": MagicMock(FastApiIntegration=MagicMock()),
        "sentry_sdk.integrations.starlette": MagicMock(StarletteIntegration=MagicMock()),
    }):
        import error_reporting
        importlib.reload(error_reporting)
        error_reporting.init_error_reporting()
        assert error_reporting.is_enabled()

        exc = ValueError("boom")
        error_reporting.capture_exception(exc, extra_key="extra_val")

    mock_sdk.capture_exception.assert_called_once_with(exc)
