from __future__ import annotations

import re

from .models import (
    ConflictPolicy,
    CommandType,
    CommandUtterance,
    IntentAdaptivity,
    IntentPriority,
    ParsedCommand,
    Race,
    VerifierExpectation,
)

_KOREAN_NUMBERS = {
    "한": 1,
    "하나": 1,
    "두": 2,
    "둘": 2,
    "세": 3,
    "셋": 3,
    "네": 4,
    "넷": 4,
    "다섯": 5,
    "여섯": 6,
    "일곱": 7,
    "여덟": 8,
    "아홉": 9,
    "열": 10,
}


def parse_utterance(utterance: CommandUtterance) -> list[ParsedCommand]:
    text = utterance.text.strip()
    lower = text.lower()
    commands: list[ParsedCommand] = []

    cancel = _parse_cancel(lower)
    if cancel:
        return [
            ParsedCommand(
                command_type=CommandType.CONTRACT_PATCH,
                action="cancel_intent",
                scope="global",
                priority=IntentPriority.HARD,
                duration="instant",
                adaptivity=IntentAdaptivity.FIXED,
                conflict_policy=ConflictPolicy.REPLACE_SCOPE,
                payload=cancel,
                expectations=[
                    VerifierExpectation(
                        metric="cancelled_command_count",
                        operator=">=",
                        value=1,
                        description="matching active intent is cancelled",
                    )
                ],
                utterance_id=utterance.utterance_id,
            )
        ]

    if race := _parse_race(lower):
        commands.append(
            ParsedCommand(
                command_type=CommandType.CONTRACT_PATCH,
                action="set_race",
                payload={"race": race.value},
                utterance_id=utterance.utterance_id,
            )
        )

    worker_count = _parse_worker_delta(lower)
    if worker_count:
        commands.append(
            ParsedCommand(
                command_type=CommandType.HARD_GOAL,
                action="produce_worker",
                scope="economy",
                priority=IntentPriority.HARD,
                duration="until_fulfilled_or_invalid",
                adaptivity=IntentAdaptivity.SAFETY_BREAKABLE,
                conflict_policy=ConflictPolicy.SUPPRESS_LOWER_PRIORITY,
                payload={"count": worker_count, "mode": "delta"},
                expectations=[
                    VerifierExpectation(
                        metric="worker_delta",
                        operator=">=",
                        value=worker_count,
                        description=f"worker count increases by {worker_count}",
                    )
                ],
                utterance_id=utterance.utterance_id,
            )
        )

    expansion_goal = _parse_expansion_goal(lower)
    if expansion_goal:
        commands.append(
            ParsedCommand(
                command_type=CommandType.HARD_GOAL,
                action="take_expansion",
                scope="economy",
                priority=IntentPriority.HARD,
                duration="until_fulfilled_or_invalid",
                adaptivity=IntentAdaptivity.SAFETY_BREAKABLE,
                conflict_policy=ConflictPolicy.SUPPRESS_LOWER_PRIORITY,
                payload=expansion_goal,
                expectations=[
                    VerifierExpectation(
                        metric="owned_bases",
                        operator=">=",
                        value=expansion_goal["base_number"],
                        description=f"secure base {expansion_goal['base_number']}",
                    )
                ],
                utterance_id=utterance.utterance_id,
            )
        )

    for structure_goal in _parse_structure_goals(lower):
        commands.append(
            ParsedCommand(
                command_type=CommandType.HARD_GOAL,
                action="build_structure",
                scope="production",
                priority=IntentPriority.HARD,
                duration="until_fulfilled_or_invalid",
                adaptivity=IntentAdaptivity.SAFETY_BREAKABLE,
                conflict_policy=ConflictPolicy.SUPPRESS_LOWER_PRIORITY,
                payload=structure_goal,
                expectations=[
                    VerifierExpectation(
                        metric=f"built_{structure_goal['structure']}",
                        operator=">=",
                        value=structure_goal.get("count", 1),
                        description=f"build {structure_goal['structure']}",
                    )
                ],
                utterance_id=utterance.utterance_id,
            )
        )

    for upgrade_goal in _parse_upgrade_goals(lower):
        commands.append(
            ParsedCommand(
                command_type=CommandType.HARD_GOAL,
                action="research_upgrade",
                scope="tech",
                priority=IntentPriority.HARD,
                duration="until_fulfilled_or_invalid",
                adaptivity=IntentAdaptivity.SAFETY_BREAKABLE,
                conflict_policy=ConflictPolicy.SUPPRESS_LOWER_PRIORITY,
                payload=upgrade_goal,
                expectations=[
                    VerifierExpectation(
                        metric="completed_upgrades",
                        operator="contains",
                        value=upgrade_goal["upgrade"],
                        description=f"complete {upgrade_goal['upgrade']}",
                    )
                ],
                utterance_id=utterance.utterance_id,
            )
        )

    for unit_goal in _parse_unit_goals(lower):
        commands.append(
            ParsedCommand(
                command_type=CommandType.HARD_GOAL,
                action="produce_unit",
                scope="production",
                priority=IntentPriority.HARD,
                duration="until_fulfilled_or_invalid",
                adaptivity=IntentAdaptivity.SAFETY_BREAKABLE,
                conflict_policy=ConflictPolicy.SUPPRESS_LOWER_PRIORITY,
                payload=unit_goal,
                expectations=[
                    VerifierExpectation(
                        metric=f"unit_count_{unit_goal['unit']}",
                        operator=">=",
                        value=unit_goal["count"],
                        description=f"produce {unit_goal['count']} {unit_goal['unit']}",
                    )
                ],
                utterance_id=utterance.utterance_id,
            )
        )

    style = _parse_style(lower)
    if style:
        commands.append(
            ParsedCommand(
                command_type=CommandType.PERSISTENT_STYLE,
                action="set_style",
                scope="global",
                priority=IntentPriority.PREFERRED,
                duration="until_changed",
                strength=max(style.values()),
                adaptivity=IntentAdaptivity.ADAPTIVE,
                conflict_policy=ConflictPolicy.REPLACE_SCOPE,
                payload={"style": style},
                expectations=[
                    VerifierExpectation(
                        metric="intent_adherence_score",
                        operator=">=",
                        value=0.65,
                        description="style should affect aggregate behavior",
                    )
                ],
                utterance_id=utterance.utterance_id,
            )
        )

    for plan in _parse_strategic_commitments(lower):
        commands.append(
            ParsedCommand(
                command_type=CommandType.STRATEGIC_COMMITMENT,
                action="commit_strategy",
                scope="strategy",
                priority=IntentPriority.HARD,
                duration="until_cancelled_or_invalid",
                strength=0.9,
                adaptivity=IntentAdaptivity.SAFETY_BREAKABLE,
                conflict_policy=ConflictPolicy.REPLACE_SCOPE,
                payload={"plan": plan, "allow_adaptation": True},
                expectations=[
                    VerifierExpectation(
                        metric="active_strategic_commitments",
                        operator="contains",
                        value=plan,
                        description=f"{plan} commitment remains active",
                    )
                ],
                utterance_id=utterance.utterance_id,
            )
        )

    instant = _parse_instant(lower)
    if instant:
        commands.append(
            ParsedCommand(
                command_type=CommandType.INSTANT_ORDER,
                action=instant,
                scope="army",
                priority=IntentPriority.URGENT,
                duration="ttl_frames",
                adaptivity=IntentAdaptivity.FIXED,
                conflict_policy=ConflictPolicy.SAFETY_OVERRIDE,
                payload={"ttl_frames": 720},
                expectations=[
                    VerifierExpectation(
                        metric=f"{instant}_orders_issued",
                        operator=">=",
                        value=1,
                        window_frames=720,
                    )
                ],
                utterance_id=utterance.utterance_id,
            )
        )

    for doctrine in _parse_micro_doctrines(lower):
        commands.append(
            ParsedCommand(
                command_type=CommandType.MICRO_DOCTRINE,
                action="set_micro_doctrine",
                scope=doctrine["scope"],
                priority=IntentPriority.HARD,
                duration="until_changed",
                adaptivity=IntentAdaptivity.ADAPTIVE,
                conflict_policy=ConflictPolicy.REPLACE_SCOPE,
                payload=doctrine,
                expectations=[
                    VerifierExpectation(
                        metric=doctrine["metric"],
                        operator=">=",
                        value=doctrine["minimum"],
                        description=doctrine["description"],
                    )
                ],
                utterance_id=utterance.utterance_id,
            )
        )

    if _looks_like_patch(lower):
        commands.append(
            ParsedCommand(
                command_type=CommandType.CONTRACT_PATCH,
                action="patch_contract",
                scope="global",
                priority=IntentPriority.PREFERRED,
                adaptivity=IntentAdaptivity.ADAPTIVE,
                conflict_policy=ConflictPolicy.REPLACE_SCOPE,
                payload={"preserve_existing": True},
                utterance_id=utterance.utterance_id,
                ambiguity_score=0.35,
            )
        )

    if not commands:
        return [
            ParsedCommand(
                command_type=CommandType.CONTRACT_PATCH,
                action="unparsed",
                priority=IntentPriority.ADVISORY,
                payload={"raw_text": text, "requires_clarification": True},
                utterance_id=utterance.utterance_id,
                confidence=0.0,
                ambiguity_score=1.0,
            )
        ]

    return commands


def _parse_race(text: str) -> Race | None:
    if "저그" in text or "zerg" in text:
        return Race.ZERG
    if "프로토스" in text or "토스" in text or "protoss" in text:
        return Race.PROTOSS
    if "테란" in text or "terran" in text:
        return Race.TERRAN
    return None


def _parse_worker_delta(text: str) -> int | None:
    if not any(token in text for token in ["일꾼", "드론", "프로브", "scv", "worker", "drone", "probe"]):
        return None
    number = _first_number(text)
    if number is None:
        return None
    if any(token in text for token in ["더", "추가", "more", "additional"]):
        return number
    return number


def _parse_expansion_goal(text: str) -> dict[str, int | str] | None:
    if not any(token in text for token in ["멀티", "확장", "third", "expand"]):
        return None
    if any(token in text for token in ["3멀티", "삼멀티", "third"]):
        return {"base_number": 3, "mode": "at_least"}
    if any(token in text for token in ["앞마당", "natural", "2멀티"]):
        return {"base_number": 2, "mode": "at_least"}
    return None


def _parse_structure_goals(text: str) -> list[dict[str, object]]:
    goals: list[dict[str, object]] = []
    patterns = {
        "spire": ["스파이어", "spire"],
        "factory": ["팩토리", "factory"],
        "gateway": ["게이트", "gateway"],
        "robotics_facility": ["로보틱스", "robotics"],
        "sunken_colony": ["성큰", "sunken"],
        "photon_cannon": ["캐논", "cannon"],
        "missile_turret": ["터렛", "turret"],
    }
    for segment in _segments(text):
        if not any(token in segment for token in ["지어", "건설", "build", "박아"]):
            continue
        count = _first_number(segment) or 1
        for structure, tokens in patterns.items():
            if any(token in segment for token in tokens):
                goals.append({"structure": structure, "count": count})
    return goals


def _parse_upgrade_goals(text: str) -> list[dict[str, object]]:
    goals: list[dict[str, object]] = []
    patterns = {
        "dragoon_range": ["드라군 사업", "사업", "dragoon range", "goon range"],
        "siege_mode": ["시즈모드", "시즈 모드", "siege mode"],
        "spider_mines": ["마인업", "마인 업", "spider mines"],
        "zergling_speed": ["링 발업", "저글링 발업", "ling speed"],
        "lurker_aspect": ["럴커 업", "lurker aspect"],
    }
    for segment in _segments(text):
        if not any(token in segment for token in ["업", "연구", "먼저", "research", "upgrade", "사업", "mode"]):
            continue
        for upgrade, tokens in patterns.items():
            if any(token in segment for token in tokens):
                goals.append({"upgrade": upgrade})
    return goals


def _parse_unit_goals(text: str) -> list[dict[str, object]]:
    goals: list[dict[str, object]] = []
    patterns = {
        "mutalisk": ["뮤탈", "mutalisk", "muta"],
        "zergling": ["저글링", "링 ", "zergling"],
        "dragoon": ["드라군", "dragoon", "goon"],
        "reaver": ["리버", "reaver"],
        "vulture": ["벌처", "vulture"],
        "siege_tank": ["탱크", "tank"],
        "marine": ["마린", "marine"],
    }
    for segment in _segments(text):
        if not any(token in segment for token in ["찍", "생산", "뽑", "produce", "make"]):
            continue
        count = _first_number(segment)
        if count is None:
            continue
        for unit, tokens in patterns.items():
            if any(token in segment for token in tokens):
                goals.append({"unit": unit, "count": count, "mode": "at_least"})
    return goals


def _parse_cancel(text: str) -> dict[str, object] | None:
    if not any(token in text for token in ["취소", "그만", "cancel", "stop"]):
        return None
    plans = _parse_strategic_commitments(text)
    if plans:
        return {"target_action": "commit_strategy", "target_plan": plans[0]}
    if any(token in text for token in ["공격", "attack"]):
        return {"target_action": "attack"}
    if any(token in text for token in ["견제", "micro", "doctrine"]):
        return {"target_action": "set_micro_doctrine"}
    return {"all": True}


def _parse_style(text: str) -> dict[str, float]:
    style: dict[str, float] = {}
    if any(token in text for token in ["침략", "공격적", "aggressive", "pressure"]):
        style.update({"aggression": 0.85, "harass": 0.7, "economy_greed": 0.35})
    if any(token in text for token in ["수비", "안전", "defensive", "safe"]):
        style.update({"defensive_safety": 0.85, "aggression": min(style.get("aggression", 0.45), 0.45)})
    if any(token in text for token in ["부유", "운영", "확장", "greedy", "macro", "expand"]):
        style.update({"economy_greed": 0.85, "defensive_safety": max(style.get("defensive_safety", 0.55), 0.55)})
    if any(token in text for token in ["견제", "흔들", "harass"]):
        style.update({"harass": 0.9})
    if any(token in text for token in ["올인 하지마", "올인은 하지", "no all-in", "no allin"]):
        style.update({"all_in_commitment": 0.0})
    return style


def _parse_strategic_commitments(text: str) -> list[str]:
    plans: list[str] = []
    patterns = {
        "two_hatch_muta": ["2햇 뮤탈", "투햇 뮤탈", "two hatch muta", "two-hatch muta"],
        "lurker_contain": ["럴커 조이기", "lurker contain"],
        "two_gate_pressure": ["2게이트", "투게이트", "two gate", "two-gate"],
        "reaver_harass": ["리버 견제", "reaver harass"],
        "vulture_harass": ["벌처 견제", "vulture harass", "vultures"],
        "tank_contain": ["탱크 조이기", "tank contain"],
    }
    for plan, tokens in patterns.items():
        if any(token in text for token in tokens):
            plans.append(plan)
    return plans


def _parse_instant(text: str) -> str | None:
    if any(token in text for token in ["지금 공격", "공격해", "attack now"]):
        return "attack"
    if any(token in text for token in ["후퇴", "빼", "retreat", "fall back"]):
        return "retreat"
    return None


def _parse_micro_doctrines(text: str) -> list[dict[str, object]]:
    doctrines: list[dict[str, object]] = []
    if any(token in text for token in ["일꾼만", "worker only", "workers only"]):
        doctrines.append(
            {
                "scope": "harass_squads",
                "target_priority": ["worker"],
                "avoid": ["main_army"],
                "metric": "worker_target_ratio",
                "minimum": 0.65,
                "description": "harass squads should prioritize workers",
            }
        )
    if any(token in text for token in ["정면 싸움", "main army", "frontal"]):
        doctrines.append(
            {
                "scope": "harass_squads",
                "rule": "avoid_main_army",
                "metric": "main_army_avoidance_ratio",
                "minimum": 0.75,
                "description": "harass squads should avoid main army fights",
            }
        )
    if any(token in text for token in ["체력 낮", "low hp", "피 없"]):
        doctrines.append(
            {
                "scope": "combat_squads",
                "rule": "retreat_low_hp",
                "metric": "low_hp_retreat_ratio",
                "minimum": 0.75,
                "description": "low hp units should retreat",
            }
        )
    return doctrines


def _looks_like_patch(text: str) -> bool:
    return any(token in text for token in ["유지하되", "아까", "keep existing", "keep previous", "but now", "except"])


def _first_number(text: str) -> int | None:
    match = re.search(r"\d+", text)
    if match:
        return int(match.group(0))
    for word, value in _KOREAN_NUMBERS.items():
        if word in text:
            return value
    return None


def _segments(text: str) -> list[str]:
    return [segment.strip() for segment in re.split(r"[.。!?]|(?:\s+그리고\s+)|(?:\s+and\s+)", text) if segment.strip()]
