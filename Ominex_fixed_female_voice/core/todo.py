# core/todo.py
import json, os, time
from typing import List, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
TASKS_PATH = os.path.join(DATA_DIR, "tasks.json")

def _load() -> Dict[str, Any]:
    if not os.path.exists(TASKS_PATH):
        return {"tasks": []}
    with open(TASKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(obj: Dict[str, Any]) -> None:
    with open(TASKS_PATH, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

class TodoStore:
    def __init__(self) -> None:
        self._cache = _load()

    def add(self, text: str) -> int:
        t = {"text": text.strip(), "done": False, "at": time.time()}
        self._cache["tasks"].append(t)
        _save(self._cache)
        return len(self._cache["tasks"])

    def list(self) -> List[Dict[str, Any]]:
        return self._cache.get("tasks", [])

    def done(self, index: int) -> bool:
        arr = self._cache.get("tasks", [])
        i = index - 1
        if 0 <= i < len(arr):
            arr[i]["done"] = True
            _save(self._cache)
            return True
        return False

    def clear(self) -> None:
        self._cache["tasks"] = []
        _save(self._cache)