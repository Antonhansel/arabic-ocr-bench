"""Engine registry.

An engine adapter is a module with one function, `ocr(image_path) -> str`,
and an optional `load() -> dict` that loads models once and returns facts
for the report (version, device, model). Each engine runs in a worker
process inside its own venv (see bench/worker.py), so a crash or a hang
costs one page, not the run.

Envs: "core" = .venv ; any other name = .venvs/<name>.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Engine:
    name: str
    module: str
    env: str
    small_set_only: bool = False     # paid or slow engines: only manifest rows with small_set=1
    page_timeout: int = 600          # seconds before a page is recorded as a timeout
    load_timeout: int = 3600         # first load may download models


ENGINES = {e.name: e for e in [
    Engine("tesseract", "bench.engines.tesseract", "core"),
    Engine("apple-vision", "bench.engines.apple_vision", "core"),
    Engine("apple-livetext", "bench.engines.apple_livetext", "core"),
    Engine("easyocr", "bench.engines.easyocr_engine", "docling"),
    Engine("paddleocr", "bench.engines.paddleocr_engine", "paddle"),
    Engine("paddleocr-max960", "bench.engines.paddleocr_max960", "paddle"),
    Engine("surya", "bench.engines.surya_engine", "surya", page_timeout=900),
    Engine("docling-easyocr", "bench.engines.docling_easyocr", "docling"),
    Engine("docling-tesseract", "bench.engines.docling_tesseract", "docling"),
    Engine("docling-rapidocr", "bench.engines.docling_rapidocr", "docling"),
    Engine("gemini-3.5-flash", "bench.engines.gemini", "core", small_set_only=True, page_timeout=300),
    Engine("or-gemini-3.8-flash", "bench.engines.or_gemini38_flash", "core", small_set_only=True, page_timeout=300),
    Engine("or-gemini-3.1-pro", "bench.engines.or_gemini31_pro", "core", small_set_only=True, page_timeout=300),
    Engine("or-gpt-6.1-sol", "bench.engines.or_gpt61_sol", "core", small_set_only=True, page_timeout=300),
    Engine("or-claude-opus-5.5", "bench.engines.or_claude_opus55", "core", small_set_only=True, page_timeout=300),
    Engine("or-qwen3.8-max", "bench.engines.or_qwen38_max", "core", small_set_only=True, page_timeout=300),
    Engine("or-mistral-large-4", "bench.engines.or_mistral_large4", "core", small_set_only=True, page_timeout=300),
    Engine("or-mistral-medium-3.5", "bench.engines.or_mistral_medium35", "core", small_set_only=True, page_timeout=300),
]}

# Engines run when --engines is not given. API engines (Gemini, OpenRouter) are
# opt-in: they send the page images to a provider and cost money.
DEFAULT_ENGINES = [n for n, e in ENGINES.items() if not e.small_set_only]
