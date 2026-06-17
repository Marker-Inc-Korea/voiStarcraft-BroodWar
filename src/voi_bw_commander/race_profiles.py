from __future__ import annotations

from dataclasses import dataclass

from .models import Race


@dataclass(frozen=True)
class RaceProfile:
    race: Race
    worker: str
    supply: str
    early_pressure: tuple[str, ...]
    harass: tuple[str, ...]
    contain: tuple[str, ...]
    anti_air: tuple[str, ...]
    spell_priority: tuple[str, ...]
    strategic_aliases: dict[str, tuple[str, ...]]

    def resolve_unit_role(self, role: str) -> tuple[str, ...]:
        return {
            "worker": (self.worker,),
            "supply": (self.supply,),
            "early_pressure": self.early_pressure,
            "harass": self.harass,
            "contain": self.contain,
            "anti_air": self.anti_air,
            "spell_priority": self.spell_priority,
        }.get(role, ())


PROFILES: dict[Race, RaceProfile] = {
    Race.ZERG: RaceProfile(
        race=Race.ZERG,
        worker="Drone",
        supply="Overlord",
        early_pressure=("Zergling", "Hydralisk"),
        harass=("Mutalisk", "Zergling runby"),
        contain=("Lurker", "Hydralisk"),
        anti_air=("Scourge", "Hydralisk", "Spore Colony"),
        spell_priority=("Defiler Plague", "Dark Swarm"),
        strategic_aliases={
            "two_hatch_muta": ("Spawning Pool", "Lair", "Spire", "Mutalisk"),
            "lurker_contain": ("Hydralisk Den", "Lurker Aspect", "Lurker"),
        },
    ),
    Race.PROTOSS: RaceProfile(
        race=Race.PROTOSS,
        worker="Probe",
        supply="Pylon",
        early_pressure=("Zealot", "Dragoon"),
        harass=("Reaver", "Dark Templar", "Corsair"),
        contain=("Dragoon", "Reaver"),
        anti_air=("Corsair", "Dragoon", "Photon Cannon"),
        spell_priority=("Psionic Storm", "Stasis Field"),
        strategic_aliases={
            "two_gate_pressure": ("Gateway", "Cybernetics Core", "Dragoon Range"),
            "reaver_harass": ("Robotics Facility", "Shuttle", "Reaver"),
        },
    ),
    Race.TERRAN: RaceProfile(
        race=Race.TERRAN,
        worker="SCV",
        supply="Supply Depot",
        early_pressure=("Marine", "Vulture"),
        harass=("Vulture", "Dropship", "Wraith"),
        contain=("Siege Tank", "Vulture"),
        anti_air=("Marine", "Goliath", "Missile Turret"),
        spell_priority=("Science Vessel Irradiate", "EMP Shockwave"),
        strategic_aliases={
            "vulture_harass": ("Factory", "Vulture", "Spider Mines"),
            "tank_contain": ("Factory", "Machine Shop", "Siege Mode", "Siege Tank"),
        },
    ),
}


def get_profile(race: Race) -> RaceProfile:
    if race not in PROFILES:
        raise ValueError(f"no race profile for {race.value}")
    return PROFILES[race]
