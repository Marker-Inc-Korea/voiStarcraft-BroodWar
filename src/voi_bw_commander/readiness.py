from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ReadinessReport:
    checks: tuple[ReadinessCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {"ready": self.ready, "checks": [check.__dict__ for check in self.checks]}


def check_runtime(root: Path) -> ReadinessReport:
    checks = (
        _exists("command schema", root / "schemas" / "command.schema.json"),
        _exists("commander package", root / "src" / "voi_bw_commander"),
        _exists("PurpleWave integration templates", root / "integrations" / "purplewave"),
        _exists("bot bridge template", root / "bot_bridge" / "CommanderBridge.hpp"),
        _exists("runtime docs", root / "docs" / "RUNTIME.md"),
        _exists("verification script", root / "scripts" / "verify_local.sh"),
        _exists("parser corpus", root / "fixtures" / "parser_corpus.json"),
        _exists("CI workflow", root / ".github" / "workflows" / "ci.yml"),
        _exists("issue completion matrix", root / "docs" / "ISSUE_COMPLETION_MATRIX.md"),
        _exists("source hook plans", root / "src" / "voi_bw_commander" / "source_hooks.py"),
        _exists("replay metric ingestion", root / "src" / "voi_bw_commander" / "replay_ingest.py"),
        _exists("input surfaces", root / "src" / "voi_bw_commander" / "input_surfaces.py"),
        _exists("StarData representation", root / "src" / "voi_bw_commander" / "stardata.py"),
        _exists("commander UI template", root / "ui" / "commander.html"),
    )
    return ReadinessReport(checks)


def _exists(name: str, path: Path) -> ReadinessCheck:
    return ReadinessCheck(name=name, passed=path.exists(), detail=str(path))
