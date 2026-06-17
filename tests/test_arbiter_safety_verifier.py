from voi_bw_commander.adapters import BotAdapter
from voi_bw_commander.arbiter import ActionCandidate, IntentArbiter
from voi_bw_commander.backends import default_manifest
from voi_bw_commander.models import CommandStatus, CommandUtterance, IntentState
from voi_bw_commander.parser import parse_utterance
from voi_bw_commander.safety import SafetyPolicy
from voi_bw_commander.verifier import Verifier


def test_arbiter_biases_toward_worker_goal_and_harass_style() -> None:
    state = IntentState()
    BotAdapter(default_manifest()).apply(
        state,
        parse_utterance(CommandUtterance(text="드론 5개 더 침략적으로 견제")),
    )

    choice = IntentArbiter().choose(
        state,
        [
            ActionCandidate("train_worker", 0.7, ("worker",)),
            ActionCandidate("harass_workers", 0.6, ("attack", "harass")),
        ],
    )

    assert choice.action in {"train_worker", "harass_workers"}
    assert choice.final_score > 1.0


def test_safety_blocks_forced_attack_when_enemy_advantage_is_large() -> None:
    state = IntentState()
    [command] = parse_utterance(CommandUtterance(text="지금 공격해"))
    decision = SafetyPolicy().evaluate(state, command, {"enemy_army_supply_advantage": 40})

    assert decision.status == CommandStatus.UNSAFE


def test_verifier_scores_expectations() -> None:
    state = IntentState()
    BotAdapter(default_manifest()).apply(state, parse_utterance(CommandUtterance(text="드론 5개 더 침략적으로")))

    result = Verifier().verify(state, {"worker_delta": 5, "intent_adherence_score": 0.7})

    assert result.passed
    assert result.score == 1.0
