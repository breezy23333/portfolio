# core/router.py
from dataclasses import dataclass
from typing import Literal

Mode = Literal["full", "demo"]

@dataclass
class RouteDecision:
    intent: str            # "trade" | "news" | "wiki" | "search" | "weather" | "crypto" | "summarize" | "brain"
    payload: str           # cleaned query (or original text)
    blocked: bool = False
    reason: str = ""

DEMO_BLOCKED_WORDS = ("trade", "buy", "sell", "delete", "system", "file", "learn", "alert", "backtest")

def decide(user_msg: str, mode: Mode = "full") -> RouteDecision:
    msg = (user_msg or "").strip()
    lower = msg.lower()

    # demo restrictions
    if mode == "demo" and any(w in lower for w in DEMO_BLOCKED_WORDS):
        return RouteDecision(intent="brain", payload=msg, blocked=True, reason="Disabled in demo mode.")

    # intents
    if lower.startswith(("trade ", "plan ", "signal ")):
        return RouteDecision("trade", msg)

    if any(k in lower for k in (" latest ", "latest", "news", "headline", "breaking")):
        q = (msg.replace("latest", "").replace("news", "").replace("headline", "").replace("breaking", "").strip()) or msg
        return RouteDecision("news", q)

    if lower.startswith(("wiki ", "wikipedia ", "who is ", "what is ", "define ")):
        q = (msg.replace("wiki ", "", 1).replace("wikipedia ", "", 1)
               .replace("who is ", "", 1).replace("what is ", "", 1)
               .replace("define ", "", 1).strip()) or msg
        return RouteDecision("wiki", q)

    if lower.startswith(("search ", "look up ")) or "google " in lower:
        q = (msg.replace("search", "", 1).replace("look up", "", 1).replace("google", "", 1).strip()) or msg
        return RouteDecision("search", q)

    if lower.startswith("weather "):
        place = msg.split(" ", 1)[1] if " " in msg else "Cape Town"
        return RouteDecision("weather", place)

    if lower.startswith(("crypto ", "price ")):
        coin = msg.split(" ", 1)[1] if " " in msg else "bitcoin"
        return RouteDecision("crypto", coin)

    if lower.startswith(("summarize ", "read ", "open ")):
        u = msg.split(" ", 1)[1] if " " in msg else ""
        return RouteDecision("summarize", u)

    return RouteDecision("brain", msg)
