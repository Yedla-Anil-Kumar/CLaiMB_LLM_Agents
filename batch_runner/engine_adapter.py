# batch_runner/engine_adapter.py
import os, json
from pathlib import Path
from typing import Dict, Any
from cloud_infra_agent.config import Input_File_For_Metric_map
from workflows.monitor_workflow import run_workflow


def _load_metric_files_via_map(batch_dir: str) -> Dict[str, Any]:
    """
    Load inputs using the explicit Input_File_For_Metric_map.
    Produces context keyed by **dotted** metric_id: {"params": <json>}.
    """
    ctx: Dict[str, Any] = {}
    loaded, missing = [], []

    # 1) Load everything listed in the map (authoritative)
    for metric_id, fname in Input_File_For_Metric_map.items():
        path = os.path.join(batch_dir, fname)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                ctx[metric_id] = {"params": data}
                loaded.append((metric_id, fname))
            except Exception as e:
                print(f"[engine_adapter] WARN: failed to load {fname} for {metric_id}: {e}")
        else:
            missing.append((metric_id, fname))

    if missing:
        miss_pretty = ", ".join([f"{m}→{f}" for m, f in missing])
        print(f"[engine_adapter] Missing mapped files (ok if intentional): {miss_pretty}")

    print("[engine_adapter] context keys:", ", ".join(sorted(ctx.keys())))
    return ctx

def run_engine(batch_dir: str, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    payload = {
        "config": {
            "save_dir": output_dir,
            "output_path": str(Path(output_dir) / "result.json"),
        },
        "context": _load_metric_files_via_map(batch_dir),
    }
    try:
        final = run_workflow(payload["config"], payload["context"]) or {}
    except Exception as e:
        print(f"[engine_adapter] ERROR: run_workflow failed: {e}")
        final = {"error": f"engine failure: {e}", "echo": {"count_inputs": len(payload['context'])}}

    out_path = Path(output_dir) / "result.json"
    try:
        out_path.write_text(json.dumps(final, indent=2), encoding="utf-8")
        print(f"[engine_adapter] Wrote {out_path}")
        return 0
    except Exception as e:
        print(f"[engine_adapter] ERROR writing result.json: {e}")
        return 2
