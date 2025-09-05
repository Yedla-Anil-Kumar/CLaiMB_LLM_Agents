#!/usr/bin/env python3
from __future__ import annotations
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# make package imports work
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_collection_agents.ml_ops_agent.logging_utils import setup_logger  # noqa: E402
from workflows.ml_ops_workflow import run_workflow                         # noqa: E402

def main() -> None:
    load_dotenv()
    setup_logger("logs/ml_ops.log", level="INFO", serialize=False)

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set (checked .env).")

    artifact_path, aggregates, metrics = run_workflow()

    print("\n=== ML Ops Monitor MVP Run ===")
    print(f"Artifact: {artifact_path}")
    print("Scores:")
    print(aggregates)
    print(f"Metrics computed: {len(metrics)}")

if __name__ == "__main__":
    main()