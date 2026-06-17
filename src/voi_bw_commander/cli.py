from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import BotAdapter
from .arbiter import ActionCandidate, IntentArbiter
from .backends import BACKEND_CANDIDATES, default_manifest
from .models import CommandStatus, CommandUtterance, IntentState
from .parser import parse_utterance
from .queue import CommandQueue, command_to_dict
from .safety import SafetyPolicy
from .verifier import Verifier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="voi-bw-commander")
    sub = parser.add_subparsers(dest="command", required=True)

    parse_cmd = sub.add_parser("parse", help="Parse a natural-language command into Command DSL JSON.")
    parse_cmd.add_argument("text")
    parse_cmd.add_argument("--queue", type=Path)

    apply_cmd = sub.add_parser("apply", help="Apply a natural-language command to an intent state.")
    apply_cmd.add_argument("text")

    sub.add_parser("candidates", help="Print backend commandability candidates.")

    verify_cmd = sub.add_parser("verify-demo", help="Run a deterministic verifier demo.")
    verify_cmd.add_argument("text")

    args = parser.parse_args(argv)
    if args.command == "parse":
        return _parse(args.text, args.queue)
    if args.command == "apply":
        return _apply(args.text)
    if args.command == "candidates":
        return _candidates()
    if args.command == "verify-demo":
        return _verify_demo(args.text)
    raise AssertionError("unreachable")


def _parse(text: str, queue_path: Path | None) -> int:
    commands = parse_utterance(CommandUtterance(text=text))
    payload = [command_to_dict(command) for command in commands]
    if queue_path:
        CommandQueue(queue_path).append(commands)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _apply(text: str) -> int:
    state = IntentState()
    manifest = default_manifest()
    adapter = BotAdapter(manifest)
    policy = SafetyPolicy()
    commands = parse_utterance(CommandUtterance(text=text))
    safe_commands = []
    for command in commands:
        decision = policy.evaluate(state, command)
        if decision.status == CommandStatus.ACCEPTED:
            safe_commands.append(command)
        else:
            state.memory.record(command, decision.status, decision.reason)
    result = adapter.apply(state, safe_commands)
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


if __name__ == "__main__":
    raise SystemExit(main())
