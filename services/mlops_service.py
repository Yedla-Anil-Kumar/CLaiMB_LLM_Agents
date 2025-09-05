#!/usr/bin/env python3
"""
ML Ops Monitor microservice (FastAPI)

Endpoints (mentor-style):
- GET  /health                     → simple liveness check
- POST /run                       → start a new ML Ops run, returns run_id
- GET  /status/{run_id}           → run status + artifact/log paths
- GET  /runs                      → list all runs (most-recent first)
- GET  /logs/{run_id}             → full logs (or last N via ?tail=200)
- GET  /latest                    → metadata for the latest run
- GET  /logs/latest               → logs for the latest run
"""

from __future__ import annotations
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from loguru import logger

# ---- import path bootstrap ----
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# --------------------------------

# ⬇️ Swap these imports to your ML Ops agent code
from agent_layer.orchestrator_mlops import run as run_mlops              # noqa: E402
from workflows.ml_ops_workflow import collect_snapshot                    # noqa: E402

# -----------------------
# Config & log setup
# -----------------------
load_dotenv()

ARTIFACT_DIR = Path(os.getenv("MLOPS_ARTIFACT_DIR", "runs_mlops_mvp")).resolve()
LOG_DIR      = Path(os.getenv("MLOPS_LOG_DIR", "logs/mlops_monitor")).resolve()
LOG_LEVEL    = os.getenv("LOG_LEVEL", "INFO")

ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# base sinks
logger.remove()
logger.add(
    sink=lambda m: print(m, end=""),
    level=LOG_LEVEL,
    backtrace=False,
    diagnose=False,
)
logger.add(
    LOG_DIR / "service.log",
    level=LOG_LEVEL,
    rotation="10 MB",
    retention=10,
    compression="zip",
)

app = FastAPI(title="ML Ops Monitor Service", version="0.1.0")

# -----------------------
# In-memory run registry
# -----------------------
class RunStatus(BaseModel):
    run_id: str
    status: str = Field(description="queued | running | finished | failed")
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    artifact_path: Optional[str] = None
    log_path: Optional[str] = None
    error: Optional[str] = None

RUNS: Dict[str, RunStatus] = {}
RUNS_LOCK = threading.Lock()

# -----------------------
# Request/Response models
# -----------------------
class RunRequest(BaseModel):
    snapshot: Optional[Dict[str, Any]] = None  # if omitted, we call collect_snapshot()
    out_dir: Optional[str] = None              # override artifact directory if desired

class RunResponse(BaseModel):
    run_id: str
    status: str
    artifact_dir: str
    log_path: str

# -----------------------
# Helpers
# -----------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    uid = uuid.uuid4().hex[:8]
    return f"mlops-monitor-{ts}-{uid}"

def _read_tail(path: Path, tail: int) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    if tail <= 0:
        return data
    lines = data.splitlines()
    return "\n".join(lines[-tail:])

def _latest_run_id() -> Optional[str]:
    with RUNS_LOCK:
        if not RUNS:
            return None
        items = [r for r in RUNS.values() if r.started_at]
    if not items:
        return None
    items.sort(key=lambda r: r.started_at or "", reverse=True)
    return items[0].run_id

# -----------------------
# Worker
# -----------------------
def _execute_run(run_id: str, snapshot: Optional[Dict[str, Any]], out_dir: Path) -> None:
    """
    Background thread: executes orchestrator.run(...) and updates RUNS.
    """
    run_log = LOG_DIR / f"{run_id}.log"
    sink_id = logger.add(run_log, level="INFO", rotation="5 MB", retention=5, compression="zip")

    with RUNS_LOCK:
        st = RUNS.get(run_id)
        if st:
            st.status = "running"
            st.started_at = _now_iso()
            st.log_path = str(run_log)

    try:
        snap = snapshot if snapshot is not None else collect_snapshot()
        logger.info(f"[{run_id}] Starting ML Ops monitor run…")
        result = run_mlops(snap, out_dir=out_dir)

        artifact_path = result.get("artifact_path")
        with RUNS_LOCK:
            st = RUNS.get(run_id)
            if st:
                st.status = "finished"
                st.finished_at = _now_iso()
                st.artifact_path = artifact_path

        logger.info(f"[{run_id}] Finished. Artifact: {artifact_path}")
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        logger.exception(f"[{run_id}] FAILED: {msg}")
        with RUNS_LOCK:
            st = RUNS.get(run_id)
            if st:
                st.status = "failed"
                st.finished_at = _now_iso()
                st.error = msg
    finally:
        logger.remove(sink_id)  # remove only the per-run sink

# -----------------------
# Endpoints
# -----------------------
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/run", response_model=RunResponse)
def start_run(req: RunRequest, tasks: BackgroundTasks) -> RunResponse:
    run_id = _new_run_id()
    out_dir = Path(req.out_dir).resolve() if req.out_dir else ARTIFACT_DIR

    meta = RunStatus(
        run_id=run_id,
        status="queued",
        started_at=_now_iso(),
        artifact_path=None,
        log_path=str(LOG_DIR / f"{run_id}.log"),
    )
    with RUNS_LOCK:
        RUNS[run_id] = meta

    tasks.add_task(_execute_run, run_id, req.snapshot, out_dir)

    return RunResponse(
        run_id=run_id,
        status="queued",
        artifact_dir=str(out_dir),
        log_path=meta.log_path or "",
    )

@app.get("/status/{run_id}", response_model=RunStatus)
def get_status(run_id: str) -> RunStatus:
    with RUNS_LOCK:
        st = RUNS.get(run_id)
    if not st:
        raise HTTPException(status_code=404, detail="run_id not found")
    return st

@app.get("/runs")
def list_runs() -> List[RunStatus]:
    with RUNS_LOCK:
        items = list(RUNS.values())
    items.sort(key=lambda r: r.started_at or "", reverse=True)
    return items

@app.get("/latest")
def latest_run() -> RunStatus:
    rid = _latest_run_id()
    if not rid:
        raise HTTPException(status_code=404, detail="no runs yet")
    return get_status(rid)

@app.get("/logs/{run_id}")
def get_logs(run_id: str, tail: int = Query(0, ge=0)) -> Dict[str, Any]:
    with RUNS_LOCK:
        st = RUNS.get(run_id)
    if not st:
        raise HTTPException(status_code=404, detail="run_id not found")
    p = Path(st.log_path or "")
    if not p.exists():
        return {"run_id": run_id, "log": ""}
    return {"run_id": run_id, "log": _read_tail(p, tail)}

@app.get("/logs/latest")
def latest_logs(tail: int = Query(0, ge=0)) -> Dict[str, Any]:
    rid = _latest_run_id()
    if not rid:
        raise HTTPException(status_code=404, detail="no runs yet")
    return get_logs(rid, tail)