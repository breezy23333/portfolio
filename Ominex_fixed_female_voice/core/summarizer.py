# core/summarizer.py
import re, math, requests
from typing import List, Tuple, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

try:
    import trafilatura  # for article extraction
except Exception:
    trafilatura = None

# ---------- helpers ----------
_STOP = set("""
a an the and or but if then else when while for from into onto about above below to of in on by with without within
is are was were be been being do did done does can could should would may might must will shall
it this that these those i you he she we they them us our your his her their
""".split())

def _sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    # split on period/question/exclamation while keeping decent sentences
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if len(p.split()) >= 5]

def _freq_summarize(text: str, max_bullets: int = 6) -> List[str]:
    sents = _sentences(text)
    if not sents:
        return []
    # simple frequency scoring
    freq: Dict[str, int] = {}
    for s in sents:
        for w in re.findall(r"[A-Za-z']{2,}", s.lower()):
            if w not in _STOP:
                freq[w] = freq.get(w, 0) + 1
    scores = []
    for i, s in enumerate(sents):
        sc = sum(freq.get(w, 0) for w in re.findall(r"[A-Za-z']{2,}", s.lower()))
        # position bonus (earlier sentences matter slightly more)
        sc += max(0, len(sents) - i) * 0.05
        scores.append((sc, i, s))
    scores.sort(reverse=True)
    # keep in original order for readability
    top = sorted(scores[:max_bullets], key=lambda t: t[1])
    return [s for _, _, s in top]

def _sec_to_mmss(sec: float) -> str:
    m = int(sec // 60)
    s = int(round(sec % 60))
    return f"{m}:{s:02d}"

def _host(url: str) -> str:
    try:
        h = urlparse(url).netloc.lower()
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""

# ---------- YouTube ----------
_YT_RX = re.compile(r"(youtube\.com|youtu\.be)", re.I)

def _yt_id(url: str) -> Optional[str]:
    try:
        u = urlparse(url)
        if "youtu.be" in u.netloc:
            return u.path.lstrip("/") or None
        if "youtube.com" in u.netloc:
            qs = parse_qs(u.query)
            return (qs.get("v") or [None])[0]
    except Exception:
        pass
    return None

def _yt_transcript(video_id: str) -> Optional[List[Dict[str, Any]]]:
    # Prefer youtube-transcript-api if available
    try:
        from youtube_transcript_api import YouTubeTranscriptApi as YTA
        return YTA.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
    except Exception:
        return None

def _summarize_transcript(segments: List[Dict[str, Any]], max_bullets: int = 6) -> Tuple[str, str]:
    text = " ".join(seg.get("text", "") for seg in segments)
    bullets = _freq_summarize(text, max_bullets=max_bullets)
    # Map bullets to nearest segment start times for key moments
    moments = []
    for b in bullets:
        # find first segment that shares a non-trivial overlap with this bullet
        btoks = set(w for w in re.findall(r"[A-Za-z']{3,}", b.lower()) if w not in _STOP)
        start = None
        for seg in segments:
            stoks = set(w for w in re.findall(r"[A-Za-z']{3,}", seg.get("text","").lower()) if w not in _STOP)
            if len(btoks & stoks) >= max(2, int(0.2*len(btoks))):
                start = float(seg.get("start", 0.0))
                break
        moments.append((b, start if start is not None else 0.0))
    lines = []
    for b, ts in moments:
        lines.append(f"- [{_sec_to_mmss(ts)}] {b}")
    speak = " | ".join(bullets[:2])[:160] if bullets else "I couldn’t summarize that."
    return "\n".join(lines) if lines else "No clear moments found.", speak

def summarize_youtube(url: str) -> Tuple[str, str]:
    vid = _yt_id(url)
    if not vid:
        return ("I couldn't parse that YouTube URL.", "I couldn't parse the link.")
    segs = _yt_transcript(vid)
    if not segs:
        return ("This video has no accessible transcript (captions disabled or unsupported).", "Transcript unavailable.")
    moments_text, speak = _summarize_transcript(segs, max_bullets=6)
    reply = f"**YouTube key moments**:\n{moments_text}\n\n(Transcript-based summary.)"
    return reply, speak

# ---------- Articles / general URLs ----------
def summarize_article(url: str, max_bullets: int = 6) -> Tuple[str, str]:
    if not trafilatura:
        return ("I couldn't extract the article text (missing trafilatura).", "Extraction unavailable.")
    try:
        downloaded = trafilatura.fetch_url(url, timeout=15)
        if not downloaded:
            return ("I couldn’t fetch that page.", "Fetch failed.")
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            favor_recall=True
        )
        if not text:
            return ("I couldn’t extract readable text from that page.", "No readable text.")
        bullets = _freq_summarize(text, max_bullets=max_bullets)
        host = _host(url)
        reply = f"Here’s a quick summary ({host}):\n" + "\n".join(f"- {b}" for b in bullets) if bullets else "I couldn't build a good summary."
        speak = " | ".join(bullets[:2])[:160] if bullets else "Summary unavailable."
        return reply, speak
    except Exception as e:
        return (f"Page summary error: {e}", "Summary error.")

# ---------- Public router ----------
def summarize_url(url: str) -> Tuple[str, str]:
    if _YT_RX.search(url):
        return summarize_youtube(url)
    return summarize_article(url)