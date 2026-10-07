"""mistralai/mistral-medium-3-5 through OpenRouter (see openrouter.py)."""
from . import openrouter as _base

_base.MODEL = "mistralai/mistral-medium-3-5"
load, ocr = _base.load, _base.ocr
