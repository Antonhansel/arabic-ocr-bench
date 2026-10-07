"""Gemini API baseline (gemini-3.5-flash), plain REST call. The API key is
read from the GEMINI_API_KEY environment variable and sent in a header,
never logged. Runs on the small set only, one page at a time.

Settings: default temperature (Google recommends keeping 1.0 for Gemini 3
models; a first try at temperature 0 ran past 240 s on one page and timed
out), thinking level "low", output capped at 8192 tokens (a page is about
1000). A capped (MAX_TOKENS) answer is still scored as returned."""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

MODEL = "gemini-3.5-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
PROMPT = ("Transcribe all the text in this document image exactly as written, in natural reading "
          "order (Arabic is read right to left). Output plain text only: no markdown, no translation, "
          "no commentary, no corrections. Keep one output line per printed line.")
_key = None


def load() -> dict:
    global _key
    _key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not _key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return {"version": MODEL, "device": "Google API",
            "model": f"{MODEL}, default temperature, thinking low, max 8192 output tokens"}


def ocr(image_path: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = {
        "contents": [{"parts": [{"inline_data": {"mime_type": "image/png", "data": b64}},
                                {"text": PROMPT}]}],
        "generationConfig": {"maxOutputTokens": 8192, "thinkingConfig": {"thinkingLevel": "low"}},
    }
    data = json.dumps(body).encode()
    for attempt in range(4):
        req = urllib.request.Request(URL, data=data, method="POST", headers={
            "Content-Type": "application/json", "x-goog-api-key": _key})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                out = json.loads(resp.read())
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}") from None
    cands = out.get("candidates") or []
    if not cands:
        raise RuntimeError(f"no candidate: {json.dumps(out)[:300]}")
    if cands[0].get("finishReason") != "STOP":
        print(f"{image_path}: finishReason={cands[0].get('finishReason')}", file=sys.stderr)
    # Token counts go to the engine log (stderr), one line per page, to price a page afterwards.
    print("USAGE " + json.dumps({"image": image_path, "usage": out.get("usageMetadata", {})}), file=sys.stderr)
    parts = cands[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))
