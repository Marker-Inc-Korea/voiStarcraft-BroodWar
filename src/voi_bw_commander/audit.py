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
        "build": ["cmakelists", ".sln", "build.gradle", "sbt", "makefile"],
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
