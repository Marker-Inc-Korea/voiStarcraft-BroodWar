from __future__ import annotations

from dataclasses import dataclass

from .models import BackendCapability, CapabilityManifest, Race


@dataclass(frozen=True)
class BackendCandidate:
    name: str
    language: str
    role: str
    expected_level: str
    rationale: str


BACKEND_CANDIDATES: tuple[BackendCandidate, ...] = (
    BackendCandidate(
        "PurpleWave",
        "Scala",
        "all-race fallback / benchmark-quality candidate",
        "2-4 after source audit",
        "Strong all-race profile; commandability depends on source hook effort.",
    ),
    BackendCandidate(
        "Steamhammer",
        "C++",
        "all-race production vertical slice candidate",
        "3-5",
        "C++ all-race bot suitable for adapter experimentation.",
    ),
    BackendCandidate(
        "McRave",
        "C++",
        "Zerg primary commandable candidate",
        "3-5",
        "Strong Zerg candidate if production/squad/micro hooks are accessible.",
    ),
    BackendCandidate(
        "Stardust",
        "C++",
        "Protoss primary commandable candidate",
        "3-5",
        "Protoss full-game BWAPI bot with source-level integration potential.",
    ),
    BackendCandidate(
        "Ecgberht",
        "Java",
        "Terran primary candidate",
        "2-4",
        "Terran bot using BWAPI4J; language boundary increases integration cost.",
    ),
    BackendCandidate(
        "LetaBot",
        "C++",
        "Terran secondary candidate",
        "2-4",
        "Terran bot candidate for source-level audit.",
    ),
    BackendCandidate(
        "SAIDA",
        "C++",
        "Terran benchmark-first",
        "0-1 until source hooks are proven",
        "Strong benchmark candidate; commandability must be proven.",
    ),
    BackendCandidate(
        "Iron",
        "C++",
        "Terran benchmark-first",
        "0-1 until source hooks are proven",
        "Strong Terran benchmark; commandability must be proven.",
    ),
)


def default_manifest(name: str = "SteamhammerVerticalSlice") -> CapabilityManifest:
    return CapabilityManifest(
        backend_name=name,
        race_support={Race.ZERG, Race.PROTOSS, Race.TERRAN},
        capabilities={
            BackendCapability.LAUNCH_CONFIG,
            BackendCapability.PERSISTENT_STYLE,
            BackendCapability.OBJECTIVE_INJECTION,
            BackendCapability.FULL_TELEMETRY,
        },
        supported_actions={
            "set_race",
            "produce_worker",
            "set_style",
            "commit_strategy",
            "attack",
            "retreat",
            "patch_contract",
        },
        integration_level=3,
        notes="Local vertical-slice manifest. Real bot hooks require commandability audit.",
    )
