from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceHook:
    area: str
    file_hint: str
    symbol_hint: str
    injection: str
    rationale: str

    def to_dict(self) -> dict[str, str]:
        return {
            "area": self.area,
            "file_hint": self.file_hint,
            "symbol_hint": self.symbol_hint,
            "injection": self.injection,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class BackendHookPlan:
    backend: str
    language: str
    hooks: tuple[SourceHook, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "backend": self.backend,
            "language": self.language,
            "hooks": [hook.to_dict() for hook in self.hooks],
        }

    def render_markdown(self) -> str:
        lines = [f"# {self.backend} Source-Level Hook Plan", "", f"Language: {self.language}", ""]
        for hook in self.hooks:
            lines.extend(
                [
                    f"## {hook.area}",
                    f"- file hint: `{hook.file_hint}`",
                    f"- symbol hint: `{hook.symbol_hint}`",
                    f"- rationale: {hook.rationale}",
                    "",
                    "```text",
                    hook.injection,
                    "```",
                    "",
                ]
            )
        return "\n".join(lines)


COMMON_CPP_INJECTION = (
    "poll commander queue once per frame; merge active IntentState into strategy, production, squad, and micro scores"
)

HOOK_PLANS: dict[str, BackendHookPlan] = {
    "Steamhammer": BackendHookPlan(
        backend="Steamhammer",
        language="C++",
        hooks=(
            SourceHook("on_frame", "Source/Steamhammer/Steamhammer.cpp", "onFrame", "CommanderBridge.poll()", COMMON_CPP_INJECTION),
            SourceHook("strategy", "Source/StrategyManager.*", "StrategyManager::update", "apply style and strategic commitment weights", "bias opening/transition decisions without external unit control"),
            SourceHook("production", "Source/ProductionManager.*", "ProductionManager::update", "inject hard goals into queue scoring", "worker/build/upgrade goals must be fulfilled by the bot's own queue"),
            SourceHook("squad", "Source/Squad.*", "Squad::update", "apply squad objectives and target regions", "harass/contain/retreat orders belong at squad objective selection"),
            SourceHook("micro", "Source/Micro.*", "Micro*::execute", "apply target priority and retreat doctrine", "micro doctrine should alter targeting, not override all unit commands externally"),
            SourceHook("telemetry", "Source/InformationManager.*", "per-frame logging", "emit command_status and intent_adherence events", "verifier needs accepted/blocked/unsafe/degraded evidence"),
        ),
    ),
    "PurpleWave": BackendHookPlan(
        backend="PurpleWave",
        language="Scala",
        hooks=(
            SourceHook("on_frame", "src/Lifecycle/PurpleWave.scala", "onFrame", "CommanderQueueConsumer.poll(\"runtime/commands.jsonl\")", "already scaffolded by integrations/purplewave templates"),
            SourceHook("strategy", "src/Strategery/**", "strategy selection", "merge style and commitments into strategy scores", "PurpleWave strategy scoring is the correct source-level bias point"),
            SourceHook("production", "src/Production/**", "production planning", "inject hard goals as production wishes", "build/tech/unit goals must enter production planning"),
            SourceHook("squad", "src/Tactics/**", "tactical decisions", "apply squad target and posture doctrine", "avoid external unit-control conflicts"),
            SourceHook("micro", "src/Micro/**", "micro decisions", "apply target and retreat rules", "standing doctrine belongs near tactical micro scoring"),
            SourceHook("telemetry", "src/Commander/CommanderTelemetry.scala", "emit", "write JSONL telemetry", "verifier consumes command lifecycle events"),
        ),
    ),
    "McRave": BackendHookPlan(
        backend="McRave",
        language="C++",
        hooks=(
            SourceHook("on_frame", "Source/McRave.cpp", "onFrame", "CommanderBridge.poll()", COMMON_CPP_INJECTION),
            SourceHook("strategy", "Source/Strategy/**", "updateStrategy", "bias Zerg plan selection", "two-hatch muta/lurker commitments must alter strategy scoring"),
            SourceHook("production", "Source/Production/**", "updateProduction", "inject larva/build/upgrade hard goals", "Zerg goals must respect larva/supply economy"),
            SourceHook("squad", "Source/Combat/**", "updateCombat", "inject harass and avoid-main-army objectives", "muta/ling objectives must be squad-level"),
            SourceHook("micro", "Source/Micro/**", "updateMicro", "prioritize worker targets and danger retreats", "muta/scourge doctrine requires micro scoring"),
            SourceHook("telemetry", "Source/Diagnostics/**", "log", "emit command telemetry", "intent adherence must be measurable"),
        ),
    ),
    "Stardust": BackendHookPlan(
        backend="Stardust",
        language="C++",
        hooks=(
            SourceHook("on_frame", "src/StardustAIModule.cpp", "onFrame", "CommanderBridge.poll()", COMMON_CPP_INJECTION),
            SourceHook("strategy", "src/Strategist/**", "update", "bias Protoss strategy choices", "two-gate/reaver commitments affect tech and army posture"),
            SourceHook("production", "src/Builder/**", "update", "inject probe/build/upgrade goals", "goals must use existing build placement and production logic"),
            SourceHook("squad", "src/Combat/**", "update", "inject pressure/reaver objectives", "squad-level target selection preserves bot autonomy"),
            SourceHook("micro", "src/Units/**", "micro", "apply dragoon/reaver target and retreat doctrine", "doctrine belongs in unit micro controllers"),
            SourceHook("telemetry", "src/Debug/**", "log", "emit JSONL telemetry", "verifier needs replay-aligned events"),
        ),
    ),
    "Ecgberht": BackendHookPlan(
        backend="Ecgberht",
        language="Java",
        hooks=(
            SourceHook("on_frame", "src/main/java/**/Ecgberht.java", "onFrame", "CommanderQueueConsumer.poll()", "Java BWAPI4J bot should poll outside LLM process"),
            SourceHook("strategy", "src/main/java/**/Strategy*.java", "update", "bias Terran bio/mech strategy", "Terran commandability starts at strategy selection"),
            SourceHook("production", "src/main/java/**/Production*.java", "update", "inject SCV/factory/siege goals", "production manager owns feasibility"),
            SourceHook("squad", "src/main/java/**/Squad*.java", "update", "inject vulture harass/tank contain objectives", "tactical objectives should not bypass BWAPI4J bot planners"),
            SourceHook("micro", "src/main/java/**/Micro*.java", "update", "apply vulture/tank/vessel doctrine", "micro target rules are source-level hooks"),
            SourceHook("telemetry", "src/main/java/**/Debug*.java", "log", "write JSONL telemetry", "runtime reports require status evidence"),
        ),
    ),
}


def get_hook_plan(backend: str) -> BackendHookPlan:
    if backend not in HOOK_PLANS:
        raise ValueError(f"no hook plan for backend: {backend}")
    return HOOK_PLANS[backend]


def write_hook_plan(backend: str, output_dir: Path) -> Path:
    plan = get_hook_plan(backend)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{backend}_HOOK_PLAN.md"
    path.write_text(plan.render_markdown(), encoding="utf-8")
    return path
