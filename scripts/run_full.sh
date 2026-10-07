#!/usr/bin/env bash
# Run the benchmark detached-friendly: every default engine on the manifest
# (extra args are passed to bench.run, e.g. --limit 10 or --kind real-scan),
# then Gemini on the small set of the same rows if WITH_GEMINI=1. Writes
# <OUT>/DONE when finished.
#   OUT=results/2026-10-06 WITH_GEMINI=1 nohup scripts/run_full.sh > results/2026-10-06/run.log 2>&1 & disown
set -u
cd "$(dirname "$0")/.."
OUT=${OUT:-results/$(date +%F)}
mkdir -p "$OUT"
rm -f "$OUT/DONE"
start=$(date +%s)
.venv/bin/python -m bench.run --out "$OUT" --resume "$@"
status=$?
if [ "${WITH_GEMINI:-0}" = 1 ]; then
  .venv/bin/python -m bench.run --out "$OUT" --resume --engines gemini-3.5-flash "$@"
  status=$((status + $?))
fi
pkill -f "$PWD/tools/llama.cpp/llama-server" 2>/dev/null
echo "exit=$status minutes=$(( ($(date +%s) - start) / 60 )) finished=$(date '+%F %T')" > "$OUT/DONE"
