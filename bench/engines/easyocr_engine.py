"""EasyOCR, Arabic model (lang 'ar'), on Apple GPU (MPS) when available.

readtext() returns boxes; page text is built with the shared _boxes.rtl_lines
rule, as for PaddleOCR and Apple Vision. EasyOCR's own paragraph=True mode
was tried on the first test page and scored worse (CER 8.7% vs 4.2%): it
merges lines inside a paragraph out of order.
"""
import easyocr
import torch

from ._boxes import rtl_lines

_reader = None


def load() -> dict:
    global _reader
    _reader = easyocr.Reader(["ar"], gpu=torch.backends.mps.is_available(), verbose=False)
    return {"version": f"easyocr {easyocr.__version__}, torch {torch.__version__}",
            "device": str(_reader.device), "model": "lang ar, boxes -> rtl_lines"}


def ocr(image_path: str) -> str:
    res = _reader.readtext(image_path, detail=1, paragraph=False)
    boxes = [(min(p[0] for p in b), min(p[1] for p in b), max(p[0] for p in b), max(p[1] for p in b), t)
             for b, t, _conf in res]
    return rtl_lines(boxes)
