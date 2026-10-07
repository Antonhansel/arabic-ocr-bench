"""Score a results folder and write results.csv + summary.md.

    .venv/bin/python -m bench.score results/2026-10-06 [--norm standard|raw|aggressive] [--common]

Scoring only reads saved OCR outputs, so it can be re-run with another
normalization without running any engine again. --common keeps only the pages
that every engine finished (API engines limited to the small set aside), so a
stopped or partial run still compares the engines on the same pages.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import platform
import statistics as st
import subprocess
from pathlib import Path

from rapidfuzz.distance import Levenshtein

from .engines import ENGINES
from .metrics import bow_recall, cer, number_recall, rev_cer, wer
from .normalize import Norm, normalize, words

ROOT = Path(__file__).resolve().parent.parent
# Kinds in report order, with the label used in column names and where their ground truth comes from.
KINDS = {
    "born-digital": ("born-digital", "PDF text layer (born-digital)"),
    "synthetic": ("synthetic", "the rendered text (synthetic)"),
    "real-scan": ("real scans", "the dataset's human transcription (real scans)"),
}
FIELDS =["page_id", "engine", "kind", "source_doc", "dpi", "font", "degradation", "small_set",
          "cer", "wer", "bow_recall", "number_recall", "rev_cer", "cer_raw", "wer_raw", "cer_aggressive",
          "seconds", "error"]


def load_records(out: Path) -> dict[tuple[str, str], dict]:
    latest: dict[tuple[str, str], dict] = {}
    for line in (out / "raw.jsonl").read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        latest[(rec["engine"], rec["page_id"])] = rec
    return latest


def score_rows(out: Path, norm_name: str) -> list[dict]:
    with open(ROOT / "data" / "manifest.csv", encoding="utf-8") as f:
        manifest = {r["page_id"]: r for r in csv.DictReader(f)}
    norm = Norm.preset(norm_name)
    rows = []
    for (engine, page_id), rec in sorted(load_records(out).items()):
        m = manifest.get(page_id)
        if m is None:
            continue
        gt = (ROOT / m["gt"]).read_text(encoding="utf-8")
        hyp = None
        if rec["error"] is None:
            p = out / "outputs" / engine / f"{page_id}.txt"
            hyp = p.read_text(encoding="utf-8") if p.exists() else ""
        ref_n, hyp_n = normalize(gt, norm), normalize(hyp or "", norm)
        ref_raw, hyp_raw = normalize(gt, "raw"), normalize(hyp or "", "raw")
        ref_ag, hyp_ag = normalize(gt, "aggressive"), normalize(hyp or "", "aggressive")
        rows.append({
            "page_id": page_id, "engine": engine, "kind": m["kind"], "source_doc": m["source_doc"],
            "dpi": m["dpi"], "font": m["font"], "degradation": m["degradation"], "small_set": m["small_set"],
            "layout": m.get("layout", ""),
            "cer": cer(ref_n, hyp_n), "wer": wer(ref_n, hyp_n), "bow_recall": bow_recall(ref_n, hyp_n),
            "number_recall": number_recall(ref_n, hyp_n),
            "rev_cer": rev_cer(ref_n, hyp, norm) if hyp else None,
            "cer_raw": cer(ref_raw, hyp_raw), "wer_raw": wer(ref_raw, hyp_raw),
            "cer_aggressive": cer(ref_ag, hyp_ag),
            "seconds": rec["seconds"], "error": rec["error"],
            "empty": rec["error"] is None and not (hyp or "").strip(),
        })
    return rows


def common_pages(rows: list[dict]) -> set[str]:
    """Pages that every full-set engine scored. Small-set-only engines (Gemini) do not shrink the set."""
    full = {r["engine"] for r in rows if not (r["engine"] in ENGINES and ENGINES[r["engine"]].small_set_only)}
    sets = [{r["page_id"] for r in rows if r["engine"] == e} for e in full]
    return set.intersection(*sets) if sets else set()


# ---------------------------------------------------------------- report helpers

def mean(xs) -> float | None:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def pct(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def secs(x) -> str:
    return "n/a" if x is None else f"{x:.1f}"


def table(header: list[str], body: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in body]
    return "\n".join(lines)


def machine() -> str:
    try:
        chip = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
        mem = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout) // 2**30
        return f"{chip}, {mem} GB RAM, macOS {platform.mac_ver()[0]}"
    except Exception:
        return platform.platform()


def by(rows, **conds):
    return [r for r in rows if all(str(r[k]) == str(v) for k, v in conds.items())]


def map_index(ops, p: int) -> int:
    """Map a reference character offset to the aligned output offset."""
    for tag, i1, i2, j1, j2 in ops:
        if i1 <= p < i2 or (p == i2 and tag != "equal" and i1 == i2):
            if tag in ("equal", "replace"):
                return min(j1 + (p - i1), j2)
            return j1
    return ops[-1][4] if ops else 0


def example(row: dict, out: Path, norm: Norm) -> dict | None:
    m_gt = (ROOT / manifest_gt(row["page_id"])).read_text(encoding="utf-8")
    hyp = (out / "outputs" / row["engine"] / f"{row['page_id']}.txt").read_text(encoding="utf-8")
    lines = [normalize(ln, norm) for ln in m_gt.split("\n")]
    lines = [ln for ln in lines if ln]
    ref = " ".join(lines)
    hyp_n = normalize(hyp, norm)
    ops = Levenshtein.opcodes(ref, hyp_n)
    best, pos = None, 0
    for ln in lines:
        a, b = pos, pos + len(ln)
        pos = b + 1
        if len(ln.split()) < 6:
            continue
        ja, jb = map_index(ops, a), map_index(ops, b)
        span = hyp_n[ja:jb].strip()
        err = Levenshtein.distance(ln, span) / len(ln)
        if err == 0:
            continue
        score = abs(err - row["cer"])
        if best is None or score < best[0]:
            best = (score, ln, span, err)
    if best is None:
        return None
    _, ln, span, err = best
    diffs = []
    rw, hw = words(ln), words(span)
    blocks: list[list[int]] = []          # merge adjacent non-equal edits
    for tag, i1, i2, j1, j2 in Levenshtein.opcodes(rw, hw):
        if tag == "equal":
            continue
        if blocks and blocks[-1][1] == i1 and blocks[-1][3] == j1:
            blocks[-1][1], blocks[-1][3] = i2, j2
        else:
            blocks.append([i1, i2, j1, j2])
    for i1, i2, j1, j2 in blocks:
        a = " ".join(rw[i1:i2]) or "(nothing)"
        b = " ".join(hw[j1:j2]) or "(missing)"
        diffs.append(f"«{a}» → «{b}»")
    return {"gt": ln, "ocr": span, "line_cer": err, "diffs": diffs[:8]}


_GT_PATHS: dict[str, str] = {}


def manifest_gt(page_id: str) -> str:
    if not _GT_PATHS:
        with open(ROOT / "data" / "manifest.csv", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                _GT_PATHS[r["page_id"]] = r["gt"]
    return _GT_PATHS[page_id]


def pick_examples(rows: list[dict], ranked: list[str]) -> list[tuple[str, dict]]:
    """Three typical (not extreme) errors from three different engines."""
    ok = [r for r in rows if r["error"] is None]
    picks: list[tuple[str, dict]] = []
    used: set[str] = set()

    def closest(cands, target_key="cer"):
        if not cands:
            return None
        med = st.median(r[target_key] for r in cands)
        return min(cands, key=lambda r: abs(r[target_key] - med))

    first = "born-digital" if any(x["kind"] == "born-digital" for x in ok) else "real-scan"
    if ranked:
        e = ranked[0]
        r = closest([x for x in ok if x["engine"] == e and x["kind"] == first and x["cer"] > 0])
        if r:
            picks.append((f"Best-ranked engine, typical {first} page", r))
            used.add(e)
    hard = ("scan", "scan-degraded synthetic page") if any(x["degradation"] == "scan" for x in ok) \
        else ("photo", "photo of a printed page")
    mids = [e for e in ranked[1:-1] if e not in used] or [e for e in ranked if e not in used]
    if mids:
        e = mids[len(mids) // 2]
        r = closest([x for x in ok if x["engine"] == e and x["degradation"] == hard[0] and x["cer"] > 0])
        if r:
            picks.append((f"Mid-ranked engine, typical {hard[1]}", r))
            used.add(e)
    gaps = []
    for e in ranked:
        if e in used:
            continue
        er = [x for x in ok if x["engine"] == e]
        if er:
            gaps.append((mean(x["wer"] - (1 - x["bow_recall"]) for x in er), e))
    if gaps and max(gaps)[0] > 0.15:
        gap, e = max(gaps)
        r = max([x for x in ok if x["engine"] == e], key=lambda x: x["wer"] - (1 - x["bow_recall"]))
        picks.append((f"Largest reading-order gap (mean WER minus order-free word miss rate: {pct(gap)})", r))
    else:
        rest = [e for e in ranked if e not in used]
        r = closest([x for x in ok if x["engine"] == rest[-1] and x["cer"] > 0]) if rest else None
        if r:
            picks.append(("Lowest-ranked engine, typical page", r))
    return picks


def write_summary(out: Path, rows: list[dict], norm_name: str, common: bool = False) -> None:
    norm = Norm.preset(norm_name)
    info = json.loads((out / "engines.json").read_text()) if (out / "engines.json").exists() else {}
    engines = sorted({r["engine"] for r in rows})
    small_only = {e for e in engines if e in ENGINES and ENGINES[e].small_set_only}
    full = [e for e in engines if e not in small_only]
    ranked = sorted(full, key=lambda e: mean(r["cer"] for r in by(rows, engine=e)))
    n_images = len({r["page_id"] for r in rows})
    kinds = [k for k in KINDS if any(r["kind"] == k for r in rows)]

    def stats(e, subset):
        rs = [r for r in subset if r["engine"] == e]
        return rs, [r for r in rs if r["error"] is None]

    md = [f"# Arabic OCR benchmark, run {out.name}", ""]
    md += [f"- Generated {dt.datetime.now().isoformat(timespec='minutes')} on {machine()}.",
           f"- {n_images} page images scored. Ground truth: {' or '.join(KINDS[k][1] for k in kinds)}.",
           f"- Normalization preset `{norm_name}`: {norm.describe()}.",
           "- CER and WER are means over pages; a failed page counts as empty output (CER = WER = 100%).",
           "- Word recall (any order) = share of ground-truth words found in the output, ignoring order.",
           "- s/page = median wall time per page once the model is loaded (load time listed separately)."]
    if common:
        md += ["- Scored with `--common`: only the pages that every engine finished, so all engines are compared on the same pages."]
    md += [""]

    md += ["## Engines", ""]
    body = []
    for e in engines:
        i = info.get(e, {})
        body.append([e, i.get("version", "n/a"), i.get("device", "n/a"), i.get("model", ""), secs(i.get("load_seconds"))])
    md += [table(["Engine", "Version", "Device", "Settings", "Load s"], body), ""]

    md += ["## Main table (full set)", ""]
    body = []
    for e in ranked:
        rs, okr = stats(e, rows)
        per_kind = []
        for k in kinds:
            kr = [r for r in rs if r["kind"] == k]
            per_kind += [pct(mean(r["cer"] for r in kr)), pct(mean(r["wer"] for r in kr))]
        body.append([e, len(rs), len(rs) - len(okr)] + per_kind +
                    [pct(mean(r["cer"] for r in rs)),
                     pct(mean(r["bow_recall"] for r in rs)),
                     secs(st.median([r["seconds"] for r in okr]) if okr else None)])
    kind_cols = [c for k in kinds for c in (f"CER {KINDS[k][0]}", f"WER {KINDS[k][0]}")]
    md += [table(["Engine", "Pages", "Failures"] + kind_cols +
                 ["CER all", "Word recall (any order)", "s/page"], body), ""]

    small = [r for r in rows if r["small_set"] == "1"]
    if small_only or small:
        md += ["## Small set (same pages for every engine, includes API engines)", ""]
        body = []
        small_ids = {r["page_id"] for r in small}
        for e in sorted(engines, key=lambda e: mean(r["cer"] for r in small if r["engine"] == e) or 9):
            rs, okr = stats(e, small)
            if len({r["page_id"] for r in rs}) < len(small_ids):
                continue
            body.append([e, len(rs), len(rs) - len(okr), pct(mean(r["cer"] for r in rs)),
                         pct(mean(r["wer"] for r in rs)), pct(mean(r["bow_recall"] for r in rs)),
                         secs(st.median([r["seconds"] for r in okr]) if okr else None)])
        md += [table(["Engine", "Pages", "Failures", "CER", "WER", "Word recall (any order)", "s/page"], body), ""]

    md += ["## CER by condition", ""]
    conds = [("Born-digital 300 dpi", dict(kind="born-digital", dpi=300)),
             ("Born-digital 150 dpi", dict(kind="born-digital", dpi=150)),
             ("Synthetic clean", dict(kind="synthetic", degradation="none")),
             ("Synthetic scan", dict(kind="synthetic", degradation="scan")),
             ("Dubai law (Word)", dict(source_doc="dubai-law-7-2025", kind="born-digital")),
             ("MOHRE booklet (InDesign)", dict(source_doc="mohre-labour-law-33-2021", kind="born-digital")),
             ("Yarmouk scans (printed Wikipedia, 300 dpi)", dict(source_doc="nod-yarmouk")),
             ("Misraj scans", dict(source_doc="misraj-dococr", degradation="scanned")),
             ("Misraj photos, one page", dict(source_doc="misraj-dococr", degradation="photo", layout="single")),
             ("Misraj photos, open book (two pages)",
              dict(source_doc="misraj-dococr", degradation="photo", layout="multi"))]
    conds = [(n, c) for n, c in conds if by(rows, **c)]
    body =[[e] + [pct(mean(r["cer"] for r in by(rows, engine=e, **c))) for _, c in conds] for e in ranked]
    md += [table(["Engine"] + [n for n, _ in conds], body), ""]

    fonts = sorted({r["font"] for r in rows if r["kind"] == "synthetic"})
    if fonts:
        md += ["## CER by font (synthetic pages, clean and scan)", ""]
        body = [[e] + [pct(mean(r["cer"] for r in by(rows, engine=e, kind="synthetic", font=f))) for f in fonts]
                for e in ranked]
        md += [table(["Engine"] + fonts, body), ""]

    md += ["## Effect of normalization (mean CER, all pages)", "",
           "raw = invisible characters and whitespace only; standard = default; aggressive = standard + ta marbuta to ha + punctuation removed.", ""]
    body = [[e, pct(mean(r["cer_raw"] for r in by(rows, engine=e))), pct(mean(r["cer"] for r in by(rows, engine=e))),
             pct(mean(r["cer_aggressive"] for r in by(rows, engine=e)))] for e in ranked + sorted(small_only)]
    md += [table(["Engine", "CER raw", f"CER {norm_name}", "CER aggressive"], body), ""]

    # The column only appears when some engine returned an empty page, so older reports stay as they were.
    show_empty = any(r["empty"] for r in rows)
    md += ["## Diagnostics", "",
           "- Reading-order suspects: pages with word recall (any order) of 85% or more but WER of 30% or more.",
           "- Visual-order suspects: pages where reversing each output line halves the CER (engine returned left-to-right order).",
           "- Number recall: share of the ground-truth numbers (article numbers, years, amounts) found in the output, any order."]
    if show_empty:
        md += ["- Empty outputs: pages where the engine returned no text and no error; they score CER = WER = 100%."]
    md += [""]
    body = []
    for e in ranked + sorted(small_only):
        okr = [r for r in rows if r["engine"] == e and r["error"] is None]
        order = sum(1 for r in okr if r["bow_recall"] >= 0.85 and r["wer"] >= 0.30)
        visual = sum(1 for r in okr if r["rev_cer"] is not None and r["cer"] > 0.3 and r["rev_cer"] < 0.5 * r["cer"])
        nums = mean(r["number_recall"] for r in by(rows, engine=e))
        body.append([e, len(okr), order, visual, pct(nums)] + ([sum(r["empty"] for r in okr)] if show_empty else []))
    md += [table(["Engine", "Pages with output", "Reading-order suspects", "Visual-order suspects",
                  "Number recall"] + (["Empty outputs"] if show_empty else []), body), ""]

    fails = [r for r in rows if r["error"]]
    md += ["## Failures", ""]
    if not fails:
        md += ["None.", ""]
    else:
        seen: dict[tuple[str, str], int] = {}
        for r in fails:
            key = (r["engine"], r["error"].split("\n")[0][:200])
            seen[key] = seen.get(key, 0) + 1
        md += [table(["Engine", "Pages", "Error"], [[e, n, err.replace("|", "/")] for (e, err), n in seen.items()]), ""]

    md += ["## Three typical errors, side by side", "",
           "Each example is the ground-truth line whose error rate is closest to the page CER, after normalization.", ""]
    for k, (why, r) in enumerate(pick_examples(rows, ranked), 1):
        ex = example(r, out, norm)
        if ex is None:
            continue
        md += [f"### {k}. {r['engine']} on `{r['page_id']}`", "",
               f"{why}. Page CER {pct(r['cer'])}, this line {pct(ex['line_cer'])}.", "",
               table(["", "Text"], [["Ground truth", ex["gt"]], ["OCR", ex["ocr"] or "(nothing)"]]), "",
               "Word differences: " + ("; ".join(ex["diffs"]) if ex["diffs"] else "spacing or punctuation only"), ""]
    (out / "summary.md").write_text("\n".join(md), encoding="utf-8")


def score_run(out: Path, norm_name: str = "standard", common: bool = False) -> None:
    rows = score_rows(out, norm_name)
    if common:
        keep = common_pages(rows)
        rows = [r for r in rows if r["page_id"] in keep]
    with open(out / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
    write_summary(out, rows, norm_name, common)
    print(f"wrote {out / 'results.csv'} ({len(rows)} rows) and {out / 'summary.md'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="results folder, e.g. results/2026-10-06")
    ap.add_argument("--norm", default="standard", choices=["standard", "raw", "aggressive"])
    ap.add_argument("--common", action="store_true", help="only pages that every engine finished (partial runs)")
    args = ap.parse_args()
    score_run(ROOT / args.out if not Path(args.out).is_absolute() else Path(args.out), args.norm, args.common)


if __name__ == "__main__":
    main()
