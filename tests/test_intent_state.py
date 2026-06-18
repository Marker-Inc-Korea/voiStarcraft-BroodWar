from voi_bw_commander.adapters import BotAdapter
from voi_bw_commander.backends import default_manifest
from voi_bw_commander.models import (
    BackendCapability,
    CapabilityManifest,
    ConflictPolicy,
    CommandUtterance,
    IntentAdaptivity,
    IntentState,
    Race,
)
from voi_bw_commander.parser import parse_utterance


def test_contract_accumulates_race_style_goal_and_commitment() -> None:
    state = IntentState()
    adapter = BotAdapter(default_manifest())
    result = adapter.apply(
        state,
        parse_utterance(CommandUtterance(text="저그 드론 5개 더 2햇 뮤탈 침략적으로 견제")),
    )

    assert not result.degraded
    assert state.contract.race == Race.ZERG
    assert state.contract.style["aggression"] == 0.85
    assert state.contract.style["harass"] == 0.9
    assert len(state.contract.hard_goals) == 1
    assert len(state.contract.strategic_commitments) == 1


def test_micro_doctrine_is_supported_by_default_manifest() -> None:
    state = IntentState()
    adapter = BotAdapter(default_manifest())
    result = adapter.apply(state, parse_utterance(CommandUtterance(text="뮤탈은 일꾼만 흔들어")))

    assert result.accepted
    assert not result.degraded


def test_unsupported_micro_doctrine_is_degraded_by_limited_manifest() -> None:
    state = IntentState()
    limited = CapabilityManifest(
        backend_name="Limited",
        race_support={Race.ZERG, Race.PROTOSS, Race.TERRAN},
        capabilities={BackendCapability.PERSISTENT_STYLE, BackendCapability.OBJECTIVE_INJECTION},
        supported_actions={"set_micro_doctrine"},
        integration_level=3,
    )
    adapter = BotAdapter(limited)
    result = adapter.apply(state, parse_utterance(CommandUtterance(text="뮤탈은 일꾼만 흔들어")))

    assert result.degraded
    assert state.memory.degraded


def test_contract_patch_preserves_style_while_adding_third_base_goal() -> None:
    state = IntentState()
    adapter = BotAdapter(default_manifest())
    adapter.apply(state, parse_utterance(CommandUtterance(text="저그 침략적으로 가고 2햇 뮤탈")))

    result = adapter.apply(state, parse_utterance(CommandUtterance(text="아까 말한 침략 스타일은 유지하되 이제 3멀티는 먹어")))

    assert not result.degraded
    assert state.contract.style["aggression"] == 0.85
    assert any(command.action == "take_expansion" for command in state.contract.hard_goals.values())
    assert any(command.action == "patch_contract" for command in state.memory.active.values())


def test_intent_metadata_survives_state_round_trip() -> None:
    state = IntentState()
    adapter = BotAdapter(default_manifest())
    adapter.apply(state, parse_utterance(CommandUtterance(text="지금 공격해")))

    hydrated = IntentState.from_dict(state.to_dict())
    [command] = list(hydrated.contract.instant_orders.values())

    assert command.adaptivity == IntentAdaptivity.FIXED
    assert command.conflict_policy == ConflictPolicy.SAFETY_OVERRIDE
