# mvp/run_once.py
from __future__ import annotations
import os
import sys
from pathlib import Path
from dotenv import load_dotenv   # ✅ NEW

# Ensure repo root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflows.bi_tracker_workflow import run_workflow  # noqa: E402
from data_collection_agents.bi_tracker_agent.logging_utils import setup_logger  # noqa: E402


def main() -> None:
    # ✅ Load env file first
    load_dotenv()
    setup_logger("logs/agent_layer.log", level="INFO", serialize=False)

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment (.env). Please check your .env file.")
        return

    res = run_workflow()
    print("\n=== BI Tracker MVP Run ===")
    print(f"Artifact: {res.get('artifact_path')}")
    print("Scores:", res.get("scores"))
    print(f"Metrics computed: {res.get('count')}")


if __name__ == "__main__":
    main()