from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import CommandStatus, CommandType, IntentState, ParsedCommand


@dataclass(frozen=True)
class SafetyDecision:
    status: CommandStatus
    reason: str = ""
    category: str = "accepted"
    details: dict[str, Any] | None = None


class SafetyPolicy:
    """Conflict and safety policy before commands reach the bot adapter."""

    def evaluate(
        self,
        state: IntentState,
        command: ParsedCommand,
        game_state: dict[str, Any] | None = None,
    ) -> SafetyDecision:
        game_state = game_state or {}

        if command.action == "unparsed":
            return SafetyDecision(
                CommandStatus.INVALID,
                "command could not be parsed",
                "invalid",
                {"requires_clarification": True},
            )

        if command.action == "attack" and game_state.get("enemy_army_supply_advantage", 0) >= 30:
            return SafetyDecision(
                CommandStatus.UNSAFE,
                "enemy army supply advantage too high for forced attack",
                "survival_override",
                {"enemy_army_supply_advantage": game_state["enemy_army_supply_advantage"]},
            )

        if command.command_type == CommandType.HARD_GOAL and game_state.get("emergency_defense"):
            if command.action in {"produce_worker", "take_expansion"}:
                return SafetyDecision(
                    CommandStatus.BLOCKED,
                    "economic hard goal blocked during emergency defense",
                    "emergency_defense",
                    {"blocked_action": command.action},
                )

        if command.command_type == CommandType.PERSISTENT_STYLE:
            requested = command.payload.get("style", {})
            current = state.contract.style
            if requested.get("aggression", 0) >= 0.8 and current.get("defensive_safety", 0) >= 0.8:
                return SafetyDecision(
                    CommandStatus.ACCEPTED,
                    "aggression accepted; arbiter will balance against defensive safety",
                    "style_conflict",
                    {
                        "requested_aggression": requested.get("aggression"),
                        "current_defensive_safety": current.get("defensive_safety"),
                    },
                )

        return SafetyDecision(CommandStatus.ACCEPTED)
