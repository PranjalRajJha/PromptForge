"""Minimal provider-agnostic LLM caller (no SDK needed).

Set one of:
  GEMINI_API_KEY  (default model: gemini-2.5-flash, override with MODEL)
  OPENAI_API_KEY  (default model: gpt-4o-mini, override with MODEL)
List the Gemini models your key can use:  python llm.py
Temperature is fixed low for reproducibility.
"""
import json
import os
import time
import urllib.error
import urllib.request

TEMPERATURE = 0.2


def _post(url, payload, headers, retries=4):
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:600]
            if e.code == 429 and ("PerDay" in body or "per day" in body):
                raise RuntimeError("DAILY QUOTA EXHAUSTED for this model. Switch MODEL (python llm.py lists models) "
                                   "or wait for the reset. Finished work is kept; rerun to resume.\n" + body[:300]) from None
            if e.code in (429, 500, 503) and attempt < retries:
                wait = 20 * (attempt + 1)
                print(f"  HTTP {e.code}, waiting {wait}s and retrying ({attempt + 1}/{retries})...")
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {e.code} from API: {body}\n"
                               "If this says the model was not found, run `python llm.py` and set MODEL to a listed name.") from None


def provider_info():
    if os.getenv("GEMINI_API_KEY"):
        return "gemini", os.getenv("MODEL", "gemini-2.5-flash")
    if os.getenv("OPENAI_API_KEY"):
        return "openai", os.getenv("MODEL", "gpt-4o-mini")
    raise RuntimeError("Set GEMINI_API_KEY or OPENAI_API_KEY")


def call_llm(prompt: str) -> str:
    provider, model = provider_info()
    if provider == "gemini":
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={os.environ['GEMINI_API_KEY']}")
        data = _post(url, {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": TEMPERATURE}}, {})
        return data["candidates"][0]["content"]["parts"][0]["text"]
    data = _post("https://api.openai.com/v1/chat/completions", {
        "model": model, "temperature": TEMPERATURE,
        "messages": [{"role": "user", "content": prompt}]},
        {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
    return data["choices"][0]["message"]["content"]


def list_gemini_models():
    url = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=100&key=" + os.environ["GEMINI_API_KEY"]
    with urllib.request.urlopen(url, timeout=60) as r:
        models = json.loads(r.read().decode("utf-8")).get("models", [])
    for m in models:
        if "generateContent" in m.get("supportedGenerationMethods", []):
            print(m["name"].replace("models/", ""))


if __name__ == "__main__":
    list_gemini_models()