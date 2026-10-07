"""Surya OCR 0.22 (surya-ocr-2 VLM), full-page mode, served locally by
llama.cpp's llama-server with Metal (the macOS path Surya documents). The
llama-server binary and the GGUF weights live in the project folder
(scripts/fetch_surya.sh). Output blocks are HTML; tags are stripped and
blocks joined in Surya's reading order."""
import atexit
import html
import re
from importlib.metadata import version

from PIL import Image

_pred = None
_mgr = None


def _html_to_text(s: str) -> str:
    s = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h[1-6]|table|ul|ol)>", "\n", s)
    s = re.sub(r"(?i)</t[dh]>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def load() -> dict:
    global _pred, _mgr
    from surya.inference import SuryaInferenceManager
    from surya.recognition import RecognitionPredictor
    from surya.settings import settings
    _mgr = SuryaInferenceManager()
    _mgr.start()
    atexit.register(_mgr.stop)
    _pred = RecognitionPredictor(_mgr)
    return {"version": f"surya-ocr {version('surya-ocr')}", "device": f"{_mgr.method} (Metal)",
            "model": f"{settings.SURYA_MODEL_CHECKPOINT} GGUF, full_page=True"}


def ocr(image_path: str) -> str:
    img = Image.open(image_path).convert("RGB")
    page = _pred([img], full_page=True)[0]
    blocks = sorted(page.blocks, key=lambda b: b.reading_order)
    texts = [_html_to_text(b.html) for b in blocks if not b.skipped and b.html]
    return "\n".join(t for t in texts if t)
