from __future__ import annotations

import re

from pydantic import BaseModel

from maintenance_orchestrator.models.domain import MaintenanceRequest, Priority, Trade


class TriageResult(BaseModel):
    trade: Trade
    priority: Priority


_KEYWORDS: list[tuple[re.Pattern[str], Trade]] = [
    (re.compile(r"\b(water|leak|drain|toilet|sink|pipe|plumb)\b", re.I), Trade.plumbing),
    (re.compile(r"\b(outlet|spark|breaker|electric|wire)\b", re.I), Trade.electrical),
    (re.compile(r"\b(heat|furnace|ac|hvac|air)\b", re.I), Trade.hvac),
    (re.compile(r"\b(fridge|washer|dryer|appliance|dishwasher)\b", re.I), Trade.appliance),
    (re.compile(r"\b(door|drywall|paint|handyman)\b", re.I), Trade.handyman),
]


class TriageService:
    """Lightweight keyword triage — replace with ML or rules engine later."""

    def classify(self, req: MaintenanceRequest) -> TriageResult:
        text = f"{req.description} {req.issue_type or ''}"
        trade = Trade.unknown
        for pat, t in _KEYWORDS:
            if pat.search(text):
                trade = t
                break
        priority = Priority.routine
        if re.search(r"\b(emergency|flood|fire|spark|no heat|gas)\b", text, re.I):
            priority = Priority.emergency
        elif re.search(r"\b(urgent|asap|soon)\b", text, re.I):
            priority = Priority.urgent
        return TriageResult(trade=trade, priority=priority)
