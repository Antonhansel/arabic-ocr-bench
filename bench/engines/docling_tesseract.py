"""Docling with its Tesseract CLI backend (lang ara), full-page OCR."""
from docling.datamodel.pipeline_options import OcrMode, TesseractCliOcrOptions

from . import _docling

_conv = None


def load() -> dict:
    global _conv
    _conv = _docling.build(TesseractCliOcrOptions(lang=["ara"], mode=OcrMode.FULL_PAGE))
    return {"version": f"docling {_docling.DOCLING_VERSION}", "device": _docling.device(_conv),
            "model": "TesseractCliOcrOptions(lang=[ara], mode=FULL_PAGE)"}


def ocr(image_path: str) -> str:
    return _docling.to_text(_conv, image_path)
