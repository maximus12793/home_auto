from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from maintenance_orchestrator.intake.service import IntakePayload
from maintenance_orchestrator.models.domain import (
    AwaitingTenantReason,
    BlockedBy,
    MaintenanceRequest,
    OrchestratorState,
)
from maintenance_orchestrator.service import Orchestrator

_orch: Orchestrator | None = None


def get_orch() -> Orchestrator:
    assert _orch is not None
    return _orch


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orch
    _orch = Orchestrator()
    yield


app = FastAPI(title="Maintenance orchestrator", version="0.1.0", lifespan=lifespan)


class TransitionBody(BaseModel):
    new_state: OrchestratorState


class TenantCoordinationBody(BaseModel):
    awaiting_tenant: bool
    reason: AwaitingTenantReason | None = None
    blocked_by: BlockedBy = BlockedBy.none
    next_action: str | None = None


@app.post("/requests", response_model=MaintenanceRequest)
def create_request(body: IntakePayload) -> MaintenanceRequest:
    return get_orch().ingest(body)


@app.get("/requests", response_model=list[MaintenanceRequest])
def list_requests(portfolio_id: str = Query(..., description="Required portfolio scope")) -> list[MaintenanceRequest]:
    return get_orch().list_portfolio(portfolio_id)


@app.get("/requests/{correlation_id}", response_model=MaintenanceRequest)
def get_request(correlation_id: str) -> MaintenanceRequest:
    r = get_orch().get(correlation_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Not found")
    return r


@app.post("/requests/{correlation_id}/triage", response_model=MaintenanceRequest)
def triage(correlation_id: str) -> MaintenanceRequest:
    try:
        return get_orch().run_triage(correlation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Not found") from None


@app.post("/requests/{correlation_id}/transition", response_model=MaintenanceRequest)
def transition(correlation_id: str, body: TransitionBody) -> MaintenanceRequest:
    try:
        return get_orch().transition(correlation_id, body.new_state)
    except KeyError:
        raise HTTPException(status_code=404, detail="Not found") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/requests/{correlation_id}/tenant-coordination", response_model=MaintenanceRequest)
def tenant_coordination(correlation_id: str, body: TenantCoordinationBody) -> MaintenanceRequest:
    try:
        return get_orch().set_tenant_coordination(
            correlation_id,
            awaiting_tenant=body.awaiting_tenant,
            reason=body.reason,
            blocked_by=body.blocked_by,
            next_action=body.next_action,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Not found") from None


@app.get("/requests/{correlation_id}/audit")
def audit(correlation_id: str):
    return get_orch().audit_for(correlation_id)
