from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuditFinding:
    area: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class AuditReport:
    backend: str
    findings: tuple[AuditFinding, ...]

    @property
    def promotable(self) -> bool:
        required = {"build", "strategy", "production", "squad", "runtime_input", "telemetry"}
        passed = {finding.area for finding in self.findings if finding.passed}
        return required.issubset(passed)

    def to_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "promotable": self.promotable,
            "findings": [finding.__dict__ for finding in self.findings],
        }


@dataclass(frozen=True)
class CommandabilityDecision:
    backend: str
    role: str
    integration_level: int
    primary_candidate: bool
    rationale: str
    forbidden_integration_modes: tuple[str, ...] = ("external_unit_control",)

    def to_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "role": self.role,
            "integration_level": self.integration_level,
            "primary_candidate": self.primary_candidate,
            "rationale": self.rationale,
            "forbidden_integration_modes": list(self.forbidden_integration_modes),
        }


def decide_commandability(report: AuditReport) -> CommandabilityDecision:
    if report.promotable:
        return CommandabilityDecision(
            backend=report.backend,
            role="commandable_backend",
            integration_level=3,
            primary_candidate=True,
            rationale="source tree exposes build, strategy, production, squad, runtime input, and telemetry indicators",
        )
    missing = [finding.area for finding in report.findings if not finding.passed]
    return CommandabilityDecision(
        backend=report.backend,
        role="benchmark_only",
        integration_level=0,
        primary_candidate=False,
        rationale=f"missing source-level command hooks: {', '.join(missing)}",
    )


def audit_source_tree(backend: str, root: Path) -> AuditReport:
    files = [path for path in root.rglob("*") if path.is_file()] if root.exists() else []
    names = " ".join(path.name.lower() for path in files)
    contents = ""
    for path in files[:200]:
        if path.suffix.lower() in {".cpp", ".h", ".hpp", ".java", ".scala", ".txt", ".md"}:
            try:
                contents += "\n" + path.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                pass
    haystack = names + "\n" + contents
    checks = {
        "build": ["cmakelists", ".sln", "build.gradle", ".sbt", "makefile", "pom.xml"],
        "strategy": ["strategy", "opening", "buildorder", "build order"],
        "production": ["production", "queue", "train", "morph"],
        "squad": ["squad", "combat", "attack", "retreat"],
        "micro": ["micro", "target", "kite", "danger"],
        "runtime_input": ["onsendtext", "socket", "command", "json", "file"],
        "telemetry": ["log", "telemetry", "event", "replay"],
    }
    findings = []
    for area, tokens in checks.items():
        matched = [token for token in tokens if token in haystack]
        findings.append(
            AuditFinding(
                area=area,
                passed=bool(matched),
                evidence=", ".join(matched) if matched else "no matching source indicators",
            )
        )
    return AuditReport(backend=backend, findings=tuple(findings))
