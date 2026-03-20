from __future__ import annotations

from maintenance_orchestrator.models.domain import QuoteRecord


class QuoteService:
    """Stub: record quotes against a request; real impl emails vendors / portal."""

    def __init__(self) -> None:
        self._by_request: dict[str, list[QuoteRecord]] = {}

    def list_quotes(self, correlation_id: str) -> list[QuoteRecord]:
        return list(self._by_request.get(correlation_id, []))

    def add_quote(self, correlation_id: str, vendor_id: str, amount_cents: int | None = None) -> QuoteRecord:
        q = QuoteRecord(vendor_id=vendor_id, amount_cents=amount_cents)
        self._by_request.setdefault(correlation_id, []).append(q)
        return q
