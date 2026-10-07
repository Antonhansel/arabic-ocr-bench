"""anthropic/claude-opus-5.5 through OpenRouter (see openrouter.py)."""
from . import openrouter as _base

_base.MODEL = "anthropic/claude-opus-5.5"
load, ocr = _base.load, _base.ocr
