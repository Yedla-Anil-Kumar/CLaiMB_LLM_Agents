# workflows/ml_ops_workflow.py
from pathlib import Path
from typing import Dict, Any, Tuple

from agent_layer.orchestrator_mlops import run as run_agent
from .snapshot_mlops import collect_snapshot

def run_workflow() -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    snapshot = collect_snapshot()
    res = run_agent(snapshot, out_dir=Path("runs_mlop_mvp"))

    artifact_path = res["artifact_path"]
    aggregates    = res["aggregates"]
    metrics       = res["metrics"]
    return artifact_path, aggregates, metrics