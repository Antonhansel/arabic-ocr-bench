"""PaddleOCR with each page shrunk so its long side is 960 px before text
detection. At the defaults, PaddleOCR 3.x does not shrink a 300 dpi scan, and
on pages with a lot of blank paper the detector marks the paper as text: the
binarized map then holds thousands of small contours, the box step reads only
the first 1,000 (DBPostProcess max_candidates), the real lines come after
them, and the page comes back empty with no error (tools/paddle_diag.py)."""
from . import paddleocr_engine as _base

_base.DET_ARGS = {"text_det_limit_type": "max", "text_det_limit_side_len": 960}
load, ocr = _base.load, _base.ocr
