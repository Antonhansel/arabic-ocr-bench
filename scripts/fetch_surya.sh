#!/usr/bin/env bash
# Surya 0.22 runs its VLM through llama.cpp on macOS. Fetch a prebuilt
# llama-server (Metal) and the Surya GGUF weights into the project folder.
set -euo pipefail
cd "$(dirname "$0")/.."
LLAMA_TAG=${LLAMA_TAG:-b11433}
if [ ! -x tools/llama.cpp/llama-server ]; then
  mkdir -p tools/llama.cpp
  curl -sSL -o /tmp/llama.tgz "https://github.com/ggml-org/llama.cpp/releases/download/${LLAMA_TAG}/llama-${LLAMA_TAG}-bin-macos-arm64.tar.gz"
  tar -xzf /tmp/llama.tgz -C tools/llama.cpp --strip-components=1
  rm -f /tmp/llama.tgz
fi
HF_HOME="$PWD/models/hf" .venvs/surya/bin/python - <<'PY'
from huggingface_hub import hf_hub_download
for f in ("surya-2.gguf", "surya-2-mmproj.gguf"):
    print(hf_hub_download(repo_id="datalab-to/surya-ocr-2-gguf", filename=f))
PY
echo done
