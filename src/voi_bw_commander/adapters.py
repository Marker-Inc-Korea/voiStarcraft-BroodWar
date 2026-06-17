from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import CapabilityManifest, CommandStatus, IntentState, ParsedCommand


@dataclass
class AdapterResult:
    accepted: list[dict[str, Any]] = field(default_factory=list)
    degraded: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)


class BotAdapter:
    def __init__(self, manifest: CapabilityManifest) -> None:
        self.manifest = manifest

    def apply(self, state: IntentState, commands: list[ParsedCommand]) -> AdapterResult:
        result = AdapterResult()
        for command in commands:
            supported, reason = self.manifest.supports(state.contract.race, command)
            if not supported:
                state.memory.record(command, CommandStatus.DEGRADED, reason)
                result.degraded.append(command.to_event(CommandStatus.DEGRADED, reason))
                continue
            status = state.accept(command, self.manifest)
            result.accepted.append(command.to_event(status))
        return result

    def runtime_payload(self, state: IntentState) -> dict[str, Any]:
        """Payload shape expected by a BWAPI bot on its frame tick command poll."""
        return {
            "backend": self.manifest.backend_name,
            "integration_level": self.manifest.integration_level,
            "contract": state.telemetry_snapshot(),
            "active_commands": [command.to_event(CommandStatus.ACTIVE) for command in state.memory.active.values()],
        }
