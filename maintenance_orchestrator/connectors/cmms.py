from __future__ import annotations

from typing import Protocol

from maintenance_orchestrator.models.domain import MaintenanceRequest
from maintenance_orchestrator.state.cmms_mapping import CmmsMapping


class CmmsConnector(Protocol):
    def upsert_work_order(self, req: MaintenanceRequest) -> str: ...


class NoOpCmmsConnector:
    """Returns fake CMMS id; swap for Atlas CMMS API."""

    def __init__(self) -> None:
        self._n = 0

    def upsert_work_order(self, req: MaintenanceRequest) -> str:
        _ = CmmsMapping.to_cmms(req.state)
        self._n += 1
        return f"CMMS-WO-{self._n:05d}"

class AtlasCmmsConnector:
    """Mock for real Atlas CMMS API."""
    def __init__(self, api_key: str = "test", base_url: str = "https://api.atlascmms.mock") -> None:
        self.api_key = api_key
        self.base_url = base_url
        self._n = 0

    def upsert_work_order(self, req: MaintenanceRequest) -> str:
        cmms_state = CmmsMapping.to_cmms(req.state)
        payload = {
            "title": f"[{req.portfolio_id}] {req.issue_type or 'Issue'} at {req.property_id}",
            "description": req.description,
            "status": cmms_state.value,
            "tenant": req.tenant.model_dump(),
        }
        # e.g., httpx.post(f"{self.base_url}/work-orders", json=payload)
        self._n += 1
        print(f"DEBUG: Sent to Atlas CMMS: {payload}")
        return f"ATLAS-WO-{self._n:05d}"
