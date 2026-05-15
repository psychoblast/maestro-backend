"""
Sentry-ready error reporting for PLMKR.

- Reads SENTRY_DSN at boot via init_error_reporting().
- Empty/unset DSN: no-op. Logs one message at boot.
- Set DSN: initializes sentry_sdk with FastAPI integration.
- capture_exception(exc, **context): no-op if disabled.
- Entire module works even if sentry-sdk is not installed.
"""

import logging
import os
from typing import Any

log = logging.getLogger("error_reporting")

_enabled = False


def init_error_reporting() -> None:
    """Initialize Sentry if SENTRY_DSN is set. No-op otherwise. Call once at boot."""
    global _enabled
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        log.info("[error_reporting] no DSN; Sentry disabled")
        _enabled = False
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=os.environ.get("RAILWAY_ENVIRONMENT", "development"),
            sample_rate=1.0,
            traces_sample_rate=0.1,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(),
            ],
            send_default_pii=False,
        )
        _enabled = True
        log.info("[error_reporting] Sentry initialized (env=%s)", os.environ.get("RAILWAY_ENVIRONMENT", "development"))
    except ImportError:
        log.warning("[error_reporting] sentry-sdk not installed; Sentry disabled")
        _enabled = False
    except Exception as exc:
        log.warning("[error_reporting] Sentry init failed: %s", exc)
        _enabled = False


def capture_exception(exc: Exception, **context: Any) -> None:
    """Capture an exception to Sentry. No-op when disabled or sentry-sdk missing."""
    if not _enabled:
        return
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            for key, val in context.items():
                scope.set_extra(key, val)
            sentry_sdk.capture_exception(exc)
    except Exception:  # noqa: BLE001 — error reporting must never raise
        pass


def is_enabled() -> bool:
    return _enabled
