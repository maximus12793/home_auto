from __future__ import annotations

import secrets
import string

from pydantic import BaseModel, Field

from maintenance_orchestrator.models.domain import (
    Channel,
    MaintenanceRequest,
    OrchestratorState,
    TenantRef,
)


def _new_correlation_id() -> str:
    suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"REQ-{suffix}"


class IntakePayload(BaseModel):
    portfolio_id: str
    property_id: str
    unit_id: str
    tenant: TenantRef
    channel: Channel
    description: str
    issue_type: str | None = None
    property_address: str | None = None
    access_notes: str | None = None


class IntakeService:
    """Normalize intake and attach provenance + correlation id."""

    def create_request(self, payload: IntakePayload) -> MaintenanceRequest:
        cid = _new_correlation_id()
        return MaintenanceRequest(
            correlation_id=cid,
            portfolio_id=payload.portfolio_id,
            property_id=payload.property_id,
            unit_id=payload.unit_id,
            tenant=payload.tenant,
            channel=payload.channel,
            description=payload.description.strip(),
            issue_type=payload.issue_type,
            state=OrchestratorState.intake,
            property_address=payload.property_address,
            access_notes=payload.access_notes,
        )
