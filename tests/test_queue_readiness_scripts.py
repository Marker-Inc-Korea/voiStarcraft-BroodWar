import subprocess
import sys

from voi_bw_commander.models import CommandUtterance
from voi_bw_commander.parser import parse_utterance
from voi_bw_commander.queue import CommandQueue
from voi_bw_commander.readiness import check_runtime


def test_queue_round_trips_parsed_commands(tmp_path) -> None:
    queue = CommandQueue(tmp_path / "commands.jsonl")
    commands = parse_utterance(CommandUtterance(text="저그 드론 5개 더"))
    queue.append(commands)

    hydrated = queue.read_commands()

    assert [command.action for command in hydrated] == [command.action for command in commands]


def test_repository_readiness_passes() -> None:
    report = check_runtime(__import__("pathlib").Path.cwd())

    assert report.ready


def test_purplewave_patch_script_dry_run() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/apply_purplewave_integration.py", "third_party/PurpleWave", "--dry-run"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "patch lifecycle" in result.stdout
