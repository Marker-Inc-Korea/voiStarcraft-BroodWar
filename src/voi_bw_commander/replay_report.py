from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReplayReport:
    command_fulfillment_rate: float
    intent_adherence_score: float
    safety_override_count: int
    degraded_count: int
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_fulfillment_rate": self.command_fulfillment_rate,
            "intent_adherence_score": self.intent_adherence_score,
            "safety_override_count": self.safety_override_count,
            "degraded_count": self.degraded_count,
            "details": self.details,
        }


def build_report(events: list[dict[str, Any]]) -> ReplayReport:
    command_events = [event for event in events if event.get("event_type") == "command_status"]
    fulfilled = [event for event in command_events if event.get("payload", {}).get("status") == "fulfilled"]
    active_or_terminal = [
        event
        for event in command_events
        if event.get("payload", {}).get("status")
        in {"active", "fulfilled", "blocked", "unsafe", "degraded", "cancelled", "superseded"}
    ]
    adherence_scores = [
        float(event.get("payload", {}).get("score"))
        for event in events
        if event.get("event_type") == "intent_adherence"
    ]
    safety_override_count = sum(
        1 for event in command_events if event.get("payload", {}).get("status") == "unsafe"
    )
    degraded_count = sum(
        1 for event in command_events if event.get("payload", {}).get("status") == "degraded"
    )
    denominator = len(active_or_terminal) or 1
    fulfillment_rate = len(fulfilled) / denominator
    adherence = sum(adherence_scores) / len(adherence_scores) if adherence_scores else 0.0
    return ReplayReport(
        command_fulfillment_rate=round(fulfillment_rate, 4),
        intent_adherence_score=round(adherence, 4),
        safety_override_count=safety_override_count,
        degraded_count=degraded_count,
        details=[f"command_events={len(command_events)}", f"adherence_samples={len(adherence_scores)}"],
    )
