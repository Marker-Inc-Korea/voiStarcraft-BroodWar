from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import asdict
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


class IntentAdaptivity(StrEnum):
    FIXED = "fixed"
    ADAPTIVE = "adaptive"
    OPPORTUNISTIC = "opportunistic"
    SAFETY_BREAKABLE = "safety_breakable"


class ConflictPolicy(StrEnum):
    STACK = "stack"
    REPLACE_SCOPE = "replace_scope"
    SUPPRESS_LOWER_PRIORITY = "suppress_lower_priority"
    REQUIRE_CONFIRMATION = "require_confirmation"
    SAFETY_OVERRIDE = "safety_override"


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerifierExpectation":
        return cls(**data)


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
    adaptivity: IntentAdaptivity = IntentAdaptivity.ADAPTIVE
    conflict_policy: ConflictPolicy = ConflictPolicy.STACK
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_type": self.command_type.value,
            "action": self.action,
            "scope": self.scope,
            "priority": self.priority.value,
            "strength": self.strength,
            "duration": self.duration,
            "payload": self.payload,
            "expectations": [expectation.to_dict() for expectation in self.expectations],
            "adaptivity": self.adaptivity.value,
            "conflict_policy": self.conflict_policy.value,
            "command_id": self.command_id,
            "utterance_id": self.utterance_id,
            "confidence": self.confidence,
            "ambiguity_score": self.ambiguity_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParsedCommand":
        return cls(
            command_type=CommandType(data["command_type"]),
            action=data["action"],
            scope=data.get("scope", "global"),
            priority=IntentPriority(data.get("priority", IntentPriority.PREFERRED.value)),
            strength=float(data.get("strength", 1.0)),
            duration=data.get("duration", "until_cancelled"),
            payload=dict(data.get("payload", {})),
            expectations=[VerifierExpectation.from_dict(item) for item in data.get("expectations", [])],
            adaptivity=IntentAdaptivity(data.get("adaptivity", IntentAdaptivity.ADAPTIVE.value)),
            conflict_policy=ConflictPolicy(data.get("conflict_policy", ConflictPolicy.STACK.value)),
            command_id=data.get("command_id", f"cmd_{uuid4().hex}"),
            utterance_id=data.get("utterance_id"),
            confidence=float(data.get("confidence", 1.0)),
            ambiguity_score=float(data.get("ambiguity_score", 0.0)),
        )


@dataclass
class CapabilityManifest:
    backend_name: str
    race_support: set[Race]
    capabilities: set[BackendCapability]
    supported_actions: set[str]
    integration_level: int
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend_name": self.backend_name,
            "race_support": sorted(race.value for race in self.race_support),
            "capabilities": sorted(capability.value for capability in self.capabilities),
            "supported_actions": sorted(self.supported_actions),
            "integration_level": self.integration_level,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityManifest":
        return cls(
            backend_name=data["backend_name"],
            race_support={Race(item) for item in data["race_support"]},
            capabilities={BackendCapability(item) for item in data["capabilities"]},
            supported_actions=set(data["supported_actions"]),
            integration_level=int(data["integration_level"]),
            notes=data.get("notes", ""),
        )

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

    def remove_command(self, command_id: str) -> None:
        for bucket in (
            self.strategic_commitments,
            self.hard_goals,
            self.standing_orders,
            self.instant_orders,
        ):
            bucket.pop(command_id, None)

    def _apply_patch(self, payload: dict[str, Any]) -> None:
        if race := payload.get("race"):
            self.race = Race(race)
        if backend := payload.get("backend_bot"):
            self.backend_bot = backend
        self.style.update(payload.get("style", {}))
        if not payload.get("preserve_existing", False):
            return
        # Patch commands intentionally keep existing goals and doctrines unless
        # a later command with a scoped replacement policy supersedes them.

    def to_dict(self) -> dict[str, Any]:
        return {
            "race": self.race.value,
            "backend_bot": self.backend_bot,
            "style": dict(self.style),
            "strategic_commitments": {
                key: command.to_dict() for key, command in self.strategic_commitments.items()
            },
            "hard_goals": {key: command.to_dict() for key, command in self.hard_goals.items()},
            "standing_orders": {key: command.to_dict() for key, command in self.standing_orders.items()},
            "instant_orders": {key: command.to_dict() for key, command in self.instant_orders.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StrategicContract":
        return cls(
            race=Race(data.get("race", Race.UNKNOWN.value)),
            backend_bot=data.get("backend_bot", "unselected"),
            style=dict(data.get("style", {})) or cls().style,
            strategic_commitments={
                key: ParsedCommand.from_dict(value)
                for key, value in data.get("strategic_commitments", {}).items()
            },
            hard_goals={
                key: ParsedCommand.from_dict(value) for key, value in data.get("hard_goals", {}).items()
            },
            standing_orders={
                key: ParsedCommand.from_dict(value)
                for key, value in data.get("standing_orders", {}).items()
            },
            instant_orders={
                key: ParsedCommand.from_dict(value) for key, value in data.get("instant_orders", {}).items()
            },
        )


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
        if command.action == "cancel_intent":
            cancelled = self.cancel_matching(command.payload)
            self.memory.record(command, CommandStatus.FULFILLED, f"cancelled={cancelled}")
            self.version += 1
            return CommandStatus.FULFILLED
        if manifest is not None:
            supported, reason = manifest.supports(self.contract.race, command)
            if not supported:
                self.memory.record(command, CommandStatus.DEGRADED, reason)
                return CommandStatus.DEGRADED
        self.contract.apply(command)
        self.memory.record(command, CommandStatus.ACTIVE)
        self.version += 1
        return CommandStatus.ACTIVE

    def cancel_matching(self, criteria: dict[str, Any]) -> int:
        target_action = criteria.get("target_action")
        target_plan = criteria.get("target_plan")
        cancel_all = criteria.get("all", False)
        cancelled = 0
        for command_id, active_command in list(self.memory.active.items()):
            if not cancel_all:
                if target_action and active_command.action != target_action:
                    continue
                if target_plan and active_command.payload.get("plan") != target_plan:
                    continue
            self.contract.remove_command(command_id)
            self.memory.record(active_command, CommandStatus.CANCELLED, "cancelled by user command")
            cancelled += 1
        return cancelled

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "contract": self.contract.to_dict(),
            "memory": {
                "active": {key: command.to_dict() for key, command in self.memory.active.items()},
                "completed": list(self.memory.completed),
                "cancelled": list(self.memory.cancelled),
                "superseded": list(self.memory.superseded),
                "blocked": list(self.memory.blocked),
                "unsafe": list(self.memory.unsafe),
                "degraded": list(self.memory.degraded),
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntentState":
        state = cls(
            contract=StrategicContract.from_dict(data.get("contract", {})),
            version=int(data.get("version", 0)),
        )
        memory = data.get("memory", {})
        state.memory.active = {
            key: ParsedCommand.from_dict(value) for key, value in memory.get("active", {}).items()
        }
        state.memory.completed = list(memory.get("completed", []))
        state.memory.cancelled = list(memory.get("cancelled", []))
        state.memory.superseded = list(memory.get("superseded", []))
        state.memory.blocked = list(memory.get("blocked", []))
        state.memory.unsafe = list(memory.get("unsafe", []))
        state.memory.degraded = list(memory.get("degraded", []))
        return state
