# agent_layer/orchestrator_mlops.py
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_core.runnables import RunnableParallel

# sys.path so we can import backbone packages when called as module
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_layer.registry_mlops import LEVEL0, LEVEL1_DEPS, CATEGORIES  # noqa: E402
from agent_layer.registry_mlops import BAND_TO_SCORE                     # noqa: E402
from agent_layer.router_mlops import route                               # noqa: E402

def _now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

def _aggregate(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    # per-category weighted averages of score_0to100
    cat_scores: Dict[str, float] = {}
    for cat, cfg in CATEGORIES.items():
        total = 0.0
        for mid, w in cfg["metrics"].items():
            v = results.get(mid, {}).get("score_0to100")
            if isinstance(v, (int, float)):
                total += w * float(v)
        cat_scores[cat] = round(total, 2)
    overall = round(sum(CATEGORIES[c]["weight"] * cat_scores.get(c, 0.0) for c in CATEGORIES), 2)
    return {"categories": cat_scores, "overall": overall}

def run(snapshot: Dict[str, Any], *, out_dir: Path = Path("runs_mlop_mvp")) -> Dict[str, Any]:
    load_dotenv()
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Level-0 in parallel ----
    l0_tools = {mid: route(mid) for mid in LEVEL0}
    parallel = RunnableParallel(**{mid: (lambda s, m=mid: l0_tools[m](s)) for mid in LEVEL0})
    l0_res: Dict[str, Dict[str, Any]] = parallel.invoke(snapshot)

    # ---- Level-1 sequential (after parents) ----
    results = dict(l0_res)
    for child, parents in LEVEL1_DEPS.items():
        if not all(p in results for p in parents):
            results[child] = {"metric_id": child, "band": "E", "score_0to100": BAND_TO_SCORE["E"],
                              "rationale": f"Missing parents: {parents}"}
            continue
        child_fn = route(child)
        results[child] = child_fn(snapshot)

    # ---- Aggregation & persist ----
    aggregates = _aggregate(results)
    run_id = f"mlops-{_now_id()}"
    artifact = {
        "run_id": run_id,
        "inputs_present": sorted([k for k, v in snapshot.items() if v]),
        "metrics": results,
        "aggregates": aggregates,
    }
    out_path = out_dir / f"{run_id}.json"
    out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return {"artifact": str(out_path), "aggregates": aggregates, "results": results}