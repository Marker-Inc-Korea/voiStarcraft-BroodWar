from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ReplayIngestResult:
    source: str
    events: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "events": list(self.events), "event_count": len(self.events)}


def ingest_replay_metrics(path: Path) -> ReplayIngestResult:
    """Ingest replay-derived metrics exported as JSON, JSONL, or CSV.

    Native Brood War .rep decoding remains a runtime/tooling boundary because it requires
    external replay parsers. This module defines the production handoff format consumed by
    verifier/reporting once a BWAPI/replay tool exports frame-level or aggregate metrics.
    """

    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows = _read_jsonl(path)
    elif suffix == ".json":
        rows = _read_json(path)
    elif suffix == ".csv":
        rows = _read_csv(path)
    else:
        raise ValueError(f"unsupported replay metric export: {path.suffix}")
    return ReplayIngestResult(source=str(path), events=tuple(_normalize_row(row) for row in rows))


def write_ingested_events(result: ReplayIngestResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for event in result.events:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                item = json.loads(line)
                if not isinstance(item, dict):
                    raise ValueError("JSONL replay rows must be objects")
                rows.append(item)
    return rows


def _read_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "events" in data:
        data = data["events"]
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("JSON replay metrics must be an object, an events object, or a list of objects")
    return list(data)


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    if "event_type" in row and "payload" in row:
        payload = row["payload"]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {"value": payload}
        return {
            "timestamp": _coerce_number(row.get("timestamp", row.get("frame", 0))),
            "event_type": str(row["event_type"]),
            "payload": payload if isinstance(payload, dict) else {"value": payload},
        }
    metric = str(row.get("metric", row.get("name", "replay_metric")))
    value = _coerce_number(row.get("value", row.get("score", row.get("count", 0))))
    payload = {"metric": metric, "value": value}
    for key in ("status", "command_id", "action", "race", "backend", "unit", "target"):
        if key in row and row[key] not in (None, ""):
            payload[key] = row[key]
    event_type = _event_type_for_metric(metric, row)
    if event_type == "intent_adherence":
        payload = {"score": float(value)}
    elif event_type == "command_status":
        payload.setdefault("status", str(row.get("status", "active")))
    return {
        "timestamp": _coerce_number(row.get("timestamp", row.get("frame", 0))),
        "event_type": event_type,
        "payload": payload,
    }


def _event_type_for_metric(metric: str, row: dict[str, Any]) -> str:
    if row.get("event_type"):
        return str(row["event_type"])
    if metric in {"intent_adherence", "intent_adherence_score"}:
        return "intent_adherence"
    if row.get("status") or metric in {"command_status", "command_fulfillment"}:
        return "command_status"
    return "replay_metric"


def _coerce_number(value: Any) -> int | float:
    if isinstance(value, (int, float)):
        return value
    text = str(value)
    try:
        number = float(text)
    except ValueError:
        return 0
    return int(number) if number.is_integer() else number
