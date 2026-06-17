# Issue Completion Matrix

| Issue | Implemented in repo | Remaining external dependency |
| --- | --- | --- |
| #1 Epic | Architecture, core package, CLI, docs, tests. | Real BWAPI game runtime. |
| #2 Commander core | Parser, DSL models, IntentState, StrategicContract, IntentMemory. | Larger command corpus. |
| #3 Vertical slice | CLI -> queue -> adapter payload -> verifier demo. | Bot-side on-frame consumer. |
| #4 Research baseline | Backend candidate matrix and commandability audit doc. | Source audits after checkout/build. |
| #5 Arbiter | IntentArbiter scoring implementation. | Hook into real bot planners. |
| #6 Race adapters | Generic BotAdapter contract and manifests. | Bot-specific C++/Scala/Java source patches. |
| #7 Race profile | Zerg, Protoss, Terran race profiles. | Bot-specific legal action validation. |
| #8 Verifier | Expectation evaluator and verifier report. | Replay parser integration. |
| #9 Benchmark | Benchmark pool definition. | Local ladder runner with real bot binaries. |
| #10 Safety | Safety policy and conflict gate. | Game-state telemetry source. |
| #11 LLM eval | Deterministic parser and test fixtures. | LLM provider integration if desired. |
| #12 Runtime ops | Runtime contract doc and queue convention. | BWAPI/Brood War installation. |
| #13 Contract/memory | StrategicContract and IntentMemory models. | Long-game persistence store. |
| #14 Commandability | Audit checklist and candidate matrix. | Actual source-level audits. |
