# api_code_repo.py
from __future__ import annotations
from fastapi import FastAPI, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import os, json, re
from datetime import datetime

from workflows.code_repo_workflow import CodeRepoWorkflow

API_KEY = os.getenv("API_KEY")
DEFAULT_RUNS_DIR = os.getenv("RUNS_DIR", "runs_code_repo_mvp")
DEFAULT_LOGS_DIR = os.getenv("LOGS_DIR", "logs")

app = FastAPI(title="Code Repo Agent API", version="0.1.0")

# ---------- Schemas ----------
class RunReq(BaseModel):
    repo_path: str
    run_id: Optional[str] = None

class RunItem(BaseModel):
    run_id: str
    output_path: str
    log_path: str
    output: Dict[str, Any]
    log: str

class RunsList(BaseModel):
    count: int
    runs: List[RunItem]

# ---------- Auth ----------
def _auth(x_api_key: Optional[str]):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# ---------- Helpers ----------
def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"<<ERROR reading {path}: {e}>>"

def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"failed to read {str(path)}: {e}"}

def _paths_for(run_id: str, runs_dir: str, logs_dir: str) -> Tuple[Path, Path]:
    return Path(runs_dir) / f"{run_id}.json", Path(logs_dir) / f"{run_id}.log"

def _collect_run(run_id: str, runs_dir: str, logs_dir: str) -> RunItem:
    out_p, log_p = _paths_for(run_id, runs_dir, logs_dir)
    if not out_p.exists():
        raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")
    output = _load_json(out_p)
    log = _read_text(log_p) if log_p.exists() else "<<no log file>>"
    return RunItem(
        run_id=run_id,
        output_path=str(out_p.resolve()),
        log_path=str(log_p.resolve()),
        output=output,
        log=log,
    )

# prefix-agnostic: e.g., code-repo-2025-09-04T19-56-33Z
RUN_ID_TS_RE = re.compile(
    r"^code-repo-(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z)$"
)


def _parse_run_ts_from_stem(stem: str) -> Optional[datetime]:
    m = RUN_ID_TS_RE.match(stem)
    if not m:
        return None
    ts = m.group("ts")
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H-%M-%SZ")
    except Exception:
        return None

def _find_all_runs(runs_dir: str) -> List[Path]:
    return sorted(Path(runs_dir).glob("*.json"))

def _find_latest_run(runs_dir: str) -> Optional[Path]:
    items = _find_all_runs(runs_dir)
    if not items:
        return None

    def sort_key(p: Path):
        stem = p.stem
        name_ts = _parse_run_ts_from_stem(stem)
        return (name_ts or datetime.fromtimestamp(p.stat().st_mtime), stem)

    items.sort(key=sort_key)
    return items[-1]

# ---------- Endpoints ----------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run", response_model=RunItem)
def run(req: RunReq, x_api_key: Optional[str] = Header(default=None)):
    _auth(x_api_key)

    runs_dir = DEFAULT_RUNS_DIR
    logs_dir = DEFAULT_LOGS_DIR
    Path(runs_dir).mkdir(parents=True, exist_ok=True)
    Path(logs_dir).mkdir(parents=True, exist_ok=True)

    wf = CodeRepoWorkflow(artifact_dir=Path(runs_dir), logs_dir=Path(logs_dir))
    out_path, result = wf.run(repo_path=req.repo_path, run_id=req.run_id)

    rid = Path(out_path).stem
    log_p = Path(logs_dir) / f"{rid}.log"

    return RunItem(
        run_id=rid,
        output_path=str(out_path.resolve()),
        log_path=str(log_p.resolve()),
        output=json.loads(out_path.read_text(encoding="utf-8")),
        log=(log_p.read_text(encoding="utf-8") if log_p.exists() else "<<no log file>>"),
    )

# Keep both /latest and /runs/latest for convenience
def _latest_impl(x_api_key: Optional[str]):
    _auth(x_api_key)
    runs_dir = DEFAULT_RUNS_DIR
    logs_dir = DEFAULT_LOGS_DIR
    latest_p = _find_latest_run(runs_dir)
    if not latest_p:
        raise HTTPException(status_code=404, detail="no runs found")
    return _collect_run(latest_p.stem, runs_dir, logs_dir)

@app.get("/latest", response_model=RunItem)
def latest(x_api_key: Optional[str] = Header(default=None)):
    return _latest_impl(x_api_key)


@app.get("/runs", response_model=RunsList)
def list_runs(
    x_api_key: Optional[str] = Header(default=None),
    limit: Optional[int] = Query(default=None, ge=1, description="Optional cap on number of runs returned (most recent first)"),
):
    _auth(x_api_key)
    runs_dir = DEFAULT_RUNS_DIR
    logs_dir = DEFAULT_LOGS_DIR

    items = _find_all_runs(runs_dir)
    def sort_key(p: Path):
        ts = _parse_run_ts_from_stem(p.stem)
        return (ts or datetime.fromtimestamp(p.stat().st_mtime), p.name)
    items.sort(key=sort_key, reverse=True)
    if limit is not None:
        items = items[:limit]

    runs = [_collect_run(p.stem, runs_dir, logs_dir) for p in items]
    return RunsList(count=len(_find_all_runs(runs_dir)), runs=runs)

@app.get("/runs/{run_id}", response_model=RunItem)
def get_run(run_id: str, x_api_key: Optional[str] = Header(default=None)):
    _auth(x_api_key)
    runs_dir = DEFAULT_RUNS_DIR
    logs_dir = DEFAULT_LOGS_DIR
    return _collect_run(run_id, runs_dir, logs_dir)
