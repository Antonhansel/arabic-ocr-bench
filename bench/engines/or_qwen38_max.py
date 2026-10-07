"""qwen/qwen3.8-max-prime through OpenRouter (see openrouter.py)."""
from . import openrouter as _base

_base.MODEL = "qwen/qwen3.8-max-prime"
load, ocr = _base.load, _base.ocr
