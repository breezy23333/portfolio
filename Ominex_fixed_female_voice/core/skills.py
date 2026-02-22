
import math, re
from dataclasses import dataclass
from typing import Callable, Any, Dict, List
from .memory import Memory
from .web import search_and_summarize
import re
from datetime import datetime

@dataclass
class SkillResult:
  text: str
  data: Any = None
  ask: bool = False           # <-- if True, frontend treats as clarifying question

SkillFn = Callable[[str, Memory, Dict], SkillResult]
_REGISTRY: dict[str, SkillFn] = {}

def skill(name: str):
  def deco(fn: SkillFn):
    _REGISTRY[name] = fn
    return fn
  return deco

def get_registry() -> dict[str, SkillFn]:
  return dict(_REGISTRY)

_NUM = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"

@skill("calc")
def calc_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
  expr = slots.get("expression","")
  m = re.search(rf"({_NUM}(?:\s*[-+/*^]\s*{_NUM})+)", expr)
  if not m:
    return SkillResult("What should I calculate? (example: 7*(12-5)^2)", ask=True)
  try:
    safe = m.group(1).replace("^","**")
    val = eval(safe, {"__builtins__": {}}, {"math": math})
    return SkillResult(f"{safe} = {val}", {"result": val})
  except Exception:
    return SkillResult("I couldn't evaluate that expression safely.")

@skill("convert")
def convert_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
  s = slots.get("text","").lower()
  tm = re.search(rf"({_NUM})\s*(c|celsius|f|fahrenheit)\b", s)
  if tm:
    x = float(tm.group(1)); unit = tm.group(2)
    if unit.startswith("c"):
      f = x*9/5+32
      return SkillResult(f"{x:g}°C is {f:.2f}°F")
    else:
      c = (x-32)*5/9
      return SkillResult(f"{x:g}°F is {c:.2f}°C")
  lm = re.search(rf"({_NUM})\s*(km|m|cm)\b", s)
  if lm:
    x = float(lm.group(1)); unit = lm.group(2)
    meters = x*1000 if unit=="km" else x/100 if unit=="cm" else x
    return SkillResult(f"{x:g}{unit} = {meters/1000:.3f}km = {meters:.2f}m = {meters*100:.0f}cm")
  return SkillResult("Convert what? (examples: 25 C, 180 cm, 3 km)", ask=True)

@skill("plan")
def plan_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
  g = slots.get("goal","").strip()
  if len(g.split()) < 3:
    return SkillResult("What do you want to plan? (e.g., plan my portfolio website)", ask=True)
  steps: List[str] = []
  text = g.lower()
  if "portfolio" in text:
    steps = [
      "Define structure (home, projects, about, contact).",
      "Gather 5–8 showcase pieces with short case notes.",
      "Design hero section (headline + sub + CTA).",
      "Implement responsive layout & dark mode.",
      "Add contact form + social links.",
      "Polish: performance, accessibility, favicon, meta."
    ]
  elif "weight" in text or "fat" in text:
    steps = [
      "Set a 2–4 week target and track baseline.",
      "Plan daily 20–30 min workouts (HIIT + walks).",
      "Dial in nutrition (protein, fiber, calories).",
      "Sleep 7–9 hours; hydrate.",
      "Weekly check-in; adjust plan."
    ]
  else:
    steps = [
      "Define the outcome in one sentence.",
      "List constraints (time, tools, budget).",
      "Break into 3–6 concrete steps.",
      "Pick the first step you can do in 10 minutes.",
      "Schedule a review checkpoint."
    ]
  out = "Here’s a quick plan:\n- " + "\n- ".join(steps) + "\n\nWhat’s the first step you want to take?"
  return SkillResult(out, {"steps": steps})

@skill("compare")
def compare_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
    t = slots.get("text", "")
    m = re.search(r"\b(.+?)\s+vs\.?\s+(.+)", t, re.I)
    if not m:
        return SkillResult("Compare which two things? (say: A vs B)", ask=True)
    a, b = m.group(1).strip(), m.group(2).strip()

    # Use Python f-strings (not JS-style ${...})
    template = (
        f"{a} vs {b}\n"
        f"Pros of {a}: • • •\n"
        f"Cons of {a}: • • •\n"
        f"Pros of {b}: • • •\n"
        f"Cons of {b}: • • •\n"
        "Pick based on: budget • speed • quality • simplicity."
    )
    return SkillResult(template)

@skill("summarize")
def summarize_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
    txt = slots.get("text", "").strip()
    if len(txt.split()) < 8:
        return SkillResult("Paste the text you want summarized.", ask=True)

    # Correct regex and sort key
    sentences = re.split(r"(?<=[.!?])\s+", txt)
    top = sorted(sentences, key=len, reverse=True)[:3]

    return SkillResult("Summary:\n- " + "\n- ".join(s.strip() for s in top))

# ---------- TASK SKILLS ----------

def _format_tasks(tasks: List[dict]) -> str:
    if not tasks:
        return "No tasks yet."
    lines = []
    for t in tasks:
        box = "✔" if t.get("done") else "□"
        lines.append(f"{t['id']:>2}. {box} {t['text']}")
    return "Tasks:\n" + "\n".join(lines)

@skill("todo_add")
def todo_add_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
    item = (slots.get("item") or "").strip()
    if not item:
        return SkillResult("Add what task? (e.g., add task finish hero section)", ask=True)
    t = mem.add_task(item)
    return SkillResult(f"Added task #{t['id']}: {t['text']}\n\n" + _format_tasks(mem.list_tasks()))

@skill("todo_list")
def todo_list_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
    tasks = mem.list_tasks()
    return SkillResult(_format_tasks(tasks), {"tasks": tasks})

@skill("todo_done")
def todo_done_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
    tid = slots.get("id")
    if not isinstance(tid, int):
        return SkillResult("Which task number is done? (say: done #2)", ask=True)
    ok = mem.mark_done(tid)
    if not ok:
        return SkillResult(f"I couldn’t find task #{tid}.")
    return SkillResult(f"Marked task #{tid} as done.\n\n" + _format_tasks(mem.list_tasks()))

@skill("todo_clear")
def todo_clear_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
    mem.clear_tasks()
    return SkillResult("All tasks cleared.")

@skill("web_search")
def web_search_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
    q = (slots.get("query") or "").strip()
    if not q:
        return SkillResult("What should I look up? (e.g., search who invented Python)", ask=True)

    summary, sources = search_and_summarize(q, max_sources=3)

    if not sources:
        return SkillResult(summary or "No results yet.")

    # Format sources
    lines = [f"- {s.title} — {s.url}" for s in sources]
    body = summary.strip()
    reply = f"{body}\n\nSources:\n" + "\n".join(lines)
    return SkillResult(reply, {"sources": [s.__dict__ for s in sources]})

@skill("web_search")
def web_search_skill(user: str, mem: Memory, slots: Dict) -> SkillResult:
    q = (slots.get("query") or "").strip()
    if not q:
        return SkillResult("What should I look up? (e.g., search who invented Python)", ask=True)

    summary, sources = search_and_summarize(q, max_sources=3)
    if not sources:
        return SkillResult(summary)  # graceful fallback message

    # Pretty list of sources
    lines = [f"- {s.title} — {s.url}" for s in sources]
    reply = f"{summary}\n\nSources:\n" + "\n".join(lines)
    return SkillResult(reply, {"sources": [s.__dict__ for s in sources]})

def _safe_calc(text: str):
    m = re.search(r"([-+/*().\d\s]+)", text)
    if not m: return "Tell me the equation to calculate."
    expr = m.group(1).strip()
    if re.search(r"[^0-9+\-*/().\s]", expr): return "I couldn't compute that safely."
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        return f"{expr} = **{result}**"
    except Exception:
        return "I couldn't compute that safely."

def _time_now(_: str):
    now = datetime.now()
    return now.strftime("It's %A, %d %B %Y • %H:%M")

def _echo(text: str):
    return text

skills = {
    "calculator": lambda payload: _safe_calc(payload.get("text","")),
    "time.now":   lambda payload: _time_now(payload.get("text","")),
    "echo":       lambda payload: _echo(payload.get("text","")),
}