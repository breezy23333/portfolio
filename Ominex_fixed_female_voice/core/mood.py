
import re

def detect_mood(text: str) -> str:
    s = (text or "").lower()

    pos = ["great", "thanks", "love", "nice", "cool", "win", "awesome", "good", "happy", "excited", "fun"]
    neg = ["angry", "annoyed", "sad", "bad", "hate", "problem", "stuck", "fail", "tired", "worried", "depressed"]

    score = sum(w in s for w in pos) - sum(w in s for w in neg)

    if score > 0:
        return "Positive"
    elif score < 0:
        return "Concerned"
    else:
        return "Neutral"

def detect_mood(text: str) -> str:
    t = (text or "").lower()
    if re.search(r"\b(happy|excited|great|awesome)\b", t): return "Happy"
    if re.search(r"\b(sad|down|depressed|tired)\b", t):    return "Sad"
    if re.search(r"\b(focus|serious|task|goal)\b", t):     return "Focus"
    if re.search(r"\b(calm|ok|fine|neutral)\b", t):        return "Calm"
    return "Neutral"