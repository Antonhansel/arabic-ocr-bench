"""Apple Live Text: VisionKit's ImageAnalyzer (text only, locale ar-SA),
through a small Swift tool kept alive for the whole run
(tools/livetext_ocr.swift). Unlike the Vision adapter (apple_vision.py), the
text and its reading order come from Apple's analyzer as is: no box sorting
on my side."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "tools" / "livetext_ocr.swift"
BIN = ROOT / "tools" / "bin" / "livetext_ocr"
_proc = None


def load() -> dict:
    global _proc
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        BIN.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["swiftc", "-parse-as-library", "-O", str(SRC), "-o", str(BIN)],
                       check=True, capture_output=True)
    _proc = subprocess.Popen([str(BIN)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    info = json.loads(_proc.stdout.readline())
    if "ar-SA" not in info.get("languages", []):
        raise RuntimeError(f"Live Text on this macOS does not list ar-SA: {info.get('languages')}")
    return {"version": f"macOS {info['os']}, VisionKit ImageAnalyzer",
            "device": "Apple Neural Engine / GPU (system managed)", "model": "text, locale ar-SA, Apple's reading order"}


def ocr(image_path: str) -> str:
    _proc.stdin.write(image_path + "\n")
    _proc.stdin.flush()
    resp = json.loads(_proc.stdout.readline())
    if resp.get("error"):
        raise RuntimeError(resp["error"])
    return resp["text"]
