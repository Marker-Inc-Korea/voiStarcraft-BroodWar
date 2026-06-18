from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import BotAdapter
from .audit import audit_source_tree, decide_commandability
from .arbiter import ActionCandidate, IntentArbiter
from .backends import BACKEND_CANDIDATES, EXCLUDED_PLAYABLE_BACKENDS, default_manifest
from .benchmark import build_regression_suite
from .eval import evaluate_corpus
from .input_surfaces import ingest_transcript, ingest_transcript_file, write_commander_ui
from .llm import LLMProviderConfig, OpenAICompatibleCommandParser, StrictLLMCommandParser
from .models import CommandStatus, CommandUtterance, IntentState
from .parser import parse_utterance
from .queue import CommandQueue, command_to_dict
from .readiness import check_runtime
from .replay_ingest import ingest_replay_metrics, write_ingested_events
from .replay_report import build_report, compare_reports
from .runner import MatchSpec
from .safety import SafetyPolicy
from .source_hooks import HOOK_PLANS, get_hook_plan, write_hook_plan
from .stardata import extract_trajectory_features, write_feature_jsonl
from .store import StateStore
from .telemetry import TelemetryLog
from .verifier import Verifier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="voi-bw-commander")
    sub = parser.add_subparsers(dest="command", required=True)

    parse_cmd = sub.add_parser("parse", help="Parse a natural-language command into Command DSL JSON.")
    parse_cmd.add_argument("text")
    parse_cmd.add_argument("--queue", type=Path)

    apply_cmd = sub.add_parser("apply", help="Apply a natural-language command to an intent state.")
    apply_cmd.add_argument("text")
    apply_cmd.add_argument("--state", type=Path)
    apply_cmd.add_argument("--telemetry", type=Path)

    sub.add_parser("candidates", help="Print backend commandability candidates.")

    verify_cmd = sub.add_parser("verify-demo", help="Run a deterministic verifier demo.")
    verify_cmd.add_argument("text")

    llm_cmd = sub.add_parser("parse-llm-json", help="Validate strict LLM JSON output.")
    llm_cmd.add_argument("json_text")

    llm_live_cmd = sub.add_parser("parse-llm-live", help="Parse text through an OpenAI-compatible LLM provider.")
    llm_live_cmd.add_argument("text")

    report_cmd = sub.add_parser("report", help="Build a report from telemetry JSONL.")
    report_cmd.add_argument("telemetry", type=Path)

    compare_cmd = sub.add_parser("compare-report", help="Compare baseline and commanded telemetry JSONL reports.")
    compare_cmd.add_argument("baseline", type=Path)
    compare_cmd.add_argument("commanded", type=Path)

    audit_cmd = sub.add_parser("audit-source", help="Audit a backend source tree for commandability.")
    audit_cmd.add_argument("backend")
    audit_cmd.add_argument("path", type=Path)

    plan_cmd = sub.add_parser("match-plan", help="Print an external BWAPI match execution plan.")
    plan_cmd.add_argument("--bot", required=True)
    plan_cmd.add_argument("--opponent", required=True)
    plan_cmd.add_argument("--race", required=True)
    plan_cmd.add_argument("--map", required=True, dest="map_name")
    plan_cmd.add_argument("--queue", required=True, type=Path)
    plan_cmd.add_argument("--telemetry", required=True, type=Path)

    bench_cmd = sub.add_parser("benchmark-plan", help="Print commanded-vs-baseline benchmark regression plans.")
    bench_cmd.add_argument("--bot", required=True)
    bench_cmd.add_argument("--race", required=True)
    bench_cmd.add_argument("--map", required=True, dest="map_name")
    bench_cmd.add_argument("--root", required=True, type=Path)
    bench_cmd.add_argument("--opponent", action="append", dest="opponents")

    ready_cmd = sub.add_parser("readiness", help="Check repository-side production readiness assets.")
    ready_cmd.add_argument("--root", type=Path, default=Path.cwd())

    eval_cmd = sub.add_parser("eval-corpus", help="Evaluate parser against a golden command corpus.")
    eval_cmd.add_argument("corpus", type=Path)

    hook_cmd = sub.add_parser("hook-plan", help="Print or write source-level hook plans for backend bots.")
    hook_cmd.add_argument("--backend", choices=sorted(HOOK_PLANS), action="append")
    hook_cmd.add_argument("--output-dir", type=Path)

    replay_cmd = sub.add_parser("replay-ingest", help="Normalize replay-derived JSON/JSONL/CSV metrics into telemetry JSONL.")
    replay_cmd.add_argument("input", type=Path)
    replay_cmd.add_argument("--output", type=Path)

    transcript_cmd = sub.add_parser("transcript", help="Parse a voice/text transcript and append commands to a queue.")
    transcript_source = transcript_cmd.add_mutually_exclusive_group(required=True)
    transcript_source.add_argument("--text")
    transcript_source.add_argument("--file", type=Path)
    transcript_cmd.add_argument("--queue", required=True, type=Path)

    ui_cmd = sub.add_parser("write-ui", help="Write the static commander UI handoff page.")
    ui_cmd.add_argument("--output", required=True, type=Path)
    ui_cmd.add_argument("--queue", required=True, type=Path)

    stardata_cmd = sub.add_parser("stardata-features", help="Extract V3 intent representation features from trajectory rows.")
    stardata_cmd.add_argument("input", type=Path)
    stardata_cmd.add_argument("--output", type=Path)

    args = parser.parse_args(argv)
    if args.command == "parse":
        return _parse(args.text, args.queue)
    if args.command == "apply":
        return _apply(args.text, args.state, args.telemetry)
    if args.command == "candidates":
        return _candidates()
    if args.command == "verify-demo":
        return _verify_demo(args.text)
    if args.command == "parse-llm-json":
        return _parse_llm_json(args.json_text)
    if args.command == "parse-llm-live":
        return _parse_llm_live(args.text)
    if args.command == "report":
        return _report(args.telemetry)
    if args.command == "compare-report":
        return _compare_report(args.baseline, args.commanded)
    if args.command == "audit-source":
        return _audit_source(args.backend, args.path)
    if args.command == "match-plan":
        return _match_plan(args.bot, args.opponent, args.race, args.map_name, args.queue, args.telemetry)
    if args.command == "benchmark-plan":
        return _benchmark_plan(args.bot, args.race, args.map_name, args.root, tuple(args.opponents or ()))
    if args.command == "readiness":
        return _readiness(args.root)
    if args.command == "eval-corpus":
        return _eval_corpus(args.corpus)
    if args.command == "hook-plan":
        return _hook_plan(tuple(args.backend or sorted(HOOK_PLANS)), args.output_dir)
    if args.command == "replay-ingest":
        return _replay_ingest(args.input, args.output)
    if args.command == "transcript":
        return _transcript(args.text, args.file, args.queue)
    if args.command == "write-ui":
        return _write_ui(args.output, args.queue)
    if args.command == "stardata-features":
        return _stardata_features(args.input, args.output)
    raise AssertionError("unreachable")


def _parse(text: str, queue_path: Path | None) -> int:
    commands = parse_utterance(CommandUtterance(text=text))
    payload = [command_to_dict(command) for command in commands]
    if queue_path:
        CommandQueue(queue_path).append(commands)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _apply(text: str, state_path: Path | None = None, telemetry_path: Path | None = None) -> int:
    store = StateStore(state_path) if state_path else None
    state = store.load() if store else IntentState()
    manifest = default_manifest()
    adapter = BotAdapter(manifest)
    policy = SafetyPolicy()
    commands = parse_utterance(CommandUtterance(text=text))
    safe_commands = []
    safety_events = []
    for command in commands:
        decision = policy.evaluate(state, command)
        if decision.status == CommandStatus.ACCEPTED:
            safe_commands.append(command)
        else:
            state.memory.record(command, decision.status, decision.reason)
            event = command.to_event(decision.status, decision.reason)
            event["category"] = decision.category
            event["details"] = decision.details or {}
            safety_events.append(event)
    result = adapter.apply(state, safe_commands)
    if store:
        store.save(state)
    if telemetry_path:
        telemetry = TelemetryLog(telemetry_path)
        for event in safety_events + result.accepted + result.degraded + result.rejected:
            telemetry.write("command_status", event)
        telemetry.write("contract_snapshot", adapter.runtime_payload(state))
    arbiter = IntentArbiter()
    choice = arbiter.choose(
        state,
        [
            ActionCandidate("train_worker", 0.7, ("worker",)),
            ActionCandidate("take_third", 0.8, ("expand",)),
            ActionCandidate("harass_workers", 0.6, ("attack", "harass")),
            ActionCandidate("frontal_attack", 0.65, ("attack", "unsafe")),
        ],
    )
    print(
        json.dumps(
            {
                "adapter_result": {
                    "accepted": result.accepted,
                    "degraded": result.degraded,
                    "rejected": result.rejected,
                },
                "runtime_payload": adapter.runtime_payload(state),
                "arbiter_choice": {
                    "action": choice.action,
                    "final_score": choice.final_score,
                    "explanation": choice.explanation,
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _candidates() -> int:
    print(
        json.dumps(
            {
                "playable_candidates": [candidate.to_dict() for candidate in BACKEND_CANDIDATES],
                "excluded_playable_backends": list(EXCLUDED_PLAYABLE_BACKENDS),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _verify_demo(text: str) -> int:
    state = IntentState()
    adapter = BotAdapter(default_manifest())
    adapter.apply(state, parse_utterance(CommandUtterance(text=text)))
    telemetry = {
        "worker_delta": 5,
        "intent_adherence_score": 0.72,
        "active_strategic_commitments": ["two_hatch_muta"],
        "worker_target_ratio": 0.7,
        "main_army_avoidance_ratio": 0.8,
        "attack_orders_issued": 1,
        "retreat_orders_issued": 1,
    }
    result = Verifier().verify(state, telemetry)
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _parse_llm_json(json_text: str) -> int:
    commands = StrictLLMCommandParser().parse_json(json_text)
    print(json.dumps([command_to_dict(command) for command in commands], ensure_ascii=False, indent=2))
    return 0


def _parse_llm_live(text: str) -> int:
    commands = OpenAICompatibleCommandParser(LLMProviderConfig.from_env()).parse_text(text)
    print(json.dumps([command_to_dict(command) for command in commands], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _report(telemetry_path: Path) -> int:
    report = build_report(TelemetryLog(telemetry_path).read())
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _compare_report(baseline_path: Path, commanded_path: Path) -> int:
    report = compare_reports(TelemetryLog(baseline_path).read(), TelemetryLog(commanded_path).read())
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _audit_source(backend: str, path: Path) -> int:
    report = audit_source_tree(backend, path)
    print(
        json.dumps(
            {"audit": report.to_dict(), "decision": decide_commandability(report).to_dict()},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _match_plan(
    bot: str,
    opponent: str,
    race: str,
    map_name: str,
    queue: Path,
    telemetry: Path,
) -> int:
    spec = MatchSpec(bot=bot, opponent=opponent, race=race, map_name=map_name, command_queue=queue, telemetry_log=telemetry)
    print(json.dumps({"plan": spec.to_command_plan()}, ensure_ascii=False, indent=2))
    return 0


def _benchmark_plan(bot: str, race: str, map_name: str, root: Path, opponents: tuple[str, ...]) -> int:
    suite = build_regression_suite(bot, race, map_name, root, opponents or ("PurpleWave", "Steamhammer"))
    print(json.dumps({"cases": [case.to_dict() for case in suite]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _readiness(root: Path) -> int:
    report = check_runtime(root)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _eval_corpus(corpus: Path) -> int:
    report = evaluate_corpus(corpus)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.passed else 1


def _hook_plan(backends: tuple[str, ...], output_dir: Path | None) -> int:
    if output_dir:
        paths = [str(write_hook_plan(backend, output_dir)) for backend in backends]
        print(json.dumps({"written": paths}, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            json.dumps(
                {"plans": [get_hook_plan(backend).to_dict() for backend in backends]},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def _replay_ingest(input_path: Path, output: Path | None) -> int:
    result = ingest_replay_metrics(input_path)
    if output:
        write_ingested_events(result, output)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _transcript(text: str | None, file: Path | None, queue: Path) -> int:
    result = ingest_transcript_file(file, queue) if file else ingest_transcript(text or "", queue)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _write_ui(output: Path, queue: Path) -> int:
    path = write_commander_ui(output, queue)
    print(json.dumps({"ui": str(path), "queue": str(queue)}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _stardata_features(input_path: Path, output: Path | None) -> int:
    features = extract_trajectory_features(input_path)
    if output:
        write_feature_jsonl(features, output)
    print(
        json.dumps(
            {"feature_count": len(features), "features": [feature.to_dict() for feature in features]},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
