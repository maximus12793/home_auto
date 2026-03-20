from __future__ import annotations

from pydantic import BaseModel
from maintenance_orchestrator.store.memory import RequestStore
from maintenance_orchestrator.store.quote_db import QuoteStore


class VendorScorecard(BaseModel):
    vendor_id: str
    total_quotes_submitted: int
    average_quote_usd: float | None


class AnalyticsService:
    def __init__(self, request_store: RequestStore, quote_store: QuoteStore) -> None:
        self.request_store = request_store
        self.quote_store = quote_store

    def get_vendor_scorecards(self) -> list[VendorScorecard]:
        """Calculates total quotes and average submitted cost per vendor."""
        # For simplicity, load all correlation IDs and fetch their quotes
        all_ids = self.request_store.all_ids()
        all_quotes = []
        for req_id in all_ids:
            all_quotes.extend(self.quote_store.list_quotes(req_id))

        counts: dict[str, int] = {}
        totals: dict[str, int] = {}

        for q in all_quotes:
            counts[q.vendor_id] = counts.get(q.vendor_id, 0) + 1
            if q.amount_cents is not None:
                totals[q.vendor_id] = totals.get(q.vendor_id, 0) + q.amount_cents

        cards = []
        for vid, count in counts.items():
            avg_usd = None
            if count > 0 and vid in totals:
                avg_usd = (totals[vid] / count) / 100.0
            cards.append(
                VendorScorecard(
                    vendor_id=vid,
                    total_quotes_submitted=count,
                    average_quote_usd=avg_usd,
                )
            )

        # Sort by most active
        cards.sort(key=lambda x: x.total_quotes_submitted, reverse=True)
        return cards
