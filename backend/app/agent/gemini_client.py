import os
import requests

def gemini_generate(text: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

    if not api_key:
        return "GEMINI_API_KEY missing (check backend/.env)"

    if not model.startswith("models/"):
        model = f"models/{model}"

    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"temperature": 0.15, "maxOutputTokens": 1500},
    }

    try:
        r = requests.post(url, json=payload, timeout=60)
        if r.status_code != 200:
            return f"Gemini error {r.status_code}: {r.text}"
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Gemini exception: {type(e).__name__}: {e}"
