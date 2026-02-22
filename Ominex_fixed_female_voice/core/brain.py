
# core/brain.py — OMINEX Core Brain (CLEAN STABLE)
# Single entry: think()
from services.llm import ask_ominex
from typing import Any, Dict, Optional, Tuple, List
import re
import requests
from datetime import datetime


# Core systems
from .memory import Memory
from .mood import detect_mood
from .planner import plan_and_execute
from .conversion import temp_convert, length_convert, weight_convert, currency_convert
from .todo import TodoStore
from .web import search_web, news_latest, format_news, search_and_summarize


# Optional systems (graceful fallback)
try:
    from .safety import safe
except Exception:
    class _Safe:
        def scan(self, text: str) -> Dict[str, Any]:
            return {"ok": True}
    safe = _Safe()

try:
    from .kb import kb_query
except Exception:
    def kb_query(*args, **kwargs):
        return {}

try:
    from .learner import learn_auto as learn_verify_store
except Exception:
    def learn_verify_store(topic, *args, **kwargs):
        return {"facts_stored": 0, "topic": topic, "considered_pages": 0, "sample": []}

try:
    from .learner import learn_autoroute
except Exception:
    learn_autoroute = None


# -------------------- STATE --------------------
mem = Memory()
todos = TodoStore()


# -------------------- INTENT SYSTEM --------------------
_RX = {
    "remember": re.compile(r"\b(remember that|remember this|save this|note that|store this)\b", re.I),
    "recall": re.compile(r"\b(recall|what did i say|memory)\b", re.I),
    "clear_memory": re.compile(r"\b(clear memory|reset memory)\b", re.I),
    "calculate": re.compile(r"^\s*(?:calc|calculate)\b|^\s*[+\-/*().\d\s]{3,}\s*$", re.I),

    "search": re.compile(
    r"\b(search|look up|find|google|wiki)\b",
    re.I
        ),

    "time": re.compile(r"\b(time now|date now|what time)\b", re.I),
    "help": re.compile(r"\b(help|what can you do)\b", re.I),
    "news": re.compile(r"\b(news|latest|headlines)\b", re.I),
    "greet": re.compile(r"\b(hi|hello|hey|molo)\b", re.I),
    "convert": re.compile(r"\bconvert\b", re.I),
    "task_add": re.compile(r"\b(add task|todo)\b", re.I),
    "task_list": re.compile(r"\b(list tasks|show tasks)\b", re.I),
}

def _classify_intent(text: str) -> str:
    for name, rx in _RX.items():
        if rx.search(text):
            return name
    return "chat"


def conversational_response(text: str):
    text = text.lower()

    if "who made you" in text:
        return "I was built by Luvo Maphela as part of the OMINEX system."

    if "what is python" in text:
        return "Python is a high-level programming language used for AI, web development, automation, and more."

    if "what is infinite" in text or "what is infinity" in text:
        return "Infinity is the concept of something without limit or end. It is used in mathematics, philosophy, and physics to describe endlessness."

    if "hello" in text or "hi" in text:
        return "Hello. OMINEX online."

    return "I'm processing that. Tell me more."


# -------------------- HELPERS --------------------
def _safe_calc(text: str) -> Optional[str]:
    if not re.fullmatch(r"[+\-/*().\d\s]{3,}", text.strip()):
        return None
    try:
        result = eval(text, {"__builtins__": {}}, {})
        return f"{text} = **{result}**"
    except Exception:
        return None


def _now_string():
    return datetime.now().strftime("%A, %d %B %Y • %H:%M")


# -------------------- MAIN BRAIN --------------------


def think(user_text: str,
          user_mood: Optional[str] = None,
          ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

    ctx = ctx or {}

    # Safety
    s = safe.scan(user_text)
    if not s.get("ok", True):
        return {
            "intent": "refuse",
            "reply": "I can’t help with that.",
            "mood": "Neutral",
            "tts": {"pitch": 0.98, "rate": 0.98},
        }

    mood = user_mood or detect_mood(user_text) or "Neutral"
    intent = _classify_intent(user_text)
    # 🔒 HARD IDENTITY LOCK (NO FALLTHROUGH)
    if "who made you" in user_text.lower():
        reply = "I was built by Luvo Maphela as part of the OMINEX system."
        try:
            mem.add_turn(role="assistant", text=reply)
        except Exception:
            pass

        return {
            "intent": "identity",
            "reply": reply,
            "mood": mood,
            "tts": {"pitch": 1.0, "rate": 1.0},
        }

    
    # Identity & hard-coded responses
    identity = conversational_response(user_text)
    if identity and "OMINEX" in identity:
        try:
            mem.add_turn(role="assistant", text=identity)
        except Exception:
            pass

        return {
            "intent": "identity",
            "reply": identity,
            "mood": mood,
            "tts": {"pitch": 1.0, "rate": 1.0},
        }

    
    print("DEBUG INTENT:", intent, "TEXT:", user_text)

    # Record user turn
    try:
        mem.add_turn(role="user", text=user_text)
    except Exception:
        pass

    reply = ""

    # ---------------- INTENT HANDLING ----------------

    if intent == "help":
        reply = "You can ask me to search, learn, plan, convert, remember, or summarize."

    elif intent == "time":
        reply = f"It’s {_now_string()}."

    elif intent == "remember":
        fact = re.sub(_RX["remember"], "", user_text, count=1).strip(": -")
        if fact:
            try:
                mem.remember(fact, importance=0.7, source="user")
                reply = "Got it — I’ll remember that."
            except Exception:
                reply = "I tried to remember that."
        else:
            reply = "Tell me what to remember."

    elif intent == "recall":
        try:
            hits = mem.search(user_text, k=5)
            if hits:
                reply = "Here’s what I remember:\n• " + "\n• ".join(
                    h if isinstance(h, str) else getattr(h, "text", "")
                    for h in hits
                )
            else:
                reply = "I don’t have anything on that yet."
        except Exception:
            reply = "Memory unavailable."

    elif intent == "calculate":
        calc = _safe_calc(user_text)
        reply = calc or "I couldn’t compute that safely."

    elif intent == "search":
        cleaned = re.sub(_RX["search"], "", user_text, count=1).strip()
        cleaned = cleaned or user_text

        try:
            result = search_and_summarize(cleaned)
            if not result:
                reply = f"I couldn't find results for '{cleaned}'."
            else:
                reply = result
        except Exception as e:
            reply = f"Search system error: {str(e)}"



    elif intent == "news":
        items = news_latest(None)
        reply = format_news(items)

    elif intent == "convert":
        m = re.search(r"(-?\d+(?:\.\d+)?)\s*([a-zA-Z]+)\s*(?:to|in)\s*([a-zA-Z]+)", user_text)
        if m:
            val = float(m.group(1))
            src = m.group(2)
            dst = m.group(3)
            try:
                for fn in (temp_convert, length_convert, weight_convert, currency_convert):
                    try:
                        out = fn(val, src, dst)
                        reply = f"{val:g} {src} ≈ {out:g} {dst}"
                        break
                    except Exception:
                        continue
                if not reply:
                    reply = "Unsupported conversion."
            except Exception:
                reply = "Conversion failed."
        else:
            reply = "Try: convert 5 kg to lb."

    elif intent == "task_add":
        task = user_text.split(" ", 1)[-1]
        idx = todos.add(task)
        reply = f"Added task #{idx}: {task}"

    elif intent == "task_list":
        items = todos.list()
        reply = "Tasks:\n" + "\n".join(f"{i}. {t}" for i, t in enumerate(items)) if items else "No tasks."

    else:
    # 1️⃣ Try KB
        try:
            kb = kb_query(user_text, k=4)
            if kb.get("answer"):
                reply = kb["answer"]
        except Exception:
            pass

        # 2️⃣ Try planner
        if not reply:
            try:
                planned = plan_and_execute(user_text=user_text, context=[])
                if planned:
                    reply = planned
            except Exception:
                pass

        # 3️⃣ REAL LLM (THIS IS THE IMPORTANT PART)
        if not reply:
            try:
                reply = ask_ominex(user_text)
                intent = "chat"
            except Exception:
                # 4️⃣ ONLY if LLM fails → demo fallback
                reply = conversational_response(user_text)
                intent = "chat"

        # Save assistant turn
        try:
            mem.add_turn(role="assistant", text=reply)
        except Exception:
            pass

    return {
        "intent": intent,
        "reply": reply,
        "mood": mood,
        "tts": {"pitch": 1.0, "rate": 1.0},
    }
