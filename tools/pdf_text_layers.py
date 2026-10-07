"""Copy-paste versus OCR on born-digital Arabic PDFs: score common PDF text
extractors on the law pages of the benchmark, against the same ground truth
the OCR engines are scored on (the glyph-by-glyph rebuild of bench/pdf_gt.py).

The extractors need their own env (they are not bench dependencies):
    uv venv /tmp/pdfx --python 3.12
    uv pip install --python /tmp/pdfx/bin/python pymupdf pypdf pdfplumber pdfminer.six rapidfuzz
    PYTHONPATH=. /tmp/pdfx/bin/python tools/pdf_text_layers.py results/pdf-text-layers

Writes results.csv (one row per page and extractor) and summary.md.
pypdf and pdfminer's high-level extract_text cannot clip a page, so they are
scored on the Dubai law only (the MOHRE pages are halves of two-page spreads).
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pdfplumber  # noqa: E402
import pymupdf  # noqa: E402
import pypdf  # noqa: E402
from pdfminer.high_level import extract_text as pdfminer_text  # noqa: E402

from bench.dataset import SOURCES, page_box, parse_page  # noqa: E402
from bench.metrics import bow_recall, cer  # noqa: E402
from bench.normalize import normalize  # noqa: E402

# Signatures of ligatures that came out reversed ("اإل" for "الإ", "يف" for "في").
REVERSED = re.compile(r"(?:^|\s)(?:اإل|األ|اال|امل)|(?:^|\s)يف(?:\s|$)")


def pdftotext(pdf, page, clip, height, *flags):
    cmd = ["pdftotext", "-f", str(page), "-l", str(page), *flags]
    if clip:
        cmd += ["-x", str(int(clip[0])), "-y", "0", "-W", str(int(clip[2] - clip[0])), "-H", str(int(height))]
    return subprocess.run(cmd + [str(pdf), "-"], capture_output=True, text=True, check=True).stdout


def pymupdf_text(pdf, page, clip, height):
    return pymupdf.open(pdf)[page - 1].get_text("text", clip=pymupdf.Rect(*clip) if clip else None)


def pdfplumber_text(pdf, page, clip, height, **opts):
    with pdfplumber.open(pdf) as doc:
        p = doc.pages[page - 1]
        return (p.crop(clip) if clip else p).extract_text(**opts) or ""


def pypdf_text(pdf, page, clip, height):
    return None if clip else (pypdf.PdfReader(pdf).pages[page - 1].extract_text() or "")


def pdfminer_high_level(pdf, page, clip, height):
    return None if clip else pdfminer_text(str(pdf), page_numbers=[page - 1])


def poppler_version() -> str:
    out = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True)
    return (out.stdout + out.stderr).split("\n")[0].replace("pdftotext version ", "")


EXTRACTORS = [
    (f"pdftotext {poppler_version()}", lambda *a: pdftotext(*a)),
    (f"pdftotext {poppler_version()} -layout", lambda *a: pdftotext(*a, "-layout")),
    (f"PyMuPDF {version('pymupdf')} get_text", pymupdf_text),
    (f"pdfplumber {version('pdfplumber')} extract_text", pdfplumber_text),
    (f"pdfplumber {version('pdfplumber')} extract_text(char_dir_render='rtl')",
     lambda *a: pdfplumber_text(*a, char_dir_render="rtl")),
    (f"pypdf {version('pypdf')} extract_text", pypdf_text),
    (f"pdfminer.six {version('pdfminer.six')} extract_text", pdfminer_high_level),
]


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    sources = {s["id"]: s for s in SOURCES}
    with open(ROOT / "data" / "manifest.csv", encoding="utf-8") as f:
        pages = [r for r in csv.DictReader(f) if r["kind"] == "born-digital" and r["dpi"] == "300"]
    rows = []
    for r in pages:
        pdf = ROOT / sources[r["source_doc"]]["file"]
        page, half = parse_page(r["pdf_page"])
        w, h = page_box(pdf, page)
        clip = None if not half else ((w / 2, 0, w, h) if half == "R" else (0, 0, w / 2, h))
        gt = normalize((ROOT / r["gt"]).read_text(encoding="utf-8"))
        for name, fn in EXTRACTORS:
            text = fn(pdf, page, clip, h)
            if text is None:
                continue
            hyp = normalize(text)
            rows.append({"page_id": r["page_id"].replace("_300dpi", ""), "source_doc": r["source_doc"],
                         "extractor": name, "cer": round(cer(gt, hyp), 4),
                         "word_recall": round(bow_recall(gt, hyp), 4), "reversed_ligatures": len(REVERSED.findall(text))})
    with open(out / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    md = ["# Arabic text layers: what common PDF extractors return", "",
          "Born-digital pages of the benchmark (8 Dubai law pages, 8 MOHRE half spreads), scored like the OCR engines",
          "(standard normalization). Ground truth: the glyph-by-glyph rebuild of bench/pdf_gt.py.", "",
          "| Extractor | Document | Pages | CER | Word recall (any order) | Reversed-ligature signatures |",
          "|---|---|---|---|---|---|"]
    for name, _ in EXTRACTORS:
        for doc in ("dubai-law-7-2025", "mohre-labour-law-33-2021"):
            sel = [x for x in rows if x["extractor"] == name and x["source_doc"] == doc]
            if not sel:
                md.append(f"| {name} | {doc} | 0 | n/a | n/a | n/a |")
                continue
            md.append(f"| {name} | {doc} | {len(sel)} | {100 * sum(x['cer'] for x in sel) / len(sel):.1f}% | "
                      f"{100 * sum(x['word_recall'] for x in sel) / len(sel):.1f}% | {sum(x['reversed_ligatures'] for x in sel)} |")
    (out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results" / "pdf-text-layers")
