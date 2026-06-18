from voi_bw_commander.models import Race
from voi_bw_commander.models import CommandUtterance
from voi_bw_commander.parser import parse_utterance
from voi_bw_commander.race_profiles import get_profile


def test_race_profiles_map_worker_and_harass_roles() -> None:
    assert get_profile(Race.ZERG).resolve_unit_role("worker") == ("Drone",)
    assert "Reaver" in get_profile(Race.PROTOSS).resolve_unit_role("harass")
    assert "Vulture" in get_profile(Race.TERRAN).resolve_unit_role("harass")


def test_race_profile_resolves_neutral_worker_goal_to_unit_type() -> None:
    command = next(command for command in parse_utterance(CommandUtterance(text="일꾼 5개 더")) if command.action == "produce_worker")

    resolution = get_profile(Race.TERRAN).resolve_command(command)

    assert resolution.valid
    assert resolution.resolved_payload["unit_type"] == "SCV"


def test_race_profile_rejects_illegal_strategy_for_race() -> None:
    command = next(command for command in parse_utterance(CommandUtterance(text="2햇 뮤탈")) if command.action == "commit_strategy")

    resolution = get_profile(Race.PROTOSS).resolve_command(command)

    assert not resolution.valid
    assert "not legal for Protoss" in resolution.reason
