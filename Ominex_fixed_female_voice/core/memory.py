import json, os
from datetime import datetime
from typing import Any, List, Dict
import json, os, time, math
from typing import Any, Dict, List
from math import exp


class Memory:
    def __init__(self, path: str = "memory.json"):
        self.path = path
        self.db: Dict[str, Any] = {"version": 2, "notes": [], "knowledge": []}
        if os.path.exists(path):
            try:
                self.db = json.load(open(path, "r", encoding="utf-8"))
            except Exception:
                pass

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)

    # ---- NEW: knowledge upsert/search/decay ----
    def upsert_knowledge(self, item: Dict[str, Any]) -> None:
        """
        item schema:
        {
          "id": str,                       # stable hash of content
          "topic": str,
          "content": str,                  # concise summary / fact(s)
          "sources": [{"url": str, "title": str}], 
          "confidence": float,             # 0..1
          "created_at": float,             # time.time()
          "updated_at": float,
          "tags": ["news","finance"],      # arbitrary
          "ttl": float | None              # seconds, optional
        }
        """
        existing = next((k for k in self.db["knowledge"] if k["id"] == item["id"]), None)
        if existing:
            # merge: keep best confidence, union sources, update timestamp
            existing["confidence"] = max(existing.get("confidence", 0), item.get("confidence", 0))
            seen = {s["url"] for s in existing.get("sources", [])}
            for s in item.get("sources", []):
                if s["url"] not in seen:
                    existing["sources"].append(s)
                    seen.add(s["url"])
            existing["content"] = item.get("content", existing["content"])
            existing["topic"] = item.get("topic", existing["topic"])
            existing["tags"] = sorted(list(set(existing.get("tags", []) + item.get("tags", []))))
            existing["updated_at"] = time.time()
            if item.get("ttl") is not None:
                existing["ttl"] = item["ttl"]
        else:
            self.db["knowledge"].append(item)
        self._save()

    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        q = query.lower()
        scored = []
        for k in self.db["knowledge"]:
            text = (k.get("topic","") + " " + k.get("content","")).lower()
            score = sum(1 for token in q.split() if token in text) + k.get("confidence",0)
            # freshness boost (you can tweak decay_rate)
            age_days = max(0.0, (time.time() - k.get("updated_at", k.get("created_at", time.time()))) / 86400.0)
            freshness = exp(-0.03 * age_days)  # slower decay
            scored.append((score + 0.5*freshness, k))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [k for _, k in scored[:limit]]

    def decay(self, decay_rate_per_day: float = 0.01) -> None:
        now = time.time()
        changed = False
        kept = []
        for k in self.db["knowledge"]:
            age_days = (now - k.get("updated_at", k.get("created_at", now))) / 86400.0
            k["confidence"] = max(0.0, k.get("confidence", 0.5) * exp(-decay_rate_per_day * age_days))
            if k.get("ttl") and now - k["created_at"] > k["ttl"]:
                changed = True
                continue  # drop expired
            kept.append(k)
        if changed:
            self.db["knowledge"] = kept
            self._save()

     
class Memory:
    def __init__(self, path: str = "data/memory.json") -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._data = {
            "notes": [],
            "profile": {},
            "tasks": [],   # ⬅️ add
            "created": datetime.utcnow().isoformat(timespec="seconds"),
        }
        self._load()

    # ... keep _load() and save() as you have them ...

    # ---------- notes ----------
    def add_note(self, text: str) -> None:
        if not text: 
            return
        self._data.setdefault("notes", []).append(text)
        self.save()

    def list_notes(self) -> List[str]:
        return list(self._data.get("notes") or [])

    # ---------- profile ----------
    def set_profile(self, key: str, value: Any) -> None:
        self._data.setdefault("profile", {})[key] = value
        self.save()

    def get_profile(self, key: str, default: Any = None) -> Any:
        return (self._data.get("profile") or {}).get(key, default)

    # ---------- tasks ----------
    def add_task(self, text: str) -> Dict:
        t = {"id": self._next_task_id(), "text": text, "done": False}
        self._data.setdefault("tasks", []).append(t)
        self.save()
        return t

    def list_tasks(self, include_done: bool = True) -> List[Dict]:
        tasks = list(self._data.get("tasks") or [])
        return tasks if include_done else [t for t in tasks if not t.get("done")]

    def mark_done(self, task_id: int) -> bool:
        for t in self._data.get("tasks", []):
            if t.get("id") == task_id:
                t["done"] = True
                self.save()
                return True
        return False

    def clear_tasks(self) -> None:
        self._data["tasks"] = []
        self.save()

    def _next_task_id(self) -> int:
        tasks = self._data.get("tasks") or []
        return (max([t.get("id", 0) for t in tasks]) + 1) if tasks else 1

    # ---------- reset ----------
    def clear(self) -> None:
        self._data["notes"] = []
        self._data["profile"] = {}
        self._data["tasks"] = []
        self.save()   

    # ---------- persistence ----------
    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._data.update(data)
            except Exception:
                # Corrupt file? start fresh but keep the old around
                backup = self.path + ".bak"
                try:
                    os.replace(self.path, backup)
                except Exception:
                    pass
                self._data["notes"] = []
                self._data["profile"] = {}

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # ---------- operations ----------
    def add_note(self, text: str) -> None:
        if not text: 
            return
        self._data.setdefault("notes", []).append(text)
        self.save()

    def list_notes(self) -> List[str]:
        return list(self._data.get("notes") or [])

    def set_profile(self, key: str, value: Any) -> None:
        self._data.setdefault("profile", {})[key] = value
        self.save()

    def get_profile(self, key: str, default: Any = None) -> Any:
        return (self._data.get("profile") or {}).get(key, default)

    def clear(self) -> None:
        self._data["notes"] = []
        self._data["profile"] = {}
        self.save()

    # convenient properties
    @property
    def data(self) -> dict:
        return self._data

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
MEM_PATH = os.path.join(DATA_DIR, "memory.json")

def _load() -> Dict[str, Any]:
    if not os.path.exists(MEM_PATH):
        return {"ltm": [], "stm": []}
    with open(MEM_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(obj: Dict[str, Any]) -> None:
    with open(MEM_PATH, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def _cosine(a: str, b: str) -> float:
    def vec(s: str):
        d: Dict[str, int] = {}
        for t in s.lower().split():
            if not t: continue
            d[t] = d.get(t, 0) + 1
        return d
    va, vb = vec(a), vec(b)
    keys = set(va) | set(vb)
    dot = sum(va.get(k,0)*vb.get(k,0) for k in keys)
    na = math.sqrt(sum(v*v for v in va.values())) or 1.0
    nb = math.sqrt(sum(v*v for v in vb.values())) or 1.0
    return dot/(na*nb)

class Memory:
    """Short-term (session turns) + long-term memories with decay."""
    def __init__(self) -> None:
        self._cache = _load()

    # ----- STM (chat turns) -----
    def add_turn(self, role: str, text: str) -> None:
        self._cache.setdefault("stm", []).append({"role": role, "text": text, "at": time.time()})
        # keep last ~40 turns
        self._cache["stm"] = self._cache["stm"][-40:]
        _save(self._cache)

    # ----- LTM (facts) -----
    def remember(self, text: str, importance: float = 0.6, source: str = "user") -> None:
        self._cache.setdefault("ltm", []).append({
            "text": text, "importance": float(importance), "source": source, "at": time.time()
        })
        _save(self._cache)

    def search(self, query: str, k: int = 3):
        now = time.time()
        items = self._cache.get("ltm", [])
        scored = []
        for m in items:
            age_days = (now - m.get("at", now)) / 86400.0
            decay = max(0.2, 1.0 - 0.01 * age_days)    # 1% per day, floor 0.2
            sim = _cosine(query or "", m.get("text",""))
            score = (m.get("importance",0.5)) * decay * (0.5 + 0.5*sim)
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:k]]

    def clear_all(self) -> None:
        self._cache = {"ltm": [], "stm": []}
        _save(self._cache)
