from voi_bw_commander.backends import BACKEND_CANDIDATES, EXCLUDED_PLAYABLE_BACKENDS


def test_research_baseline_includes_required_full_game_candidates() -> None:
    names = {candidate.name for candidate in BACKEND_CANDIDATES}

    assert {
        "PurpleWave",
        "Steamhammer",
        "McRave",
        "Stardust",
        "Locutus",
        "Ecgberht",
        "LetaBot",
        "ZZZKBot",
        "SAIDA",
        "Iron",
    }.issubset(names)


def test_research_baseline_excludes_non_playable_backends() -> None:
    names = {entry["name"] for entry in EXCLUDED_PLAYABLE_BACKENDS}

    assert "SparCraft/FAP" in names
    assert "StarData" in names
