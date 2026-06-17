from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import CommandStatus, CommandType, IntentState, ParsedCommand


@dataclass(frozen=True)
class SafetyDecision:
    status: CommandStatus
    reason: str = ""


class SafetyPolicy:
    """Conflict and safety policy before commands reach the bot adapter."""

    def evaluate(self, state: IntentState, command: ParsedCommand, game_state: dict[str, Any] | None = None) -> SafetyDecision:
        game_state = game_state or {}

        if command.action == "unparsed":
            return SafetyDecision(CommandStatus.INVALID, "command could not be parsed")

        if command.action == "attack" and game_state.get("enemy_army_supply_advantage", 0) >= 30:
            return SafetyDecision(CommandStatus.UNSAFE, "enemy army supply advantage too high for forced attack")

        if command.command_type == CommandType.PERSISTENT_STYLE:
            requested = command.payload.get("style", {})
            current = state.contract.style
            if requested.get("aggression", 0) >= 0.8 and current.get("defensive_safety", 0) >= 0.8:
                return SafetyDecision(
                    CommandStatus.ACCEPTED,
                    "aggression accepted; arbiter will balance against defensive safety",
                )

        return SafetyDecision(CommandStatus.ACCEPTED)
