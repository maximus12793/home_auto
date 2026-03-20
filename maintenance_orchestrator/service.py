from __future__ import annotations

from maintenance_orchestrator.audit.log import AuditLog
from maintenance_orchestrator.connectors.cmms import CmmsConnector, NoOpCmmsConnector
from maintenance_orchestrator.intake.service import IntakePayload, IntakeService
from maintenance_orchestrator.models.domain import (
    AuditEvent,
    AwaitingTenantReason,
    BlockedBy,
    MaintenanceRequest,
    OrchestratorState,
)
from maintenance_orchestrator.quotes.service import QuoteService
from maintenance_orchestrator.router.service import RouterService
from maintenance_orchestrator.state.lifecycle import apply_blocked_flags_for_state, assert_transition_allowed
from maintenance_orchestrator.store.memory import RequestStore
from maintenance_orchestrator.triage.service import TriageService
from maintenance_orchestrator.vendors.directory import VendorDirectory
from maintenance_orchestrator.connectors.email import EmailConnector
from maintenance_orchestrator.connectors.sms import SmsConnector


class Orchestrator:
    """Wires intake, triage, router, CMMS stub, quotes, audit."""

    def __init__(
        self,
        store: RequestStore | None = None,
        audit: AuditLog | None = None,
        vendors: VendorDirectory | None = None,
        cmms: CmmsConnector | None = None,
    ) -> None:
        self.store = store or RequestStore()
        self.audit = audit or AuditLog()
        self.vendors = vendors or VendorDirectory()
        self.vendors.seed_demo()
        self.intake = IntakeService()
        self.triage = TriageService()
        self.router = RouterService(self.vendors)
        self.quotes = QuoteService()
        self.cmms = cmms or NoOpCmmsConnector()
        self.email = EmailConnector()
        self.sms = SmsConnector()

    def ingest(self, payload: IntakePayload) -> MaintenanceRequest:
        req = self.intake.create_request(payload)
        self.store.put(req)
        self._log(req.correlation_id, "system", "request_created", {"channel": req.channel.value})
        
        if req.tenant.email:
            self.email.send(
                req.tenant.email, 
                f"Maintenance Request Received: {req.correlation_id}", 
                f"Thank you for submitting your {req.issue_type} request. Our team will review it shortly."
            )
        if req.tenant.phone:
            self.sms.send(
                req.tenant.phone, 
                f"Your Onyx property request {req.correlation_id} has been received."
            )
            
        return req

    def get(self, correlation_id: str) -> MaintenanceRequest | None:
        return self.store.get(correlation_id)

    def list_portfolio(self, portfolio_id: str) -> list[MaintenanceRequest]:
        return self.store.list_portfolio(portfolio_id)

    def run_triage(self, correlation_id: str) -> MaintenanceRequest:
        req = self.store.get(correlation_id)
        if req is None:
            raise KeyError(correlation_id)
        result = self.triage.classify(req)
        suggestion = self.router.suggest(
            req.model_copy(update={"trade": result.trade, "priority": result.priority})
        )

        def mut(r: MaintenanceRequest) -> MaintenanceRequest:
            r = r.model_copy(deep=True)
            r.trade = result.trade
            r.priority = result.priority
            r.state = OrchestratorState.triage
            r.dispatch_path = suggestion.dispatch_path
            r.extra["routing_suggestion"] = {
                "preferred_vendor_ids": suggestion.preferred_vendor_ids,
            }
            return r

        updated = self.store.update(correlation_id, mut)
        assert updated is not None
        self._log(
            correlation_id,
            "system",
            "triage_completed",
            {
                "trade": result.trade.value,
                "priority": result.priority.value,
                "dispatch_path": suggestion.dispatch_path.value,
            },
        )
        return updated

    def transition(self, correlation_id: str, new_state: OrchestratorState) -> MaintenanceRequest:
        req = self.store.get(correlation_id)
        if req is None:
            raise KeyError(correlation_id)
        assert_transition_allowed(req.state, new_state)

        def mut(r: MaintenanceRequest) -> MaintenanceRequest:
            r = r.model_copy(deep=True)
            r.state = new_state
            if new_state in (
                OrchestratorState.quoting,
                OrchestratorState.vendor_selected,
                OrchestratorState.scheduled,
                OrchestratorState.in_progress,
            ) and r.cmms_work_order_id is None:
                r.cmms_work_order_id = self.cmms.upsert_work_order(r)
            if new_state == OrchestratorState.completed:
                from maintenance_orchestrator.models.domain import utcnow

                r.completed_at = utcnow()
            return apply_blocked_flags_for_state(r)

        updated = self.store.update(correlation_id, mut)
        assert updated is not None
        self._log(
            correlation_id,
            "system",
            "state_transition",
            {
                "from": req.state.value,
                "to": new_state.value,
                "cmms_work_order_id": updated.cmms_work_order_id,
            },
        )
        return updated

    def set_tenant_coordination(
        self,
        correlation_id: str,
        *,
        awaiting_tenant: bool,
        reason: AwaitingTenantReason | None,
        blocked_by: BlockedBy,
        next_action: str | None,
    ) -> MaintenanceRequest:
        req = self.store.get(correlation_id)
        if req is None:
            raise KeyError(correlation_id)

        def mut(r: MaintenanceRequest) -> MaintenanceRequest:
            r = r.model_copy(deep=True)
            r.awaiting_tenant = awaiting_tenant
            r.awaiting_tenant_reason = reason if awaiting_tenant else None
            r.blocked_by = blocked_by if awaiting_tenant else BlockedBy.none
            r.next_action = next_action
            return r

        updated = self.store.update(correlation_id, mut)
        assert updated is not None
        self._log(
            correlation_id,
            "owner",
            "tenant_coordination_updated",
            {
                "awaiting_tenant": awaiting_tenant,
                "reason": reason.value if reason else None,
                "blocked_by": blocked_by.value,
            },
        )
        return updated

    def audit_for(self, correlation_id: str) -> list[AuditEvent]:
        return self.audit.for_request(correlation_id)

    def _log(self, correlation_id: str, actor: str, action: str, payload: dict) -> None:
        self.audit.append(
            AuditEvent(request_correlation_id=correlation_id, actor=actor, action=action, payload=payload)
        )
