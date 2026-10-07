"""Download the benchmark inputs from their original publishers, or list them.

    .venv/bin/python scripts/download_data.py --dry-run      # list every file, download nothing
    .venv/bin/python scripts/download_data.py --only laws    # the two UAE law PDFs, 1.2 MB
    .venv/bin/python scripts/download_data.py                # everything, about 580 MB

This repository holds no page image, PDF or transcription. The benchmark reads:

- laws: the official PDFs of Dubai Law No. (7) of 2025 (Dubai Legislation
  Portal) and Federal Decree-Law No. (33) of 2021 (MOHRE booklet). Their text
  layer is the ground truth of the born-digital pages and the text of the
  synthetic pages. 1.2 MB.
- nod: NOD, Yarmouk collection (Hegghammer 2021, Zenodo), CC BY 4.0: the
  clean colour scans and their transcriptions. 42 MB.
- misraj: Misraj-DocOCR (Hugging Face, pinned revision), Apache-2.0: page
  images and Markdown transcriptions in two Parquet files. 537 MB.

A file already on disk is not downloaded again, but it is checked again. NOD
and Misraj files are checked against their published checksums: a mismatch
stops the script. The law publishers give no checksum, so a PDF that differs
from the copy behind the published results gets a warning: its ground truth
may differ too.

URLs, checksums and licenses come from bench/dataset.py (SOURCES) and
bench/realscans.py. Next step: scripts/build_dataset.sh renders the pages and
writes the ground truth.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench import realscans  # noqa: E402
from bench.dataset import SOURCES, download, sha256  # noqa: E402

GROUPS = ("laws", "nod", "misraj")


def files() -> list[dict]:
    """Every input file: group, license, URL, local path and expected checksum."""
    out = [{"group": "laws", "license": s["license"], "url": s["url"], "path": ROOT / s["file"],
            "algo": "sha256", "digest": s["sha256"], "source": s} for s in SOURCES]
    out += [{"group": "nod", "license": realscans.NOD_LICENSE, "url": realscans.NOD_URL.format(name=n),
             "path": realscans.NOD_DIR / n, "algo": "md5", "digest": d}
            for n, d in realscans.NOD_FILES.items()]
    out += [{"group": "misraj", "license": realscans.MISRAJ_LICENSE,
             "url": realscans.MISRAJ_URL.format(rev=realscans.MISRAJ_REV, name=n),
             "path": realscans.MISRAJ_DIR / n, "algo": "sha256", "digest": d}
            for n, d in realscans.MISRAJ_FILES.items()]
    return out


def get(f: dict) -> tuple[bool, str]:
    """Download one file if it is missing, then check it. Returns (ok, status)."""
    if f["group"] != "laws":
        realscans.fetch(f["url"], f["path"], f["digest"], f["algo"])  # raises on a checksum mismatch
        return True, f"{f['algo']} matches the published checksum"
    path = download(f["source"])                                     # raises if it is not a PDF
    if sha256(path) == f["digest"]:
        return True, "sha256 matches the copy behind the published results"
    return False, ("WARNING: sha256 differs from the copy behind the published results, "
                   "so the ground truth built from it may differ")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print every file to download, download nothing")
    ap.add_argument("--only", action="append", choices=GROUPS, help="only this group; repeat for several")
    args = ap.parse_args(argv)
    for f in files():
        if args.only and f["group"] not in args.only:
            continue
        state = "present" if f["path"].exists() else "missing"
        print(f"[{f['group']}] {f['path'].relative_to(ROOT)} ({state})\n"
              f"  url:     {f['url']}\n"
              f"  license: {f['license']}\n"
              f"  {f['algo'] + ':':8} {f['digest']}", flush=True)
        if args.dry_run:
            continue
        try:
            ok, status = get(f)
        except RuntimeError as e:
            sys.exit(f"error: {e}")
        print(f"  {status}", file=sys.stdout if ok else sys.stderr, flush=True)


if __name__ == "__main__":
    main()
