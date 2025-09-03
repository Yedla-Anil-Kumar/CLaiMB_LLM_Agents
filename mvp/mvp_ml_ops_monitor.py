# mvp/mvp_ml_ops_monitor.py
from __future__ import annotations
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from data_collection_agents.ml_ops_agent.logging_utils import setup_logger

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflows.ml_ops_workflow import run_workflow  # noqa: E402

def main() -> None:
    load_dotenv()
    setup_logger("logs/bi_tracker.log", level="INFO", serialize=False)
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set (checked .env).")
    artifact, aggregates, results = run_workflow()
    print("\n=== ML Ops Monitor MVP Run ===")
    print(f"Artifact: {artifact}")
    print(f"Scores: {aggregates}")
    print(f"Metrics computed: {len(results)}")

if __name__ == "__main__":
    main()