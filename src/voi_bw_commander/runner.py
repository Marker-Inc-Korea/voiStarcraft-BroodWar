from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MatchSpec:
    bot: str
    opponent: str
    race: str
    map_name: str
    command_queue: Path
    telemetry_log: Path

    def to_command_plan(self) -> list[str]:
        return [
            "launch Brood War 1.16.1-compatible runtime",
            f"load bot={self.bot}",
            f"load opponent={self.opponent}",
            f"set race={self.race}",
            f"set map={self.map_name}",
            f"bot polls command queue={self.command_queue}",
            f"bot writes telemetry log={self.telemetry_log}",
        ]
