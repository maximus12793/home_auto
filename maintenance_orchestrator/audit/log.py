from __future__ import annotations

from maintenance_orchestrator.models.domain import AuditEvent


class AuditLog:
    """Append-only in-memory audit trail per request."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> AuditEvent:
        self._events.append(event)
        return event

    def for_request(self, correlation_id: str) -> list[AuditEvent]:
        return [e for e in self._events if e.request_correlation_id == correlation_id]
