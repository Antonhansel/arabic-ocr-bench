"""google/gemini-3.1-pro-preview through OpenRouter (see openrouter.py)."""
from . import openrouter as _base

_base.MODEL = "google/gemini-3.1-pro-preview"
load, ocr = _base.load, _base.ocr
