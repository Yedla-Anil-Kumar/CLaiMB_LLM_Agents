# workflows/monitor_workflow.py
from __future__ import annotations
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from agent_layer.registry import LEVEL0, LEVEL1_DEPS, CATEGORIES
from agent_layer.tool_loader import load_function
import os, json, time

# Known metrics (strict allow-list)
KNOWN_METRICS = (
    set(LEVEL0)
    | set(LEVEL1_DEPS.keys())
    | {m for cat in CATEGORIES.values() for m in (cat.get("metrics", {}) or {}).keys()}
)

def setup(config: Dict[str, Any]) -> Dict[str, Any]:
    return config or {}

def ingest(context: Dict[str, Any]) -> Dict[str, Any]:
    return context or {}

def _ctx_for(metric_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    # 1) exact dotted id
    c = context.get(metric_id, {})
    # 2) legacy underscore key (single pass) → dotted
    if not c:
        legacy = metric_id.replace(".", "_")
        c = context.get(legacy, {}) or {}
    # 3) wrap raw dict as {"params": ...}
    if isinstance(c, dict) and c and "params" not in c:
        return {"params": c}
    return c

def run_parallel(context: Dict[str, Any], metrics: List[str], max_workers: int = 8) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not metrics:
        return out

    def _run(metric_id: str):
        fn = load_function(metric_id)   # dotted id end-to-end
        return metric_id, fn(_ctx_for(metric_id, context))

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run, m): m for m in metrics}
        for fut in as_completed(futures):
            m = futures[fut]
            try:
                name, res = fut.result()
                out[name] = res
            except Exception as e:
                out[m] = {"metric_id": m, "score": 0.0, "rationale": f"runner exception: {e}"}
    return out

def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(w for w in weights.values() if isinstance(w, (int, float)))
    if total <= 0:
        n = len(weights) or 1
        return {k: 1.0 / n for k in weights}
    return {k: float(w) / total for k, w in weights.items()}

def _score_of(v: Any):
    return v.get("score") if isinstance(v, dict) else None

def aggregate(results: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    cfg = config or {}

    # Allow runtime overrides but keep base structure
    cat_cfg = {k: dict(v) for k, v in CATEGORIES.items()}
    if "category_weights" in cfg:
        for c, w in cfg["category_weights"].items():
            if c in cat_cfg:
                cat_cfg[c]["weight"] = w
    if "metric_weights" in cfg:
        for c, mws in cfg["metric_weights"].items():
            if c in cat_cfg and isinstance(mws, dict):
                cat_cfg[c]["metrics"] = {**cat_cfg[c].get("metrics", {}), **mws}

    cat_w_norm = _normalize({c: meta.get("weight", 0.0) for c, meta in cat_cfg.items()})
    breakdown, category_scores = [], {}
    overall_acc = overall_used = 0.0

    for c, meta in cat_cfg.items():
        mw = meta.get("metrics", {}) or {}
        mw_norm = _normalize(mw) if mw else {}
        parts, acc, used = [], 0.0, 0.0
        for m, w in mw_norm.items():
            sc = _score_of(results.get(m))
            parts.append({"metric": m, "weight": w, "score": sc})
            if isinstance(sc, (int, float)):
                acc += w * sc
                used += w
        cat_score = (acc / used) if used > 0 else None
        category_scores[c] = cat_score
        cw = cat_w_norm.get(c, 0.0)
        breakdown.append({"name": c, "weight": cw, "effective_weight_sum": used, "metrics": parts})
        if isinstance(cat_score, (int, float)) and cw > 0:
            overall_acc += cw * cat_score
            overall_used += cw

    overall_score = (overall_acc / overall_used) if overall_used > 0 else None
    simple_scores = [v.get("score") for v in results.values()
                     if isinstance(v, dict) and isinstance(v.get("score"), (int, float))]
    simple_avg = (sum(simple_scores) / len(simple_scores)) if simple_scores else None

    return {
        "overall_score": overall_score,
        "category_scores": category_scores,
        "breakdown": breakdown,
        "simple_average_debug": simple_avg,
        "count_metrics": len(results),
        "scored_metrics": len(simple_scores),
    }

def report(results: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
    return {"metrics": results, "summary": summary}

def _save_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run_workflow(config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    cfg = setup(config)
    ctx = ingest(context)

    # # Strict, single flow: only run metrics that have inputs
    # present_dotted = set(ctx.keys()) | {k.replace("_", ".") for k in ctx.keys()}
    # planned = sorted(m for m in KNOWN_METRICS if m in present_dotted)

    planned = sorted(m for m in KNOWN_METRICS if m in ctx)

    print("[orchestrator] metrics to run (inputs present only):", planned)

    # Single-stage execution (no separate L0/L1; no implicit deps)
    results = run_parallel(ctx, planned, max_workers=int(cfg.get("max_workers", 8)))

    # Aggregate + save
    summ = aggregate(results, cfg)
    final = report(results, summ)

    output_path = cfg.get("output_path")
    save_dir = cfg.get("save_dir") or "./runs"
    if output_path:
        _save_json(output_path, final)
    else:
        ts = int(time.time())
        os.makedirs(save_dir, exist_ok=True)
        _save_json(os.path.join(save_dir, f"run-{ts}.json"), final)

    return final
