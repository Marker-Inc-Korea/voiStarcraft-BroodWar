# Production Runtime Contract

## Process Boundary

The LLM and parser run outside the Brood War process. The bot process only consumes validated command queue entries.

```text
Commander CLI/service
-> validated JSONL command queue
-> BWAPI bot on-frame polling
-> bot-specific adapter hooks
-> telemetry JSONL
-> verifier report
```

## Local Queue

Default queue format is JSON Lines. Each line is a validated `ParsedCommand` dictionary.

```bash
python -m voi_bw_commander.cli parse "저그 드론 5개 더" --queue runtime/commands.jsonl
```

## Stateful Commander Run

```bash
PYTHONPATH=src python3 -m voi_bw_commander.cli apply \
  "저그로 해. 드론 5개 더 찍고 2햇 뮤탈. 침략적으로 가되 정면 싸움은 피하고 일꾼만 흔들어." \
  --state runtime/state.json \
  --telemetry runtime/telemetry.jsonl
```

## Report Generation

```bash
PYTHONPATH=src python3 -m voi_bw_commander.cli report runtime/telemetry.jsonl
```

## Backend Audit

```bash
PYTHONPATH=src python3 -m voi_bw_commander.cli audit-source Steamhammer third_party/Steamhammer
```

## Match Plan

```bash
PYTHONPATH=src python3 -m voi_bw_commander.cli match-plan \
  --bot Steamhammer \
  --opponent PurpleWave \
  --race Zerg \
  --map FightingSpirit \
  --queue runtime/commands.jsonl \
  --telemetry runtime/telemetry.jsonl
```

## Readiness Check

```bash
PYTHONPATH=src python3 -m voi_bw_commander.cli readiness --root .
```

## Apply PurpleWave Integration

After checking out PurpleWave to `third_party/PurpleWave`, apply the source templates:

```bash
python3 scripts/apply_purplewave_integration.py third_party/PurpleWave --dry-run
python3 scripts/apply_purplewave_integration.py third_party/PurpleWave
```

The script copies commander integration sources to `src/Commander` and inserts the queue consumer poll into `src/Lifecycle/PurpleWave.scala`.

## Required External Runtime

Actual Brood War execution requires:

- StarCraft: Brood War 1.16.1 compatible runtime.
- BWAPI version matching the chosen bot.
- Bot source or binary.
- Map pool and replay/log directories.

This repository currently provides the commander core and adapter contract. A concrete bot repository must pass the commandability audit before its source hooks are implemented.
