from __future__ import annotations

import threading
from collections.abc import Callable, Iterable

from maintenance_orchestrator.models.domain import MaintenanceRequest


class RequestStore:
    """Portfolio-scoped storage. Every list operation requires portfolio_id."""

    def __init__(self) -> None:
        self._by_correlation: dict[str, MaintenanceRequest] = {}
        self._lock = threading.Lock()

    def put(self, req: MaintenanceRequest) -> MaintenanceRequest:
        with self._lock:
            self._by_correlation[req.correlation_id] = req
        return req

    def get(self, correlation_id: str) -> MaintenanceRequest | None:
        with self._lock:
            return self._by_correlation.get(correlation_id)

    def list_portfolio(self, portfolio_id: str) -> list[MaintenanceRequest]:
        with self._lock:
            return [r for r in self._by_correlation.values() if r.portfolio_id == portfolio_id]

    def update(
        self, correlation_id: str, mutator: Callable[[MaintenanceRequest], MaintenanceRequest]
    ) -> MaintenanceRequest | None:
        with self._lock:
            cur = self._by_correlation.get(correlation_id)
            if cur is None:
                return None
            updated = mutator(cur)
            self._by_correlation[correlation_id] = updated
            return updated

    def all_ids(self) -> Iterable[str]:
        with self._lock:
            return list(self._by_correlation.keys())
