# workflows/enterprise_workflow.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Tuple

from agent_layer.snapshot_enterprise import collect_snapshot
from agent_layer.orchestrator_enterprise import run as run_agent, now_utc_iso

ARTIFACT_DIR = Path("runs_enterprise_mvp")

def run_workflow(run_id: str | None = None, verbose: bool = True) -> Tuple[Path, Dict[str, Any]]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    rid = run_id or f"enterprise-{now_utc_iso()}"

    snapshot = collect_snapshot()
    results, scores, waves = run_agent(snapshot, verbose=verbose)

    artifact = {
        "run": {
            "run_id": rid,
            "waves": waves,
        },
        "scores": scores,
        "metrics": results,  # keyed by compute_* ids; each has band A..E, score_0to100, rationale, gaps, and legacy Score
        "snapshot_meta": snapshot.get("meta", {}),
    }

    out_path = ARTIFACT_DIR / f"{rid}.json"
    out_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")

    return out_path, scores