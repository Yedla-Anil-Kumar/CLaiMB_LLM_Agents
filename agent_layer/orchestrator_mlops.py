# agent_layer/orchestrator_mlops.py
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

from dotenv import load_dotenv
from langchain_core.runnables import RunnableParallel
from loguru import logger  # <-- add loguru

# import path bootstrap (if needed when run as module)
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_layer.registry_mlops import LEVEL0, LEVEL1_DEPS, CATEGORIES, BAND_TO_SCORE  # noqa: E402
from agent_layer.router_mlops import route # noqa: E402


class MLOpsOrchestrator:
    """
    Deterministic, multi-wave orchestrator for ML Ops agent.

    - One shared LLM contract (wrappers already enforce strict JSON).
    - Minimal snapshot passed through to each metric wrapper.
    - Waves computed from a simple DAG (LEVEL0 + LEVEL1_DEPS).
    - Per-category aggregation to an overall score (0..100).
    """

    def __init__(self, *, out_dir: Path | str = "runs_mlop_mvp", log_dir: Path | str = "logs/ml_ops") -> None:
        load_dotenv()
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    # ---------- public API ----------
    def run(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all metrics in topological waves, aggregate, and write an artifact.
        Returns:
          {
            "run_id": <str>,
            "artifact_path": <str>,
            "log_path": <str>,          # <-- NEW
            "metrics": {...},
            "aggregates": {...}
          }
        """
        waves = self._compute_waves()
        results: Dict[str, Dict[str, Any]] = {}

        # create run_id and a per-run log sink
        run_id = self._now_id(prefix="mlops")
        run_log = (self.log_dir / f"{run_id}.log").resolve()
        run_sink_id = logger.add(
            run_log,
            level="INFO",
            rotation="5 MB",
            retention=10,
            compression="zip",
            enqueue=True,
        )
        logger.info(f"[{run_id}] Starting MLOps orchestrator run")

        try:
            # Execute waves in order; each wave runs in parallel
            for wave in waves:
                logger.info(f"[{run_id}] Executing wave with {len(wave)} metrics: {', '.join(wave)}")
                rp = RunnableParallel(**{mid: route(mid) for mid in wave})
                wave_out: Dict[str, Dict[str, Any]] = rp.invoke(snapshot)

                for mid, res in wave_out.items():
                    results[mid] = self._normalize(mid, res)

            # Patch any missing LEVEL1 nodes (unsatisfied deps → error band)
            for child, parents in LEVEL1_DEPS.items():
                if child not in results and all(p in results for p in parents):
                    results[child] = self._normalize(child, route(child).invoke(snapshot))
                elif child not in results:
                    results[child] = self._normalize(
                        child,
                        {
                            "band": "E",
                            "rationale": f"Missing parents: {sorted(parents)}",
                            "gaps": ["Resolve upstream dependencies before evaluating this metric."],
                        },
                    )

            aggregates = self._aggregate(results)
            artifact = {
                "run_id": run_id,
                "inputs_present": sorted([k for k, v in (snapshot or {}).items() if v]),
                "metrics": results,
                "aggregates": aggregates,
            }

            out_path = self.out_dir / f"{run_id}.json"
            out_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"[{run_id}] Finished. Artifact written: {out_path}")

            return {
                "run_id": run_id,
                "artifact_path": str(out_path),
                "log_path": str(run_log),       # <-- NEW
                "metrics": results,
                "aggregates": aggregates,
            }
        finally:
            # ensure we close the per-run sink so subsequent runs go to their own files
            logger.remove(run_sink_id)

    # ---------- helpers ----------
    @staticmethod
    def _now_id(prefix: str) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        return f"{prefix}-{ts}"

    def _compute_waves(self) -> List[List[str]]:
        nodes: Set[str] = set(LEVEL0) | set(LEVEL1_DEPS.keys())
        deps: Dict[str, Set[str]] = {n: set() for n in nodes}
        for child, parents in LEVEL1_DEPS.items():
            deps.setdefault(child, set()).update(parents)
            for p in parents:
                nodes.add(p)
                deps.setdefault(p, set())

        wave0 = [n for n in nodes if n in LEVEL0 or not deps.get(n)]
        waves: List[List[str]] = [sorted(set(wave0))] if wave0 else []
        done: Set[str] = set(wave0)
        remaining: Set[str] = set(nodes) - done

        guard = 0
        while remaining and guard < 1000:
            guard += 1
            ready = [n for n in remaining if deps.get(n, set()).issubset(done)]
            if not ready:
                waves.append(sorted(remaining))
                break
            waves.append(sorted(ready))
            done.update(ready)
            remaining -= set(ready)

        return waves if waves else [[]]

    def _normalize(self, metric_id: str, res: Dict[str, Any] | None) -> Dict[str, Any]:
        out: Dict[str, Any] = dict(res or {})
        out["metric_id"] = metric_id

        band = out.get("band", "C")
        try:
            band_str = str(band).strip().upper()
        except Exception:
            band_str = "C"

        score = out.get("score_0to100")
        if not isinstance(score, (int, float)):
            if band_str in BAND_TO_SCORE:
                score = BAND_TO_SCORE[band_str]
            else:
                try:
                    n = int(band_str)
                    score = max(0, min(100, 20 * n))
                except Exception:
                    score = BAND_TO_SCORE.get("C", 60)
        out["band"] = band_str
        out["score_0to100"] = float(score)

        rationale = str(out.get("rationale", "Limited evidence; conservative band."))
        out["rationale"] = rationale[:600]
        gaps = out.get("gaps") or []
        try:
            gaps = [str(g)[:280] for g in gaps][:5]
        except Exception:
            gaps = []
        out["gaps"] = gaps

        return out

    def _aggregate(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        cat_scores: Dict[str, float] = {}
        for cat, cfg in CATEGORIES.items():
            weights = cfg.get("metrics", {})
            total = 0.0
            for mid, w in weights.items():
                v = results.get(mid, {}).get("score_0to100")
                if isinstance(v, (int, float)):
                    total += float(w) * float(v)
            cat_scores[cat] = round(total, 2)

        overall = round(
            sum(CATEGORIES[c]["weight"] * cat_scores.get(c, 0.0) for c in CATEGORIES),
            2,
        )
        return {"categories": cat_scores, "overall": overall}


def run(snapshot: Dict[str, Any], *, out_dir: Path | str = "runs_mlop_mvp", log_dir: Path | str = "logs/ml_ops") -> Dict[str, Any]:
    orchestrator = MLOpsOrchestrator(out_dir=out_dir, log_dir=log_dir)
    return orchestrator.run(snapshot)