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

## Required External Runtime

Actual Brood War execution requires:

- StarCraft: Brood War 1.16.1 compatible runtime.
- BWAPI version matching the chosen bot.
- Bot source or binary.
- Map pool and replay/log directories.

This repository currently provides the commander core and adapter contract. A concrete bot repository must pass the commandability audit before its source hooks are implemented.
