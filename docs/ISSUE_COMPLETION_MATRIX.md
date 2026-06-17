# Issue Completion Matrix

| Issue | Implemented in repo | Remaining external dependency |
| --- | --- | --- |
| #1 Epic | Architecture, core package, CLI, docs, tests, CI, bot bridge template. | Real BWAPI game runtime. |
| #2 Commander core | Parser, DSL models, IntentState, StrategicContract, IntentMemory, state store. | Larger command corpus. |
| #3 Vertical slice | CLI -> queue -> adapter payload -> telemetry -> report/verifier. | Bot-side on-frame consumer in chosen bot. |
| #4 Research baseline | Backend candidate matrix and commandability audit doc/CLI. | Source audits after checkout/build. |
| #5 Arbiter | IntentArbiter scoring implementation. | Hook into real bot planners. |
| #6 Race adapters | Generic BotAdapter contract, manifests, C++ queue bridge template. | Bot-specific C++/Scala/Java source patches. |
| #7 Race profile | Zerg, Protoss, Terran race profiles. | Bot-specific legal action validation. |
| #8 Verifier | Expectation evaluator, telemetry writer, report builder. | Replay parser integration. |
| #9 Benchmark | Benchmark pool definition and external match plan generator. | Local ladder runner with real bot binaries. |
| #10 Safety | Safety policy and conflict gate. | Game-state telemetry source. |
| #11 LLM eval | Deterministic parser, strict LLM JSON gate, schema tests. | LLM provider integration if desired. |
| #12 Runtime ops | Runtime contract doc, queue convention, CI, verify script. | BWAPI/Brood War installation. |
| #13 Contract/memory | StrategicContract, IntentMemory, JSON persistence models. | Longer-game database store if needed. |
| #14 Commandability | Audit checklist, candidate matrix, source-tree audit CLI. | Actual source-level audits. |
