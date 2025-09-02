# agent_layer/orchestrator.py
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_core.runnables import RunnableParallel
from .registry import REGISTRY, CATEGORY_WEIGHTS
from .router import route

def _now_run_id() -> str:
    return time.strftime("bi-tracker-%Y%m%d-%H%M%S")

def _layers() -> Tuple[List[str], List[str]]:
    l0 = [mid for mid, meta in REGISTRY.items() if not meta.get("depends_on")]
    l1 = [mid for mid, meta in REGISTRY.items() if meta.get("depends_on")]
    return l0, l1

def _aggregate(metrics: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    # Average bands per category, then 50/50 overall
    cats: Dict[str, List[float]] = {}
    for mid, obj in metrics.items():
        meta = REGISTRY.get(mid, {})
        cat = meta.get("category", "business_integration")
        band = obj.get("band", obj.get("score", 3))
        try:
            band = max(1, min(5, float(band)))
        except Exception:
            band = 3.0
        cats.setdefault(cat, []).append(float(band))

    bi = round(sum(cats.get("business_integration", []) or [0]) / max(1, len(cats.get("business_integration", []))), 2) \
         if cats.get("business_integration") else 0.0
    dm = round(sum(cats.get("decision_making", []) or [0]) / max(1, len(cats.get("decision_making", []))), 2) \
         if cats.get("decision_making") else 0.0

    overall = round(
        CATEGORY_WEIGHTS.get("business_integration", 0.5) * bi +
        CATEGORY_WEIGHTS.get("decision_making", 0.5) * dm,
        2
    )
    return {"business_integration": bi, "decision_making": dm, "overall_score": overall}

def run(snapshot: Dict[str, Any], out_dir: Path | None = None) -> Dict[str, Any]:
    l0, l1 = _layers()

    # ---- Level 0: parallel
    parallel = RunnableParallel(**{mid: route(mid) for mid in l0})
    l0_out: Dict[str, Dict[str, Any]] = parallel.invoke(snapshot)

    # ---- Level 1: sequential (deps are gating only; prompts remain uniform)
    l1_out: Dict[str, Dict[str, Any]] = {}
    for mid in l1:
        
        res = route(mid).invoke(snapshot)
        l1_out[mid] = res

    metrics = {**l0_out, **l1_out}
    scores = _aggregate(metrics)
    run_id = _now_run_id()

    result = {
        "agent": "bi_tracker_mvp",
        "run_id": run_id,
        "scores": scores,
        "metrics": metrics,
        "count": len(metrics),
    }

    # Persist
    out_dir = out_dir or Path("runs_bi_mvp")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{run_id}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    result["artifact_path"] = str(out_path)
    return result