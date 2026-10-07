"""Engine worker. Runs inside the engine's venv: python -m bench.worker <module>

Protocol, one JSON object per line:
  worker -> runner, first line: {"ready": true, "load_seconds": s, "info": {...}}
                                or {"ready": false, "error": "...", "trace": "..."}
  runner -> worker: {"image": "/abs/path.png"}
  worker -> runner: {"text": "..." | null, "seconds": s, "error": null | "..."}

Libraries print progress bars to stdout; fd 1 is pointed at stderr so the
protocol channel stays clean. stderr goes to the engine log.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
import traceback


def main() -> int:
    proto = os.fdopen(os.dup(1), "w", buffering=1, encoding="utf-8")
    os.dup2(2, 1)
    sys.stdout = sys.stderr

    def send(obj: dict) -> None:
        proto.write(json.dumps(obj, ensure_ascii=False) + "\n")
        proto.flush()

    t0 = time.perf_counter()
    try:
        mod = importlib.import_module(sys.argv[1])
        info = mod.load() if hasattr(mod, "load") else {}
    except BaseException as e:  # import errors, missing models, SystemExit from libs
        send({"ready": False, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-4000:]})
        return 1
    send({"ready": True, "load_seconds": time.perf_counter() - t0, "info": info or {}})

    for line in sys.stdin:
        if not line.strip():
            continue
        req = json.loads(line)
        t = time.perf_counter()
        try:
            text, err = mod.ocr(req["image"]), None
        except Exception as e:
            text, err = None, f"{type(e).__name__}: {e}"
            traceback.print_exc()
        send({"text": text, "seconds": time.perf_counter() - t, "error": err})
    return 0


if __name__ == "__main__":
    sys.exit(main())
