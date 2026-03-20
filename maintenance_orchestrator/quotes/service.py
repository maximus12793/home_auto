from __future__ import annotations

from maintenance_orchestrator.models.domain import QuoteRecord


from maintenance_orchestrator.store.quote_db import QuoteStore, DatabaseQuoteStore

class QuoteService:
    """Record quotes against a request using the database store."""

    def __init__(self, store: QuoteStore | None = None) -> None:
        self.store = store or DatabaseQuoteStore()

    def list_quotes(self, correlation_id: str) -> list[QuoteRecord]:
        return self.store.list_quotes(correlation_id)

    def add_quote(self, correlation_id: str, vendor_id: str, amount_cents: int | None = None, notes: str | None = None, status: str = "pending") -> QuoteRecord:
        q = QuoteRecord(vendor_id=vendor_id, amount_cents=amount_cents, notes=notes, status=status)
        return self.store.add_quote(correlation_id, q)
