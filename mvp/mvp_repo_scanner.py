# mvp/mvp_repo_scanner.py
from __future__ import annotations
import argparse
import json
from pathlib import Path

# make imports work as module
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflows.code_repo_workflow import run_workflow # noqa: E402

def main() -> None:
    parser = argparse.ArgumentParser(description="Run Code Repo Agent once on a local repo dir.")
    parser.add_argument("--repo", required=True, help="Path to the repository root (local)")
    args = parser.parse_args()

    result = run_workflow(args.repo)

    artifact = result.get("artifact_path") or "(not saved)"
    aggregates = result.get("aggregates") or {}
    metrics = result.get("metrics") or {}

    print("\n=== Code Repo Agent MVP Run ===")
    print(f"Artifact: {artifact}")
    if aggregates:
        print("Scores:")
        print(json.dumps(aggregates, indent=2))
    else:
        print("Scores: (none)")

    print(f"Metrics computed: {len(metrics) if isinstance(metrics, dict) else 0}")
    if isinstance(metrics, dict) and metrics:
        preview_ids = list(metrics.keys())[:8]
        print(f"Preview: {', '.join(preview_ids)}")

if __name__ == "__main__":
    main()