from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .runner import MatchSpec


@dataclass(frozen=True)
class BenchmarkOpponent:
    name: str
    race: str
    role: str
    commandable: bool


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    baseline: MatchSpec
    commanded: MatchSpec
    expected_outputs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "baseline_plan": self.baseline.to_command_plan(),
            "commanded_plan": self.commanded.to_command_plan(),
            "expected_outputs": list(self.expected_outputs),
        }


BENCHMARK_POOL: tuple[BenchmarkOpponent, ...] = (
    BenchmarkOpponent("PurpleWave", "All", "fallback and strength benchmark", True),
    BenchmarkOpponent("Steamhammer", "All", "vertical-slice benchmark", True),
    BenchmarkOpponent("McRave", "Zerg", "Zerg strength benchmark", True),
    BenchmarkOpponent("Stardust", "Protoss", "Protoss strength benchmark", True),
    BenchmarkOpponent("Locutus", "Protoss", "Protoss secondary benchmark", True),
    BenchmarkOpponent("SAIDA", "Terran", "Terran strong benchmark", False),
    BenchmarkOpponent("Iron", "Terran", "Terran strong benchmark", False),
)


def build_regression_suite(
    bot: str,
    race: str,
    map_name: str,
    root: Path,
    opponents: tuple[str, ...] = ("PurpleWave", "Steamhammer"),
) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    for opponent in opponents:
        case_root = root / f"{bot}_vs_{opponent}_{race}_{map_name}"
        cases.append(
            BenchmarkCase(
                name=f"{bot}_vs_{opponent}_{race}_{map_name}",
                baseline=MatchSpec(
                    bot=bot,
                    opponent=opponent,
                    race=race,
                    map_name=map_name,
                    command_queue=case_root / "baseline" / "commands.jsonl",
                    telemetry_log=case_root / "baseline" / "telemetry.jsonl",
                ),
                commanded=MatchSpec(
                    bot=bot,
                    opponent=opponent,
                    race=race,
                    map_name=map_name,
                    command_queue=case_root / "commanded" / "commands.jsonl",
                    telemetry_log=case_root / "commanded" / "telemetry.jsonl",
                ),
                expected_outputs=(
                    "baseline replay",
                    "commanded replay",
                    "telemetry JSONL",
                    "crash log if process exits non-zero",
                    "desync marker if replay hash diverges",
                    "compare-report JSON",
                ),
            )
        )
    return cases
