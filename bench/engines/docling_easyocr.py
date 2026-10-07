"""Docling with its EasyOCR backend (lang ar), full-page OCR."""
from docling.datamodel.pipeline_options import EasyOcrOptions, OcrMode

from . import _docling

_conv = None


def load() -> dict:
    global _conv
    _conv = _docling.build(EasyOcrOptions(lang=["ar"], mode=OcrMode.FULL_PAGE))
    return {"version": f"docling {_docling.DOCLING_VERSION}", "device": _docling.device(_conv),
            "model": "EasyOcrOptions(lang=[ar], mode=FULL_PAGE)"}


def ocr(image_path: str) -> str:
    return _docling.to_text(_conv, image_path)
