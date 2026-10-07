"""Docling with its RapidOCR backend (onnxruntime, PP-OCR Arabic
recognizer), full-page OCR."""
from docling.datamodel.pipeline_options import OcrMode, RapidOcrOptions

from . import _docling

_conv = None


def load() -> dict:
    global _conv
    _conv = _docling.build(RapidOcrOptions(lang=["arabic"], mode=OcrMode.FULL_PAGE))
    return {"version": f"docling {_docling.DOCLING_VERSION}", "device": _docling.device(_conv),
            "model": "RapidOcrOptions(lang=[arabic], backend onnxruntime, mode=FULL_PAGE)"}


def ocr(image_path: str) -> str:
    return _docling.to_text(_conv, image_path)
