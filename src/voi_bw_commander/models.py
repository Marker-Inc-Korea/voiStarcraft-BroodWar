from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any
from uuid import uuid4


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class Race(StrEnum):
    ZERG = "Zerg"
    PROTOSS = "Protoss"
    TERRAN = "Terran"
    RANDOM = "Random"
    UNKNOWN = "Unknown"


class CommandType(StrEnum):
    INSTANT_ORDER = "instant_order"
    HARD_GOAL = "hard_goal"
    PERSISTENT_STYLE = "persistent_style"
    STRATEGIC_COMMITMENT = "strategic_commitment"
    MICRO_DOCTRINE = "micro_doctrine"
    CONTRACT_PATCH = "contract_patch"


class IntentPriority(StrEnum):
    ADVISORY = "advisory"
    PREFERRED = "preferred"
    HARD = "hard"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class CommandStatus(StrEnum):
    ACCEPTED = "accepted"
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    BLOCKED = "blocked"
    UNSAFE = "unsafe"
    INVALID = "invalid"
    SUPERSEDED = "superseded"
    DEGRADED = "degraded"
    CANCELLED = "cancelled"


class BackendCapability(StrEnum):
    BENCHMARK_ONLY = "benchmark_only"
    LAUNCH_CONFIG = "launch_config"
    PERSISTENT_STYLE = "persistent_style"
    OBJECTIVE_INJECTION = "objective_injection"
    MICRO_DOCTRINE = "micro_doctrine"
    FULL_TELEMETRY = "full_telemetry"


@dataclass(frozen=True)
class CommandUtterance:
    text: str
    language: str = "ko"
    source: str = "text"
    timestamp: float = field(default_factory=time)
    utterance_id: str = field(default_factory=lambda: f"utt_{uuid4().hex}")


@dataclass
class VerifierExpectation:
    metric: str
    operator: str
    value: Any
    window_frames: int | None = None
    description: str = ""

    def evaluate(self, telemetry: dict[str, Any]) -> tuple[bool, str]:
        actual = telemetry.get(self.metric)
        if actual is None:
            return False, f"missing metric: {self.metric}"
        if self.operator == ">=":
            return actual >= self.value, f"{self.metric}={actual} expected >= {self.value}"
        if self.operator == "<=":
            return actual <= self.value, f"{self.metric}={actual} expected <= {self.value}"
        if self.operator == "==":
            return actual == self.value, f"{self.metric}={actual} expected == {self.value}"
        if self.operator == "contains":
            return self.value in actual, f"{self.metric} contains {self.value}: {actual}"
        raise ValueError(f"unsupported verifier operator: {self.operator}")


@dataclass
class ParsedCommand:
    command_type: CommandType
    action: str
    scope: str = "global"
    priority: IntentPriority = IntentPriority.PREFERRED
    strength: float = 1.0
    duration: str = "until_cancelled"
    payload: dict[str, Any] = field(default_factory=dict)
    expectations: list[VerifierExpectation] = field(default_factory=list)
    command_id: str = field(default_factory=lambda: f"cmd_{uuid4().hex}")
    utterance_id: str | None = None
    confidence: float = 1.0
    ambiguity_score: float = 0.0

    def to_event(self, status: CommandStatus, reason: str = "") -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "type": self.command_type.value,
            "action": self.action,
            "status": status.value,
            "reason": reason,
            "payload": self.payload,
        }


@dataclass
class CapabilityManifest:
    backend_name: str
    race_support: set[Race]
    capabilities: set[BackendCapability]
    supported_actions: set[str]
    integration_level: int
    notes: str = ""

    def supports(self, race: Race, command: ParsedCommand) -> tuple[bool, str]:
        if command.action == "set_race":
            return True, "supported"
        if race != Race.UNKNOWN and race not in self.race_support and Race.RANDOM not in self.race_support:
            return False, f"{self.backend_name} does not support race {race.value}"
        if command.action not in self.supported_actions:
            return False, f"{self.backend_name} does not support action {command.action}"
        required = {
            CommandType.PERSISTENT_STYLE: BackendCapability.PERSISTENT_STYLE,
            CommandType.STRATEGIC_COMMITMENT: BackendCapability.OBJECTIVE_INJECTION,
            CommandType.HARD_GOAL: BackendCapability.OBJECTIVE_INJECTION,
            CommandType.MICRO_DOCTRINE: BackendCapability.MICRO_DOCTRINE,
        }.get(command.command_type)
        if required and required not in self.capabilities:
            return False, f"{self.backend_name} lacks {required.value}"
        return True, "supported"


@dataclass
class IntentMemory:
    active: dict[str, ParsedCommand] = field(default_factory=dict)
    completed: list[dict[str, Any]] = field(default_factory=list)
    cancelled: list[dict[str, Any]] = field(default_factory=list)
    superseded: list[dict[str, Any]] = field(default_factory=list)
    blocked: list[dict[str, Any]] = field(default_factory=list)
    unsafe: list[dict[str, Any]] = field(default_factory=list)
    degraded: list[dict[str, Any]] = field(default_factory=list)

    def record(self, command: ParsedCommand, status: CommandStatus, reason: str = "") -> None:
        event = command.to_event(status, reason)
        if status in {CommandStatus.ACCEPTED, CommandStatus.ACTIVE}:
            self.active[command.command_id] = command
        elif status == CommandStatus.FULFILLED:
            self.active.pop(command.command_id, None)
            self.completed.append(event)
        elif status == CommandStatus.CANCELLED:
            self.active.pop(command.command_id, None)
            self.cancelled.append(event)
        elif status == CommandStatus.SUPERSEDED:
            self.active.pop(command.command_id, None)
            self.superseded.append(event)
        elif status == CommandStatus.BLOCKED:
            self.blocked.append(event)
        elif status == CommandStatus.UNSAFE:
            self.unsafe.append(event)
        elif status == CommandStatus.DEGRADED:
            self.degraded.append(event)


@dataclass
class StrategicContract:
    race: Race = Race.UNKNOWN
    backend_bot: str = "unselected"
    style: dict[str, float] = field(
        default_factory=lambda: {
            "aggression": 0.5,
            "harass": 0.5,
            "economy_greed": 0.5,
            "defensive_safety": 0.5,
            "all_in_commitment": 0.2,
        }
    )
    strategic_commitments: dict[str, ParsedCommand] = field(default_factory=dict)
    hard_goals: dict[str, ParsedCommand] = field(default_factory=dict)
    standing_orders: dict[str, ParsedCommand] = field(default_factory=dict)
    instant_orders: dict[str, ParsedCommand] = field(default_factory=dict)

    def apply(self, command: ParsedCommand) -> None:
        if command.command_type == CommandType.PERSISTENT_STYLE:
            self.style.update(command.payload.get("style", {}))
        elif command.command_type == CommandType.STRATEGIC_COMMITMENT:
            self.strategic_commitments[command.command_id] = command
        elif command.command_type == CommandType.HARD_GOAL:
            self.hard_goals[command.command_id] = command
        elif command.command_type == CommandType.MICRO_DOCTRINE:
            self.standing_orders[command.command_id] = command
        elif command.command_type == CommandType.INSTANT_ORDER:
            self.instant_orders[command.command_id] = command
        elif command.command_type == CommandType.CONTRACT_PATCH:
            self._apply_patch(command.payload)

    def _apply_patch(self, payload: dict[str, Any]) -> None:
        if race := payload.get("race"):
            self.race = Race(race)
        if backend := payload.get("backend_bot"):
            self.backend_bot = backend
        self.style.update(payload.get("style", {}))


@dataclass
class IntentState:
    contract: StrategicContract = field(default_factory=StrategicContract)
    memory: IntentMemory = field(default_factory=IntentMemory)
    version: int = 0

    def accept(
        self,
        command: ParsedCommand,
        manifest: CapabilityManifest | None = None,
    ) -> CommandStatus:
        if manifest is not None:
            supported, reason = manifest.supports(self.contract.race, command)
            if not supported:
                self.memory.record(command, CommandStatus.DEGRADED, reason)
                return CommandStatus.DEGRADED
        self.contract.apply(command)
        self.memory.record(command, CommandStatus.ACTIVE)
        self.version += 1
        return CommandStatus.ACTIVE

    def telemetry_snapshot(self) -> dict[str, Any]:
        return {
            "race": self.contract.race.value,
            "backend_bot": self.contract.backend_bot,
            "style": dict(self.contract.style),
            "active_commands": len(self.memory.active),
            "hard_goals": len(self.contract.hard_goals),
            "strategic_commitments": len(self.contract.strategic_commitments),
            "standing_orders": len(self.contract.standing_orders),
            "version": self.version,
        }
