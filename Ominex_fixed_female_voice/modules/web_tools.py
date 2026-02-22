# modules/web_tools.py
import os, re
import requests
import wikipedia
import trafilatura
from urllib.parse import urlparse
from duckduckgo_search import DDGS

from core.web import news_latest, format_news, search_web as ddg_basic_search

NEWS_API_KEY   = os.getenv("NEWS_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID  = os.getenv("GOOGLE_CSE_ID", "")

BLOCKLIST = ("zhihu.com", "baidu.com", "weibo.com", "bilibili.com", "portfolio.hu")

DESIGN_ALLOWLIST = (
    "behance.net","dribbble.com","awwwards.com","uxdesign.cc","siteinspire.com",
    "land-book.com","lapa.ninja","collectui.com","uigarage.net","designspiration.com",
    "onepagelove.com","pttrns.com","muz.li","pinterest.com","reddit.com"
)

def _domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""

def _looks_english(text: str) -> bool:
    if not text:
        return True
    if any('\u4e00' <= ch <= '\u9fff' for ch in text):
        return False
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    return (ascii_chars / max(1, len(text))) > 0.70

def _filter_english(results):
    out = []
    for r in results or []:
        txt = f"{r.get('title','')} {r.get('snippet','')}"
        url = r.get("url") or ""
        host = _domain(url)
        if any(host.endswith(dom) for dom in DESIGN_ALLOWLIST):
            out.append(r); continue
        if _looks_english(txt) and not any(b in host for b in BLOCKLIST):
            out.append(r)
    return out

def _format_results(results, query: str) -> str:
    lines = []
    for i, item in enumerate(results[:3], start=1):
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        snippet = (item.get("snippet") or "").strip()
        lines.append(f"{i}. {title}\n   {snippet}\n   {url}")
    return f"Top results for **{query}**:\n" + "\n\n".join(lines)

def news_text(topic: str) -> str:
    items = news_latest(topic, country="za", max_items=8)
    return format_news(items, limit=6) if items else "No recent headlines found."

def wiki_text(query: str) -> str:
    try:
        wikipedia.set_lang("en")
        page = wikipedia.page(query, auto_suggest=True, redirect=True)
        extract = wikipedia.summary(page.title, sentences=2)
        return f"{page.title}: {extract}"
    except Exception:
        return "I couldn’t find a good Wikipedia summary for that."

def ddg_search(query: str, n: int = 5):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=n, safesearch="moderate", region="us-en"):
            results.append({"title": r.get("title",""), "url": r.get("href",""), "snippet": r.get("body","")})
    return results

def search_text(query: str) -> str:
    # keep your special news intent behavior if you want:
    q = (query or "").strip()
    if re.search(r"\b(latest\s+news|headlines|^news\b)", q, flags=re.I):
        topic = re.sub(r"^(news|headlines)\s*[:\-]?\s*", "", q, flags=re.I).strip()
        return news_text(topic)

    # basic ddg search (your core.web.search_web can be used too)
    try:
        results = _filter_english(ddg_search(q, n=5))
        return _format_results(results, q) if results else "No results found."
    except Exception as e:
        return f"Search error: {e}"

def summarize_url_text(url: str, max_sentences: int = 5) -> str:
    try:
        downloaded = trafilatura.fetch_url(url, timeout=15)
        if not downloaded:
            return "I couldn’t fetch that page."
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False, favor_recall=True)
        if not text:
            return "I couldn’t extract readable text from that page."
        sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if len(s.split()) > 4]
        bullets = sentences[:max_sentences]
        host = _domain(url)
        return f"Here’s a quick summary ({host}):\n" + "\n".join([f"- {s.rstrip('.')}" for s in bullets])
    except Exception as e:
        return f"Page summary error: {e}"

def weather_text(place: str) -> str:
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": place, "count": 1, "language": "en", "format": "json"},
            timeout=10
        ).json()
        if not geo.get("results"):
            return "I couldn't find that location."
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        name = geo["results"][0]["name"]

        w = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": True},
            timeout=10
        ).json()
        cur = w.get("current_weather") or {}
        if not cur:
            return "Weather data unavailable."
        temp = cur.get("temperature")
        wind = cur.get("windspeed")
        code = cur.get("weathercode")
        desc = {0:"Clear",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",45:"Fog",48:"Rime fog",
                51:"Light drizzle",61:"Light rain",71:"Snow",80:"Rain showers"}.get(code, "Weather")
        return f"{name}: {desc}, {temp}°C, wind {wind} km/h"
    except Exception as e:
        return f"Weather error: {e}"

def crypto_text(symbol: str) -> str:
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": symbol.lower(), "vs_currencies": "usd"},
            timeout=10
        ).json()
        price = r.get(symbol.lower(), {}).get("usd")
        if price is None:
            return "Unknown coin. Try bitcoin, ethereum, dogecoin."
        return f"{symbol.title()} ~ ${price:,.2f} USD"
    except Exception as e:
        return f"Crypto error: {e}"
