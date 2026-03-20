from __future__ import annotations

from maintenance_orchestrator.models.domain import OrchestratorState


# Placeholder CMMS statuses — replace with Atlas CMMS values when integrated.
CMMS_OPEN = "open"
CMMS_IN_PROGRESS = "in_progress"
CMMS_DONE = "done"
CMMS_CANCELLED = "cancelled"


class CmmsMapping:
    """Bidirectional orchestrator <-> CMMS status mapping (stub)."""

    @staticmethod
    def to_cmms(state: OrchestratorState) -> str:
        if state in (
            OrchestratorState.intake,
            OrchestratorState.triage,
            OrchestratorState.research,
            OrchestratorState.quoting,
            OrchestratorState.vendor_selected,
        ):
            return CMMS_OPEN
        if state in (OrchestratorState.scheduled, OrchestratorState.in_progress):
            return CMMS_IN_PROGRESS
        if state == OrchestratorState.completed:
            return CMMS_DONE
        return CMMS_CANCELLED

    @staticmethod
    def from_cmms(cmms_status: str) -> OrchestratorState | None:
        s = cmms_status.lower().strip()
        if s in ("open", "new", "assigned"):
            return OrchestratorState.vendor_selected
        if s in ("in_progress", "in progress", "scheduled"):
            return OrchestratorState.in_progress
        if s in ("done", "complete", "closed"):
            return OrchestratorState.completed
        if s in ("cancelled", "canceled"):
            return OrchestratorState.cancelled
        return None
