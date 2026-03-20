from __future__ import annotations

from pydantic import BaseModel

from maintenance_orchestrator.models.domain import DispatchPath, MaintenanceRequest, Priority, Trade
from maintenance_orchestrator.vendors.directory import VendorDirectory


class RoutingSuggestion(BaseModel):
    dispatch_path: DispatchPath
    preferred_vendor_ids: list[str]


class RouterService:
    """Choose dispatch path from triaged request + property-scoped vendor directory."""

    def __init__(self, vendors: VendorDirectory) -> None:
        self._vendors = vendors

    def suggest(self, req: MaintenanceRequest) -> RoutingSuggestion:
        if req.priority == Priority.emergency:
            return RoutingSuggestion(
                dispatch_path=DispatchPath.emergency_dispatch,
                preferred_vendor_ids=self._vendors.match(req.property_id, req.trade)[:3],
            )
        if req.trade == Trade.unknown or req.needs_owner_review:
            return RoutingSuggestion(dispatch_path=DispatchPath.owner_review, preferred_vendor_ids=[])
        matches = self._vendors.match(req.property_id, req.trade)
        if not matches:
            return RoutingSuggestion(
                dispatch_path=DispatchPath.marketplace_assisted,
                preferred_vendor_ids=[],
            )
        if req.priority == Priority.urgent:
            return RoutingSuggestion(
                dispatch_path=DispatchPath.preferred_vendor_quotes,
                preferred_vendor_ids=matches[:3],
            )
        return RoutingSuggestion(
            dispatch_path=DispatchPath.preferred_vendor_quotes,
            preferred_vendor_ids=matches[:5],
        )
