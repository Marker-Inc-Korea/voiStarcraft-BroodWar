from pathlib import Path

from voi_bw_commander.audit import audit_source_tree, decide_commandability
from voi_bw_commander.replay_report import build_report, compare_reports
from voi_bw_commander.telemetry import TelemetryLog


def test_telemetry_report_counts_statuses(tmp_path) -> None:
    log = TelemetryLog(tmp_path / "telemetry.jsonl")
    log.write("command_status", {"status": "fulfilled"})
    log.write("command_status", {"status": "degraded"})
    log.write("command_status", {"status": "blocked"})
    log.write("command_status", {"status": "active", "category": "style_conflict"})
    log.write("intent_adherence", {"score": 0.8})

    report = build_report(log.read())

    assert report.command_fulfillment_rate == 0.25
    assert report.intent_adherence_score == 0.8
    assert report.blocked_count == 1
    assert report.conflict_count == 1
    assert report.degraded_count == 1


def test_audit_source_tree_detects_hooks(tmp_path: Path) -> None:
    source = tmp_path / "StrategyManager.cpp"
    source.write_text(
        "BuildOrder strategy production queue squad combat retreat command telemetry log",
        encoding="utf-8",
    )
    (tmp_path / "CMakeLists.txt").write_text("add_executable(fake StrategyManager.cpp)", encoding="utf-8")

    report = audit_source_tree("FakeBot", tmp_path)

    assert report.promotable
    decision = decide_commandability(report)
    assert decision.role == "commandable_backend"
    assert decision.primary_candidate


def test_commandability_decision_keeps_missing_hooks_as_benchmark(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("strong bot binary only", encoding="utf-8")

    report = audit_source_tree("StrongBinaryOnly", tmp_path)
    decision = decide_commandability(report)

    assert decision.role == "benchmark_only"
    assert not decision.primary_candidate
    assert "external_unit_control" in decision.forbidden_integration_modes


def test_compare_reports_computes_commanded_deltas(tmp_path) -> None:
    baseline = TelemetryLog(tmp_path / "baseline.jsonl")
    commanded = TelemetryLog(tmp_path / "commanded.jsonl")
    baseline.write("intent_adherence", {"score": 0.4})
    baseline.write("command_status", {"status": "fulfilled"})
    commanded.write("intent_adherence", {"score": 0.8})
    commanded.write("command_status", {"status": "fulfilled"})
    commanded.write("command_status", {"status": "unsafe"})
    commanded.write("command_status", {"status": "degraded"})

    report = compare_reports(baseline.read(), commanded.read())

    assert report.adherence_delta == 0.4
    assert report.safety_override_delta == 1
    assert report.degraded_delta == 1
