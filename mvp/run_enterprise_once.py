# mvp/run_enterprise_once.py
from __future__ import annotations
import argparse
from dotenv import load_dotenv
from workflows.enterprise_workflow import run_workflow
from data_collection_agents.enterprise_systems_agent.logging_utils import setup_logger  # noqa: E402

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Enterprise Systems Agent once.")
    p.add_argument("--run-id", default=None, help="Optional run id (default: enterprise-<UTC>)")
    p.add_argument("--quiet", action="store_true", help="Suppress per-wave printouts")
    return p.parse_args()

def main() -> None:
    load_dotenv()  
    setup_logger("logs/agent_layer.log", level="INFO", serialize=False)

    args = parse_args()
    out_path, scores = run_workflow(run_id=args.run_id, verbose=not args.quiet)

    print("\n=== Enterprise Systems Agent MVP Run ===")
    print(f"Artifact: {out_path}")
    print(f"Scores: {scores}")

if __name__ == "__main__":
    main()