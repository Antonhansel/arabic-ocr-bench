"""Real scans (dataset v1): printed pages that went through a scanner or a
phone camera, transcribed by people, taken from two public datasets. They go
into data/manifest.csv as kind "real-scan".

- NOD, Yarmouk collection (Hegghammer 2021, Zenodo 10.5281/zenodo.5068735,
  CC BY 4.0): Arabic Wikipedia articles printed on paper and scanned in
  colour at 300 dpi, from the Yarmouk Arabic OCR Dataset (Abu Doush et al.
  2018), one plain-text transcription per article. NOD also ships 42 versions
  with synthetic noise; only the clean colour scans (yarmouk_01_col) are used.
  50 of the 100 articles: every second one in ID order.
- Misraj-DocOCR (Hugging Face Misraj/Misraj-DocOCR, revision 7177bf7,
  Apache-2.0): 400 pages with a human-verified Markdown transcription, "real +
  synthetic" according to its card. The pages used were classified by eye as
  scans or photos (phone or book camera) of printed pages and are listed, with their uuid, in
  data/realscans_misraj.csv, with their capture ("scanned" or "photo") and
  layout: "multi" for a photo of an open book, whose transcription reads the
  right page, then the left one. Born-digital renders, synthetic pages, and pages
  that are mostly pictures, tables of contents or indexes are left out.

Images and transcriptions are downloaded and extracted here and never
committed: the transcriptions belong to the datasets. Every download is
checked against its published checksum.
"""
from __future__ import annotations

import csv
import hashlib
import html
import io
import re
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "data" / "external"
OUT = ROOT / "data" / "realscans"

NOD_URL = "https://zenodo.org/api/records/5068735/files/{name}/content"
NOD_FILES = {  # md5 published by Zenodo
    "ground_truth.tar.lzma": "f7f37148ccd1fc07f39a7d7a88f1f2a0",
    "yarmouk_01_col.tar.lzma": "a845e80b66fea3507ad39f3c07684ff6",
}
MISRAJ_REV = "7177bf70f77ce259890d6af0bef53f18faf26ec9"
MISRAJ_URL = "https://huggingface.co/datasets/Misraj/Misraj-DocOCR/resolve/{rev}/data/{name}"
MISRAJ_FILES = {  # sha256 = Git LFS object id on Hugging Face
    "train-00000-of-00002.parquet": "8afa47430982ec5b827290aca2e78fb9c57edf080f173561c02c2b462e116ffe",
    "train-00001-of-00002.parquet": "c9fac8883b9729e4d61ca4bcff1bfd023e5065110a8a780917e14c6491f99a6c",
}
NOD_DOI = "https://doi.org/10.5281/zenodo.5068735"
MISRAJ_PAGE = "https://huggingface.co/datasets/Misraj/Misraj-DocOCR"
NOD_LICENSE = "CC BY 4.0"        # Zenodo record 5068735
MISRAJ_LICENSE = "Apache-2.0"    # dataset card at MISRAJ_REV
NOD_DIR = EXT / "nod-yarmouk"
MISRAJ_DIR = EXT / "misraj-dococr"


def fetch(url: str, path: Path, digest: str, algo: str) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".part")
        with urllib.request.urlopen(url, timeout=600) as r, open(tmp, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        tmp.rename(path)
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    if h.hexdigest() != digest:
        raise RuntimeError(f"{path.name}: {algo} {h.hexdigest()} does not match the published {digest}")
    return path


# ---------------------------------------------------------------- Misraj Markdown

TABLE_ROW = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S | re.I)
TABLE_CELL = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", re.S | re.I)


def md_to_text(md: str) -> str:
    """Misraj Markdown/HTML to the plain text printed on the page.

    Kept: every printed word, page numbers (<page_number>), numbered-list
    numbers. Tables are read row by row, cells in the order of the HTML.
    Dropped: watermarks (site names stamped on the scan), image placeholders,
    emphasis and heading markup, list bullets, horizontal rules."""
    t = re.sub(r"<watermark>.*?</watermark>", "\n", md, flags=re.S | re.I)
    t = re.sub(r"<image>.*?</image>|<img\b[^>]*>", "\n", t, flags=re.S | re.I)
    t = re.sub(r"</?page_number>", "\n", t, flags=re.I)

    def table(m: re.Match) -> str:
        rows = []
        for row in TABLE_ROW.findall(m.group(0)):
            cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip() for c in TABLE_CELL.findall(row)]
            rows.append(" ".join(c for c in cells if c))
        return "\n" + "\n".join(r for r in rows if r) + "\n"

    t = re.sub(r"<table\b.*?</table>", table, t, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)                                # <ins>, <b>, stray tags
    t = html.unescape(t)
    lines = []
    for ln in t.split("\n"):
        s = ln.strip()
        if re.fullmatch(r"(\*\s*){3,}|(-\s*){3,}|(_\s*){3,}", s):   # horizontal rule
            continue
        if re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?", s):  # Markdown table separator
            continue
        s = re.sub(r"^#{1,6}\s+", "", s)                         # heading
        s = re.sub(r"^[-*+]\s+", "", s)                          # bullet
        if s.startswith("|") and s.endswith("|"):                # Markdown table row
            s = " ".join(c.strip() for c in s.strip("|").split("|") if c.strip())
        # Escaped characters are printed text: park them in private-use code
        # points so the emphasis rules below cannot eat them.
        s = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|<>])", lambda m: chr(0xE000 + ord(m.group(1))), s)
        s = s.replace("**", "").replace("__", "")
        s = re.sub(r"(?<![\w*])\*(?=[^\s*])([^*\n]+?)(?<=[^\s*])\*(?![\w*])", r"\1", s)  # *italic*
        s = re.sub("[-]", lambda m: chr(ord(m.group(0)) - 0xE000), s)
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            lines.append(s)
    return "\n".join(lines)


# ---------------------------------------------------------------- pages

def yarmouk_pages() -> list[dict]:
    gt_tar = fetch(NOD_URL.format(name="ground_truth.tar.lzma"), NOD_DIR / "ground_truth.tar.lzma",
                   NOD_FILES["ground_truth.tar.lzma"], "md5")
    img_tar = fetch(NOD_URL.format(name="yarmouk_01_col.tar.lzma"), NOD_DIR / "yarmouk_01_col.tar.lzma",
                    NOD_FILES["yarmouk_01_col.tar.lzma"], "md5")
    from PIL import Image
    gts: dict[str, str] = {}
    with tarfile.open(gt_tar, "r:xz") as t:
        for m in t.getmembers():
            hit = re.fullmatch(r"ground_truth/yarmouk_gt/(\d+)\.txt", m.name)
            if hit:
                gts[hit.group(1)] = t.extractfile(m).read().decode("utf-8")
    ids = sorted(gts, key=int)[::2]                               # 50 of 100: every second article
    todo = {aid for aid in ids if not (OUT / f"yarmouk-{aid}.png").exists()}
    if todo:
        OUT.mkdir(parents=True, exist_ok=True)
        # Read the archive front to back: a backward seek in an LZMA stream decompresses it again.
        with tarfile.open(img_tar, "r|xz") as t:
            for m in t:
                hit = re.search(r"/(\d+)_1\.tiff$", m.name)
                if not hit or hit.group(1) not in todo:
                    continue
                im = Image.open(io.BytesIO(t.extractfile(m).read()))
                dpi = im.info.get("dpi", (300, 300))              # the TIFFs carry 300 dpi
                im.convert("RGB").save(OUT / f"yarmouk-{hit.group(1)}.png", dpi=tuple(round(d) for d in dpi))
    pages = []
    for aid in ids:
        text = "\n".join(ln.strip() for ln in gts[aid].replace("\r\n", "\n").split("\n") if ln.strip())
        pages.append({"page_id": f"yarmouk-{aid}", "image": OUT / f"yarmouk-{aid}.png", "gt": text,
                      "source_doc": "nod-yarmouk", "source_url": NOD_DOI, "ref": aid, "dpi": 300,
                      "capture": "scanned", "layout": "single", "license": NOD_LICENSE,
                      "notes": "NOD yarmouk_01_col (clean colour scan)"})
    return pages


def misraj_pages() -> list[dict]:
    import pyarrow.parquet as pq
    shards = [fetch(MISRAJ_URL.format(rev=MISRAJ_REV, name=n), MISRAJ_DIR / n, d, "sha256")
              for n, d in MISRAJ_FILES.items()]
    with open(ROOT / "data" / "realscans_misraj.csv", encoding="utf-8") as f:
        picks = {int(r["row"]): r for r in csv.DictReader(f)}
    pages, row = [], 0
    for shard in shards:
        table = pq.read_table(shard)
        for rec in table.to_pylist():
            pick = picks.get(row)
            if pick:
                if rec["uuid"] != pick["uuid"]:
                    raise RuntimeError(f"Misraj row {row}: uuid {rec['uuid']} is not {pick['uuid']}")
                out = OUT / f"misraj-{row:03d}.png"
                if not out.exists():
                    OUT.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(rec["image"]["bytes"])        # PNG as distributed, no DPI stored
                pages.append({"page_id": f"misraj-{row:03d}", "image": out, "gt": md_to_text(rec["markdown"]),
                              "source_doc": "misraj-dococr", "source_url": MISRAJ_PAGE, "ref": f"{row} ({rec['uuid']})",
                              "dpi": 0, "capture": pick["capture"], "layout": pick["layout"],
                              "license": MISRAJ_LICENSE, "notes": pick["note"]})
            row += 1
    missing = set(picks) - {int(p["page_id"].split("-")[1]) for p in pages}
    if missing:
        raise RuntimeError(f"Misraj rows not found: {sorted(missing)}")
    return pages


def interleave(a: list, b: list) -> list:
    out = []
    for i in range(max(len(a), len(b))):
        out += a[i:i + 1] + b[i:i + 1]
    return out


def all_pages(limit: int | None = None) -> list[dict]:
    pages = interleave(yarmouk_pages(), misraj_pages())
    return pages if limit is None else pages[:max(1, limit)]
