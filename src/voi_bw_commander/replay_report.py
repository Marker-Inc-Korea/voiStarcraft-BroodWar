from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReplayReport:
    command_fulfillment_rate: float
    intent_adherence_score: float
    safety_override_count: int
    blocked_count: int
    conflict_count: int
    degraded_count: int
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_fulfillment_rate": self.command_fulfillment_rate,
            "intent_adherence_score": self.intent_adherence_score,
            "safety_override_count": self.safety_override_count,
            "blocked_count": self.blocked_count,
            "conflict_count": self.conflict_count,
            "degraded_count": self.degraded_count,
            "details": self.details,
        }


@dataclass
class ComparisonReport:
    baseline: ReplayReport
    commanded: ReplayReport
    fulfillment_delta: float
    adherence_delta: float
    safety_override_delta: int
    degraded_delta: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline": self.baseline.to_dict(),
            "commanded": self.commanded.to_dict(),
            "fulfillment_delta": self.fulfillment_delta,
            "adherence_delta": self.adherence_delta,
            "safety_override_delta": self.safety_override_delta,
            "degraded_delta": self.degraded_delta,
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
    blocked_count = sum(
        1 for event in command_events if event.get("payload", {}).get("status") == "blocked"
    )
    conflict_count = sum(
        1
        for event in command_events
        if event.get("payload", {}).get("category") in {"style_conflict", "command_conflict"}
    )
    denominator = len(active_or_terminal) or 1
    fulfillment_rate = len(fulfilled) / denominator
    adherence = sum(adherence_scores) / len(adherence_scores) if adherence_scores else 0.0
    return ReplayReport(
        command_fulfillment_rate=round(fulfillment_rate, 4),
        intent_adherence_score=round(adherence, 4),
        safety_override_count=safety_override_count,
        blocked_count=blocked_count,
        conflict_count=conflict_count,
        degraded_count=degraded_count,
        details=[f"command_events={len(command_events)}", f"adherence_samples={len(adherence_scores)}"],
    )


def compare_reports(baseline_events: list[dict[str, Any]], commanded_events: list[dict[str, Any]]) -> ComparisonReport:
    baseline = build_report(baseline_events)
    commanded = build_report(commanded_events)
    return ComparisonReport(
        baseline=baseline,
        commanded=commanded,
        fulfillment_delta=round(commanded.command_fulfillment_rate - baseline.command_fulfillment_rate, 4),
        adherence_delta=round(commanded.intent_adherence_score - baseline.intent_adherence_score, 4),
        safety_override_delta=commanded.safety_override_count - baseline.safety_override_count,
        degraded_delta=commanded.degraded_count - baseline.degraded_count,
    )
