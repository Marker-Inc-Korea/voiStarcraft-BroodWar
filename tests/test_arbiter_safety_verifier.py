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


def test_arbiter_applies_expansion_hard_goal_bonus() -> None:
    state = IntentState()
    BotAdapter(default_manifest()).apply(state, parse_utterance(CommandUtterance(text="이제 3멀티는 먹어")))

    choice = IntentArbiter().choose(
        state,
        [
            ActionCandidate("train_army", 0.8, ("army",)),
            ActionCandidate("take_third", 0.7, ("expand",)),
        ],
    )

    assert choice.action == "take_third"
    assert "hard_goal:take_expansion=0.90" in choice.explanation


def test_arbiter_penalizes_frontal_fight_when_doctrine_avoids_main_army() -> None:
    state = IntentState()
    BotAdapter(default_manifest()).apply(state, parse_utterance(CommandUtterance(text="정면 싸움은 피하고 일꾼만 흔들어")))

    frontal = IntentArbiter().score(state, ActionCandidate("frontal_attack", 0.9, ("attack", "frontal", "main_army")))
    harass = IntentArbiter().score(state, ActionCandidate("worker_harass", 0.7, ("attack", "harass")))

    assert harass.final_score > frontal.final_score
    assert "micro_doctrine:avoid_main_army=-1.00" in frontal.explanation


def test_safety_blocks_forced_attack_when_enemy_advantage_is_large() -> None:
    state = IntentState()
    [command] = parse_utterance(CommandUtterance(text="지금 공격해"))
    decision = SafetyPolicy().evaluate(state, command, {"enemy_army_supply_advantage": 40})

    assert decision.status == CommandStatus.UNSAFE
    assert decision.category == "survival_override"
    assert decision.details == {"enemy_army_supply_advantage": 40}


def test_safety_blocks_economic_hard_goal_during_emergency_defense() -> None:
    state = IntentState()
    [command] = parse_utterance(CommandUtterance(text="드론 5개 더"))
    decision = SafetyPolicy().evaluate(state, command, {"emergency_defense": True})

    assert decision.status == CommandStatus.BLOCKED
    assert decision.category == "emergency_defense"
    assert decision.details == {"blocked_action": "produce_worker"}


def test_safety_explains_style_conflict_without_rejecting() -> None:
    state = IntentState()
    BotAdapter(default_manifest()).apply(state, parse_utterance(CommandUtterance(text="수비적으로 안전하게")))
    style_command = next(command for command in parse_utterance(CommandUtterance(text="이제 침략적으로 가")) if command.action == "set_style")

    decision = SafetyPolicy().evaluate(state, style_command)

    assert decision.status == CommandStatus.ACCEPTED
    assert decision.category == "style_conflict"
    assert "arbiter will balance" in decision.reason


def test_verifier_scores_expectations() -> None:
    state = IntentState()
    BotAdapter(default_manifest()).apply(state, parse_utterance(CommandUtterance(text="드론 5개 더 침략적으로")))

    result = Verifier().verify(state, {"worker_delta": 5, "intent_adherence_score": 0.7})

    assert result.passed
    assert result.score == 1.0
