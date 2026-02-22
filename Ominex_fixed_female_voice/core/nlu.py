# core/nlu.py
import re
from dataclasses import dataclass

@dataclass
class Intent:
    name: str
    slots: dict

# All patterns in one place
_PAT = {
    # Utilities / reasoning
    "calc":       re.compile(r"\b(calc(ulate)?|what is|=)\b", re.I),
    "convert":    re.compile(r"\b(convert|in\s+(?:meters|km|cm)|celsius|fahrenheit)\b", re.I),
    "plan":       re.compile(r"\b(plan|steps|roadmap|how do i)\b", re.I),
    "compare":    re.compile(r"\b(compare|pros and cons|vs\.?)\b", re.I),
    "summarize":  re.compile(r"\b(summar(?:y|ise)|tl;dr|short version)\b", re.I),

    # Web lookup
    "web_query":  re.compile(r"\b(search|look\s*up|lookup|find)\b", re.I),
    "wh_q":       re.compile(r"^\s*(who|what|when|where|why|how)\b.*\?*$", re.I),
    "latest":     re.compile(r"\b(latest|news|update)\b", re.I),

    # Tasks
    "todo_add":   re.compile(r"\b(add|remember)\s+(this\s+)?(task|to[-\s]?do)\b", re.I),
    "todo_list":  re.compile(r"\b(list|show)\s+(tasks?|todos?)\b", re.I),
    "todo_done":  re.compile(r"\b(done|finish|complete)\s+(task\s*)?#?(\d+)\b", re.I),
    "todo_clear": re.compile(r"\b(clear|delete|remove)\s+(all\s+)?(tasks?|todos?)\b", re.I),
}

def detect_intent(text: str) -> Intent | None:
    s = (text or "").strip()
    if not s:
        return None

    # Utilities / reasoning
    if _PAT["calc"].search(s):
        return Intent("calc", {"expression": s})
    if _PAT["convert"].search(s):
        return Intent("convert", {"text": s})
    if _PAT["plan"].search(s):
        return Intent("plan", {"goal": s})
    if _PAT["compare"].search(s):
        return Intent("compare", {"text": s})
    if _PAT["summarize"].search(s):
        return Intent("summarize", {"text": s})

    # Web lookup (generic who/what/when + explicit "search")
    if _PAT["web_query"].search(s):
        q = re.split(r"\b(search|look\s*up|lookup|find)\b", s, flags=re.I, maxsplit=1)[-1].strip(" :?")
        return Intent("web_search", {"query": q or s})
    if _PAT["wh_q"].search(s) or _PAT["latest"].search(s):
        return Intent("web_search", {"query": s})

    # Tasks
    if _PAT["todo_add"].search(s):
        after = re.split(r"\b(add|remember)\s+(this\s+)?(task|to[-\s]?do)\b", s, flags=re.I, maxsplit=1)[-1].strip(" .:")
        return Intent("todo_add", {"item": after})
    if _PAT["todo_list"].search(s):
        return Intent("todo_list", {})
    m = _PAT["todo_done"].search(s)
    if m:
        return Intent("todo_done", {"id": int(m.group(3))})
    if _PAT["todo_clear"].search(s):
        return Intent("todo_clear", {})

    return None