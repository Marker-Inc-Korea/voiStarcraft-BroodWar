from voi_bw_commander.models import Race
from voi_bw_commander.race_profiles import get_profile


def test_race_profiles_map_worker_and_harass_roles() -> None:
    assert get_profile(Race.ZERG).resolve_unit_role("worker") == ("Drone",)
    assert "Reaver" in get_profile(Race.PROTOSS).resolve_unit_role("harass")
    assert "Vulture" in get_profile(Race.TERRAN).resolve_unit_role("harass")
