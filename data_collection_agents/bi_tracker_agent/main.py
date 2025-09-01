#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bi_tracker_agent.canonical import BIInputs  # noqa: E402
from bi_tracker_agent.orchestrator import BIOrchestrator  # noqa: E402
from bi_tracker_agent.logging_utils import setup_logger # noqa: E402

def main() -> None:
    load_dotenv()
    setup_logger("logs/bi_tracker.log", level="INFO", serialize=False)

    SAMPLES_DIR = Path("data/Sample_Inputs")
    OUTPUT_DIR  = Path("data/Outputs")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sample_files = sorted(SAMPLES_DIR.glob("*.json"))
    if not sample_files:
        raise RuntimeError(f"No JSON files found in {SAMPLES_DIR}")

    orch = BIOrchestrator(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.0")),
    )

    for sample in sample_files:
        payload = json.loads(sample.read_text(encoding="utf-8"))
        bi = BIInputs.from_dict(payload)
        result = orch.analyze_inputs(bi)
        out_file = OUTPUT_DIR / f"{sample.stem}_result.json"
        out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
