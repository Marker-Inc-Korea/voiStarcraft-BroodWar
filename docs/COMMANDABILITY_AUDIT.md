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
