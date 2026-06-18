from __future__ import annotations

from dataclasses import dataclass

from .models import IntentState


@dataclass(frozen=True)
class ActionCandidate:
    action: str
    base_score: float
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScoredAction:
    action: str
    final_score: float
    explanation: tuple[str, ...]


class IntentArbiter:
    """Scores bot action candidates against the active strategic contract."""

    def score(self, state: IntentState, candidate: ActionCandidate) -> ScoredAction:
        score = candidate.base_score
        reasons: list[str] = [f"base={candidate.base_score:.2f}"]
        style = state.contract.style

        if "attack" in candidate.tags:
            delta = (style.get("aggression", 0.5) - 0.5) * 1.2
            score += delta
            reasons.append(f"aggression_bias={delta:.2f}")

        if "harass" in candidate.tags:
            delta = (style.get("harass", 0.5) - 0.5) * 1.0
            score += delta
            reasons.append(f"harass_bias={delta:.2f}")

        if "expand" in candidate.tags or "worker" in candidate.tags:
            delta = (style.get("economy_greed", 0.5) - 0.5) * 0.9
            score += delta
            reasons.append(f"economy_bias={delta:.2f}")

        if "unsafe" in candidate.tags:
            delta = -style.get("defensive_safety", 0.5)
            score += delta
            reasons.append(f"safety_penalty={delta:.2f}")

        for goal in state.contract.hard_goals.values():
            if goal.action == "produce_worker" and "worker" in candidate.tags:
                score += 1.0
                reasons.append("hard_goal:produce_worker=1.00")
            if goal.action == "take_expansion" and "expand" in candidate.tags:
                score += 0.9
                reasons.append("hard_goal:take_expansion=0.90")

        for commitment in state.contract.strategic_commitments.values():
            plan = commitment.payload.get("plan")
            if plan and plan in candidate.tags:
                score += commitment.strength
                reasons.append(f"strategic_commitment:{plan}={commitment.strength:.2f}")

        for doctrine in state.contract.standing_orders.values():
            avoid = tuple(doctrine.payload.get("avoid", ()))
            rule = doctrine.payload.get("rule")
            if "main_army" in avoid and {"frontal", "main_army"} & set(candidate.tags):
                score -= 1.0
                reasons.append("micro_doctrine:avoid_main_army=-1.00")
            if rule == "retreat_low_hp" and "retreat" in candidate.tags:
                score += 0.7
                reasons.append("micro_doctrine:retreat_low_hp=0.70")

        return ScoredAction(candidate.action, round(score, 4), tuple(reasons))

    def choose(self, state: IntentState, candidates: list[ActionCandidate]) -> ScoredAction:
        if not candidates:
            raise ValueError("no action candidates provided")
        return max((self.score(state, candidate) for candidate in candidates), key=lambda item: item.final_score)
