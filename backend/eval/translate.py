"""Server-side mirror of react-frontend/src/utils/translator.js's Google gtx
call, so the eval harness can exercise the multilingual test cases the same
way the real frontend does: translate the user's query to English before it
ever reaches rag.py, since that's what production actually sends to the model.
"""
import requests

GTX_URL = "https://translate.googleapis.com/translate_a/single"


def translate(text: str, to: str, source: str = "auto"):
    """Returns (translated_text, detected_source_lang)."""
    params = {"client": "gtx", "sl": source, "tl": to, "dt": "t", "q": text}
    resp = requests.get(GTX_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    translated = "".join(chunk[0] for chunk in data[0] if chunk[0])
    detected_lang = data[2] if len(data) > 2 else None
    return translated, detected_lang
