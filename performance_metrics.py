"""
In-memory rolling performance metrics for PLMKR.

Stores last N timings per route and computes p50/p95/p99.
Thread-safe; suitable for single-process deployments (Railway containers).
"""

import threading
from collections import deque
from typing import Optional


_WINDOW_SIZE = 1000  # samples per route


class _RouteMetrics:
    def __init__(self):
        self._lock   = threading.Lock()
        self._timings: deque[float] = deque(maxlen=_WINDOW_SIZE)

    def record(self, duration_ms: float) -> None:
        with self._lock:
            self._timings.append(duration_ms)

    def percentiles(self) -> dict:
        with self._lock:
            data = sorted(self._timings)
        if not data:
            return {"p50": None, "p95": None, "p99": None, "count": 0}
        n = len(data)

        def _pct(p: float) -> float:
            idx = max(0, int(n * p / 100) - 1)
            return round(data[idx], 2)

        return {
            "p50":   _pct(50),
            "p95":   _pct(95),
            "p99":   _pct(99),
            "count": n,
        }


_registry: dict[str, _RouteMetrics] = {}
_registry_lock = threading.Lock()


def record_request(route: str, duration_ms: float) -> None:
    with _registry_lock:
        if route not in _registry:
            _registry[route] = _RouteMetrics()
        metrics = _registry[route]
    metrics.record(duration_ms)


def get_all_percentiles() -> dict[str, dict]:
    with _registry_lock:
        routes = list(_registry.items())
    return {route: m.percentiles() for route, m in routes}
