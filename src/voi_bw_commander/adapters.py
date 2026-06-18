from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import CapabilityManifest, CommandStatus, IntentState, ParsedCommand, Race
from .race_profiles import get_profile


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


class RaceAwareBotAdapter(BotAdapter):
    def __init__(self, manifest: CapabilityManifest, race: Race) -> None:
        super().__init__(manifest)
        self.race = race
        self.profile = get_profile(race)

    def apply(self, state: IntentState, commands: list[ParsedCommand]) -> AdapterResult:
        result = AdapterResult()
        for command in commands:
            resolution = self.profile.resolve_command(command)
            if not resolution.valid:
                state.memory.record(command, CommandStatus.INVALID, resolution.reason)
                result.rejected.append(command.to_event(CommandStatus.INVALID, resolution.reason))
                continue
            command.payload.update(resolution.resolved_payload)
            supported, reason = self.manifest.supports(self.race, command)
            if not supported:
                state.memory.record(command, CommandStatus.DEGRADED, reason)
                result.degraded.append(command.to_event(CommandStatus.DEGRADED, reason))
                continue
            status = state.accept(command, self.manifest)
            result.accepted.append(command.to_event(status))
        return result


def create_race_adapter(manifest: CapabilityManifest, race: Race) -> RaceAwareBotAdapter:
    return RaceAwareBotAdapter(manifest, race)
