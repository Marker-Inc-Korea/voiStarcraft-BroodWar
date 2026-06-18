from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STYLE_LABELS = ("aggression", "defensive", "harass", "contain", "greed")


@dataclass(frozen=True)
class TrajectoryFeatures:
    game_id: str
    race: str
    aggression: float
    defensive: float
    harass: float
    contain: float
    greed: float
    source_metrics: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_id": self.game_id,
            "race": self.race,
            "labels": {
                "aggression": self.aggression,
                "defensive": self.defensive,
                "harass": self.harass,
                "contain": self.contain,
                "greed": self.greed,
            },
            "source_metrics": self.source_metrics,
        }


def load_trajectory_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "games" in data:
            data = data["games"]
        return data if isinstance(data, list) else [data]
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    raise ValueError(f"unsupported trajectory input: {path.suffix}")


def extract_trajectory_features(path: Path) -> list[TrajectoryFeatures]:
    return [features_from_row(row, index) for index, row in enumerate(load_trajectory_rows(path))]


def features_from_row(row: dict[str, Any], index: int = 0) -> TrajectoryFeatures:
    metrics = {
        "attack_count": _number(row.get("attack_count", row.get("attacks", 0))),
        "worker_harass_count": _number(row.get("worker_harass_count", row.get("worker_harass", 0))),
        "expansion_count": _number(row.get("expansion_count", row.get("expansions", 0))),
        "static_defense_count": _number(row.get("static_defense_count", row.get("static_defense", 0))),
        "contain_uptime": _number(row.get("contain_uptime", 0)),
        "army_supply": _number(row.get("army_supply", 0)),
        "worker_count": _number(row.get("worker_count", 0)),
        "duration_frames": max(_number(row.get("duration_frames", row.get("frames", 1))), 1.0),
    }
    attack_rate = metrics["attack_count"] / (metrics["duration_frames"] / 24 / 60)
    army_total = metrics["army_supply"] + metrics["worker_count"] + 1
    return TrajectoryFeatures(
        game_id=str(row.get("game_id", row.get("replay_id", f"game_{index}"))),
        race=str(row.get("race", "Unknown")),
        aggression=_clamp(attack_rate / 6 + metrics["army_supply"] / army_total),
        defensive=_clamp(metrics["static_defense_count"] / 8 + metrics["worker_count"] / army_total * 0.3),
        harass=_clamp(metrics["worker_harass_count"] / max(metrics["attack_count"], 1)),
        contain=_clamp(metrics["contain_uptime"]),
        greed=_clamp(metrics["expansion_count"] / 5 + metrics["worker_count"] / 80),
        source_metrics=metrics,
    )


def write_feature_jsonl(features: list[TrajectoryFeatures], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for item in features:
            handle.write(json.dumps(item.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return 0.0


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)
