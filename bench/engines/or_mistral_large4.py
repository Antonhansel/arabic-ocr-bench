"""mistralai/mistral-large-4-0 through OpenRouter (see openrouter.py)."""
from . import openrouter as _base

_base.MODEL = "mistralai/mistral-large-4-0"
load, ocr = _base.load, _base.ocr
