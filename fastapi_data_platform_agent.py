# fastapi_data_platform_agent.py
# FastAPI wrapper for the Data Platform Scanner (mvp_data_platform_scanner.py)
# Endpoints:
# - GET  /health         → quick health check
# - POST /run            → run a scan now (optional run_id, verbose)
# - GET  /latest         → fetch the latest run artifact
# - GET  /runs           → list available run_ids
# - GET  /runs/{run_id}  → fetch a specific run artifact

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import json
import glob

# Import your MVP scanner entrypoint
from mvp_data_platform_scanner import run_once

# Directory where run artifacts are stored
RUNS_DIR = Path("runs_mvp_scanner")
RUNS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Data Platform Scanner Agent API",
    version="0.1.0",
    description="Snowflake/BigQuery/Databricks/Redshift scanning — deterministic DAG orchestration."
)


# Request body schema for /run endpoint
class RunRequest(BaseModel):
    run_id: str | None = None
    verbose: bool = False


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/run")
def run_now(req: RunRequest):
    """Run a new scan immediately."""
    rid = req.run_id or f"data-scan-{datetime.utcnow():%Y%m%dT%H%M%S}"
    try:
        out = run_once()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return out  # {"run_id","ts","results":[...],"aggregate":{...}}


@app.get("/runs")
def list_runs():
    """List all available runs."""
    files = sorted(glob.glob(str(RUNS_DIR / "*.json")))
    runs = [Path(f).stem for f in files]
    return {"count": len(runs), "runs": runs}


@app.get("/latest")
def latest():
    """Fetch the latest run artifact."""
    files = sorted(glob.glob(str(RUNS_DIR / "*.json")))
    if not files:
        return {"status": "no_runs"}
    with open(files[-1], encoding="utf-8") as f:
        return json.load(f)


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    """Fetch a specific run artifact by run_id."""
    path = RUNS_DIR / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="run_id not found")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

@app.get("/runs/latest/{n}")
def latest_n_runs(n: int):
    """Fetch the last n run artifacts."""
    files = sorted(glob.glob(str(RUNS_DIR / "*.json")))
    if not files:
        return {"status": "no_runs"}
    
    # Take the last n files
    last_files = files[-n:]
    runs = []
    for f in last_files:
        with open(f, encoding="utf-8") as file:
            runs.append(json.load(file))
    
    return {"count": len(runs), "runs": runs}


# uvicorn fastapi_data_platform_agent:app --reload