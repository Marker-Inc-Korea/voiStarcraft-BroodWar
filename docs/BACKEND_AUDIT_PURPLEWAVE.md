# PurpleWave Commandability Audit

Audit date: 2026-06-18

Local source checked out to `third_party/PurpleWave` for inspection. The source is not committed because `third_party/` is ignored.

## Automated Audit

The source tree contains indicators for:

- build: `pom.xml`
- strategy/opening/build-order logic
- production queue logic
- squad and combat logic
- micro/target/danger logic
- runtime command/file indicators
- logging/event/replay indicators

Conclusion: PurpleWave is a credible commandable-backend candidate, but it still requires source-level patching in its Scala/JBWAPI runtime. It should not be treated as production-integrated until a bot-side command consumer and intent hooks are patched into its lifecycle.

## Hook Candidates

| Area | Candidate source |
| --- | --- |
| Frame lifecycle | `src/Lifecycle/PurpleWave.scala`, `src/Lifecycle/With.scala` |
| On-frame deferred commands | `src/Debugging/LambdaQueue.scala` |
| Production queue | `src/Tactic/Production/Produce.scala`, `src/Tactic/Production/Production.scala` |
| Squad orchestration | `src/Tactic/Tactician.scala`, `src/Tactic/Squads/Squads.scala` |
| Attack squad | `src/Tactic/Tactician.scala` |
| Mission harass/drop logic | `src/Tactic/Missions/*` |
| Micro commander | `src/Micro/Agency/Commander.scala` |
| Retreat and fight/flee | `src/Micro/Actions/Combat/Maneuvering/Retreat.scala`, `src/Micro/Actions/Combat/Decisionmaking/FightOrFlee.scala` |
| Targeting | `src/Micro/Targeting/*` |

## Required Patch Plan

1. Add a Scala command queue consumer that reads validated JSONL emitted by this repository.
2. Invoke the consumer from `PurpleWave.onFrame()` before tactical/production decisions are finalized.
3. Store active contract state in a PurpleWave-side `CommanderIntent` singleton.
4. Add production bias hooks near `Tactic.Production.Produce`.
5. Add attack/harass/retreat bias hooks near `Tactic.Tactician` and squad automation.
6. Add target-priority and retreat-threshold hooks in micro decision modules.
7. Emit telemetry JSONL for accepted, degraded, unsafe, and fulfilled commands.

## Promotion Decision

PurpleWave is promoted from “candidate only” to “source-audited commandable candidate.”

It is not yet a completed production backend because the Brood War/JBWAPI runtime is not available in this macOS workspace, and no source patch has been compiled or executed inside PurpleWave yet.
