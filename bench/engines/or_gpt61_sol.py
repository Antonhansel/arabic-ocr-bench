"""openai/gpt-6.1-sol through OpenRouter (see openrouter.py)."""
from . import openrouter as _base

_base.MODEL = "openai/gpt-6.1-sol"
load, ocr = _base.load, _base.ocr
