"""Why PaddleOCR returns empty pages on some 300 dpi scans.

Runs the PaddleOCR pipeline (same settings as bench/engines/paddleocr_engine.py)
on given pages under a few detection settings, and records what the text
detector saw: the size of the probability map, its strongest values, the share
of pixels above the binarization threshold, and the number of text boxes.
Each probability map is also saved as a PNG next to the report.

Run in the paddle env, with the bench's model cache:
    HOME=$PWD/models/home PADDLE_PDX_CACHE_HOME=$PWD/models/paddlex \
      .venvs/paddle/bin/python tools/paddle_diag.py OUT_DIR PAGE.png [PAGE.png ...]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

from paddleocr import PaddleOCR
from paddlex.inference.models.text_detection import processors as P

OUT = Path(sys.argv[1])
PAGES = [Path(p) for p in sys.argv[2:]]
OUT.mkdir(parents=True, exist_ok=True)

# name -> extra PaddleOCR arguments (None = the bench default)
SETTINGS = {
    "default": {},
    "long-side-960": {"text_det_limit_type": "max", "text_det_limit_side_len": 960},
    "long-side-1920": {"text_det_limit_type": "max", "text_det_limit_side_len": 1920},
    "thresh-0.15": {"text_det_thresh": 0.15},
}

_maps: list[dict] = []
_orig = P.DBPostProcess.process


def _capture(self, pred, img_shape, thresh, box_thresh, unclip_ratio):
    p = pred[0]
    _maps.append({"map": p.copy(), "thresh": float(thresh), "box_thresh": float(box_thresh)})
    return _orig(self, pred, img_shape, thresh, box_thresh, unclip_ratio)


P.DBPostProcess.process = _capture

report = []
for name, extra in SETTINGS.items():
    ocr = PaddleOCR(lang="ar", use_doc_orientation_classify=False, use_doc_unwarping=False,
                    use_textline_orientation=False, **extra)
    for page in PAGES:
        _maps.clear()
        t0 = time.time()
        res = ocr.predict(str(page))[0]
        secs = time.time() - t0
        m = _maps[-1]
        prob = m["map"]
        heat = Image.fromarray((np.clip(prob, 0, 1) * 255).astype(np.uint8))
        heat_path = OUT / f"{page.stem}__{name}.png"
        heat.save(heat_path)
        row = {
            "page": page.stem, "setting": name, "seconds": round(secs, 1),
            "image": list(Image.open(page).size), "map": [int(prob.shape[1]), int(prob.shape[0])],
            "map_max": round(float(prob.max()), 3), "map_p999": round(float(np.percentile(prob, 99.9)), 3),
            "share_over_thresh": round(float((prob > m["thresh"]).mean()), 5),
            "thresh": m["thresh"], "box_thresh": m["box_thresh"],
            "boxes": len(res["dt_polys"]), "chars": sum(len(t) for t in res["rec_texts"]),
        }
        report.append(row)
        print(json.dumps(row), flush=True)

(OUT / "report.json").write_text(json.dumps(report, indent=2))
