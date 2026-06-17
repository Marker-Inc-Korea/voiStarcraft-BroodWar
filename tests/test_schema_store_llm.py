import json

import pytest

from voi_bw_commander.llm import StrictLLMCommandParser
from voi_bw_commander.models import CommandUtterance, IntentState, ParsedCommand
from voi_bw_commander.parser import parse_utterance
from voi_bw_commander.schema import SchemaError, parse_command_dict
from voi_bw_commander.store import StateStore


def test_command_round_trip_schema() -> None:
    [command] = [item for item in parse_utterance(CommandUtterance(text="드론 5개 더")) if item.action == "produce_worker"]
    hydrated = parse_command_dict(command.to_dict())

    assert isinstance(hydrated, ParsedCommand)
    assert hydrated.action == "produce_worker"
    assert hydrated.payload["count"] == 5


def test_llm_parser_rejects_invalid_json() -> None:
    with pytest.raises(SchemaError):
        StrictLLMCommandParser().parse_json("{not json")


def test_llm_parser_accepts_valid_command_json() -> None:
    command = parse_utterance(CommandUtterance(text="공격적으로"))[0]
    parsed = StrictLLMCommandParser().parse_json(json.dumps(command.to_dict()))

    assert parsed[0].action == "set_style"


def test_state_store_round_trip(tmp_path) -> None:
    state = IntentState()
    store = StateStore(tmp_path / "state.json")
    state.version = 7
    store.save(state)

    assert store.load().version == 7
