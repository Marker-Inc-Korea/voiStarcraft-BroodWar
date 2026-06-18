from voi_bw_commander.models import CommandType, CommandUtterance
from voi_bw_commander.parser import parse_utterance


def test_parse_korean_complex_zerg_command() -> None:
    commands = parse_utterance(
        CommandUtterance(
            text="저그로 해. 드론 5개 더 찍고 2햇 뮤탈. 침략적으로 가되 정면 싸움은 피하고 일꾼만 흔들어."
        )
    )

    actions = {command.action for command in commands}
    types = {command.command_type for command in commands}

    assert "set_race" in actions
    assert "produce_worker" in actions
    assert "set_style" in actions
    assert "commit_strategy" in actions
    assert "set_micro_doctrine" in actions
    assert CommandType.CONTRACT_PATCH in types


def test_unparsed_command_requires_clarification() -> None:
    [command] = parse_utterance(CommandUtterance(text="뭔가 멋지게 해봐"))

    assert command.action == "unparsed"
    assert command.payload["requires_clarification"] is True
    assert command.ambiguity_score == 1.0


def test_parse_contract_patch_with_expansion_goal() -> None:
    commands = parse_utterance(CommandUtterance(text="아까 침략 스타일 유지하되 이제 3멀티는 먹어"))

    expansion = next(command for command in commands if command.action == "take_expansion")
    patch = next(command for command in commands if command.action == "patch_contract")

    assert expansion.payload["base_number"] == 3
    assert expansion.expectations[0].metric == "owned_bases"
    assert patch.payload["preserve_existing"] is True


def test_parse_cancel_strategy_command() -> None:
    [command] = parse_utterance(CommandUtterance(text="2햇 뮤탈 취소해"))

    assert command.action == "cancel_intent"
    assert command.payload == {"target_action": "commit_strategy", "target_plan": "two_hatch_muta"}
    assert command.expectations[0].metric == "cancelled_command_count"
