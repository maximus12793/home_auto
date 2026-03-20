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
