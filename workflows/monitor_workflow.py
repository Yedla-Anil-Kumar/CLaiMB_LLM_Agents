# # workflows/monitor_workflow.py
# from __future__ import annotations
# from typing import Dict, Any, List
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from agent_layer.registry import LEVEL0, LEVEL1_DEPS, CATEGORIES
# from agent_layer.tool_loader import load_function
# import os, json, time

# # Known metrics (strict allow-list)
# KNOWN_METRICS = (
#     set(LEVEL0)
#     | set(LEVEL1_DEPS.keys())
#     | {m for cat in CATEGORIES.values() for m in (cat.get("metrics", {}) or {}).keys()}
# )

# def setup(config: Dict[str, Any]) -> Dict[str, Any]:
#     return config or {}

# def ingest(context: Dict[str, Any]) -> Dict[str, Any]:
#     return context or {}

# def _ctx_for(metric_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
#     # 1) exact dotted id
#     c = context.get(metric_id, {})
#     # 2) legacy underscore key (single pass) → dotted
#     if not c:
#         legacy = metric_id.replace(".", "_")
#         c = context.get(legacy, {}) or {}
#     # 3) wrap raw dict as {"params": ...}
#     if isinstance(c, dict) and c and "params" not in c:
#         return {"params": c}
#     return c

# def run_parallel(context: Dict[str, Any], metrics: List[str], max_workers: int = 8) -> Dict[str, Any]:
#     out: Dict[str, Any] = {}
#     if not metrics:
#         return out

#     def _run(metric_id: str):
#         fn = load_function(metric_id)   # dotted id end-to-end
#         return metric_id, fn(_ctx_for(metric_id, context))

#     with ThreadPoolExecutor(max_workers=max_workers) as pool:
#         futures = {pool.submit(_run, m): m for m in metrics}
#         for fut in as_completed(futures):
#             m = futures[fut]
#             try:
#                 name, res = fut.result()
#                 out[name] = res
#             except Exception as e:
#                 out[m] = {"metric_id": m, "score": 0.0, "rationale": f"runner exception: {e}"}
#     return out

# def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
#     total = sum(w for w in weights.values() if isinstance(w, (int, float)))
#     if total <= 0:
#         n = len(weights) or 1
#         return {k: 1.0 / n for k in weights}
#     return {k: float(w) / total for k, w in weights.items()}

# def _score_of(v: Any):
#     return v.get("score") if isinstance(v, dict) else None

# def aggregate(results: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
#     cfg = config or {}

#     # Allow runtime overrides but keep base structure
#     cat_cfg = {k: dict(v) for k, v in CATEGORIES.items()}
#     if "category_weights" in cfg:
#         for c, w in cfg["category_weights"].items():
#             if c in cat_cfg:
#                 cat_cfg[c]["weight"] = w
#     if "metric_weights" in cfg:
#         for c, mws in cfg["metric_weights"].items():
#             if c in cat_cfg and isinstance(mws, dict):
#                 cat_cfg[c]["metrics"] = {**cat_cfg[c].get("metrics", {}), **mws}

#     cat_w_norm = _normalize({c: meta.get("weight", 0.0) for c, meta in cat_cfg.items()})
#     breakdown, category_scores = [], {}
#     overall_acc = overall_used = 0.0

#     for c, meta in cat_cfg.items():
#         mw = meta.get("metrics", {}) or {}
#         mw_norm = _normalize(mw) if mw else {}
#         parts, acc, used = [], 0.0, 0.0
#         for m, w in mw_norm.items():
#             sc = _score_of(results.get(m))
#             parts.append({"metric": m, "weight": w, "score": sc})
#             if isinstance(sc, (int, float)):
#                 acc += w * sc
#                 used += w
#         cat_score = (acc / used) if used > 0 else None
#         category_scores[c] = cat_score
#         cw = cat_w_norm.get(c, 0.0)
#         breakdown.append({"name": c, "weight": cw, "effective_weight_sum": used, "metrics": parts})
#         if isinstance(cat_score, (int, float)) and cw > 0:
#             overall_acc += cw * cat_score
#             overall_used += cw

#     overall_score = (overall_acc / overall_used) if overall_used > 0 else None
#     simple_scores = [v.get("score") for v in results.values()
#                      if isinstance(v, dict) and isinstance(v.get("score"), (int, float))]
#     simple_avg = (sum(simple_scores) / len(simple_scores)) if simple_scores else None

#     return {
#         "overall_score": overall_score,
#         "category_scores": category_scores,
#         "breakdown": breakdown,
#         "simple_average_debug": simple_avg,
#         "count_metrics": len(results),
#         "scored_metrics": len(simple_scores),
#     }

# def report(results: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
#     return {"metrics": results, "summary": summary}

# def _save_json(path: str, data: Dict[str, Any]) -> None:
#     os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)

# def run_workflow(config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
#     cfg = setup(config)
#     ctx = ingest(context)

#     # # Strict, single flow: only run metrics that have inputs
#     # present_dotted = set(ctx.keys()) | {k.replace("_", ".") for k in ctx.keys()}
#     # planned = sorted(m for m in KNOWN_METRICS if m in present_dotted)

#     planned = sorted(m for m in KNOWN_METRICS if m in ctx)

#     print("[orchestrator] metrics to run (inputs present only):", planned)

#     # Single-stage execution (no separate L0/L1; no implicit deps)
#     results = run_parallel(ctx, planned, max_workers=int(cfg.get("max_workers", 8)))

#     # Aggregate + save
#     summ = aggregate(results, cfg)
#     final = report(results, summ)

#     output_path = cfg.get("output_path")
#     save_dir = cfg.get("save_dir") or "./runs"
#     if output_path:
#         _save_json(output_path, final)
#     else:
#         ts = int(time.time())
#         os.makedirs(save_dir, exist_ok=True)
#         _save_json(os.path.join(save_dir, f"run-{ts}.json"), final)

#     return final


# # workflows/monitor_workflow.py
# from __future__ import annotations
# from typing import Dict, Any, List
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from agent_layer.registry import LEVEL0, LEVEL1_DEPS, CATEGORIES
# from agent_layer.tool_loader import load_function
# import os, json, time

# # Known metrics (strict allow-list)
# KNOWN_METRICS = (
#     set(LEVEL0)
#     | set(LEVEL1_DEPS.keys())
#     | {m for cat in CATEGORIES.values() for m in (cat.get("metrics", {}) or {}).keys()}
# )

# def setup(config: Dict[str, Any]) -> Dict[str, Any]:
#     return config or {}

# def ingest(context: Dict[str, Any]) -> Dict[str, Any]:
#     return context or {}

# def _ctx_for(metric_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
#     c = context.get(metric_id, {})
#     if isinstance(c, dict) and c and "params" not in c:
#         return {"params": c}
#     return c

# # ---------- NEW: helpers for DAG-based execution ----------

# # L0 = everything listed in LEVEL0 that is NOT explicitly a Level-1 metric
# L0_PARALLEL: List[str] = [m for m in LEVEL0 if m not in LEVEL1_DEPS]
# # All L1 candidates come from the LEVEL1_DEPS keys
# L1_ALL: List[str] = sorted(LEVEL1_DEPS.keys())

# def _present_in_ctx(metric_id: str, ctx: Dict[str, Any]) -> bool:
#     """Treat exact key and single-underscore legacy as present."""
#     return (metric_id in ctx)

# def _call_metric(metric_id: str, ctx_for_metric: Dict[str, Any]) -> dict:
#     """Load and run a metric with the single-dict calling convention."""
#     fn = load_function(metric_id)  # dotted id end-to-end
#     out = fn(ctx_for_metric) or {}
#     out.setdefault("metric_id", metric_id)
#     return out

# def _run_parallel_stable(metric_ctx_map: Dict[str, Dict[str, Any]], max_workers: int) -> Dict[str, Any]:
#     """
#     Run a set of metrics in parallel.
#     Deterministic behavior via sorted submission and assembly keyed by metric_id.
#     """
#     results: Dict[str, Any] = {}
#     if not metric_ctx_map:
#         return results
#     ordered = sorted(metric_ctx_map.items(), key=lambda kv: kv[0])
#     with ThreadPoolExecutor(max_workers=max_workers) as pool:
#         futs = {pool.submit(_call_metric, m, c): m for m, c in ordered}
#         for fut in as_completed(futs):
#             m = futs[fut]
#             try:
#                 results[m] = fut.result()
#             except Exception as e:
#                 results[m] = {"metric_id": m, "score": 0.0, "rationale": f"runner exception: {e}"}
#     return results

# # ---------- unchanged: aggregation helpers ----------

# def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
#     total = sum(w for w in weights.values() if isinstance(w, (int, float)))
#     if total <= 0:
#         n = len(weights) or 1
#         return {k: 1.0 / n for k in weights}
#     return {k: float(w) / total for k, w in weights.items()}

# def _score_of(v: Any):
#     return v.get("score") if isinstance(v, dict) else None

# def aggregate(results: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
#     cfg = config or {}

#     # Allow runtime overrides but keep base structure
#     cat_cfg = {k: dict(v) for k, v in CATEGORIES.items()}
#     if "category_weights" in cfg:
#         for c, w in cfg["category_weights"].items():
#             if c in cat_cfg:
#                 cat_cfg[c]["weight"] = w
#     if "metric_weights" in cfg:
#         for c, mws in cfg["metric_weights"].items():
#             if c in cat_cfg and isinstance(mws, dict):
#                 cat_cfg[c]["metrics"] = {**cat_cfg[c].get("metrics", {}), **mws}

#     cat_w_norm = _normalize({c: meta.get("weight", 0.0) for c, meta in cat_cfg.items()})
#     breakdown, category_scores = [], {}
#     overall_acc = overall_used = 0.0

#     for c, meta in cat_cfg.items():
#         mw = meta.get("metrics", {}) or {}
#         mw_norm = _normalize(mw) if mw else {}
#         parts, acc, used = [], 0.0, 0.0
#         for m, w in mw_norm.items():
#             sc = _score_of(results.get(m))
#             parts.append({"metric": m, "weight": w, "score": sc})
#             if isinstance(sc, (int, float)):
#                 acc += w * sc
#                 used += w
#         cat_score = (acc / used) if used > 0 else None
#         category_scores[c] = cat_score
#         cw = cat_w_norm.get(c, 0.0)
#         breakdown.append({"name": c, "weight": cw, "effective_weight_sum": used, "metrics": parts})
#         if isinstance(cat_score, (int, float)) and cw > 0:
#             overall_acc += cw * cat_score
#             overall_used += cw

#     overall_score = (overall_acc / overall_used) if overall_used > 0 else None
#     simple_scores = [v.get("score") for v in results.values()
#                      if isinstance(v, dict) and isinstance(v.get("score"), (int, float))]
#     simple_avg = (sum(simple_scores) / len(simple_scores)) if simple_scores else None

#     return {
#         "overall_score": overall_score,
#         "category_scores": category_scores,
#         "breakdown": breakdown,
#         "simple_average_debug": simple_avg,
#         "count_metrics": len(results),
#         "scored_metrics": len(simple_scores),
#     }

# def report(results: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
#     return {"metrics": results, "summary": summary}

# def _save_json(path: str, data: Dict[str, Any]) -> None:
#     os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)

# # ---------- NEW: orchestrator respecting L0 parallel + L1 parallel waves ----------

# def run_workflow(config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
#     cfg = setup(config)
#     ctx = ingest(context)
#     max_workers = int(cfg.get("max_workers", 8))

#     # -------- Level 0: Parallel island --------
#     l0_planned = [m for m in L0_PARALLEL if _present_in_ctx(m, ctx)]
#     print("[orchestrator] L0 metrics (parallel):", l0_planned)

#     l0_ctx_map = {m: _ctx_for(m, ctx) for m in l0_planned}
#     results: Dict[str, Any] = _run_parallel_stable(l0_ctx_map, max_workers=max_workers)

#     # -------- Level 1: Parallel waves (deps → deps outputs injected) --------
#     remaining = {m for m in L1_ALL if _present_in_ctx(m, ctx)}
#     print("[orchestrator] L1 candidates:", sorted(remaining))

#     while remaining:
#         ready = [m for m in sorted(remaining) if all(d in results for d in LEVEL1_DEPS.get(m, []))]
#         if not ready:
#             # deps missing for the remaining; record and break
#             for m in sorted(remaining):
#                 missing = [d for d in LEVEL1_DEPS.get(m, []) if d not in results]
#                 results[m] = {
#                     "metric_id": m,
#                     "score": 0.0,
#                     "rationale": f"skipped: unsatisfied dependencies {missing}",
#                 }
#             break

#         print("[orchestrator] L1 wave (parallel):", ready)

#         wave_ctx_map: Dict[str, Dict[str, Any]] = {}
#         for m in ready:
#             base = _ctx_for(m, ctx)  # preserves {"params": ...} wrapping
#             deps_payload = {d: results[d] for d in LEVEL1_DEPS.get(m, [])}
#             merged = dict(base)
#             merged["deps"] = deps_payload
#             wave_ctx_map[m] = merged

#         wave_results = _run_parallel_stable(wave_ctx_map, max_workers=max_workers)
#         results.update(wave_results)
#         remaining.difference_update(ready)

#     # -------- Aggregate + Save (unchanged) --------
#     summ = aggregate(results, cfg)
#     final = report(results, summ)

#     output_path = cfg.get("output_path")
#     save_dir = cfg.get("save_dir") or "./runs"
#     if output_path:
#         _save_json(output_path, final)
#     else:
#         ts = int(time.time())
#         os.makedirs(save_dir, exist_ok=True)
#         _save_json(os.path.join(save_dir, f"run-{ts}.json"), final)

#     return final


# # workflows/monitor_workflow.py
# from __future__ import annotations
# from typing import Dict, Any, List
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import os, json, time

# from loguru import logger
# from cloud_infra_agent.logging_utils import timed

# from agent_layer.registry import LEVEL0, LEVEL1_DEPS, CATEGORIES
# from agent_layer.tool_loader import load_function

# # Known metrics (strict allow-list)
# KNOWN_METRICS = (
#     set(LEVEL0)
#     | set(LEVEL1_DEPS.keys())
#     | {m for cat in CATEGORIES.values() for m in (cat.get("metrics", {}) or {}).keys()}
# )

# def setup(config: Dict[str, Any]) -> Dict[str, Any]:
#     return config or {}

# def ingest(context: Dict[str, Any]) -> Dict[str, Any]:
#     return context or {}

# def _ctx_for(metric_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
#     c = context.get(metric_id, {})
#     if isinstance(c, dict) and c and "params" not in c:
#         return {"params": c}
#     return c

# # ---------- NEW: helpers for DAG-based execution ----------
# # L0 = everything listed in LEVEL0 that is NOT explicitly a Level-1 metric
# L0_PARALLEL: List[str] = [m for m in LEVEL0 if m not in LEVEL1_DEPS]
# # All L1 candidates come from the LEVEL1_DEPS keys
# L1_ALL: List[str] = sorted(LEVEL1_DEPS.keys())

# def _present_in_ctx(metric_id: str, ctx: Dict[str, Any]) -> bool:
#     """Treat exact key as present."""
#     return (metric_id in ctx)

# def _call_metric(metric_id: str, ctx_for_metric: Dict[str, Any]) -> dict:
#     """
#     Load and run a metric with the single-dict calling convention.
#     Adds nested timing + robust error capture.
#     """
#     fn = load_function(metric_id)  # dotted id
#     with timed(f"metric.{metric_id}"):
#         try:
#             with timed("LLM.call"):
#                 out = fn(ctx_for_metric) or {}
#         except Exception as e:
#             logger.exception(f"[runner] Exception in metric '{metric_id}': {e}")
#             return {
#                 "metric_id": metric_id,
#                 "score": 0.0,
#                 "rationale": f"runner exception: {e}",
#                 "gaps": [],
#                 "evidence": {},
#             }

#     # Normalize and log highlights for quick skim
#     out.setdefault("metric_id", metric_id)
#     score = out.get("score")
#     rationale = (out.get("rationale") or "").strip().replace("\n", " ")
#     if len(rationale) > 220:
#         rationale = rationale[:217] + "..."
#     gaps = out.get("gaps") or []
#     flags = out.get("flags") or out.get("evidence", {}).get("flags")
#     if isinstance(flags, dict):
#         flags = list(flags.keys())
#     if flags and not isinstance(flags, list):
#         flags = [str(flags)]

#     logger.info(f"[{metric_id}] score={score} | rationale={rationale or '—'}")
#     if flags:
#         logger.info(f"[{metric_id}] flags={flags}")
#     if gaps:
#         logger.info(f"[{metric_id}] gaps={gaps}")

#     return out

# def _run_parallel_stable(metric_ctx_map: Dict[str, Dict[str, Any]], max_workers: int) -> Dict[str, Any]:
#     """
#     Run a set of metrics in parallel.
#     Deterministic submission (sorted) and keyed assembly.
#     """
#     results: Dict[str, Any] = {}
#     if not metric_ctx_map:
#         return results

#     ordered = sorted(metric_ctx_map.items(), key=lambda kv: kv[0])
#     with ThreadPoolExecutor(max_workers=max_workers) as pool:
#         futs = {pool.submit(_call_metric, m, c): m for m, c in ordered}
#         for fut in as_completed(futs):
#             m = futs[fut]
#             try:
#                 results[m] = fut.result()
#             except Exception as e:
#                 logger.exception(f"[runner] Exception collecting future for '{m}': {e}")
#                 results[m] = {"metric_id": m, "score": 0.0, "rationale": f"runner exception (future): {e}"}
#     return results

# # ---------- unchanged: aggregation helpers ----------
# def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
#     total = sum(w for w in weights.values() if isinstance(w, (int, float)))
#     if total <= 0:
#         n = len(weights) or 1
#         return {k: 1.0 / n for k in weights}
#     return {k: float(w) / total for k, w in weights.items()}

# def _score_of(v: Any):
#     return v.get("score") if isinstance(v, dict) else None

# def aggregate(results: Dict[str, Any], config: Dict[str, Any] | None = None) -> Dict[str, Any]:
#     cfg = config or {}

#     # Allow runtime overrides but keep base structure
#     cat_cfg = {k: dict(v) for k, v in CATEGORIES.items()}
#     if "category_weights" in cfg:
#         for c, w in cfg["category_weights"].items():
#             if c in cat_cfg:
#                 cat_cfg[c]["weight"] = w
#     if "metric_weights" in cfg:
#         for c, mws in cfg["metric_weights"].items():
#             if c in cat_cfg and isinstance(mws, dict):
#                 cat_cfg[c]["metrics"] = {**cat_cfg[c].get("metrics", {}), **mws}

#     cat_w_norm = _normalize({c: meta.get("weight", 0.0) for c, meta in cat_cfg.items()})
#     breakdown, category_scores = [], {}
#     overall_acc = overall_used = 0.0

#     for c, meta in cat_cfg.items():
#         mw = meta.get("metrics", {}) or {}
#         mw_norm = _normalize(mw) if mw else {}
#         parts, acc, used = [], 0.0, 0.0
#         for m, w in mw_norm.items():
#             sc = _score_of(results.get(m))
#             parts.append({"metric": m, "weight": w, "score": sc})
#             if isinstance(sc, (int, float)):
#                 acc += w * sc
#                 used += w
#         cat_score = (acc / used) if used > 0 else None
#         category_scores[c] = cat_score
#         cw = cat_w_norm.get(c, 0.0)
#         breakdown.append({"name": c, "weight": cw, "effective_weight_sum": used, "metrics": parts})
#         if isinstance(cat_score, (int, float)) and cw > 0:
#             overall_acc += cw * cat_score
#             overall_used += cw

#     overall_score = (overall_acc / overall_used) if overall_used > 0 else None
#     simple_scores = [v.get("score") for v in results.values()
#                      if isinstance(v, dict) and isinstance(v.get("score"), (int, float))]
#     simple_avg = (sum(simple_scores) / len(simple_scores)) if simple_scores else None

#     return {
#         "overall_score": overall_score,
#         "category_scores": category_scores,
#         "breakdown": breakdown,
#         "simple_average_debug": simple_avg,
#         "count_metrics": len(results),
#         "scored_metrics": len(simple_scores),
#     }

# def report(results: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
#     return {"metrics": results, "summary": summary}

# def _save_json(path: str, data: Dict[str, Any]) -> None:
#     os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
#     with open(path, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=2, ensure_ascii=False)

# # ---------- NEW: orchestrator respecting L0 parallel + L1 parallel waves ----------
# def run_workflow(config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
#     with timed("setup"):
#         cfg = setup(config)
#     with timed("ingest"):
#         ctx = ingest(context)

#     max_workers = int(cfg.get("max_workers", 8))

#     # -------- Level 0: Parallel island --------
#     l0_planned = [m for m in L0_PARALLEL if _present_in_ctx(m, ctx)]
#     logger.info(f"[orchestrator] L0 metrics (parallel): {l0_planned}")
#     l0_ctx_map = {m: _ctx_for(m, ctx) for m in l0_planned}

#     with timed("L0.parallel"):
#         results: Dict[str, Any] = _run_parallel_stable(l0_ctx_map, max_workers=max_workers)

#     # -------- Level 1: Parallel waves (deps → deps outputs injected) --------
#     remaining = {m for m in L1_ALL if _present_in_ctx(m, ctx)}
#     logger.info(f"[orchestrator] L1 candidates: {sorted(remaining)}")

#     wave_index = 0
#     while remaining:
#         ready = [m for m in sorted(remaining) if all(d in results for d in LEVEL1_DEPS.get(m, []))]
#         if not ready:
#             # deps missing for the remaining; record and break
#             for m in sorted(remaining):
#                 missing = [d for d in LEVEL1_DEPS.get(m, []) if d not in results]
#                 logger.warning(f"[orchestrator] Skipping '{m}' due to missing deps {missing}")
#                 results[m] = {
#                     "metric_id": m,
#                     "score": 0.0,
#                     "rationale": f"skipped: unsatisfied dependencies {missing}",
#                 }
#             break

#         logger.info(f"[orchestrator] L1 wave#{wave_index} (parallel): {ready}")
#         wave_ctx_map: Dict[str, Dict[str, Any]] = {}
#         for m in ready:
#             base = _ctx_for(m, ctx)  # preserves {"params": ...}
#             deps_payload = {d: results[d] for d in LEVEL1_DEPS.get(m, [])}
#             merged = dict(base)
#             merged["deps"] = deps_payload
#             wave_ctx_map[m] = merged

#         with timed(f"L1.wave#{wave_index}.parallel"):
#             wave_results = _run_parallel_stable(wave_ctx_map, max_workers=max_workers)
#         results.update(wave_results)
#         remaining.difference_update(ready)
#         wave_index += 1

#     # -------- Aggregate + Save --------
#     with timed("aggregate"):
#         summ = aggregate(results, cfg)
#     final = report(results, summ)

#     output_path = cfg.get("output_path")
#     save_dir = cfg.get("save_dir") or "./runs"
#     with timed("persist"):
#         if output_path:
#             _save_json(output_path, final)
#             logger.info(f"[orchestrator] Output saved to: {output_path}")
#         else:
#             ts = int(time.time())
#             os.makedirs(save_dir, exist_ok=True)
#             out = os.path.join(save_dir, f"run-{ts}.json")
#             _save_json(out, final)
#             logger.info(f"[orchestrator] Output saved to: {out}")

#     return final

# workflows/monitor_workflow.py
from __future__ import annotations
from typing import Dict, Any, List, Iterable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from textwrap import shorten
import os, json, time

from loguru import logger
from cloud_infra_agent.logging_utils import timed

from agent_layer.registry import LEVEL0, LEVEL1_DEPS, CATEGORIES
from agent_layer.tool_loader import load_function

# ---------------------------
# Helpers for formatting logs
# ---------------------------

def _short(s: str, width: int = 180) -> str:
    return shorten((s or "").replace("\n", " ").strip(), width=width, placeholder="...")

def _metric_line(m: dict) -> str:
    mid = m.get("metric_id", "?")
    score = m.get("score", "—")
    band = m.get("band") or (m.get("evidence") or {}).get("band")
    cat  = m.get("category") or (m.get("evidence") or {}).get("category")
    rat  = _short(m.get("rationale", ""))

    gaps = m.get("gaps") or []
    flags = m.get("flags") or (m.get("evidence") or {}).get("flags") or []
    if isinstance(flags, dict): flags = list(flags.keys())
    if flags and not isinstance(flags, list): flags = [str(flags)]

    band_s = f" | band={band}" if band is not None else ""
    cat_s  = f" | category={cat}" if cat else ""
    gf = f" | gaps={len(gaps)}" if gaps else ""
    ff = f" | flags={len(flags)}" if flags else ""
    return f"[{mid}] score={score}{band_s}{cat_s} | {rat}{gf}{ff}"

class debug_timed:
    """DEBUG-only timer that prints exactly like your target format."""
    def __init__(self, section: str):
        self.section = section
        self.t0 = 0.0
    def __enter__(self):
        self.t0 = time.perf_counter()
        logger.debug(f"▶️ start: {self.section}")
        return self
    def __exit__(self, exc_type, exc, tb):
        dur_ms = (time.perf_counter() - self.t0) * 1000.0
        # note the two spaces after colon to match example: "✅ done:  LLM.call ..."
        logger.debug(f"✅ done:  {self.section} ({dur_ms:.2f} ms)")

# ---------------------------
# Core setup / ingest
# ---------------------------

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
    c = context.get(metric_id, {})
    if isinstance(c, dict) and c and "params" not in c:
        return {"params": c}
    return c

# ---------- DAG-based execution ----------
# L0 = everything listed in LEVEL0 that is NOT explicitly a Level-1 metric
L0_PARALLEL: List[str] = [m for m in LEVEL0 if m not in LEVEL1_DEPS]
# All L1 candidates come from the LEVEL1_DEPS keys
L1_ALL: List[str] = sorted(LEVEL1_DEPS.keys())

def _present_in_ctx(metric_id: str, ctx: Dict[str, Any]) -> bool:
    """Treat exact key as present."""
    return (metric_id in ctx)

def _call_metric(metric_id: str, ctx_for_metric: Dict[str, Any]) -> dict:
    """Run a metric with the single-dict calling convention; add DEBUG LLM timing + INFO summary."""
    fn = load_function(metric_id)  # dotted id
    with timed(f"metric.{metric_id}"):
        try:
            with debug_timed("LLM.call"):
                out = fn(ctx_for_metric) or {}
        except Exception as e:
            logger.exception(f"[runner] Exception in metric '{metric_id}': {e}")
            return {
                "metric_id": metric_id,
                "score": 0.0,
                "rationale": f"runner exception: {e}",
                "gaps": [],
                "evidence": {},
            }

    out.setdefault("metric_id", metric_id)
    logger.info(_metric_line(out))
    return out

def _run_parallel_stable(metric_ctx_map: Dict[str, Dict[str, Any]], max_workers: int) -> Dict[str, Any]:
    """Run a set of metrics in parallel. Deterministic submission + keyed assembly."""
    results: Dict[str, Any] = {}
    if not metric_ctx_map:
        return results

    ordered = sorted(metric_ctx_map.items(), key=lambda kv: kv[0])
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {pool.submit(_call_metric, m, c): m for m, c in ordered}
        for fut in as_completed(futs):
            m = futs[fut]
            try:
                results[m] = fut.result()
            except Exception as e:
                logger.exception(f"[runner] Exception collecting future for '{m}': {e}")
                results[m] = {"metric_id": m, "score": 0.0, "rationale": f"runner exception (future): {e}"}
    return results

# ---------- aggregation helpers ----------
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

def _summarize_end(results: Dict[str, Any], summary: Dict[str, Any], out_path: str) -> None:
    # Top 5 lowest scores
    scored: List[Tuple[str, float]] = [
        (m, v.get("score")) for m, v in results.items()
        if isinstance(v, dict) and isinstance(v.get("score"), (int, float))
    ]
    scored.sort(key=lambda x: (x[1], x[0]))
    worst = scored[:5]

    cats = summary.get("category_scores", {}) or {}
    cats_line = ", ".join([
        f"{c}={cats[c]:.2f}" if isinstance(cats[c], (int, float)) else f"{c}=—"
        for c in sorted(cats.keys())
    ])

    overall = summary.get("overall_score")
    simple_avg = summary.get("simple_average_debug")

    def _fmt(v): return f"{v:.2f}" if isinstance(v, (int, float)) else "—"

    logger.info("🟩 RUN SUMMARY")
    logger.info(f"• overall={_fmt(overall)} | simple_avg={_fmt(simple_avg)}")
    logger.info(f"• categories: {cats_line or '—'}")
    if worst:
        worst_line = "; ".join([f"{m}={s:.1f}" for m, s in worst])
        logger.info(f"• top risks: {worst_line}")
    else:
        logger.info("• top risks: —")
    logger.info(f"• saved: {out_path}")

# ---------- Orchestrator (L0 parallel + L1 waves) ----------
def run_workflow(config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    with timed("setup"):
        cfg = setup(config)
    with timed("ingest"):
        ctx = ingest(context)

    # Header exactly in the order/wording you requested
    present = sorted(ctx.keys())
    logger.info(f"📦 context: {len(present)} inputs → {present}")
    logger.info("🟦 RUN START")
    run_id = cfg.get("run_id", "(auto)")
    max_workers = int(cfg.get("max_workers", 8))
    logger.info(f"• run_id={run_id} • max_workers={max_workers}")

    # -------- Level 0: Parallel island --------
    l0_planned = [m for m in L0_PARALLEL if _present_in_ctx(m, ctx)]
    logger.info(f"🔹 L0 parallel: {len(l0_planned)} metrics → {l0_planned}")
    l0_ctx_map = {m: _ctx_for(m, ctx) for m in l0_planned}

    with timed("L0.parallel"):
        results: Dict[str, Any] = _run_parallel_stable(l0_ctx_map, max_workers=max_workers)

    # -------- Level 1: Parallel waves (deps → deps outputs injected) --------
    remaining = {m for m in L1_ALL if _present_in_ctx(m, ctx)}
    logger.info(f"🔶 L1 candidates: {len(remaining)} → {sorted(remaining)}")

    wave_index = 0
    while remaining:
        ready = [m for m in sorted(remaining) if all(d in results for d in LEVEL1_DEPS.get(m, []))]
        if not ready:
            # deps missing for the remaining; record and break
            for m in sorted(remaining):
                missing = [d for d in LEVEL1_DEPS.get(m, []) if d not in results]
                logger.warning(f"⏭️  skip '{m}' (missing deps {missing})")
                results[m] = {
                    "metric_id": m,
                    "score": 0.0,
                    "rationale": f"skipped: unsatisfied dependencies {missing}",
                }
            break

        logger.info(f"🔸 L1 wave#{wave_index}: {len(ready)} → {ready}")
        wave_ctx_map: Dict[str, Dict[str, Any]] = {}
        for m in ready:
            base = _ctx_for(m, ctx)  # preserves {"params": ...}
            deps_payload = {d: results[d] for d in LEVEL1_DEPS.get(m, [])}
            merged = dict(base)
            merged["deps"] = deps_payload
            wave_ctx_map[m] = merged

        with timed(f"L1.wave#{wave_index}.parallel"):
            wave_results = _run_parallel_stable(wave_ctx_map, max_workers=max_workers)
        results.update(wave_results)
        remaining.difference_update(ready)
        wave_index += 1

    # -------- Aggregate + Save --------
    with timed("aggregate"):
        summ = aggregate(results, cfg)
    final = report(results, summ)

    output_path = cfg.get("output_path")
    save_dir = cfg.get("save_dir") or "./runs"
    with timed("persist"):
        if output_path:
            _save_json(output_path, final)
            out_path = output_path
        else:
            ts = int(time.time())
            os.makedirs(save_dir, exist_ok=True)
            out_path = os.path.join(save_dir, f"run-{ts}.json")
            _save_json(out_path, final)

    _summarize_end(final.get("metrics", {}), final.get("summary", {}), out_path)
    logger.info("🟪 RUN END")
    return final
