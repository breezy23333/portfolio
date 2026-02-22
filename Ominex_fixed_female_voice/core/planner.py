
from dataclasses import dataclass
from typing import Dict
from .nlu import detect_intent
from .skills import get_registry, SkillResult
from .memory import Memory

@dataclass
class PlanOutcome:
    text: str
    meta: dict
    ask: bool = False

def plan_and_execute(user: str, memory: Memory) -> PlanOutcome:
    intent = detect_intent(user)
    if not intent:
        return PlanOutcome("", {"intent": None}, ask=False)
    skills = get_registry()
    fn = skills.get(intent.name)
    if not fn:
        return PlanOutcome("", {"intent": intent.name, "error": "no-skill"}, ask=False)
    result: SkillResult = fn(user, memory, intent.slots)
    return PlanOutcome(result.text, {"intent": intent.name, "data": result.data}, ask=result.ask)

# core/planner.py
def plan_and_execute(user_text: str, context: list[str] | None = None) -> str:
    # Expand later if you want multi-step tool chains.
    # For now just return empty to let brain fallback to chat.
    return ""