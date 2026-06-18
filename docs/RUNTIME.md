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

Bot-side `onFrame` consumers must use cursor-based polling. `bot_bridge/CommanderBridge.hpp`
provides `pollNew()` so commands are not replayed every frame and invalid queue lines are
isolated as invalid envelopes instead of being blindly applied.

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

Replay-derived metrics can be normalized into telemetry JSONL from JSON, JSONL, or CSV:

```bash
PYTHONPATH=src python3 -m voi_bw_commander.cli replay-ingest runtime/replay_metrics.csv --output runtime/telemetry.jsonl
```

Native `.rep` decoding is an external runtime boundary. The production contract is that a
BWAPI/replay exporter emits frame or aggregate metrics, then this repo normalizes them for
reports and verifier checks.

## Backend Audit

```bash
PYTHONPATH=src python3 -m voi_bw_commander.cli audit-source Steamhammer third_party/Steamhammer
```

## Source-Level Hook Plans

Generate per-backend patch plans before changing third-party bot code:

```bash
PYTHONPATH=src python3 -m voi_bw_commander.cli hook-plan --backend McRave
PYTHONPATH=src python3 -m voi_bw_commander.cli hook-plan --output-dir runtime/hook-plans
```

The plans cover `on_frame`, `strategy`, `production`, `squad`, `micro`, and `telemetry`
for McRave, Stardust, Ecgberht, Steamhammer, and PurpleWave. They intentionally place
intent influence inside the bot's own decision loop rather than issuing external unit
commands that fight the bot planner.

## Input Surfaces

Voice and UI should terminate in transcript text, then append validated commands to the
queue:

```bash
PYTHONPATH=src python3 -m voi_bw_commander.cli transcript --text "저그 드론 5개 더" --queue runtime/commands.jsonl
PYTHONPATH=src python3 -m voi_bw_commander.cli transcript --file runtime/transcript.txt --queue runtime/commands.jsonl
PYTHONPATH=src python3 -m voi_bw_commander.cli write-ui --output runtime/commander.html --queue runtime/commands.jsonl
```

The committed `ui/commander.html` is a static handoff surface. Production deployments can
wrap it with a local service, but the game process should still consume only the validated
JSONL queue.

## Live LLM Provider

Strict JSON validation remains mandatory. Optional live provider parsing uses an
OpenAI-compatible chat-completions endpoint:

```bash
OPENAI_API_KEY=... VOI_LLM_MODEL=gpt-4.1-mini \
PYTHONPATH=src python3 -m voi_bw_commander.cli parse-llm-live "테란 벌처 3기 생산하고 마인업"
```

Environment variables:

- `OPENAI_API_KEY` or `VOI_LLM_API_KEY`
- `VOI_LLM_MODEL`
- `VOI_LLM_BASE_URL`
- `VOI_LLM_TIMEOUT_SECONDS`

Provider output is never trusted directly; it must pass `StrictLLMCommandParser`.

## StarData / V3 Representation

Trajectory rows exported from StarData-style datasets can be converted into intent labels:

```bash
PYTHONPATH=src python3 -m voi_bw_commander.cli stardata-features trajectories.jsonl --output runtime/features.jsonl
```

The feature schema emits `aggression`, `defensive`, `harass`, `contain`, and `greed`
signals for future classifier training and intent-adherence calibration.

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

This repository provides the commander core, adapter contract, source-level hook plans,
input surfaces, LLM provider gate, replay metric ingestion, and V3 representation surface.
A concrete bot repository must still pass commandability audit and receive source-level
decision-loop hooks before live Brood War execution is claimed complete.

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
4. Generate `hook-plan` and patch the target bot's source-level decision points.
5. Generate a `match-plan` or `benchmark-plan`.
6. Start Brood War/BWAPI with the selected bot and queue path.
7. Send commands only through `parse --queue`, `transcript`, `parse-llm-live`, or the validated commander service.
8. Normalize replay-derived metrics with `replay-ingest` if needed.
9. Generate `report` or `compare-report` from telemetry after the match.

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
