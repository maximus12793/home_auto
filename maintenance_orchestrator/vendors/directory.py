from __future__ import annotations

from pydantic import BaseModel

from maintenance_orchestrator.models.domain import Trade


class VendorRecord(BaseModel):
    vendor_id: str
    name: str
    trades: list[Trade]
    property_ids: list[str]  # vendors can be scoped to specific properties


class VendorDirectory:
    """In-memory vendor list; replace with DB."""

    def __init__(self, vendors: list[VendorRecord] | None = None) -> None:
        self._vendors = vendors or []

    def seed_demo(self) -> None:
        self._vendors = [
            VendorRecord(
                vendor_id="v-plumb-1",
                name="Northside Plumbing",
                trades=[Trade.plumbing],
                property_ids=["prop-a"],
            ),
            VendorRecord(
                vendor_id="v-elec-1",
                name="SafeWire Electric",
                trades=[Trade.electrical],
                property_ids=["prop-a", "prop-b"],
            ),
            VendorRecord(
                vendor_id="v-handy-1",
                name="Quick Handyman",
                trades=[Trade.handyman, Trade.plumbing],
                property_ids=["prop-b"],
            ),
        ]

    def match(self, property_id: str, trade: Trade) -> list[str]:
        out: list[str] = []
        for v in self._vendors:
            if property_id not in v.property_ids:
                continue
            if trade in v.trades:
                out.append(v.vendor_id)
        return out
