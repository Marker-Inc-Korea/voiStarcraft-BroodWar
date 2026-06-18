import json
import os
import subprocess
import sys
import urllib.request

from voi_bw_commander.input_surfaces import ingest_transcript, render_commander_ui
from voi_bw_commander.llm import LLMProviderConfig, OpenAICompatibleCommandParser
from voi_bw_commander.queue import CommandQueue
from voi_bw_commander.replay_ingest import ingest_replay_metrics, write_ingested_events
from voi_bw_commander.source_hooks import HOOK_PLANS, get_hook_plan, write_hook_plan
from voi_bw_commander.stardata import extract_trajectory_features


def test_source_hook_plans_cover_required_backends_and_areas(tmp_path) -> None:
    required_backends = {"McRave", "Stardust", "Ecgberht", "Steamhammer", "PurpleWave"}
    required_areas = {"on_frame", "strategy", "production", "squad", "micro", "telemetry"}

    assert required_backends.issubset(HOOK_PLANS)
    for backend in required_backends:
        plan = get_hook_plan(backend)
        assert {hook.area for hook in plan.hooks} == required_areas
        assert "Source-Level Hook Plan" in plan.render_markdown()

    path = write_hook_plan("Steamhammer", tmp_path)
    assert path.exists()
    assert "ProductionManager" in path.read_text(encoding="utf-8")


def test_openai_compatible_parser_uses_strict_gate() -> None:
    command_json = {
        "command_type": "persistent_style",
        "action": "set_style",
        "payload": {"style": {"aggression": 0.85}},
    }

    def requester(request: urllib.request.Request, timeout_seconds: float) -> bytes:
        assert request.headers["Authorization"] == "Bearer test-key"
        assert timeout_seconds == 3
        return json.dumps({"choices": [{"message": {"content": json.dumps(command_json)}}]}).encode("utf-8")

    parser = OpenAICompatibleCommandParser(
        LLMProviderConfig(api_key="test-key", model="test-model", timeout_seconds=3),
        requester=requester,
    )

    [command] = parser.parse_text("공격적으로 가")

    assert command.action == "set_style"
    assert command.payload["style"]["aggression"] == 0.85


def test_replay_metric_ingest_normalizes_csv_and_writes_jsonl(tmp_path) -> None:
    source = tmp_path / "metrics.csv"
    source.write_text(
        "frame,metric,value,status,command_id,action\n"
        "24,intent_adherence_score,0.82,,,\n"
        "48,command_status,1,fulfilled,cmd_1,produce_worker\n",
        encoding="utf-8",
    )

    result = ingest_replay_metrics(source)
    output = tmp_path / "telemetry.jsonl"
    write_ingested_events(result, output)

    assert result.events[0]["event_type"] == "intent_adherence"
    assert result.events[0]["payload"]["score"] == 0.82
    assert result.events[1]["event_type"] == "command_status"
    assert "produce_worker" in output.read_text(encoding="utf-8")


def test_transcript_ingest_and_static_ui(tmp_path) -> None:
    queue_path = tmp_path / "commands.jsonl"
    result = ingest_transcript("저그 드론 5개 더", queue_path)
    ui = render_commander_ui(queue_path)

    assert result.command_count >= 2
    assert CommandQueue(queue_path).read_commands()
    assert "Intent Commander" in ui
    assert str(queue_path) in ui


def test_stardata_feature_extraction_from_jsonl(tmp_path) -> None:
    source = tmp_path / "trajectories.jsonl"
    source.write_text(
        json.dumps(
            {
                "game_id": "g1",
                "race": "Zerg",
                "attacks": 12,
                "worker_harass": 8,
                "expansions": 3,
                "static_defense": 1,
                "contain_uptime": 0.4,
                "army_supply": 60,
                "worker_count": 45,
                "frames": 24 * 60 * 12,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    [features] = extract_trajectory_features(source)

    assert features.game_id == "g1"
    assert features.harass > 0.6
    assert features.to_dict()["labels"]["greed"] > 0


def test_new_cli_surfaces_smoke(tmp_path) -> None:
    env = {**os.environ, "PYTHONPATH": "src"}
    queue = tmp_path / "commands.jsonl"
    ui = tmp_path / "commander.html"
    metrics = tmp_path / "metrics.jsonl"
    metrics.write_text(json.dumps({"metric": "intent_adherence_score", "value": 0.7}) + "\n", encoding="utf-8")

    hook = subprocess.run(
        [sys.executable, "-m", "voi_bw_commander.cli", "hook-plan", "--backend", "McRave"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    transcript = subprocess.run(
        [
            sys.executable,
            "-m",
            "voi_bw_commander.cli",
            "transcript",
            "--text",
            "저그 드론 5개 더",
            "--queue",
            str(queue),
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    subprocess.run(
        [sys.executable, "-m", "voi_bw_commander.cli", "write-ui", "--output", str(ui), "--queue", str(queue)],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    replay = subprocess.run(
        [sys.executable, "-m", "voi_bw_commander.cli", "replay-ingest", str(metrics)],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    stardata = subprocess.run(
        [sys.executable, "-m", "voi_bw_commander.cli", "stardata-features", str(metrics)],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert "McRave" in hook.stdout
    assert "command_count" in transcript.stdout
    assert ui.exists()
    assert "intent_adherence" in replay.stdout
    assert "feature_count" in stardata.stdout
