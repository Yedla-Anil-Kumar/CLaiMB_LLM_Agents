# scripts/run_enterprise_agent.py
#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from enterprise_systems_agent.canonical import (  # noqa: E402
    EnterpriseInputs,
)
from enterprise_systems_agent.orchestrator import (  # noqa: E402
    EnterpriseOrchestrator,
)
from enterprise_systems_agent.logging_utils import setup_logger # noqa: E402

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Enterprise Systems agent on JSON input(s).")
    p.add_argument("--inputs", default="data/sample_inputs", help="File or directory of JSON.")
    p.add_argument("--out", default="data/aggregate_results.json", help="Aggregate output path.")
    p.add_argument("--per-input-dir", default="data/Output", help="Where to write per-input JSONs.")
    p.add_argument("--model", default=os.getenv("OPENAI_MODEL","gpt-4o-mini"))
    p.add_argument("--temperature", type=float, default=0.0)
    return p.parse_args()

def iter_json(path: Path):
    if path.is_file():
        yield path
        return
    for p in sorted(path.glob("*.json")):
        if p.is_file():
            yield p

def main() -> None:
    load_dotenv()
    setup_logger("logs/enterprise_systems.log", level="INFO", serialize=False)
    args = parse_args()

    inputs_path = Path(args.inputs).resolve()
    out_path = Path(args.out).resolve()
    per_dir = Path(args.per_input_dir).resolve()
    per_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    orch = EnterpriseOrchestrator(model=args.model, temperature=args.temperature)

    aggregate = []
    for f in iter_json(inputs_path):
        name = f.stem
        payload = json.loads(f.read_text(encoding="utf-8"))
        ent = EnterpriseInputs.from_dict(payload)
        result = orch.analyze_inputs(ent)

        per_json = json.dumps(result, indent=2, ensure_ascii=False)
        (per_dir / f"{name}.json").write_text(per_json, encoding="utf-8")

        aggregate.append(result)

        print(f"✅ {name}")
        # print(json.dumps(result, indent=2, ensure_ascii=False))

    out_path.write_text(json.dumps(aggregate, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"🧾 Aggregate → {out_path}")

if __name__ == "__main__":
    main()