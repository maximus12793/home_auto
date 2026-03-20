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


from maintenance_orchestrator.store.database import DatabaseRequestStore, DatabaseAuditLog

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orch
    _orch = Orchestrator(
        store=DatabaseRequestStore(),
        audit=DatabaseAuditLog()
    )
    yield


import os
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Maintenance orchestrator", version="0.1.0", lifespan=lifespan)

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

class TransitionBody(BaseModel):
    new_state: OrchestratorState


class TenantCoordinationBody(BaseModel):
    awaiting_tenant: bool
    reason: AwaitingTenantReason | None = None
    blocked_by: BlockedBy = BlockedBy.none
    next_action: str | None = None

from maintenance_orchestrator.models.domain import QuoteRecord

class QuoteSubmitBody(BaseModel):
    vendor_id: str
    amount_cents: int | None = None
    notes: str | None = None
    status: str = "pending"

from maintenance_orchestrator.analytics.service import AnalyticsService, VendorScorecard

@app.get("/analytics/scorecards", response_model=list[VendorScorecard])
def get_scorecards():
    svc = AnalyticsService(get_orch().store, get_orch().quotes.store)
    return svc.get_vendor_scorecards()

@app.get("/requests/{correlation_id}/quotes", response_model=list[QuoteRecord])
def get_quotes(correlation_id: str) -> list[QuoteRecord]:
    return get_orch().quotes.list_quotes(correlation_id)

@app.post("/requests/{correlation_id}/quotes", response_model=QuoteRecord)
def submit_quote(correlation_id: str, body: QuoteSubmitBody) -> QuoteRecord:
    try:
        return get_orch().quotes.add_quote(
            correlation_id,
            vendor_id=body.vendor_id,
            amount_cents=body.amount_cents,
            notes=body.notes,
            status=body.status,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Not found")


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
