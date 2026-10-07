"""Build the dataset. v0: born-digital pages from public UAE law PDFs (ground
truth = PDF text layer, extracted glyph by glyph) and synthetic pages (known
text from the same laws, rendered with three fonts, clean and with light scan
degradation). v1 adds real scans and photos of printed pages from two public datasets
(bench/realscans.py). Writes data/manifest.csv.

Usage (from the project root, see scripts/build_dataset.sh for the env vars):
    .venv/bin/python -m bench.dataset --limit 1     # one born-digital page
    .venv/bin/python -m bench.dataset --limit 10
    .venv/bin/python -m bench.dataset --real 1      # full v0 + one real scan
    .venv/bin/python -m bench.dataset               # full v0 + all real scans
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import random
import re
import subprocess
import unicodedata
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import realscans
from .pdf_gt import extract_page

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
# Neither law PDF states a license. The repository does not redistribute them:
# scripts/download_data.py fetches them from the publishers.
LAW_LICENSE = "none stated in the PDF (official UAE legislation)"

# "sha256" is the hash of the copy behind the published results. The publishers
# give no checksum, so scripts/download_data.py only warns when a PDF differs.
SOURCES = [
    {
        "id": "dubai-law-7-2025",
        "title": "Dubai Law No. (7) of 2025 regulating contracting activities (Dubai Legislation Portal, Arabic)",
        "url": "https://dlp.dubai.gov.ae/Legislation%20Ar%20Reference/2025/%D9%82%D8%A7%D9%86%D9%88%D9%86%20%D8%B1%D9%82%D9%85%20(7)%20%D9%84%D8%B3%D9%86%D8%A9%202025%20%D8%A8%D8%B4%D8%A3%D9%86%20%D8%AA%D9%86%D8%B8%D9%8A%D9%85%20%D9%85%D8%B2%D8%A7%D9%88%D9%84%D8%A9%20%D8%A3%D9%86%D8%B4%D8%B7%D8%A9%20%D8%A7%D9%84%D9%85%D9%82%D8%A7%D9%88%D9%84%D8%A7%D8%AA.pdf",
        "sha256": "63cd3da6282bc5b29ffec2cc00786b9fdbb90e797e5e0ec7da0ba3ffe0e0cc5d",
        "license": LAW_LICENSE,
        "file": "data/pdfs/dubai_law_7_2025_contracting.pdf",
        "producer": "Microsoft Word 2016, US Letter, one column",
        "fonts": "Times New Roman",
        "layout": "single",
        # 1-based PDF pages used as born-digital test pages
        "pages": ["1", "2", "4", "6", "8", "10", "12", "14"],
        # pages whose text feeds the synthetic set
        "synthetic_from": ["5", "11"],
    },
    {
        "id": "mohre-labour-law-33-2021",
        "title": "Federal Decree-Law No. (33) of 2021 on labour relations, MOHRE booklet (Arabic)",
        "url": "https://mohre.gov.ae/assets/download/43e39236/%D9%85%D8%B1%D8%B3%D9%88%D9%85%20%D8%A8%D9%82%D8%A7%D9%86%D9%88%D9%86%20%D8%A7%D8%AA%D8%AD%D8%A7%D8%AF%D9%8A%20%D8%B1%D9%82%D9%85%2033%20%D9%84%D8%B3%D9%86%D8%A9%202021%20%D8%A8%D8%B4%D8%A3%D9%86%20%D8%AA%D9%86%D8%B8%D9%8A%D9%85%20%D8%B9%D9%84%D8%A7%D9%82%D8%A7%D8%AA%20%D8%A7%D9%84%D8%B9%D9%85%D9%84%20%D9%88%D8%AA%D8%B9%D8%AF%D9%8A%D9%84%D8%A7%D8%AA%D9%87_638990570577815564.pdf.aspx",
        "sha256": "b02030b1a0cbbe9a4f36b499985008d1ee059222549ddf876d0a62341297f31b",
        "license": LAW_LICENSE,
        "file": "data/pdfs/mohre_labour_law_33_2021.pdf",
        "producer": "Adobe InDesign 20.2, A5 pages laid out as two-page spreads",
        "fonts": "Muna, TheSansArabic",
        "layout": "spread-rtl",
        # "<pdf page>R" = right half of the spread (read first), "L" = left half
        "pages": ["8R", "10L", "12R", "16L", "20R", "26L", "32R", "38L"],
        "synthetic_from": ["14R", "24L"],
    },
]

SYNTH_FONTS = [
    # (label, file, face index) ; Noto Naskh Arabic is OFL, the two others ship with macOS.
    # Geeza Pro was dropped: it has no glyph for 0-9, brackets, quotes or colon, so
    # FreeType drew empty boxes where the ground truth has digits (check_coverage).
    ("noto-naskh", str(ROOT / "fonts/NotoNaskhArabic.ttf"), 0),
    ("tahoma", "/System/Library/Fonts/Supplemental/Tahoma.ttf", 0),
    ("times-new-roman", "/System/Library/Fonts/Supplemental/Times New Roman.ttf", 0),
]
DPIS = (300, 150)
FOOTER = re.compile(r"الجريدة الرسمية|^\d+$")
# Signatures of reversed ligatures left by naive extractors ("اإلمارة",
# "األنشطة", standalone "يف" for "في"). The glyph-aware extractor must not
# produce them; a page that has several is dropped.
SUSPICIOUS = re.compile(r"(?:^|\s)(?:اإل|األ|اال|امل)|(?:^|\s)يف(?:\s|$)")


@dataclass
class Row:
    page_id: str
    image: str
    gt: str
    kind: str
    degradation: str
    dpi: int
    font: str
    source_doc: str
    source_url: str
    pdf_page: str
    small_set: int = 0
    notes: str = ""
    layout: str = ""        # real scans: "single", or "multi" for an open book (two pages)
    license: str = ""       # license of the source document or dataset


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(src: dict) -> Path:
    path = ROOT / src["file"]
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(src["url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        if not data.startswith(b"%PDF"):
            raise RuntimeError(f"{src['id']}: download is not a PDF")
        path.write_bytes(data)
    return path


def page_box(pdf: Path, page: int) -> tuple[float, float]:
    out = subprocess.run(["pdfinfo", "-f", str(page), "-l", str(page), str(pdf)],
                         capture_output=True, text=True, check=True).stdout
    m = re.search(rf"Page\s+{page} size:\s+([\d.]+) x ([\d.]+)", out)
    return float(m.group(1)), float(m.group(2))


def parse_page(spec: str) -> tuple[int, str]:
    m = re.fullmatch(r"(\d+)([RL]?)", spec)
    return int(m.group(1)), m.group(2)


def gt_for(src: dict, spec: str) -> tuple[str, list[str]]:
    pdf = ROOT / src["file"]
    page, half = parse_page(spec)
    x_range = None
    if half:
        w, _ = page_box(pdf, page)
        x_range = (w / 2, w + 1) if half == "R" else (-1, w / 2)
    return extract_page(str(pdf), page - 1, x_range)


def gt_problems(text: str, warnings: list[str], pdf_text: bool = True) -> list[str]:
    """Reasons to drop a page. The presentation-form and reversed-ligature
    checks catch broken PDF text layers; human transcriptions (real scans)
    skip them, because ﷺ, the ornate brackets around Quran verses and names
    such as املوص are printed on those pages."""
    problems = [w for w in warnings if "orphan marks" not in w]
    letters = [c for c in text if c.isalpha()]
    arabic = [c for c in letters if "ARABIC" in unicodedata.name(c, "")]
    if not letters or len(arabic) / len(letters) < 0.6:
        problems.append("less than 60% Arabic letters")
    if pdf_text and any(0xFB50 <= ord(c) <= 0xFDFF or 0xFE70 <= ord(c) <= 0xFEFF for c in text):
        problems.append("presentation-form characters in text layer")
    bad = SUSPICIOUS.findall(text) if pdf_text else []
    if len(bad) > 2:
        problems.append(f"{len(bad)} reversed-ligature signatures")
    if len(text.split()) < 40:
        problems.append("fewer than 40 words")
    return problems


def render(src: dict, spec: str, dpi: int, out: Path) -> None:
    pdf = ROOT / src["file"]
    page, half = parse_page(spec)
    cmd = ["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page), "-png", "-singlefile"]
    if half:
        w, h = page_box(pdf, page)
        half_px = round(w / 2 * dpi / 72)
        x = half_px if half == "R" else 0
        cmd += ["-x", str(x), "-y", "0", "-W", str(half_px), "-H", str(round(h * dpi / 72))]
    cmd += [str(pdf), str(out.with_suffix(""))]
    subprocess.run(cmd, check=True, capture_output=True)


# ---------------------------------------------------------------- synthetic

def synthetic_passage(text: str, max_words: int = 170) -> list[str]:
    """Clean extracted page text into paragraphs for re-rendering."""
    lines = [ln for ln in text.split("\n") if not FOOTER.search(ln.strip())]
    paras: list[str] = []
    for ln in lines:
        ln = ln.replace("ـ", "").replace("◄", "").strip()
        ln = re.sub(r"\s+", " ", ln)
        if not ln:
            continue
        starts_block = re.match(r"^(المادة|\d+\.|[أ-ي]\.)\s", ln) or ln.startswith("المادة")
        if paras and not starts_block and not paras[-1].startswith("المادة"):
            paras[-1] += " " + ln
        else:
            paras.append(ln)
    out, n = [], 0
    for p in paras:
        w = len(p.split())
        if n + w > max_words and out:
            break
        out.append(p)
        n += w
    return out


def check_coverage(text: str, font_path: str, index: int) -> None:
    """Pillow does no font fallback: a character missing from the font is drawn
    as an empty box while the ground truth still has it. Refuse to render."""
    from fontTools.ttLib import TTFont
    font = TTFont(font_path, fontNumber=index) if font_path.endswith(".ttc") else TTFont(font_path)
    cmap = font.getBestCmap()
    missing = sorted({c for c in text if not c.isspace() and ord(c) not in cmap})
    if missing:
        raise RuntimeError(f"{Path(font_path).name} has no glyph for {''.join(missing)!r}")


def render_synthetic(paras: list[str], font_path: str, index: int, out: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont, features
    check_coverage("\n".join(paras), font_path, index)
    if not features.check("raqm"):
        raise RuntimeError("Pillow has no raqm layout engine: run through scripts/build_dataset.sh "
                           "(needs `brew install fribidi` and DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib)")
    dpi, W, H = 300, 2480, 3508                      # A4 at 300 dpi
    margin, top = 236, 300                           # 2 cm side margins
    font = ImageFont.truetype(font_path, round(14 / 72 * dpi), index=index,
                              layout_engine=ImageFont.Layout.RAQM)
    line_h = round(font.size * 1.75)
    img = Image.new("L", (W, H), 255)
    draw = ImageDraw.Draw(img)
    y = top
    width = W - 2 * margin
    for p in paras:
        words, line = p.split(), ""
        lines = []
        for w in words:
            cand = (line + " " + w).strip()
            if font.getlength(cand, direction="rtl", language="ar") > width and line:
                lines.append(line)
                line = w
            else:
                line = cand
        if line:
            lines.append(line)
        for ln in lines:
            lw = font.getlength(ln, direction="rtl", language="ar")
            draw.text((W - margin - lw, y), ln, font=font, fill=0, direction="rtl", language="ar")
            y += line_h
        y += line_h // 2
    if y > H - top:
        raise RuntimeError(f"text does not fit on one page ({y}px)")
    img.save(out, dpi=(dpi, dpi))


def degrade_scan(src: Path, out: Path, seed: int) -> str:
    """Light scan look: small rotation, blur, grey paper, sensor noise, JPEG."""
    import numpy as np
    from PIL import Image, ImageFilter
    rng = random.Random(seed)
    angle = rng.choice([-1, 1]) * rng.uniform(0.5, 1.5)
    img = Image.open(src).convert("L")
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=255)
    img = img.filter(ImageFilter.GaussianBlur(0.9))
    a = np.asarray(img).astype(np.float32)
    a = 25 + a * (230 - 25) / 255                     # ink not black, paper not white
    a += np.random.default_rng(seed).normal(0, 10, a.shape)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70)
    Image.open(io.BytesIO(buf.getvalue())).save(out, dpi=(300, 300))
    return f"rotation {angle:+.2f} deg; gaussian blur 0.9 px; grey levels 25-230; noise sigma 10; JPEG q70"


# ---------------------------------------------------------------- main

def stratified(rows: list[Row]) -> list[Row]:
    """Round-robin over conditions so that --limit N gives a mixed subset."""
    buckets: dict[str, list[Row]] = {}
    for r in rows:
        key = f"{r.kind}|{r.dpi}|{r.degradation}"
        buckets.setdefault(key, []).append(r)
    order = sorted(buckets, key=lambda k: (not k.startswith("born"), -int(k.split("|")[1]), k))
    out: list[Row] = []
    while any(buckets.values()):
        for k in order:
            if buckets[k]:
                out.append(buckets[k].pop(0))
    return out


def interleave_docs(items: list[tuple[dict, str]]) -> list[tuple[dict, str]]:
    by_doc: dict[str, list] = {}
    for src, spec in items:
        by_doc.setdefault(src["id"], []).append((src, spec))
    out = []
    while any(by_doc.values()):
        for k in list(by_doc):
            if by_doc[k]:
                out.append(by_doc[k].pop(0))
    return out


def build(limit: int | None, real_limit: int | None = None) -> list[Row]:
    for d in ("gt", "pages", "synthetic"):
        (DATA / d).mkdir(parents=True, exist_ok=True)
    rows: list[Row] = []
    dropped: list[str] = []
    picks = interleave_docs([(s, p) for s in SOURCES for p in s["pages"]])
    n_pages = len(picks) if limit is None else max(1, min(len(picks), limit))
    for src, spec in picks[:n_pages]:
        download(src)
        pid = f"{src['id']}_p{spec}"
        text, warnings = gt_for(src, spec)
        problems = gt_problems(text, warnings)
        if problems:
            dropped.append(f"{pid}: {'; '.join(problems)}")
            continue
        gt_path = DATA / "gt" / f"{pid}.txt"
        gt_path.write_text(text + "\n", encoding="utf-8")
        for dpi in DPIS:
            img = DATA / "pages" / f"{pid}_{dpi}dpi.png"
            if not img.exists():
                render(src, spec, dpi, img)
            rows.append(Row(f"{pid}_{dpi}dpi", str(img.relative_to(ROOT)), str(gt_path.relative_to(ROOT)),
                            "born-digital", "none", dpi, src["fonts"],
                            src["id"], src["url"], spec, license=src["license"]))
    if limit is None:
        texts = []
        for src in SOURCES:
            download(src)
            for spec in src["synthetic_from"]:
                text, _ = gt_for(src, spec)
                texts.append((src, spec, synthetic_passage(text)))
        for ti, (src, spec, paras) in enumerate(texts):
            gt_text = "\n".join(paras)
            base_id = f"synth-t{ti + 1}"
            gt_path = DATA / "gt" / f"{base_id}.txt"
            gt_path.write_text(gt_text + "\n", encoding="utf-8")
            for fi, (flabel, fpath, findex) in enumerate(SYNTH_FONTS):
                clean = DATA / "synthetic" / f"{base_id}_{flabel}_clean.png"
                render_synthetic(paras, fpath, findex, clean)
                rows.append(Row(f"{base_id}_{flabel}_clean", str(clean.relative_to(ROOT)),
                                str(gt_path.relative_to(ROOT)), "synthetic", "none", 300, flabel,
                                src["id"], src["url"], spec, license=src["license"]))
                scan = DATA / "synthetic" / f"{base_id}_{flabel}_scan.png"
                desc = degrade_scan(clean, scan, seed=1000 * ti + fi)
                rows.append(Row(f"{base_id}_{flabel}_scan", str(scan.relative_to(ROOT)),
                                str(gt_path.relative_to(ROOT)), "synthetic", "scan", 300, flabel,
                                src["id"], src["url"], spec, notes=desc, license=src["license"]))
        # Real scans: their transcriptions belong to the datasets, so they are
        # written next to the images in data/realscans/ (not committed).
        gt_dir = realscans.OUT / "gt"
        gt_dir.mkdir(parents=True, exist_ok=True)
        for p in realscans.all_pages(real_limit):
            problems = gt_problems(p["gt"], [], pdf_text=False)
            if problems:
                dropped.append(f"{p['page_id']}: {'; '.join(problems)}")
                continue
            gt_path = gt_dir / f"{p['page_id']}.txt"
            gt_path.write_text(p["gt"] + "\n", encoding="utf-8")
            rows.append(Row(p["page_id"], str(p["image"].relative_to(ROOT)), str(gt_path.relative_to(ROOT)),
                            "real-scan", p["capture"], p["dpi"], "", p["source_doc"], p["source_url"],
                            p["ref"], notes=p["notes"], layout=p["layout"], license=p["license"]))
    rows = stratified(rows)
    mark_small_set(rows)
    with open(DATA / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(Row.__dataclass_fields__))
        w.writeheader()
        for r in rows:
            w.writerow(r.__dict__)
    (DATA / "dropped_pages.txt").write_text("\n".join(dropped) + ("\n" if dropped else ""), encoding="utf-8")
    print(f"{len(rows)} images, {len(dropped)} pages dropped -> data/manifest.csv")
    for d in dropped:
        print("  dropped:", d)
    return rows


def mark_small_set(rows: list[Row]) -> None:
    """Images for slow or paid engines. v0 (10): per document two 300 dpi pages
    and one 150 dpi page, one scan-degraded synthetic page per font, one clean
    synthetic page. Real scans (10 more): 4 Yarmouk scans, 4 Misraj scans and
    2 Misraj photos."""
    seen: dict = {}

    def take(key, n: int) -> int:
        seen[key] = seen.get(key, 0) + 1
        return int(seen[key] <= n)

    for r in rows:
        if r.kind == "born-digital":
            r.small_set = take((r.dpi, r.source_doc), 2 if r.dpi == 300 else 1)
        elif r.kind == "real-scan":
            r.small_set = take((r.source_doc, r.degradation), 2 if r.degradation == "photo" else 4)
        elif r.degradation == "none":
            r.small_set = take("clean", 1)
        else:
            r.small_set = take(("scan", r.font), 1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None,
                    help="only the first N born-digital pages, no synthetic set and no real scans")
    ap.add_argument("--real", type=int, default=None,
                    help="only the first N real-scan pages (Yarmouk and Misraj alternate)")
    args = ap.parse_args()
    build(args.limit, args.real)


if __name__ == "__main__":
    main()
