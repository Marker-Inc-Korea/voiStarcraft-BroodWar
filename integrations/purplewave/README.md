# PurpleWave Integration Template

These files are source-level integration templates for PurpleWave after it passes commandability audit.

Target insertion points:

- Call `CommanderQueueConsumer.poll()` from `src/Lifecycle/PurpleWave.scala` inside `onFrame()` before tactical and production decisions.
- Read `CommanderIntent.current` from production, tactic, squad, and micro modules.
- Emit accepted/degraded/fulfilled telemetry through `CommanderTelemetry`.

The files are intentionally standalone Scala templates. They must be copied into PurpleWave source and wired to PurpleWave's existing `With` lifecycle and logging facilities during the backend-specific patch.
