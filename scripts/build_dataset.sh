#!/usr/bin/env bash
# Build dataset v0. Pillow needs Homebrew's fribidi for Arabic shaping (raqm).
# Usage: scripts/build_dataset.sh [--limit N]
set -euo pipefail
cd "$(dirname "$0")/.."
# Law PDFs: downloaded if missing, then compared with the copies behind the published results.
.venv/bin/python scripts/download_data.py --only laws
[ -f fonts/NotoNaskhArabic.ttf ] || {
  mkdir -p fonts
  curl -sSL -o fonts/NotoNaskhArabic.ttf "https://github.com/google/fonts/raw/main/ofl/notonaskharabic/NotoNaskhArabic%5Bwght%5D.ttf"
  curl -sSL -o fonts/OFL-NotoNaskhArabic.txt "https://github.com/google/fonts/raw/main/ofl/notonaskharabic/OFL.txt"
}
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib .venv/bin/python -m bench.dataset "$@"
