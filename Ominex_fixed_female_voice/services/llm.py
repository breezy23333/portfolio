# services/llm.py
import os
from openai import OpenAI

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = (
    "You are OMINEX. "
    "Calm, intelligent, emotionally restrained. "
    "Short, precise responses. "
    "No emojis. No filler. No hype."
)


def ask_ominex(user_text: str, max_tokens: int = 120) -> str:
    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()
