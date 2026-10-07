"""google/gemini-3.8-flash through OpenRouter (see openrouter.py)."""
from . import openrouter as _base

_base.MODEL = "google/gemini-3.8-flash"
load, ocr = _base.load, _base.ocr
