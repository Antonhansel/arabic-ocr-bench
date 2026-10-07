#!/usr/bin/env bash
# Combine runs into one results folder, so one summary covers every image of
# the manifest: copies outputs/ and raw records, merges engines.json, then
# scores. The copies are the original measurements; nothing is re-run.
#   scripts/combine_runs.sh results/2026-10-07-all results/2026-10-06 results/2026-10-07-realscans
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=$1; shift
mkdir -p "$OUT/outputs"
: > "$OUT/raw.jsonl"
for run in "$@"; do
  cp -R "$run/outputs/." "$OUT/outputs/"
  cat "$run/raw.jsonl" >> "$OUT/raw.jsonl"
done
.venv/bin/python - "$OUT" "$@" <<'PY'
import json, sys
from pathlib import Path
out, runs = Path(sys.argv[1]), sys.argv[2:]
merged = {}
for run in runs:
    p = Path(run) / "engines.json"
    if p.exists():
        for name, info in json.loads(p.read_text()).items():
            merged.setdefault(name, {}).update(info)   # later runs win (newer versions, same settings)
(out / "engines.json").write_text(json.dumps(merged, indent=2, ensure_ascii=False))
print(f"{len(merged)} engines in {out / 'engines.json'}")
PY
.venv/bin/python -m bench.score "$OUT"
