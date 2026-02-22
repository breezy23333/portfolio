# core/safety.py
import re

_BLOCK = [
    re.compile(r"how to make (?:a )?bomb", re.I),
    re.compile(r"hard drugs|cook meth|fentanyl", re.I),
    re.compile(r"credit card generator|carding", re.I),
]

class _Safe:
    def scan(self, text: str):
        for r in _BLOCK:
            if r.search(text or ""):
                return {"ok": False, "message": "I can’t help with that, but I can suggest safer alternatives."}
        return {"ok": True}

safe = _Safe()