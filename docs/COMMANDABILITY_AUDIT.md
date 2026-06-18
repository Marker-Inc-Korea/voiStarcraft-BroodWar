# Strongest-Bot Commandability Audit

The strongest bot should become the primary executor only if it can accept source-level intent injection without fighting its own planners.

## Audit Checklist

| Area | Required evidence |
| --- | --- |
| Build/run | Bot builds reproducibly and launches with BWAPI-compatible Brood War runtime. |
| Strategy | Source location for strategy selection and opening/build plan choice. |
| Production | Source location for production queue scoring or build priority insertion. |
| Expansion | Source location for expansion timing and greed/safety tradeoff. |
| Squad | Source location for attack, retreat, contain, harass, and target region objectives. |
| Micro | Source location for target priority, retreat thresholds, spell priority, and danger scoring. |
| Runtime input | File/socket/onSendText path that can be polled safely from the bot frame loop. |
| Telemetry | Events for accepted, active, fulfilled, blocked, unsafe, degraded, and overridden commands. |

## Promotion Rule

A bot can be promoted to primary commandable backend only when it reaches at least integration level 3:

- Runtime persistent style injection.
- Runtime build/tech/squad objective injection.
- Verifiable telemetry for accepted and blocked commands.

If a strong bot cannot expose these hooks, keep it as a benchmark backend.

## Current Decision Policy

Strength alone is not enough. The primary backend must be the strongest bot that also exposes source-level decision hooks.

| Backend | Initial role | Promotion condition |
| --- | --- | --- |
| Steamhammer | all-race commandable engineering target | Promote when source checkout passes build/strategy/production/squad/runtime/telemetry audit. |
| PurpleWave | all-race fallback and benchmark-quality target | Promote when Scala lifecycle and planner hooks are patched safely. |
| McRave | Zerg primary candidate | Promote after Zerg production, squad, and micro hook locations are verified. |
| Stardust | Protoss primary candidate | Promote after build/tech/squad hook locations are verified. |
| Ecgberht/LetaBot | Terran primary candidates | Promote the one with lower runtime integration risk after audit. |
| SAIDA/Iron | benchmark-only until proven otherwise | Do not command through external unit control unless source planner hooks are available. |

## Forbidden Shortcut

External unit-control injection is forbidden as a primary integration mode. It bypasses the bot planner, can fight production/squad/micro managers, and will usually make a strong bot weaker. Commands must enter through strategy, production, squad, micro, or telemetry-owned source hooks.
