from pathlib import Path

from voi_bw_commander.audit import audit_source_tree
from voi_bw_commander.replay_report import build_report
from voi_bw_commander.telemetry import TelemetryLog


def test_telemetry_report_counts_statuses(tmp_path) -> None:
    log = TelemetryLog(tmp_path / "telemetry.jsonl")
    log.write("command_status", {"status": "fulfilled"})
    log.write("command_status", {"status": "degraded"})
    log.write("intent_adherence", {"score": 0.8})

    report = build_report(log.read())

    assert report.command_fulfillment_rate == 0.5
    assert report.intent_adherence_score == 0.8
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
