# Issue Completion Matrix

| Issue | Implemented in repo | Remaining external dependency |
| --- | --- | --- |
| #1 Epic | Architecture, commander core, parser/schema, race profiles, adapters, arbiter, safety, telemetry, verifier reports, benchmark planner, runtime docs, commandability decisioning, CI, and E2E repo-side vertical slice tests. | Live Brood War/BWAPI runtime with selected bot source hooks and recorded replays. |
| #2 Commander core | Parser, DSL models, IntentState, StrategicContract, IntentMemory, state store, cancellation lifecycle, persisted replay/rehydration, strict LLM schema gate. | Larger production corpus and optional live LLM provider. |
| #3 Vertical slice | Natural language -> validated queue -> persisted state -> telemetry -> verifier report E2E test. | Bot-side on-frame consumer inside the selected live bot runtime. |
| #4 Research baseline | Machine-readable backend candidate matrix, excluded non-playable backend list, candidates CLI, baseline drift tests. | Fresh source/build audits as bot versions change. |
| #5 Arbiter | Scoring implementation for production, expansion, attack, strategic commitment, squad/micro doctrine, and safety penalty hooks. | Source-level hook into real bot planner scoring functions. |
| #6 Race adapters | Generic adapter plus race-aware adapter manifests for McRave Zerg, Stardust Protoss, and Ecgberht Terran; illegal race strategy rejection. | Bot-specific C++/Scala/Java source patches. |
| #7 Race profile | Zerg, Protoss, Terran role mappings and legal command resolution/validation. | Per-bot legal action constraints once source hooks are wired. |
| #8 Verifier | Expectation evaluator, telemetry writer, report builder, blocked/conflict/degraded counters, baseline-vs-commanded comparison report. | Replay parser integration from live game artifacts. |
| #9 Benchmark | Benchmark pool, commanded-vs-baseline regression planner, crash/desync/compare-report output contract. | Local ladder runner with real bot binaries and maps. |
| #10 Safety | Structured safety/conflict decisions, emergency-defense blocking, unsafe override telemetry, report counters. | Real game-state telemetry source for richer safety decisions. |
| #11 LLM eval | Golden parser corpus, eval CLI, strict LLM JSON gate, CI coverage. | Larger corpus and optional provider-specific evaluation. |
| #12 Runtime ops | Runtime contract, version policy, folder convention, crash/desync/corrupt queue handling, schema migration policy, release gate, readiness checks. | BWAPI/Brood War installation and operator-maintained bot binaries. |
| #13 Contract/memory | Deep intent metadata, adaptivity/conflict policy, patch semantics, take-expansion hard goal, cancellation history, JSON persistence. | Longer-game durable database if multi-match memory is required. |
| #14 Commandability | Audit checklist, source-tree audit CLI, commandability decision model, forbidden external unit-control policy, backend decision documentation. | Full source-level audits for each checked-out bot version. |
