#!/usr/bin/env bash
# Create the core venv (.venv) and one venv per heavy engine (.venvs/<name>).
# Usage: scripts/setup_envs.sh [core] [docling] [paddle] [surya]   (default: all)
set -u
cd "$(dirname "$0")/.."
PY=${PY:-3.12}
envs=("$@")
[ ${#envs[@]} -eq 0 ] && envs=(core docling paddle surya)
for e in "${envs[@]}"; do
  if [ "$e" = core ]; then dir=.venv; else dir=.venvs/$e; fi
  echo "=== $e -> $dir"
  [ -x "$dir/bin/python" ] || uv venv --python "$PY" "$dir"
  if uv pip install --python "$dir/bin/python" -r "envs/$e.txt"; then
    uv pip freeze --python "$dir/bin/python" > "envs/$e.lock.txt"
    echo "=== $e OK"
  else
    echo "=== $e FAILED"
  fi
done
