"""Run OCR engines on the manifest, then score.

    .venv/bin/python -m bench.run --engines tesseract --limit 1
    .venv/bin/python -m bench.run --engines tesseract,easyocr --limit 10
    .venv/bin/python -m bench.run                      # all default engines, full manifest
    .venv/bin/python -m bench.run --engines gemini-3.5-flash   # small set only
    .venv/bin/python -m bench.run --kind real-scan --limit 10  # first 10 real scans

Writes into results/<date>/ (or --out):
    outputs/<engine>/<page_id>.txt   raw OCR text, as returned
    raw.jsonl                        one line per (engine, page): seconds, error
    engines.json                     version, device, model, load time per engine
    logs/<engine>.log                engine stderr
    results.csv, summary.md          written by bench.score at the end

Each engine runs in a worker process in its own venv. A page that crashes the
worker or exceeds the engine's page timeout is recorded as a failure and the
worker is restarted for the next page. An engine that fails to load is
recorded as failing every page, with the error.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

from .engines import DEFAULT_ENGINES, ENGINES, Engine

ROOT = Path(__file__).resolve().parent.parent


def python_for(env: str) -> Path:
    return ROOT / (".venv" if env == "core" else f".venvs/{env}") / "bin" / "python"


def engine_env(engine: Engine) -> dict:
    """Keep every model cache inside the project folder. For the Python ML
    envs HOME is redirected too, so libraries that write to ~/.cache,
    ~/.EasyOCR or ~/.paddlex write under models/home instead. The core env
    keeps the real HOME. Workers inherit the rest of the environment,
    including GEMINI_API_KEY and OPENROUTER_API_KEY for the API engines."""
    env = dict(os.environ)
    models = ROOT / "models"
    if engine.env != "core":
        env["HOME"] = str(models / "home")
    env.update({
        "HF_HOME": str(models / "hf"),
        "TORCH_HOME": str(models / "torch"),
        "XDG_CACHE_HOME": str(models / "home" / ".cache"),
        "EASYOCR_MODULE_PATH": str(models / "easyocr"),
        "PADDLE_PDX_CACHE_HOME": str(models / "paddlex"),
        "MPLCONFIGDIR": str(models / "home" / ".matplotlib"),
        "LLAMA_CPP_BINARY": str(ROOT / "tools" / "llama.cpp" / "llama-server"),
        "PYTHONPATH": str(ROOT),
        "PYTHONUNBUFFERED": "1",
        "TOKENIZERS_PARALLELISM": "false",
        "PYTORCH_ENABLE_MPS_FALLBACK": "1",
    })
    for d in ("home", "hf", "torch", "easyocr", "paddlex"):
        (models / d).mkdir(parents=True, exist_ok=True)
    return env


class Worker:
    def __init__(self, engine: Engine, log_path: Path):
        self.engine = engine
        self.log = open(log_path, "a", encoding="utf-8")
        self.log.write(f"\n===== worker start {dt.datetime.now().isoformat(timespec='seconds')}\n")
        self.log.flush()
        py = python_for(engine.env)
        if not py.exists():
            raise FileNotFoundError(f"venv for env '{engine.env}' missing: {py} (run scripts/setup_envs.sh {engine.env})")
        self.proc = subprocess.Popen(
            [str(py), "-m", "bench.worker", engine.module],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log,
            cwd=ROOT, env=engine_env(engine), text=True, encoding="utf-8", bufsize=1,
        )
        self.q: queue.Queue = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        for line in self.proc.stdout:
            self.q.put(line)
        self.q.put(None)

    def read(self, timeout: float) -> dict | None:
        try:
            line = self.q.get(timeout=timeout)
        except queue.Empty:
            return None
        return None if line is None else json.loads(line)

    def send(self, obj: dict) -> None:
        self.proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def alive(self) -> bool:
        return self.proc.poll() is None

    def stop(self) -> None:
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=30)
        except Exception:
            self.proc.kill()
        self.log.close()

    def kill(self) -> None:
        self.proc.kill()
        self.proc.wait()
        self.log.close()


def log_tail(path: Path, n: int = 600) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-n:].strip().replace("\n", " | ")
    except FileNotFoundError:
        return ""


def select_rows(rows: list[dict], engine: Engine, limit: int | None, small: bool,
                kind: str | None = None) -> list[dict]:
    if kind:
        rows = [r for r in rows if r["kind"] == kind]
    if small or engine.small_set_only:
        rows = [r for r in rows if r["small_set"] == "1"]
    return rows[:limit] if limit else rows


def run_engine(engine: Engine, rows: list[dict], out: Path, resume: bool) -> None:
    (out / "outputs" / engine.name).mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    log_path = out / "logs" / f"{engine.name}.log"
    raw_path = out / "raw.jsonl"
    done = set()
    if resume and raw_path.exists():
        for line in raw_path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if rec["engine"] == engine.name and rec["error"] is None:
                done.add(rec["page_id"])
    todo = [r for r in rows if r["page_id"] not in done]
    print(f"[{engine.name}] {len(todo)} pages ({len(done)} already done)", flush=True)
    if not todo:
        return

    def record(row: dict, text: str | None, seconds: float | None, error: str | None) -> None:
        if text is not None:
            (out / "outputs" / engine.name / f"{row['page_id']}.txt").write_text(text, encoding="utf-8")
        rec = {"engine": engine.name, "page_id": row["page_id"], "seconds": seconds, "error": error,
               "time": dt.datetime.now().isoformat(timespec="seconds")}
        with open(raw_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def start() -> tuple[Worker | None, str | None]:
        try:
            w = Worker(engine, log_path)
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"
        t0 = time.time()
        msg = w.read(timeout=engine.load_timeout)
        if msg is None:
            alive = w.alive()
            w.kill()
            why = f"load timeout after {engine.load_timeout}s" if alive else "worker exited during load"
            return None, f"{why}: {log_tail(log_path)}"
        if not msg.get("ready"):
            w.stop()
            return None, f"load failed: {msg.get('error')}"
        info = msg.get("info", {})
        info["load_seconds"] = round(msg.get("load_seconds", time.time() - t0), 2)
        eng_path = out / "engines.json"
        allinfo = json.loads(eng_path.read_text()) if eng_path.exists() else {}
        allinfo[engine.name] = info
        eng_path.write_text(json.dumps(allinfo, indent=2, ensure_ascii=False))
        print(f"[{engine.name}] loaded in {info['load_seconds']}s: {info}", flush=True)
        return w, None

    worker, err = start()
    for i, row in enumerate(todo):
        if worker is None:
            record(row, None, None, err)
            continue
        image = str(ROOT / row["image"])
        worker.send({"image": image})
        resp = worker.read(timeout=engine.page_timeout)
        if resp is None:
            alive = worker.alive()
            code = worker.proc.poll()
            worker.kill()
            why = (f"timeout after {engine.page_timeout}s" if alive
                   else f"worker crashed (exit {code}): {log_tail(log_path, 300)}")
            record(row, None, None, why)
            print(f"[{engine.name}] {row['page_id']}: {why}", flush=True)
            worker, err = start()
            continue
        record(row, resp["text"], resp["seconds"], resp["error"])
        status = resp["error"] or f"{resp['seconds']:.1f}s, {len(resp['text'] or '')} chars"
        print(f"[{engine.name}] {i + 1}/{len(todo)} {row['page_id']}: {status}", flush=True)
    if worker is not None:
        worker.stop()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engines", default=",".join(DEFAULT_ENGINES),
                    help=f"comma list from: {', '.join(ENGINES)}")
    ap.add_argument("--limit", type=int, default=None, help="first N manifest rows (the manifest is stratified)")
    ap.add_argument("--small", action="store_true", help="only rows with small_set=1")
    ap.add_argument("--kind", choices=["born-digital", "synthetic", "real-scan"], default=None,
                    help="only rows of this kind (applied before --limit)")
    ap.add_argument("--out", default=None, help="results folder (default results/<today>)")
    ap.add_argument("--resume", action="store_true", help="skip (engine, page) pairs already done without error")
    ap.add_argument("--norm", default="standard", help="normalization preset for the report")
    args = ap.parse_args()

    names = [n.strip() for n in args.engines.split(",") if n.strip()]
    unknown = [n for n in names if n not in ENGINES]
    if unknown:
        sys.exit(f"unknown engines: {unknown}; known: {list(ENGINES)}")
    out = ROOT / (args.out or f"results/{dt.date.today().isoformat()}")
    out.mkdir(parents=True, exist_ok=True)
    with open(ROOT / "data" / "manifest.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for name in names:
        engine = ENGINES[name]
        run_engine(engine, select_rows(rows, engine, args.limit, args.small, args.kind), out, args.resume)

    from .score import score_run
    score_run(out, args.norm)


if __name__ == "__main__":
    main()
