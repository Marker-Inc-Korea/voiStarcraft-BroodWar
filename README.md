# voiStarcraft-BroodWar

Natural-language commander layer for autonomous StarCraft: Brood War BWAPI bots.

## Project Goal

Build a production-grade platform where an existing full-game Brood War bot keeps playing autonomously, while a user's Korean or English natural-language commands persistently bias its strategic intent, build priorities, squad objectives, and micro doctrine.

The user should not manually click units. The user acts as a commander:

```text
"Zerg. Make five more drones, commit to two-hatch muta, play aggressive,
but avoid frontal fights and keep harassing workers."
```

The bot remains the executor:

```text
Natural language
-> Command DSL
-> Intent State
-> Race Profile
-> Bot Adapter
-> Autonomous full-game BWAPI bot
-> Intent Arbiter
-> BWAPI unit commands
-> Replay/telemetry verifier
```

## Critical Planning Notes

This project is valuable only if the command layer changes long-running behavior, not just one-off actions. A command like "play aggressively" must remain active until cancelled or superseded, affecting production, expansion timing, attack thresholds, squad target selection, and risk tolerance across the game.

Not every strong Brood War bot is a good commandable backend. Backend selection must prioritize full-game capability, source availability, BWAPI or BWAPI-wrapper integration, maintainability, and runtime injection points. Strong binary-only or hard-to-modify bots should be treated as benchmark opponents first.

The safest product path is:

1. Prove the commander UX with one all-race backend.
2. Add deeper per-race adapters for the best modifiable bots.
3. Add benchmark-only strong bots for evaluation.
4. Add replay-based verification to prove that intent actually changed behavior.

## Backend Strategy

### Backend roles

| Role | Requirement | Purpose |
| --- | --- | --- |
| Commandable backend | Source-modifiable full-game bot | Receives runtime intent injection. |
| Benchmark backend | Strong full-game bot, may be closed or hard to modify | Opponent and evaluation target. |
| Fallback backend | Stable all-race bot | Keeps product usable across Zerg, Protoss, and Terran. |
| Excluded backend | Micro-only, simulator-only, dataset-only, or partial-game code | Research support only, not the playable backend. |

### Initial candidates

| Race | Primary commandable target | Secondary target | Benchmark/fallback |
| --- | --- | --- | --- |
| All-race MVP | Steamhammer or PurpleWave | UAlbertaBot for reference | PurpleWave |
| Zerg | McRave | Steamhammer-Zerg, ZZZKBot | PurpleWave-Zerg |
| Protoss | Stardust | Locutus | PurpleWave-Protoss |
| Terran | Ecgberht or LetaBot | LetaBot or Ecgberht | SAIDA, Iron, PurpleWave-Terran |

### Current assessment

Steamhammer is the best first engineering target if C++ modification speed and all-race coverage matter most. Its public site describes it as a full-featured starter bot for all races, and the release history lists active 2025 AIIDE versions.

PurpleWave is the best all-race fallback and benchmark-quality reference. Its README states that it can play all three races, supports many professional-style strategies, is MIT licensed, and has strong competition results.

McRave, Stardust, and Ecgberht/LetaBot should be evaluated as V1 race-specific adapters, not day-one dependencies. Each has different language/runtime costs, so the adapter boundary must be explicit.

SAIDA and Iron should start as benchmark-only targets unless source access and runtime command injection are proven practical.

## Intent Model

Commands are normalized into an `IntentState`, not directly translated into clicks.

```json
{
  "race": "Zerg",
  "backend_bot": "Steamhammer",
  "intent_state": {
    "strategic_style": {
      "aggression": 0.85,
      "harass": 0.8,
      "economy_greed": 0.35,
      "defensive_safety": 0.45,
      "all_in_commitment": 0.3
    },
    "strategic_commitments": [
      {
        "type": "tech_path",
        "name": "two_hatch_muta",
        "strength": 0.9,
        "duration": "until_cancelled_or_invalid"
      }
    ],
    "hard_goals": [
      {
        "type": "produce_worker",
        "count": 5,
        "mode": "delta",
        "priority": "hard",
        "status": "active_until_fulfilled"
      }
    ],
    "standing_orders": [
      {
        "scope": "harass_squads",
        "rule": "avoid_main_army",
        "priority": "high"
      },
      {
        "scope": "mutalisk_squads",
        "rule": "prioritize_workers",
        "priority": "high"
      }
    ]
  }
}
```

## Command Classes

| Class | Example | Persistence | Verifiable |
| --- | --- | --- | --- |
| Instant order | "Attack now", "Retreat now" | Short TTL | Yes |
| Hard goal | "Make five more workers", "Build a Spire" | Until done or invalid | Yes |
| Persistent style | "Play aggressive", "Play defensively" | Until changed | Statistical |
| Strategic commitment | "Two-hatch muta", "Tank contain" | Until cancelled, invalid, or unsafe | Yes |
| Standing micro doctrine | "Mutas only hit workers and leave" | Until changed | Statistical |

## Arbiter Scoring

The commander layer should bias existing bot decisions instead of replacing the bot:

```text
final_score(action)
= base_bot_score(action)
+ intent_bias(action)
+ hard_goal_bonus(action)
+ strategic_commitment_bonus(action)
- violation_penalty(action)
- safety_penalty(action)
```

This lets the bot remain autonomous while making its choices measurably reflect user intent.

## Production Architecture

```text
User Input
  - Korean/English text
  - voice later
  - command UI later
        |
        v
Commander LLM
  - parses natural language
  - emits strict Command DSL JSON
        |
        v
Intent State Manager
  - stores instant orders
  - tracks hard goals
  - maintains persistent styles
  - resolves conflicts
        |
        v
Race Profile Layer
  - maps worker/supply/tech/harass concepts per race
        |
        v
Bot Registry
  - selects backend
  - exposes capability manifest
        |
        v
Bot Adapter
  - converts intent into backend-specific knobs/objectives
        |
        v
Intent Arbiter in Bot Runtime
  - merges base bot plan with user intent
        |
        v
BWAPI Bot + BWAPI
        |
        v
Telemetry + Replay Verifier
```

## Implementation Plan

### Phase 0: Repository and research baseline

Deliverables:

- Project README and architecture decision record.
- GitHub Issues for MVP, V1, V2, and verifier workstreams.
- Backend candidate matrix with integration levels.

Exit criteria:

- The repo states the long-term goal, constraints, and staged implementation plan.
- Every major milestone is represented as a GitHub Issue.

### Phase 1: Commander core MVP

Deliverables:

- `CommandDSL` JSON schema.
- `IntentState` data model.
- Deterministic parser fixtures for core Korean commands.
- Optional LLM parser wrapper with strict schema validation.
- In-memory and file-backed command queue.

Supported commands:

- Worker delta: "일꾼 5개 더", "드론 5개 더", "SCV 5개 더".
- Style: aggressive, defensive, greedy, harass-first.
- Tactical: attack now, retreat now.

Exit criteria:

- Commands can be parsed, validated, merged, cancelled, and replayed in tests.

### Phase 2: BWAPI bridge and all-race backend MVP

Deliverables:

- Local process boundary between commander service and bot runtime.
- File or socket queue consumed by the bot on frame ticks.
- First backend adapter using Steamhammer or PurpleWave.
- Capability manifest for each backend.

Exit criteria:

- A full-game bot can start, receive command queue updates, and expose telemetry events.
- At least one all-race backend can apply worker goals and high-level style bias.

### Phase 3: Intent arbiter integration

Deliverables:

- Production/build priority bias hooks.
- Expansion and attack-threshold bias hooks.
- Squad objective hooks for attack, retreat, and harass.
- Safety override and conflict handling.

Exit criteria:

- The same bot behaves differently under aggressive, defensive, and greedy styles.
- Hard goals are fulfilled unless blocked by explicit game-state constraints.

### Phase 4: Race profiles

Deliverables:

- `ZergRaceProfile`.
- `ProtossRaceProfile`.
- `TerranRaceProfile`.
- Race-specific command aliases, tech names, unit names, and validation rules.

Exit criteria:

- Race-neutral commands map to legal race-specific goals.
- Illegal commands produce safe, explainable validation errors.

### Phase 5: V1 race-specific adapters

Deliverables:

- Zerg adapter spike: McRave or Steamhammer-Zerg.
- Protoss adapter spike: Stardust or Locutus.
- Terran adapter spike: Ecgberht or LetaBot.
- Adapter interface hardened around real integration pain.

Exit criteria:

- At least one race-specific backend reaches integration level 3 or higher.

### Phase 6: Verifier and reports

Deliverables:

- Telemetry schema.
- Replay/log analyzer.
- Intent adherence score.
- Per-command fulfillment report.
- Baseline-vs-commanded comparison harness.

Exit criteria:

- Reports can answer: "Was the command followed?", "Why was it ignored?", and "How did it change play?"

### Phase 7: Benchmark ladder

Deliverables:

- Benchmark opponent pool.
- BASIL/SSCAIT-inspired local batch runner.
- Win-rate and crash-rate reporting.
- Regression suite for commanded vs uncommanded behavior.

Exit criteria:

- Product changes are measured against strength, stability, and command adherence.

## Integration Levels

| Level | Capability |
| --- | --- |
| 0 | Benchmark only; no command injection. |
| 1 | Launch-time strategy or race configuration. |
| 2 | Runtime persistent style injection. |
| 3 | Runtime build, tech, and squad objective injection. |
| 4 | Runtime micro doctrine injection. |
| 5 | Full telemetry and replay verifier integration. |

## Verifier Metrics

Core metrics:

- Command fulfillment rate.
- Intent adherence score.
- Command-to-effect latency.
- Safety override count.
- Conflict count.
- Win-rate delta.
- Crash/desync rate.

Race-specific examples:

- Zerg: drone goal fulfillment, mutalisk worker target ratio, third hatchery timing shift.
- Protoss: probe goal fulfillment, dragoon range timing, reaver worker-shot value.
- Terran: SCV goal fulfillment, factory timing, vulture harass attempts, tank contain uptime.

## Engineering Principles

- Treat the bot as an autonomous executor, not a remote-controlled unit group.
- Keep LLM parsing outside the game process.
- Use strict schemas and deterministic validation before runtime injection.
- Prefer reversible biasing over brittle hard overrides.
- Every command must be explainable as fulfilled, active, blocked, unsafe, invalid, or superseded.
- Every backend must declare capabilities before receiving commands.
- Production quality requires telemetry, replay validation, and regression tests from the start.

## References

- BWAPI: https://bwapi.github.io/
- BWAPI `AIModule`: https://bwapi.github.io/class_b_w_a_p_i_1_1_a_i_module.html
- BWAPI `UnitInterface`: https://bwapi.github.io/class_b_w_a_p_i_1_1_unit_interface.html
- PurpleWave: https://github.com/dgant/PurpleWave
- Steamhammer: https://satirist.org/ai/starcraft/steamhammer/
- McRave: https://github.com/Cmccrave/McRave
- Stardust: https://github.com/bmnielsen/Stardust
- Locutus: https://github.com/bmnielsen/Locutus
- Ecgberht: https://github.com/Jabbo16/Ecgberht
- LetaBot: https://github.com/MartinRooijackers/LetaBot
- SAIDA SSCAIT profile: https://www.sscaitournament.com/index.php?action=botDetails&bot=SAIDA
- Iron: https://bwem.sourceforge.net/Iron.html
- BASIL Ladder: https://www.basil-ladder.net/
- StarData paper: https://arxiv.org/abs/1708.02139
