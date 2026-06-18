from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import BotAdapter
from .audit import audit_source_tree, decide_commandability
from .arbiter import ActionCandidate, IntentArbiter
from .backends import BACKEND_CANDIDATES, default_manifest
from .benchmark import build_regression_suite
from .eval import evaluate_corpus
from .llm import StrictLLMCommandParser
from .models import CommandStatus, CommandUtterance, IntentState
from .parser import parse_utterance
from .queue import CommandQueue, command_to_dict
from .readiness import check_runtime
from .replay_report import build_report, compare_reports
from .runner import MatchSpec
from .safety import SafetyPolicy
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
    print(json.dumps([candidate.__dict__ for candidate in BACKEND_CANDIDATES], ensure_ascii=False, indent=2))
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


if __name__ == "__main__":
    raise SystemExit(main())
