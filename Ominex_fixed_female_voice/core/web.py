# core/web.py — clean utilities for OMINEX
from urllib.parse import urlparse, parse_qs, unquote
import os, re, html
from typing import List, Dict, Optional, Tuple
import requests

# -------- Optional deps (safe fallbacks) --------
try:
    from duckduckgo_search import DDGS          # pip install duckduckgo-search
except Exception:
    DDGS = None

try:
    import wikipedia                            # pip install wikipedia
    wikipedia.set_lang("en")
except Exception:
    wikipedia = None

try:
    from .summarizer import summarize_url as _summarize_url
except Exception:
    _summarize_url = None

try:
    from bs4 import BeautifulSoup               # pip install beautifulsoup4 (optional)
except Exception:
    BeautifulSoup = None

# -------- Constants --------
USER_AGENT   = "OMINEX/1.0 (+learning-bot)"
TIMEOUT      = 12
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or os.getenv("NEWSAPI_KEY")
_URL         = re.compile(r"^https?://", re.I)

# -------- Small helpers --------
def _http_get(url: str, params: dict | None = None, timeout: int = TIMEOUT) -> Optional[requests.Response]:
    try:
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": USER_AGENT})
        if r.status_code == 200:
            return r
    except Exception:
        pass
    return None

def _clean(txt: str) -> str:
    txt = html.unescape(txt or "")
    txt = re.sub(r"<[^>]+>", "", txt).strip()
    return txt

# ======================= NEWS =======================
def _unwrap_gnews(url: str) -> str:
    # some Google News links contain ?url=<original>; prefer that
    try:
        qs = parse_qs(urlparse(url).query)
        if "url" in qs and qs["url"]:
            return unquote(qs["url"][0])
    except Exception:
        pass
    return url

def _dedupe_title_src(title: str, src: str) -> str:
    # remove trailing " – Source" or " — Source" if title already contains it
    t, s = (title or "").strip(), (src or "").strip()
    if not t or not s:
        return t
    for sep in (" — ", " – "):
        tail = f"{sep}{s}"
        if t.endswith(tail):
            return t[: -len(tail)].rstrip()
    return t

def news_latest(q: str = "", *, country: str = "za", max_items: int = 8) -> List[Dict[str, str]]:
    """
    No-key path first (Google News RSS) -> fallback to NewsAPI if a key is present.
    Returns: [{title, url, source, published}]
    """
    items: List[Dict[str, str]] = []

    # ---- Path A: Google News RSS (no API key)
    base = "https://news.google.com/rss"
    feed_url = f"{base}/search" if q else f"{base}/headlines/section/topic/WORLD"
    params = {"hl": "en-ZA", "gl": "ZA", "ceid": "ZA:en"}
    if q:
        params["q"] = q

    r = _http_get(feed_url, params)
    if r:
        text = r.text
        for frag in re.findall(r"<item>(.*?)</item>", text, flags=re.DOTALL):
            def grab(tag):
                m = re.search(fr"<{tag}>(.*?)</{tag}>", frag, re.DOTALL)
                return _clean(m.group(1)) if m else ""

            src_m = re.search(r"<source[^>]*>(.*?)</source>", frag, re.DOTALL)
            src   = _clean(src_m.group(1)) if src_m else "Google News"

            title = _dedupe_title_src(grab("title"), src)
            link  = _unwrap_gnews(grab("link"))
            pub   = grab("pubDate")

            if title and link:
                items.append({"title": title, "url": link, "source": src, "published": pub})
            if len(items) >= max_items:
                break

    # ---- Path B: NewsAPI (optional)
    if not items and NEWS_API_KEY:
        url = "https://newsapi.org/v2/top-headlines" if not q else "https://newsapi.org/v2/everything"
        params = {"apiKey": NEWS_API_KEY, "pageSize": max_items}
        if q:
            params.update({"q": q, "language": "en", "sortBy": "publishedAt"})
        else:
            params["country"] = (country or "za").lower()

        r = _http_get(url, params)
        if r:
            try:
                data = r.json()
                for a in data.get("articles", []):
                    items.append({
                        "title": a.get("title") or "",
                        "url": a.get("url") or "",
                        "source": (a.get("source") or {}).get("name") or "",
                        "published": a.get("publishedAt") or ""
                    })
            except Exception:
                pass

    return items

def format_news(items: List[Dict[str, str]], limit: int = 6) -> str:
    if not items:
        return "No recent headlines found."
    out = []
    for i, it in enumerate(items[:limit], 1):
        title = _clean(it.get("title", ""))
        src   = _clean(it.get("source", ""))
        when  = _clean(it.get("published", ""))
        url   = it.get("url", "")
        line = f"{i}. {title}"
        if src:  line += f" — {src}"
        if when: line += f" ({when})"
        if url:  line += f"\n   {url}"
        out.append(line)
    return "\n".join(out)

# ======================= WEB SEARCH =======================
def search_web_list(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Structured search results.
    Returns: [{"title": str, "url": str, "snippet": str}]
    """
    q = (query or "").strip()
    if not q:
        return []
    if DDGS is None:
        return [{"title": "Search unavailable", "url": "", "snippet": "duckduckgo-search not installed"}]

    try:
        rows: List[Dict[str, str]] = []
        seen = set()
        with DDGS() as ddgs:
            for hit in ddgs.text(q, max_results=max_results, region="za-en", safesearch="moderate"):
                title = (hit.get("title") or hit.get("body") or "Result").strip()
                url   = (hit.get("href")  or hit.get("url")  or "").strip()
                body  = (hit.get("body")  or "").strip()
                if not url or url in seen:
                    continue
                seen.add(url)
                rows.append({"title": title, "url": url, "snippet": body})
        return rows
    except Exception as e:
        print("DDGS ERROR:", e)
        return []


def search_web(query: str, max_results: int = 5) -> str:
    """
    Backward-compatible formatted string of results.
    """
    rows = search_web_list(query, max_results=max_results)
    if not rows:
        return f"(web search unavailable or no results) planned for: “{query}”"
    return "\n".join([f"- {r['title']} — {r['url']}" for r in rows])

# ======================= WIKIPEDIA =======================
def wikipedia_summary(q: str, sentences: int = 3) -> Optional[Dict[str, str]]:
    if wikipedia is None:
        return None
    try:
        title = wikipedia.search(q, results=1)
        if not title:
            return None
        page = wikipedia.page(title[0], auto_suggest=False, preload=False)
        summ = wikipedia.summary(page.title, sentences=sentences)
        return {"title": page.title, "summary": summ, "url": page.url}
    except Exception:
        return None

# =================== FETCH & SUMMARIZE ===================
def _basic_summarize(text: str, max_len: int = 600) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0]
    return cut + "…"

def _fetch_and_extract(url: str) -> str:
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        if not BeautifulSoup:
            # crude strip if bs4 not installed
            txt = re.sub(r"<[^>]+>", " ", r.text)
            txt = re.sub(r"\s+", " ", txt)
            return txt
        soup = BeautifulSoup(r.text, "html.parser")
        # prefer main/article/section p's, then fallback
        areas = soup.find_all(["article", "main", "section"])
        if areas:
            paras = [p.get_text(" ", strip=True) for a in areas for p in a.find_all("p")]
        else:
            paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        txt = " ".join(paras).strip()
        return txt or url
    except Exception:
        return url

def fetch_url_readable(url: str) -> Tuple[str, str, str]:
    """
    Fetch URL and return (clean_text, title, url).
    Falls back gracefully if bs4 is missing.
    """
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    r.raise_for_status()
    content = r.text

    title = ""
    text = content

    if BeautifulSoup:
        soup = BeautifulSoup(content, "html.parser")
        # remove scripts/styles/nav/aside
        for bad in soup(["script","style","noscript","header","footer","nav","aside"]):
            bad.decompose()
        title = (soup.title.string.strip() if soup.title and soup.title.string else "") or url
        text = " ".join(x.get_text(separator=" ", strip=True) for x in soup.find_all(["article","main","section","p","li"]))
        if not text:
            text = soup.get_text(separator=" ", strip=True)
    else:
        # crude fallback
        text = re.sub(r"<[^>]+>", " ", content)
        title = url

    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:200000], (title[:200] if title else url), url

def search_and_summarize(query: str, max_results: int = 5) -> str:
    q = (query or "").strip()
    if not q:
        return "No query provided."

    if _URL.match(q):
        if _summarize_url:
            try:
                summ = _summarize_url(q)
                return summ or q
            except Exception:
                pass
        text = _fetch_and_extract(q)
        return _basic_summarize(text)

    rows = search_web_list(q, max_results=max_results)
    if not rows:
        return f"(no results) planned for: “{q}”"

    listing = "\n".join([f"- {r['title']} — {r['url']}" for r in rows])
    first_url = rows[0]["url"]

    if _summarize_url:
        try:
            summ = _summarize_url(first_url)
            if summ:
                return f"{listing}\n\n**Summary of first result:**\n{summ}"
        except Exception:
            pass

    text = _fetch_and_extract(first_url)
    summ = _basic_summarize(text)
    return f"{listing}\n\n**Summary of first result:**\n{summ}"   # ✅ fixed