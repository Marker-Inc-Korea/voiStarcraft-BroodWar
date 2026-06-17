from __future__ import annotations

from typing import Any

from .models import CommandType, IntentPriority, ParsedCommand


class SchemaError(ValueError):
    pass


def validate_command_dict(data: dict[str, Any]) -> None:
    required = {"command_type", "action", "payload"}
    missing = required - data.keys()
    if missing:
        raise SchemaError(f"missing required fields: {sorted(missing)}")
    try:
        CommandType(data["command_type"])
    except ValueError as exc:
        raise SchemaError(f"invalid command_type: {data['command_type']}") from exc
    if "priority" in data:
        try:
            IntentPriority(data["priority"])
        except ValueError as exc:
            raise SchemaError(f"invalid priority: {data['priority']}") from exc
    if not isinstance(data["action"], str) or not data["action"]:
        raise SchemaError("action must be a non-empty string")
    if not isinstance(data["payload"], dict):
        raise SchemaError("payload must be an object")
    if "strength" in data and not 0 <= float(data["strength"]) <= 1:
        raise SchemaError("strength must be between 0 and 1")
    for expectation in data.get("expectations", []):
        _validate_expectation(expectation)


def parse_command_dict(data: dict[str, Any]) -> ParsedCommand:
    validate_command_dict(data)
    return ParsedCommand.from_dict(data)


def _validate_expectation(data: dict[str, Any]) -> None:
    required = {"metric", "operator", "value"}
    missing = required - data.keys()
    if missing:
        raise SchemaError(f"expectation missing fields: {sorted(missing)}")
    if data["operator"] not in {">=", "<=", "==", "contains"}:
        raise SchemaError(f"invalid expectation operator: {data['operator']}")
