from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Channel(str, Enum):
    form = "form"
    email = "email"
    sms = "sms"
    voice = "voice"
    helpdesk = "helpdesk"


class Trade(str, Enum):
    plumbing = "plumbing"
    electrical = "electrical"
    handyman = "handyman"
    hvac = "hvac"
    appliance = "appliance"
    unknown = "unknown"


class Priority(str, Enum):
    emergency = "emergency"
    urgent = "urgent"
    routine = "routine"


class OrchestratorState(str, Enum):
    intake = "Intake"
    triage = "Triage"
    research = "Research"
    quoting = "Quoting"
    vendor_selected = "VendorSelected"
    scheduled = "Scheduled"
    in_progress = "InProgress"
    completed = "Completed"
    cancelled = "Cancelled"


class BlockedBy(str, Enum):
    none = "none"
    tenant = "tenant"
    vendor = "vendor"
    owner = "owner"
    permit = "permit"


class AwaitingTenantReason(str, Enum):
    schedule_access = "schedule_access"
    more_photos = "more_photos"
    confirm_permission_to_enter = "confirm_permission_to_enter"
    clarify_scope = "clarify_scope"


class DispatchPath(str, Enum):
    emergency_dispatch = "emergency_dispatch"
    preferred_vendor_quotes = "preferred_vendor_quotes"
    marketplace_assisted = "marketplace_assisted"
    owner_review = "owner_review"


class TenantRef(BaseModel):
    """Who filed the request (asserted until verified off-channel)."""

    display_name: str
    email: str | None = None
    phone: str | None = None
    tenant_id: UUID | None = None


class MaintenanceRequest(BaseModel):
    """A single maintenance thread scoped to portfolio + property + unit."""

    correlation_id: str = Field(..., description="Stable id e.g. REQ-… across CMMS/email/SMS")
    internal_id: UUID = Field(default_factory=uuid4)

    portfolio_id: str
    property_id: str
    unit_id: str

    tenant: TenantRef
    channel: Channel
    description: str
    issue_type: str | None = None

    trade: Trade = Trade.unknown
    priority: Priority = Priority.routine

    state: OrchestratorState = OrchestratorState.intake
    dispatch_path: DispatchPath | None = None

    awaiting_tenant: bool = False
    awaiting_tenant_reason: AwaitingTenantReason | None = None
    blocked_by: BlockedBy = BlockedBy.none
    next_action: str | None = None
    needs_owner_review: bool = False

    cmms_work_order_id: str | None = None

    created_at: datetime = Field(default_factory=utcnow)
    first_response_at: datetime | None = None
    completed_at: datetime | None = None

    property_address: str | None = None
    access_notes: str | None = None

    extra: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    request_correlation_id: str
    event_id: UUID = Field(default_factory=uuid4)
    at: datetime = Field(default_factory=utcnow)
    actor: str
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)


class QuoteRecord(BaseModel):
    quote_id: UUID = Field(default_factory=uuid4)
    vendor_id: str
    amount_cents: int | None = None
    currency: str = "USD"
    notes: str | None = None
    status: str = "pending"
