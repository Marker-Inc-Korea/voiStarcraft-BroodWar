# Issue Completion Matrix

| Issue | Implemented in repo | Remaining external dependency |
| --- | --- | --- |
| #1 Epic | Architecture, commander core, parser/schema, race profiles, adapters, arbiter, safety, telemetry, verifier reports, benchmark planner, runtime docs, commandability decisioning, source hook plans, input surfaces, replay metric ingestion, live LLM provider gate, StarData representation, CI, and E2E repo-side vertical slice tests. | Live Brood War/BWAPI runtime with selected bot source patched and recorded live replays. |
| #2 Commander core | Parser, DSL models, IntentState, StrategicContract, IntentMemory, state store, cancellation lifecycle, persisted replay/rehydration, strict LLM schema gate, optional OpenAI-compatible provider client. | Larger production corpus and provider-specific online evaluation. |
| #3 Vertical slice | Natural language/transcript/LLM JSON -> validated queue -> persisted state -> telemetry/replay-metric ingest -> verifier report E2E test. | Bot-side on-frame consumer compiled inside the selected live bot runtime. |
| #4 Research baseline | Machine-readable backend candidate matrix, excluded non-playable backend list, candidates CLI, baseline drift tests. | Fresh source/build audits as bot versions change. |
| #5 Arbiter | Scoring implementation for production, expansion, attack, strategic commitment, squad/micro doctrine, and safety penalty hooks; source-level hook plans identify planner insertion points. | Actual edits inside each third-party bot's planner source. |
| #6 Race adapters | Generic adapter plus race-aware adapter manifests for McRave Zerg, Stardust Protoss, and Ecgberht Terran; illegal race strategy rejection; expanded unit/building/upgrade resolution. | Bot-specific C++/Scala/Java source patches. |
| #7 Race profile | Zerg, Protoss, Terran role mappings and legal command resolution/validation for workers, combat units, structures, upgrades, strategies, and micro doctrine. | Per-bot legal action constraints once source hooks are wired. |
| #8 Verifier | Expectation evaluator, telemetry writer, report builder, blocked/conflict/degraded counters, baseline-vs-commanded comparison report, replay-derived JSON/JSONL/CSV metric ingestion. | Native `.rep` export tool in live runtime. |
| #9 Benchmark | Benchmark pool, commanded-vs-baseline regression planner, crash/desync/compare-report output contract. | Local ladder runner with real bot binaries and maps. |
| #10 Safety | Structured safety/conflict decisions, emergency-defense blocking, unsafe override telemetry, report counters. | Real game-state telemetry source for richer safety decisions. |
| #11 LLM eval | Golden parser corpus, eval CLI, strict LLM JSON gate, OpenAI-compatible provider client, CI coverage with mocked provider. | Larger corpus and provider-specific online evaluation. |
| #12 Runtime ops | Runtime contract, version policy, folder convention, crash/desync/corrupt queue handling, schema migration policy, release gate, readiness checks, static UI, transcript ingestion, hook-plan CLI. | BWAPI/Brood War installation and operator-maintained bot binaries. |
| #13 Contract/memory | Deep intent metadata, adaptivity/conflict policy, patch semantics, take-expansion hard goal, cancellation history, JSON persistence. | Longer-game durable database if multi-match memory is required. |
| #14 Commandability | Audit checklist, source-tree audit CLI, commandability decision model, forbidden external unit-control policy, backend decision documentation, per-backend source-level hook plans for McRave/Stardust/Ecgberht/Steamhammer/PurpleWave. | Full source-level audits and patch application for each checked-out bot version. |

| Gap closeout | Implemented in repo | Remaining external dependency |
| --- | --- | --- |
| Source-level hooks | Hook plans for `on_frame`, `strategy`, `production`, `squad`, `micro`, `telemetry`; PurpleWave integration templates; C++ bridge template. | Applying and compiling those hooks in third-party bot repositories. |
| Real-time polling | Cursor-based C++ `pollNew()` bridge prevents repeated command replay per frame. | Include bridge in selected bot and call from `onFrame`. |
| Replay parser | Replay-derived JSON/JSONL/CSV metrics normalize into verifier/report telemetry. | Native `.rep` decoder/exporter from BWAPI or replay tooling. |
| Voice/UI | Transcript ingestion CLI and static commander UI handoff. | Optional speech-to-text engine and local service wrapper. |
| Live LLM | OpenAI-compatible provider client plus strict schema gate. | API key/network availability and online eval corpus. |
| Expanded parser | Structure, upgrade, and unit production goals with race legality checks. | Bot-specific feasibility constraints after source patching. |
| StarData/V3 | Trajectory feature extraction into aggression/defensive/harass/contain/greed labels. | Full StarData download/training jobs. |
