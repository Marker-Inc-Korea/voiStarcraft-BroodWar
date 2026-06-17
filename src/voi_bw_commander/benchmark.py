from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkOpponent:
    name: str
    race: str
    role: str
    commandable: bool


BENCHMARK_POOL: tuple[BenchmarkOpponent, ...] = (
    BenchmarkOpponent("PurpleWave", "All", "fallback and strength benchmark", True),
    BenchmarkOpponent("Steamhammer", "All", "vertical-slice benchmark", True),
    BenchmarkOpponent("McRave", "Zerg", "Zerg strength benchmark", True),
    BenchmarkOpponent("Stardust", "Protoss", "Protoss strength benchmark", True),
    BenchmarkOpponent("Locutus", "Protoss", "Protoss secondary benchmark", True),
    BenchmarkOpponent("SAIDA", "Terran", "Terran strong benchmark", False),
    BenchmarkOpponent("Iron", "Terran", "Terran strong benchmark", False),
)
