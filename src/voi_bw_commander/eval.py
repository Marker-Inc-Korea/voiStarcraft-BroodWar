from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import CommandUtterance
from .parser import parse_utterance


@dataclass(frozen=True)
class CorpusResult:
    case_id: str
    passed: bool
    details: tuple[str, ...]


@dataclass(frozen=True)
class CorpusReport:
    passed: bool
    score: float
    results: tuple[CorpusResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "results": [
                {"case_id": result.case_id, "passed": result.passed, "details": list(result.details)}
                for result in self.results
            ],
        }


def evaluate_corpus(path: Path) -> CorpusReport:
    cases = json.loads(path.read_text(encoding="utf-8"))
    results = tuple(_evaluate_case(case) for case in cases)
    score = sum(1 for result in results if result.passed) / (len(results) or 1)
    return CorpusReport(passed=all(result.passed for result in results), score=round(score, 4), results=results)


def _evaluate_case(case: dict[str, Any]) -> CorpusResult:
    commands = parse_utterance(CommandUtterance(text=case["text"]))
    actions = [command.action for command in commands]
    plans = [command.payload.get("plan") for command in commands if command.payload.get("plan")]
    races = [command.payload.get("race") for command in commands if command.payload.get("race")]
    max_ambiguity = max((command.ambiguity_score for command in commands), default=0.0)

    details: list[str] = []
    for action in case["expected_actions"]:
        if action not in actions:
            details.append(f"missing action: {action}; got {actions}")
    for plan in case.get("expected_plans", []):
        if plan not in plans:
            details.append(f"missing plan: {plan}; got {plans}")
    expected_race = case.get("expected_race")
    if expected_race and expected_race not in races:
        details.append(f"missing race: {expected_race}; got {races}")
    if len(commands) < int(case.get("min_commands", 1)):
        details.append(f"too few commands: {len(commands)}")
    if max_ambiguity > float(case.get("max_ambiguity", 1.0)):
        details.append(f"ambiguity too high: {max_ambiguity}")

    return CorpusResult(case_id=case["id"], passed=not details, details=tuple(details or ["ok"]))
