"""Tesseract 5 (LSTM) through its CLI, Arabic model `ara`, default page
segmentation (--psm 3, automatic layout)."""
import subprocess

LANG = "ara"
PSM = "3"


def load() -> dict:
    version = subprocess.run(["tesseract", "--version"], capture_output=True, text=True).stdout.split("\n")[0]
    langs = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stdout.split()
    if LANG not in langs:
        raise RuntimeError(f"tesseract has no '{LANG}' traineddata (brew install tesseract-lang)")
    return {"version": version, "device": "cpu", "model": f"tessdata {LANG}, psm {PSM}"}


def ocr(image_path: str) -> str:
    r = subprocess.run(["tesseract", image_path, "stdout", "-l", LANG, "--psm", PSM],
                       capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-500:])
    return r.stdout
