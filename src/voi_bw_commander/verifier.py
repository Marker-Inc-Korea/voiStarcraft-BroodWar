from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import IntentState


@dataclass
class VerificationResult:
    passed: bool
    score: float
    details: list[str] = field(default_factory=list)


class Verifier:
    def verify(self, state: IntentState, telemetry: dict[str, Any]) -> VerificationResult:
        checks = []
        details: list[str] = []
        for command in state.memory.active.values():
            for expectation in command.expectations:
                passed, detail = expectation.evaluate(telemetry)
                checks.append(passed)
                details.append(f"{command.action}: {detail}")
        if not checks:
            return VerificationResult(True, 1.0, ["no active verifier expectations"])
        score = sum(1 for item in checks if item) / len(checks)
        return VerificationResult(score >= 0.8, round(score, 4), details)
