import os
from openai import OpenAI

def test_ominex_api():
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are OMINEX. Calm, intelligent, restrained."},
            {"role": "user", "content": "Say hello in one short sentence."}
        ],
        max_tokens=50
    )

    print("OMINEX:", response.choices[0].message.content)

if __name__ == "__main__":
    test_ominex_api()
