"""Vision models through OpenRouter's chat API, with the same transcription
prompt as gemini.py. The API key is read from the OPENROUTER_API_KEY
environment variable and sent in a header, never logged. Small set only, one
call at a time. MODEL is set by the thin per-model modules (or_*.py).

Settings: default temperature, reasoning effort "low" where the model has it
(as Gemini's thinking level low), output capped at 16384 tokens so reasoning
cannot eat the page. A code fence wrapped around the whole answer, which some
models add despite the prompt, is removed. Cost and token counts go to the
engine log as one USAGE line per page."""
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

from .gemini import PROMPT

URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = ""
_key = None


def load() -> dict:
    global _key
    if not MODEL:
        raise RuntimeError("no MODEL set: use one of the or_*.py modules")
    _key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not _key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return {"version": MODEL, "device": "OpenRouter API",
            "model": f"{MODEL}, default temperature, reasoning low, max 16384 output tokens"}


def payload(image_path: str, b64: str) -> dict:
    mime = mimetypes.guess_type(image_path)[0] or "image/png"
    return {
        "model": MODEL,
        "max_tokens": 16384,
        "reasoning": {"effort": "low"},
        "usage": {"include": True},
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            {"type": "text", "text": PROMPT},
        ]}],
    }


def strip_fence(s: str) -> str:
    t = s.strip()
    if t.startswith("```") and t.endswith("```") and len(t) > 6:
        t = t[3:-3]
        t = t.split("\n", 1)[1] if "\n" in t else ""   # drop the language tag line
    return t.strip("\n")


def text_of(out: dict) -> str:
    choices = out.get("choices") or []
    if not choices:
        raise RuntimeError(f"no choice: {json.dumps(out)[:300]}")
    content = (choices[0].get("message") or {}).get("content") or ""
    if isinstance(content, list):
        content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
    return strip_fence(content)


def ocr(image_path: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    data = json.dumps(payload(image_path, b64)).encode()
    for attempt in range(4):
        req = urllib.request.Request(URL, data=data, method="POST", headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {_key}",
            "HTTP-Referer": "https://github.com/Antonhansel/arabic-ocr-bench", "X-Title": "arabic-ocr-bench"})
        try:
            with urllib.request.urlopen(req, timeout=280) as resp:
                out = json.loads(resp.read())
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}") from None
    if out.get("error"):
        raise RuntimeError(f"API error: {json.dumps(out['error'])[:300]}")
    finish = (out.get("choices") or [{}])[0].get("finish_reason")
    if finish not in ("stop", None):
        print(f"{image_path}: finish_reason={finish}", file=sys.stderr)
    print("USAGE " + json.dumps({"image": image_path, "model": out.get("model"),
                                 "provider": out.get("provider"), "usage": out.get("usage", {})}), file=sys.stderr)
    text = text_of(out)
    # A model that spends its whole budget without writing (seen with Mistral Large 4) failed;
    # recording it as an empty page would score it like PaddleOCR's silent blanks.
    if not text.strip() and finish in ("error", "length"):
        raise RuntimeError(f"no text, finish_reason={finish}")
    return text
