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


def test_race_profile_resolves_expanded_command_aliases() -> None:
    commands = parse_utterance(CommandUtterance(text="테란 벌처 3기 생산하고 팩토리 지어. 시즈모드 연구."))
    profile = get_profile(Race.TERRAN)

    unit = profile.resolve_command(next(command for command in commands if command.action == "produce_unit"))
    structure = profile.resolve_command(next(command for command in commands if command.action == "build_structure"))
    upgrade = profile.resolve_command(next(command for command in commands if command.action == "research_upgrade"))

    assert unit.valid and unit.resolved_payload["unit_type"] == "Vulture"
    assert structure.valid and structure.resolved_payload["structure_type"] == "Factory"
    assert upgrade.valid and upgrade.resolved_payload["upgrade_type"] == "Siege Mode"


def test_race_profile_rejects_cross_race_structure() -> None:
    command = next(command for command in parse_utterance(CommandUtterance(text="스파이어 지어")) if command.action == "build_structure")

    resolution = get_profile(Race.TERRAN).resolve_command(command)

    assert not resolution.valid
    assert "not legal for Terran" in resolution.reason
