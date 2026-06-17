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
