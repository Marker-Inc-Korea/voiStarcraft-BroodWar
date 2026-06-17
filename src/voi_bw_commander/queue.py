from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import ParsedCommand, VerifierExpectation
from .schema import parse_command_dict


def command_to_dict(command: ParsedCommand) -> dict[str, Any]:
    data = asdict(command)
    data["command_type"] = command.command_type.value
    data["priority"] = command.priority.value
    data["expectations"] = [asdict(expectation) for expectation in command.expectations]
    return data


class CommandQueue:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, commands: list[ParsedCommand]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            for command in commands:
                handle.write(json.dumps(command_to_dict(command), ensure_ascii=False, sort_keys=True))
                handle.write("\n")

    def read_raw(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        items: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items

    def read_commands(self) -> list[ParsedCommand]:
        return [parse_command_dict(item) for item in self.read_raw()]

    def clear(self) -> None:
        self.path.write_text("", encoding="utf-8")
