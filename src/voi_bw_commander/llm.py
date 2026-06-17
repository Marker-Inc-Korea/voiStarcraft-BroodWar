from __future__ import annotations

import json

from .models import ParsedCommand
from .schema import SchemaError, parse_command_dict


class StrictLLMCommandParser:
    """Validates LLM JSON output before it can reach runtime state."""

    def parse_json(self, content: str) -> list[ParsedCommand]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise SchemaError(f"invalid JSON from LLM: {exc}") from exc
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise SchemaError("LLM output must be a command object or list of command objects")
        return [parse_command_dict(item) for item in data]
