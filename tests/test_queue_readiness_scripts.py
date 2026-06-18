import os
import subprocess
import sys

from voi_bw_commander.models import CommandUtterance
from voi_bw_commander.parser import parse_utterance
from voi_bw_commander.queue import CommandQueue
from voi_bw_commander.readiness import check_runtime
from voi_bw_commander.store import StateStore


def test_queue_round_trips_parsed_commands(tmp_path) -> None:
    queue = CommandQueue(tmp_path / "commands.jsonl")
    commands = parse_utterance(CommandUtterance(text="저그 드론 5개 더"))
    queue.append(commands)

    hydrated = queue.read_commands()

    assert [command.action for command in hydrated] == [command.action for command in commands]


def test_repository_readiness_passes() -> None:
    report = check_runtime(__import__("pathlib").Path.cwd())

    assert report.ready
    names = {check.name for check in report.checks}
    assert "CI workflow" in names
    assert "parser corpus" in names


def test_state_store_replays_persisted_contract(tmp_path) -> None:
    from voi_bw_commander.adapters import BotAdapter
    from voi_bw_commander.backends import default_manifest
    from voi_bw_commander.models import IntentState

    store = StateStore(tmp_path / "state.json")
    state = IntentState()
    BotAdapter(default_manifest()).apply(state, parse_utterance(CommandUtterance(text="저그 드론 5개 더")))
    store.save(state)

    replayed = store.load()

    assert replayed.contract.race.value == "Zerg"
    assert replayed.contract.hard_goals
    assert replayed.memory.active


def test_purplewave_patch_script_dry_run() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/apply_purplewave_integration.py", "third_party/PurpleWave", "--dry-run"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "patch lifecycle" in result.stdout


def test_cli_apply_writes_safety_stage_telemetry(tmp_path) -> None:
    telemetry = tmp_path / "telemetry.jsonl"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "voi_bw_commander.cli",
            "apply",
            "뭔가 멋지게 해봐",
            "--telemetry",
            str(telemetry),
        ],
        check=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "src"},
        text=True,
    )

    assert '"status": "invalid"' in telemetry.read_text(encoding="utf-8")
    assert '"category": "invalid"' in telemetry.read_text(encoding="utf-8")


def test_cli_benchmark_plan_includes_regression_outputs(tmp_path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "voi_bw_commander.cli",
            "benchmark-plan",
            "--bot",
            "Steamhammer",
            "--race",
            "Zerg",
            "--map",
            "FightingSpirit",
            "--root",
            str(tmp_path),
            "--opponent",
            "PurpleWave",
        ],
        check=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "src"},
        text=True,
    )

    assert "baseline_plan" in result.stdout
    assert "commanded_plan" in result.stdout
    assert "compare-report JSON" in result.stdout
    assert "desync marker" in result.stdout


def test_cli_vertical_slice_from_language_to_report(tmp_path) -> None:
    queue = tmp_path / "commands.jsonl"
    state = tmp_path / "state.json"
    telemetry = tmp_path / "telemetry.jsonl"
    env = {**os.environ, "PYTHONPATH": "src"}

    subprocess.run(
        [
            sys.executable,
            "-m",
            "voi_bw_commander.cli",
            "parse",
            "저그 드론 5개 더 2햇 뮤탈 견제 일꾼만",
            "--queue",
            str(queue),
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "voi_bw_commander.cli",
            "apply",
            "저그 드론 5개 더 2햇 뮤탈 견제 일꾼만",
            "--state",
            str(state),
            "--telemetry",
            str(telemetry),
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    report = subprocess.run(
        [sys.executable, "-m", "voi_bw_commander.cli", "report", str(telemetry)],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert queue.exists()
    assert state.exists()
    assert telemetry.exists()
    assert "command_fulfillment_rate" in report.stdout
    assert "degraded_count" in report.stdout
