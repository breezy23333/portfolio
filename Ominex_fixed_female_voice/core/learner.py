# core/learner.py — OMINEX Web Learner (topics → crawl → summarize → RAG)
import os, re, json, time, sqlite3, math, hashlib          # ✅ add hashlib
from typing import List, Dict, Tuple, Optional, Any        # ✅ add Optional, Any
import numpy as np

# Optional deps guarded
try:
    import trafilatura                                     # ✅ guard this
except Exception:
    trafilatura = None

from .web import search_web_list, fetch_url_readable       # ✅ use list version
import requests
from duckduckgo_search import DDGS
from .memory import Memory

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "learn.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

ALLOW_DOMAINS = {
    "wikipedia.org","investopedia.com","reuters.com","bbc.com","apnews.com",
    "theverge.com","arstechnica.com","techcrunch.com","khanacademy.org",
    "towardsdatascience.com","medium.com","docs.python.org","numpy.org","pandas.pydata.org",
    "etfsa.co.za", "justonelap.com", "moneyweb.co.za", "businesstech.co.za",
    "sharenet.co.za", "satrix.co.za", "morningstar.com"
}
BLOCK_DOMAINS = {"baidu.com","weibo.com","bilibili.com","zhihu.com"}

def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS topics(
            id INTEGER PRIMARY KEY, topic TEXT UNIQUE, added_ts INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS sources(
            id INTEGER PRIMARY KEY, url TEXT UNIQUE, domain TEXT, title TEXT,
            topic TEXT, first_seen INTEGER, last_seen INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS chunks(
            id INTEGER PRIMARY KEY, source_id INTEGER, text TEXT, vec BLOB,
            FOREIGN KEY(source_id) REFERENCES sources(id))""")
    return True

init_db()

# ---------- tiny embedding (no big downloads) ----------
# Fast, zero-fit hashing vectorizer → cosine similarity
try:
    from sklearn.feature_extraction.text import HashingVectorizer
    _hv = HashingVectorizer(n_features=16384, alternate_sign=False, norm="l2")
    def _embed(texts: List[str]) -> np.ndarray:
        if not isinstance(texts, list): texts = [texts]
        X = _hv.transform(texts).astype(np.float32)
        return X.toarray()
except Exception:
    # Fallback: simple bag-of-words
    def _embed(texts: List[str]) -> np.ndarray:
        if not isinstance(texts, list): texts = [texts]
        arr = np.zeros((len(texts), 256), dtype=np.float32)
        for i,t in enumerate(texts):
            for w in re.findall(r"[a-z0-9]{2,}", (t or "").lower()):
                arr[i, hash(w)%256] += 1.0
            n = np.linalg.norm(arr[i]); 
            if n>0: arr[i]/=n
        return arr

def _domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""

def _looks_ok(url: str) -> bool:
    d = _domain(url)
    if not d: return False
    if any(d.endswith(b) for b in BLOCK_DOMAINS): return False
    # allow if allowlisted; otherwise be conservative (https + English-ish)
    if any(d.endswith(a) for a in ALLOW_DOMAINS): return True
    return url.startswith("https://")

def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    return text

def _split_chunks(text: str, max_chars=900) -> List[str]:
    words = text.split()
    out, cur = [], []
    n=0
    for w in words:
        n += len(w)+1
        cur.append(w)
        if n >= max_chars:
            out.append(" ".join(cur)); cur=[]; n=0
    if cur: out.append(" ".join(cur))
    return out

def add_topic(topic: str) -> dict:
    topic = (topic or "").strip()
    topic = re.sub(r'^(learn|research|study)\s*:\s*', '', topic, flags=re.I)
    if not topic: return {"ok": False, "error": "Empty topic"}
    with _conn() as c:
        c.execute("INSERT OR IGNORE INTO topics(topic,added_ts) VALUES(?,?)", (topic, int(time.time())))
    return {"ok": True, "topic": topic}

def list_topics() -> List[str]:
    with _conn() as c:
        rows = c.execute("SELECT topic FROM topics ORDER BY added_ts DESC").fetchall()
    return [r[0] for r in rows]

def _extract_readable(url: str) -> str:
    # 1) Try trafilatura (best)
    if trafilatura is not None:
        try:
            downloaded = trafilatura.fetch_url(url, timeout=15)
            if downloaded:
                text = trafilatura.extract(downloaded, include_comments=False, favor_recall=True) or ""
                text = _clean_text(text)
                if len(text) >= 200:
                    return text
        except Exception:
            pass
    # 2) Fallback: requests + BeautifulSoup (no lxml requirement)
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent":"Mozilla/5.0"})
        if r.ok and r.text:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")   # ✅ use std parser
            for tag in soup(["script","style","noscript","header","footer","nav","aside"]):
                tag.extract()
            text = " ".join((soup.get_text(" ") or "").split())
            if len(text) >= 200:
                return text
    except Exception:
        pass
    return ""

def crawl_topic_once(topic: str, max_new: int = 3) -> List[dict]:
    """search → fetch → chunk → embed → store"""
    # Prefer centralised search
    hits = search_web_list(topic, max_results=12) or []
    results = [{"title": h.get("title",""), "url": h.get("url","")} for h in hits if _looks_ok(h.get("url",""))]

    # Fallback directly to DDGS if wrapper returned nothing
    if not results:
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(topic, max_results=12, safesearch="moderate", region="za-en"):
                    url = r.get("href") or r.get("url") or ""
                    if not url or not _looks_ok(url): 
                        continue
                    results.append({"title": r.get("title",""), "url": url})
                    if len(results) >= 12: 
                        break
        except Exception:
            pass
        
    stored = []
    with _conn() as c:
        for item in results:
            if len(stored) >= max_new: break
            url = item["url"]; dom = _domain(url)
            try:
                text = _extract_readable(url)
                if not text: 
                    continue  # skip if extraction failed
                c.execute("INSERT OR IGNORE INTO sources(url,domain,title,topic,first_seen,last_seen) VALUES(?,?,?,?,?,?)",
                          (url, dom, item.get("title",""), topic, int(time.time()), int(time.time())))
                c.execute("UPDATE sources SET last_seen=? WHERE url=?", (int(time.time()), url))
                sid = c.execute("SELECT id FROM sources WHERE url=?", (url,)).fetchone()[0]

                chunks = _split_chunks(text, 900)
                vecs = _embed(chunks)
                for ch, v in zip(chunks, vecs):
                    c.execute("INSERT INTO chunks(source_id,text,vec) VALUES(?,?,?)",
                              (sid, ch, memoryview(v.tobytes())))
                stored.append({"url": url, "title": item.get("title",""), "chunks": len(chunks)})
            except Exception as e:
                print("LEARN fetch error:", url, e)
                continue
    return stored

def learn_tick(max_per_topic: int = 2) -> dict:
    """Run one learning cycle over all topics."""
    topics = list_topics()
    summary = {}
    for t in topics:
        summary[t] = crawl_topic_once(t, max_new=max_per_topic)
    return {"ok": True, "summary": summary}

def kb_stats() -> dict:
    with _conn() as c:
        n_topics = c.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
        n_sources = c.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        n_chunks = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    return {"topics": n_topics, "sources": n_sources, "chunks": n_chunks}

def kb_query(question: str, k: int = 5) -> dict:
    """Return top-k supporting snippets for a question."""
    qv = _embed([question])[0]
    with _conn() as c:
        rows = c.execute("SELECT chunks.id, chunks.text, chunks.vec, sources.url, sources.title "
                         "FROM chunks JOIN sources ON chunks.source_id=sources.id").fetchall()
    if not rows: return {"matches": []}
    texts, sims = [], []
    for _cid, text, vec_blob, url, title in rows:
        v = np.frombuffer(vec_blob, dtype=np.float32)
        sim = float(np.dot(qv, v) / (np.linalg.norm(qv)*np.linalg.norm(v) + 1e-9))
        texts.append((sim, text, url, title))
    texts.sort(key=lambda x: x[0], reverse=True)
    top = texts[:k]
    out = [{"score": round(s,3), "text": t, "url": u, "title": ti} for s,t,u,ti in top]
    # tiny synth answer (concatenate top snippets)
    answer = " ".join([t for _,t,_,_ in top])[:1200]
    return {"answer": answer, "matches": out}

# ====================== ADD BELOW (do not delete your existing code) ======================
# --- Simple summarizer (sentence scoring) ---
import re as _re
from typing import Optional as _Optional, List as _List, Dict as _Dict, Tuple as _Tuple

def _tidy_text__sum(t: str) -> str:
    t = _re.sub(r"[ \t]+\n", "\n", t)
    t = _re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def _split_sentences__sum(text: str) -> _List[str]:
    sents = _re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sents if len(s.strip()) > 40]

def summarize_text(text: str, max_sentences: int = 6) -> _Tuple[str, _List[str]]:
    sents = _split_sentences__sum(text)[:120]
    if not sents:
        return "", []
    scored = [(min(len(s), 300) / 300.0 + (1.0 / (1 + i * 0.15)), s) for i, s in enumerate(sents)]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[:max_sentences]]
    ordered = [s for s in sents if s in top][:max_sentences]
    para = " ".join(ordered)
    bullets = ordered[: min(5, len(ordered))]
    return para, bullets

# --- Web topic learning (quick summarize on top of your crawler) ---
def web_summarize(topic: str, max_sources: int = 3) -> dict:
    """Search → fetch readable text → summarize (does NOT touch your DB)."""
    from duckduckgo_search import DDGS
    hits: _List[_Dict] = []
    texts: _List[str] = []
    with DDGS() as ddgs:
        for r in ddgs.text(topic, max_results=10, safesearch="moderate", region="za-en"):
            url = r.get("href") or r.get("url") or ""
            if not url or not _looks_ok(url):
                continue
            hits.append({"title": r.get("title", "") or "Source", "url": url, "snippet": r.get("body", "")})
            try:
                txt = _extract_readable(url)
                if txt:
                    texts.append(txt)
            except Exception:
                pass
            if len(hits) >= max_sources:
                break

    corpus = ("\n\n".join(texts))[:240_000]
    if not corpus:
        return {
            "topic": topic,
            "summary": "No readable content found.",
            "bullets": [],
            "sources": hits,
            "kind": "web",
        }
    summary, bullets = summarize_text(corpus, max_sentences=6)
    return {
        "topic": topic,
        "summary": summary,
        "bullets": bullets,
        "sources": hits,
        "kind": "web",
    }

# --- YouTube video learning (captions) ---
# pip install youtube-transcript-api
try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
except Exception:
    YouTubeTranscriptApi = None
    TranscriptsDisabled = Exception
    NoTranscriptFound = Exception

_YT_PAT = _re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([A-Za-z0-9_-]{6,})"
)

def _extract_yt_id(s: str) -> _Optional[str]:
    m = _YT_PAT.search(s)
    return m.group(1) if m else None

def _yt_oembed_title(url: str) -> _Optional[str]:
    import requests as _req
    try:
        o = _req.get("https://www.youtube.com/oembed", params={"url": url, "format": "json"}, timeout=12)
        if o.status_code == 200:
            return o.json().get("title")
    except Exception:
        pass
    return None

def _fetch_yt_transcript(video_id: str, langs: _Optional[_List[str]] = None) -> _Optional[str]:
    if YouTubeTranscriptApi is None:
        return None
    if not langs:
        langs = ["en", "en-US", "en-GB", "af", "xh", "zu"]
    try:
        for lang in langs:
            try:
                segs = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                return _tidy_text__sum(" ".join(s["text"] for s in segs))
            except (NoTranscriptFound, TranscriptsDisabled):
                continue
        segs = YouTubeTranscriptApi.get_transcript(video_id)
        return _tidy_text__sum(" ".join(s["text"] for s in segs))
    except Exception:
        return None

def learn_from_video(url_or_text: str) -> dict:
    vid = _extract_yt_id(url_or_text)
    if not vid:
        return {"topic": "Video", "summary": "No YouTube URL detected.", "bullets": [], "sources": [], "kind": "video"}

    full_url = f"https://www.youtube.com/watch?v={vid}"
    title = _yt_oembed_title(full_url) or "YouTube Video"
    transcript = _fetch_yt_transcript(vid)

    if not transcript:
        # weak fallback: meta description
        try:
            import requests as _req
            from bs4 import BeautifulSoup as _BS
            html = _req.get(full_url, timeout=12).text
            soup = _BS(html, "html.parser")
            meta = soup.find("meta", {"name": "description"})
            text = meta.get("content", "").strip() if meta else ""
        except Exception:
            text = ""
    else:
        text = transcript

    if not text:
        return {
            "topic": title,
            "summary": "Could not access captions or meaningful text for this video.",
            "bullets": [],
            "sources": [{"title": title, "url": full_url, "snippet": "YouTube video"}],
            "kind": "video",
        }

    summary, bullets = summarize_text(text, max_sentences=6)
    return {
        "topic": title,
        "summary": summary,
        "bullets": bullets,
        "sources": [{"title": title, "url": full_url, "snippet": "YouTube video (captions)"}],
        "kind": "video",
    }

# --- Auto-router (topic vs video) ---
def learn_autoroute(query_or_url: str, max_sources: int = 3) -> dict:
    """If input contains a YouTube link, learn from video; otherwise summarize web topic."""
    if _extract_yt_id(query_or_url):
        return learn_from_video(query_or_url)
    return web_summarize(query_or_url, max_sources=max_sources)

SAFE_MAX_PAGES = 6
MIN_SOURCE_AGREEMENT = 2

def _hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def _clean(txt: str) -> str:
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

# ...
def learn_auto(topic: str, mem: Memory, tags: List[str] | None = None) -> Dict[str, Any]:
    """
    Learn about a *topic* safely, verify across multiple sources,
    and persist high-confidence facts into Memory as knowledge objects.
    Returns a brief report for UI.
    """
    tags = tags or ["auto-learn"]
    results = search_web_list(topic, max_results=SAFE_MAX_PAGES)   # ✅ list of dicts

    pages = []
    for r in results:
        url = r.get("url")
        if not url:
            continue
        try:
            html_text, title, final_url = fetch_url_readable(url)
            pages.append({"title": title or final_url, "url": final_url, "text": html_text})
        except Exception:
            continue

def _extract_facts(text: str) -> List[str]:
    """
    Extract bullet-like factual statements (simple heuristic).
    Keep them short so they store well.
    """
    lines = re.split(r"[.;]\s+", text)
    facts = []
    for ln in lines:
        ln = _clean(ln)
        if 40 <= len(ln) <= 240 and "http" not in ln:
            facts.append(ln)
    return facts[:10]

def _merge_and_score(fact_sources: Dict[str, List[Dict[str,str]]]) -> List[Tuple[str, float, List[Dict[str,str]]]]:
    """
    Confidence = base (0.35) + 0.25 * log(#sources+1) + 0.15 * avg title similarity (heuristic)
    """
    out = []
    for fact, sources in fact_sources.items():
        n = len(sources)
        if n < MIN_SOURCE_AGREEMENT:
            continue
        base = 0.35 + 0.25 * min(1.5, (n ** 0.5))  # diminishing returns
        conf = min(0.95, base)
        out.append((fact, conf, sources))
    return sorted(out, key=lambda x: x[1], reverse=True)

def learn_auto(topic: str, mem: Memory, tags: List[str] | None = None) -> Dict[str, Any]:
    """
    Learn about a *topic* safely, verify across multiple sources,
    and persist high-confidence facts into Memory as knowledge objects.
    Returns a brief report for UI.
    """
    tags = tags or ["auto-learn"]
    results = search_web(topic, limit=SAFE_MAX_PAGES)  # your existing search wrapper

    pages = []
    for r in results:
        try:
            html_text, title, url = fetch_url_readable(r["url"])
            pages.append({"title": title or url, "url": url, "text": html_text})
        except Exception:
            continue

    # extract facts per page
    fact_sources: Dict[str, List[Dict[str,str]]] = {}
    for pg in pages:
        facts = _extract_facts(pg["text"])
        for f in facts:
            fact_sources.setdefault(f, []).append({"url": pg["url"], "title": pg["title"]})

    merged = _merge_and_score(fact_sources)

    stored = []
    for fact, conf, sources in merged:
        item = {
            "id": _hash(f"{topic}|{fact}"),
            "topic": topic,
            "content": fact,
            "sources": sources[:4],          # keep it light
            "confidence": conf,
            "created_at": time.time(),
            "updated_at": time.time(),
            "tags": tags,
            # time-sensitive topics can expire; set TTL if needed e.g., 90 days:
            # "ttl": 90*86400
        }
        mem.upsert_knowledge(item)
        stored.append(item)

    return {
        "topic": topic,
        "considered_pages": len(pages),
        "facts_stored": len(stored),
        "low_confidence_dropped": max(0, len(fact_sources) - len(merged)),
        "sample": stored[:3]
    }

# ====================== END PATCH ======================