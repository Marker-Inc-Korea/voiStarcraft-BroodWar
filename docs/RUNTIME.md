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

## Version Contract

- Brood War runtime: 1.16.1-compatible execution environment.
- BWAPI/JBWAPI/BWMirror: pin to the selected backend bot's documented version.
- Commander queue schema: `schemas/command.schema.json`.
- Python package: install with `python -m pip install -e . pytest` for CI-equivalent local runs.
- Backend source: keep each bot checkout under `third_party/<BotName>` and never patch a bot until `audit-source` passes.

## Folder Convention

```text
runtime/
  commands.jsonl              validated command queue for the active bot
  telemetry.jsonl             commander/bot telemetry stream
  state.json                  persisted IntentState
  bench/<case>/baseline/      uncommanded regression run
  bench/<case>/commanded/     commanded regression run
  replays/                    copied BW replay artifacts
  logs/                       bot stdout/stderr, crash logs, desync markers
```

## Operator Runbook

1. Run `scripts/verify_local.sh`.
2. Run `PYTHONPATH=src python3 -m voi_bw_commander.cli readiness --root .`.
3. Audit the target bot source with `audit-source`.
4. Generate a `match-plan` or `benchmark-plan`.
5. Start Brood War/BWAPI with the selected bot and queue path.
6. Send commands only through `parse --queue` or the validated commander service.
7. Generate `report` or `compare-report` from telemetry after the match.

## Failure Handling

- Crash: persist bot stdout/stderr and process exit code under `runtime/logs`.
- Desync: write a desync marker with replay hash, map, bot versions, and command queue digest.
- Corrupted queue: stop consuming at the first invalid JSONL line, copy the queue to `runtime/logs`, and require schema validation before resume.
- Unsupported command: emit `degraded` or `invalid` status, never raw unit commands.
- Unsafe command: emit `unsafe` or `blocked` with a survival/conflict reason.

## Schema Migration Policy

- Additive command fields are allowed when `ParsedCommand.from_dict` has defaults.
- Removing or renaming fields requires a new schema version and migration note.
- CI must pass parser corpus, schema validation, queue round-trip, and report tests before release.

## Release Gate

The repo-side release gate is:

```bash
scripts/verify_local.sh
PYTHONPATH=src python3 -m voi_bw_commander.cli readiness --root .
PYTHONPATH=src python3 -m voi_bw_commander.cli eval-corpus fixtures/parser_corpus.json
```

Live-game release additionally requires a recorded Brood War replay, telemetry JSONL, and verifier report from the selected backend runtime.
