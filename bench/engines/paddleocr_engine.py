"""PaddleOCR 3.x pipeline with lang='ar' (PaddleOCR picks its Arabic
recognition model and its server detection model), on CPU (PaddlePaddle has
no Apple GPU backend). Document orientation, unwarping and text-line
orientation modules are off: the pages are upright. Boxes are turned into
page text with the shared _boxes.rtl_lines rule. DET_ARGS holds extra text-detection
settings for variants (see paddleocr_max960.py); empty means PaddleOCR defaults."""
import paddle
import paddleocr
from paddleocr import PaddleOCR

from ._boxes import rtl_lines

_ocr = None
DET_ARGS: dict = {}


def load() -> dict:
    global _ocr
    _ocr = PaddleOCR(lang="ar", use_doc_orientation_classify=False, use_doc_unwarping=False,
                     use_textline_orientation=False, **DET_ARGS)
    try:
        det, rec = _ocr._get_ocr_model_names("ar", None)
        model = f"det {det}, rec {rec}"
    except Exception:
        model = "lang ar"
    if DET_ARGS:
        model += ", " + ", ".join(f"{k}={v}" for k, v in DET_ARGS.items())
    return {"version": f"paddleocr {paddleocr.__version__}, paddlepaddle {paddle.__version__}",
            "device": "cpu", "model": model}


def ocr(image_path: str) -> str:
    res = _ocr.predict(image_path)[0]
    boxes = [(float(b[0]), float(b[1]), float(b[2]), float(b[3]), t)
             for b, t in zip(res["rec_boxes"], res["rec_texts"])]
    return rtl_lines(boxes)
