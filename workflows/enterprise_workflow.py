# workflows/enterprise_workflow.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Tuple
from loguru import logger

from agent_layer.snapshot_enterprise import collect_snapshot
from agent_layer.orchestrator_enterprise import EnterpriseOrchestrator, now_utc_iso
from data_collection_agents.enterprise_systems_agent.logging_utils import setup_logger  # NEW

ARTIFACT_DIR = Path("runs_enterprise_mvp")
LOGS_DIR = Path("logs")  # NEW


class EnterpriseWorkflow:
    """
    Thin workflow wrapper that:
      - sets up per-run logging
      - collects snapshot
      - runs the orchestrator
      - writes artifact json
    """

    def __init__(self, artifact_dir: Path | None = None, logs_dir: Path | None = None) -> None:  # CHANGED
        self.artifact_dir = artifact_dir or ARTIFACT_DIR
        self.logs_dir = logs_dir or LOGS_DIR  # NEW
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)  # NEW
        self.orchestrator = EnterpriseOrchestrator()

    def run(self, run_id: str | None = None, verbose: bool = True) -> Tuple[Path, Dict[str, Any]]:
        rid = run_id or f"enterprise-{now_utc_iso()}"

        # 🔐 One file per run (plus console). Uses your existing setup_logger, no changes needed there.
        per_run_log = (self.logs_dir / f"{rid}.log").resolve()
        setup_logger(log_path=str(per_run_log), level="INFO", serialize=False)  # NEW
        logger.info(f"Starting EnterpriseWorkflow.run (run_id={rid})")  # NEW

        snapshot = collect_snapshot()
        results, scores, waves = self.orchestrator.run(snapshot, verbose=verbose)

        artifact = {
            "run": {"run_id": rid, "waves": waves},
            "scores": scores,
            "metrics": results,  # keyed by compute_* ids
            "snapshot_meta": snapshot.get("meta", {}),
        }

        out_path = (self.artifact_dir / f"{rid}.json").resolve()
        out_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(f"Artifact written → {out_path}")  # NEW
        return out_path, scores

# === public functional entrypoint kept for CLI compatibility ===
def run_workflow(run_id: str | None = None, verbose: bool = True) -> Tuple[Path, Dict[str, Any]]:
    """
    Backwards-compatible functional API used by mvp/run_enterprise_once.py.
    Internally uses EnterpriseWorkflow class.
    """
    wf = EnterpriseWorkflow()
    return wf.run(run_id=run_id, verbose=verbose)