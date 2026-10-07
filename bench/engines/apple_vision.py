"""Apple Vision VNRecognizeTextRequest (accurate level, language ar-SA,
language correction on), through a small Swift tool kept alive for the
whole run (tools/vision_ocr.swift). Boxes are turned into text with
_boxes.rtl_lines."""
import json
import subprocess
from pathlib import Path

from PIL import Image

from ._boxes import rtl_lines

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "tools" / "vision_ocr.swift"
BIN = ROOT / "tools" / "bin" / "vision_ocr"
_proc = None


def load() -> dict:
    global _proc
    if not BIN.exists() or BIN.stat().st_mtime < SRC.stat().st_mtime:
        BIN.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["swiftc", "-O", str(SRC), "-o", str(BIN)], check=True, capture_output=True)
    _proc = subprocess.Popen([str(BIN)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    info = json.loads(_proc.stdout.readline())
    if "ar-SA" not in info.get("languages", []):
        raise RuntimeError(f"Vision on this macOS does not list ar-SA: {info.get('languages')}")
    return {"version": f"macOS {info['os']}, VNRecognizeTextRequest revision {info['revision']}",
            "device": "Apple Neural Engine / GPU (system managed)", "model": "accurate, ar-SA, language correction on"}


def ocr(image_path: str) -> str:
    _proc.stdin.write(image_path + "\n")
    _proc.stdin.flush()
    resp = json.loads(_proc.stdout.readline())
    if resp.get("error"):
        raise RuntimeError(resp["error"])
    w, h = Image.open(image_path).size
    boxes = []
    for o in resp["observations"]:
        # Vision boxes are normalized, origin bottom-left
        x0, x1 = o["x"] * w, (o["x"] + o["w"]) * w
        y0, y1 = (1 - o["y"] - o["h"]) * h, (1 - o["y"]) * h
        boxes.append((x0, y0, x1, y1, o["text"]))
    return rtl_lines(boxes)
